import pytest
from decimal import Decimal

from contexts.transfers.infrastructure.testing.fake_account_repository import FakeAccountRepository
from contexts.transfers.domain.transfer_execution import TransferExecution
from contexts.transfers.domain.account_number import AccountNumber
from contexts.transfers.domain.account import Account
from contexts.transfers.domain.transfer import Transfer, TransferStatus
from contexts.transfers.domain.money import Money

AMOUNT = Money(Decimal("500.00"))


# Fresh instances per test so no test can mutate state another test relies on.
@pytest.fixture
def from_account():
    return Account(AccountNumber("1234567890123456"), Money(Decimal("10000.00")))


@pytest.fixture
def to_account():
    return Account(AccountNumber("6543210987654321"), Money(Decimal("50000.00")))

# The FakeAccountRepository creates the from_ and to_account and also used for lookups
@pytest.fixture
def transfer_execution(from_account, to_account):
    return TransferExecution(FakeAccountRepository(from_account, to_account))


def test_successful_transfers_get_the_right_status(transfer_execution, from_account, to_account):
    transfer = Transfer(from_account.number, to_account.number, AMOUNT)
    transfer_processed = transfer_execution.execute(transfer)
    assert transfer_processed.status == TransferStatus.SUCCESS, (
        f"valid transfer should succeed: expected SUCCESS, got {transfer_processed.status}"
    )


def test_failed_transfers_get_the_right_status(to_account):
    # The source account is absent from the repository, so its lookup fails.
    unknown_from_account = AccountNumber("1111111111111111")
    invalid_transfer = Transfer(unknown_from_account, to_account.number, AMOUNT)
    transfer_execution = TransferExecution(FakeAccountRepository(to_account))
    transfer_processed = transfer_execution.execute(invalid_transfer)
    assert transfer_processed.status == TransferStatus.FAILED, (
        f"transfer from an unknown account should fail: expected FAILED, got {transfer_processed.status}"
    )


def test_failed_transfer_records_the_reason_as_a_string():
    # Can't use accounts from the fixture as different balances are needed
    from_account = Account(AccountNumber("1234567890123456"), Money(Decimal("100.00")))
    to_account = Account(AccountNumber("6543210987654321"), Money(Decimal("50000.00")))
    transfer_execution = TransferExecution(FakeAccountRepository(from_account, to_account))

    transfer_processed = transfer_execution.execute(
        Transfer(from_account.number, to_account.number, Money(Decimal("500.00")))
    )

    assert isinstance(transfer_processed.failure_reason, str), (
        "failure_reason should be a string message, not an exception object: "
        f"got {type(transfer_processed.failure_reason)}"
    )


@pytest.fixture
def processed_accounts(transfer_execution, from_account, to_account):
    transfer_execution.execute(Transfer(from_account.number, to_account.number, AMOUNT))
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
    from_account = Account(AccountNumber("1234567890123456"), Money(Decimal("100.00")))
    to_account = Account(AccountNumber("6543210987654321"), Money(Decimal("50000.00")))
    transfer_execution = TransferExecution(FakeAccountRepository(from_account, to_account))

    _transfer = transfer_execution.execute(
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
    # If this is needed on other test cases, evaluate the option to create a Fake
    class CreditFailsAccount(Account):
        def credit(self, amount):
            raise RuntimeError("simulated credit failure")

    from_account = Account(AccountNumber("1234567890123456"), Money(Decimal("10000.00")))
    to_account = CreditFailsAccount(AccountNumber("6543210987654321"), Money(Decimal("50000.00")))
    transfer_execution = TransferExecution(FakeAccountRepository(from_account, to_account))

    # A non-TransferError surfaces loudly rather than being masked as a failed transfer...
    with pytest.raises(RuntimeError):
        transfer_execution.execute(Transfer(from_account.number, to_account.number, AMOUNT))

    # ...but the source debit is still compensated before it propagates.
    assert from_account.balance == Money(Decimal("10000.00")), (
        "the source debit must be rolled back when the credit fails: "
        f"expected 10000.00, got {from_account.balance}"
    )

def test_execute_batch_with_no_transfers_returns_no_results():
    transfer_execution = TransferExecution(FakeAccountRepository())
    results = transfer_execution.execute_batch([])
    assert results == [], f"empty batch should produce no results, got {results}"

def test_execute_batch_continues_after_a_failed_transfer():
    from_1 = Account(AccountNumber("1111111111111111"), Money(Decimal("1000.00")))
    to_1 = Account(AccountNumber("2222222222222222"), Money(Decimal("0.00")))
    from_2 = Account(AccountNumber("3333333333333333"), Money(Decimal("100.00")))  # too little
    to_2 = Account(AccountNumber("4444444444444444"), Money(Decimal("0.00")))
    from_3 = Account(AccountNumber("5555555555555555"), Money(Decimal("1000.00")))
    to_3 = Account(AccountNumber("6666666666666666"), Money(Decimal("0.00")))
    transfer_execution = TransferExecution(
        FakeAccountRepository(from_1, to_1, from_2, to_2, from_3, to_3)
    )
    t1 = Transfer(from_1.number, to_1.number, Money(Decimal("500.00")))
    t2 = Transfer(from_2.number, to_2.number, Money(Decimal("500.00")))  # insufficient funds, only 100
    t3 = Transfer(from_3.number, to_3.number, Money(Decimal("500.00")))

    transfer_execution.execute_batch([t1, t2, t3])

    assert t1.status == TransferStatus.SUCCESS, (
        f"t1 has sufficient funds and should succeed: expected SUCCESS, got {t1.status}"
    )
    assert t2.status == TransferStatus.FAILED, (
        f"t2 has insufficient funds and should fail: expected FAILED, got {t2.status}"
    )
    assert t3.status == TransferStatus.SUCCESS, (
        f"t3 must still be processed after t2 fails: expected SUCCESS, got {t3.status}"
    )

def test_execute_batch_fails_a_transfer_when_an_account_does_not_exist(from_account, to_account):
    transfer_execution = TransferExecution(FakeAccountRepository(from_account)) # to_account never added to the repository
    transfer = Transfer(from_account.number, to_account.number, Money(Decimal("500.00")))

    transfer_execution.execute_batch([transfer])

    assert transfer.status == TransferStatus.FAILED, (
        f"transfer to a non-existent account should fail: expected FAILED, got {transfer.status}"
    )
    assert from_account.balance == Money(Decimal("10000.00")), (
        f"failed transfer must not debit from_account: expected 10000.00, got {from_account.balance}"
    )
