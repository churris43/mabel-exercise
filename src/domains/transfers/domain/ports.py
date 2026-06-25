from __future__ import annotations

from abc import ABC, abstractmethod

from domains.transfers.domain.transfer import Transfer


class TransferLoader(ABC):
    """Read-only input gateway that loads Transfers from an external source."""

    @abstractmethod
    def load(self) -> list[Transfer]: ...
