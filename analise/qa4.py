import pandas as pd, numpy as np, itertools
pd.set_option('display.width',250)
df = pd.read_excel('dados -PrevencaoPerdas_Base.xlsx', sheet_name='Dados')
b=['parou_48h','sem_ping_24h','violacao_blindagem','device_compartilhado','jornada_impossivel']
for c in b: df[c]=(df[c]=='SIM')
df['inad15']=df.dias_inadimplencia_max>=15
df['APR']=df.desfecho=='APROPRIADA'
df['RISCO']=df.desfecho!='DEVOLVIDA'

print("### Co-ocorrencia parou_48h x sem_ping_24h ###")
print(pd.crosstab(df.parou_48h, df.sem_ping_24h))
print("\ntaxa APROPRIADA por celula:")
print((df.pivot_table(index='parou_48h',columns='sem_ping_24h',values='APR',aggfunc=['mean','sum','count'])*1).round(3).to_string())
print()
print("### Combos de 2 sinais: precisao para APROPRIADA ###")
feats=b+['inad15']
rows=[]
for k in [1,2,3]:
    for combo in itertools.combinations(feats,k):
        m=np.ones(len(df),bool)
        for c in combo: m &= df[c].values
        n=m.sum()
        if n<5: continue
        rows.append(dict(combo=' + '.join(combo), n=int(n), APR=int(df.APR[m].sum()),
                         prec=df.APR[m].mean(), recall=df.APR[m].sum()/df.APR.sum(),
                         prec_risco=df.RISCO[m].mean()))
r=pd.DataFrame(rows).sort_values(['prec','n'],ascending=[False,False])
print(r.head(25).to_string(index=False,float_format=lambda x:f"{x:,.3f}"))
print()
print("### Os 'invisiveis': blindagem OU device sem gatilho de relogio ###")
solo=(~df.parou_48h)&(~df.sem_ping_24h)&(~df.jornada_impossivel)&(~df.inad15)&(df.violacao_blindagem|df.device_compartilhado)
print("n =", solo.sum(), "| desfechos:", df.desfecho[solo].value_counts().to_dict())
print()
print("### Blindagem: efeito condicional dentro dos que ja tem sinal de telemetria ###")
tel=df.parou_48h|df.sem_ping_24h
print(pd.crosstab(df.violacao_blindagem[tel], df.desfecho[tel]))
print((pd.crosstab(df.violacao_blindagem[tel], df.desfecho[tel],normalize='index')*100).round(1))
print()
print("### Inadimplencia dentro dos que tem 2+ sinais telemetria ###")
df['n_tel']=df[['parou_48h','sem_ping_24h','violacao_blindagem','device_compartilhado','jornada_impossivel']].sum(axis=1)
sub=df[df.n_tel>=2]
sub=sub.copy(); sub['fx_inad']=pd.cut(sub.dias_inadimplencia_max,[-1,0,14,29,60],labels=['0','1-14','15-29','30+'])
print(pd.crosstab(sub.fx_inad,sub.desfecho))
print((pd.crosstab(sub.fx_inad,sub.desfecho,normalize='index')*100).round(1))
print()
print("### Modelo simples: regressao logistica (sem vazamento) ###")
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold
X=pd.get_dummies(df[['parou_48h','sem_ping_24h','violacao_blindagem','device_compartilhado','jornada_impossivel','dias_inadimplencia_max','dist_base_km','faixa_caucao','pacote_tipo','faixa_idade','sexo','regiao']],drop_first=True).astype(float)
y=df.APR.astype(int)
m=LogisticRegression(max_iter=2000,C=1.0).fit(X,y)
coef=pd.Series(m.coef_[0],index=X.columns).sort_values(ascending=False)
print(coef.round(3).to_string())
print("\nAUC 5-fold (APROPRIADA):", cross_val_score(LogisticRegression(max_iter=2000),X,y,cv=StratifiedKFold(5,shuffle=True,random_state=1),scoring='roc_auc').mean().round(3))
print("AUC 5-fold (RISCO):", cross_val_score(LogisticRegression(max_iter=2000),X,df.RISCO.astype(int),cv=StratifiedKFold(5,shuffle=True,random_state=1),scoring='roc_auc').mean().round(3))
