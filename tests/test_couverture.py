"""La couverture et le contrôle entre fournisseurs."""

from __future__ import annotations

import pandas as pd
import pytest

from vic import controle, couverture, donnees, vwap


@pytest.fixture
def prepare(consolide, iex):
    return vwap.preparer(donnees.apparier(consolide, iex, depuis=consolide["seance"].min(), attendues=4))


def test_la_part_du_volume_se_calcule_a_la_main(prepare):
    """Six barres à dix actions contre huit barres à cent : 60 sur 800."""
    resultat = couverture.globale(prepare)
    assert resultat["part_du_volume"] == pytest.approx(60 / 800)


def test_la_part_des_minutes_compte_les_barres_et_non_les_actions(prepare):
    """Six minutes présentes sur huit, ce qui n'a rien à voir avec la part du volume."""
    resultat = couverture.globale(prepare)
    assert resultat["part_des_minutes"] == pytest.approx(6 / 8)
    assert resultat["minutes_muettes"] == 2


def test_les_seances_ecourtees_sont_retirees():
    """Une séance de trois heures et demie fausserait toute moyenne par séance."""
    complete = pd.DataFrame({"seance": ["a"] * donnees.BARRES_ATTENDUES})
    courte = pd.DataFrame({"seance": ["b"] * 210})
    table = pd.concat([complete, courte], ignore_index=True)
    assert donnees.seances_completes(table) == {"a"}


def test_le_controle_voit_deux_fournisseurs_identiques(consolide):
    """Confronter une série à elle-même doit donner un écart nul, sinon la mesure est fausse."""
    resultat = controle.confronter(consolide, consolide)
    assert resultat["ecart_de_prix_maximal_cents"] == pytest.approx(0.0)
    assert resultat["prix_identiques_au_dixieme_de_cent"] == pytest.approx(1.0)
    assert resultat["minutes_communes"] == len(consolide)


def test_le_controle_refuse_des_fenetres_disjointes(consolide):
    """Une comparaison sans minute commune ne mesurerait rien : elle doit échouer bruyamment."""
    decale = consolide.copy()
    decale["local"] = decale["local"] + pd.Timedelta(days=400)
    with pytest.raises(ValueError):
        controle.confronter(consolide, decale)
