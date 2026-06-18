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


# A separate directory for save() output, kept apart from the input CSV so a
# test can assert the directory is empty when nothing was written.
@pytest.fixture
def output_dir(tmp_path):
    path = tmp_path / "reports"
    path.mkdir()
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


# save() returns the path it wrote, so tests use that rather than guessing the
# timestamped filename.
def test_save_writes_all_loaded_accounts(csv_path, output_dir):
    repository = CsvAccountRepository(csv_path, output_path=output_dir)
    original = repository.load()

    saved_path = repository.save()

    reloaded = CsvAccountRepository(saved_path).load()
    assert len(reloaded) == len(original), "Saved file has a different number of accounts than were loaded"
    for number, account in original.items():
        assert reloaded[number].balance == account.balance, (
            f"Balance for {number} was not saved correctly"
        )


def test_save_persists_mutated_balances(csv_path, output_dir):
    repository = CsvAccountRepository(csv_path, output_path=output_dir)
    accounts = repository.load()
    account = accounts["1212343433335665"]
    account.debit(Money(Decimal("200.00")))  # 1200.00 -> 1000.00

    saved_path = repository.save()

    reloaded = CsvAccountRepository(saved_path).load()
    assert reloaded["1212343433335665"].balance == Money(Decimal("1000.00")), (
        "save() did not persist the mutated balance to disk"
    )


def test_save_without_loading_writes_nothing(csv_path, output_dir):
    repository = CsvAccountRepository(csv_path, output_path=output_dir)

    saved_path = repository.save()

    assert saved_path is None, "save() should not write a file when nothing has been loaded"
    assert list(output_dir.iterdir()) == [], "save() created a file despite nothing being loaded"
