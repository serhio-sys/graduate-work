
import gzip
import django
from pathlib import Path
from django.core.exceptions import (
    ValidationError,
)
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from django.utils.translation import ngettext


class MinimumLengthValidator:
    """
    Validate that the password is of a minimum length.
    """

    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                ngettext(
                    "Пароль закороткий. Він має містити понад "
                    "%(min_length)d символів.",
                    "Пароль закороткий. Він має містити понад "
                    "%(min_length)d символів.",
                    self.min_length,
                ),
                code="password_too_short",
                params={"min_length": self.min_length},
            )

    def get_help_text(self):
        return ngettext(
            "Your password must contain at least %(min_length)d character.",
            "Your password must contain at least %(min_length)d characters.",
            self.min_length,
        ) % {"min_length": self.min_length}


class NumericPasswordValidator:
    """
    Validate that the password is not entirely numeric.
    """

    def validate(self, password, user=None):
        if password.isdigit():
            raise ValidationError(
                _("Пароль містить тільки цифри."),
                code="password_entirely_numeric",
            )

    def get_help_text(self):
        return _("Your password can’t be entirely numeric.")\
        