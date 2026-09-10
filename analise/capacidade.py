import pandas as pd, numpy as np
pd.set_option('display.width',250)
df = pd.read_excel('dados -PrevencaoPerdas_Base.xlsx', sheet_name='Dados')
b=['parou_48h','sem_ping_24h','violacao_blindagem','device_compartilhado','jornada_impossivel']
for c in b: df[c]=(df[c]=='SIM')
df['APR']=df.desfecho=='APROPRIADA'
df['REC']=df.desfecho=='RECUPERADA_POS_ACIONAMENTO'
df['RISCO']=df.desfecho!='DEVOLVIDA'
df['inad']=df.dias_inadimplencia_max
df['tem_sinal']=df.dia_primeiro_sinal.notna()

SEM = 26.0  # 6 meses ~ 26 semanas

print("### CARTEIRA ATIVA EQUIVALENTE ###")
print(f"locacoes encerradas na janela : {len(df)}")
print(f"duracao media do contrato     : {df.dia_desfecho.mean():.0f} dias")
print(f"carteira ativa simultanea ~   : {len(df)*df.dia_desfecho.mean()/182:.0f} motos")
print()
print("### VAZAO DE SINAIS (fila de entrada) ###")
print(f"locacoes que geraram >=1 sinal: {df.tem_sinal.sum()}  ->  {df.tem_sinal.sum()/SEM:.1f} /semana")
print()

tel2 = df.parou_48h & df.sem_ping_24h
g1 = tel2 & ((df.inad>=15) | df.violacao_blindagem | df.jornada_impossivel)
g2 = (~g1) & ((tel2) | ((df.parou_48h|df.sem_ping_24h)&((df.inad>=15)|df.violacao_blindagem)))
g3 = (~g1)&(~g2)&(df.parou_48h|df.sem_ping_24h|(df.inad>=15))
g0 = (~g1)&(~g2)&(~g3)

print("### VAZAO E CARGA POR GRUPO ###")
print(f"{'grupo':<14}{'n':>5}{'/semana':>9}{'%fila':>8}{'APR':>5}{'REC':>5}{'risco':>7}{'prec_risco':>12}")
for nome,m in [('G1 CRITICO',g1),('G2 ALTO',g2),('G3 VIGIAR',g3),('G0 fora',g0)]:
    n=m.sum()
    print(f"{nome:<14}{n:>5}{n/SEM:>9.1f}{n/df.tem_sinal.sum()*100:>7.0f}%{df.APR[m].sum():>5}{df.REC[m].sum():>5}{df.RISCO[m].sum():>7}{df.RISCO[m].mean()*100:>11.0f}%")
print()
print("### CURVA DE CAPACIDADE: recall de RISCO vs tamanho da fila ###")
score = (df.parou_48h.astype(int)*2 + df.sem_ping_24h.astype(int)*2
         + df.violacao_blindagem.astype(int) + (df.inad>=15).astype(int)
         + (df.inad>=30).astype(int) + df.jornada_impossivel.astype(int)
         + df.device_compartilhado.astype(int))
df['score']=score
ordem = df.sort_values('score',ascending=False)
tot_risco=df.RISCO.sum(); tot_apr=df.APR.sum()
print(f"{'top N':>7}{'%carteira':>11}{'/semana':>9}{'risco capt':>12}{'recall':>9}{'APR capt':>10}{'recall_APR':>12}")
for N in [15,25,30,40,50,65,80,100,130,187,253]:
    sub=ordem.head(N)
    print(f"{N:>7}{N/len(df)*100:>10.1f}%{N/SEM:>9.1f}{sub.RISCO.sum():>12}{sub.RISCO.sum()/tot_risco*100:>8.0f}%{sub.APR.sum():>10}{sub.APR.sum()/tot_apr*100:>11.0f}%")
print()
print("### EFICACIA ATUAL DO ACIONAMENTO (base para a projecao) ###")
for nome,m in [('G1',g1),('G2',g2),('G3',g3),('G0',g0)]:
    r=df.REC[m].sum(); a=df.APR[m].sum()
    tx = r/(r+a)*100 if (r+a)>0 else float('nan')
    print(f"{nome}: REC={r:>2} APR={a:>2}  taxa de sucesso = {tx:5.1f}%")
print()
print(f"GLOBAL: REC={df.REC.sum()} APR={df.APR.sum()} -> sucesso {df.REC.sum()/(df.REC.sum()+df.APR.sum())*100:.1f}%")
