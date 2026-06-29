import json

from decimal import Decimal
from contexts.transfers.domain.money import Money
from contexts.transfers.domain.account_number import AccountNumber
from contexts.transfers.domain.transfer import Transfer
from contexts.transfers.infrastructure.json_transfer_reporter import JsonTransferReporter


def _transfer():
    return Transfer(
        AccountNumber("1111234522221234"),
        AccountNumber("3212343433335755"),
        Money(Decimal("500.00")),
    )

def _read_records(path):
    with path.open() as file:
        return json.load(file)

# `tmp_path` is a built-in pytest fixture: a unique, empty temporary directory
# (as a pathlib.Path) created fresh for each test and cleaned up automatically.
# We point the reporter at it so tests never write into the real storage/reports/ tree.
def test_report_record_has_six_fields(tmp_path):
    transfer = _transfer()

    path = JsonTransferReporter(tmp_path).write([transfer])

    record = _read_records(path)[0]
    assert list(record.keys()) == [
        "TransferID",
        "FromAccountNumber",
        "ToAccountNumber",
        "Amount",
        "Status",
        "FailureReason",
    ], f"the report record fields are incorrect: got {list(record.keys())}"

def test_report_record_contains_correct_transfer_information(tmp_path):
    transfer = _transfer()
    transfer.mark_failed("Insufficient Funds")

    path = JsonTransferReporter(tmp_path).write([transfer])

    record = _read_records(path)[0]
    assert record["FromAccountNumber"] == "1111234522221234", (
        f"FromAccountNumber is incorrect: got {record['FromAccountNumber']}"
    )
    assert record["ToAccountNumber"] == "3212343433335755", (
        f"ToAccountNumber is incorrect: got {record['ToAccountNumber']}"
    )
    assert record["Amount"] == "500.00", f"Amount is incorrect: got {record['Amount']}"
    assert record["Status"] == "failed", f"Status is incorrect: got {record['Status']}"
    assert record["FailureReason"] == "Insufficient Funds", (
        f"FailureReason is incorrect: got '{record['FailureReason']}'"
    )

def test_failure_reason_is_empty_when_not_set(tmp_path):
    transfer = _transfer()
    transfer.mark_successful()

    path = JsonTransferReporter(tmp_path).write([transfer])

    record = _read_records(path)[0]
    assert record["FailureReason"] == "", (
        f"FailureReason should be empty when no reason is set: got '{record['FailureReason']}'"
    )

def test_empty_batch_writes_an_empty_array(tmp_path):
    path = JsonTransferReporter(tmp_path).write([])

    records = _read_records(path)
    assert records == [], (
        f"an empty batch should produce an empty JSON array: got {records}"
    )

def test_failure_reason_preserves_commas_and_quotes(tmp_path):
    reason = 'Declined, "retry" later'
    transfer = _transfer()
    transfer.mark_failed(reason)

    path = JsonTransferReporter(tmp_path).write([transfer])

    record = _read_records(path)[0]
    assert record["FailureReason"] == reason, (
        f"FailureReason with commas/quotes was not preserved: expected '{reason}', got '{record['FailureReason']}'"
    )

def test_pending_transfer_is_reported_with_empty_failure_reason(tmp_path):
    transfer = _transfer()  # a pending transfer (default state)

    path = JsonTransferReporter(tmp_path).write([transfer])

    record = _read_records(path)[0]
    assert record["Status"] == "pending", (
        f"the reporter should serialize a pending transfer's Status as 'pending': got {record['Status']}"
    )
    assert record["FailureReason"] == "", (
        f"the reporter should leave FailureReason empty for a pending transfer: got '{record['FailureReason']}'"
    )
