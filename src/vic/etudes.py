"""Les cinq études du dépôt, chacune rendant le tableau qu'elle écrit dans `results/tables`."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import controle, couverture, divergence, signaux, vwap
from .donnees import CACHE, DEBUT_IEX, FERMETURE, OUVERTURE, SYMBOLES, apparier, lire

TABLES = Path("results/tables")
GLISSEMENTS = (0.0, 0.25, 0.5, 1.0)


def charger(symbole: str, cache: Path = CACHE) -> pd.DataFrame:
    """Les deux flux d'un symbole, appariés et munis de leurs moyennes pondérées."""
    consolide = lire(symbole, "sip", cache)
    iex = lire(symbole, "iex", cache)
    return vwap.preparer(apparier(consolide, iex, depuis=DEBUT_IEX))


def _ecrire(table: pd.DataFrame, nom: str, dossier: Path = TABLES) -> Path:
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / f"{nom}.csv"
    table.to_csv(chemin, index=False)
    return chemin


def etude_couverture(tables: dict[str, pd.DataFrame], dossier: Path = TABLES) -> pd.DataFrame:
    """Ce qu'IEX voit, symbole par symbole, puis année par année, puis heure par heure."""
    lignes = [{"symbole": s, **couverture.globale(t)} for s, t in tables.items()]
    globale = pd.DataFrame(lignes)
    _ecrire(globale, "couverture", dossier)
    _ecrire(pd.concat([couverture.par_annee(t).assign(symbole=s) for s, t in tables.items()]),
            "couverture_par_annee", dossier)
    _ecrire(pd.concat([couverture.par_mois(t).assign(symbole=s) for s, t in tables.items()]),
            "couverture_par_mois", dossier)
    _ecrire(pd.concat([couverture.par_demi_heure(t).assign(symbole=s) for s, t in tables.items()]),
            "couverture_par_demi_heure", dossier)
    return globale


def etude_divergence(tables: dict[str, pd.DataFrame], dossier: Path = TABLES) -> pd.DataFrame:
    """De combien les deux moyennes pondérées s'écartent."""
    resumes, distributions, pires, moments = [], [], [], []
    for symbole, table in tables.items():
        e = vwap.ecarts(table)
        resumes.append({"symbole": symbole, **divergence.resume(e),
                        **divergence.echelle(table)})
        distributions.append(divergence.distribution(e).assign(symbole=symbole))
        pires.append(divergence.pires_seances(e).assign(symbole=symbole))
        moments.append(divergence.par_moment(table, e).assign(symbole=symbole))
    resume = pd.DataFrame(resumes)
    _ecrire(resume, "divergence", dossier)
    _ecrire(pd.concat(distributions), "divergence_distribution", dossier)
    _ecrire(pd.concat(pires), "divergence_pires_seances", dossier)
    _ecrire(pd.concat(moments), "divergence_par_moment", dossier)
    return resume


def etude_signaux(tables: dict[str, pd.DataFrame], dossier: Path = TABLES) -> pd.DataFrame:
    """Les quatre versions du signal, à quatre niveaux de glissement."""
    morceaux = []
    for symbole, table in tables.items():
        for g in GLISSEMENTS:
            morceaux.append(signaux.toutes_les_versions(table, g).assign(
                symbole=symbole, glissement_cents=g))
    resultat = pd.concat(morceaux, ignore_index=True)
    _ecrire(resultat, "signaux", dossier)
    return resultat


def etude_desaccords(tables: dict[str, pd.DataFrame], dossier: Path = TABLES) -> pd.DataFrame:
    """Sur combien de minutes les deux flux tiennent des positions différentes.

    Cette étude se sépare de la précédente parce qu'elle ne compare pas des rendements mais des
    positions, minute par minute : c'est elle qui dit d'où vient l'écart que la précédente mesure.
    """
    resultat = pd.DataFrame([{"symbole": s, **signaux.desaccords(t)} for s, t in tables.items()])
    _ecrire(resultat, "desaccords", dossier)
    return resultat


def etude_controle(symbole: str = "QQQ", cache: Path = CACHE,
                   dossier: Path = TABLES) -> pd.DataFrame:
    """Le flux consolidé d'Alpaca confronté à celui de Polygon, sur la fenêtre commune.

    Polygon ne garde que deux ans glissants sur son offre gratuite : le contrôle porte donc sur le
    dernier mois disponible, ce qui suffit à trancher entre « les deux agrégateurs voient le même
    marché » et « ils ne le voient pas ».

    Les deux séries sont coupées sur la même fenêtre horaire avant d'être confrontées. Polygon
    publie aussi les extensions d'avant et d'après-bourse, qu'Alpaca a déjà perdues au chargement :
    sans cette coupe, les 11 685 barres hors séance de juin 2026 se compteraient comme des minutes
    manquées par Alpaca, ce qui décrirait un trou de couverture qui n'existe pas.
    """
    fichiers = sorted(cache.glob(f"polygon_{symbole}_1Min_*.parquet"))
    if not fichiers:
        raise FileNotFoundError(
            f"aucune barre Polygon en cache pour {symbole}. Lancer « vic fetch --controle ».")
    polygon = pd.concat([pd.read_parquet(f) for f in fichiers], ignore_index=True)
    polygon["local"] = polygon["horodatage"].dt.tz_convert("America/New_York")
    heure = polygon["local"].dt.time
    polygon = polygon.loc[(heure >= OUVERTURE) & (heure < FERMETURE)].copy()
    alpaca = lire(symbole, "sip", cache)
    debut, fin = polygon["local"].min(), polygon["local"].max()
    alpaca = alpaca[(alpaca["local"] >= debut) & (alpaca["local"] <= fin)]
    resultat = pd.DataFrame([{"symbole": symbole, "debut": str(debut.date()),
                              "fin": str(fin.date()),
                              **controle.confronter(alpaca, polygon)}])
    _ecrire(resultat, "controle_polygon", dossier)
    return resultat


def tout(cache: Path = CACHE, dossier: Path = TABLES,
         tables: dict[str, pd.DataFrame] | None = None) -> dict[str, pd.DataFrame]:
    """Les cinq études, dans l'ordre où elles se lisent.

    Les tables appariées se passent en argument quand l'appelant les a déjà chargées. Les relire
    est l'étape la plus lourde du dépôt, six années de barres d'une minute sur deux symboles et
    deux flux, et rien n'oblige à la faire deux fois.
    """
    if tables is None:
        tables = {s: charger(s, cache) for s in SYMBOLES}
    sortie = {
        "couverture": etude_couverture(tables, dossier),
        "divergence": etude_divergence(tables, dossier),
        "signaux": etude_signaux(tables, dossier),
        "desaccords": etude_desaccords(tables, dossier),
    }
    try:
        sortie["controle"] = etude_controle("QQQ", cache, dossier)
    except FileNotFoundError as erreur:
        # le contrôle est un bonus : son absence ne doit pas empêcher les quatre autres études
        sortie["controle"] = pd.DataFrame([{"statut": "non disponible", "raison": str(erreur)}])
    return sortie
