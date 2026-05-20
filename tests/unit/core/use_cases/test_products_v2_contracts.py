from scout.core.use_cases.products_v2 import ProductRecord, ProductVariantRecord


def test_product_record_contract() -> None:
    product = ProductRecord(
        objectID="esteelauder_643_141225",
        brand="Estee Lauder",
        name="Double Wear",
        subtitle="Stay-in-Place Longwear Matte Foundation",
        url=(
            "https://www.esteelauder.com/product/643/141225/product-catalog/makeup/"
            "face/foundation/double-wear/stay-in-place-longwear-matte-foundation"
        ),
        category="Makeup",
        price=52.0,
        currency="USD",
        colors=["3N1 Ivory Beige"],
        variants=[
            ProductVariantRecord(name="3N1 Ivory Beige", color="3N1 Ivory Beige", size="1.0 oz.")
        ],
    )

    assert product.price == 52.0
    assert product.variants[0].size == "1.0 oz."
