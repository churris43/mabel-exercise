from __future__ import annotations

from abc import ABC, abstractmethod

from domains.transfers.domain.account import Account
from domains.transfers.domain.account_number import AccountNumber

class AccountRepository(ABC):
    """Repository + Unit-of-Work over the Account aggregate.

    Contract for callers: fetch accounts with ``get_by_number`` and mutate them
    in place (debit/credit). Writing the result out is not the repository's job —
    callers read the touched accounts via ``loaded_accounts`` and hand them to an
    AccountReporter.
    """

    @abstractmethod
    def get_by_number(self, number: AccountNumber) -> Account: ...

    @abstractmethod
    def loaded_accounts(self) -> list[Account]:
        """Return the accounts served so far, for the reporter to write. Empty
        when nothing has been loaded."""
        ...
