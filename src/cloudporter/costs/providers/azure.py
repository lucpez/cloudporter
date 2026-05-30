import json
import urllib.parse
import urllib.request
from typing import Any
from urllib.error import URLError

from cloudporter.costs import PricingError

_PRICES_URL = "https://prices.azure.com/api/retail/prices"
_REGION = "swedencentral"


def get_hourly_price(identifier: str, variant: str) -> float:
    filter_expr = (
        f"armSkuName eq '{identifier}' and armRegionName eq '{_REGION}'"
        " and priceType eq 'Consumption'"
    )
    url = f"{_PRICES_URL}?{urllib.parse.urlencode({'$filter': filter_expr})}"

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data: dict[str, Any] = json.loads(resp.read())
    except URLError as exc:
        raise PricingError(f"failed to fetch Azure pricing data: {exc}") from exc

    is_windows = variant == "windows"
    items = [
        item
        for item in data.get("Items", [])
        if ("Windows" in item.get("productName", "")) == is_windows
        and item.get("unitOfMeasure") == "1 Hour"
        and "Spot" not in item.get("skuName", "")
        and "Low Priority" not in item.get("skuName", "")
    ]

    if not items:
        raise PricingError(f"price not found for {identifier!r} in {_REGION}")

    return float(items[0]["retailPrice"])
