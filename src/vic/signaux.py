"""Le signal du dépôt 21, rejoué sur chacun des deux flux, et la décomposition de l'écart.

**Le signal.** Acheter quand le prix est au-dessus du prix moyen pondéré depuis l'ouverture, vendre à
découvert sinon, solder à la clôture. C'est la règle de Zarattini et Aziz, reprise telle quelle.

**Pourquoi quatre versions et non deux.** Le signal compare deux grandeurs, un prix et une moyenne.
Chacune peut venir de l'un ou l'autre flux, ce qui fait quatre combinaisons. Les deux versions pures
disent ce qu'un praticien et un réplicateur à budget nul obtiennent. Les deux versions croisées
servent à répondre à la question qui compte : **laquelle des deux grandeurs porte l'erreur ?** Sans
elles, on saurait que le résultat change sans savoir pourquoi.

**Le rendement encaissé est toujours celui du marché.** Quel que soit le flux qui décide, la position
est prise sur le vrai marché et rapporte ce que le vrai marché fait. Facturer le résultat au prix
d'IEX reviendrait à créditer le réplicateur d'un marché qui n'existe pas.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# les quatre combinaisons : d'où vient le prix, d'où vient la moyenne pondérée
VERSIONS = {
    "consolidé": ("prix_consolide", "moyenne_consolide"),
    "IEX": ("prix_iex", "moyenne_iex"),
    "prix consolidé, moyenne IEX": ("prix_consolide", "moyenne_iex"),
    "prix IEX, moyenne consolidée": ("prix_iex", "moyenne_consolide"),
}
JOURS_PAR_AN = 252


def positions(table: pd.DataFrame, prix: str, moyenne: str) -> pd.Series:
    """La position détenue à chaque minute, décidée par la minute précédente.

    Le décalage d'une minute est ce qui empêche de connaître le futur : la comparaison faite à la
    fin de la minute t décide de la position tenue pendant la minute t+1. Sans lui, la stratégie
    achèterait au prix qu'elle vient d'observer, et tous les chiffres seraient faux.

    Une comparaison impossible, faute de prix ou de moyenne, laisse la position à zéro. Une
    comparaison qui tombe exactement à égalité aussi : c'est le cas de la première minute, où la
    moyenne pondérée n'a qu'une observation et vaut donc le prix lui-même.
    """
    signal = np.sign(table[prix] - table[moyenne])
    signal = pd.Series(signal, index=table.index).fillna(0.0)
    tenue = signal.groupby(table["seance"]).shift(1).fillna(0.0)
    return tenue


def rendements_du_marche(table: pd.DataFrame) -> pd.Series:
    """Le rendement d'une minute sur le vrai marché, remis à zéro à chaque ouverture.

    La première minute de chaque séance ne porte aucun rendement, la stratégie étant hors du marché
    de la clôture de la veille à l'ouverture du jour.
    """
    r = table.groupby("seance")["prix_consolide"].pct_change()
    return r.fillna(0.0)


@dataclass(frozen=True)
class Resultat:
    """Ce qu'une version du signal produit."""

    nom: str
    rendement_total: float
    annualise: float
    volatilite: float
    sharpe: float
    pire_creux: float
    changements_par_jour: float
    minutes_investies: float

    def en_ligne(self) -> dict:
        return {"version": self.nom, "rendement_total": self.rendement_total,
                "annualise": self.annualise, "volatilite": self.volatilite,
                "sharpe": self.sharpe, "pire_creux": self.pire_creux,
                "changements_par_jour": self.changements_par_jour,
                "minutes_investies": self.minutes_investies}


def rejouer(table: pd.DataFrame, prix: str, moyenne: str, nom: str,
            glissement_cents: float = 0.0) -> Resultat:
    """Une version du signal, jouée du début à la fin de la fenêtre.

    Le glissement est facturé à chaque changement de position, et pour deux fois la position
    détenue : passer d'acheteur à vendeur à découvert veut dire vendre ce qu'on a puis vendre autant
    de nouveau.
    """
    tenue = positions(table, prix, moyenne)
    marche = rendements_du_marche(table)
    brut = tenue * marche

    changements = tenue.diff().fillna(tenue).abs()
    cout = changements * (glissement_cents / 100.0) / table["prix_consolide"]
    net = brut - cout

    valeur = (1.0 + net).cumprod()
    total = float(valeur.iloc[-1] - 1.0)
    seances = int(table["seance"].nunique())
    minutes_par_an = JOURS_PAR_AN * 390
    annualise = float(valeur.iloc[-1] ** (JOURS_PAR_AN / seances) - 1.0)
    volatilite = float(net.std(ddof=1) * np.sqrt(minutes_par_an))
    sharpe = float(annualise / volatilite) if volatilite > 0 else float("nan")
    creux = float((1.0 - valeur / valeur.cummax()).max())
    return Resultat(nom=nom, rendement_total=total, annualise=annualise, volatilite=volatilite,
                    sharpe=sharpe, pire_creux=creux,
                    changements_par_jour=float(changements.sum() / (2 * seances)),
                    minutes_investies=float((tenue != 0).mean()))


def desaccords(table: pd.DataFrame) -> dict:
    """Sur combien de minutes les deux flux donnent des positions différentes.

    Trois cas se distinguent, et ils ne coûtent pas la même chose. Le **silence** est la minute où
    IEX n'a encore rien vu de la séance, donc ne décide rien. Le **contresens** est la minute où les
    deux flux prennent des positions opposées, l'un acheteur et l'autre vendeur : c'est le cas qui
    coûte deux fois le mouvement du marché. Le reste est l'accord.
    """
    ref = positions(table, "prix_consolide", "moyenne_consolide")
    autre = positions(table, "prix_iex", "moyenne_iex")
    silence = (autre == 0) & (ref != 0)
    contresens = (ref * autre) < 0
    accord = (ref == autre) & (ref != 0)
    marche = rendements_du_marche(table)
    return {
        "minutes": int(len(table)),
        "part_accord": float(accord.mean()),
        "part_silence": float(silence.mean()),
        "part_contresens": float(contresens.mean()),
        "cout_du_contresens": float((autre - ref)[contresens].mul(marche[contresens]).sum()),
        "cout_du_silence": float((autre - ref)[silence].mul(marche[silence]).sum()),
    }


def toutes_les_versions(table: pd.DataFrame, glissement_cents: float = 0.0) -> pd.DataFrame:
    """Les quatre versions du signal, dans un tableau."""
    return pd.DataFrame([rejouer(table, prix, moyenne, nom, glissement_cents).en_ligne()
                         for nom, (prix, moyenne) in VERSIONS.items()])
