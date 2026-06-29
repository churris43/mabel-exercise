import csv

import pytest

from decimal import Decimal
from contexts.transfers.application.process_transfers import ProcessTransfers
from contexts.transfers.domain.money import Money
from contexts.transfers.domain.transfer import TransferStatus
from contexts.transfers.infrastructure.csv_account_repository import CsvAccountRepository
from contexts.transfers.infrastructure.csv_account_reporter import CsvAccountReporter
from contexts.transfers.infrastructure.csv_transfer_reporter import CsvTransferReporter

# End-to-end test of the whole flow. The sample inputs are written into tmp_path
# so the test is self-contained; all generated output is redirected there too.
SAMPLE_ACCOUNTS = [
    ("1111234522226789", "5000.00"),
    ("1111234522221234", "10000.00"),
    ("2222123433331212", "550.00"),
    ("1212343433335665", "1200.00"),
    ("3212343433335755", "50000.00"),
]

SAMPLE_TRANSFERS = [
    ("1111234522226789", "1212343433335665", "500.00"),
    ("3212343433335755", "2222123433331212", "1000.00"),
    ("3212343433335755", "1111234522226789", "320.50"),
    ("1111234522221234", "1212343433335665", "25.60"),
]

# Balances after applying every transfer in SAMPLE_TRANSFERS, computed by hand.
EXPECTED_BALANCES = {
    "1111234522226789": Decimal("4820.50"),   # -500.00, +320.50
    "1111234522221234": Decimal("9974.40"),   # -25.60
    "2222123433331212": Decimal("1550.00"),   # +1000.00
    "1212343433335665": Decimal("1725.60"),   # +500.00, +25.60
    "3212343433335755": Decimal("48679.50"),  # -1000.00, -320.50
}


def _write_csv(path, rows):
    with path.open("w", newline="") as file:
        csv.writer(file).writerows(rows)
    return path

@pytest.fixture
def accounts_csv(tmp_path):
    return _write_csv(tmp_path / "accounts.csv", SAMPLE_ACCOUNTS)

@pytest.fixture
def transfers_csv(tmp_path):
    return _write_csv(tmp_path / "transfers.csv", SAMPLE_TRANSFERS)

@pytest.fixture
def result(tmp_path, accounts_csv, transfers_csv):
    return ProcessTransfers(
        accounts_csv,
        transfers_csv,
        CsvTransferReporter(tmp_path),
        CsvAccountReporter(tmp_path),
    ).run()

def test_every_sample_transfer_succeeds(result):
    statuses = [t.status for t in result.transfers]
    assert statuses == [TransferStatus.SUCCESS] * 4, (
        f"all four sample transfers should succeed: got {statuses}"
    )

def test_final_balances_match_the_expected_totals(result):
    reloaded = CsvAccountRepository(result.balances_path).load()
    for number, expected in EXPECTED_BALANCES.items():
        assert reloaded[number].balance == Money(expected), (
            f"account {number} should end at {expected}, got {reloaded[number].balance}"
        )

def test_a_report_row_is_written_for_every_transfer(result):
    with result.report_path.open(newline="") as file:
        rows = list(csv.reader(file))
    assert len(rows) == 5, (
        f"report should have a header plus one row per transfer: expected 5, got {len(rows)}"
    )

def test_a_report_row_is_written_for_every_account(result):
    with result.balances_path.open(newline="") as file:
        rows = list(csv.reader(file))
    expected = len(EXPECTED_BALANCES)
    assert len(rows) == expected, (
        f"balances report should have one row per account (no header): "
        f"expected {expected}, got {len(rows)}"
    )

def test_balances_path_is_none_when_no_transfers_are_processed(tmp_path, accounts_csv):
    # With no transfers, no account is ever fetched, so nothing is loaded and
    # there is nothing to write — the orchestrator must skip the account reporter.
    empty_transfers = tmp_path / "no_transfers.csv"
    empty_transfers.write_text("")
    output_dir = tmp_path / "out"

    result = ProcessTransfers(
        accounts_csv,
        empty_transfers,
        CsvTransferReporter(output_dir),
        CsvAccountReporter(output_dir),
    ).run()

    assert result.balances_path is None, (
        f"balances_path should be None when nothing was loaded: got {result.balances_path}"
    )
    assert list(output_dir.glob("account_balance_*.csv")) == [], (
        "no balances file should be written when nothing was processed"
    )
