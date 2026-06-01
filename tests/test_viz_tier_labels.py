"""Tier-accurate figure labels for seed vs archival compendium."""

from __future__ import annotations

import os

os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from src.viz import panels, style


def test_archival_panel_titles_use_archival_phrasing(archival_compendium, monkeypatch):
    monkeypatch.setenv("GRATEFUL_DATA_TIER", "archival")
    comp = archival_compendium
    fig, ax = plt.subplots()
    panels.draw_top_songs(ax, comp)
    assert "archival" in ax.get_title().lower()
    assert "seed" not in ax.get_title().lower()
    plt.close(fig)

    fig, ax = plt.subplots()
    panels.draw_sentiment_by_kind(ax, comp)
    assert "curated overlay" in ax.get_title().lower()
    plt.close(fig)


def test_archival_provenance_footer(archival_compendium, monkeypatch):
    monkeypatch.setenv("GRATEFUL_DATA_TIER", "archival")
    text = style.provenance_text(archival_compendium)
    assert "archival compendium" in text
    assert "ingested shows" in text
    assert str(len(archival_compendium.shows)) in text


def test_seed_provenance_footer(compendium, monkeypatch):
    monkeypatch.delenv("GRATEFUL_DATA_TIER", raising=False)
    text = style.provenance_text(compendium, tier="seed")
    assert "curated real shows" in text


def test_seed_panel_titles_use_seed_phrasing(compendium, monkeypatch):
    monkeypatch.delenv("GRATEFUL_DATA_TIER", raising=False)
    fig, ax = plt.subplots()
    panels.draw_top_songs(ax, compendium)
    assert "seed" in ax.get_title().lower()
    plt.close(fig)
