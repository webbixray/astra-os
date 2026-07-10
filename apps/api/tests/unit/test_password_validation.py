from __future__ import annotations

import pytest

from app.application.use_cases.auth_use_cases import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    validate_password_strength,
)
from app.domain.exceptions.domain_exceptions import ValidationError


class TestPasswordValidation:
    def test_valid_password(self):
        validate_password_strength("Abcdef1!xyz")

    def test_too_short(self):
        with pytest.raises(ValidationError, match=f"{PASSWORD_MIN_LENGTH}"):
            validate_password_strength("Ab1!")

    def test_too_long(self):
        with pytest.raises(ValidationError, match=f"{PASSWORD_MAX_LENGTH}"):
            validate_password_strength("A" * (PASSWORD_MAX_LENGTH + 1))

    def test_missing_uppercase(self):
        with pytest.raises(ValidationError, match="uppercase"):
            validate_password_strength("abcdef1!xyz")

    def test_missing_lowercase(self):
        with pytest.raises(ValidationError, match="lowercase"):
            validate_password_strength("ABCDEF1!XYZ")

    def test_missing_digit(self):
        with pytest.raises(ValidationError, match="digit"):
            validate_password_strength("Abcdefg!xyz")

    def test_missing_special_char(self):
        with pytest.raises(ValidationError, match="special"):
            validate_password_strength("Abcdef1xyz")

    def test_password_with_spaces(self):
        with pytest.raises(ValidationError, match="special"):
            validate_password_strength("Abc def 1 xyz")
