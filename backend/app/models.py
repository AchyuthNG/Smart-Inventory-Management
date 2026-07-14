from pydantic import BaseModel, Field


class MovementCreate(BaseModel):
    product_id: int
    branch_id: int
    change_qty: int = Field(..., description="positive = inbound, negative = outbound")
    reason: str = Field(default="restock", max_length=100)


class StockLevelOut(BaseModel):
    product_id: int
    product_name: str
    sku: str
    branch_id: int
    branch_name: str
    quantity: int
    version: int
    low_stock_threshold: int
    is_low: bool


class ProductOut(BaseModel):
    id: int
    sku: str
    name: str
    low_stock_threshold: int


class BranchOut(BaseModel):
    id: int
    name: str


class AlertOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    branch_id: int
    branch_name: str
    triggered_at: str
    resolved: bool


class DepletionRateOut(BaseModel):
    product_id: int
    product_name: str
    branch_id: int
    branch_name: str
    avg_daily_outbound: float
    current_stock: int
    days_until_empty: float | None
    fast_depleting: bool


class MovementResultOut(BaseModel):
    movement_id: int
    new_quantity: int


class MovementOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    sku: str
    branch_id: int
    branch_name: str
    change_qty: int
    direction: str          # "in" or "out", derived from sign of change_qty
    reason: str
    created_at: str        # ISO-8601


class PaginatedMovementsOut(BaseModel):
    items: list[MovementOut]
    total: int             # total rows matching the filter (before pagination)
    limit: int
    offset: int
    has_more: bool