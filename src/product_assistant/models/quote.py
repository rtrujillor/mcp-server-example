"""Quote generation result model."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from product_assistant.models.line_item import QuoteLineItem


class GenerateQuoteResult(BaseModel):
    """Result of a formal quote generation with itemized costs and discounts."""
    
    valid: bool = Field(description="Whether the quote is valid and within plan limits")
    currency: str = Field(description="Quote currency (e.g. EUR)")
    cycle: str = Field(description="Billing cycle: monthly or yearly")
    plan_id: str = Field(description="Requested plan identifier")
    users: int = Field(description="Number of users in the quote")
    items: List[QuoteLineItem] = Field(description="Itemised cost breakdown")
    subtotal: float = Field(description="Raw sum of all line items before discounts")
    tax: float = Field(description="Applicable tax amount (0 for this PoC)")
    total: float = Field(description="subtotal + tax")
    applied_discounts: List[Dict[str, Any]] = Field(description="Volume or promotional discounts applied")
    notes: List[str] = Field(description="Human-readable remarks about the quote")
    valid_until: str = Field(description="ISO-8601 date the quote expires (today + 14 days)")
    trace: Dict[str, List[str]] = Field(description="Traceability: which resource keys were read")
    error: Optional[str] = Field(default=None, description="Error message when valid=False")
