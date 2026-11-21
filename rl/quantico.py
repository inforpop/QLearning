"""
Aprendizado por Reforço Quântico (QRL) — inspirado em Dong, Chen, Li & Tarn,
"Quantum Reinforcement Learning", IEEE Trans. SMC-B, 2008.

Ideia central
-------------
* Cada estado s guarda um registrador de 2 qubits em superposição das 4 ações:
      |ψ_s⟩ = c0|00⟩ + c1|01⟩ + c2|10⟩ + c3|11⟩      (|00⟩=↑, |01⟩=→, |10⟩=↓, |11⟩=←)
* Escolher a ação = MEDIR o registrador: a ação a sai com probabilidade |c_a|².
  A exploração vem da própria natureza probabilística da medição (sem ε).
* Aprender = AMPLIFICAÇÃO DE AMPLITUDE (Grover). Depois de executar a ação a,
  o estado gira no plano {|a⟩, |a⊥⟩} por um ângulo proporcional ao erro TD:
      δ = r + γ·V(s') − V(s)          (V aprendido por TD(0))
      Δθ = k · δ
  δ > 0 amplifica a ação; δ < 0 a atenua. Uma iteração completa de Grover
  é exatamente uma rotação de 2θ nesse plano; aqui usamos a versão
  fracionária (Grover generalizado), que permite reforços graduais.

Tudo é simulado em NumPy (vetor de estado), sem dependências externas —
o que deixa o deploy no Heroku leve.
"""
from __future__ import annotations

import time

import numpy as np

from .ambiente import GridWorld, NOMES_ACOES, media_movel

ROTULOS_BASE = ["|00⟩", "|01⟩", "|10⟩", "|11⟩"]

# ============================================================================
# Mini-simulador de circuitos (2 qubits) — portas como matrizes
# ============================================================================
I2 = np.eye(2)
H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
X = np.array([[0, 1], [1, 0]])
Z = np.array([[1, 0], [0, -1]])
CZ = np.diag([1, 1, 1, -1])


def kron(*mats):
    out = np.array([[1.0]])
    for m in mats:
        out = np.kron(out, m)
    return out


def oraculo(marcado: int) -> np.ndarray:
    """Oráculo de fase U_a = I − 2|a⟩⟨a|  (inverte o sinal do estado marcado)."""
    # Construído com portas: X nos bits 0 do alvo, CZ, e desfaz os X.
    b1, b0 = divmod(marcado, 2)
    flips = kron(I2 if b1 else X, I2 if b0 else X)
    return flips @ CZ @ flips


def difusor() -> np.ndarray:
    """Operador de difusão U_s = 2|s⟩⟨s| − I  (inversão em torno da média)."""
    HH = kron(H, H)
    return HH @ (kron(X, X) @ CZ @ kron(X, X)) @ HH * -1


def demo_grover(marcado: int = 2) -> dict:
    """Executa o algoritmo de Grover com 2 qubits e devolve cada etapa."""
    psi0 = np.zeros(4)
    psi0[0] = 1.0
    etapas = [("Estado inicial |00⟩", psi0)]
    psi = kron(H, H) @ psi0
    etapas.append(("Hadamard H⊗H (superposição)", psi))
    psi = oraculo(marcado) @ psi
    etapas.append((f"Oráculo marca {ROTULOS_BASE[marcado]}", psi))
    psi = difusor() @ psi
    etapas.append(("Difusão (inversão na média)", psi))
    return {
        "marcado": marcado,
        "rotulos": ROTULOS_BASE,
        "acoes": NOMES_ACOES,
        "etapas": [
            {"nome": n, "amplitudes": np.round(v.real, 4).tolist(),
             "probabilidades": np.round(np.abs(v) ** 2, 4).tolist()}
            for n, v in etapas
        ],
    }


# ============================================================================
# Operações do agente quântico
# ============================================================================
def medir(psi: np.ndarray, rng: np.random.Generator) -> int:
    """Colapsa o registrador: devolve a ação com probabilidade |amplitude|²."""
    p = np.abs(psi) ** 2
    return int(rng.choice(len(psi), p=p / p.sum()))


def rotacao_grover(psi: np.ndarray, acao: int, delta: float,
                   theta_min: float, theta_max: float) -> np.ndarray:
    """
    Gira |ψ⟩ no plano {|a⟩, |a⊥⟩} por `delta` radianos (Grover generalizado).
    θ é o ângulo tal que |ψ⟩ = sen θ |a⟩ + cos θ |a⊥⟩.
    """
    amp_a = psi[acao]
    resto = psi.copy()
    resto[acao] = 0.0
    n_resto = np.linalg.norm(resto)
    if n_resto < 1e-12:  # estado já é |a⟩ — usa |a⊥⟩ uniforme nas demais
        resto = np.ones_like(psi)
        resto[acao] = 0.0
        n_resto = np.linalg.norm(resto)
    theta = np.arctan2(abs(amp_a), n_resto)
    novo = float(np.clip(theta + delta, theta_min, theta_max))
    out = np.sin(novo) * np.eye(len(psi))[acao] + np.cos(novo) * resto / n_resto
    return out / np.linalg.norm(out)


def iteracao_grover_completa(psi: np.ndarray, acao: int) -> np.ndarray:
    """Uma iteração de Grover padrão G = U_ψ U_a (refletindo em torno de |ψ⟩)."""
    Ua = np.eye(len(psi)) - 2 * np.outer(np.eye(len(psi))[acao], np.eye(len(psi))[acao])
    Upsi = 2 * np.outer(psi, psi) - np.eye(len(psi))
    return Upsi @ Ua @ psi


# ============================================================================
# Treinamento
# ============================================================================
def treinar_quantico(episodios: int = 400, alpha: float = 0.1, gamma: float = 0.95,
                     k: float = 0.05, p_min: float = 0.01, p_max: float = 0.97, semente: int = 42) -> dict:
    rng = np.random.default_rng(semente)
    env = GridWorld()
    n_s, n_a = env.n_estados, env.n_acoes

    psi = np.full((n_s, n_a), 1 / np.sqrt(n_a))   # H⊗H|00⟩ em todo estado
    V = np.zeros(n_s)

    # Limites de probabilidade de cada ação: nunca zera (preserva exploração)
    theta_min = np.arcsin(np.sqrt(p_min))
    theta_max = np.arcsin(np.sqrt(p_max))

    recompensas, passos, sucessos, entropia = [], [], [], []
    medicoes = 0
    t0 = time.perf_counter()

    for _ in range(episodios):
        s = env.reset()
        total, fim, motivo = 0.0, False, ""
        while not fim:
            a = medir(psi[s], rng)
            medicoes += 1
            s2, r, fim, motivo = env.step(a)

            v_prox = 0.0 if motivo in ("objetivo", "armadilha") else V[s2]
            td = r + gamma * v_prox - V[s]
            V[s] += alpha * td                                   # TD(0)
            psi[s] = rotacao_grover(psi[s], a, k * td, theta_min, theta_max)
            s, total = s2, total + r

        p = np.abs(psi) ** 2
        ent = -np.sum(p * np.log2(np.clip(p, 1e-12, 1)), axis=1).mean()
        recompensas.append(round(total, 2))
        passos.append(env.passos)
        sucessos.append(1 if motivo == "objetivo" else 0)
        entropia.append(round(float(ent), 4))

    duracao = time.perf_counter() - t0
    probs = np.abs(psi) ** 2
    politica = probs.argmax(axis=1)
    avaliacao = env.caminho_guloso(lambda st: politica[st])

    ultimos = max(1, episodios // 10)
    return {
        "modo": "quantico",
        "ambiente": env.descricao(),
        "recompensas": recompensas,
        "recompensas_media": media_movel(recompensas),
        "passos": passos,
        "passos_media": media_movel(passos),
        "exploracao": entropia,               # entropia média (bits) da medição
        "amplitudes": np.round(psi, 4).tolist(),
        "probabilidades": np.round(probs, 4).tolist(),
        "valor": np.round(V, 2).tolist(),
        "politica": politica.tolist(),
        "politica_simbolos": [NOMES_ACOES[a] for a in politica],
        "avaliacao": avaliacao,
        "rotulos_base": ROTULOS_BASE,
        "metricas": {
            "taxa_sucesso_final": round(100 * float(np.mean(sucessos[-ultimos:])), 1),
            "recompensa_media_final": round(float(np.mean(recompensas[-ultimos:])), 2),
            "passos_medios_final": round(float(np.mean(passos[-ultimos:])), 1),
            "primeiro_sucesso": (sucessos.index(1) + 1) if 1 in sucessos else None,
            "medicoes": medicoes,
            "tempo_ms": round(duracao * 1000, 1),
        },
    }
