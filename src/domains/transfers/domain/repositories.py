from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from domains.transfers.domain.account import Account
from domains.transfers.domain.account_number import AccountNumber

class AccountRepository(ABC):
    """Repository + Unit-of-Work over the Account aggregate.

    Contract for callers: fetch accounts with ``get_by_number`` and mutate them
    in place (debit/credit), then call ``save()`` once to commit. ``save()``
    takes no per-account argument because it persists every account mutated
    since the repository was created — it is a Unit-of-Work commit, not a
    single-entity write.
    """

    @abstractmethod
    def get_by_number(self, number: AccountNumber) -> Account: ...

    @abstractmethod
    def save(self) -> Path | None:
        """Flush all mutated accounts. Returns the written file path, or None
        when there was nothing to persist."""
        ...
