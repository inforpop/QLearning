# Q-Learning: Aprendizado por Reforço em Python — Computação Clássica × Quântica

Dashboard em **Flask** com duas abas que treinam, em tempo real, dois agentes no mesmo labirinto (GridWorld 6×6 com paredes e armadilhas):

| Aba | Como o agente escolhe a ação | Como o agente aprende |
|---|---|---|
| 🖥️ **Computação Clássica** | ε-greedy sobre a tabela Q | Q(s,a) ← Q(s,a) + α·[r + γ·maxₐ′ Q(s′,a′) − Q(s,a)] |
| ⚛️ **Computação Quântica** | **Medição** de um registrador de 2 qubits em superposição das 4 ações | **Amplificação de amplitude (Grover)** proporcional ao erro TD: Δθ = k·[r + γ·V(s′) − V(s)] |

A aba quântica traz também um **laboratório do algoritmo de Grover com 2 qubits** (H⊗H → oráculo → difusão), simulado com portas reais (H, X, CZ) em NumPy.

📞 **Meus Contatos:** [www.inforpop.com](https://www.inforpop.com)
📱 WhatsApp: [55 21 99961-8643](https://wa.me/5521999618643)
✉️ Email: [inforpop@hotmail.com](mailto:inforpop@hotmail.com)
🔗 LinkedIn: [Pedro Paulo Ribeiro](https://www.linkedin.com/in/pedro-paulo-ribeiro-pcd-1451498/)

---

## Estrutura

```
qlearning-dashboard/
├── app.py                 # Flask: páginas e API
├── rl/
│   ├── ambiente.py        # GridWorld (estados, ações, recompensas)
│   ├── classico.py        # Q-Learning tabular ε-greedy
│   └── quantico.py        # QRL: simulador de 2 qubits, medição, Grover
├── templates/index.html   # Dashboard (abas Clássica / Quântica)
├── static/
│   ├── css/style.css
│   ├── js/dashboard.js    # Gráficos SVG interativos (sem CDN)
│   └── img/anexo.png      # Imagem do cabeçalho
├── tests/test_app.py      # Testes (pytest)
├── requirements.txt
├── Procfile               # Heroku: gunicorn
└── .python-version        # Heroku: versão do Python
```

## API

| Método | Rota | Corpo / parâmetros |
|---|---|---|
| GET | `/` | Dashboard |
| POST | `/api/classico/treinar` | `{"episodios":400,"alpha":0.1,"gamma":0.95,"epsilon":1.0,"decaimento":0.99,"semente":42}` |
| POST | `/api/quantico/treinar` | `{"episodios":400,"alpha":0.1,"gamma":0.95,"k":0.05,"semente":42}` |
| GET | `/api/quantico/grover?marcado=2` | Etapas do Grover de 2 qubits |
| GET | `/health` | `{"status":"ok"}` |

## Rodar localmente

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python app.py
# abra http://localhost:5000
```

Testes: `pip install pytest && pytest -q`

## Implantação no Heroku

Pré-requisitos: conta no Heroku, [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli) e Git.

```bash
cd qlearning-dashboard
git init
git add .
git commit -m "Q-Learning clássico x quântico"

heroku login
heroku create qlearning-inforpop        # escolha um nome disponível
git push heroku main                    # (ou: git push heroku master)
heroku ps:scale web=1
heroku open
```

Logs: `heroku logs --tail`

> O Heroku detecta Python pelo `requirements.txt`, usa a versão do `.python-version` e sobe o app pelo `Procfile` (`gunicorn app:app`). Não há dependências pesadas: a parte quântica é simulada em NumPy.

## Sobre a parte quântica

Baseada em Dong, Chen, Li & Tarn, *Quantum Reinforcement Learning*, IEEE Trans. SMC-B, 2008.

* Cada estado guarda |ψ⟩ = c₀|00⟩ + c₁|01⟩ + c₂|10⟩ + c₃|11⟩ (↑ → ↓ ←), iniciado em H⊗H|00⟩ (25% cada).
* A ação é obtida medindo |ψ⟩ — a exploração é intrínseca (não há ε).
* Após a ação, |ψ⟩ gira no plano {|a⟩, |a⊥⟩}: uma iteração completa de Grover é uma rotação de 2θ; aqui usamos a versão fracionária, proporcional ao erro TD (positivo amplifica, negativo atenua). As probabilidades ficam entre 1% e 97% para nunca perder a exploração.
* O teste `test_rotacao_equivale_a_iteracao_de_grover` confirma que a rotação de 2θ é idêntica ao operador G = U_ψ·U_a.

Autor: **Pedro Paulo Ribeiro** — Cientista de Dados · desenvolvedor desde 1987.
