"""
Q-Learning — Aprendizado por Reforço em Python
Dashboard Flask: Computação Clássica × Computação Quântica

Autor: Pedro Paulo Ribeiro — www.inforpop.com
"""
import os

from flask import Flask, jsonify, render_template, request

from rl.ambiente import GridWorld
from rl.classico import treinar_classico
from rl.quantico import demo_grover, treinar_quantico

app = Flask(__name__)

CONTATOS = {
    "site": "https://www.inforpop.com",
    "site_rotulo": "www.inforpop.com",
    "whatsapp": "https://wa.me/5521999618643",
    "whatsapp_rotulo": "55 21 99961-8643",
    "email": "inforpop@hotmail.com",
    "linkedin": "https://www.linkedin.com/in/pedro-paulo-ribeiro-pcd-1451498/",
    "linkedin_rotulo": "Pedro Paulo Ribeiro",
}


def _num(dados, chave, padrao, minimo, maximo, tipo=float):
    """Lê um parâmetro numérico do JSON, com limites de segurança."""
    try:
        valor = tipo(dados.get(chave, padrao))
    except (TypeError, ValueError):
        valor = padrao
    return max(minimo, min(maximo, valor))


@app.route("/")
def index():
    return render_template("index.html", contatos=CONTATOS)


@app.route("/api/ambiente")
def api_ambiente():
    return jsonify(GridWorld().descricao())


@app.route("/api/classico/treinar", methods=["POST"])
def api_classico():
    d = request.get_json(silent=True) or {}
    resultado = treinar_classico(
        episodios=_num(d, "episodios", 400, 10, 3000, int),
        alpha=_num(d, "alpha", 0.1, 0.001, 1.0),
        gamma=_num(d, "gamma", 0.95, 0.0, 0.999),
        epsilon=_num(d, "epsilon", 1.0, 0.0, 1.0),
        decaimento=_num(d, "decaimento", 0.99, 0.9, 1.0),
        semente=_num(d, "semente", 42, 0, 10**6, int),
    )
    return jsonify(resultado)


@app.route("/api/quantico/treinar", methods=["POST"])
def api_quantico():
    d = request.get_json(silent=True) or {}
    resultado = treinar_quantico(
        episodios=_num(d, "episodios", 400, 10, 3000, int),
        alpha=_num(d, "alpha", 0.1, 0.001, 1.0),
        gamma=_num(d, "gamma", 0.95, 0.0, 0.999),
        k=_num(d, "k", 0.05, 0.001, 1.0),
        semente=_num(d, "semente", 42, 0, 10**6, int),
    )
    return jsonify(resultado)


@app.route("/api/quantico/grover")
def api_grover():
    marcado = _num(request.args, "marcado", 2, 0, 3, int)
    return jsonify(demo_grover(marcado))


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=porta, debug=os.environ.get("FLASK_DEBUG") == "1")
