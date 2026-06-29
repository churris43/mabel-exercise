import csv

from decimal import Decimal
from domains.transfers.domain.account import Account
from domains.transfers.domain.account_number import AccountNumber
from domains.transfers.domain.money import Money
from domains.transfers.infrastructure.csv_account_reporter import CsvAccountReporter
from domains.transfers.infrastructure.csv_account_repository import CsvAccountRepository


ACCOUNT_NUMBER = "1212343433335665"
BALANCE = "1200.00"

def _account(number=ACCOUNT_NUMBER, balance=BALANCE):
    return Account(AccountNumber(number), Money(Decimal(balance)))

def _read_rows(path):
    with path.open(newline="") as file:
        return list(csv.reader(file))

# `tmp_path` is a built-in pytest fixture: a unique, empty temporary directory
# (as a pathlib.Path) created fresh for each test and cleaned up automatically.
# We point the reporter at it so tests never write into the real storage/reports/ tree.

def test_writes_one_row_per_account(tmp_path):
    accounts = [_account(), _account("2222123433331212")]

    path = CsvAccountReporter(tmp_path).write(accounts)

    rows = _read_rows(path)
    assert len(rows) == 2, (
        f"the snapshot should have one row per account (no header): expected 2, got {len(rows)}"
    )

def test_row_contains_account_number_and_balance(tmp_path):
    path = CsvAccountReporter(tmp_path).write([_account()])

    row = _read_rows(path)[0]
    assert row == [ACCOUNT_NUMBER, BALANCE], (
        f"a row should be [account_number, balance]: got {row}"
    )

def test_returns_path_to_a_file_inside_the_output_directory(tmp_path):
    path = CsvAccountReporter(tmp_path).write([_account()])

    assert path.exists(), f"write() should return the path of a file that exists: {path}"
    assert path.parent == tmp_path, (
        f"the file should be written inside the output directory: expected {tmp_path}, got {path.parent}"
    )

def test_creates_the_output_directory_when_missing(tmp_path):
    missing_dir = tmp_path / "reports" / "balances"  # does not exist yet

    CsvAccountReporter(missing_dir).write([_account()])

    assert missing_dir.is_dir(), (
        f"write() should create the output directory if it does not exist: {missing_dir}"
    )

def test_empty_account_list_writes_a_file_with_no_rows(tmp_path):
    path = CsvAccountReporter(tmp_path).write([])

    rows = _read_rows(path)
    assert rows == [], f"an empty account list should produce a file with no rows: got {rows}"

def test_reporter_and_repository_agree_on_the_csv_format(tmp_path):
    accounts = [_account(), _account("2222123433331212", "550.00")]
    path = CsvAccountReporter(tmp_path).write(accounts)

    reloaded = CsvAccountRepository(path).load()
    assert reloaded[ACCOUNT_NUMBER].balance == Money(Decimal(BALANCE)), (
        f"account {ACCOUNT_NUMBER} should reload with the same balance via the repository: "
        f"expected {BALANCE}, got {reloaded[ACCOUNT_NUMBER].balance}"
    )
    assert reloaded["2222123433331212"].balance == Money(Decimal("550.00")), (
        "account 2222123433331212 should reload with the same balance via the repository: "
        f"expected 550.00, got {reloaded['2222123433331212'].balance}"
    )