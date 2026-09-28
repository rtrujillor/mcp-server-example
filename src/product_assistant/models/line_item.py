"""Quote line item model."""
from pydantic import BaseModel, Field


class QuoteLineItem(BaseModel):
    """Represents a single line item in a quote."""
    
    name: str = Field(description="Description of the line item")
    unit_price: float = Field(description="Price per unit in the plan currency")
    quantity: int = Field(description="Number of units")
    line_total: float = Field(description="unit_price x quantity")
