"""Smoke test — validates project setup."""


def test_import_src():
    import src  # noqa: F401


def test_import_nodes():
    import src.nodes  # noqa: F401


def test_import_utils():
    import src.utils  # noqa: F401
