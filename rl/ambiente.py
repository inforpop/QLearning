"""
Ambiente GridWorld para Aprendizado por Reforço.

O agente começa no canto superior esquerdo e precisa chegar ao objetivo
(canto inferior direito), desviando de paredes e armadilhas.

Ações: 0 = cima, 1 = direita, 2 = baixo, 3 = esquerda
"""
from __future__ import annotations

import numpy as np

ACOES = {0: (-1, 0), 1: (0, 1), 2: (1, 0), 3: (0, -1)}
NOMES_ACOES = ["↑", "→", "↓", "←"]


class GridWorld:
    def __init__(self, linhas: int = 6, colunas: int = 6, max_passos: int = 100):
        self.linhas = linhas
        self.colunas = colunas
        self.max_passos = max_passos
        self.inicio = (0, 0)
        self.objetivo = (linhas - 1, colunas - 1)
        self.paredes = {(1, 1), (1, 2), (2, 4), (3, 1), (4, 3), (4, 4)}
        self.armadilhas = {(2, 2), (3, 4), (5, 1)}

        # Recompensas
        self.r_passo = -1.0
        self.r_parede = -2.0
        self.r_objetivo = 20.0
        self.r_armadilha = -20.0

        self.n_estados = linhas * colunas
        self.n_acoes = 4
        self.reset()

    # ---------------------------------------------------------------- utilidades
    def para_estado(self, pos: tuple[int, int]) -> int:
        return pos[0] * self.colunas + pos[1]

    def para_pos(self, estado: int) -> tuple[int, int]:
        return divmod(estado, self.colunas)

    def tipo_celula(self, pos: tuple[int, int]) -> str:
        if pos in self.paredes:
            return "parede"
        if pos in self.armadilhas:
            return "armadilha"
        if pos == self.objetivo:
            return "objetivo"
        if pos == self.inicio:
            return "inicio"
        return "livre"

    def descricao(self) -> dict:
        return {
            "linhas": self.linhas,
            "colunas": self.colunas,
            "celulas": [
                [self.tipo_celula((i, j)) for j in range(self.colunas)]
                for i in range(self.linhas)
            ],
        }

    # ---------------------------------------------------------------- dinâmica
    def reset(self) -> int:
        self.pos = self.inicio
        self.passos = 0
        return self.para_estado(self.pos)

    def step(self, acao: int) -> tuple[int, float, bool, str]:
        """Executa uma ação. Retorna (próximo_estado, recompensa, terminou, motivo)."""
        self.passos += 1
        di, dj = ACOES[acao]
        ni, nj = self.pos[0] + di, self.pos[1] + dj

        fora = not (0 <= ni < self.linhas and 0 <= nj < self.colunas)
        if fora or (ni, nj) in self.paredes:
            recompensa, nova = self.r_parede, self.pos  # bate e fica parado
        else:
            nova = (ni, nj)
            recompensa = self.r_passo

        self.pos = nova
        if nova == self.objetivo:
            return self.para_estado(nova), self.r_objetivo, True, "objetivo"
        if nova in self.armadilhas:
            return self.para_estado(nova), self.r_armadilha, True, "armadilha"
        if self.passos >= self.max_passos:
            return self.para_estado(nova), recompensa, True, "limite"
        return self.para_estado(nova), recompensa, False, ""

    def caminho_guloso(self, escolher_acao) -> dict:
        """Segue a política aprendida (sem exploração) e devolve o trajeto."""
        estado = self.reset()
        caminho = [list(self.pos)]
        total, motivo = 0.0, "limite"
        for _ in range(self.max_passos):
            estado, r, fim, m = self.step(int(escolher_acao(estado)))
            caminho.append(list(self.pos))
            total += r
            if fim:
                motivo = m or "limite"
                break
        return {"caminho": caminho, "recompensa": round(total, 2),
                "passos": len(caminho) - 1, "resultado": motivo}


def media_movel(valores, janela: int = 20) -> list[float]:
    v = np.asarray(valores, dtype=float)
    if len(v) == 0:
        return []
    cs = np.cumsum(np.insert(v, 0, 0.0))
    out = []
    for i in range(1, len(v) + 1):
        ini = max(0, i - janela)
        out.append(round((cs[i] - cs[ini]) / (i - ini), 3))
    return out
