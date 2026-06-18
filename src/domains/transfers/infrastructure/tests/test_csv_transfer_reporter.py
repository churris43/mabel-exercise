import csv

from decimal import Decimal
from domains.transfers.domain.money import Money
from domains.transfers.domain.account_number import AccountNumber
from domains.transfers.domain.transfer import Transfer
from domains.transfers.infrastructure.csv_transfer_reporter import CsvTransferReporter


def _transfer():
    return Transfer(
        AccountNumber("1111234522221234"),
        AccountNumber("3212343433335755"),
        Money(Decimal("500.00")),
    )


def _read_rows(path):
    with path.open(newline="") as file:
        return list(csv.reader(file))


# `tmp_path` is a built-in pytest fixture: a unique, empty temporary directory
# (as a pathlib.Path) created fresh for each test and cleaned up automatically.
# We point the reporter at it so tests never write into the real storage/reports/ tree.
def test_report_has_six_headings(tmp_path):
    path = CsvTransferReporter(tmp_path).write([])

    header = _read_rows(path)[0]

    assert len(header) == 6, (
        f"the report header should have 6 columns: expected 6, got {len(header)}"
    )
    assert header == [
        "TransferID",
        "FromAccountNumber",
        "ToAccountNumber",
        "Amount",
        "Status",
        "FailureReason",
    ], f"the report header columns are incorrect: got {header}"


def test_report_row_contains_correct_transfer_information(tmp_path):
    transfer = _transfer()
    transfer.mark_failed("Insufficient Funds")

    path = CsvTransferReporter(tmp_path).write([transfer])

    row = _read_rows(path)[1]  # first data row, after the header
    assert row[1] == "1111234522221234", (
        f"FromAccountNumber is incorrect: expected 1111234522221234, got {row[1]}"
    )
    assert row[2] == "3212343433335755", (
        f"ToAccountNumber is incorrect: expected 3212343433335755, got {row[2]}"
    )
    assert row[3] == "500.00", f"Amount is incorrect: expected 500.00, got {row[3]}"
    assert row[4] == "failed", f"Status is incorrect: expected failed, got {row[4]}"
    assert row[5] == "Insufficient Funds", (
        f"FailureReason is incorrect: expected 'Insufficient Funds', got '{row[5]}'"
    )


def test_failure_reason_is_empty_when_not_set(tmp_path):
    transfer = _transfer()
    transfer.mark_successful()

    path = CsvTransferReporter(tmp_path).write([transfer])

    row = _read_rows(path)[1]
    assert row[5] == "", (
        f"FailureReason should be empty when no reason is set: got '{row[5]}'"
    )


def test_empty_batch_writes_only_the_header(tmp_path):
    path = CsvTransferReporter(tmp_path).write([])

    rows = _read_rows(path)
    assert len(rows) == 1, (
        f"an empty batch should produce only a header row: expected 1, got {len(rows)}"
    )


def test_failure_reason_with_special_characters_round_trips(tmp_path):
    reason = 'Declined, "retry" later'
    transfer = _transfer()
    transfer.mark_failed(reason)

    path = CsvTransferReporter(tmp_path).write([transfer])

    row = _read_rows(path)[1]
    assert row[5] == reason, (
        f"FailureReason with commas/quotes was not preserved: expected '{reason}', got '{row[5]}'"
    )


def test_pending_transfer_is_reported_with_empty_failure_reason(tmp_path):
    transfer = _transfer()  # never processed -> still PENDING

    path = CsvTransferReporter(tmp_path).write([transfer])

    row = _read_rows(path)[1]
    assert row[4] == "pending", (
        f"Status should be pending for an unprocessed transfer: expected pending, got {row[4]}"
    )
    assert row[5] == "", (
        f"FailureReason should be empty for a pending transfer: got '{row[5]}'"
    )
