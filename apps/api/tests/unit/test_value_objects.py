from datetime import UTC
from decimal import Decimal

import pytest

from app.domain.value_objects import (
    URL,
    DateTimeRange,
    Email,
    Money,
    Percentage,
    PhoneNumber,
)


class TestMoney:
    def test_create_basic(self):
        m = Money(amount=Decimal("10.50"), currency="USD")
        assert m.amount == Decimal("10.50")
        assert m.currency == "USD"

    def test_create_from_float(self):
        m = Money(amount=19.99, currency="EUR")
        assert m.amount == Decimal("19.99")

    def test_create_from_string(self):
        m = Money(amount="100.00", currency="GBP")
        assert m.amount == Decimal("100.00")

    def test_from_cents(self):
        m = Money.from_cents(1999, "USD")
        assert m.amount == Decimal("19.99")
        assert m.cents == 1999

    def test_invalid_currency_raises(self):
        with pytest.raises(ValueError, match="Invalid currency"):
            Money(amount=Decimal(10), currency="XYZ")

    def test_add_same_currency(self):
        a = Money(amount=Decimal(10), currency="USD")
        b = Money(amount=Decimal(5), currency="USD")
        result = a + b
        assert result.amount == Decimal(15)

    def test_add_different_currency_raises(self):
        a = Money(amount=Decimal(10), currency="USD")
        b = Money(amount=Decimal(5), currency="EUR")
        with pytest.raises(ValueError, match="Cannot add"):
            a + b

    def test_subtract(self):
        a = Money(amount=Decimal(20), currency="USD")
        b = Money(amount=Decimal(5), currency="USD")
        result = a - b
        assert result.amount == Decimal(15)

    def test_multiply(self):
        m = Money(amount=Decimal(10), currency="USD")
        result = m * 3
        assert result.amount == Decimal(30)

    def test_comparisons(self):
        a = Money(amount=Decimal(10), currency="USD")
        b = Money(amount=Decimal(20), currency="USD")
        assert b > a
        assert a < b
        assert a <= b
        assert b >= a
        assert a == Money(amount=Decimal(10), currency="USD")

    def test_is_zero(self):
        assert Money(amount=Decimal(0), currency="USD").is_zero()
        assert not Money(amount=Decimal(1), currency="USD").is_zero()

    def test_is_positive_negative(self):
        assert Money(amount=Decimal(1), currency="USD").is_positive()
        assert Money(amount=Decimal(-1), currency="USD").is_negative()

    def test_format(self):
        m = Money(amount=Decimal("1234.56"), currency="USD")
        assert m.format() == "$1,234.56"

    def test_to_dict_from_dict(self):
        m = Money(amount=Decimal("42.50"), currency="EUR")
        d = m.to_dict()
        assert d == {"amount": "42.50", "currency": "EUR"}
        m2 = Money.from_dict(d)
        assert m2 == m

    def test_immutable(self):
        m = Money(amount=Decimal(10), currency="USD")
        with pytest.raises(AttributeError):
            m.amount = Decimal(20)


class TestEmail:
    def test_valid_email(self):
        e = Email("user@example.com")
        assert str(e) == "user@example.com"

    def test_lowercase_normalization(self):
        e = Email("USER@EXAMPLE.COM")
        assert str(e) == "user@example.com"

    def test_strips_whitespace(self):
        e = Email("  user@example.com  ")
        assert str(e) == "user@example.com"

    def test_local_and_domain(self):
        e = Email("user@example.com")
        assert e.local == "user"
        assert e.domain == "example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(ValueError, match="Invalid email"):
            Email("not-an-email")

    def test_invalid_email_no_at(self):
        with pytest.raises(ValueError, match="Invalid email"):
            Email("userexample.com")

    def test_immutable(self):
        e = Email("user@example.com")
        with pytest.raises(AttributeError):
            e.value = "other@example.com"


class TestURL:
    def test_valid_url(self):
        u = URL("https://example.com/path")
        assert str(u) == "https://example.com/path"
        assert u.scheme == "https"
        assert u.host == "example.com"
        assert u.path == "/path"

    def test_http_url(self):
        u = URL("http://localhost:3000/api")
        assert u.scheme == "http"
        assert u.host == "localhost:3000"

    def test_ftp_url(self):
        u = URL("ftp://files.example.com/data")
        assert u.scheme == "ftp"

    def test_invalid_url_no_scheme(self):
        with pytest.raises(ValueError, match="Invalid URL"):
            URL("example.com")

    def test_invalid_url_no_host(self):
        with pytest.raises(ValueError, match="Invalid URL"):
            URL("https://")

    def test_unsupported_scheme(self):
        with pytest.raises(ValueError, match="Invalid URL"):
            URL("javascript:alert(1)")


class TestPhoneNumber:
    def test_valid_international(self):
        p = PhoneNumber("+14155552671")
        assert str(p) == "+14155552671"

    def test_strips_formatting(self):
        p = PhoneNumber("+1 (415) 555-2671")
        assert str(p) == "+14155552671"

    def test_country_code(self):
        p = PhoneNumber("+441234567890")
        assert p.country_code == "44"

    def test_invalid_too_short(self):
        with pytest.raises(ValueError, match="Invalid phone"):
            PhoneNumber("+123456")

    def test_invalid_starts_with_zero(self):
        with pytest.raises(ValueError, match="Invalid phone"):
            PhoneNumber("00123456789")


class TestPercentage:
    def test_valid_percentage(self):
        p = Percentage(Decimal("75.5"))
        assert p.value == Decimal("75.5")

    def test_as_fraction(self):
        p = Percentage(Decimal(50))
        assert p.as_fraction == Decimal("0.5")

    def test_invalid_over_100(self):
        with pytest.raises(ValueError, match="between 0 and 100"):
            Percentage(Decimal(101))

    def test_invalid_negative(self):
        with pytest.raises(ValueError, match="between 0 and 100"):
            Percentage(Decimal(-1))

    def test_boundary_values(self):
        assert Percentage(Decimal(0)).value == Decimal(0)
        assert Percentage(Decimal(100)).value == Decimal(100)

    def test_str(self):
        assert str(Percentage(Decimal("42.5"))) == "42.5%"

    def test_float(self):
        assert float(Percentage(Decimal("42.5"))) == 42.5

    def test_add(self):
        a = Percentage(Decimal(30))
        b = Percentage(Decimal(20))
        assert (a + b).value == Decimal(50)

    def test_sub(self):
        a = Percentage(Decimal(50))
        b = Percentage(Decimal(20))
        assert (a - b).value == Decimal(30)


class TestDateTimeRange:
    def test_valid_range(self):
        from datetime import datetime

        start = datetime(2024, 1, 1, tzinfo=UTC)
        end = datetime(2024, 12, 31, tzinfo=UTC)
        r = DateTimeRange(start=start, end=end)
        assert r.duration_hours > 0

    def test_invalid_range_start_after_end(self):
        from datetime import datetime

        start = datetime(2024, 12, 31, tzinfo=UTC)
        end = datetime(2024, 1, 1, tzinfo=UTC)
        with pytest.raises(ValueError, match="Start date must be before end"):
            DateTimeRange(start=start, end=end)

    def test_contains(self):
        from datetime import datetime

        r = DateTimeRange(
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 12, 31, tzinfo=UTC),
        )
        assert r.contains(datetime(2024, 6, 15, tzinfo=UTC))
        assert not r.contains(datetime(2025, 1, 1, tzinfo=UTC))

    def test_overlaps(self):
        from datetime import datetime

        r1 = DateTimeRange(
            start=datetime(2024, 1, 1, tzinfo=UTC),
            end=datetime(2024, 6, 30, tzinfo=UTC),
        )
        r2 = DateTimeRange(
            start=datetime(2024, 3, 1, tzinfo=UTC),
            end=datetime(2024, 12, 31, tzinfo=UTC),
        )
        r3 = DateTimeRange(
            start=datetime(2025, 1, 1, tzinfo=UTC),
            end=datetime(2025, 12, 31, tzinfo=UTC),
        )
        assert r1.overlaps(r2)
        assert not r1.overlaps(r3)
