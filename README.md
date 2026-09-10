# Prevenção de Perdas — Case Mottu

Análise de apropriação indébita em locações de moto: quais sinais predizem a
perda, quanto tempo existe para agir, e como priorizar a fila da equipe de
Recuperação.

**[▶ Abrir o notebook no Google Colab](https://colab.research.google.com/github/Mikaelbr073/mottu-prevencao-perdas/blob/main/notebook/mottu_prevencao_perdas.ipynb)**

---

## A resposta em três linhas

**Nenhum sinal isolado prediz apropriação.** Moto parada por 48h, sozinha, deu
zero perda em 71 casos. O que prediz é a conjunção de moto imobilizada com
rastreador mudo: 43,8% de apropriação contra uma base de 4,8%.

**A janela é de 9 dias (mediana), sempre entre o 5º e o 12º.** Isso impõe um SLA
de 72 horas — o único prazo em que nenhuma perda da base tinha acontecido.

**O grupo crítico é 1,2 caso por semana.** A Mottu não tem problema de
capacidade, tem problema de ordem na fila: a equipe acerta 94% no grupo onde
quase nada se perde e 30% no grupo onde 9 em cada 10 viram perda.

---

## Estrutura

```
├── notebook/
│   └── mottu_prevencao_perdas.ipynb   análise completa, narrativa + apêndice
├── analise/
│   ├── build_notebook.py              gera o notebook
│   ├── explore1.py … qa6.py           exploração passo a passo
│   └── capacidade.py                  vazão da fila e curva de capacidade
├── dados -PrevencaoPerdas_Base.xlsx   base (500 locações encerradas)
├── Problema.txt                       enunciado
└── MEMORY.md                          registro de decisões e achados
```

## Como rodar

**No Colab:** clique no link acima. A base é carregada automaticamente; se não
for encontrada, o notebook abre um seletor de arquivo.

**Local:**

```bash
pip install pandas openpyxl matplotlib
python analise/build_notebook.py     # regenera o notebook
```

O notebook roda de cima para baixo sem estado escondido. Todo número do texto
sai do código da célula acima dele.

## Notas de método

- Não há modelo treinado, e isso é deliberado: com 24 eventos de perda, um
  classificador seria menos confiável que a regra e impossível de explicar para
  quem trabalha em campo.
- `dias_locacao` foi descartada por vazamento — sozinha acerta o desfecho em
  98,6% dos casos, porque só existe depois que ele aconteceu.
- `jornada_impossivel` lidera o ranking de lift com n=2 e foi descartada.
- Nenhuma variável de perfil (sexo, idade, caução, pacote) entra na regra: lift
  próximo de 1, e usar isso para decidir cobrança é problema de justiça.

Os dados são sintéticos, criados para o processo seletivo, e não representam a
operação real.
