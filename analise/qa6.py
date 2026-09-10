import pandas as pd, numpy as np
pd.set_option('display.width',250)
df = pd.read_excel('dados -PrevencaoPerdas_Base.xlsx', sheet_name='Dados')
b=['parou_48h','sem_ping_24h','violacao_blindagem','device_compartilhado','jornada_impossivel']
for c in b: df[c]=(df[c]=='SIM')
df['APR']=df.desfecho=='APROPRIADA'
print("### Vies de tempo-imortal: flag depende da duracao da exposicao? ###")
dv=df[df.desfecho=='DEVOLVIDA'].copy()
dv['fx']=pd.qcut(dv.dia_desfecho,4)
print("Somente DEVOLVIDAS (exposicao = dia_desfecho):")
print(dv.groupby('fx',observed=True)[b+['dias_inadimplencia_max']].mean().round(3).to_string())
print("\nn por faixa:", dv.groupby('fx',observed=True).size().to_dict())
print()
print("### Nordeste 1: mix de sinais explica a taxa? ###")
g=df.groupby('regiao').agg(n=('APR','size'), taxa_APR=('APR','mean'),
    parou=('parou_48h','mean'), semping=('sem_ping_24h','mean'),
    blind=('violacao_blindagem','mean'), inad15=('dias_inadimplencia_max',lambda s:(s>=15).mean()),
    dois=('parou_48h','size'))
df['tel2']=df.parou_48h&df.sem_ping_24h
g['pct_tel2']=df.groupby('regiao').tel2.mean()
g['APR_dado_tel2']=df[df.tel2].groupby('regiao').APR.mean()
g['n_tel2']=df[df.tel2].groupby('regiao').size()
print(g.drop(columns=['dois']).round(3).to_string())
print()
print("### Caucao / pacote dentro do grupo critico ###")
crit=df.tel2
print(pd.crosstab(df.faixa_caucao[crit], df.APR[crit], normalize='index').round(3).to_string())
print(pd.crosstab(df.pacote_tipo[crit], df.APR[crit], normalize='index').round(3).to_string())
print(pd.crosstab(df.dist_base_km[crit], df.APR[crit], normalize='index').round(3).to_string())
print(pd.crosstab(df.faixa_idade[crit], df.APR[crit], normalize='index').round(3).to_string())
