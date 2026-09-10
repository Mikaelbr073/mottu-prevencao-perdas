import pandas as pd, numpy as np
pd.set_option('display.width',250)
df = pd.read_excel('dados -PrevencaoPerdas_Base.xlsx', sheet_name='Dados')
b=['parou_48h','sem_ping_24h','violacao_blindagem','device_compartilhado','jornada_impossivel']
for c in b: df[c]= (df[c]=='SIM')
df['tem_sinal']=df.dia_primeiro_sinal.notna()

print("### Regra de acionamento do dia_primeiro_sinal ###")
for thr in [13,14,15,16]:
    rule = df.parou_48h | df.sem_ping_24h | df.jornada_impossivel | (df.dias_inadimplencia_max>=thr)
    print(f"thr inadimp>={thr}: divergencias = {(rule!=df.tem_sinal).sum()}")
rule = df.parou_48h | df.sem_ping_24h | df.jornada_impossivel | (df.dias_inadimplencia_max>=15)
print("com blindagem/device incluidos:", ((rule|df.violacao_blindagem|df.device_compartilhado)!=df.tem_sinal).sum())
print()
print("### blindagem/device isolados geram sinal? ###")
solo = df[(~df.parou_48h)&(~df.sem_ping_24h)&(~df.jornada_impossivel)&(df.dias_inadimplencia_max<15)]
print(pd.crosstab(solo.violacao_blindagem, solo.tem_sinal))
print(pd.crosstab(solo.device_compartilhado, solo.tem_sinal))
print()
print("### LEAKAGE: gap = dias_locacao - dia_desfecho ###")
df['gap']=df.dias_locacao-df.dia_desfecho
print(pd.crosstab(df.gap>0, df.desfecho))
print()
print("### Taxas por sinal (perda = APROPRIADA) ###")
base_ap = (df.desfecho=='APROPRIADA').mean()
base_risk = (df.desfecho!='DEVOLVIDA').mean()
print(f"base APROPRIADA={base_ap:.3%} | base RISCO(apr+rec)={base_risk:.3%}\n")
rows=[]
feats = b + ['inadimp>=15','inadimp>=30','8+ km','caucao R$0-300','Semanal','18-24']
df['inadimp>=15']=df.dias_inadimplencia_max>=15
df['inadimp>=30']=df.dias_inadimplencia_max>=30
df['8+ km']=df.dist_base_km=='8+ km'
df['caucao R$0-300']=df.faixa_caucao=='R$0-300'
df['Semanal']=df.pacote_tipo=='Semanal'
df['18-24']=df.faixa_idade=='18-24'
for f in feats:
    m=df[f]
    n=m.sum()
    ap=(df.loc[m,'desfecho']=='APROPRIADA').mean()
    rk=(df.loc[m,'desfecho']!='DEVOLVIDA').mean()
    ap0=(df.loc[~m,'desfecho']=='APROPRIADA').mean()
    rec_ap = (m & (df.desfecho=='APROPRIADA')).sum()/ (df.desfecho=='APROPRIADA').sum()
    rows.append(dict(sinal=f, n=int(n), pct_base=n/len(df),
                     prec_APR=ap, lift_APR=ap/base_ap,
                     recall_APR=rec_ap, taxa_sem_sinal=ap0,
                     prec_RISCO=rk, lift_RISCO=rk/base_risk))
r=pd.DataFrame(rows).sort_values('lift_APR',ascending=False)
print(r.to_string(index=False, float_format=lambda x: f"{x:,.3f}"))
