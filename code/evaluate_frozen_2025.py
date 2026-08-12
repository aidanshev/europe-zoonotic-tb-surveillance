#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np,pandas as pd
from scipy.special import expit,logit
from sklearn.metrics import average_precision_score,roc_auc_score,brier_score_loss,log_loss
from sklearn.linear_model import LogisticRegression

def metrics(y,p):
 p=np.clip(np.asarray(p,float),1e-6,1-1e-6);y=np.asarray(y,int)
 return {'auroc':float(roc_auc_score(y,p)) if len(np.unique(y))==2 else None,'auprc':float(average_precision_score(y,p)),'brier':float(brier_score_loss(y,p)),'log_loss':float(log_loss(y,p,labels=[0,1]))}

def calib(y,p):
 p=np.clip(np.asarray(p,float),1e-6,1-1e-6);x=logit(p).reshape(-1,1);y=np.asarray(y,int)
 try:
  lr=LogisticRegression(C=1e6,solver='lbfgs').fit(x,y);return {'intercept':float(lr.intercept_[0]),'slope':float(lr.coef_[0,0])}
 except Exception:return {'intercept':None,'slope':None}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--outcomes',required=True);ap.add_argument('--predictions',required=True);ap.add_argument('--output-dir',required=True);ap.add_argument('--bootstrap',type=int,default=10000);ap.add_argument('--permutations',type=int,default=20000);ap.add_argument('--seed',type=int,default=20260719);a=ap.parse_args()
 out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True);o=pd.read_csv(a.outcomes);p=pd.read_csv(a.predictions)
 reqo={'country_code','species_reporting_status','human_cases'};reqp={'country_code','history_probability','dynamic_animal_probability'}
 if not reqo.issubset(o) or not reqp.issubset(p):raise ValueError('FAIL_CLOSED: required columns missing')
 if p.country_code.nunique()!=26:raise ValueError(f'FAIL_CLOSED: controlling prediction file must contain 26 unique scored countries, found {p.country_code.nunique()}')
 d=p.merge(o,on='country_code',how='left',validate='one_to_one');eligible=d.species_reporting_status.isin(['reported','reported_zero']) & d.human_cases.notna();d=d[eligible].copy();d['y']=(d.human_cases>0).astype(int)
 if len(d)<20 or d.y.nunique()<2:raise ValueError('FAIL_CLOSED: insufficient evaluable 2025 outcomes')
 mh=metrics(d.y,d.history_probability);ma=metrics(d.y,d.dynamic_animal_probability)
 obs={'delta_auprc':ma['auprc']-mh['auprc'],'delta_brier':mh['brier']-ma['brier'],'delta_log_loss':mh['log_loss']-ma['log_loss']}
 rng=np.random.default_rng(a.seed);n=len(d);boots=[]
 for _ in range(a.bootstrap):
  ix=rng.integers(0,n,n);z=d.iloc[ix]
  if z.y.nunique()<2:continue
  xh=metrics(z.y,z.history_probability);xa=metrics(z.y,z.dynamic_animal_probability);boots.append([xa['auprc']-xh['auprc'],xh['brier']-xa['brier'],xh['log_loss']-xa['log_loss']])
 b=np.asarray(boots);ci={k:[float(v) for v in np.quantile(b[:,i],[.025,.975])] for i,k in enumerate(obs)}
 delta=logit(np.clip(d.dynamic_animal_probability,1e-6,1-1e-6))-logit(np.clip(d.history_probability,1e-6,1-1e-6));perm=[]
 for _ in range(a.permutations):
  pp=expit(logit(np.clip(d.history_probability.to_numpy(),1e-6,1-1e-6))+rng.permutation(delta))
  perm.append(average_precision_score(d.y,pp)-mh['auprc'])
 pval=(1+sum(x>=obs['delta_auprc'] for x in perm))/(1+a.permutations)
 thresholds=np.arange(.05,.51,.05);dc=[]
 for t in thresholds:
  row={'threshold':float(t)}
  for name,col in [('history','history_probability'),('dynamic','dynamic_animal_probability')]:
   pred=d[col]>=t;tp=int(((pred)&(d.y==1)).sum());fp=int(((pred)&(d.y==0)).sum());row[name+'_net_benefit']=tp/n-fp/n*t/(1-t);row[name+'_reviews']=int(pred.sum())
  dc.append(row)
 result={'status':'PROSPECTIVE_2025_EVALUATED_WITHOUT_REFIT','n_evaluable':n,'n_events':int(d.y.sum()),'history':mh,'dynamic_animal':ma,'differences_positive_favors_dynamic':obs,'country_bootstrap_95_ci':ci,'animal_alignment_permutation_p':float(pval),'calibration':{'history':calib(d.y,d.history_probability),'dynamic':calib(d.y,d.dynamic_animal_probability)}}
 (out/'PROSPECTIVE_2025_RESULTS.json').write_text(json.dumps(result,indent=2));pd.DataFrame(dc).to_csv(out/'decision_curve.csv',index=False);d.to_csv(out/'scored_countries.csv',index=False);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
