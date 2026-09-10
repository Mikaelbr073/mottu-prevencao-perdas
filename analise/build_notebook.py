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

### Case 1 · Análise de apropriação indébita em locações

---

**A pergunta que este notebook responde:** a equipe de RecOps não consegue
acompanhar todas as locações que dão sinal. Quem ela deve acompanhar, e quando
deve agir?

**Resposta curta:** o grupo que concentra as perdas tem **1,2 caso por semana**.
A Mottu não tem problema de capacidade. Tem problema de ordem na fila.

---

*Base: 500 locações encerradas em 6 meses. Dados sintéticos, criados para este
processo seletivo.*""")


# ============================================================ SUMARIO
md("""## Sumário

| Seção | O que tem |
|---|---|
| **1. A resposta em uma página** | As três perguntas do case, respondidas com número |
| **2. O que dá e o que não dá para usar** | Integridade da base e as armadilhas que rejeitei |
| **3. Pergunta 1 — Quais sinais predizem** | Sinal isolado é ruído; a conjunção é que prediz |
| **4. Pergunta 2 — A janela** | 9 dias de mediana, e o SLA que isso impõe |
| **5. Pergunta 3 — Os grupos** | G1/G2/G3, o esforço de cada um e a curva de capacidade |
| **6. Metas e critérios** | O que eu me comprometo a atingir e como se mede |
| **7. Além do que foi pedido** | Um bug de detecção, a projeção e o cartão de triagem |
| **8. Limitações** | Onde esta análise não alcança |
| **9. Apêndice técnico** | Tabelas completas e reprodutibilidade |

---

**Como ler:** o texto conta a história e os números aparecem prontos. Todo
número sai do código da célula acima dele — nada foi digitado à mão. Quem
quiser auditar, o apêndice tem as tabelas completas.""")


# ============================================================ SETUP
md("""---
## Preparação

Duas células de encanamento. Se estiver no Colab e a base não for encontrada,
a segunda abre o seletor de arquivos.""")

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

code('''# Onde a base pode estar, em ordem de tentativa.
ARQUIVO = "dados -PrevencaoPerdas_Base.xlsx"
RAW_URL = ""   # preencher com a URL raw do GitHub quando o repo existir

def carrega_base():
    candidatos = [
        ARQUIVO,
        os.path.join("..", ARQUIVO),
        os.path.join("/content", ARQUIVO),
        os.path.join("/content/drive/MyDrive", ARQUIVO),
    ]
    for c in candidatos:
        if os.path.exists(c):
            print(f"base encontrada em: {c}")
            return pd.read_excel(c, sheet_name="Dados")

    if RAW_URL:
        try:
            print("baixando a base...")
            return pd.read_excel(RAW_URL, sheet_name="Dados")
        except Exception as e:
            print(f"download falhou ({e}); tentando upload manual")

    try:
        from google.colab import files
        print("Selecione o arquivo .xlsx da base:")
        subiu = files.upload()
        nome = list(subiu.keys())[0]
        return pd.read_excel(io.BytesIO(subiu[nome]), sheet_name="Dados")
    except ImportError:
        raise FileNotFoundError(
            "Base nao encontrada. Coloque o .xlsx ao lado do notebook "
            "ou preencha RAW_URL."
        )

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
# 1. A resposta em uma página

Se você só ler esta seção, tem as três respostas.

### Pergunta 1 — Quais sinais melhor predizem a apropriação?

**Nenhum sinal isolado prediz.** Moto parada por 48h, sozinha, deu **zero
apropriação em 71 casos**. Inadimplência acima de 30 dias, sozinha, também deu
zero em 24 casos.

O que prediz é a **conjunção de moto imobilizada com rastreador mudo**:
`parou_48h` + `sem_ping_24h` juntos levam a apropriação em **43,8%** dos casos,
contra uma base de 4,8%. Com inadimplência de 30 dias ou mais em cima, vai a
**81,2%**.

A inadimplência é amplificador, não gatilho.

### Pergunta 2 — Qual é a janela entre o primeiro sinal e a perda?

**Mediana de 9 dias.** Todas as 23 perdas com sinal aconteceram entre o quinto
e o décimo segundo dia — nenhuma antes, nenhuma depois.

Para o acionamento isso significa um **SLA de 72 horas**. Nenhuma perda ocorreu
até o terceiro dia, então agir dentro desse prazo chega antes de todas elas.
Com 7 dias, 26% já foram perdidas.

### Pergunta 3 — Quais grupos de acionamento?

| grupo | regra | casos/semana | risco | o que fazer |
|---|---|---|---|---|
| **G1 Crítico** | parada + sem ping + (inadimplência ≥15d ou blindagem) | **1,2** | 90% | contato ativo em 72h, busca preparada |
| **G2 Alto** | dois sinais, sem agravante | 1,3 | 54% | contato em 5 dias |
| **G3 Vigiar** | um sinal isolado | 7,2 | 17% | régua automática, sem gente |

**O G1 é 1,2 caso por semana.** Isso é o ponto central deste trabalho: o grupo
onde estão 19 das 24 perdas cabe em qualquer capacidade. Ele não é atendido hoje
porque está afogado numa fila de 9,7 casos semanais atendida por ordem de
chegada.""")

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
# 2. O que dá e o que não dá para usar

Antes de responder qualquer coisa, olhei a base procurando motivo para não
confiar nela. Achei pouco — e achei três armadilhas.""")

md("""### 2.1 A base está limpa

Nenhuma linha precisa de tratamento.""")

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

md("""### 2.2 Três coisas que parecem sinal e não são

**Armadilha 1 — `dias_locacao` entrega a resposta.**

`dias_locacao` é a duração *contratada*. `dia_desfecho` é o dia em que a locação
de fato acabou. As duas só batem quando a moto volta normalmente. Quem usar essa
coluna como preditor vai ter um modelo quase perfeito e completamente inútil:
ela só existe depois que o desfecho aconteceu.""")

code('''vaza = (df.dias_locacao - df.dia_desfecho) > 0
tab = pd.crosstab(vaza, df.desfecho)
tab.index = ["contrato terminou no prazo", "terminou antes do prazo"]
display(tab)

acerto = (vaza == df.RISCO).mean()
print(f"\\nUsar so 'terminou antes do prazo' acerta o desfecho em {pct(acerto)} dos casos.")
print("Por isso dias_locacao esta fora da analise. Nao entra em regra nenhuma.")''')

md("""**Armadilha 2 — o preditor perfeito com n = 2.**

`jornada_impossivel` tem 100% de precisão e o maior lift da base inteira. E tem
duas ocorrências. Duas. Colocar isso no topo de um ranking é o erro que a base
parece ter sido montada para provocar.""")

code('''linhas = []
for c in FLAGS + ["inad15", "inad30"]:
    m = df[c]
    n = int(m.sum())
    if n == 0:
        continue
    linhas.append({
        "sinal": c,
        "n": n,
        "precisao": df.APR[m].mean(),
        "lift": df.APR[m].mean() / TX_APR,
        "recall": df.APR[m].sum() / df.APR.sum(),
    })
rank = pd.DataFrame(linhas).sort_values("lift", ascending=False).reset_index(drop=True)
rank["veredito"] = np.where(rank.n < 20, "amostra pequena demais", "usavel")
display(rank.style.format({"precisao": "{:.1%}", "lift": "{:.1f}x", "recall": "{:.1%}"}))

print("jornada_impossivel: lidera o ranking com n=2. Descartado.")
print("device_compartilhado: n=14. Sugestivo, nao conclusivo. Fora de regra.")''')

md("""**Armadilha 3 — as flags são do contrato inteiro, não do dia.**

`parou_48h` quer dizer "aconteceu em algum momento", e `dias_inadimplencia_max`
é o máximo do contrato. No dia da decisão o RecOps não conhece o máximo. Isso
normalmente criaria viés: contrato de 239 dias acumula mais flag que um de 21.

Testei. Não acontece nesta base — as taxas são planas ao longo da duração. Dá
para comparar direto, sem normalizar por exposição. É artefato do dado
sintético, e na operação real não valeria; fica registrado como premissa.""")

code('''dev = df[df.desfecho == "DEVOLVIDA"].copy()
dev["faixa"] = pd.qcut(dev.dia_desfecho, 4)
expo = dev.groupby("faixa", observed=True).agg(
    n=("APR", "size"),
    parou_48h=("parou_48h", "mean"),
    sem_ping_24h=("sem_ping_24h", "mean"),
    inad_media=("inad", "mean"),
)
display(expo.style.format({"parou_48h": "{:.1%}", "sem_ping_24h": "{:.1%}",
                           "inad_media": "{:.1f}"}))
print("Taxas planas entre o contrato mais curto e o mais longo: sem vies de exposicao.")''')

md("""### 2.3 O alvo que faz sentido

O case pergunta o que prediz **apropriação**. Mas `RECUPERADA_POS_ACIONAMENTO`
é um desfecho *tratado*: aquelas motos só voltaram porque alguém agiu. Sem
acionamento, teriam virado apropriação.

Modelar só `APROPRIADA` ensina a prever "perda que o RecOps não conseguiu
evitar" — uma mistura de risco do cliente com falha operacional.

**Decisão: o alvo é `APROPRIADA + RECUPERADA` (risco de perda, 16%).**
`APROPRIADA` isolada (4,8%) vira a métrica de resultado, não o alvo.""")

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
# 3. Pergunta 1 — Quais sinais melhor predizem a apropriação?

O enunciado avisa que sinal de telemetria pode ter causa inocente: moto na
garagem fica horas sem mandar ping. O aviso está certo, e os números mostram
que ele é ainda mais forte do que parece.""")

md("""### 3.1 Sozinho, quase nenhum sinal significa alguma coisa""")

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

md("""Os três zeros dizem tudo:

- **Moto parada sem estar muda: 0 perdas em 71 casos.** É a moto na garagem que
  o enunciado descreve.
- **Blindagem violada sem telemetria ruim: 0 em 25.**
- **Inadimplência acima de 30 dias, sozinha: 0 em 24.** Isso é aperto
  financeiro, não intenção de ficar com a moto.

Cliente que atrasa pagamento e continua rodando está trabalhando para pagar.
Quem some com a moto para de rodar e some do rastreador ao mesmo tempo.""")

md("""### 3.2 A tabela que resume o case""")

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

md("""Não é gradiente. É um salto.

Três das quatro células ficam em torno de zero. A quarta — moto parada **e**
rastreador mudo — vai para 43,8%. Nenhum dos dois sinais isolados chega perto
disso.

A leitura operacional: **o par é o sinal.** Alarme em cima de `parou_48h`
sozinho gera 71 acionamentos que não viram perda nenhuma. É exatamente o que
consome a equipe hoje.""")

md("""### 3.3 O ranking, com o tamanho da amostra à vista

Ranking de lift sem mostrar o `n` engana. Este mostra.""")

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

md("""### Resposta à pergunta 1

**Não existe um sinal que prediga apropriação.** Existe uma combinação.

O par `parou_48h` + `sem_ping_24h` é o preditor real: leva a apropriação em
**43,8%** dos casos contra 4,8% da base, e captura **21 das 24 perdas**. A
inadimplência funciona como amplificador — sobe para 63,3% com 15 dias ou mais,
e 81,2% com 30 ou mais — mas sozinha não prediz nada.

`violacao_blindagem` merece nota separada. Sozinha não vale (0 em 25), mas
somada à telemetria ruim leva o risco de perda a **91,7%**. É agravante, não
gatilho.

Fora da regra: `jornada_impossivel` (n=2) e `device_compartilhado` (n=14), por
tamanho de amostra. E nada de perfil — sexo, idade, caução e tipo de pacote têm
lift próximo de 1 e desaparecem dentro do grupo crítico.""")


# ============================================================ 4. PERGUNTA 2
md("""---
# 4. Pergunta 2 — A janela entre o primeiro sinal e a perda

A janela é `dia_desfecho - dia_primeiro_sinal`. Vale lembrar o que o
`dia_primeiro_sinal` cobre de fato: eu reconstruí a regra que liga esse relógio
e ela aparece na seção 7 — nem todo sinal o dispara.""")

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

md("""### Resposta à pergunta 2

**A janela média é de 8,7 dias; a mediana, 9.** Mas a média não é o número
interessante — a dispersão é.

As 23 perdas com sinal caem todas entre o **dia 5 e o dia 12**. Nenhuma antes,
nenhuma depois. É uma faixa estreita, e ela define o orçamento de tempo do
processo inteiro: detecção, entrada na fila, contato, decisão de busca.

**O que isso significa para o desenho do acionamento:**

| prazo de contato | perdas que já aconteceram | leitura |
|---|---|---|
| **72 horas** | **0%** | chega antes de todas |
| 5 dias | 8,7% | ainda salva 91% |
| 7 dias | 26,1% | um quarto já foi |
| 10 dias | 82,6% | tarde demais |

**O SLA do grupo crítico é 72 horas.** Não por conservadorismo: é o único prazo
em que nenhuma perda da base tinha acontecido ainda.

Um cuidado ao ler isso. A janela sozinha **não separa** perda de recuperação —
recuperadas têm mediana de 11 dias, faixa sobreposta. Isso acontece porque a
janela da recuperada inclui o tempo que a equipe levou para agir. O que separa
não é a duração, é o teto: **nenhuma perda passou do dia 12**.

E a comparação com devolução normal mostra por que dá para triar. Locação que
termina bem tem mediana de 51 dias entre sinal e fim, com cauda até 218. Sinal
que já está velho há semanas quase nunca é perda.""")


# ============================================================ 5. PERGUNTA 3
md("""---
# 5. Pergunta 3 — Os grupos de acionamento

### 5.1 Os critérios que usei

Montei os grupos com três regras, nesta ordem:

1. **Só entra sinal com amostra que sustente.** Fora `jornada_impossivel` (n=2)
   e `device_compartilhado` (n=14).
2. **Nada de perfil demográfico.** Lift próximo de 1, e usar idade ou sexo para
   decidir cobrança é problema de justiça, não só de estatística.
3. **A regra tem que caber num cartão.** Quem usa isso é analista em turno, não
   cientista de dados. Nada de score contínuo com dez variáveis.

O corte de inadimplência em 15 dias não foi escolhido por mim: é o limiar que a
própria operação já usa para ligar o relógio de sinal (mostro isso na seção 7).""")

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

md("""### 5.2 O esforço que cada grupo exige

Converter volume em vazão semanal muda o que a conversa parece ser.""")

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

md("""### 5.3 A fila está ordenada ao contrário

Este é o achado que muda o diagnóstico. Olhando a taxa de sucesso do
acionamento por grupo:""")

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

md("""O time recupera quase tudo no G3 — onde a perda realizada é de 1% e o
volume é de 7,2 casos por semana. E falha na maioria do G1, onde 9 em cada 10
casos viram perda ou exigem busca.

**Não é falta de competência nem de gente. É ordem de fila.** Com 9,7 sinais por
semana chegando e atendimento por ordem de chegada, o caso crítico entra atrás
de seis casos inofensivos. Quando alguém liga, já passou do dia 12.

Uma ressalva honesta: `RECUPERADA` só existe porque a equipe agiu, então não dá
para afirmar quantas das 30 recuperações do G3 teriam virado perda sozinhas — o
contrafactual não é observável nesta base. O que é sólido é a assimetria: **19
das 24 perdas estão no G1**, e é lá que o sucesso desaba.""")

md("""### 5.4 Onde cortar a fila

Ordenei todas as locações por um score simples e olhei quanto de risco cada
tamanho de fila captura. A pergunta é onde parar.""")

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

md("""A curva vermelha satura no **top 40**: dali em diante, dobrar ou triplicar
a fila não captura **nenhuma perda a mais**. Passar de 40 para 130 acionamentos
semanais adiciona 90 contatos e zero motos salvas.

Esse platô é a justificativa numérica do corte. Não escolhi o tamanho do grupo
por sensação de capacidade — escolhi onde o retorno acaba.""")

md("""### Resposta à pergunta 3

Três grupos, nesta ordem:

---

**G1 — Crítico · 1,2 caso/semana · 90% de risco**
`parou_48h` **e** `sem_ping_24h` **e** (`inadimplência ≥ 15d` **ou** `blindagem
violada`)

Contém 19 das 24 perdas. **SLA de 72 horas**, contato ativo por telefone, e
autorização de busca já preparada em paralelo — não depois do contato falhar.
Esforço: quase nada em volume, muito em prioridade. É 1,2 caso por semana; cabe
em qualquer equipe.

**Por que é o primeiro:** maior concentração de perda, e a janela mais apertada.

---

**G2 — Alto · 1,3 caso/semana · 54% de risco**
Dois sinais de telemetria, sem o agravante do G1.

Contato em até 5 dias, pode ser por canal mais barato — mensagem com
confirmação de leitura, e ligação só se não responder. Metade vira risco real,
metade se resolve sozinha.

**Por que é o segundo:** risco relevante, mas metade dos contatos seria
desperdício se tratado com o esforço do G1.

---

**G3 — Vigiar · 7,2 casos/semana · 17% de risco**
Um sinal isolado.

**Sem gente.** Régua automática: push no app, SMS, e só sobe para humano se um
segundo sinal aparecer. É 74% da fila e concentra 2 perdas em 187 casos — tratar
isso com ligação é queimar a capacidade que o G1 precisa.

**Por que é o terceiro:** volume alto, risco baixo. É exatamente o que consome a
equipe hoje.

---

**G1 + G2 = 13% da carteira e 21 das 24 perdas**, a 2,5 acionamentos por semana.""")


# ============================================================ 6. METAS
md("""---
# 6. Metas e critérios

O enunciado pede que as metas e os critérios fiquem documentados. Estes são os
meus, com o número que cada um persegue e como se verifica.""")

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

md("""**Critério de parada da fila:** acionar até o ponto em que o próximo
contato ainda captura perda. Nesta base isso é o top 40 semanal. Se a operação
tiver mais capacidade, ela **não** deve ser gasta alargando a fila — deve ir
para reduzir o tempo de resposta do G1.

**Critério de promoção entre grupos:** um caso do G3 sobe para G2 assim que um
segundo sinal aparece. Um caso do G2 sobe para G1 quando ganha inadimplência de
15 dias ou violação de blindagem. A régua é sempre o par de sinais, nunca o
tempo parado sozinho.

**Critério de revisão:** se a precisão do G1 cair abaixo de 50% por dois meses
seguidos, os limiares foram contaminados e precisam ser recalculados. Regra boa
hoje não é regra boa para sempre — principalmente quando ela muda o
comportamento que estava medindo.""")


# ============================================================ 7. EXTRAS
md("""---
# 7. Além do que foi pedido

Três coisas que apareceram no caminho e que valem mais que a resposta formal.""")

md("""### 7.1 Dois sinais não ligam o relógio — e isso é um bug de detecção

Testei qual regra preenche o campo `dia_primeiro_sinal` e reconstruí ela com uma
única divergência em 500 linhas.""")

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

md("""**`violacao_blindagem` e `device_compartilhado` não iniciam o relógio de
sinal.** Só entram no radar de carona, quando outro sinal aparece.

São 32 locações que nunca foram vistas. Nesta base todas terminaram em
devolução, então não custou nada — e é por isso que o problema está invisível.
Mas a blindagem violada, quando combinada com telemetria ruim, leva o risco de
perda a 91,7%. É o agravante mais forte da base, e a operação só o enxerga
quando já está acompanhando o caso por outro motivo.

**Recomendação:** fazer `violacao_blindagem` iniciar o relógio por conta
própria. Custo: 25 casos a mais em 6 meses, cerca de **1 por semana**.""")

md("""### 7.2 O que acontece se isso for aplicado

A projeção tem uma premissa que eu prefiro dizer alto: ela assume que o gargalo
do G1 é o **tempo de resposta**, não a dificuldade intrínseca do caso. Se parte
dessas perdas for irrecuperável por natureza — cliente que planejou sumir desde
o primeiro dia — o ganho real fica abaixo do cenário base.

Por isso apresento faixa, não número único.""")

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

md("""No cenário base a taxa volta para perto de onde estava antes da alta que
motivou o case — e o esforço para chegar lá é de 2,5 acionamentos por semana,
com prioridade certa.""")

md("""### 7.3 Cartão de triagem

O que o analista precisa ter na tela. Cabe em meia página e não menciona
estatística.""")

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

O que esta análise **não** sustenta:

**São 24 eventos de perda.** Todo corte por filial, regional ou perfil chega em
grupos de 10 a 15 casos. A regional Nordeste 1 aparece com 10,4% de apropriação
contra 1,5% da Sudeste 1, e converte o dobro dado o mesmo sinal — mas são 15
casos. Trato como hipótese a investigar, não como conclusão.

**A base só tem locações encerradas.** Contratos em curso, inclusive os de alto
risco ainda vivos, não estão aqui. A taxa real tende a ser maior que a
observada.

**As flags são agregados de contrato, não estado do dia.** Verifiquei que não há
viés de exposição nesta base, mas isso é artefato do dado sintético. Numa base
real seria preciso reconstruir cada sinal no tempo antes de aplicar a regra.

**`RECUPERADA` é desfecho tratado.** O contrafactual não é observável: não dá
para saber quantas recuperações teriam virado perda sem acionamento. Por isso
uso a assimetria entre grupos, não o número absoluto de recuperações, como
evidência.

**Os dados são sintéticos.** Os limiares — 48h, 24h, 15 dias — não devem ser
transplantados para produção sem recalibrar. O que vale transplantar é o
método: procurar a conjunção, não o sinal isolado; medir a janela; e cortar a
fila onde a curva satura.

**O que eu pediria antes de rodar isso de verdade:** custo de um acionamento,
custo de uma moto perdida e capacidade real da equipe. Com esses três números a
priorização deixa de ser por risco e passa a ser por valor esperado, que é a
forma certa de fazer.""")


# ============================================================ 9. APENDICE
md("""---
# 9. Apêndice técnico

Tabelas completas para quem quiser conferir os números do texto.""")

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

md("""### Reprodutibilidade

Este notebook roda de cima para baixo sem estado escondido. Todo número do texto
sai das células acima — nenhum foi digitado à mão.

**Não há modelo treinado, e isso é deliberado.** Com 24 eventos, um classificador
seria menos confiável que a regra e impossível de explicar para quem trabalha em
campo. Regra explicável vence caixa-preta quando quem decide é um analista em
turno com o cliente na linha.

**Bibliotecas:** `pandas`, `numpy`, `matplotlib`. Nada além do que já vem no
Colab.""")

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
