from __future__ import annotations
import pytest

from decimal import Decimal
from domains.transfers.domain.money import Money
from domains.transfers.domain.account_number import AccountNumber
from domains.transfers.infrastructure.csv_account_repository import CsvAccountRepository
from domains.transfers.domain.exceptions import AccountNumberNotFoundError, InvalidAccountNumberError

ACCOUNTS_CSV = (
    "1111234522226789,5000.00\n"
    "1111234522221234,10000.00\n"
    "2222123433331212,550.00\n"
    "1212343433335665,1200.00\n"
    "3212343433335755,50000.00\n"
)


# `tmp_path` is a built-in pytest fixture: a unique, empty temporary directory
# (as a pathlib.Path) created fresh for each test and cleaned up automatically.
# We build the input CSV inside it so tests never depend on files in specs/.
@pytest.fixture
def csv_path(tmp_path):
    path = tmp_path / "account_balances.csv"
    path.write_text(ACCOUNTS_CSV)
    return path


@pytest.fixture
def accounts(csv_path):
    return CsvAccountRepository(csv_path).load()


def test_loading_csv_file_creates_one_account_object_per_row(accounts):
    assert len(accounts) == 5, (
        f"loading the csv should create one account per row: expected 5, got {len(accounts)}"
    )

def test_loading_csv_file_creates_object_with_correct_information(accounts):
    account = accounts["1212343433335665"]
    assert account.balance == Money(Decimal("1200.00")), (
        f"account 1212343433335665 should load with its csv balance: expected 1200.00, got {account.balance}"
    )

def test_fetching_an_existing_account_returns_the_correct_account(csv_path):
    """ Tests using get_by_number returns the correct account """
    repository = CsvAccountRepository(csv_path)
    account = repository.get_by_number(AccountNumber("1212343433335665"))
    assert account.balance == Money(Decimal("1200.00")), (
        f"get_by_number should return account 1212343433335665: expected balance 1200.00, got {account.balance}"
    )

def test_fetching_a_non_existing_account_raises_exception(csv_path):
    repository = CsvAccountRepository(csv_path)
    with pytest.raises(AccountNumberNotFoundError):
        repository.get_by_number(AccountNumber("1234567890123456"))


def test_loading_a_csv_with_a_rubbish_row_fails_fast(tmp_path):
    bad_csv = tmp_path / "accounts.csv"
    bad_csv.write_text(
        "1212343433335665,1200.00\n"
        "rubbish,not-a-number\n"
    )
    repository = CsvAccountRepository(bad_csv)

    with pytest.raises(InvalidAccountNumberError):
        repository.load()


# loaded_accounts() exposes the identity map for the reporter to write. Each
# test below isolates one behaviour: full set | empty-before-load | mutations.
def test_loaded_accounts_returns_every_loaded_account(csv_path):
    repository = CsvAccountRepository(csv_path)
    repository.load()

    assert len(repository.loaded_accounts()) == 5, (
        f"loaded_accounts() should return one account per loaded row: expected 5, "
        f"got {len(repository.loaded_accounts())}"
    )


def test_loaded_accounts_is_empty_before_anything_is_loaded(csv_path):
    repository = CsvAccountRepository(csv_path)

    assert repository.loaded_accounts() == [], (
        "loaded_accounts() should be empty when nothing has been loaded, and must "
        "not trigger a load"
    )


def test_loaded_accounts_reflects_in_place_mutations(csv_path):
    repository = CsvAccountRepository(csv_path)
    repository.get_by_number(AccountNumber("1212343433335665")).debit(Money(Decimal("200.00")))

    mutated = next(a for a in repository.loaded_accounts() if a.number.value == "1212343433335665")
    assert mutated.balance == Money(Decimal("1000.00")), (
        "loaded_accounts() should reflect in-place mutations (same identity-mapped "
        f"instance): expected 1000.00, got {mutated.balance}"
    )
