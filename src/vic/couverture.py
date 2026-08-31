"""Ce qu'IEX voit du marché : la part du volume, et la part des minutes.

Deux mesures, et elles ne disent pas la même chose. La **part du volume** dit combien d'actions
passent par IEX sur cent qui s'échangent, donc le poids de cette bourse. La **part des minutes** dit
sur combien de minutes IEX a vu au moins une transaction, donc la densité de l'information qu'un
programme branché dessus reçoit.

Un flux peut très bien porter 2 % du volume et être présent à chaque minute, auquel cas sa moyenne
pondérée suivrait de près celle du marché. C'est parce que les deux mesures s'écartent que le sujet
existe.
"""

from __future__ import annotations

import pandas as pd


def globale(table: pd.DataFrame) -> dict:
    """Les deux parts sur toute la fenêtre, plus le retard à la première transaction.

    Deux régimes de défaillance se comptent séparément, parce qu'ils ne se soignent pas de la même
    façon. Le **retard** est le nombre de minutes qu'IEX met à voir sa première transaction du jour,
    et il ne se mesure que sur les séances où il finit par en voir une. La **séance entièrement
    muette** est le jour où IEX ne publie aucune barre : elle n'a pas de retard, elle a une absence,
    et la confondre avec un retard donnerait un maximum faussement rassurant.
    """
    total_c = float(table["volume_consolide"].sum())
    total_i = float(table["volume_iex"].fillna(0.0).sum())
    minutes = len(table)
    presentes = int(table["presente_iex"].sum())
    ouvertures = table.groupby("seance")["local"].min()
    vues = table[table["presente_iex"]].groupby("seance")["local"].min()
    muettes = ouvertures.index.difference(vues.index)
    # sur combien de minutes après l'ouverture IEX voit sa première transaction de la séance
    premiere = vues - ouvertures.loc[vues.index]
    return {
        "seances": int(table["seance"].nunique()),
        "minutes": minutes,
        "part_du_volume": total_i / total_c,
        "part_des_minutes": presentes / minutes,
        "minutes_muettes": minutes - presentes,
        "seances_sans_aucune_barre": int(len(muettes)),
        "seances_avec_retard_mesurable": int(len(premiere)),
        "retard_median_minutes": float(premiere.dt.total_seconds().median() / 60.0),
        "retard_pire_minutes": float(premiere.dt.total_seconds().max() / 60.0),
    }


def par_annee(table: pd.DataFrame) -> pd.DataFrame:
    """Les mêmes parts année par année : la part d'IEX n'est pas une constante."""
    an = pd.Series([d.year for d in table["seance"]], index=table.index, name="annee")
    lignes = []
    for annee, bloc in table.groupby(an):
        total_c = float(bloc["volume_consolide"].sum())
        lignes.append({
            "annee": int(annee),
            "seances": int(bloc["seance"].nunique()),
            "part_du_volume": float(bloc["volume_iex"].fillna(0.0).sum()) / total_c,
            "part_des_minutes": float(bloc["presente_iex"].mean()),
        })
    return pd.DataFrame(lignes)


def par_mois(table: pd.DataFrame) -> pd.DataFrame:
    """Les mêmes parts mois par mois.

    L'année est une maille trop grosse pour une part qui bouge. Le mois permet de confronter une
    mesure faite sur un mois isolé, celle du contrôle Polygon par exemple, à la mesure de la fenêtre
    entière, sans avoir à refaire le calcul à la main.
    """
    mois = pd.Series([f"{d.year:04d}-{d.month:02d}" for d in table["seance"]],
                     index=table.index, name="mois")
    lignes = []
    for etiquette, bloc in table.groupby(mois):
        lignes.append({
            "mois": str(etiquette),
            "seances": int(bloc["seance"].nunique()),
            "minutes": int(len(bloc)),
            "part_du_volume": float(bloc["volume_iex"].fillna(0.0).sum())
            / float(bloc["volume_consolide"].sum()),
            "part_des_minutes": float(bloc["presente_iex"].mean()),
        })
    return pd.DataFrame(lignes)


def par_demi_heure(table: pd.DataFrame) -> pd.DataFrame:
    """La présence d'IEX selon le moment de la séance.

    Le creux de la mi-journée est le moment où un flux minoritaire se tait le plus, et c'est aussi
    celui où un signal de suivi de tendance change le plus souvent d'avis. Les deux se rencontrent,
    d'où la découpe.
    """
    minute = (table["local"].dt.hour * 60 + table["local"].dt.minute) - (9 * 60 + 30)
    demi = (minute // 30).clip(0, 12)
    lignes = []
    for numero, bloc in table.groupby(demi):
        debut = 9 * 60 + 30 + 30 * int(numero)
        lignes.append({
            "demi_heure": f"{debut // 60:02d}h{debut % 60:02d}",
            "part_des_minutes": float(bloc["presente_iex"].mean()),
            "part_du_volume": float(bloc["volume_iex"].fillna(0.0).sum())
            / float(bloc["volume_consolide"].sum()),
        })
    return pd.DataFrame(lignes)
