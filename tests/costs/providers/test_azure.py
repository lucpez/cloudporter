import json
from unittest.mock import MagicMock, patch

import pytest

from cloudporter.costs import PricingError
from cloudporter.costs.providers.azure import get_hourly_price

_LINUX_ITEM = {
    "retailPrice": 0.0832,
    "productName": "Virtual Machines Bsv2 Series",
    "skuName": "Standard_B2s_v2",
    "unitOfMeasure": "1 Hour",
}
_WINDOWS_ITEM = {
    "retailPrice": 0.1664,
    "productName": "Virtual Machines Bsv2 Series Windows",
    "skuName": "Standard_B2s_v2",
    "unitOfMeasure": "1 Hour",
}


def _mock_urlopen(items: list[object]) -> MagicMock:
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    mock.read.return_value = json.dumps({"Items": items}).encode()
    return mock


def test_linux_price() -> None:
    with patch("cloudporter.costs.providers.azure.urllib.request.urlopen") as mock:
        mock.return_value = _mock_urlopen([_LINUX_ITEM, _WINDOWS_ITEM])
        assert get_hourly_price("Standard_B2s_v2", "linux") == pytest.approx(0.0832)


def test_windows_price() -> None:
    with patch("cloudporter.costs.providers.azure.urllib.request.urlopen") as mock:
        mock.return_value = _mock_urlopen([_LINUX_ITEM, _WINDOWS_ITEM])
        assert get_hourly_price("Standard_B2s_v2", "windows") == pytest.approx(0.1664)


def test_spot_filtered_out() -> None:
    spot_item = {**_LINUX_ITEM, "skuName": "Standard_B2s_v2 Spot"}
    with patch("cloudporter.costs.providers.azure.urllib.request.urlopen") as mock:
        mock.return_value = _mock_urlopen([spot_item])
        with pytest.raises(PricingError, match="not found"):
            get_hourly_price("Standard_B2s_v2", "linux")


def test_no_results() -> None:
    with patch("cloudporter.costs.providers.azure.urllib.request.urlopen") as mock:
        mock.return_value = _mock_urlopen([])
        with pytest.raises(PricingError, match="not found"):
            get_hourly_price("Standard_B2s_v2", "linux")


def test_network_error() -> None:
    from urllib.error import URLError

    with patch("cloudporter.costs.providers.azure.urllib.request.urlopen") as mock:
        mock.side_effect = URLError("timeout")
        with pytest.raises(PricingError, match="failed to fetch"):
            get_hourly_price("Standard_B2s_v2", "linux")
