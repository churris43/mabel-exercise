import pytest

from domains.transfers.domain.account_number import AccountNumber
from domains.transfers.domain.exceptions import InvalidAccountNumberError

valid_account_number = "1234567890123456"

def test_account_numbers_are_digits():
    with pytest.raises(InvalidAccountNumberError):
        AccountNumber("POAIDSKDKSKSRODK")

def test_account_numbers_are_16_digits_long():
    with pytest.raises(InvalidAccountNumberError):
        AccountNumber("123456789012345")

def test_16_digits_account_numbers_are_acceptable():
    assert AccountNumber(valid_account_number), (
        f"a valid 16-digit account number should be accepted: {valid_account_number}"
    )