import json
import urllib.parse
import urllib.request
from typing import Any
from urllib.error import URLError

from cloudporter.costs import PricingError

_PRICES_URL = "https://prices.azure.com/api/retail/prices"
_REGION = "swedencentral"

_DB_SERVICE_NAME = {
    "mysql": "Azure Database for MySQL",
    "postgres": "Azure Database for PostgreSQL",
}


def _fetch_prices(filter_expr: str) -> list[dict[str, Any]]:
    url = f"{_PRICES_URL}?{urllib.parse.urlencode({'$filter': filter_expr})}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data: dict[str, Any] = json.loads(resp.read())
    except URLError as exc:
        raise PricingError(f"failed to fetch Azure pricing data: {exc}") from exc
    return list(data.get("Items", []))


def _get_vm_price(identifier: str, variant: str) -> float:
    filter_expr = (
        f"armSkuName eq '{identifier}' and armRegionName eq '{_REGION}'"
        " and priceType eq 'Consumption'"
    )
    is_windows = variant == "windows"
    items = [
        item
        for item in _fetch_prices(filter_expr)
        if ("Windows" in item.get("productName", "")) == is_windows
        and item.get("unitOfMeasure") == "1 Hour"
        and "Spot" not in item.get("skuName", "")
        and "Low Priority" not in item.get("skuName", "")
    ]
    if not items:
        raise PricingError(f"price not found for {identifier!r} in {_REGION}")
    return float(items[0]["retailPrice"])


def _get_db_price(identifier: str, variant: str) -> float:
    service = _DB_SERVICE_NAME.get(variant)
    if service is None:
        raise PricingError(f"unknown database engine for Azure pricing: {variant!r}")
    filter_expr = (
        f"armSkuName eq '{identifier}' and armRegionName eq '{_REGION}'"
        f" and priceType eq 'Consumption' and serviceName eq '{service}'"
    )
    items = [
        item
        for item in _fetch_prices(filter_expr)
        if item.get("unitOfMeasure") == "1 Hour"
        and "Spot" not in item.get("skuName", "")
    ]
    if not items:
        raise PricingError(
            f"price not found for {identifier!r} ({variant}) in {_REGION}"
        )
    return float(items[0]["retailPrice"])


def get_hourly_price(identifier: str, variant: str) -> float:
    if variant in _DB_SERVICE_NAME:
        return _get_db_price(identifier, variant)
    return _get_vm_price(identifier, variant)
