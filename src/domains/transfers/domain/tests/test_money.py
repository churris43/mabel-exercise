import pytest

from domains.transfers.domain.money import Money
from decimal import Decimal

from domains.transfers.domain.exceptions import InsufficientFundsError

amount = "200.15"

@pytest.fixture
def money():
    return Money(Decimal(amount))

def test_instantiating_negative_money_throws_an_exception():
    with pytest.raises(ValueError):
        Money(Decimal("-100"))

def test_amounts_are_rounded_to_two_decimals():
    money = Money(Decimal(".014333"))
    assert money.amount == Decimal("0.01"), (
        f"money should round to 2 decimals on construction: expected 0.01, got {money.amount}"
    )

def test_amounts_round_half_up():
    money = Money(Decimal("1.005"))
    assert money.amount == Decimal("1.01"), (
        f"money should round half up: expected 1.01, got {money.amount}"
    )

def test_subtracting_amount_that_results_in_positive_reduces_the_amount(money):
    money_with_new_amount = money.subtract(Money(Decimal("100.20")))
    assert money_with_new_amount.amount == Decimal("99.95"), (
        f"subtracting 100.20 from 200.15 should reduce the amount: expected 99.95, got {money_with_new_amount.amount}"
    )

def test_subtracting_amount_that_results_in_negative_throws_exception(money):
    with pytest.raises(InsufficientFundsError):
        money.subtract(Money(Decimal("5000.00")))
    
def test_adding_an_amount_increases_the_amount(money):
    money_with_new_amount = money.add(Money(Decimal("100.20")))
    assert money_with_new_amount.amount == Decimal("300.35"), (
        f"adding 100.20 to 200.15 should increase the amount: expected 300.35, got {money_with_new_amount.amount}"
    )