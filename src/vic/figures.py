"""Les cinq figures, chacune rendant les nombres qu'elle dessine.

Une fabrique qui rend ses nombres est testable : le test compare ce que la figure affirme à ce que
les tableaux disent, et une figure qui dérive de ses données casse le test au lieu de tromper le
lecteur en silence.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gvf.style import appliquer, enregistrer

FIGURES = Path("results/figures")


def _ouvrir(*args, **kwargs):
    appliquer()
    return plt.subplots(*args, **kwargs)


def couverture(par_annee: pd.DataFrame, dossier: Path = FIGURES) -> dict:
    """La part du volume et la part des minutes, année par année, dans deux volets.

    Deux volets et non deux axes sur un même graphique : les deux grandeurs n'ont ni la même échelle
    ni le même sens, et les superposer suggérerait une relation que rien n'établit.
    """
    fig, (g, d) = _ouvrir(1, 2, figsize=(11, 4.2))
    rendus = {}
    for symbole, bloc in par_annee.groupby("symbole"):
        bloc = bloc.sort_values("annee")
        g.plot(bloc["annee"], 100 * bloc["part_du_volume"], marker="o", label=symbole)
        d.plot(bloc["annee"], 100 * bloc["part_des_minutes"], marker="o", label=symbole)
        rendus[symbole] = {"volume_min": float(100 * bloc["part_du_volume"].min()),
                           "volume_max": float(100 * bloc["part_du_volume"].max()),
                           "minutes_min": float(100 * bloc["part_des_minutes"].min())}
    g.set_ylabel("part du volume consolidé, en pourcentage")
    g.set_title("Ce qu'IEX capte du volume")
    d.set_ylabel("part des minutes avec au moins une transaction, en pourcentage")
    d.set_title("Ce qu'IEX voit des minutes")
    d.set_ylim(0, 102)
    for axe in (g, d):
        axe.set_xlabel("année")
        axe.legend()
    return {"chemins": enregistrer(fig, dossier, "couverture"), "valeurs": rendus}


def distribution(par_symbole: dict[str, pd.DataFrame], dossier: Path = FIGURES) -> dict:
    """La densité de l'écart entre les deux moyennes pondérées, en cents.

    L'axe est coupé à cinquante cents de part et d'autre : au-delà, la queue est trop fine pour se
    voir et écraserait tout le reste. La part des minutes hors cadre est écrite sur la figure.
    """
    fig, axe = _ouvrir(figsize=(9, 4.6))
    rendus = {}
    borne = 50.0
    for symbole, ecarts in par_symbole.items():
        e = ecarts["ecart_cents"].to_numpy()
        dedans = np.abs(e) <= borne
        axe.hist(e[dedans], bins=200, density=True, histtype="step", linewidth=1.6, label=symbole)
        rendus[symbole] = {"mediane_absolue": float(np.median(np.abs(e))),
                           "biais": float(e.mean()),
                           "part_hors_cadre": float(1.0 - dedans.mean())}
    axe.axvline(0.0, color="0.4", linewidth=0.9)
    axe.set_xlabel("moyenne pondérée IEX moins moyenne pondérée consolidée, en cents")
    axe.set_ylabel("densité")
    hors = ", ".join(f"{s} : {100 * v['part_hors_cadre']:.1f} %" for s, v in rendus.items())
    axe.set_title(f"L'écart entre les deux prix moyens, hors cadre au-delà de 50 cents ({hors})")
    axe.legend()
    return {"chemins": enregistrer(fig, dossier, "distribution"), "valeurs": rendus}


def moments(par_moment: pd.DataFrame, dossier: Path = FIGURES) -> dict:
    """L'écart moyen selon la demi-heure, en points de base."""
    fig, axe = _ouvrir(figsize=(9.5, 4.4))
    rendus = {}
    for symbole, bloc in par_moment.groupby("symbole"):
        axe.plot(bloc["demi_heure"], bloc["ecart_moyen_pb"], marker="o", label=symbole)
        rendus[symbole] = {"pire_moment": str(bloc.loc[bloc["ecart_moyen_pb"].idxmax(),
                                                       "demi_heure"]),
                           "pire_valeur_pb": float(bloc["ecart_moyen_pb"].max()),
                           "meilleure_valeur_pb": float(bloc["ecart_moyen_pb"].min())}
    axe.set_xlabel("demi-heure de la séance, heure de New York")
    axe.set_ylabel("écart absolu moyen, en points de base")
    axe.set_title("L'écart se creuse à mesure que la séance avance")
    axe.legend()
    return {"chemins": enregistrer(fig, dossier, "moments"), "valeurs": rendus}


def versions(signaux: pd.DataFrame, dossier: Path = FIGURES) -> dict:
    """Le ratio de Sharpe des quatre versions, par symbole, sans glissement.

    Les deux versions croisées se placent entre les deux versions pures quand l'erreur d'une seule
    grandeur suffit à expliquer l'écart. Le lecteur voit donc d'un coup d'œil laquelle des deux, du
    prix ou de la moyenne, porte l'erreur.
    """
    sans_frais = signaux[signaux["glissement_cents"] == 0.0]
    ordre = ["consolidé", "prix consolidé, moyenne IEX", "prix IEX, moyenne consolidée", "IEX"]
    fig, axe = _ouvrir(figsize=(10, 4.8))
    symboles = sorted(sans_frais["symbole"].unique())
    largeur = 0.8 / len(symboles)
    rendus = {}
    for k, symbole in enumerate(symboles):
        bloc = sans_frais[sans_frais["symbole"] == symbole].set_index("version").loc[ordre]
        positions = np.arange(len(ordre)) + (k - (len(symboles) - 1) / 2) * largeur
        axe.bar(positions, bloc["sharpe"], width=largeur, label=symbole)
        rendus[symbole] = {nom: float(v) for nom, v in bloc["sharpe"].items()}
    axe.set_xticks(np.arange(len(ordre)))
    axe.set_xticklabels(["tout consolidé", "prix consolidé\nmoyenne IEX",
                         "prix IEX\nmoyenne consolidée", "tout IEX"])
    axe.set_ylabel("ratio de Sharpe, sans glissement")
    axe.set_title("D'où vient l'erreur : du prix, ou du prix moyen ?")
    axe.legend()
    return {"chemins": enregistrer(fig, dossier, "versions"), "valeurs": rendus}


def desaccords(table: pd.DataFrame, dossier: Path = FIGURES) -> dict:
    """La part des minutes en accord, en contresens et en silence.

    L'échelle est logarithmique : l'accord dépasse 96 % et le silence n'atteint pas un dixième de
    pour cent, si bien qu'une échelle ordinaire rendrait les deux petites barres invisibles.
    """
    fig, axe = _ouvrir(figsize=(8.5, 4.2))
    categories = [("part_accord", "même position"), ("part_contresens", "positions opposées"),
                  ("part_silence", "IEX n'a rien vu")]
    symboles = list(table["symbole"])
    largeur = 0.8 / len(symboles)
    rendus = {}
    for k, symbole in enumerate(symboles):
        ligne = table[table["symbole"] == symbole].iloc[0]
        valeurs = [100 * float(ligne[c]) for c, _ in categories]
        positions = np.arange(len(categories)) + (k - (len(symboles) - 1) / 2) * largeur
        barres = axe.bar(positions, valeurs, width=largeur, label=symbole)
        axe.bar_label(barres, fmt="%.2f", padding=2, fontsize=8)
        rendus[symbole] = dict(zip([c for c, _ in categories], valeurs, strict=True))
    axe.set_yscale("log")
    axe.set_xticks(np.arange(len(categories)))
    axe.set_xticklabels([libelle for _, libelle in categories])
    axe.set_ylabel("part des minutes, en pourcentage, échelle logarithmique")
    axe.set_title("Ce qui sépare les deux versions du signal, minute par minute")
    axe.legend()
    return {"chemins": enregistrer(fig, dossier, "desaccords"), "valeurs": rendus}
