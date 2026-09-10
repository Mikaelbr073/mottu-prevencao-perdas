# Mottu — Case 1: Prevenção de Perdas
## Memória de análise da base

> Documento de trabalho. Registra o que foi verificado na base, com números,
> para não precisar refazer a exploração. Atualizado em 2026-09-10.

---

# ⏸ ESTADO ATUAL — ONDE CONTINUAR

**Última atualização:** 2026-09-10, ~16h30.

### Onde paramos
Notebook **escrito, validado e publicado**. Repositório **público**. Base
carrega sozinha no Colab (sem upload). PDF **ainda não iniciado**.

### Repositório
https://github.com/Mikaelbr073/mottu-prevencao-perdas (público)

Abrir no Colab:
```
https://colab.research.google.com/github/Mikaelbr073/mottu-prevencao-perdas/blob/main/notebook/mottu_prevencao_perdas.ipynb
```

### Feedback do usuário sobre o notebook (aplicado)
O Colab tinha virado ensaio — texto longo, títulos de efeito ("Não é
gradiente, é um salto"), jargão ("duas células de encanamento"). Reescrito:
**Colab = número + gráfico, enxuto. PDF = onde vai o detalhamento.**
Retrabalho feito via `analise/build_notebook.py`; commit
`Enxuga o notebook e carrega a base direto do repositório`.

Regra para daqui em diante: ao escrever qualquer texto do notebook, manter o
padrão enxuto que já está lá — não reintroduzir prosa longa nem título
"cara de IA". O PDF é que recebe o texto corrido.

### Fluxo de iteração (funcionando)
1. Editar `analise/build_notebook.py`
2. `python analise/build_notebook.py` (regenera o `.ipynb`)
3. Validar com o script em `scratchpad/valida.py` (roda todas as células,
   pega erro antes de publicar) — recriar se o scratchpad tiver sido limpo,
   é curto, está registrado no histórico da sessão
4. `git add -A && git commit && git push`
5. Usuário recarrega a aba do Colab

### Próximos passos
1. Construir o **PDF** — estrutura no §7c, mas agora com uma correção: o PDF
   é quem carrega o detalhamento (texto corrido, explicação de método), com
   **prints dos gráficos do Colab** embutidos. O link do Colab vai no fim,
   para quem quiser conferir mais a fundo — não é o inverso.
2. Logo da Mottu para a capa (pendente do usuário)

### Bloqueios / pendências do usuário
- [ ] **Logo da Mottu** para a capa do PDF

### Estado do ambiente (verificado)
| item | status |
|---|---|
| `uv` 0.12.12 | instalado |
| `matplotlib` 3.11.1 / `nbformat` 5.11.1 | instalados |
| `gh` 2.100.0 | autenticado como `Mikaelbr073` |
| git user | Mikael Carvalho / mcb3@discente.ifpe.edu.br |
| Repositório | público, `main`, sincronizado |
| Notebook | 62 células, 25 de código, todas validadas |
| `colab-mcp` | abandonado — ver §7e |
| PDF | não iniciado |

---

## 0. Arquivos

| arquivo | conteúdo |
|---|---|
| `dados -PrevencaoPerdas_Base.xlsx` | aba `Dados` (500×18) + aba `Dicionario` (18×2) |
| `Problema.txt` | enunciado do case (contexto, 3 perguntas, premissas) |
| `MEMORY.md` | este arquivo |

**Alvo do case:** 3 perguntas — (1) quais sinais predizem apropriação, (2) janela
média entre 1º sinal e perda + o que significa para o acionamento, (3) até 3
grupos de acionamento priorizados para o RecOps.

---

## 1. Veredito sobre qualidade da base

**A base NÃO precisa de limpeza.** 500 linhas, 0 duplicatas, 0 `locacao_id`
repetido, 0 nulos — exceto `dia_primeiro_sinal` (247 vazios, intencional =
"nenhum sinal"). Coerência temporal 100%: nenhum sinal posterior ao desfecho,
nenhum `dia_desfecho > dias_locacao`, nenhuma data ≤ 0.

O que precisa de tratamento é o **desenho da análise**, não os dados. São 5
armadilhas:

### 1a. VAZAMENTO em `dias_locacao` — a mais grave

`dias_locacao` = duração **contratada**. `dia_desfecho` = dia em que a locação
de fato terminou. Elas só coincidem quando a moto volta normalmente:

| desfecho | `dias_locacao == dia_desfecho` |
|---|---|
| DEVOLVIDA | 417 / 420 |
| APROPRIADA | 1 / 24 |
| RECUPERADA | 3 / 56 |

`dias_locacao > dia_desfecho` acerta o desfecho em **98,6%** dos casos.

**Regra:** `dias_locacao` NÃO entra como preditor em nada. Serve só para
contexto. A janela usa `dia_desfecho`.

### 1b. Flags são "aconteceu em algum momento", não estado no dia D

`parou_48h`, `sem_ping_24h`, `violacao_blindagem`, `device_compartilhado`,
`jornada_impossivel` são booleanos de contrato inteiro. `dias_inadimplencia_max`
é o **máximo** do contrato. No dia da decisão o RecOps não conhece o máximo.

Testei viés de tempo-imortal (contrato longo acumula mais flag). **Não existe
nesta base** — taxa de flag é plana por quartil de duração, olhando só DEVOLVIDAS:

```
quartil de dia_desfecho   parou_48h  sem_ping_24h  inad_média
 21 - 79 d  (n=105)         18,1%       13,3%         4,5
 80 -134 d  (n=107)         20,6%       12,1%         7,3
135 -184 d  (n=103)         16,5%       11,7%         5,8
185 -239 d  (n=105)         15,2%       14,3%         7,3
```

**Consequência:** pode comparar taxas direto, sem normalizar por exposição.
Isso é artefato do dado sintético — na operação real não valeria. Registrar
como premissa explícita.

### 1c. `dia_primeiro_sinal` não cobre todos os sinais — regra reconstruída

Testada contra as 500 linhas, com **1 única divergência**:

```
dia_primeiro_sinal existe  <=>  parou_48h  OU  sem_ping_24h
                                OU jornada_impossivel
                                OU dias_inadimplencia_max >= 15
```

Limiar de inadimplência confirmado em **15 dias** (casos sem telemetria):
`(9,14] -> 23 sem sinal / 1 com`; `(14,21] -> 0 / 18`; `(21,50] -> 0 / 54`.

**`violacao_blindagem` e `device_compartilhado` NÃO ligam o relógio.**
Existem **32 locações** com uma dessas flags e sem data de sinal — 20 de
blindagem, 12 de device; todas com inadimplência 0; **todas DEVOLVIDA**.

Não muda a conclusão desta base (nenhuma virou perda), mas muda o desenho da
regra operacional a propor: hoje esses dois sinais só entram no radar de carona
com outro sinal.

*Exceção única:* `L-0113` — inadimplência 10 d, nenhuma flag, sinal no dia 12,
desfecho RECUPERADA no dia 22. Um caso em 500; ignorar.

### 1d. Duas variáveis com n pequeno demais para sustentar regra

- **`jornada_impossivel`: n = 2.** Ambas APROPRIADA -> precisão 100%, lift 20,8x.
  É numericamente o "melhor" preditor da base e é **estatisticamente inútil**.
  Colocá-lo no topo do ranking é a armadilha do case.
- **`device_compartilhado`: n = 14**, 2 apropriadas (14,3%). Sugestivo, não
  conclusivo. Sozinho tem lift 0,89 para risco — ou seja, nada.

### 1e. O alvo certo provavelmente não é `APROPRIADA` isolada

`RECUPERADA_POS_ACIONAMENTO` é desfecho **tratado**: sem acionamento teria
virado APROPRIADA.

- Taxa de perda observada: **4,8%** (24/500) — bate com o enunciado
- Taxa de risco materializado: **16,0%** (80/500)

Modelar só APROPRIADA = aprender "perda que o RecOps não conseguiu evitar", que
mistura risco do cliente com falha operacional.

**DECIDIDO:** alvo = `APROPRIADA + RECUPERADA` (16%). Ver §7.

### 1f. Censura amostral

A base só tem locações **encerradas** nos últimos 6 meses. Contratos em curso —
inclusive os de alto risco ainda vivos — não estão. A taxa real tende a ser maior
que a observada. Premissa a declarar.

---

## 2. Distribuições básicas

```
desfecho                       n     %
DEVOLVIDA                    420  84,0
RECUPERADA_POS_ACIONAMENTO    56  11,2
APROPRIADA                    24   4,8      <- bate com "subiu para 4,8%"

pacote:  Semanal 318 / Mensal 182
caução:  R$301-600 205 / R$0-300 197 / R$601+ 98
sexo:    M 409 / F 91
idade:   25-34 187 / 18-24 154 / 35-44 113 / 45+ 46
dist:    3-8km 223 / 0-3km 160 / 8+km 117
filiais: 8 (48 a 71 locações cada)   regionais: 4

flags SIM:  parou_48h 119 | sem_ping_24h 104 | violacao_blindagem 49
            device_compartilhado 14 | jornada_impossivel 2

dias_inadimplencia_max: mediana 0, média 8,1, máx 44
  por desfecho -> DEVOLVIDA méd 6,2 | RECUPERADA 14,7 | APROPRIADA 24,9
```

---

## 3. ACHADO CENTRAL — sinal isolado é ruído, a conjunção é que prediz

Base de comparação: **4,8%** de apropriação.

| condição | n | APROPRIADA | Risco (APR+REC) |
|---|---|---|---|
| `parou_48h` **sozinho** (sem sem_ping) | 71 | **0 — 0,0%** | 22,5% |
| `sem_ping_24h` **sozinho** (sem parou) | 56 | 2 — 3,6% | 37,5% |
| `violacao_blindagem` **sozinha** | 25 | **0 — 0,0%** | 20,0% |
| `inadimplência >=30d` **sozinha** | 24 | **0 — 0,0%** | 0,0% |
| | | | |
| `parou_48h` **+** `sem_ping_24h` | 48 | **21 — 43,8%** | 60,4% |
| + `inadimplência >=15d` | 30 | **19 — 63,3%** | 90,0% |
| + `inadimplência >=30d` | 16 | **13 — 81,2%** | 93,8% |
| `blindagem` **+** telemetria | 24 | 7 — 29,2% | **91,7%** |

Tabela 2×2 que resume o case inteiro:

```
                    sem_ping=NÃO       sem_ping=SIM
parou_48h = NÃO      0,3% (1/325)       3,6% (2/56)
parou_48h = SIM      0,0% (0/71)       43,8% (21/48)   <- 21 das 24 perdas
```

**Leitura de negócio:** moto parada sozinha = moto na garagem (0 em 71).
Inadimplência alta sozinha = aperto financeiro, não apropriação (0 em 24).
O que prediz é **moto imobilizada + rastreador mudo ao mesmo tempo**; a
inadimplência é **amplificador**, não gatilho.

**23 das 24 apropriações têm 2+ sinais.** Só `L-0225` foi perdida sem sinal algum.

### Distribuição por nº de sinais de telemetria

| nº sinais | n | DEVOLVIDA | RECUPERADA | APROPRIADA | % APR |
|---|---|---|---|---|---|
| 0 | 288 | 279 | 8 | 1 | 0,3% |
| 1 | 152 | 122 | 30 | 0 | 0,0% |
| 2 | 44 | 17 | 13 | 14 | 31,8% |
| 3 | 16 | 2 | 5 | 9 | 56,2% |

### Ranking de lift (para APROPRIADA)

```
sinal                   n    precisão   lift   recall
jornada_impossivel      2     100,0%    20,8x    8,3%   <- n=2, DESCARTAR
inadimplência >=30d    40      32,5%     6,8x   54,2%
sem_ping_24h          104      22,1%     4,6x   95,8%   <- melhor recall
parou_48h             119      17,6%     3,7x   87,5%
inadimplência >=15d   120      15,8%     3,3x   79,2%
violacao_blindagem     49      14,3%     3,0x   29,2%
device_compartilhado   14      14,3%     3,0x    8,3%   <- n=14
8+ km                 117       7,7%     1,6x   37,5%
18-24                 154       7,1%     1,5x   45,8%
Semanal               318       5,0%     1,0x   66,7%   <- nulo
caução R$0-300        197       4,6%     1,0x   37,5%   <- nulo
```

---

## 4. JANELA DE AÇÃO

`janela = dia_desfecho − dia_primeiro_sinal`

| desfecho | n | mediana | média | min | máx |
|---|---|---|---|---|---|
| **APROPRIADA** | 23 | **9 d** | 8,7 d | **5** | **12** |
| RECUPERADA | 56 | 11 d | 10,8 d | 3 | 19 |
| DEVOLVIDA | 174 | 51 d | 64,9 d | 1 | 218 |

*(23 e não 24 porque `L-0225` não tem sinal.)*

Valores brutos das 23 apropriações:
`5,5,6,7,7,7,8,8,8,8,8,9,9,9,9,10,10,10,10,11,11,12,12`

### Acumulado de perdas por dia após o 1º sinal — **o número mais acionável**

```
até  3 d:    0,0%  (0/23)   <- agir aqui chega antes de 100% das perdas
até  5 d:    8,7%  (2/23)
até  7 d:   26,1%  (6/23)
até 10 d:   82,6%  (19/23)
até 14 d:  100,0%  (23/23)
```

**Interpretação:** SLA de **72h** de contato chega antes de todas as perdas.
5 dias chega antes de 91%. 7 dias já perde 26% delas. A janela é o orçamento de
tempo do processo inteiro (detecção -> fila -> contato -> decisão de busca).

Cuidado: a janela **sozinha não separa** APROPRIADA de RECUPERADA (9 vs 11 dias
de mediana, faixas sobrepostas) — a janela de RECUPERADA inclui o tempo de ação
do time. O que separa é o **teto de 12 dias** nas perdas.

`dia_primeiro_sinal` (quando o risco aparece no contrato): mediana 50 d para
APROPRIADA, 38 d para RECUPERADA, 60 d para DEVOLVIDA. Sem padrão forte.

---

## 5. Diagnóstico operacional

### 5a. O RecOps está gastando capacidade no caso fácil

| nº sinais | RECUPERADA | APROPRIADA | taxa de sucesso do acionamento |
|---|---|---|---|
| 0 | 8 | 1 | 88,9% |
| 1 | 30 | 0 | **100,0%** |
| 2 | 13 | 14 | **48,1%** |
| 3 | 5 | 9 | **35,7%** |

Acerta 100% nos casos de 1 sinal — que **nunca viram perda** (0 apropriadas em
152). Despenca para 36% onde a perda de fato acontece. **É problema de
ordenação de fila, não de detecção.**

### 5b. Concentração regional — Nordeste 1

| regional | n | % APR | % com parou+sem_ping | APR *dado* parou+sem_ping |
|---|---|---|---|---|
| **Nordeste 1** | 125 | **10,4%** | 12,0% | **66,7%** (n=15) |
| Sul 1 | 109 | 4,6% | 11,0% | 41,7% (n=12) |
| Sudeste 2 | 129 | 3,1% | 8,5% | 36,4% (n=11) |
| Sudeste 1 | 137 | 1,5% | 7,3% | 20,0% (n=10) |

Não é só mix de sinais: **dado o mesmo sinal crítico, converte ~2x mais**.
Aponta para capacidade / tempo de resposta local, não perfil de cliente.
Ressalva: n=15. Tratar como hipótese a investigar, não como conclusão.

Por filial: Santa Efigênia 12,7% (9/71) e Boa Vista 7,4% (4/54) no topo;
Vila Industrial 0% (0/70).

### 5c. O que NÃO prediz — não usar

Sexo, faixa etária, caução e tipo de pacote têm **lift ≈ 1,0** e desaparecem
dentro do grupo crítico (caução R$601+ tem 54,5% de apropriação — *maior* que
a faixa R$0-300, com 50%). `dist_base_km` 0-3 km parece protetor (0 de 6 no
grupo crítico) mas n=6 não sustenta regra.

**Não construir o score sobre perfil demográfico** — além de estatisticamente
fraco, é problema de fairness em decisão de crédito/cobrança.

---

## 6. Grupos propostos (rascunho, já testado contra a base)

| grupo | regra | n | % base | perdas capturadas | precisão APR | precisão risco |
|---|---|---|---|---|---|---|
| **G1 Crítico** | `parou_48h` **e** `sem_ping_24h` **e** (`inad>=15` **ou** `blindagem`) | 30 | 6,0% | **19 / 24** | 63,3% | 90,0% |
| **G2 Alto** | 2 sinais sem o agravante | 35 | 7,0% | +2 | 5,7% | 54,3% |
| **G3 Vigiar** | 1 sinal isolado | 187 | 37,4% | +2 | 1,1% | 17,1% |
| *fora do radar* | — | 248 | 49,6% | 1 | 0,4% | 0,8% |

Cobertura acumulada: **G1 -> 19/24 · G1+G2 -> 21/24 · G1+G2+G3 -> 23/24**

**G1+G2 = 13% da carteira e 21 das 24 perdas.**

G3 é grande demais para acionamento humano (37% da carteira) -> tem que ser
régua automática (SMS/push/app), não ligação. G1 exige contato ativo + preparo
de busca dentro de 72h.

---

## 7. DECISÕES FECHADAS (2026-09-10)

1. **Alvo = `APROPRIADA + RECUPERADA`** (16%, 80 casos). `RECUPERADA` é desfecho
   tratado; modelar só `APROPRIADA` ensina a prever falha do RecOps, não risco
   do cliente. `APROPRIADA` isolada vira **métrica de resultado**, não alvo.

2. **Capacidade — premissa ancorada na vazão**, não em chute de headcount:
   - carteira ativa equivalente: **~333 motos**
   - fila de sinais: **9,7/semana**
   - premissa declarada: 1 squad sustenta **~40 acionamentos ativos/semana**
     por 500 locações encerradas (~8/dia com follow-up)
   - G1+G2 = 2,5/semana = **6% da capacidade**
   - apresentar **curva de sensibilidade**, não número único

3. **Entregáveis: PDF + Google Colab.** O Colab é a prova executável do PDF.

4. **Notebook = narrativo com apêndice técnico** no fim.

5. **Enquadramento (decidido após reler o enunciado):** o case NÃO é problema de
   predição, é de **alocação**. A frase-chave é *"O desafio da operação é decidir
   quem acompanhar e quando agir"*. Não treinar modelo — o case nunca pede, e 24
   eventos não sustentam. Não usar perfil demográfico (lift ~1,0 + fairness).

6. **Rubrica real**, na seção final do enunciado (o cabeçalho `##lança` está
   corrompido, provavelmente "Nuances"): *"Documente as metas e os critérios que
   você desenvolveu. Será avaliada a **coerência** entre suas escolhas e suas
   conclusões."* -> avaliam coerência, não sofisticação.

---

## 7b. VAZÃO DA FILA — o número que vira a narrativa

| grupo | n | **casos/semana** | % da fila | risco real | sucesso do RecOps hoje |
|---|---|---|---|---|---|
| **G1 Crítico** | 30 | **1,2** | 12% | **90%** | **29,6%** |
| G2 Alto | 35 | 1,3 | 14% | 54% | 89,5% |
| G3 Vigiar | 187 | 7,2 | 74% | 17% | 93,8% |
| G0 fora | 248 | — | — | 1% | 50,0% |
| **global** | | 9,7 | | 16% | **70,0%** |

**A Mottu não tem problema de capacidade, tem problema de triagem.** O grupo
crítico é 1,2 caso/semana afogado numa fila de 9,7 atendida por ordem de
chegada. O time acerta 94% onde quase nada se perde e 30% onde 90% vira perda.

Ressalva a manter explícita: `RECUPERADA` só existe porque o time agiu, então o
contrafactual do G3 **não é identificável**. O que é sólido é a assimetria —
19 das 24 perdas estão no G1.

### Curva de capacidade (score = 2×parou + 2×sem_ping + blindagem + inad15 + inad30 + jornada + device)

```
top N   %carteira  /semana   recall risco   recall APR
   30      6,0%      1,2          34%          79%
   40      8,0%      1,5          40%          92%   <- ponto de operação
   65     13,0%      2,5          57%          96%
  130     26,0%      5,0          71%          96%   <- platô: dobrar não captura nada
  253     50,6%      9,7          96%          96%
```

**Platô no top 40**: depois dele o recall de apropriação satura em 96%. Essa é a
justificativa quantitativa do corte.

### Projeção (cenários, não número mágico)

G1 tem 27 casos de risco, 19 viraram perda (sucesso 29,6%). Fora do G1 há 5
perdas. Se o sucesso no G1 subir:

| cenário | sucesso G1 | perdas totais | taxa |
|---|---|---|---|
| hoje | 29,6% | 24 | 4,8% |
| conservador | 50% | ~18,5 | ~3,7% |
| base | 65% | ~14,5 | ~2,9% |
| otimista | 80% | ~10,4 | ~2,1% |

Premissa a dizer em voz alta: assume que o gargalo é o SLA, não a dificuldade
intrínseca do caso.

---

## 7c. ESTRUTURA DO PDF (acordada)

Risco a evitar: o extra enterrar o obrigatório. Banca abre procurando as 3
respostas; se tiver que garimpar, a percepção é "não respondeu".

```
├─ Capa (logo da Mottu — usuário vai passar)
├─ Sumário
├─ p.1  Resposta em uma página    <- as 3 respostas, sem depender de outra página
├─ p.2  Pergunta 1 — sinais
├─ p.3  Pergunta 2 — janela e SLA
├─ p.4  Pergunta 3 — os 3 grupos + esforço
├─ p.5  Metas e critérios          <- a rubrica pede explicitamente
├─ p.6  ALÉM DO PEDIDO             <- extras, rotulados como extra
└─ p.7  Limitações e premissas
```

**Linguagem do PDF: humana.** Sem jargão, sem cara de texto gerado por IA.
Frases curtas, número concreto, primeira pessoa quando couber.

### Os 5 diferenciais acordados
1. Reframe: 1,2 caso/semana — fila invertida, não falta de capacidade
2. Tabela 2×2 (`parou_48h` sozinho = 0/71) — responde a pista dos sinais benignos
3. Armadilhas rejeitadas (`jornada_impossivel` n=2; vazamento de `dias_locacao`)
4. Achado de produto: blindagem e device não ligam o relógio (32 casos invisíveis)
5. Curva de capacidade com o platô + projeção em 3 cenários

---

## 7d. AMBIENTE / FERRAMENTAS

- `matplotlib` 3.11.1 e `nbformat` 5.11.1 **instalados** nesta máquina em
  2026-09-10 (não vinham por padrão). `sklearn` continua ausente — e não é
  necessário, já que não vamos treinar modelo.
- **`colab-mcp` instalado e registrado** (escopo user, em `~/.claude.json`):
  - `uv` 0.12.12 instalado via `pip install uv`
  - binário: `C:/Users/Profi/AppData/Local/Python/pythoncore-3.14-64/Scripts/uvx.exe`
  - args: `git+https://github.com/googlecolab/colab-mcp`
  - status verificado: **Connected**
- **Fluxo do colab-mcp** (lido no código-fonte, não está no README): o servidor
  sobe um websocket local com token secreto e expõe **uma** ferramenta,
  `open_colab_browser_connection`. Chamar ela abre o navegador em
  `colab.research.google.com/notebooks/empty.ipynb#mcpProxyToken=…&mcpProxyPort=…`.
  Quando o front do Colab conecta de volta, as ferramentas de edição de notebook
  aparecem via `notifications/tools/list_changed`.
- ⚠️ Ferramentas MCP só carregam na **inicialização** da sessão. O servidor foi
  registrado no meio da sessão, então exige reinício com `claude --continue`
  (preserva o histórico e recarrega os MCPs).

---

## 7e. COLAB-MCP — abandonado (mas com dois bugs achados e corrigidos)

Tentativa de usar `googlecolab/colab-mcp` para editar o notebook ao vivo.
**Não conectou.** Abandonado em favor do fluxo GitHub + Colab. Registro aqui
para não refazer o diagnóstico do zero.

### Bug 1 — portas IPv4/IPv6 divergentes (real, do projeto)
`websocket_server.py` chama `websockets.serve(host="localhost", port=0)`.
No Windows `localhost` resolve para IPv6 **e** IPv4, e `port=0` sorteia uma
porta **por socket**. O código anuncia só a do primeiro:

```
sockets: [('::1', 64369), ('127.0.0.1', 64370)]
anunciado: 64369        <- só IPv6; IPv4 nessa porta dá timeout
```
Em 4 de 5 execuções anunciou a porta IPv6.

### Bug 2 — meu primeiro patch (registro do erro)
Forcei `host="127.0.0.1"`: consertou IPv4 e **quebrou IPv6**. Trocar um pelo
outro não resolve. **Correção certa:** escolher uma porta livre e amarrar os
dois stacks nela — `host=["127.0.0.1", "::1"], port=<porta escolhida>`.
Resultado verificado:
```
server listening on [::1]:65327
server listening on 127.0.0.1:65327     <- mesma porta, os dois
```

### Armadilha do `uvx`
`uvx --from . colab-mcp` serviu **build em cache** e ignorou os patches,
inclusive com `--reinstall`. Dois "testes corrigidos" rodaram código velho.
Solução: venv dedicado com `pip install <dir>` e apontar o MCP para o `.exe`.
Ficou em `C:/Users/Profi/.local/share/colab-mcp-venv/Scripts/colab-mcp.exe`,
fonte patcheada em `C:/Users/Profi/.local/share/colab-mcp-fix`.

### Patch extra útil
Adicionei log do token/porta (`MCP_PROXY_TOKEN=` / `MCP_PROXY_PORT=`) — o
projeto não loga, e sem isso é impossível parear sem copiar do navegador.

### Por que ainda assim não conectou
Com as portas certas, o log passou a mostrar `connection closed` — o navegador
**chega** ao servidor, mas fecha o TCP antes de mandar a linha de requisição
HTTP. Não é porta nem token. Hipótese não confirmada: Chrome bloqueando
HTTPS (`colab.research.google.com`) -> IP privado (`127.0.0.1`) por
**Private Network Access**, sem preflight que o servidor não responde.

**Teste que falta**, se um dia valer a pena: abrir no **Chrome** (não em outro
navegador — o Colab é testado nele) com
`chrome://flags/#block-insecure-private-network-requests` desabilitado.

### Comportamento operacional que custou caro
**Recusar/cancelar a chamada da ferramenta mata o processo do servidor** e
invalida o token. Aconteceu 4+ vezes e mascarou os bugs reais. Se retomar:
deixar a chamada rodar (a primeira retorna `false` de propósito).

### Não instalar
`@google/colab-mcp` **não existe** no npm (404). O único `colab-mcp` no npm é
de um usuário aleatório (`pachuli_x2`), não do Google. A doc oficial
([Google Developers Blog](https://developers.googleblog.com/announcing-the-colab-mcp-server-connect-any-ai-agent-to-google-colab/))
não cobre pareamento no navegador nem troubleshooting.

---

## 8. Premissas a declarar no entregável

- Dados sintéticos, 500 locações **encerradas** em 6 meses; contratos em curso
  ausentes (censura à direita).
- `dias_locacao` descartada por vazamento.
- Flags são agregados de contrato, não estado point-in-time; sem viés de
  exposição **nesta base** (verificado), o que não se sustentaria em produção.
- `RECUPERADA` é desfecho tratado — contrafactual do risco não observado.
- `jornada_impossivel` (n=2) e `device_compartilhado` (n=14) excluídos de
  qualquer regra por tamanho de amostra.
- Números por filial/regional têm n baixo (10-15 no corte crítico); usar como
  hipótese, não conclusão.

---

## 9. ROTEIRO DO NOTEBOOK (a construir)

Formato acordado: **narrativo com apêndice técnico**. A banca lê como artigo;
quem quiser auditar desce até o fim. Mesma ordem do PDF.

Arquivo alvo: `notebook/mottu_prevencao_perdas.ipynb`
Gerar via script `analise/build_notebook.py` (monta o JSON com `nbformat`) —
assim dá para regenerar sem editar JSON na mão.

| # | tipo | conteúdo |
|---|---|---|
| 1 | md | Capa |
| 2 | md | Sumário |
| 3 | md | Como ler este notebook |
| 4 | code | Setup: imports, paleta, helper de gráfico |
| 5 | code | Carregar dados — tenta caminho local, cai para `files.upload()` no Colab |
| 6 | code | Colunas derivadas (flags booleanas, `APR`, `REC`, `RISCO`, `janela`, `score`) |
| | | **§1 A resposta em uma página** |
| 7 | md | As 3 respostas, número grande, sem depender de outra seção |
| 8 | code | Painel-resumo (3 cartões / gráfico) |
| | | **§2 O que dá e o que não dá para usar** |
| 9 | md | Abertura |
| 10 | code | Checagem de integridade (duplicatas, nulos, coerência temporal) |
| 11 | md | As armadilhas |
| 12 | code | Vazamento de `dias_locacao` (98,6%) |
| 13 | code | `jornada_impossivel` n=2 |
| 14 | md | Escolha do alvo |
| 15 | code | 4,8% vs 16% |
| | | **§3 Pergunta 1 — sinais** |
| 16 | md | Abertura |
| 17 | code | Tabela sinal isolado vs combinado |
| 18 | code | **Heatmap 2×2** `parou_48h` × `sem_ping_24h` |
| 19 | code | Ranking de lift **com o n à vista** (marcando o n=2) |
| 20 | md | Resposta |
| | | **§4 Pergunta 2 — janela** |
| 21 | md | Abertura |
| 22 | code | Distribuição da janela por desfecho |
| 23 | code | **Curva acumulada de perdas por dia** |
| 24 | md | Resposta / SLA de 72h |
| | | **§5 Pergunta 3 — grupos** |
| 25 | md | Critérios de montagem |
| 26 | code | Monta G1/G2/G3 + tabela |
| 27 | code | Vazão semanal por grupo |
| 28 | code | **Gráfico da inversão** (esforço vs onde a perda está) |
| 29 | code | **Curva de capacidade** com o platô marcado |
| 30 | md | Resposta / esforço por grupo |
| | | **§6 Metas e critérios** |
| 31 | md | SLA, metas, gatilhos de revisão |
| 32 | code | Tabela de metas |
| | | **§7 Além do que foi pedido** |
| 33 | md | Os 32 casos invisíveis |
| 34 | code | Evidência |
| 35 | md | Projeção |
| 36 | code | Cenários conservador / base / otimista |
| 37 | md | Cartão de triagem (uma página para o analista) |
| | | **§8 Limitações** |
| 38 | md | n=500, 24 eventos, sintético, censura |
| | | **§9 Apêndice técnico** |
| 39 | md | Abertura |
| 40 | code | Tabelas completas / reprodutibilidade |

### Gráficos a produzir (7)
1. Painel-resumo das 3 respostas
2. Heatmap 2×2 `parou_48h` × `sem_ping_24h`
3. Lift por sinal com n anotado (n=2 destacado como descartado)
4. Janela por desfecho (distribuição)
5. Curva acumulada de perdas após o 1º sinal (com a linha de 72h)
6. Inversão da fila: % do esforço vs % das perdas por grupo
7. Curva de capacidade com o platô no top 40
8. Projeção em 3 cenários

### Notas técnicas
- Usar **matplotlib puro** (sem seaborn) para portabilidade no Colab
- Paleta: verde Mottu `#0FBF61`, escuro `#101820`, cinza `#B8BFC7`,
  vermelho `#E0443E`, âmbar `#F5A623`
- Todo número mostrado tem que sair do código da célula, não hardcoded
- Notebook precisa rodar **de cima para baixo sem erro** — validar local antes
  de subir

---

## 10. ESTILO DE ESCRITA (PDF e notebook)

O usuário foi explícito: **linguagem humana, sem cara de texto de IA.**

**Fazer:**
- Frases curtas. Número concreto no lugar de adjetivo.
- Primeira pessoa quando couber ("olhei", "testei", "descartei")
- Dizer o que foi rejeitado e por quê
- Afirmar o que é sólido, marcar o que é hipótese

**Não fazer** — palavras e vícios a evitar:
robusto, crucial, fundamental, aprofundar, mergulhar, vale destacar,
é importante notar, em suma, holístico, sinergia, jornada, desbloquear,
poderoso, elevar, alavancar, transformador, no cenário atual,
"não se trata apenas de X, mas de Y", listas de três adjetivos,
abrir parágrafo com "Além disso" / "Ademais".

Regra prática: se a frase continuar verdadeira depois de tirar o adjetivo,
tira o adjetivo.

---

## 11. Reprodutibilidade

Scripts de exploração salvos em `analise/` (rodar a partir da raiz do projeto,
onde está o `.xlsx`):

| script | o que produz |
|---|---|
| `explore1.py` | shape, nulos, dtypes, distribuição de todas as colunas |
| `e2.py` | `dias_locacao` vs `dia_desfecho`, estrutura de sinais, nº de sinais |
| `qa.py` | auditoria de qualidade: duplicatas, coerência temporal, inconsistências |
| `qa2.py` | reconstrução da regra do `dia_primeiro_sinal`, vazamento, lift por sinal |
| `qa3.py` | janela de ação, cortes por regional/filial, eficácia do acionamento |
| `qa4.py` | combinações de sinais, co-ocorrência, os 32 "invisíveis" |
| `qa5.py` | sinal isolado vs combinado, grupos G1/G2/G3, janela por grupo |
| `qa6.py` | viés de tempo-imortal, mix regional, perfil dentro do grupo crítico |

`python analise/qa5.py` reproduz a tabela do §3 e os grupos do §6.
*(Obs.: `qa4.py` termina com erro na última seção — tentativa de regressão
logística com `sklearn`, que não está instalado. As tabelas anteriores rodam
normalmente.)*

Ambiente: Python 3, pandas 3.0.5, openpyxl. **`sklearn` NÃO está instalado** —
a análise é toda tabular (crosstabs, lift, precisão/recall), sem modelo
treinado. Para o case isso é adequado e até preferível: regra explicável >
modelo caixa-preta para uma equipe de campo.
