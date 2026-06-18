from domains.transfers.domain.repositories import AccountRepository
from domains.transfers.domain.account import Account
from domains.transfers.domain.account_number import AccountNumber
from domains.transfers.domain.exceptions import AccountNumberNotFoundError

class FakeAccountRepository(AccountRepository):
    """In-memory AccountRepository for tests.

    Lives under infrastructure/testing/ to make clear it's a test double, not a
    production adapter. It mirrors the real adapter's contract — notably it
    raises AccountNumberNotFoundError (not a bare KeyError) for a missing
    account — so tests exercise the same failure behaviour as production.
    """

    def __init__(self, *accounts):
        self._accounts = {a.number.value: a for a in accounts}

    def get_by_number(self, number: AccountNumber) -> Account:
        try:
            return self._accounts[number.value]
        except KeyError:
            raise AccountNumberNotFoundError() from None

    def save(self):
        pass
