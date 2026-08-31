"""Les cinq figures, confrontées aux tableaux qu'elles dessinent.

Chaque fabrique rend un dictionnaire de valeurs à côté de ses fichiers. Le test compare ce
dictionnaire au tableau donné en entrée, de sorte qu'une figure qui dériverait de ses données casse
un test au lieu de tromper le lecteur en silence. Aucun test n'ouvre le PNG : ce qui est vérifié,
c'est le nombre que la figure affirme, pas le pixel qui le porte.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

figures = pytest.importorskip("vic.figures")


def test_la_couverture_dessine_les_bornes_du_tableau(tmp_path):
    """Les minimums et le maximum affichés sont ceux des colonnes, convertis en pourcentage."""
    table = pd.DataFrame({
        "annee": [2021, 2022],
        "part_du_volume": [0.01, 0.02],
        "part_des_minutes": [0.80, 0.90],
        "symbole": ["QQQ", "QQQ"],
    })
    rendu = figures.couverture(table, dossier=tmp_path)["valeurs"]["QQQ"]
    assert rendu["volume_min"] == pytest.approx(1.0)
    assert rendu["volume_max"] == pytest.approx(2.0)
    assert rendu["minutes_min"] == pytest.approx(80.0)


def test_la_distribution_dessine_la_mediane_le_biais_et_le_hors_cadre(tmp_path):
    """Trois écarts dedans et un à cent cents : un quart de l'échantillon sort du cadre."""
    ecarts = {"QQQ": pd.DataFrame({"ecart_cents": [-2.0, 0.0, 4.0, 100.0]})}
    rendu = figures.distribution(ecarts, dossier=tmp_path)["valeurs"]["QQQ"]
    assert rendu["mediane_absolue"] == pytest.approx(3.0)
    assert rendu["biais"] == pytest.approx(25.5)
    assert rendu["part_hors_cadre"] == pytest.approx(0.25)


def test_les_moments_designent_la_pire_demi_heure(tmp_path):
    """La demi-heure nommée doit être celle qui porte le plus grand écart du tableau."""
    table = pd.DataFrame({
        "demi_heure": ["09h30", "12h00", "15h30"],
        "ecart_moyen_pb": [2.0, 3.0, 5.0],
        "symbole": ["QQQ"] * 3,
    })
    rendu = figures.moments(table, dossier=tmp_path)["valeurs"]["QQQ"]
    assert rendu["pire_moment"] == "15h30"
    assert rendu["pire_valeur_pb"] == pytest.approx(5.0)
    assert rendu["meilleure_valeur_pb"] == pytest.approx(2.0)


def test_les_versions_ne_dessinent_que_le_glissement_nul(tmp_path):
    """Filtrer sur un autre glissement changerait les barres sans changer le titre."""
    lignes = []
    for glissement, sharpe in ((0.0, 1.6), (0.25, 0.9)):
        for version in ("consolidé", "prix consolidé, moyenne IEX",
                        "prix IEX, moyenne consolidée", "IEX"):
            lignes.append({"version": version, "sharpe": sharpe, "symbole": "QQQ",
                           "glissement_cents": glissement})
    rendu = figures.versions(pd.DataFrame(lignes), dossier=tmp_path)["valeurs"]["QQQ"]
    assert set(rendu) == {"consolidé", "prix consolidé, moyenne IEX",
                          "prix IEX, moyenne consolidée", "IEX"}
    assert all(v == pytest.approx(1.6) for v in rendu.values())


def test_les_desaccords_dessinent_les_trois_parts_en_pourcentage(tmp_path):
    """Les hauteurs des trois barres sont les trois colonnes, multipliées par cent."""
    table = pd.DataFrame([{"symbole": "QQQ", "part_accord": 0.96, "part_contresens": 0.03,
                           "part_silence": 0.0007}])
    rendu = figures.desaccords(table, dossier=tmp_path)["valeurs"]["QQQ"]
    assert rendu["part_accord"] == pytest.approx(96.0)
    assert rendu["part_contresens"] == pytest.approx(3.0)
    assert rendu["part_silence"] == pytest.approx(0.07)


def test_chaque_fabrique_ecrit_ses_deux_fichiers(tmp_path):
    """Une figure qui ne s'enregistre pas ne se verrait qu'à la relecture du README."""
    ecarts = {"QQQ": pd.DataFrame({"ecart_cents": np.array([-1.0, 1.0])})}
    chemins = figures.distribution(ecarts, dossier=tmp_path)["chemins"]
    suffixes = sorted(str(c).rsplit(".", 1)[-1] for c in chemins)
    assert suffixes == ["pdf", "png"]
