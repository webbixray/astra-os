from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Self
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal = field(default=Decimal("0.00"))
    currency: str = "USD"

    VALID_CURRENCIES = frozenset({
        "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY", "INR", "BRL",
        "MXN", "KRW", "SGD", "HKD", "SEK", "NOK", "DKK", "PLN", "CZK", "HUF",
        "THB", "IDR", "MYR", "PHP", "VND", "ZAR", "AED", "SAR", "QAR", "KWD",
        "BHD", "TRY", "RUB", "NGN", "KES", "EGP", "ARS", "CLP", "COP", "PEN",
    })

    def __post_init__(self) -> None:
        if isinstance(self.amount, (int, float)):
            object.__setattr__(self, "amount", Decimal(str(self.amount)).quantize(Decimal("0.01")))
        elif isinstance(self.amount, str):
            try:
                object.__setattr__(self, "amount", Decimal(self.amount).quantize(Decimal("0.01")))
            except InvalidOperation:
                raise ValueError(f"Invalid amount: {self.amount}")
        if self.currency not in self.VALID_CURRENCIES:
            raise ValueError(f"Invalid currency: {self.currency}")

    @classmethod
    def from_cents(cls, cents: int, currency: str = "USD") -> Self:
        return cls(amount=Decimal(str(cents)) / Decimal(100), currency=currency)

    @property
    def cents(self) -> int:
        return int(self.amount * Decimal(100))

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(amount=self.amount + other.amount, currency=self.currency)

    def __sub__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        return Money(amount=self.amount - other.amount, currency=self.currency)

    def __mul__(self, factor: float | Decimal) -> Money:
        return Money(amount=self.amount * Decimal(str(factor)), currency=self.currency)

    def __gt__(self, other: Money) -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} and {other.currency}")
        return self.amount > other.amount

    def __ge__(self, other: Money) -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} and {other.currency}")
        return self.amount >= other.amount

    def __lt__(self, other: Money) -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} and {other.currency}")
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare {self.currency} and {other.currency}")
        return self.amount <= other.amount

    def is_zero(self) -> bool:
        return self.amount == Decimal("0.00")

    def is_positive(self) -> bool:
        return self.amount > Decimal("0.00")

    def is_negative(self) -> bool:
        return self.amount < Decimal("0.00")

    def format(self, *, symbol: bool = True) -> str:
        symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "INR": "₹"}
        if symbol and self.currency in symbols:
            return f"{symbols[self.currency]}{self.amount:,.2f}"
        return f"{self.amount:,.2f} {self.currency}"

    def to_dict(self) -> dict[str, Any]:
        return {"amount": str(self.amount), "currency": self.currency}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Money:
        return cls(amount=Decimal(data["amount"]), currency=data["currency"])


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    _PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )

    def __post_init__(self) -> None:
        if not self._PATTERN.match(self.value):
            raise ValueError(f"Invalid email address: {self.value}")
        object.__setattr__(self, "value", self.value.lower().strip())

    @property
    def local(self) -> str:
        return self.value.split("@")[0]

    @property
    def domain(self) -> str:
        return self.value.split("@")[1]

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class URL:
    value: str

    def __post_init__(self) -> None:
        parsed = urlparse(self.value)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(f"Invalid URL: {self.value}")
        if parsed.scheme not in ("http", "https", "ftp", "ftps"):
            raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")

    @property
    def scheme(self) -> str:
        return urlparse(self.value).scheme

    @property
    def host(self) -> str:
        return urlparse(self.value).netloc

    @property
    def path(self) -> str:
        return urlparse(self.value).path

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PhoneNumber:
    value: str

    _PATTERN = re.compile(r"^\+?[1-9]\d{6,14}$")

    def __post_init__(self) -> None:
        cleaned = re.sub(r"[\s\-\(\)]", "", self.value)
        if not self._PATTERN.match(cleaned):
            raise ValueError(f"Invalid phone number: {self.value}")
        object.__setattr__(self, "value", cleaned)

    @property
    def country_code(self) -> str:
        if self.value.startswith("+"):
            return self.value[1:3] if len(self.value) > 3 else self.value[1:]
        return ""

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Percentage:
    value: Decimal

    def __post_init__(self) -> None:
        if isinstance(self.value, (int, float)):
            object.__setattr__(self, "value", Decimal(str(self.value)))
        if self.value < Decimal(0) or self.value > Decimal(100):
            raise ValueError(f"Percentage must be between 0 and 100: {self.value}")

    @property
    def as_fraction(self) -> Decimal:
        return self.value / Decimal(100)

    def __add__(self, other: Percentage) -> Percentage:
        return Percentage(self.value + other.value)

    def __sub__(self, other: Percentage) -> Percentage:
        return Percentage(self.value - other.value)

    def __mul__(self, factor: float | Decimal) -> Percentage:
        return Percentage(self.value * Decimal(str(factor)))

    def __str__(self) -> str:
        return f"{self.value}%"

    def __float__(self) -> float:
        return float(self.value)


@dataclass(frozen=True, slots=True)
class DateTimeRange:
    start: Any
    end: Any

    def __post_init__(self) -> None:
        if self.start and self.end and self.start > self.end:
            raise ValueError("Start date must be before end date")

    @property
    def duration_hours(self) -> float:
        if not self.start or not self.end:
            return 0.0
        delta = self.end - self.start
        return delta.total_seconds() / 3600

    def contains(self, dt: Any) -> bool:
        if not self.start or not self.end:
            return False
        return self.start <= dt <= self.end

    def overlaps(self, other: DateTimeRange) -> bool:
        if not self.start or not self.end or not other.start or not other.end:
            return False
        return self.start < other.end and other.start < self.end
