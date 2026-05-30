import json
from unittest.mock import MagicMock, patch

import pytest

from cloudporter.costs import PricingError
from cloudporter.costs.providers.aws import get_hourly_price

_SAMPLE_DATA = [
    {
        "instance_type": "t3.medium",
        "pricing": {
            "us-east-1": {
                "linux": {"ondemand": "0.0416"},
                "mswin": {"ondemand": "0.0936"},
            }
        },
    }
]


def _mock_urlopen(data: object) -> MagicMock:
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    mock.read.return_value = json.dumps(data).encode()
    return mock


def test_linux_price() -> None:
    with patch("cloudporter.costs.providers.aws.urllib.request.urlopen") as mock:
        mock.return_value = _mock_urlopen(_SAMPLE_DATA)
        assert get_hourly_price("t3.medium", "linux") == pytest.approx(0.0416)


def test_windows_price() -> None:
    with patch("cloudporter.costs.providers.aws.urllib.request.urlopen") as mock:
        mock.return_value = _mock_urlopen(_SAMPLE_DATA)
        assert get_hourly_price("t3.medium", "windows") == pytest.approx(0.0936)


def test_instance_not_found() -> None:
    with patch("cloudporter.costs.providers.aws.urllib.request.urlopen") as mock:
        mock.return_value = _mock_urlopen([])
        with pytest.raises(PricingError, match="not found"):
            get_hourly_price("t3.nonexistent", "linux")


def test_unknown_variant() -> None:
    with pytest.raises(PricingError, match="unknown variant"):
        get_hourly_price("t3.medium", "bsd")


def test_network_error() -> None:
    from urllib.error import URLError

    with patch("cloudporter.costs.providers.aws.urllib.request.urlopen") as mock:
        mock.side_effect = URLError("connection refused")
        with pytest.raises(PricingError, match="failed to fetch"):
            get_hourly_price("t3.medium", "linux")
