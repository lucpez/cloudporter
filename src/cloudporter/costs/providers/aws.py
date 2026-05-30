import json
import urllib.request
from typing import Any
from urllib.error import URLError

from cloudporter.costs import PricingError

_VANTAGE_URL = "https://instances.vantage.sh/instances.json"
_REGION = "us-east-1"
_VARIANT_KEY = {"linux": "linux", "windows": "mswin"}


def get_hourly_price(identifier: str, variant: str) -> float:
    os_key = _VARIANT_KEY.get(variant)
    if os_key is None:
        raise PricingError(f"unknown variant for AWS pricing: {variant!r}")

    req = urllib.request.Request(_VANTAGE_URL, headers={"User-Agent": "cloudporter"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data: list[dict[str, Any]] = json.loads(resp.read())
    except URLError as exc:
        raise PricingError(f"failed to fetch AWS pricing data: {exc}") from exc

    for entry in data:
        if entry.get("instance_type") == identifier:
            try:
                return float(entry["pricing"][_REGION][os_key]["ondemand"])
            except (KeyError, TypeError, ValueError) as exc:
                raise PricingError(
                    f"price not found for {identifier!r} in {_REGION}"
                ) from exc

    raise PricingError(f"instance type {identifier!r} not found in pricing data")
