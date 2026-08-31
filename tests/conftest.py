"""Deux séances fabriquées dont chaque réponse se calcule de tête.

Aucun test du dépôt ne touche au réseau ni aux barres réelles. Les prix sont choisis pour que les
prix moyens pondérés tombent sur des nombres ronds, si bien qu'une erreur de formule saute aux yeux
au lieu de se cacher derrière une décimale plausible.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest


def _seance(jour: str, prix: list[float], volumes: list[int]) -> pd.DataFrame:
    debut = pd.Timestamp(f"{jour} 09:30", tz="America/New_York")
    local = [debut + pd.Timedelta(minutes=k) for k in range(len(prix))]
    return pd.DataFrame({
        "local": local,
        "seance": [dt.date.fromisoformat(jour)] * len(prix),
        "cloture": prix,
        "volume": volumes,
        "prix_moyen": prix,
        "montant": [p * v for p, v in zip(prix, volumes, strict=True)],
    })


@pytest.fixture
def consolide() -> pd.DataFrame:
    """Deux séances de quatre minutes, prix qui monte puis prix qui descend."""
    return pd.concat([_seance("2024-01-02", [10.0, 12.0, 14.0, 16.0], [100, 100, 100, 100]),
                      _seance("2024-01-03", [20.0, 18.0, 16.0, 14.0], [100, 100, 100, 100])],
                     ignore_index=True)


@pytest.fixture
def iex(consolide: pd.DataFrame) -> pd.DataFrame:
    """Le même marché vu par une bourse qui rate la deuxième minute de chaque séance."""
    garde = consolide["local"].dt.minute % 4 != 31 % 4
    reduit = consolide[consolide.index % 4 != 1].copy()
    reduit["volume"] = 10
    reduit["montant"] = reduit["prix_moyen"] * reduit["volume"]
    assert bool(garde.any())
    return reduit.reset_index(drop=True)
