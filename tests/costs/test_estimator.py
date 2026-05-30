from typing import Any
from unittest.mock import patch

import pytest

from cloudporter.costs.estimator import estimate
from cloudporter.manifest.schema import Manifest


def _make_manifest(resources: list[dict[str, object]]) -> Manifest:
    return Manifest.model_validate({"name": "test-app", "resources": resources})


def _item(name: str, identifier: str, variant: str) -> dict[str, str]:
    return {
        "name": name,
        "type": "compute",
        "identifier": identifier,
        "variant": variant,
    }  # noqa: E501


def _mapping_side_effect(aws: list[dict[str, Any]], azure: list[dict[str, Any]]) -> Any:
    return lambda _m, p: aws if p == "aws" else azure


_COMPUTE = {"type": "compute", "cpu": 2, "memory_gb": 4, "os": "ubuntu-22.04"}
_COMPUTE_XL = {"type": "compute", "cpu": 4, "memory_gb": 8, "os": "ubuntu-22.04"}
_WINDOWS = {"type": "compute", "cpu": 2, "memory_gb": 4, "os": "windows-server-2022"}


def test_estimate_single_resource() -> None:
    manifest = _make_manifest([{"name": "srv", **_COMPUTE}])
    aws_map = [_item("srv", "t3.medium", "linux")]
    azure_map = [_item("srv", "Standard_B2s_v2", "linux")]

    with (
        patch(
            "cloudporter.costs.estimator._mapping",
            side_effect=_mapping_side_effect(aws_map, azure_map),
        ),  # noqa: E501
        patch("cloudporter.costs.estimator._aws.get_hourly_price", return_value=0.04),
        patch("cloudporter.costs.estimator._azure.get_hourly_price", return_value=0.08),
    ):
        result = estimate(manifest)

    assert len(result) == 1
    assert result[0].name == "srv"
    assert result[0].monthly_cost["aws"] == pytest.approx(0.04 * 730, rel=1e-3)
    assert result[0].monthly_cost["azure"] == pytest.approx(0.08 * 730, rel=1e-3)


def test_estimate_multiple_resources() -> None:
    manifest = _make_manifest(
        [{"name": "web", **_COMPUTE}, {"name": "api", **_COMPUTE_XL}]
    )  # noqa: E501
    aws_map = [_item("web", "t3.medium", "linux"), _item("api", "m5.xlarge", "linux")]
    azure_map = [
        _item("web", "Standard_B2s_v2", "linux"),
        _item("api", "Standard_B4s_v2", "linux"),
    ]

    with (
        patch(
            "cloudporter.costs.estimator._mapping",
            side_effect=_mapping_side_effect(aws_map, azure_map),
        ),  # noqa: E501
        patch("cloudporter.costs.estimator._aws.get_hourly_price", return_value=0.04),
        patch("cloudporter.costs.estimator._azure.get_hourly_price", return_value=0.08),
    ):
        result = estimate(manifest)

    assert len(result) == 2
    assert {r.name for r in result} == {"web", "api"}


def test_estimate_windows_resource() -> None:
    manifest = _make_manifest([{"name": "win", **_WINDOWS}])
    aws_map = [_item("win", "t3.medium", "windows")]
    azure_map = [_item("win", "Standard_B2s_v2", "windows")]

    with (
        patch(
            "cloudporter.costs.estimator._mapping",
            side_effect=_mapping_side_effect(aws_map, azure_map),
        ),  # noqa: E501
        patch(
            "cloudporter.costs.estimator._aws.get_hourly_price", return_value=0.09
        ) as aws_p,  # noqa: E501
        patch("cloudporter.costs.estimator._azure.get_hourly_price", return_value=0.17),
    ):
        result = estimate(manifest)

    aws_p.assert_called_once_with("t3.medium", "windows")
    assert result[0].monthly_cost["aws"] == pytest.approx(0.09 * 730, rel=1e-3)
