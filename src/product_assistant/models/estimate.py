"""Cost estimation result model."""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from product_assistant.models.line_item import QuoteLineItem
from product_assistant.models.usage import UsageProfile


class EstimateCostResult(BaseModel):
    """Result of a cost estimation with validation and traceability."""
    
    valid: bool = Field(description="Whether the estimate is within plan limits")
    currency: str = Field(description="Estimate currency (e.g. EUR)")
    plan: str = Field(description="Evaluated plan identifier")
    usage: UsageProfile = Field(description="Usage profile provided as input")
    items: List[QuoteLineItem] = Field(description="Itemised cost breakdown")
    total_estimated_cost: float = Field(description="Sum of all line items")
    notes: List[str] = Field(description="Human-readable remarks about the estimate")
    trace: Dict[str, List[str]] = Field(description="Traceability: which resource keys were read")
    error: Optional[str] = Field(default=None, description="Error message when valid=False")
