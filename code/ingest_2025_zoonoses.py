#!/usr/bin/env python3
"""Fail-closed ingestion template for the 2025 EFSA-ECDC zoonoses release.

Preferred inputs are official CSV/XLSX/HTML tables. PDF table extraction is permitted
only when text tables are machine-readable; OCR and map digitization are prohibited.
"""
from __future__ import annotations
import argparse,hashlib,json,re,shutil
from pathlib import Path
import pandas as pd
EU27=['AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','GR','HU','IE','IT','LV','LT','LU','MT','NL','PL','PT','RO','SK','SI','ES','SE']
NAME_TO_CODE={'Austria':'AT','Belgium':'BE','Bulgaria':'BG','Croatia':'HR','Cyprus':'CY','Czechia':'CZ','Czech Republic':'CZ','Denmark':'DK','Estonia':'EE','Finland':'FI','France':'FR','Germany':'DE','Greece':'GR','Hungary':'HU','Ireland':'IE','Italy':'IT','Latvia':'LV','Lithuania':'LT','Luxembourg':'LU','Malta':'MT','Netherlands':'NL','The Netherlands':'NL','Poland':'PL','Portugal':'PT','Romania':'RO','Slovakia':'SK','Slovenia':'SI','Spain':'ES','Sweden':'SE'}
def sha256(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def norm(s):return re.sub(r'[^a-z0-9]+','_',str(s).strip().lower()).strip('_')
def read_tables(path):
 suf=path.suffix.lower()
 if suf=='.csv':return [('csv',pd.read_csv(path))]
 if suf in ('.xlsx','.xls'):
  book=pd.ExcelFile(path);return [(s,pd.read_excel(path,sheet_name=s)) for s in book.sheet_names]
 if suf in ('.html','.htm'):return [(f'html_table_{i}',t) for i,t in enumerate(pd.read_html(path),1)]
 if suf=='.pdf':
  try:import pdfplumber
  except ImportError as e:raise RuntimeError('pdfplumber is required for text-table PDF extraction') from e
  out=[]
  with pdfplumber.open(path) as pdf:
   for pn,page in enumerate(pdf.pages,1):
    for ti,t in enumerate(page.extract_tables() or [],1):
     if t and len(t)>1:out.append((f'pdf_page_{pn}_table_{ti}',pd.DataFrame(t[1:],columns=t[0])))
  return out
 raise ValueError(f'Unsupported file type: {suf}')
def find_col(df,candidates):
 cols={norm(c):c for c in df.columns}
 for c in candidates:
  if norm(c) in cols:return cols[norm(c)]
 return None
def normalize_human(path,report_year):
 tables=read_tables(path);candidates=[]
 for name,df in tables:
  cc=find_col(df,['country_code','iso2']);cn=find_col(df,['country','member_state','country_name']);cases=find_col(df,['cases','confirmed_cases','human_cases'])
  if (cc or cn) and cases:candidates.append((name,df,cc,cn,cases,find_col(df,['species_reporting_status','reporting_status'])))
 if not candidates:raise ValueError('FAIL_CLOSED: no table with country and human-case columns')
 name,df,cc,cn,cases,status=max(candidates,key=lambda x:len(x[1]));rows=[];source_hash=sha256(path)
 for _,r in df.iterrows():
  country=str(r[cn]).strip() if cn and pd.notna(r[cn]) else '';code=str(r[cc]).strip().upper() if cc and pd.notna(r[cc]) else NAME_TO_CODE.get(country,'')
  if code not in EU27:continue
  raw=r[cases];state=str(r[status]).strip().lower() if status and pd.notna(r[status]) else None
  if pd.isna(raw) or str(raw).strip() in ('','..',':','NA','N/A'):human_cases=None;state=state or 'species_specific_unavailable'
  else:human_cases=int(float(raw));state=state or ('reported_zero' if human_cases==0 else 'reported')
  if state not in ['reported','reported_zero','species_specific_unavailable','unknown']:raise ValueError(f'FAIL_CLOSED: invalid reporting state {state!r} for {code}')
  if state in ['species_specific_unavailable','unknown'] and human_cases is not None:raise ValueError(f'FAIL_CLOSED: unavailable row has numeric count for {code}')
  if state in ['reported','reported_zero'] and human_cases is None:raise ValueError(f'FAIL_CLOSED: reported row lacks count for {code}')
  rows.append({'country_code':code,'country':country or code,'report_year':report_year,'species_reporting_status':state,'human_cases':human_cases,'source_file_sha256':source_hash,'source_table':name,'origin_within_eu':None,'origin_outside_eu':None,'origin_unknown':None,'vintage_date':None})
 out=pd.DataFrame(rows).drop_duplicates('country_code',keep=False)
 if out.country_code.duplicated().any():raise ValueError('FAIL_CLOSED: duplicated country codes')
 if len(out)<20:raise ValueError(f'FAIL_CLOSED: only {len(out)} EU country rows found')
 return out
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--human-file',required=True);ap.add_argument('--report-year',type=int,default=2025);ap.add_argument('--output-dir',required=True);ap.add_argument('--expected-eu-total',type=int);a=ap.parse_args();src=Path(a.human_file);outdir=Path(a.output_dir);outdir.mkdir(parents=True,exist_ok=True);raw=outdir/'raw';raw.mkdir(exist_ok=True);shutil.copy2(src,raw/src.name);human=normalize_human(src,a.report_year);human.to_csv(outdir/'human_country_2025_normalized.csv',index=False);numeric_total=int(human.human_cases.dropna().sum());n_unavailable=int(human.human_cases.isna().sum());checks={'row_count':len(human),'numeric_total':numeric_total,'unavailable_countries':n_unavailable,'unique_country_codes':bool(human.country_code.is_unique),'expected_total_match':None if a.expected_eu_total is None else numeric_total==a.expected_eu_total}
 if a.expected_eu_total is not None and numeric_total!=a.expected_eu_total:raise ValueError(f'FAIL_CLOSED: country total {numeric_total} != expected EU total {a.expected_eu_total}')
 receipt={'status':'PASS','report_year':a.report_year,'source_file':src.name,'source_sha256':sha256(src),'checks':checks,'rules':['unavailable_not_zero','no_ocr','no_map_digitization','exact_total_reconciliation_if_supplied']};(outdir/'INGESTION_RECEIPT.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
