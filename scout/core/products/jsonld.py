"""Extract product data from JSON-LD script tags."""

from __future__ import annotations

import json
from html.parser import HTMLParser

from pydantic import BaseModel, Field


class ProductJsonLd(BaseModel):
    name: str = ""
    brand: str = ""
    sku: str = ""
    description: str = ""
    images: list[str] = Field(default_factory=list)
    price: float | None = None
    currency: str = ""
    in_stock: bool | None = None


class _JsonLdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_jsonld = False
        self.scripts: list[str] = []
        self._current: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key.lower(): value or "" for key, value in attrs}
        self.in_jsonld = (
            tag.lower() == "script" and attr_map.get("type", "").lower() == "application/ld+json"
        )
        if self.in_jsonld:
            self._current = []

    def handle_data(self, data: str) -> None:
        if self.in_jsonld:
            self._current.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self.in_jsonld:
            self.scripts.append("".join(self._current))
            self._current = []
            self.in_jsonld = False


def extract_product_jsonld(html: str) -> ProductJsonLd | None:
    """Return the first schema.org Product JSON-LD object found in HTML."""
    parser = _JsonLdParser()
    parser.feed(html or "")

    for script in parser.scripts:
        try:
            raw = json.loads(script)
        except json.JSONDecodeError:
            continue
        product = _find_product(raw)
        if product:
            return _normalise_product(product)
    return None


def _find_product(value: object) -> dict | None:
    if isinstance(value, list):
        for item in value:
            found = _find_product(item)
            if found:
                return found
    if isinstance(value, dict):
        raw_type = value.get("@type", "")
        types = raw_type if isinstance(raw_type, list) else [raw_type]
        if any(str(item).lower() == "product" for item in types):
            return value
        graph = value.get("@graph")
        if graph:
            return _find_product(graph)
    return None


def _normalise_product(raw: dict) -> ProductJsonLd:
    images = _listify(raw.get("image"))
    offer = _first(raw.get("offers"))
    brand = raw.get("brand", "")
    if isinstance(brand, dict):
        brand = brand.get("name", "")

    return ProductJsonLd(
        name=str(raw.get("name", "") or ""),
        brand=str(brand or ""),
        sku=str(raw.get("sku", "") or ""),
        description=str(raw.get("description", "") or ""),
        images=images,
        price=_to_price(offer.get("price") if offer else None),
        currency=str(offer.get("priceCurrency", "") if offer else ""),
        in_stock=_to_stock(offer.get("availability") if offer else None),
    )


def _listify(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str) and value:
        return [value]
    return []


def _first(value: object) -> dict:
    if isinstance(value, list):
        return value[0] if value and isinstance(value[0], dict) else {}
    return value if isinstance(value, dict) else {}


def _to_price(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).replace("$", "").replace(",", ""))
    except ValueError:
        return None


def _to_stock(value: object) -> bool | None:
    if value is None:
        return None
    text = str(value).lower()
    if "instock" in text:
        return True
    if "outofstock" in text:
        return False
    return None
