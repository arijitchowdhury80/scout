"""Product catalog contracts for provider-agnostic extraction."""

from __future__ import annotations

from pydantic import BaseModel, Field

from scout.core.platform.types import Citation


class ProductVariantRecord(BaseModel):
    sku: str = ""
    name: str = ""
    color: str = ""
    size: str = ""
    price: float | None = None
    currency: str = "USD"
    in_stock: bool | None = None


class ProductRecord(BaseModel):
    schema_version: str = "product.v2"
    objectID: str
    brand: str = ""
    name: str
    subtitle: str = ""
    url: str
    category: str = ""
    subcategory: str = ""
    product_type: str = ""
    price: float | None = None
    sale_price: float | None = None
    currency: str = "USD"
    rating: float | None = None
    review_count: int | None = None
    colors: list[str] = Field(default_factory=list)
    sizes: list[str] = Field(default_factory=list)
    variants: list[ProductVariantRecord] = Field(default_factory=list)
    badges: list[str] = Field(default_factory=list)
    description: str = ""
    benefits: list[str] = Field(default_factory=list)
    ingredients: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    completeness_score: float = Field(default=0.0, ge=0.0, le=1.0)
    citations: list[Citation] = Field(default_factory=list)
