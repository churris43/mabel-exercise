import pytest

from decimal import Decimal
from domains.transfers.domain.transfer import Transfer, TransferStatus
from domains.transfers.domain.money import Money
from domains.transfers.domain.account_number import AccountNumber

@pytest.fixture
def transfer():
    return Transfer(
        AccountNumber("1234567890123456"),
        AccountNumber("6543210987654321"),
        Money(Decimal("200"))
        )

def test_new_transfer_objects_have_pending_status(transfer):
    assert transfer.status == TransferStatus.PENDING, (
        f"a new transfer should start pending: expected PENDING, got {transfer.status}"
    )

def test_mark_transfer_as_successful_sets_correct_status(transfer):
    transfer.mark_successful()
    assert transfer.status == TransferStatus.SUCCESS, (
        f"mark_successful should set the status: expected SUCCESS, got {transfer.status}"
    )

def test_mark_transfer_as_failed_sets_correct_status(transfer):
    transfer.mark_failed("Insufficient Funds")
    assert transfer.status == TransferStatus.FAILED, (
        f"mark_failed should set the status: expected FAILED, got {transfer.status}"
    )

def test_mark_transfer_as_failed_sets_failure_reason(transfer):
    failure_reason = "Insufficient Funds"
    transfer.mark_failed(failure_reason)
    assert transfer.failure_reason == failure_reason, (
        f"mark_failed should record the reason: expected '{failure_reason}', got '{transfer.failure_reason}'"
    )