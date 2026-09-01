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


@pytest.fixture
def premiere_minute_decidable():
    """Une séance dont le prix moyen de chaque barre diffère de sa clôture, comme sur le vrai marché.

    Les clôtures valent 10, 11, 12 et 13, les prix moyens 9,50, 10,50, 11,50 et 12,50. La moyenne
    pondérée de la première minute vaut donc 9,50 et non 10 : c'est le prix moyen de la barre, jamais
    sa clôture. Le gabarit ordinaire du dépôt pose les deux égaux, si bien qu'il ne peut pas voir la
    différence.
    """
    import datetime as dt

    import pandas as pd

    debut = pd.Timestamp("2024-02-05 09:30", tz="America/New_York")
    cloture = [10.0, 11.0, 12.0, 13.0]
    prix_moyen = [9.5, 10.5, 11.5, 12.5]
    table = pd.DataFrame({
        "local": [debut + pd.Timedelta(minutes=k) for k in range(4)],
        "seance": [dt.date(2024, 2, 5)] * 4,
        "cloture": cloture,
        "volume": [100] * 4,
        "prix_moyen": prix_moyen,
        "montant": [p * 100 for p in prix_moyen],
    })
    return vwap.preparer(donnees.apparier(table, table, depuis=dt.date(2024, 2, 5), attendues=4))


def test_la_premiere_minute_compare_deux_grandeurs_differentes(premiere_minute_decidable):
    """Le prix n'égale pas sa propre moyenne pondérée à la première minute, et le décalage suffit.

    La moyenne pondérée de la première minute est le prix moyen de la barre, 9,50, quand le signal
    compare la clôture, 10. La comparaison rend donc +1 et non 0. Si la position reste nulle, c'est
    parce que la minute t décide de la minute t+1 et qu'aucune minute ne précède l'ouverture.
    """
    signal = np.sign(premiere_minute_decidable["prix_consolide"]
                     - premiere_minute_decidable["moyenne_consolide"])
    tenue = signaux.positions(premiere_minute_decidable, "prix_consolide", "moyenne_consolide")
    assert premiere_minute_decidable["moyenne_consolide"].iloc[0] == pytest.approx(9.5)
    assert signal.iloc[0] == 1.0
    assert tenue.iloc[0] == 0.0


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


@pytest.fixture
def croisement():
    """Une séance dont le prix passe au-dessus puis au-dessous de sa moyenne pondérée.

    Les quatre prix sont 10, 14, 6 et 10, à volume constant, donc la moyenne pondérée vaut 10, 12,
    10 et 10. Le signe de la distance se lit de tête, 0, +1, -1 et 0, et il change deux fois : c'est
    ce changement qui rend le décalage d'une minute visible dans le résultat.
    """
    import datetime as dt

    import pandas as pd

    debut = pd.Timestamp("2024-02-05 09:30", tz="America/New_York")
    prix = [10.0, 14.0, 6.0, 10.0]
    table = pd.DataFrame({
        "local": [debut + pd.Timedelta(minutes=k) for k in range(4)],
        "seance": [dt.date(2024, 2, 5)] * 4,
        "cloture": prix,
        "volume": [100] * 4,
        "prix_moyen": prix,
        "montant": [p * 100 for p in prix],
    })
    return vwap.preparer(donnees.apparier(table, table, depuis=dt.date(2024, 2, 5), attendues=4))


def test_la_position_est_celle_decidee_a_la_minute_davant(croisement):
    """Le contrôle qui casse dès que le décalage d'une minute disparaît ou change de longueur.

    Le signe de la distance vaut 0, +1, -1 puis 0. La position tenue est donc ce signe repoussé
    d'une minute, soit 0, 0, +1 puis -1. Sans décalage elle vaudrait 0, +1, -1 puis 0, ce qui
    donnerait à la stratégie le prix de la minute qu'elle est en train de regarder.
    """
    tenue = signaux.positions(croisement, "prix_consolide", "moyenne_consolide")
    assert list(tenue) == [0.0, 0.0, 1.0, -1.0]


def test_le_rendement_sans_glissement_se_calcule_a_la_main(croisement):
    """Les positions 0, 0, +1 puis -1 sur les rendements 0, +2/5, -4/7 puis +2/3.

    Les deux minutes qui portent une position rapportent donc -4/7 puis -2/3, soit un capital
    multiplié par 3/7 puis par 1/3, et le total ressort à 1/7 moins un.
    """
    resultat = signaux.rejouer(croisement, "prix_consolide", "moyenne_consolide", "test", 0.0)
    assert resultat.rendement_total == pytest.approx(1 / 7 - 1.0)


def test_le_glissement_est_facture_au_cent_pres(croisement):
    """Un aller-retour coûte deux fois le glissement, et le compte se fait à la main.

    Les changements de position valent 0, 0, 1 puis 2, et le glissement d'un cent se rapporte au
    prix de la minute, 6 dollars puis 10. Le coût est donc de 0,01/6 à la troisième minute et de
    0,02/10 à la quatrième. Un coût facturé de travers, moitié moins par exemple, se voit ici.
    """
    resultat = signaux.rejouer(croisement, "prix_consolide", "moyenne_consolide", "test", 1.0)
    attendu = (1.0 - 4.0 / 7.0 - 0.01 / 6.0) * (1.0 - 2.0 / 3.0 - 0.02 / 10.0) - 1.0
    assert resultat.rendement_total == pytest.approx(attendu)


def test_les_changements_par_jour_comptent_les_allers_retours(croisement):
    """Trois unités de position échangées sur une séance font 1,5 changement, pas 3.

    Passer de 0 à +1 puis de +1 à -1 fait bouger la position de 1 puis de 2 unités. Un aller-retour
    complet vaut deux unités, donc le compte de changements se divise par deux.
    """
    resultat = signaux.rejouer(croisement, "prix_consolide", "moyenne_consolide", "test", 0.0)
    assert resultat.changements_par_jour == pytest.approx(3.0 / 2.0)


def test_la_volatilite_est_annualisee_sur_les_minutes_de_seance(croisement):
    """Une année compte 252 séances de 390 minutes, et non 252 minutes.

    Prendre 252 au lieu de 252 x 390 diviserait toutes les volatilités publiées par 1,24 et
    multiplierait d'autant les quatre ratios de Sharpe.
    """
    resultat = signaux.rejouer(croisement, "prix_consolide", "moyenne_consolide", "test", 0.0)
    nets = [0.0, 0.0, -4.0 / 7.0, -2.0 / 3.0]
    attendu = float(np.std(nets, ddof=1) * np.sqrt(252 * 390))
    assert resultat.volatilite == pytest.approx(attendu)


def test_les_quatre_parts_des_desaccords_somment_a_un(prepare):
    """La première minute de séance ne décide rien : sans sa part, le lecteur perd 0,26 %."""
    r = signaux.desaccords(prepare)
    total = r["part_accord"] + r["part_silence"] + r["part_contresens"] + r["part_aucune_position"]
    assert total == pytest.approx(1.0)


def test_une_seance_entierement_muette_est_comptee_comme_telle(consolide, iex):
    """Une journée sans aucune barre IEX est une panne, pas un retard de quelques minutes.

    La première séance est retirée du flux IEX en entier. Le silence total passe alors à trois
    minutes, dont deux viennent de cette panne et une seule du trou ordinaire de la seconde séance.
    Sans la décomposition, les trois se liraient comme trois retards à l'ouverture.
    """
    amputee = iex[iex["seance"] != iex["seance"].min()]
    prepare = vwap.preparer(donnees.apparier(consolide, amputee,
                                             depuis=consolide["seance"].min(), attendues=4))
    r = signaux.desaccords(prepare)
    assert r["seances_entierement_muettes"] == 1
    assert r["minutes_de_silence"] == 3
    assert r["minutes_de_silence_hors_seances_muettes"] == 1
