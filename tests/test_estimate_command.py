from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from cloudporter.cli import app
from cloudporter.costs import PricingError
from cloudporter.costs.estimator import ResourceCost

runner = CliRunner()

VALID_MANIFEST = """\
name: my-app
resources:
  - name: web-server
    type: compute
    cpu: 2
    memory_gb: 4
    os: ubuntu-22.04
"""


def _manifest_file(tmp_path: Path) -> Path:
    f = tmp_path / "manifest.yaml"
    f.write_text(VALID_MANIFEST)
    return f


_WEB_COST = ResourceCost(
    name="web-server",
    resource_type="compute",
    monthly_cost={"aws": 30.37, "azure": 52.44},
)


def test_estimate_success(tmp_path: Path) -> None:
    with patch("cloudporter.cli._estimate", return_value=[_WEB_COST]):
        result = runner.invoke(app, ["estimate", str(_manifest_file(tmp_path))])
    assert result.exit_code == 0
    assert "web-server" in result.output
    assert "30.37" in result.output
    assert "52.44" in result.output
    assert "AWS" in result.output
    assert "AZURE" in result.output


def test_estimate_shows_cheaper_provider(tmp_path: Path) -> None:
    with patch("cloudporter.cli._estimate", return_value=[_WEB_COST]):
        result = runner.invoke(app, ["estimate", str(_manifest_file(tmp_path))])
    assert result.exit_code == 0
    assert "AWS" in result.output
    assert "cheaper" in result.output


def test_estimate_pricing_error(tmp_path: Path) -> None:
    err = PricingError("API unreachable")
    with patch("cloudporter.cli._estimate", side_effect=err):
        result = runner.invoke(app, ["estimate", str(_manifest_file(tmp_path))])
    assert result.exit_code == 1
    assert "API unreachable" in result.output


def test_estimate_file_not_found(tmp_path: Path) -> None:
    result = runner.invoke(app, ["estimate", str(tmp_path / "nonexistent.yaml")])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_estimate_multiple_resources(tmp_path: Path) -> None:
    costs = [
        ResourceCost(
            name="web",
            resource_type="compute",
            monthly_cost={"aws": 30.37, "azure": 52.44},
        ),  # noqa: E501
        ResourceCost(
            name="api",
            resource_type="compute",
            monthly_cost={"aws": 60.74, "azure": 104.88},
        ),  # noqa: E501
    ]
    with patch("cloudporter.cli._estimate", return_value=costs):
        result = runner.invoke(app, ["estimate", str(_manifest_file(tmp_path))])
    assert result.exit_code == 0
    assert "web" in result.output
    assert "api" in result.output
    assert "91.11" in result.output  # AWS total
    assert "157.32" in result.output  # Azure total
