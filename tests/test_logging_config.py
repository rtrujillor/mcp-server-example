import logging
from unittest.mock import Mock

import pytest

from product_assistant.logging_config import configure_logging


def test_configure_logging_uses_configured_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setattr(logging, "basicConfig", basic_config := Mock())

    configure_logging()

    assert basic_config.call_args.kwargs["level"] == logging.DEBUG
    assert basic_config.call_args.kwargs["force"] is True


def test_configure_logging_rejects_unknown_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LOG_LEVEL", "verbose")

    with pytest.raises(ValueError, match="Unsupported LOG_LEVEL 'VERBOSE'"):
        configure_logging()
