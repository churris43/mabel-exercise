import pytest

from domains.transfers.domain.exceptions import InsufficientFundsError
from decimal import Decimal
from domains.transfers.domain.account import Account
from domains.transfers.domain.money import Money

balance = Money(Decimal("1000.23"))

@pytest.fixture
def account():
    return Account(1111234522226789, balance)

def test_debiting_amount_lower_than_balance_reduces_balance(account):
    account.debit(Money(Decimal("200")))
    assert account.balance == Money(Decimal("800.23")), (
        f"debiting 200 should reduce the balance: expected 800.23, got {account.balance}"
    )

def test_debiting_amount_greater_than_balance_throws_exception(account):
    with pytest.raises(InsufficientFundsError):
        account.debit(Money(Decimal("1200.93")))

def test_crediting_an_amount_increases_balance(account):
    account.credit(Money(Decimal("200.48")))
    assert account.balance == Money(Decimal("1200.71")), (
        f"crediting 200.48 should increase the balance: expected 1200.71, got {account.balance}"
    )

def test_crediting_a_sub_cent_amount_is_rounded_to_two_decimals(account):
    account.credit(Money(Decimal(".014333")))  # rounds to 0.01
    assert account.balance == Money(Decimal("1000.24")), (
        f"crediting .014333 should round to a cent: expected 1000.24, got {account.balance}"
    )