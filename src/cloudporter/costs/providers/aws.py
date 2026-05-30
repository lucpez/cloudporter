import json
import urllib.request
from typing import Any
from urllib.error import URLError

from cloudporter.costs import PricingError

_VANTAGE_EC2_URL = "https://instances.vantage.sh/instances.json"
_VANTAGE_RDS_URL = "https://instances.vantage.sh/rds/instances.json"
_REGION = "us-east-1"
_EC2_VARIANT_KEY = {"linux": "linux", "windows": "mswin"}
_RDS_VARIANT_KEY = {"mysql": "MySQL", "postgres": "PostgreSQL"}


def _fetch(url: str) -> list[dict[str, Any]]:
    req = urllib.request.Request(url, headers={"User-Agent": "cloudporter"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return list(json.loads(resp.read()))
    except URLError as exc:
        raise PricingError(f"failed to fetch AWS pricing data: {exc}") from exc


def _get_ec2_price(identifier: str, variant: str) -> float:
    os_key = _EC2_VARIANT_KEY.get(variant)
    if os_key is None:
        raise PricingError(f"unknown variant for AWS EC2 pricing: {variant!r}")
    for entry in _fetch(_VANTAGE_EC2_URL):
        if entry.get("instance_type") == identifier:
            try:
                return float(entry["pricing"][_REGION][os_key]["ondemand"])
            except (KeyError, TypeError, ValueError) as exc:
                raise PricingError(
                    f"price not found for {identifier!r} in {_REGION}"
                ) from exc
    raise PricingError(f"instance type {identifier!r} not found in pricing data")


def _get_rds_price(identifier: str, variant: str) -> float:
    engine_key = _RDS_VARIANT_KEY.get(variant)
    if engine_key is None:
        raise PricingError(f"unknown variant for AWS RDS pricing: {variant!r}")
    for entry in _fetch(_VANTAGE_RDS_URL):
        if entry.get("instance_type") == identifier:
            try:
                return float(entry["pricing"][_REGION][engine_key]["ondemand"])
            except (KeyError, TypeError, ValueError) as exc:
                raise PricingError(
                    f"price not found for {identifier!r} in {_REGION}"
                ) from exc
    raise PricingError(f"RDS instance class {identifier!r} not found in pricing data")


def get_hourly_price(identifier: str, variant: str) -> float:
    if identifier.startswith("db."):
        return _get_rds_price(identifier, variant)
    return _get_ec2_price(identifier, variant)
