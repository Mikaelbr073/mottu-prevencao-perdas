# -*- coding: utf-8 -*-
# Monta o notebook do case Mottu.
# Rodar da raiz do projeto:  python analise/build_notebook.py
# Saida: notebook/mottu_prevencao_perdas.ipynb

import json, os

cells = []
def md(s):   cells.append(("markdown", s))
def code(s): cells.append(("code", s))


# ============================================================ CAPA
md("""# Prevenção de Perdas — Mottu

### Case 1 · Apropriação indébita em locações

Base: 500 locações encerradas em 6 meses. Dados sintéticos.""")


# ============================================================ SUMARIO
md("""## Sumário

| Seção | O que tem |
|---|---|
| **1. A resposta em uma página** | As três perguntas do case, respondidas com número |
| **2. Base** | Integridade, variáveis fora da regra, alvo |
| **3. Pergunta 1 — Sinais** | Isolado vs. combinado, matriz 2×2, lift |
| **4. Pergunta 2 — Janela** | 9 dias de mediana; SLA de 72h |
| **5. Pergunta 3 — Grupos** | G1/G2/G3, esforço e curva de capacidade |
| **6. Metas e critérios** | Metas, SLA e gatilhos de revisão |
| **7. Extras** | Falha de detecção, projeção, cartão de triagem |
| **8. Limitações** | |
| **9. Apêndice** | Tabelas completas |

---

Todo número sai do código da célula acima dele.

**O detalhamento completo está no PDF.** Aqui ficam os números e os gráficos.""")


# ============================================================ SETUP
md("""---
## Preparação""")

code('''import io, os, sys, textwrap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.patches import Rectangle

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 60)

# paleta
VERDE    = "#0FBF61"
ESCURO   = "#101820"
CINZA    = "#B8BFC7"
CINZA_CL = "#E8EBED"
VERMELHO = "#E0443E"
AMBAR    = "#F5A623"
AZUL     = "#2D7FF9"

plt.rcParams.update({
    "figure.dpi": 110,
    "savefig.dpi": 110,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "axes.edgecolor": CINZA,
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": CINZA_CL,
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
    "xtick.color": ESCURO,
    "ytick.color": ESCURO,
    "text.color": ESCURO,
    "axes.labelcolor": ESCURO,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "legend.frameon": False,
})

def limpa(ax, x=True, y=True):
    for lado in ["top", "right"]:
        ax.spines[lado].set_visible(False)
    if not x: ax.xaxis.grid(False)
    if not y: ax.yaxis.grid(False)
    return ax

def pct(v, casas=1):
    return f"{v*100:.{casas}f}%".replace(".", ",")

print("bibliotecas carregadas")''')

code('''ARQUIVO = "dados -PrevencaoPerdas_Base.xlsx"
RAW_URL = ("https://raw.githubusercontent.com/Mikaelbr073/"
           "mottu-prevencao-perdas/main/dados%20-PrevencaoPerdas_Base.xlsx")

def carrega_base():
    for c in [ARQUIVO, os.path.join("..", ARQUIVO), os.path.join("/content", ARQUIVO)]:
        if os.path.exists(c):
            return pd.read_excel(c, sheet_name="Dados")
    try:
        return pd.read_excel(RAW_URL, sheet_name="Dados")
    except Exception:
        from google.colab import files
        subiu = files.upload()
        return pd.read_excel(io.BytesIO(subiu[list(subiu)[0]]), sheet_name="Dados")

df = carrega_base()
print(f"{len(df)} locacoes, {df.shape[1]} colunas")''')

code('''# Colunas derivadas. Tudo o que a analise usa nasce aqui.

FLAGS = ["parou_48h", "sem_ping_24h", "violacao_blindagem",
         "device_compartilhado", "jornada_impossivel"]

for c in FLAGS:
    df[c] = (df[c] == "SIM")

df["APR"]   = df.desfecho == "APROPRIADA"                    # moto perdida
df["REC"]   = df.desfecho == "RECUPERADA_POS_ACIONAMENTO"    # RecOps recuperou
df["RISCO"] = df.desfecho != "DEVOLVIDA"                     # alvo da analise

df["inad"]      = df.dias_inadimplencia_max
df["inad15"]    = df.inad >= 15
df["inad30"]    = df.inad >= 30
df["tem_sinal"] = df.dia_primeiro_sinal.notna()
df["janela"]    = df.dia_desfecho - df.dia_primeiro_sinal
df["n_flags"]   = df[FLAGS].sum(axis=1)

# 6 meses de base -> 26 semanas. Usado para converter volume em vazao.
SEMANAS = 26.0

TX_APR   = df.APR.mean()
TX_RISCO = df.RISCO.mean()

print(f"apropriacao : {pct(TX_APR)}   ({df.APR.sum()} de {len(df)})")
print(f"risco       : {pct(TX_RISCO)}   ({df.RISCO.sum()} de {len(df)})")''')


# ============================================================ 1. RESPOSTA
md("""---
# 1. Resposta em uma página

**1 · Sinais.** Nenhum sinal isolado prediz. `parou_48h` sozinho: 0 perdas em 71
casos. Inadimplência ≥30d sozinha: 0 em 24. O par `parou_48h` + `sem_ping_24h`
leva a 43,8% de apropriação contra base de 4,8%; com inadimplência ≥30d, 81,2%.

**2 · Janela.** Mediana de 9 dias, todas entre o 5º e o 12º. Nenhuma perda antes
do 3º dia, o que fixa o **SLA em 72h**. Em 7 dias, 26% já foram perdidas.

**3 · Grupos.**

| grupo | regra | casos/semana | risco | ação |
|---|---|---|---|---|
| **G1** | parada + sem ping + (inad ≥15d ou blindagem) | **1,2** | 90% | contato em 72h + busca preparada |
| **G2** | dois sinais, sem agravante | 1,3 | 54% | contato em 5 dias |
| **G3** | um sinal isolado | 7,2 | 17% | régua automática |

G1 concentra 19 das 24 perdas e cabe em 1,2 caso/semana. Hoje ele fica atrás de
uma fila de 9,7 atendida por ordem de chegada.""")

code('''fig, axes = plt.subplots(1, 3, figsize=(12, 3.4))

# --- painel 1: onde a perda acontece
tel2 = df.parou_48h & df.sem_ping_24h
grupos = [
    ("Nenhum\\nsinal",      (~df.parou_48h) & (~df.sem_ping_24h)),
    ("Um sinal\\nsozinho",  (df.parou_48h ^ df.sem_ping_24h)),
    ("Parada +\\nsem ping", tel2),
]
xs   = [g[0] for g in grupos]
taxa = [df.APR[g[1]].mean() for g in grupos]
ns   = [int(g[1].sum()) for g in grupos]

ax = axes[0]
barras = ax.bar(xs, taxa, color=[CINZA, CINZA, VERMELHO], width=0.6)
ax.axhline(TX_APR, color=ESCURO, ls="--", lw=1)
ax.text(2.45, TX_APR + 0.012, f"base {pct(TX_APR)}", ha="right", fontsize=8, color=ESCURO)
for b, t, n in zip(barras, taxa, ns):
    ax.text(b.get_x() + b.get_width()/2, t + 0.015, pct(t), ha="center",
            fontweight="bold", fontsize=10)
    ax.text(b.get_x() + b.get_width()/2, -0.045, f"n={n}", ha="center",
            fontsize=8, color=CINZA)
ax.set_ylim(0, 0.55)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.set_title("Onde a perda acontece", loc="left")
limpa(ax, x=False)

# --- painel 2: a janela
ax = axes[1]
jan = df.loc[df.APR & df.tem_sinal, "janela"]
ax.hist(jan, bins=range(4, 15), color=VERMELHO, alpha=0.85, edgecolor="white")
ax.axvline(jan.median(), color=ESCURO, lw=1.6)
ax.text(jan.median() + 0.25, ax.get_ylim()[1]*0.88,
        f"mediana\\n{int(jan.median())} dias", fontsize=9, fontweight="bold")
ax.axvspan(0, 3, color=VERDE, alpha=0.18)
ax.text(1.5, ax.get_ylim()[1]*0.55, "SLA\\n72h", ha="center", fontsize=8,
        color="#0a7a3e", fontweight="bold")
ax.set_xlim(0, 14)
ax.set_xlabel("dias entre o 1º sinal e a perda")
ax.set_title("Quanto tempo existe para agir", loc="left")
limpa(ax, x=False)

# --- painel 3: fila vs perda
ax = axes[2]
g1 = tel2 & (df.inad15 | df.violacao_blindagem | df.jornada_impossivel)
g2 = (~g1) & (tel2 | ((df.parou_48h | df.sem_ping_24h) & (df.inad15 | df.violacao_blindagem)))
g3 = (~g1) & (~g2) & (df.parou_48h | df.sem_ping_24h | df.inad15)
nomes = ["G1", "G2", "G3"]
fila  = [m.sum() / df.tem_sinal.sum() for m in (g1, g2, g3)]
perda = [df.APR[m].sum() / df.APR.sum() for m in (g1, g2, g3)]
y = np.arange(3)
ax.barh(y + 0.19, fila,  height=0.34, color=CINZA,    label="% da fila")
ax.barh(y - 0.19, perda, height=0.34, color=VERMELHO, label="% das perdas")
for i, (f, p) in enumerate(zip(fila, perda)):
    ax.text(f + 0.02, i + 0.19, pct(f, 0), va="center", fontsize=9)
    ax.text(p + 0.02, i - 0.19, pct(p, 0), va="center", fontsize=9, fontweight="bold")
ax.set_yticks(y); ax.set_yticklabels(nomes)
ax.set_xlim(0, 1.05); ax.invert_yaxis()
ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.legend(loc="lower right", fontsize=8)
ax.set_title("A fila está invertida", loc="left")
limpa(ax, y=False)

plt.tight_layout()
plt.show()

print(f"G1 = {int(g1.sum())} casos em 6 meses = {g1.sum()/SEMANAS:.1f} por semana")''')


# ============================================================ 2. DADOS
md("""---
# 2. Base""")

code('''checagens = [
    ("linhas",                        len(df),                                          "500 esperadas"),
    ("locacao_id duplicado",          int(df.locacao_id.duplicated().sum()),             "0"),
    ("linhas duplicadas",             int(df.drop(columns=["locacao_id"]).duplicated().sum()), "0"),
    ("nulos fora de dia_primeiro_sinal",
        int(df.drop(columns=["dia_primeiro_sinal", "janela"]).isna().sum().sum()),        "0"),
    ("sinal depois do desfecho",      int((df.dia_primeiro_sinal > df.dia_desfecho).sum()), "0"),
    ("desfecho alem do contrato",     int((df.dia_desfecho > df.dias_locacao).sum()),    "0"),
    ("dia de desfecho <= 0",          int((df.dia_desfecho <= 0).sum()),                 "0"),
]
print(f"{'checagem':<38}{'valor':>8}   esperado")
print("-" * 62)
for nome, valor, esperado in checagens:
    print(f"{nome:<38}{valor:>8}   {esperado}")

vazios = int(df.dia_primeiro_sinal.isna().sum())
print(f"\\ndia_primeiro_sinal vazio: {vazios} — nao e falha, e a marca de "
      f"'nenhum sinal de risco'")''')

code('''vaza = (df.dias_locacao - df.dia_desfecho) > 0
acerto = (vaza == df.RISCO).mean()
print(f"dias_locacao fora da analise: sozinha acerta o desfecho em {pct(acerto)} dos casos (vazamento)")

linhas = []
for c in FLAGS + ["inad15", "inad30"]:
    m = df[c]
    n = int(m.sum())
    if n == 0:
        continue
    linhas.append({"sinal": c, "n": n, "precisao": df.APR[m].mean(),
                   "lift": df.APR[m].mean() / TX_APR,
                   "recall": df.APR[m].sum() / df.APR.sum()})
rank = pd.DataFrame(linhas).sort_values("lift", ascending=False).reset_index(drop=True)
rank["uso"] = np.where(rank.n < 20, "fora (amostra < 20)", "na regra")
display(rank.style.format({"precisao": "{:.1%}", "lift": "{:.1f}x", "recall": "{:.1%}"}))

dev = df[df.desfecho == "DEVOLVIDA"].copy()
dev["faixa"] = pd.qcut(dev.dia_desfecho, 4)
expo = dev.groupby("faixa", observed=True).agg(
    n=("APR", "size"), parou_48h=("parou_48h", "mean"),
    sem_ping_24h=("sem_ping_24h", "mean"), inad_media=("inad", "mean"))
display(expo.style.format({"parou_48h": "{:.1%}", "sem_ping_24h": "{:.1%}", "inad_media": "{:.1f}"}))
print("taxa de flag plana entre contrato curto e longo: sem vies de exposicao")''')

md("""Fora da regra: `dias_locacao` (vazamento), `jornada_impossivel` (n=2),
`device_compartilhado` (n=14), perfil demográfico (lift ≈ 1).

**Alvo = `APROPRIADA + RECUPERADA` (16%).** `RECUPERADA` é desfecho tratado —
sem acionamento teria virado apropriação. `APROPRIADA` isolada (4,8%) é a
métrica de resultado.""")

code('''fig, ax = plt.subplots(figsize=(7.5, 1.9))
cont = df.desfecho.value_counts()
ordem = ["DEVOLVIDA", "RECUPERADA_POS_ACIONAMENTO", "APROPRIADA"]
cores = [CINZA_CL, AMBAR, VERMELHO]
esq = 0
for nome, cor in zip(ordem, cores):
    v = cont[nome]
    ax.barh([0], [v], left=esq, color=cor, edgecolor="white", height=0.55)
    ax.text(esq + v/2, 0, f"{nome.split('_')[0]}\\n{v} ({pct(v/len(df),1)})",
            ha="center", va="center", fontsize=9,
            color=ESCURO if nome == "DEVOLVIDA" else "white", fontweight="bold")
    esq += v
ax.plot([cont["DEVOLVIDA"], len(df)], [-0.42, -0.42], color=ESCURO, lw=1.4)
ax.text((cont["DEVOLVIDA"] + len(df))/2, -0.62,
        f"alvo da analise: risco de perda = {pct(TX_RISCO)}",
        ha="center", fontsize=9, fontweight="bold")
ax.set_xlim(0, len(df)); ax.set_ylim(-0.85, 0.42)
ax.axis("off")
ax.set_title("Os tres desfechos, e o que estou tentando prever", loc="left")
plt.tight_layout(); plt.show()''')


# ============================================================ 3. PERGUNTA 1
md("""---
# 3. Pergunta 1 — Sinais""")

md("""### 3.1 Sinal isolado vs. combinado""")

code('''def bloco(mask, rotulo):
    n = int(mask.sum())
    return {
        "condicao": rotulo,
        "n": n,
        "apropriadas": int(df.APR[mask].sum()),
        "taxa_apropriacao": df.APR[mask].mean() if n else np.nan,
        "taxa_risco": df.RISCO[mask].mean() if n else np.nan,
    }

tel2 = df.parou_48h & df.sem_ping_24h
linhas = [
    bloco(df.parou_48h & ~df.sem_ping_24h,                    "parou_48h sozinho"),
    bloco(~df.parou_48h & df.sem_ping_24h,                    "sem_ping_24h sozinho"),
    bloco(df.violacao_blindagem & ~(df.parou_48h | df.sem_ping_24h), "blindagem sozinha"),
    bloco(df.inad30 & ~(df.parou_48h | df.sem_ping_24h),      "inadimplencia >=30d sozinha"),
    bloco(tel2,                                               "parou_48h + sem_ping_24h"),
    bloco(tel2 & df.inad15,                                   "   + inadimplencia >=15d"),
    bloco(tel2 & df.inad30,                                   "   + inadimplencia >=30d"),
    bloco(df.violacao_blindagem & (df.parou_48h | df.sem_ping_24h), "blindagem + telemetria"),
]
comp = pd.DataFrame(linhas)
display(comp.style.format({"taxa_apropriacao": "{:.1%}", "taxa_risco": "{:.1%}"})
            .background_gradient(subset=["taxa_apropriacao"], cmap="Reds"))

print(f"base de comparacao: {pct(TX_APR)} de apropriacao")''')

md("""### 3.2 Matriz `parou_48h` × `sem_ping_24h`""")

code('''fig, ax = plt.subplots(figsize=(6.2, 4.2))
M = np.zeros((2, 2)); N = np.zeros((2, 2), dtype=int)
for i, p in enumerate([False, True]):
    for j, s in enumerate([False, True]):
        m = (df.parou_48h == p) & (df.sem_ping_24h == s)
        N[i, j] = int(m.sum())
        M[i, j] = df.APR[m].mean() if m.sum() else 0

im = ax.imshow(M, cmap="Reds", vmin=0, vmax=0.5)
for i in range(2):
    for j in range(2):
        ax.text(j, i - 0.10, pct(M[i, j]), ha="center", va="center",
                fontsize=19, fontweight="bold",
                color="white" if M[i, j] > 0.25 else ESCURO)
        ax.text(j, i + 0.20, f"{int(M[i,j]*N[i,j]+0.5)} de {N[i,j]}",
                ha="center", va="center", fontsize=9,
                color="white" if M[i, j] > 0.25 else CINZA)
ax.set_xticks([0, 1]); ax.set_xticklabels(["ping normal", "SEM PING 24h"])
ax.set_yticks([0, 1]); ax.set_yticklabels(["rodando", "PARADA 48h"])
ax.set_title("Taxa de apropriação por combinação de sinal", loc="left", pad=12)
ax.grid(False)
for s in ax.spines.values():
    s.set_visible(False)
plt.tight_layout(); plt.show()

print(f"Uma celula sozinha concentra {int(df.APR[tel2].sum())} das {int(df.APR.sum())} perdas da base.")''')

md("""### 3.3 Lift por sinal""")

code('''r = rank.sort_values("lift", ascending=True)
fig, ax = plt.subplots(figsize=(9, 4.2))
cores = [CINZA if n < 20 else VERMELHO for n in r.n]
b = ax.barh(r.sinal, r.lift, color=cores, height=0.62)
ax.axvline(1, color=ESCURO, lw=1.2)
ax.text(1.15, -0.45, "lift 1 = igual a base", fontsize=8, color=ESCURO)
for barra, n, lf in zip(b, r.n, r.lift):
    ax.text(lf + 0.35, barra.get_y() + barra.get_height()/2,
            f"{lf:.1f}x   n={n}", va="center", fontsize=9,
            fontweight="bold" if n >= 20 else "normal",
            color=ESCURO if n >= 20 else CINZA)
ax.set_xlim(0, max(r.lift) * 1.30)
ax.set_xlabel("lift sobre a taxa base de apropriação")
ax.set_title("Cinza = amostra pequena demais para virar regra", loc="left")
limpa(ax, y=False)
plt.tight_layout(); plt.show()''')

md("""### Resposta

O preditor é o par `parou_48h` + `sem_ping_24h`: **43,8%** de apropriação contra
4,8% da base, capturando **21 das 24 perdas**.

Inadimplência é amplificador: 63,3% com ≥15d, 81,2% com ≥30d. Sozinha, nada.

`violacao_blindagem` sozinha não vale (0 em 25), mas com telemetria ruim leva o
risco a **91,7%**.

Fora da regra: `jornada_impossivel` (n=2), `device_compartilhado` (n=14) e as
variáveis de perfil (lift ≈ 1).""")


# ============================================================ 4. PERGUNTA 2
md("""---
# 4. Pergunta 2 — Janela

`janela = dia_desfecho - dia_primeiro_sinal`. Nem todo sinal liga esse relógio;
a regra reconstruída está na seção 7.""")

code('''jan = df[df.tem_sinal].groupby("desfecho").janela.describe(
    percentiles=[.1, .25, .5, .75, .9])
display(jan[["count", "mean", "min", "25%", "50%", "75%", "max"]]
        .style.format("{:.1f}"))

ap = df.loc[df.APR & df.tem_sinal, "janela"]
print(f"\\nAs {len(ap)} perdas com sinal, em dias:")
print("  " + ", ".join(str(int(v)) for v in sorted(ap)))
print(f"\\nmediana {ap.median():.0f} · minimo {ap.min():.0f} · maximo {ap.max():.0f}")''')

code('''fig, axes = plt.subplots(1, 2, figsize=(12, 3.9))

# --- distribuicao por desfecho
ax = axes[0]
dados, rotulos, cores = [], [], []
for nome, cor in [("DEVOLVIDA", CINZA), ("RECUPERADA_POS_ACIONAMENTO", AMBAR),
                  ("APROPRIADA", VERMELHO)]:
    v = df.loc[df.tem_sinal & (df.desfecho == nome), "janela"].dropna()
    dados.append(v); rotulos.append(nome.split("_")[0].title()); cores.append(cor)
_kw = dict(patch_artist=True, widths=0.55,
           medianprops=dict(color=ESCURO, lw=1.8),
           flierprops=dict(marker="o", markersize=3, alpha=0.35))
try:                                   # matplotlib >= 3.10
    bp = ax.boxplot(dados, orientation="horizontal", **_kw)
except TypeError:                      # versoes anteriores
    bp = ax.boxplot(dados, vert=False, **_kw)
for caixa, cor in zip(bp["boxes"], cores):
    caixa.set_facecolor(cor); caixa.set_edgecolor(cor); caixa.set_alpha(0.75)
ax.set_yticklabels(rotulos)
ax.set_xlabel("dias entre o 1º sinal e o fim da locação")
ax.set_title("A perda tem prazo. A devolução não.", loc="left")
limpa(ax, y=False)

# --- curva acumulada
ax = axes[1]
dias = np.arange(0, 15)
acum = [(ap <= d).mean() for d in dias]
ax.plot(dias, acum, color=VERMELHO, lw=2.4, marker="o", markersize=4)
ax.fill_between(dias, acum, color=VERMELHO, alpha=0.10)
ax.axvline(3, color=VERDE, lw=1.8, ls="--")
ax.text(3.2, 0.60, "SLA 72h\\nchega antes\\nde todas", fontsize=9,
        color="#0a7a3e", fontweight="bold")
for d in [5, 7, 10]:
    v = (ap <= d).mean()
    ax.annotate(f"dia {d}: {pct(v,0)}", xy=(d, v), xytext=(d - 3.6, v + 0.09),
                fontsize=8.5, arrowprops=dict(arrowstyle="->", color=CINZA, lw=0.9))
ax.set_ylim(0, 1.05); ax.set_xlim(0, 14)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.set_xlabel("dias após o primeiro sinal")
ax.set_ylabel("perdas já ocorridas")
ax.set_title("Quanto tempo o acionamento tem", loc="left")
limpa(ax)

plt.tight_layout(); plt.show()

print("acumulado de perdas apos o 1o sinal")
for d in [3, 5, 7, 10, 14]:
    print(f"  ate {d:>2} dias : {pct((ap<=d).mean(),1):>6}  ({int((ap<=d).sum())} de {len(ap)})")''')

md("""### Resposta

**Média 8,7 dias, mediana 9.** As 23 perdas com sinal caem todas entre o dia 5
e o dia 12.

| prazo de contato | perdas já ocorridas |
|---|---|
| **72 horas** | **0%** |
| 5 dias | 8,7% |
| 7 dias | 26,1% |
| 10 dias | 82,6% |

**SLA do G1 = 72 horas** — o único prazo em que nenhuma perda tinha acontecido.

Duas ressalvas: a janela sozinha não separa perda de recuperação (mediana 11
dias, faixas sobrepostas), porque a janela da recuperada inclui o tempo de ação
da equipe; o que separa é o teto de 12 dias. E devolução normal tem mediana de
51 dias, com cauda até 218 — sinal velho quase nunca é perda.""")


# ============================================================ 5. PERGUNTA 3
md("""---
# 5. Pergunta 3 — Grupos

### 5.1 Critérios

Fora da regra: `jornada_impossivel` (n=2), `device_compartilhado` (n=14) e
perfil demográfico. Corte de inadimplência em 15d = limiar que a própria
operação já usa para ligar o relógio de sinal (seção 7).""")

code('''G1 = tel2 & (df.inad15 | df.violacao_blindagem | df.jornada_impossivel)
G2 = (~G1) & (tel2 | ((df.parou_48h | df.sem_ping_24h) & (df.inad15 | df.violacao_blindagem)))
G3 = (~G1) & (~G2) & (df.parou_48h | df.sem_ping_24h | df.inad15)
G0 = ~(G1 | G2 | G3)

df["grupo"] = np.select([G1, G2, G3], ["G1", "G2", "G3"], default="fora")

def resumo(mask, nome, regra):
    n = int(mask.sum())
    return {
        "grupo": nome,
        "regra": regra,
        "n": n,
        "% da carteira": n / len(df),
        "casos/semana": n / SEMANAS,
        "perdas": int(df.APR[mask].sum()),
        "% das perdas": df.APR[mask].sum() / df.APR.sum(),
        "risco": df.RISCO[mask].mean() if n else 0,
    }

tabela = pd.DataFrame([
    resumo(G1, "G1 Critico",  "parada + sem ping + (inad>=15 ou blindagem)"),
    resumo(G2, "G2 Alto",     "dois sinais, sem agravante"),
    resumo(G3, "G3 Vigiar",   "um sinal isolado"),
    resumo(G0, "fora",        "nenhum sinal relevante"),
])
display(tabela.style.format({"% da carteira": "{:.1%}", "casos/semana": "{:.1f}",
                             "% das perdas": "{:.1%}", "risco": "{:.1%}"})
        .background_gradient(subset=["risco"], cmap="Reds"))

print(f"G1        -> {int(df.APR[G1].sum())} das {int(df.APR.sum())} perdas")
print(f"G1+G2     -> {int(df.APR[G1|G2].sum())} das {int(df.APR.sum())} perdas, "
      f"em {pct((G1|G2).mean())} da carteira")''')

md("""### 5.2 Esforço por grupo""")

code('''fila_semana = df.tem_sinal.sum() / SEMANAS
carteira_ativa = len(df) * df.dia_desfecho.mean() / 182

print(f"carteira ativa equivalente : ~{carteira_ativa:.0f} motos")
print(f"fila de sinais             : {fila_semana:.1f} por semana")
print()
for nome, m in [("G1", G1), ("G2", G2), ("G3", G3)]:
    print(f"  {nome}: {m.sum()/SEMANAS:5.1f} caso(s)/semana   "
          f"risco {pct(df.RISCO[m].mean(),0):>5}   "
          f"{pct(m.sum()/df.tem_sinal.sum(),0):>5} da fila")

print()
print("PREMISSA declarada: 1 squad de RecOps sustenta ~40 acionamentos ativos")
print("por semana a cada 500 locacoes encerradas (~8/dia com follow-up).")
carga = (G1.sum() + G2.sum()) / SEMANAS
print(f"G1+G2 = {carga:.1f} acionamentos/semana = {carga/40:.0%} dessa capacidade.")''')

md("""### 5.3 A fila está invertida""")

code('''ef = []
for nome, m in [("G1", G1), ("G2", G2), ("G3", G3), ("fora", G0)]:
    rec, apr = int(df.REC[m].sum()), int(df.APR[m].sum())
    ef.append({"grupo": nome, "recuperadas": rec, "perdidas": apr,
               "casos de risco": rec + apr,
               "sucesso do acionamento": rec / (rec + apr) if (rec + apr) else np.nan})
ef = pd.DataFrame(ef)
display(ef.style.format({"sucesso do acionamento": "{:.1%}"}))

fig, ax = plt.subplots(figsize=(8.4, 3.6))
sub = ef[ef.grupo != "fora"]
x = np.arange(len(sub))
ax.bar(x, sub["sucesso do acionamento"], color=[VERMELHO, AMBAR, VERDE], width=0.55)
for i, (s, r) in enumerate(zip(sub["sucesso do acionamento"], sub["casos de risco"])):
    ax.text(i, s + 0.03, pct(s, 0), ha="center", fontweight="bold", fontsize=12)
    ax.text(i, -0.09, f"{r} casos de risco", ha="center", fontsize=8.5, color=CINZA)
ax.set_xticks(x); ax.set_xticklabels(["G1 Crítico", "G2 Alto", "G3 Vigiar"])
ax.set_ylim(0, 1.12)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.set_title("O time acerta onde não importa e erra onde importa", loc="left")
limpa(ax, x=False)
plt.tight_layout(); plt.show()''')

md("""Ressalva: `RECUPERADA` só existe porque a equipe agiu — o contrafactual do
G3 não é observável. O que é sólido: **19 das 24 perdas estão no G1**.""")

md("""### 5.4 Onde cortar a fila""")

code('''df["score"] = (df.parou_48h.astype(int) * 2 + df.sem_ping_24h.astype(int) * 2
               + df.violacao_blindagem.astype(int) + df.inad15.astype(int)
               + df.inad30.astype(int) + df.jornada_impossivel.astype(int)
               + df.device_compartilhado.astype(int))

ordenado = df.sort_values("score", ascending=False)
tamanhos = [10, 15, 20, 25, 30, 40, 50, 65, 80, 100, 130, 160, 187, 220, 253]
curva = []
for n in tamanhos:
    top = ordenado.head(n)
    curva.append({"top N": n, "% carteira": n/len(df), "casos/semana": n/SEMANAS,
                  "recall risco": top.RISCO.sum()/df.RISCO.sum(),
                  "recall perdas": top.APR.sum()/df.APR.sum()})
curva = pd.DataFrame(curva)

fig, ax = plt.subplots(figsize=(9, 4.2))
ax.plot(curva["casos/semana"], curva["recall perdas"], color=VERMELHO, lw=2.4,
        marker="o", markersize=4, label="perdas capturadas")
ax.plot(curva["casos/semana"], curva["recall risco"], color=AZUL, lw=2.0,
        marker="s", markersize=3.5, label="casos de risco capturados")
corte = 40 / SEMANAS
ax.axvline(corte, color=ESCURO, ls="--", lw=1.4)
ax.text(corte + 0.12, 0.30, "ponto de operação\\ntop 40 · 1,5 caso/semana",
        fontsize=9, fontweight="bold")
ax.annotate("daqui para a direita\\nnão captura nenhuma perda a mais",
            xy=(3.2, 0.96), xytext=(4.2, 0.62), fontsize=8.5, color=CINZA,
            arrowprops=dict(arrowstyle="->", color=CINZA, lw=0.9))
ax.set_xlabel("acionamentos por semana")
ax.set_ylabel("cobertura")
ax.set_ylim(0, 1.05)
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.legend(loc="lower right")
ax.set_title("A curva satura cedo", loc="left")
limpa(ax)
plt.tight_layout(); plt.show()

display(curva[curva["top N"].isin([25, 30, 40, 65, 130, 253])]
        .style.format({"% carteira": "{:.1%}", "casos/semana": "{:.1f}",
                       "recall risco": "{:.0%}", "recall perdas": "{:.0%}"}))''')

md("""### Resposta

| grupo | regra | esforço | por quê |
|---|---|---|---|
| **G1 · 1,2/sem · risco 90%** | parada + sem ping + (inad ≥15d ou blindagem) | SLA 72h, contato ativo, busca preparada em paralelo | 19 das 24 perdas estão aqui |
| **G2 · 1,3/sem · risco 54%** | dois sinais, sem agravante | mensagem em até 5 dias, liga só se não responder | metade vira risco real |
| **G3 · 7,2/sem · risco 17%** | um sinal isolado | régua automática, sem gente, sobe se aparecer 2º sinal | 74% da fila, 2 perdas em 187 casos |

**G1 + G2 = 13% da carteira e 21 das 24 perdas**, a 2,5 acionamentos/semana.""")


# ============================================================ 6. METAS
md("""---
# 6. Metas e critérios""")

code('''metas = pd.DataFrame([
    {"o que": "SLA de contato no G1", "meta": "72h desde o 1º sinal",
     "hoje": "sem SLA definido",
     "por que": "nenhuma perda da base ocorreu antes do dia 3"},
    {"o que": "Sucesso do acionamento no G1", "meta": "de 29,6% para 65%",
     "hoje": "29,6%",
     "por que": "G2 ja opera a 89,5%; 65% e a metade do caminho"},
    {"o que": "Taxa de apropriação", "meta": "abaixo de 3,0% em 2 trimestres",
     "hoje": "4,8%",
     "por que": "cenario base da projecao da secao 7"},
    {"o que": "Cobertura das perdas pela fila", "meta": "manter acima de 90%",
     "hoje": "92% no top 40",
     "por que": "abaixo disso o corte esta apertado demais"},
    {"o que": "Esforço humano no G3", "meta": "zero ligacao ativa",
     "hoje": "74% da fila",
     "por que": "2 perdas em 187 casos nao pagam contato humano"},
    {"o que": "Revisão dos limiares", "meta": "trimestral",
     "hoje": "nao ha",
     "por que": "regra fixa apodrece quando o comportamento muda"},
])
display(metas.style.hide(axis="index"))''')

md("""**Parada da fila:** top 40/semana — além disso, capacidade extra vai
para reduzir o tempo de resposta do G1, não para alargar a fila.

**Promoção entre grupos:** G3 → G2 com um 2º sinal; G2 → G1 com inadimplência
≥15d ou blindagem violada.

**Revisão:** se a precisão do G1 cair abaixo de 50% por 2 meses seguidos, os
limiares precisam ser recalculados.""")


# ============================================================ 7. EXTRAS
md("""---
# 7. Extras""")

md("""### 7.1 Falha de detecção: dois sinais não ligam o relógio""")

code('''regra = (df.parou_48h | df.sem_ping_24h | df.jornada_impossivel | (df.inad >= 15))
print(f"divergencias entre a regra reconstruida e o campo real: "
      f"{int((regra != df.tem_sinal).sum())} em {len(df)}")
print()
print("  dia_primeiro_sinal existe  <=>  parou_48h  OU  sem_ping_24h")
print("                                  OU jornada_impossivel")
print("                                  OU dias_inadimplencia_max >= 15")
print()

invisiveis = ((~df.parou_48h) & (~df.sem_ping_24h) & (~df.jornada_impossivel)
              & (~df.inad15) & (df.violacao_blindagem | df.device_compartilhado))
print(f"Locacoes com blindagem violada ou device compartilhado que NUNCA")
print(f"entraram no radar: {int(invisiveis.sum())}")
print(f"  blindagem            : {int((invisiveis & df.violacao_blindagem).sum())}")
print(f"  device compartilhado : {int((invisiveis & df.device_compartilhado).sum())}")
print(f"  desfechos            : {df.desfecho[invisiveis].value_counts().to_dict()}")''')

md("""`violacao_blindagem` e `device_compartilhado` não iniciam o relógio de
sinal — só entram de carona quando outro sinal aparece. São 32 locações nunca
vistas (todas DEVOLVIDA nesta base). Mas blindagem + telemetria ruim leva o
risco a 91,7%: é o agravante mais forte e a operação só o vê por acaso.

**Recomendação:** fazer `violacao_blindagem` iniciar o relógio sozinha. Custo:
~1 caso a mais por semana.""")

md("""### 7.2 Projeção

Premissa: o gargalo do G1 é o tempo de resposta, não a dificuldade do caso.
Por isso, faixa — não número único.""")

code('''risco_g1 = int(df.RISCO[G1].sum())
perdas_g1 = int(df.APR[G1].sum())
perdas_fora = int(df.APR.sum()) - perdas_g1
sucesso_hoje = int(df.REC[G1].sum()) / risco_g1

cenarios = []
for nome, s in [("hoje", sucesso_hoje), ("conservador", 0.50),
                ("base", 0.65), ("otimista", 0.80)]:
    perdas = risco_g1 * (1 - s) + perdas_fora
    cenarios.append({"cenario": nome, "sucesso no G1": s,
                     "perdas projetadas": perdas,
                     "taxa de apropriacao": perdas / len(df),
                     "motos salvas": int(df.APR.sum()) - perdas})
proj = pd.DataFrame(cenarios)
display(proj.style.format({"sucesso no G1": "{:.1%}", "perdas projetadas": "{:.1f}",
                           "taxa de apropriacao": "{:.2%}", "motos salvas": "{:.1f}"}))

fig, ax = plt.subplots(figsize=(8.4, 3.4))
cores = [CINZA, AMBAR, VERDE, VERDE]
b = ax.bar(proj.cenario, proj["taxa de apropriacao"], color=cores, width=0.55)
b[3].set_alpha(0.55)
ax.axhline(0.031, color=AZUL, ls="--", lw=1.3)
ax.text(3.45, 0.0325, "3,1% — antes da alta", ha="right", fontsize=8.5, color=AZUL)
for barra, v in zip(b, proj["taxa de apropriacao"]):
    ax.text(barra.get_x() + barra.get_width()/2, v + 0.0015, pct(v, 1),
            ha="center", fontweight="bold")
ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax.set_ylim(0, 0.058)
ax.set_title("Taxa de apropriação por cenário de melhora no G1", loc="left")
limpa(ax, x=False)
plt.tight_layout(); plt.show()''')

md("""### 7.3 Cartão de triagem""")

code('''cartao = textwrap.dedent(f"""
+--------------------------------------------------------------------+
|  TRIAGEM RECOPS — cartao de bolso                                   |
+--------------------------------------------------------------------+
|                                                                     |
|  PERGUNTA 1: a moto esta parada ha 48h E sem ping ha 24h?           |
|                                                                     |
|     NAO  ->  nao e caso critico. Regua automatica (G3).             |
|              Nenhuma ligacao. Sobe se aparecer 2o sinal.            |
|                                                                     |
|     SIM  ->  PERGUNTA 2: tem inadimplencia de 15 dias ou mais,      |
|              OU alerta de violacao de blindagem?                    |
|                                                                     |
|              SIM ->  [ G1 CRITICO ]                                 |
|                      Ligar em ate 72h. Preparar busca em            |
|                      paralelo, nao depois.                          |
|                      ~9 em cada 10 viram perda ou busca.            |
|                                                                     |
|              NAO ->  [ G2 ALTO ]                                    |
|                      Mensagem em ate 5 dias.                        |
|                      Ligar so se nao responder.                     |
|                                                                     |
+--------------------------------------------------------------------+
|  NAO acione por: moto parada sozinha ({int((df.parou_48h & ~df.sem_ping_24h).sum()):>3} casos, 0 perdas)      |
|                  atraso de pagamento sozinho ({int((df.inad30 & ~(df.parou_48h|df.sem_ping_24h)).sum()):>3} casos, 0 perdas) |
+--------------------------------------------------------------------+
""")
print(cartao)''')


# ============================================================ 8. LIMITACOES
md("""---
# 8. Limitações

- **24 eventos de perda.** Cortes por filial/regional/perfil chegam a grupos de
  10-15 casos — hipótese, não conclusão (ex.: Nordeste 1 com 10,4% de
  apropriação vs. 1,5% da Sudeste 1).
- **Só locações encerradas.** Contratos de risco ainda em curso não entram; a
  taxa real tende a ser maior.
- **Flags são agregadas do contrato**, não estado do dia. Sem viés de exposição
  nesta base (verificado), mas é artefato do dado sintético.
- **`RECUPERADA` é desfecho tratado** — contrafactual não observável.
- **Dados sintéticos.** Os limiares (48h, 24h, 15 dias) não devem ser
  transplantados sem recalibrar; o método sim — conjunção > sinal isolado,
  medir a janela, cortar onde a curva satura.
- Faltam três números para priorizar por valor esperado em vez de risco: custo
  de um acionamento, custo de uma moto perdida, capacidade real da equipe.""")


# ============================================================ 9. APENDICE
md("""---
# 9. Apêndice""")

code('''print("=" * 64)
print("DISTRIBUICAO DOS DESFECHOS")
print("=" * 64)
d = df.desfecho.value_counts().to_frame("n")
d["%"] = (d.n / len(df) * 100).round(1)
display(d)

print("=" * 64)
print("TODAS AS COMBINACOES DE SINAL COM n >= 10")
print("=" * 64)
import itertools
feats = ["parou_48h", "sem_ping_24h", "violacao_blindagem", "inad15", "inad30"]
linhas = []
for k in (1, 2, 3):
    for combo in itertools.combinations(feats, k):
        m = np.ones(len(df), bool)
        for c in combo:
            m &= df[c].values
        if m.sum() < 10:
            continue
        linhas.append({"combinacao": " + ".join(combo), "n": int(m.sum()),
                       "perdas": int(df.APR[m].sum()),
                       "precisao": df.APR[m].mean(),
                       "recall": df.APR[m].sum()/df.APR.sum(),
                       "risco": df.RISCO[m].mean()})
combos = pd.DataFrame(linhas).sort_values("precisao", ascending=False)
display(combos.style.format({"precisao": "{:.1%}", "recall": "{:.1%}", "risco": "{:.1%}"}))''')

code('''print("=" * 64)
print("POR REGIONAL")
print("=" * 64)
reg = df.groupby("regiao").agg(
    n=("APR", "size"), perdas=("APR", "sum"),
    taxa_apropriacao=("APR", "mean"), taxa_risco=("RISCO", "mean"),
)
reg["com_par_critico"] = df.groupby("regiao").apply(
    lambda g: (g.parou_48h & g.sem_ping_24h).mean(), include_groups=False)
display(reg.style.format({"taxa_apropriacao": "{:.1%}", "taxa_risco": "{:.1%}",
                          "com_par_critico": "{:.1%}"}))

print("=" * 64)
print("VARIAVEIS DE PERFIL — nenhuma prediz")
print("=" * 64)
perfil = []
for col in ["sexo", "faixa_idade", "faixa_caucao", "pacote_tipo", "dist_base_km"]:
    for val in df[col].unique():
        m = df[col] == val
        perfil.append({"variavel": col, "valor": val, "n": int(m.sum()),
                       "taxa": df.APR[m].mean(), "lift": df.APR[m].mean()/TX_APR})
perfil = pd.DataFrame(perfil).sort_values("lift", ascending=False)
display(perfil.style.format({"taxa": "{:.1%}", "lift": "{:.2f}x"}))''')

md("""Sem modelo treinado: com 24 eventos, um classificador seria menos
confiável que a regra e impossível de explicar em campo.""")

code('''import matplotlib, sys
print(f"python     {sys.version.split()[0]}")
print(f"pandas     {pd.__version__}")
print(f"numpy      {np.__version__}")
print(f"matplotlib {matplotlib.__version__}")
print(f"\\nlinhas na base: {len(df)}")
print(f"perdas        : {int(df.APR.sum())}")
print(f"casos de risco: {int(df.RISCO.sum())}")''')


# ============================================================ MONTAGEM
def montar():
    nb = {
        "cells": [],
        "metadata": {
            "colab": {"provenance": [], "toc_visible": True},
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 0,
    }
    for tipo, fonte in cells:
        linhas = fonte.split("\n")
        src = [l + "\n" for l in linhas[:-1]] + [linhas[-1]]
        c = {"cell_type": tipo, "metadata": {}, "source": src}
        if tipo == "code":
            c["execution_count"] = None
            c["outputs"] = []
        nb["cells"].append(c)

    destino = os.path.join("notebook", "mottu_prevencao_perdas.ipynb")
    os.makedirs("notebook", exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)

    n_md = sum(1 for t, _ in cells if t == "markdown")
    n_code = len(cells) - n_md
    print(f"gerado: {destino}")
    print(f"  {len(cells)} celulas ({n_md} markdown, {n_code} codigo)")
    return destino


if __name__ == "__main__":
    montar()
