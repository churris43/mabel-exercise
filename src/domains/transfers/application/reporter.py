from abc import ABC, abstractmethod
from pathlib import Path

from domains.transfers.domain.transfer import Transfer

class TransferReporter(ABC):
    """Output port for the Reporting supporting concern.

    The application (ProcessTransfers) drives this port to emit a record of the
    processed transfers; infrastructure adapters decide the format and
    destination. It lives in the application layer — not in domain/ alongside the
    repository ports — because reporting is a supporting concern, not a core
    domain invariant.
    """

    @abstractmethod
    def write(self, transfers: list[Transfer]) -> Path:
        """Write the report and return the path of the file that was produced."""
        ...