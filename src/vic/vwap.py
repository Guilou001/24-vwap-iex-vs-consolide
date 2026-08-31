"""Le prix moyen pondéré par les volumes, cumulé depuis l'ouverture, sur chacun des deux flux.

**La définition, en mots simples.** À chaque minute, on divise tout l'argent échangé depuis
l'ouverture par toutes les actions échangées depuis l'ouverture. Le résultat est le prix moyen payé
par l'ensemble du marché depuis le matin.

**Ce que le flux change.** Le numérateur et le dénominateur sont des sommes sur les transactions
vues. Le flux consolidé les voit toutes ; IEX n'en voit qu'une petite part. Les deux moyennes ne
portent donc pas sur la même population, et rien ne garantit qu'elles se ressemblent, même si le
prix instantané, lui, est le même partout à l'arbitrage près.

**Le traitement des minutes manquantes.** Une minute sans transaction chez IEX n'ajoute rien aux
deux cumuls, donc la moyenne pondérée ne bouge pas. Le prix, lui, est reporté depuis la dernière
minute où IEX a vu quelque chose : c'est le dernier prix qu'un programme branché sur ce seul flux
connaîtrait. Tant qu'IEX n'a rien vu depuis l'ouverture, les deux grandeurs sont absentes, et aucune
position ne peut être prise.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def cumuler(table: pd.DataFrame, montant: str, volume: str) -> pd.Series:
    """Le prix moyen pondéré depuis l'ouverture, séance par séance.

    Les deux cumuls sont remis à zéro à chaque séance, ce que fait le groupement par date. Les
    minutes absentes comptent pour zéro dans la somme, donc elles laissent la moyenne inchangée,
    ce qui est le comportement voulu et non un artefact.
    """
    m = table[montant].fillna(0.0)
    v = table[volume].fillna(0.0)
    somme_m = m.groupby(table["seance"]).cumsum()
    somme_v = v.groupby(table["seance"]).cumsum()
    return pd.Series(np.where(somme_v > 0, somme_m / somme_v.replace(0, np.nan), np.nan),
                     index=table.index)


def prix_reporte(table: pd.DataFrame, colonne: str) -> pd.Series:
    """Le dernier prix connu du flux, reporté sur les minutes où il n'a rien vu.

    Le report ne franchit pas la clôture : chaque séance repart du silence, sans quoi le prix de la
    veille servirait de signal à l'ouverture du lendemain, ce qui n'a pas de sens sur un flux dont
    on mesure justement les trous.
    """
    return table.groupby("seance")[colonne].ffill()


def preparer(apparie: pd.DataFrame) -> pd.DataFrame:
    """Les deux prix et les deux moyennes pondérées, prêts pour la comparaison.

    Quatre colonnes en sortent, deux par flux. Elles suffisent à écrire tout le reste du dépôt.
    """
    table = apparie.copy()
    table["moyenne_consolide"] = cumuler(table, "montant_consolide", "volume_consolide")
    table["moyenne_iex"] = cumuler(table, "montant_iex", "volume_iex")
    table["prix_consolide"] = table["cloture_consolide"]
    table["prix_iex"] = prix_reporte(table, "cloture_iex")
    return table


def ecarts(table: pd.DataFrame) -> pd.DataFrame:
    """L'écart entre les deux moyennes pondérées, en cents et en points de base.

    Les deux unités disent deux choses différentes. Le cent dit ce qu'un pupitre verrait sur son
    écran ; le point de base rend les titres comparables entre eux, un cent ne pesant pas la même
    chose sur un fonds à 500 dollars et sur un fonds à 40.
    """
    lisibles = table["moyenne_iex"].notna() & table["moyenne_consolide"].notna()
    ecart = table["moyenne_iex"] - table["moyenne_consolide"]
    sortie = table.loc[lisibles, ["local", "seance"]].copy()
    sortie["ecart_cents"] = 100.0 * ecart[lisibles]
    sortie["ecart_pb"] = 10_000.0 * (ecart[lisibles] / table.loc[lisibles, "moyenne_consolide"])
    return sortie
