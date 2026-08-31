"""Le signal, ses quatre versions et la mesure des désaccords."""

from __future__ import annotations

import numpy as np
import pytest

from vic import donnees, signaux, vwap


@pytest.fixture
def prepare(consolide, iex):
    return vwap.preparer(donnees.apparier(consolide, iex, depuis=consolide["seance"].min(), attendues=4))


def test_la_position_vient_de_la_minute_precedente(prepare):
    """Sans ce décalage, la stratégie achèterait au prix qu'elle vient d'observer."""
    tenue = signaux.positions(prepare, "prix_consolide", "moyenne_consolide")
    premieres = prepare.groupby("seance").head(1).index
    for i in premieres:
        assert tenue[i] == 0.0


def test_le_prix_egale_sa_propre_moyenne_a_la_premiere_minute(prepare):
    """La comparaison de 9 h 31 tombe à zéro : la position ne se prend qu'à 9 h 32.

    Ce n'est pas un défaut du code, c'est une propriété de la définition : à la première minute la
    moyenne pondérée n'a qu'une observation, donc elle vaut le prix lui-même.
    """
    signal = np.sign(prepare["prix_consolide"] - prepare["moyenne_consolide"])
    premieres = prepare.groupby("seance").head(1).index
    for i in premieres:
        assert signal[i] == 0.0


def test_une_tendance_qui_monte_donne_une_position_acheteuse(prepare):
    """Le contrôle le plus simple : sur une séance qui monte, le signal reste acheteur."""
    tenue = signaux.positions(prepare, "prix_consolide", "moyenne_consolide")
    montante = prepare["seance"] == prepare["seance"].min()
    apres_la_premiere = montante & (tenue.index > prepare.index[montante][1])
    assert (tenue[apres_la_premiere] == 1.0).all()


def test_le_rendement_encaisse_est_celui_du_vrai_marche(prepare):
    """Quel que soit le flux qui décide, le rendement vient du prix consolidé."""
    r = signaux.rendements_du_marche(prepare)
    attendu = 12.0 / 10.0 - 1.0
    assert r.iloc[1] == pytest.approx(attendu)
    assert r.iloc[4] == pytest.approx(0.0)


def test_les_deux_flux_identiques_ne_produisent_aucun_desaccord(consolide):
    """Le contrôle qui prouve que la mesure de désaccord mesure bien le flux."""
    prepare = vwap.preparer(donnees.apparier(consolide, consolide,
                                             depuis=consolide["seance"].min(), attendues=4))
    resultat = signaux.desaccords(prepare)
    assert resultat["part_contresens"] == pytest.approx(0.0)
    assert resultat["part_silence"] == pytest.approx(0.0)


def test_le_glissement_ne_peut_pas_augmenter_le_rendement(prepare):
    """Facturer un coût doit faire baisser le résultat, jamais l'inverse."""
    sans = signaux.rejouer(prepare, "prix_consolide", "moyenne_consolide", "test", 0.0)
    avec = signaux.rejouer(prepare, "prix_consolide", "moyenne_consolide", "test", 1.0)
    assert avec.rendement_total <= sans.rendement_total


def test_les_quatre_versions_sont_bien_quatre(prepare):
    """Une combinaison omise passerait autrement inaperçue."""
    table = signaux.toutes_les_versions(prepare)
    assert len(table) == 4
    assert set(table["version"]) == set(signaux.VERSIONS)
