import pandas as pd, numpy as np
pd.set_option('display.width',250)
df = pd.read_excel('dados -PrevencaoPerdas_Base.xlsx', sheet_name='Dados')
b=['parou_48h','sem_ping_24h','violacao_blindagem','device_compartilhado','jornada_impossivel']
for c in b: df[c]=(df[c]=='SIM')
df['APR']=df.desfecho=='APROPRIADA'; df['RISCO']=df.desfecho!='DEVOLVIDA'
df['inad']=df.dias_inadimplencia_max

print("### Sinal ISOLADO x combinado (o argumento do 'ruido benigno') ###")
def cel(mask,label):
    n=mask.sum(); 
    print(f"{label:<52} n={n:>3}  APR={df.APR[mask].sum():>2} ({df.APR[mask].mean():6.1%})  RISCO={df.RISCO[mask].mean():6.1%}")
cel(df.parou_48h&~df.sem_ping_24h, "parou_48h SOZINHO (sem sem_ping)")
cel(~df.parou_48h&df.sem_ping_24h, "sem_ping SOZINHO (sem parou_48h)")
cel(df.parou_48h&df.sem_ping_24h,  "parou_48h + sem_ping_24h")
cel(df.parou_48h&df.sem_ping_24h&(df.inad>=15), "parou + sem_ping + inad>=15")
cel(df.parou_48h&df.sem_ping_24h&(df.inad>=30), "parou + sem_ping + inad>=30")
cel(df.violacao_blindagem&~(df.parou_48h|df.sem_ping_24h), "blindagem SOZINHA")
cel(df.violacao_blindagem&(df.parou_48h|df.sem_ping_24h), "blindagem + telemetria")
cel((df.inad>=30)&~(df.parou_48h|df.sem_ping_24h), "inad>=30 SOZINHA")
cel((df.inad>=30)&(df.parou_48h|df.sem_ping_24h), "inad>=30 + telemetria")
print()
print("### GRUPOS PROPOSTOS ###")
tel2 = df.parou_48h & df.sem_ping_24h
g1 = tel2 & ((df.inad>=15) | df.violacao_blindagem | df.jornada_impossivel)
g2 = (~g1) & ( (tel2) | ((df.parou_48h|df.sem_ping_24h)&((df.inad>=15)|df.violacao_blindagem)) )
g3 = (~g1)&(~g2)&( (df.parou_48h|df.sem_ping_24h|(df.inad>=15)) )
g0 = (~g1)&(~g2)&(~g3)
for name,m in [('G1 CRITICO',g1),('G2 ALTO',g2),('G3 MONITORAR',g3),('G0 fora do radar',g0)]:
    print(f"{name:<18} n={m.sum():>3} ({m.mean():5.1%})  APR={df.APR[m].sum():>2}/{df.APR.sum()} recall={df.APR[m].sum()/df.APR.sum():6.1%}  prec_APR={df.APR[m].mean():6.1%}  prec_RISCO={df.RISCO[m].mean():6.1%}")
print()
print("Cobertura acumulada de APROPRIADAS:")
print(f"  G1: {df.APR[g1].sum()}/24   G1+G2: {df.APR[g1|g2].sum()}/24   G1+G2+G3: {df.APR[g1|g2|g3].sum()}/24")
print()
print("### Janela por grupo (dias entre 1o sinal e desfecho) ###")
df['janela']=df.dia_desfecho-df.dia_primeiro_sinal
for name,m in [('G1',g1),('G2',g2),('G3',g3)]:
    sub=df[m&df.APR]
    print(f"{name}: APR n={len(sub)} janela med={sub.janela.median()} min={sub.janela.min()} max={sub.janela.max()}")
print()
print("### Dia do 1o sinal no contrato (quando o risco aparece) ###")
print(df.groupby('desfecho').dia_primeiro_sinal.describe(percentiles=[.25,.5,.75]).round(1).to_string())
print()
print("### Sanity: dias_locacao NAO deve ser usado (vazamento) ###")
print("corr(gap>0, nao-DEVOLVIDA):", ((df.dias_locacao-df.dia_desfecho>0)==df.RISCO).mean().round(3), "de acerto trivial")
