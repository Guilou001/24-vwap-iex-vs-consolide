"""Le prix moyen pondéré, vérifié sur des nombres qui se calculent de tête."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from vic import donnees, vwap


def test_la_moyenne_ponderee_se_calcule_a_la_main(consolide):
    """Sur des volumes égaux, la moyenne pondérée est la moyenne ordinaire des prix."""
    calculee = vwap.cumuler(consolide, "montant", "volume")
    attendues = [10.0, 11.0, 12.0, 13.0, 20.0, 19.0, 18.0, 17.0]
    assert list(np.round(calculee, 10)) == attendues


def test_la_moyenne_repart_a_chaque_seance(consolide):
    """La première minute d'une séance n'a qu'une observation, donc la moyenne vaut le prix."""
    calculee = vwap.cumuler(consolide, "montant", "volume")
    premieres = consolide.groupby("seance").head(1).index
    for i in premieres:
        assert calculee[i] == pytest.approx(consolide.loc[i, "prix_moyen"])


def test_le_prix_reporte_ne_franchit_pas_la_cloture(consolide):
    """Un flux muet à l'ouverture n'hérite pas du prix de la veille."""
    table = consolide.copy()
    table.loc[4, "cloture"] = np.nan
    reporte = vwap.prix_reporte(table, "cloture")
    assert bool(np.isnan(reporte.iloc[4]))
    assert reporte.iloc[3] == pytest.approx(16.0)


def test_les_minutes_absentes_laissent_la_moyenne_immobile(consolide, iex):
    """Une minute sans transaction chez IEX ne fait pas bouger sa moyenne pondérée."""
    apparie = donnees.apparier(consolide, iex, depuis=consolide["seance"].min(), attendues=4)
    prepare = vwap.preparer(apparie)
    muettes = ~prepare["presente_iex"]
    assert bool(muettes.any())
    for i in prepare.index[muettes]:
        if i > 0 and prepare.loc[i, "seance"] == prepare.loc[i - 1, "seance"]:
            assert prepare.loc[i, "moyenne_iex"] == pytest.approx(prepare.loc[i - 1, "moyenne_iex"])


def test_l_ecart_est_nul_quand_les_deux_flux_voient_la_meme_chose(consolide):
    """Le contrôle qui prouve que l'écart mesure une différence de flux et rien d'autre."""
    apparie = donnees.apparier(consolide, consolide, depuis=consolide["seance"].min(), attendues=4)
    ecarts = vwap.ecarts(vwap.preparer(apparie))
    assert float(ecarts["ecart_cents"].abs().max()) == pytest.approx(0.0, abs=1e-9)


def test_l_ecart_en_points_de_base_suit_le_niveau_du_prix():
    """Un même écart en cents pèse deux fois moins sur un titre deux fois plus cher."""
    table = pd.DataFrame({
        "local": pd.to_datetime(["2024-01-02 09:30", "2024-01-02 09:31"], utc=True),
        "seance": [pd.Timestamp("2024-01-02").date()] * 2,
        "moyenne_consolide": [100.0, 200.0],
        "moyenne_iex": [100.01, 200.01],
    })
    ecarts = vwap.ecarts(table)
    assert list(np.round(ecarts["ecart_cents"], 6)) == [1.0, 1.0]
    assert ecarts["ecart_pb"].iloc[0] == pytest.approx(2 * ecarts["ecart_pb"].iloc[1], rel=1e-3)


def test_l_echelle_compare_l_ecart_a_ce_que_le_signal_mesure(consolide, iex):
    """Un écart nul ne peut jamais faire basculer une décision, quelle que soit la distance."""
    from vic import divergence

    apparie = donnees.apparier(consolide, consolide, depuis=consolide["seance"].min(), attendues=4)
    resultat = divergence.echelle(vwap.preparer(apparie))
    assert resultat["ecart_median_pb"] == pytest.approx(0.0)
    assert resultat["part_ou_l_ecart_depasse_la_distance"] == pytest.approx(0.0)
    assert bool(iex is not None)
