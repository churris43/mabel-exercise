import json

from decimal import Decimal
from domains.transfers.domain.account import Account
from domains.transfers.domain.account_number import AccountNumber
from domains.transfers.domain.money import Money
from domains.transfers.infrastructure.json_account_reporter import JsonAccountReporter


def _account(number, balance):
    return Account(AccountNumber(number), Money(Decimal(balance)))


def _read_records(path):
    with path.open() as file:
        return json.load(file)


# `tmp_path` is a built-in pytest fixture: a unique, empty temporary directory
# (as a pathlib.Path) created fresh for each test and cleaned up automatically.
# We point the reporter at it so tests never write into the real storage/reports/ tree.

# Each test below asserts exactly one behaviour, so a regression points at a
# single cause:
#   record count | record content | return value | dir creation | empty input.


def test_writes_one_record_per_account(tmp_path):
    accounts = [_account("1111234522226789", "5000.00"), _account("2222123433331212", "550.00")]

    path = JsonAccountReporter(tmp_path).write(accounts)

    records = _read_records(path)
    assert len(records) == 2, (
        f"the snapshot should have one record per account: expected 2, got {len(records)}"
    )


def test_record_contains_account_number_and_balance(tmp_path):
    path = JsonAccountReporter(tmp_path).write([_account("1212343433335665", "1200.00")])

    record = _read_records(path)[0]
    assert record == {"AccountNumber": "1212343433335665", "Balance": "1200.00"}, (
        f"a record should be {{AccountNumber, Balance}}: got {record}"
    )


def test_returns_path_to_a_file_inside_the_output_directory(tmp_path):
    path = JsonAccountReporter(tmp_path).write([_account("1212343433335665", "1200.00")])

    assert path.exists(), f"write() should return the path of a file that exists: {path}"
    assert path.parent == tmp_path, (
        f"the file should be written inside the output directory: expected {tmp_path}, got {path.parent}"
    )


def test_creates_the_output_directory_when_missing(tmp_path):
    missing_dir = tmp_path / "reports" / "balances"  # does not exist yet

    JsonAccountReporter(missing_dir).write([_account("1212343433335665", "1200.00")])

    assert missing_dir.is_dir(), (
        f"write() should create the output directory if it does not exist: {missing_dir}"
    )


def test_empty_account_list_writes_an_empty_array(tmp_path):
    path = JsonAccountReporter(tmp_path).write([])

    records = _read_records(path)
    assert records == [], f"an empty account list should produce an empty JSON array: got {records}"
