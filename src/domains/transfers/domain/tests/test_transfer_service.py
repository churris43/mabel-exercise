import pytest
from decimal import Decimal

from domains.transfers.infrastructure.testing.fake_account_repository import FakeAccountRepository
from domains.transfers.domain.transfer_service import TransferService
from domains.transfers.infrastructure.csv_account_repository import CsvAccountRepository
from domains.transfers.domain.account_number import AccountNumber
from domains.transfers.domain.account import Account
from domains.transfers.domain.transfer import Transfer, TransferStatus
from domains.transfers.domain.money import Money

AMOUNT = Money(Decimal("500.00"))
CSV_PATH = "specs/mable_account_balances.csv"


# Fresh instances per test so no test can mutate state another test relies on.
@pytest.fixture
def from_account():
    return Account(AccountNumber("1111234522221234"), Money(Decimal("10000.00")))


@pytest.fixture
def to_account():
    return Account(AccountNumber("3212343433335755"), Money(Decimal("50000.00")))


@pytest.fixture
def service(from_account, to_account):
    return TransferService(FakeAccountRepository(from_account, to_account))


def test_successful_transfers_get_the_right_status(service, from_account, to_account):
    transfer = Transfer(from_account.number, to_account.number, AMOUNT)
    transfer_processed = service.process(transfer)
    assert transfer_processed.status == TransferStatus.SUCCESS, (
        f"valid transfer should succeed: expected SUCCESS, got {transfer_processed.status}"
    )


def test_failed_transfers_get_the_right_status(to_account):
    invalid_transfer = Transfer(
        AccountNumber("1234567890123456"),
        to_account.number,
        AMOUNT,
    )
    transfer_service = TransferService(CsvAccountRepository(CSV_PATH))
    transfer_processed = transfer_service.process(invalid_transfer)
    assert transfer_processed.status == TransferStatus.FAILED, (
        f"transfer from an unknown account should fail: expected FAILED, got {transfer_processed.status}"
    )


def test_failed_transfer_records_the_reason_as_a_string():
    from_account = Account(AccountNumber("1111234522221234"), Money(Decimal("100.00")))
    to_account = Account(AccountNumber("3212343433335755"), Money(Decimal("50000.00")))
    service = TransferService(FakeAccountRepository(from_account, to_account))

    transfer_processed = service.process(
        Transfer(from_account.number, to_account.number, Money(Decimal("500.00")))
    )

    assert isinstance(transfer_processed.failure_reason, str), (
        "failure_reason should be a string message, not an exception object: "
        f"got {type(transfer_processed.failure_reason)}"
    )


@pytest.fixture
def processed_accounts(service, from_account, to_account):
    service.process(Transfer(from_account.number, to_account.number, AMOUNT))
    return from_account, to_account

def test_successful_transfer_debits_the_from_account(processed_accounts):
    from_account, _ = processed_accounts
    assert from_account.balance == Money(Decimal("9500.00")), (
        f"from_account should be debited by 500.00: expected 9500.00, got {from_account.balance}"
    )

def test_successful_transfer_credits_the_to_account(processed_accounts):
    _, to_account = processed_accounts
    assert to_account.balance == Money(Decimal("50500.00")), (
        f"to_account should be credited by 500.00: expected 50500.00, got {to_account.balance}"
    )

def test_failed_transfers_leave_both_balances_unchanged():
    from_account = Account(AccountNumber("1111234522221234"), Money(Decimal("100.00")))
    to_account = Account(AccountNumber("3212343433335755"), Money(Decimal("50000.00")))
    service = TransferService(FakeAccountRepository(from_account, to_account))

    _transfer = service.process(
        Transfer(from_account.number, to_account.number, Money(Decimal("500.00")))
    )

    assert from_account.balance == Money(Decimal("100.00")), (
        f"failed transfer must not debit from_account: expected 100.00, got {from_account.balance}"
    )
    assert to_account.balance == Money(Decimal("50000.00")), (
        f"failed transfer must not credit to_account: expected 50000.00, got {to_account.balance}"
    )

def test_unexpected_credit_failure_is_rolled_back_and_propagates():
    # An Account whose credit blows up with a NON-domain error, to simulate a bug
    # or infra failure occurring AFTER the source has already been debited.
    class CreditFailsAccount(Account):
        def credit(self, amount):
            raise RuntimeError("simulated credit failure")

    from_account = Account(AccountNumber("1111234522221234"), Money(Decimal("10000.00")))
    to_account = CreditFailsAccount(AccountNumber("3212343433335755"), Money(Decimal("50000.00")))
    service = TransferService(FakeAccountRepository(from_account, to_account))

    # A non-TransferError surfaces loudly rather than being masked as a failed transfer...
    with pytest.raises(RuntimeError):
        service.process(Transfer(from_account.number, to_account.number, AMOUNT))

    # ...but the source debit is still compensated before it propagates.
    assert from_account.balance == Money(Decimal("10000.00")), (
        "the source debit must be rolled back when the credit fails: "
        f"expected 10000.00, got {from_account.balance}"
    )


def test_process_batch_with_no_transfers_returns_no_results():
    service = TransferService(FakeAccountRepository())

    results = service.process_batch([])

    assert results == [], f"empty batch should produce no results, got {results}"

def test_process_batch_continues_after_a_failed_transfer():
    from_1 = Account(AccountNumber("1111111111111111"), Money(Decimal("1000.00")))
    to_1 = Account(AccountNumber("2222222222222222"), Money(Decimal("0.00")))
    from_2 = Account(AccountNumber("3333333333333333"), Money(Decimal("100.00")))  # too little
    to_2 = Account(AccountNumber("4444444444444444"), Money(Decimal("0.00")))
    from_3 = Account(AccountNumber("5555555555555555"), Money(Decimal("1000.00")))
    to_3 = Account(AccountNumber("6666666666666666"), Money(Decimal("0.00")))
    service = TransferService(
        FakeAccountRepository(from_1, to_1, from_2, to_2, from_3, to_3)
    )
    t1 = Transfer(from_1.number, to_1.number, Money(Decimal("500.00")))
    t2 = Transfer(from_2.number, to_2.number, Money(Decimal("500.00")))  # insufficient funds
    t3 = Transfer(from_3.number, to_3.number, Money(Decimal("500.00")))

    service.process_batch([t1, t2, t3])

    assert t1.status == TransferStatus.SUCCESS, (
        f"t1 has sufficient funds and should succeed: expected SUCCESS, got {t1.status}"
    )
    assert t2.status == TransferStatus.FAILED, (
        f"t2 has insufficient funds and should fail: expected FAILED, got {t2.status}"
    )
    assert t3.status == TransferStatus.SUCCESS, (
        f"t3 must still be processed after t2 fails: expected SUCCESS, got {t3.status}"
    )


def test_process_batch_fails_a_transfer_when_an_account_does_not_exist():
    from_account = Account(AccountNumber("1111111111111111"), Money(Decimal("1000.00")))
    missing_account = AccountNumber("9999999999999999")  # never added to the repository
    service = TransferService(FakeAccountRepository(from_account))
    transfer = Transfer(from_account.number, missing_account, Money(Decimal("500.00")))

    service.process_batch([transfer])

    assert transfer.status == TransferStatus.FAILED, (
        f"transfer to a non-existent account should fail: expected FAILED, got {transfer.status}"
    )
    assert from_account.balance == Money(Decimal("1000.00")), (
        f"failed transfer must not debit from_account: expected 1000.00, got {from_account.balance}"
    )
