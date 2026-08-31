# Prérequis : uv (https://docs.astral.sh/uv/)
UV ?= uv

setup:
	$(UV) sync --locked --all-extras

test:             ## 19 tests fermés, sans réseau ni données de marché
	$(UV) run pytest

lint:
	$(UV) run ruff check .

data:             ## les deux flux sur six ans, plus le mois de contrôle Polygon
	$(UV) run vic fetch --controle

all:              ## les cinq études et les cinq figures
	$(UV) run vic tout
