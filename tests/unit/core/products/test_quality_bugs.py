"""Tests for Phase 6 quality bug fixes — junk filter, dedup, brand fallback."""

from __future__ import annotations


from scout.core.products.algolia import (
    brand_fallback,
    canonical_url,
    is_junk_record,
    build_algolia_record,
    build_listing_algolia_record,
)
from scout.core.types import ProductListingCard


class TestJunkFilter:
    def test_rejects_hang_tight(self) -> None:
        assert is_junk_record("Hang Tight") is True

    def test_rejects_verify_age(self) -> None:
        assert is_junk_record("Verify your age") is True

    def test_rejects_access_denied(self) -> None:
        assert is_junk_record("Access Denied") is True

    def test_rejects_captcha(self) -> None:
        assert is_junk_record("CAPTCHA") is True

    def test_rejects_checkout(self) -> None:
        assert is_junk_record("Checkout") is True

    def test_rejects_your_cart(self) -> None:
        assert is_junk_record("Your Cart") is True

    def test_rejects_404(self) -> None:
        assert is_junk_record("404") is True

    def test_rejects_error_codes(self) -> None:
        assert is_junk_record("Error 403") is True

    def test_accepts_real_product(self) -> None:
        assert is_junk_record("Nike Air Max 90") is False

    def test_accepts_normal_title(self) -> None:
        assert is_junk_record("Premium Leather Wallet") is False

    def test_case_insensitive(self) -> None:
        assert is_junk_record("access denied") is True
        assert is_junk_record("ACCESS DENIED") is True


class TestCanonicalUrl:
    def test_strips_variant_param(self) -> None:
        url = "https://shop.com/shoes/air-max?variant=123&color=red"
        result = canonical_url(url)
        assert "variant" not in result
        assert "color" not in result

    def test_preserves_non_variant_params(self) -> None:
        url = "https://shop.com/shoes?category=running&variant=123"
        result = canonical_url(url)
        assert "category=running" in result
        assert "variant" not in result

    def test_no_query_unchanged(self) -> None:
        url = "https://shop.com/shoes/air-max"
        assert canonical_url(url) == url

    def test_strips_fragment(self) -> None:
        url = "https://shop.com/shoes#reviews"
        result = canonical_url(url)
        assert "#" not in result

    def test_same_product_different_variants_same_canonical(self) -> None:
        url1 = "https://shop.com/shoes/air-max?variant=1&size=10"
        url2 = "https://shop.com/shoes/air-max?variant=2&size=11"
        assert canonical_url(url1) == canonical_url(url2)


class TestBrandFallback:
    def test_returns_existing_brand(self) -> None:
        assert brand_fallback("Nike", "https://www.nike.com/shoes") == "Nike"

    def test_fallback_to_domain(self) -> None:
        assert brand_fallback("", "https://www.nike.com/shoes") == "Nike"

    def test_strips_www(self) -> None:
        assert brand_fallback("", "https://www.adidas.com/") == "Adidas"

    def test_no_www(self) -> None:
        assert brand_fallback("", "https://patagonia.com/jackets") == "Patagonia"

    def test_empty_url(self) -> None:
        assert brand_fallback("", "") == ""


class TestBuildRecordIntegration:
    def test_brand_fallback_applied_in_build_algolia_record(self) -> None:
        record = build_algolia_record(
            url="https://www.acme.com/widget",
            title="Widget",
            category_name="Gadgets",
            category_url="https://www.acme.com/gadgets",
            product=None,
        )
        assert record.brand == "Acme"

    def test_brand_fallback_applied_in_listing_record(self) -> None:
        card = ProductListingCard(
            url="https://www.shopify-store.com/product",
            name="Test Product",
            brand="",
            category_url="https://www.shopify-store.com/category",
            category_name="Category",
        )
        record = build_listing_algolia_record(card)
        assert record.brand == "Shopify-store"
        assert record.citations
        assert record.citations[0]["source_url"] == "https://www.shopify-store.com/category"
        assert record.citations[0]["field"] == "name"

    def test_product_page_record_includes_citation(self) -> None:
        record = build_algolia_record(
            url="https://www.acme.com/widget",
            title="Widget",
            category_name="Gadgets",
            category_url="https://www.acme.com/gadgets",
            product=None,
        )

        assert record.citations
        assert record.citations[0]["source_id"]
        assert record.citations[0]["source_url"] == "https://www.acme.com/gadgets"
        assert record.citations[0]["claim"] == "Widget"

    def test_dedup_same_canonical_url(self) -> None:
        record1 = build_algolia_record(
            url="https://shop.com/shoes?variant=1",
            title="Shoe",
            category_name="",
            category_url="",
            product=None,
        )
        record2 = build_algolia_record(
            url="https://shop.com/shoes?variant=2",
            title="Shoe",
            category_name="",
            category_url="",
            product=None,
        )
        assert record1.objectID == record2.objectID
