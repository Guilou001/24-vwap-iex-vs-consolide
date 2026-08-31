"""De combien les deux moyennes pondérées s'écartent, et quand l'écart est le plus grand.

La question se pose en deux temps. D'abord la distribution : un écart médian de quelques dixièmes de
cent ne gêne personne, un écart qui atteint plusieurs cents un jour sur vingt en gêne beaucoup. Puis
le moment : si l'écart se concentre à l'ouverture, quand les volumes sont énormes et les trous rares,
il pèse peu ; s'il se concentre en fin de séance, quand un signal de suivi de tendance décide de
sortir, il pèse lourd.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

QUANTILES = (0.5, 0.75, 0.9, 0.95, 0.99, 1.0)


def distribution(ecarts: pd.DataFrame) -> pd.DataFrame:
    """Les quantiles de l'écart en valeur absolue, dans les deux unités."""
    lignes = []
    for q in QUANTILES:
        lignes.append({
            "quantile": q,
            "ecart_cents": float(np.quantile(ecarts["ecart_cents"].abs(), q)),
            "ecart_pb": float(np.quantile(ecarts["ecart_pb"].abs(), q)),
        })
    return pd.DataFrame(lignes)


def resume(ecarts: pd.DataFrame) -> dict:
    """Le biais moyen et la dispersion, plus la part des minutes au-delà d'un cent.

    Le biais est mesuré signé et non en valeur absolue : un flux qui se trompe toujours dans le même
    sens ne pose pas le même problème qu'un flux qui bruite symétriquement, parce que le premier
    décale tous les signaux du même côté.
    """
    e = ecarts["ecart_cents"].to_numpy()
    return {
        "minutes": int(len(e)),
        "biais_cents": float(e.mean()),
        "ecart_type_cents": float(e.std(ddof=1)),
        "median_absolu_cents": float(np.median(np.abs(e))),
        "part_au_dela_d_un_cent": float((np.abs(e) > 1.0).mean()),
        "part_au_dela_de_cinq_cents": float((np.abs(e) > 5.0).mean()),
        "biais_pb": float(ecarts["ecart_pb"].mean()),
    }


def pires_seances(ecarts: pd.DataFrame, combien: int = 10) -> pd.DataFrame:
    """Les séances où l'écart moyen absolu est le plus grand."""
    par_jour = ecarts.groupby("seance").agg(
        ecart_moyen_cents=("ecart_cents", lambda s: float(np.abs(s).mean())),
        ecart_max_cents=("ecart_cents", lambda s: float(np.abs(s).max())),
        ecart_moyen_pb=("ecart_pb", lambda s: float(np.abs(s).mean())),
    )
    return par_jour.sort_values("ecart_moyen_cents", ascending=False).head(combien).reset_index()


def par_moment(table: pd.DataFrame, ecarts: pd.DataFrame) -> pd.DataFrame:
    """L'écart moyen selon la demi-heure de la séance."""
    joint = ecarts.merge(table[["local", "presente_iex"]], on="local", how="left")
    minute = (joint["local"].dt.hour * 60 + joint["local"].dt.minute) - (9 * 60 + 30)
    demi = (minute // 30).clip(0, 12)
    lignes = []
    for numero, bloc in joint.groupby(demi):
        debut = 9 * 60 + 30 + 30 * int(numero)
        lignes.append({
            "demi_heure": f"{debut // 60:02d}h{debut % 60:02d}",
            "ecart_moyen_cents": float(bloc["ecart_cents"].abs().mean()),
            "ecart_moyen_pb": float(bloc["ecart_pb"].abs().mean()),
        })
    return pd.DataFrame(lignes)


def echelle(table: pd.DataFrame) -> dict:
    """L'écart entre les deux moyennes, rapporté à ce que le signal mesure.

    Un écart de deux points de base ne dit rien tant qu'on ne sait pas à quoi le comparer. Le bon
    point de comparaison est la **distance entre le prix et sa moyenne pondérée**, puisque c'est le
    signe de cette distance que la règle regarde. Un écart dix fois plus petit qu'elle ne change
    presque jamais le signe ; un écart du même ordre le change une fois sur deux.

    La dernière ligne est la mesure directe : la part des minutes où l'écart entre les deux moyennes
    dépasse la distance elle-même, donc où il suffirait à faire basculer la décision.
    """
    distance = (table["prix_consolide"] - table["moyenne_consolide"]).abs()
    ecart = (table["moyenne_iex"] - table["moyenne_consolide"]).abs()
    lisible = ecart.notna()
    niveau = table["moyenne_consolide"]
    return {
        "distance_mediane_pb": float(10_000.0 * (distance / niveau).median()),
        "ecart_median_pb": float(10_000.0 * (ecart / niveau)[lisible].median()),
        "rapport": float((ecart / niveau)[lisible].median() / (distance / niveau).median()),
        "part_ou_l_ecart_depasse_la_distance": float((ecart[lisible] > distance[lisible]).mean()),
    }
