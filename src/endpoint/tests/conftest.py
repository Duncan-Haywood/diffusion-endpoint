import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--integration",
        action="store_true",
        dest="integration",
        default=False,
        help="enable integration decorated tests",
    )
    parser.addoption(
        "--docker",
        action="store_true",
        dest="docker",
        default=False,
        help="enable docker decorated tests",
    )
