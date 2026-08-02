from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from src.core.exceptions import ValidationError


def parse_amount(value: object, *, field: str = "amount") -> Decimal:
    """Coerces a caller-supplied amount (str/int/float/Decimal) to a 2-decimal
    Decimal, raising ValidationError for anything invalid or not > 0.

    Callers of the service layer aren't only the REST routers — the AI agent
    and the test suite both call services directly with plain strings,
    bypassing the Pydantic schema coercion that normally happens first for
    HTTP requests. Comparing an un-coerced string against 0 raises TypeError
    instead of failing validation cleanly, so every amount must pass through
    here before any numeric use.
    """
    if isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, (int, float, str)):
        try:
            decimal_value = Decimal(str(value))
        except InvalidOperation as exc:
            raise ValidationError("Amount must be a valid number", field=field) from exc
    else:
        raise ValidationError("Amount must be a valid number", field=field)

    decimal_value = decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if decimal_value <= 0:
        raise ValidationError("Amount must be greater than 0", field=field)

    return decimal_value
