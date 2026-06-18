import csv

import pytest

from decimal import Decimal
from domains.transfers.application.process_transfers import ProcessTransfers
from domains.transfers.domain.money import Money
from domains.transfers.domain.transfer import TransferStatus
from domains.transfers.infrastructure.csv_account_repository import CsvAccountRepository

# End-to-end test of the whole flow against the example files shipped in specs/.
# Inputs are read read-only; all generated output is redirected into tmp_path.
ACCOUNTS_CSV = "specs/mable_account_balances.csv"
TRANSFERS_CSV = "specs/mable_transactions.csv"

# Balances after applying every transfer in mable_transactions.csv, computed by hand.
EXPECTED_BALANCES = {
    "1111234522226789": Decimal("4820.50"),   # -500.00, +320.50
    "1111234522221234": Decimal("9974.40"),   # -25.60
    "2222123433331212": Decimal("1550.00"),   # +1000.00
    "1212343433335665": Decimal("1725.60"),   # +500.00, +25.60
    "3212343433335755": Decimal("48679.50"),  # -1000.00, -320.50
}


@pytest.fixture
def result(tmp_path):
    return ProcessTransfers(ACCOUNTS_CSV, TRANSFERS_CSV, output_path=tmp_path).run()


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
