from pydantic import BaseModel, Field


class OrderRequest(BaseModel):

    width_mm: int = Field(
        gt=0
    )

    required_weight_kg: float = Field(
        gt=0
    )


class OptimizeRequest(BaseModel):

    thickness_mm: float = Field(
        gt=0
    )

    coil_width_mm: int = Field(
        gt=0
    )

    kerf_mm: float = Field(
        ge=0
    )

    coil_weight_kg: float | None = Field(
        default=None,
        gt=0
    )

    orders: list[OrderRequest]

    stock_widths_mm: list[int] = Field(
        min_length=1
    )

    top_n: int = Field(
        default=10,
        ge=1,
        le=100
    )