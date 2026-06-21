"""Domain exceptions: violations of the transfer domain's invariants.

These live in the domain layer because they express business rules — an
account number must be 16 digits, a balance cannot go below zero, a referenced
account must exist — not infrastructure or framework concerns.
"""

class TransferError(Exception):
    """Base for all transfer-domain rule violations."""
    
class InvalidAccountNumberError(TransferError):
    def __init__(self, message="Invalid account number"):
        super().__init__(message)

class AccountNumberNotFoundError(TransferError):
    def __init__(self, message="Account number not found"):
        super().__init__(message)

class InsufficientFundsError(TransferError):
    def __init__(self, message="Insufficient Funds"):
        super().__init__(message)
