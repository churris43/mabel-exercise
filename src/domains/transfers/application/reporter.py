from abc import ABC, abstractmethod
from pathlib import Path

from domains.transfers.domain.account import Account
from domains.transfers.domain.transfer import Transfer

class TransferReporter(ABC):
    """Output port for reporting transfer results.

    The application (e.g. ProcessTransfers) drives this port to emit a record of the
    processed transfers; infrastructure adapters decide the format and
    destination. It lives in the application layer — not in domain/ alongside the
    repository ports — because reporting is a supporting concern, not a core
    domain invariant.
    """

    @abstractmethod
    def write(self, transfers: list[Transfer]) -> Path:
        """Write the report and return the path of the file that was produced."""
        ...


class AccountReporter(ABC):
    """Output port for writing the account balances snapshot.

    Lives here alongside TransferReporter (not in domain/ with the
    AccountRepository port) because writing the snapshot is a supporting concern,
    separate from the repository's read + Unit-of-Work responsibility.
    """

    @abstractmethod
    def write(self, accounts: list[Account]) -> Path:
        """Write the balances snapshot and return the path of the file produced."""
        ...