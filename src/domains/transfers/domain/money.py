# Defer evaluation of type annotations so methods can reference Money before
# the class is fully defined (avoids needing quoted forward references).
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from domains.transfers.domain.exceptions import InsufficientFundsError

from dataclasses import dataclass

CENTS = Decimal("0.01")

@dataclass(frozen=True)
class Money:
    """A non-negative monetary amount.

    Amounts are whole-cent only: any extra precision is rounded to 2 decimal
    places (ROUND_HALF_UP) on construction, so all Money values — including the
    results of add()/subtract() — carry exactly 2 decimals.
    """

    amount: Decimal

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Negative money amounts are not acceptable")
        # Money is whole-cent only: normalise any extra precision to 2 decimals.
        # Frozen dataclasses block normal assignment, so set the field via
        # object.__setattr__.
        object.__setattr__(self, "amount", self.amount.quantize(CENTS, rounding=ROUND_HALF_UP))
    
    def subtract(self, other: Money) -> Money:
        result = self.amount - other.amount
        if result < 0:
            raise InsufficientFundsError()
        return Money(result)

    def add(self, other: Money) -> Money:
        return Money(self.amount + other.amount)
    
    def __str__(self) -> str:
        return f"{self.amount:.2f}"