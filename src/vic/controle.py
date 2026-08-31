"""Un troisième fournisseur, pour vérifier que le flux consolidé est bien le flux consolidé.

Tout le dépôt repose sur une comparaison entre deux séries livrées par **le même** fournisseur. Si
ce fournisseur se trompait sur l'une des deux, la mesure entière serait fausse et rien dans la
comparaison ne le montrerait. Un contrôle indépendant est donc nécessaire, et Polygon le fournit :
c'est un autre agrégateur, avec sa propre chaîne de collecte, sur les mêmes barres d'une minute.

Ce que le contrôle peut établir et ce qu'il ne peut pas : il peut confirmer que deux chaînes
indépendantes voient le même marché consolidé, ce qui rend l'écart mesuré attribuable à IEX. Il ne
peut pas prouver qu'aucune des deux ne se trompe de la même façon, et le dépôt ne le prétend pas.
"""

from __future__ import annotations

import pandas as pd


def confronter(alpaca: pd.DataFrame, polygon: pd.DataFrame) -> dict:
    """Les prix et les volumes des deux agrégateurs, sur leurs minutes communes.

    Les deux fournisseurs sont comparés sur les seules minutes que tous deux publient, faute de
    quoi la différence mesurerait un décalage de couverture et non un désaccord sur les nombres.
    """
    a = alpaca[["local", "cloture", "volume", "prix_moyen"]].rename(
        columns={"cloture": "cloture_a", "volume": "volume_a", "prix_moyen": "moyen_a"})
    p = polygon[["local", "cloture", "volume", "prix_moyen"]].rename(
        columns={"cloture": "cloture_p", "volume": "volume_p", "prix_moyen": "moyen_p"})
    joint = a.merge(p, on="local", how="inner")
    if joint.empty:
        raise ValueError("aucune minute commune aux deux fournisseurs")

    ecart_prix = (joint["cloture_a"] - joint["cloture_p"]).abs()
    ecart_volume = (joint["volume_a"] - joint["volume_p"]).abs()
    return {
        "minutes_communes": int(len(joint)),
        "minutes_alpaca_seul": int(len(a) - len(joint)),
        "minutes_polygon_seul": int(len(p) - len(joint)),
        "ecart_de_prix_maximal_cents": float(100.0 * ecart_prix.max()),
        "ecart_de_prix_median_cents": float(100.0 * ecart_prix.median()),
        "prix_identiques_au_dixieme_de_cent": float((100.0 * ecart_prix < 0.1).mean()),
        "ecart_de_volume_moyen": float(
            ecart_volume.sum() / joint[["volume_a", "volume_p"]].mean(axis=1).sum()),
    }
