from enum import Enum

from domains.transfers.domain.account_number import AccountNumber
from domains.transfers.domain.money import Money


class TransferStatus(Enum):
    """Lifecycle state of a Transfer.

    - PENDING: created but not yet processed (the initial state);
    - SUCCESS: funds were debited and credited successfully;
    - FAILED: processing was rejected (e.g. insufficient funds or an unknown
      account); see ``failure_reason`` for why.
    """

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class Transfer:
    """A request to move an amount of money from one account to another.

    Carries the instruction (from/to account numbers and amount) together with
    the outcome of processing it: a ``status`` that starts PENDING and becomes
    SUCCESS or FAILED, plus a ``failure_reason`` populated only when FAILED.
    """

    def __init__(self, from_account_number: AccountNumber, to_account_number: AccountNumber, amount: Money):
        self.from_account_number = from_account_number
        self.to_account_number = to_account_number
        self.amount = amount
        self.status = TransferStatus.PENDING
        self.failure_reason: str | None = None
    
    def mark_successful(self):
        self.status = TransferStatus.SUCCESS
    
    def mark_failed(self, reason: str):
        self.status = TransferStatus.FAILED
        self.failure_reason = reason