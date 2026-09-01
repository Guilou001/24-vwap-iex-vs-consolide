"""Les commandes du dépôt."""

from __future__ import annotations

import typer

from . import etudes, figures
from .donnees import CACHE, DEBUT_IEX, SYMBOLES

app = typer.Typer(add_completion=False, help="Le VWAP d'IEX contre celui du flux consolidé.")


@app.command()
def fetch(controle: bool = typer.Option(False, help="télécharger aussi le mois de contrôle Polygon")):
    """Les barres d'une minute des deux flux, mises en cache."""
    from gvf.marches import Requete, barres_alpaca, barres_polygon

    for symbole in SYMBOLES:
        for flux, debut in (("sip", "2020-01-01"), ("iex", str(DEBUT_IEX))):
            for an in range(2020, 2027):
                d = debut if an == 2020 else f"{an}-01-01"
                f = "2026-08-29" if an == 2026 else f"{an}-12-31"
                table = barres_alpaca(Requete(symbole=symbole, debut=d, fin=f, pas="1Min",
                                              flux=flux, ajustement="brut"), cache=CACHE)
                typer.echo(f"{symbole} {an} {flux} : {len(table)} barres")
        if controle:
            table = barres_polygon(Requete(symbole=symbole, debut="2026-06-01", fin="2026-06-30",
                                           pas="1Min", ajustement="brut"), cache=CACHE)
            typer.echo(f"{symbole} contrôle Polygon : {len(table)} barres")


@app.command()
def couverture():
    """Ce qu'IEX voit du marché."""
    tables = {s: etudes.charger(s) for s in SYMBOLES}
    typer.echo(etudes.etude_couverture(tables).to_string(index=False))


@app.command()
def divergence():
    """De combien les deux moyennes pondérées s'écartent."""
    tables = {s: etudes.charger(s) for s in SYMBOLES}
    typer.echo(etudes.etude_divergence(tables).to_string(index=False))


@app.command()
def signal():
    """Les quatre versions du signal du dépôt 21, puis le compte des désaccords."""
    tables = {s: etudes.charger(s) for s in SYMBOLES}
    typer.echo(etudes.etude_signaux(tables).to_string(index=False))
    typer.echo(etudes.etude_desaccords(tables).to_string(index=False))


@app.command()
def controle():
    """Le flux consolidé d'Alpaca confronté à celui de Polygon."""
    typer.echo(etudes.etude_controle().to_string(index=False))


@app.command()
def tout():
    """Les cinq études et les cinq figures."""
    import pandas as pd

    from . import vwap

    tables = {s: etudes.charger(s) for s in SYMBOLES}
    for nom, table in etudes.tout(tables=tables).items():
        typer.echo(f"\n== {nom}\n{table.to_string(index=False)}")

    ecarts = {s: vwap.ecarts(t) for s, t in tables.items()}
    par_annee = pd.read_csv(etudes.TABLES / "couverture_par_annee.csv")
    par_moment = pd.read_csv(etudes.TABLES / "divergence_par_moment.csv")
    signaux = pd.read_csv(etudes.TABLES / "signaux.csv")
    desaccords = pd.read_csv(etudes.TABLES / "desaccords.csv")
    for rendu in (figures.couverture(par_annee), figures.distribution(ecarts),
                  figures.moments(par_moment), figures.versions(signaux),
                  figures.desaccords(desaccords)):
        typer.echo(f"figure : {rendu['chemins']}")
