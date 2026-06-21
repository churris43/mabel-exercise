import pytest

from decimal import Decimal
from domains.transfers.domain.money import Money
from domains.transfers.infrastructure.csv_transfer_loader import CsvTransferLoader
from domains.transfers.domain.exceptions import InvalidAccountNumberError

TRANSFERS_CSV = (
    "1111234522226789,1212343433335665,500.00\n"
    "3212343433335755,2222123433331212,1000.00\n"
    "3212343433335755,1111234522226789,320.50\n"
    "1111234522221234,1212343433335665,25.60\n"
)


# `tmp_path` is a built-in pytest fixture: a unique, empty temporary directory
# (as a pathlib.Path) created fresh for each test and cleaned up automatically.
# We build the input CSV inside it so tests never depend on files in specs/.
@pytest.fixture
def csv_path(tmp_path):
    path = tmp_path / "transfers.csv"
    path.write_text(TRANSFERS_CSV)
    return path


@pytest.fixture
def transfers(csv_path):
    return CsvTransferLoader(csv_path).load()

def test_loading_csv_file_creates_one_transfer_object_per_row(transfers):
    assert len(transfers) == 4, (
        f"loading the csv should create one transfer per row: expected 4, got {len(transfers)}"
    )

def test_loading_csv_file_creates_object_with_correct_information(transfers):
    transfer = transfers[1]
    assert transfer.amount == Money(Decimal("1000.00")), (
        f"the second transfer should load with its csv amount: expected 1000.00, got {transfer.amount}"
    )


def test_loading_a_csv_with_an_invalid_account_number_fails_fast(tmp_path):
    bad_csv = tmp_path / "transfers.csv"
    bad_csv.write_text(
        "1111234522226789,1212343433335665,500.00\n"
        "notanumber,1212343433335665,1000.00\n"  # from-account is not a valid account number
    )
    repository = CsvTransferLoader(bad_csv)

    with pytest.raises(InvalidAccountNumberError):
        repository.load()


def test_loading_a_csv_with_a_rubbish_line_fails_fast(tmp_path):
    bad_csv = tmp_path / "transfers.csv"
    bad_csv.write_text(
        "1111234522226789,1212343433335665,500.00\n"
        "this line is total rubbish\n"  # not three comma-separated columns
    )
    repository = CsvTransferLoader(bad_csv)

    with pytest.raises(ValueError):
        repository.load()


def test_loading_a_csv_skips_empty_lines_in_the_middle(tmp_path):
    csv_with_gap = tmp_path / "transfers.csv"
    csv_with_gap.write_text(
        "1111234522226789,1212343433335665,500.00\n"
        "\n"
        "3212343433335755,2222123433331212,1000.00\n"
    )
    repository = CsvTransferLoader(csv_with_gap)

    transfers = repository.load()

    assert len(transfers) == 2, (
        f"empty lines should be skipped, not parsed: expected 2 transfers, got {len(transfers)}"
    )