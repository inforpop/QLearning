import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402
from rl.quantico import demo_grover, iteracao_grover_completa, rotacao_grover  # noqa: E402


def test_pagina_inicial():
    r = app.test_client().get("/")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "inforpop@hotmail.com" in html and "Computação Quântica" in html


def test_treino_classico():
    r = app.test_client().post("/api/classico/treinar", json={"episodios": 300})
    d = r.get_json()
    assert d["avaliacao"]["resultado"] == "objetivo"


def test_treino_quantico():
    r = app.test_client().post("/api/quantico/treinar", json={"episodios": 300})
    d = r.get_json()
    assert d["avaliacao"]["resultado"] == "objetivo"
    assert np.allclose(np.sum(d["probabilidades"], axis=1), 1, atol=1e-3)


def test_grover_2_qubits_acha_marcado():
    for m in range(4):
        assert demo_grover(m)["etapas"][-1]["probabilidades"][m] > 0.999


def test_rotacao_equivale_a_iteracao_de_grover():
    psi = np.full(4, 0.5)
    theta = np.arcsin(0.5)
    assert np.allclose(iteracao_grover_completa(psi, 1), rotacao_grover(psi, 1, 2 * theta, 0, np.pi / 2))
