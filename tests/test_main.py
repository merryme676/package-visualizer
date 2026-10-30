"""Тесты для инструмента визуализации."""

import sys
from unittest.mock import patch

sys.path.insert(0, "src")
from main import parse_args  # noqa: E402


def test_parse_required_args():
    """Проверка разбора основных аргументов."""
    with patch(
        "sys.argv", ["main.py", "--package", "Test", "--version", "1.0"]
    ):
        args = parse_args()
        assert args.package == "Test"
        assert args.version == "1.0"


def test_ascii_flag():
    """Проверка флага --ascii."""
    with patch("sys.argv", ["main.py", "--ascii"]):
        args = parse_args()
        assert args.ascii is True


def test_default_values():
    """Проверка, что по умолчанию аргументы пустые."""
    with patch("sys.argv", ["main.py"]):
        args = parse_args()
        assert args.package is None
        assert args.ascii is False
