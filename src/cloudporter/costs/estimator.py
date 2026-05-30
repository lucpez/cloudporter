from dataclasses import dataclass, field

from cloudporter.costs import PricingError as PricingError  # re-export
from cloudporter.costs.providers import aws as _aws
from cloudporter.costs.providers import azure as _azure
from cloudporter.manifest.schema import Manifest
from cloudporter.translator.translate import mapping as _mapping

_HOURS_PER_MONTH = 730
_PROVIDERS = {"aws": _aws, "azure": _azure}


@dataclass
class ResourceCost:
    name: str
    resource_type: str
    monthly_cost: dict[str, float] = field(default_factory=dict)


def estimate(manifest: Manifest) -> list[ResourceCost]:
    costs: dict[str, ResourceCost] = {}

    for provider_name, provider_module in _PROVIDERS.items():
        for item in _mapping(manifest, provider_name):
            name = item["name"]
            if name not in costs:
                costs[name] = ResourceCost(name=name, resource_type=item["type"])
            hourly = provider_module.get_hourly_price(
                item["identifier"], item["variant"]
            )
            costs[name].monthly_cost[provider_name] = round(
                hourly * _HOURS_PER_MONTH, 2
            )

    return list(costs.values())
