from decimal import Decimal
from typing import Any
from pydantic import BaseModel, ConfigDict, field_serializer


class FinancialBaseModel(BaseModel):
    """Base model enforcing financial precision and strict serialization standards."""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        validate_assignment=True,
    )

    @field_serializer('*', mode='plain', when_used='json')
    def serialize_financial_fields(self, value: Any) -> Any:
        """Ensure Decimal instances are serialized as exact strings preserving precision."""
        if isinstance(value, Decimal):
            exponent = abs(value.as_tuple().exponent)
            precision = max(exponent, 2)
            return f"{value:.{precision}f}"
        return value

