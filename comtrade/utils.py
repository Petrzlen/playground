import locale

from enum import Enum


# TODO: Will need dictionary from values to name.
class MMEnum(Enum):
    """So the enum values are 'value' instead of '<class Blah: ...>' """
    # https://stackoverflow.com/questions/24487405/enum-getting-value-of-enum-on-string-conversion
    def __str__(self):
        return str(self.value)


def format_money(amount):
    # https://stackoverflow.com/questions/1823058/how-to-print-number-with-commas-as-thousands-separators
    # return locale.format("$%d", amount, grouping=True)  # for non-american
    return f"${amount:,}"