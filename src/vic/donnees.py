"""Les barres d'une minute des deux flux, posées sur la même grille de minutes.

**Les deux flux, en mots simples.** Une action américaine ne s'échange pas à un seul endroit. Une
transaction peut se faire sur seize bourses différentes et sur une trentaine de systèmes privés, et
toutes remontent à un agrégateur officiel appelé le **flux consolidé**, qui est ce que voient les
pupitres. IEX est une de ces bourses, la plus petite de celles qui publient gratuitement, et
c'est celle que les fournisseurs de données offrent sans abonnement.

**Ce que cela change pour une grille de minutes.** Le flux consolidé publie une barre pour chaque
minute où le titre s'est échangé quelque part, ce qui, sur un fonds très liquide, veut dire toutes
les minutes. IEX ne publie une barre que pour les minutes où une transaction s'est faite chez lui.
Il en manque donc, et il faut décider quoi mettre à la place.

**La décision retenue.** Rien. Une minute sans transaction chez IEX ne fait pas bouger le prix moyen
pondéré calculé sur IEX, et le dernier prix connu reste le dernier prix connu. C'est exactement ce
qu'un programme de réplication à budget nul fait sans y penser, et c'est donc ce qu'il faut mesurer.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

CACHE = Path(__file__).resolve().parents[2] / "data" / "marches"

SYMBOLES = ("QQQ", "SPY")
OUVERTURE = dt.time(9, 30)
FERMETURE = dt.time(16, 0)
BARRES_ATTENDUES = 390
# Mesuré le 2026-08-30 : la fenêtre glissante d'Alpaca sur le flux IEX commence là. Elle avance,
# donc ce dépôt fixe sa fenêtre d'étude à cette date et la déclare.
DEBUT_IEX = dt.date(2020, 8, 3)


def fichiers(symbole: str, flux: str, cache: Path = CACHE) -> list[Path]:
    """Les fichiers de cache d'un symbole et d'un flux, dans l'ordre des années."""
    return sorted(cache.glob(f"alpaca_{symbole}_1Min_{flux}_brut_*.parquet"))


def lire(symbole: str, flux: str, cache: Path = CACHE) -> pd.DataFrame:
    """Toutes les barres d'un symbole et d'un flux, ramenées à l'heure de New York.

    Les colonnes rendues sont l'horodatage local, la date de séance, le prix de clôture de la
    minute, le volume et le montant échangé. Le montant est le produit du prix moyen de la barre par
    son volume : c'est lui qui se cumule pour faire le prix moyen pondéré, et non le prix de
    clôture.
    """
    tables = [pd.read_parquet(f) for f in fichiers(symbole, flux, cache)]
    if not tables:
        raise FileNotFoundError(
            f"aucune barre en cache pour {symbole} sur le flux {flux}. Lancer « vic fetch ».")
    table = pd.concat(tables, ignore_index=True)
    table = table.drop_duplicates(subset="horodatage").sort_values("horodatage")

    local = table["horodatage"].dt.tz_convert("America/New_York")
    dans_la_seance = (local.dt.time >= OUVERTURE) & (local.dt.time < FERMETURE)
    table = table.loc[dans_la_seance].copy()
    local = local.loc[dans_la_seance]

    table["local"] = local
    table["seance"] = local.dt.date
    # le prix moyen de la barre, celui que le fournisseur publie, et non la clôture : employer la
    # clôture pour cumuler donnerait un prix moyen pondéré faux dès la première minute agitée
    table["montant"] = table["prix_moyen"] * table["volume"]
    return table[["local", "seance", "ouverture", "haut", "bas", "cloture", "volume", "prix_moyen",
                  "montant"]].reset_index(drop=True)


def seances_completes(consolide: pd.DataFrame, attendues: int = BARRES_ATTENDUES) -> set:
    """Les séances où le flux consolidé a bien ses 390 minutes.

    Les séances écourtées de veille de congé sont retirées : elles ferment à 13 h, si bien que leur
    prix moyen pondéré porte sur trois heures et demie au lieu de six et demie, et les mêler aux
    autres fausserait toute moyenne par séance.

    Le filtre est plus large que son motif, et c'est mesuré. Sur la fenêtre du dépôt il retire 12
    séances sur QQQ, toutes des veilles de congé, mais 14 sur SPY, dont deux séances ordinaires où
    le flux consolidé lui-même a manqué quelques minutes, le 2021-05-05 avec 385 barres et le
    2023-06-05 avec 386. Sur un titre moins traité, la même règle écarterait des dizaines de séances
    normales sans rien signaler.

    Le compte attendu est un argument et non une constante figée : les tests travaillent sur des
    séances de quatre minutes, et une constante en dur les obligerait à fabriquer 390 barres pour
    vérifier une formule qui tient en une ligne.
    """
    compte = consolide.groupby("seance").size()
    return set(compte[compte == attendues].index)


def apparier(consolide: pd.DataFrame, iex: pd.DataFrame, depuis: dt.date = DEBUT_IEX,
             attendues: int = BARRES_ATTENDUES) -> pd.DataFrame:
    """Les deux flux sur la même grille de minutes, celle du consolidé.

    Le consolidé donne la grille parce qu'il est complet. Chaque minute reçoit donc ses deux
    versions, et les colonnes du flux IEX sont vides pour les minutes où IEX n'a rien vu. C'est
    cette absence qui est l'objet du dépôt : la remplir d'office reviendrait à cacher le phénomène
    qu'on mesure.
    """
    gardees = seances_completes(consolide, attendues)
    gardees = {s for s in gardees if s >= depuis}
    c = consolide[consolide["seance"].isin(gardees)].copy()
    i = iex[iex["seance"].isin(gardees)].copy()

    colonnes = ["cloture", "volume", "prix_moyen", "montant"]
    fusion = c.merge(i[["local", *colonnes]], on="local", how="left",
                     suffixes=("_consolide", "_iex"))
    fusion["presente_iex"] = fusion["volume_iex"].notna()
    return fusion.sort_values("local").reset_index(drop=True)
