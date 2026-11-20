"""Shared test helpers. Tests never use the network (plan 9.1)."""

from pathlib import Path

import pytest

from pfrt import config, detect

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures"


@pytest.fixture(scope="session")
def keywords():
    return detect.load_keywords(REPO / "config" / "keywords.csv")


@pytest.fixture(scope="session")
def sources():
    """The real sources.csv rows, by source_id."""
    states = config.load_states(REPO / "config" / "states.csv")
    rows = config.load_sources(REPO / "config" / "sources.csv", {s.state for s in states})
    return {s.source_id: s for s in rows}


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Fail loudly if any test tries to open a real connection."""
    import socket

    def guard(*args, **kwargs):
        raise RuntimeError("tests must not use the network")

    monkeypatch.setattr(socket, "create_connection", guard)
    monkeypatch.setattr(socket.socket, "connect", guard)
