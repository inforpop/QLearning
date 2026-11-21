"""
Q-Learning clássico (tabular) com política ε-greedy.

Regra de atualização (Watkins, 1989):
    Q(s,a) ← Q(s,a) + α · [ r + γ · max_a' Q(s',a') − Q(s,a) ]
"""
from __future__ import annotations

import time

import numpy as np

from .ambiente import GridWorld, NOMES_ACOES, media_movel


def treinar_classico(episodios: int = 400, alpha: float = 0.1, gamma: float = 0.95,
                     epsilon: float = 1.0, epsilon_min: float = 0.05,
                     decaimento: float = 0.99, semente: int = 42) -> dict:
    rng = np.random.default_rng(semente)
    env = GridWorld()
    Q = np.zeros((env.n_estados, env.n_acoes))

    recompensas, passos, sucessos, eps_hist = [], [], [], []
    t0 = time.perf_counter()

    for _ in range(episodios):
        s = env.reset()
        total, fim, motivo = 0.0, False, ""
        while not fim:
            # ε-greedy: explora com probabilidade ε, senão explora o melhor Q
            if rng.random() < epsilon:
                a = int(rng.integers(env.n_acoes))
            else:
                melhores = np.flatnonzero(Q[s] == Q[s].max())
                a = int(rng.choice(melhores))

            s2, r, fim, motivo = env.step(a)
            alvo = r if motivo in ("objetivo", "armadilha") else r + gamma * Q[s2].max()
            Q[s, a] += alpha * (alvo - Q[s, a])
            s, total = s2, total + r

        recompensas.append(round(total, 2))
        passos.append(env.passos)
        sucessos.append(1 if motivo == "objetivo" else 0)
        eps_hist.append(round(epsilon, 4))
        epsilon = max(epsilon_min, epsilon * decaimento)

    duracao = time.perf_counter() - t0
    politica = Q.argmax(axis=1)
    avaliacao = env.caminho_guloso(lambda st: politica[st])

    ultimos = max(1, episodios // 10)
    return {
        "modo": "classico",
        "ambiente": env.descricao(),
        "recompensas": recompensas,
        "recompensas_media": media_movel(recompensas),
        "passos": passos,
        "passos_media": media_movel(passos),
        "exploracao": eps_hist,
        "q_table": np.round(Q, 2).tolist(),
        "valor": np.round(Q.max(axis=1), 2).tolist(),
        "politica": politica.tolist(),
        "politica_simbolos": [NOMES_ACOES[a] for a in politica],
        "avaliacao": avaliacao,
        "metricas": {
            "taxa_sucesso_final": round(100 * float(np.mean(sucessos[-ultimos:])), 1),
            "recompensa_media_final": round(float(np.mean(recompensas[-ultimos:])), 2),
            "passos_medios_final": round(float(np.mean(passos[-ultimos:])), 1),
            "primeiro_sucesso": (sucessos.index(1) + 1) if 1 in sucessos else None,
            "tempo_ms": round(duracao * 1000, 1),
        },
    }
