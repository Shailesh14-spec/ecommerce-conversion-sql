"""Build a reconciled retail star schema and a chronological demand benchmark."""
from pathlib import Path
from decimal import Decimal,ROUND_HALF_UP
import argparse,hashlib,json,sqlite3
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/model';OUT.mkdir(parents=True,exist_ok=True)
REPORT=ROOT/'reports';REPORT.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ROOT/'data/raw/Online Retail.xlsx');args=p.parse_args()
raw=pd.read_excel(args.source)
raw['SourceRow']=np.arange(2,len(raw)+2)
assert len(raw)==541909,'Unexpected upstream row count; review source'
required=['InvoiceNo','StockCode','Quantity','InvoiceDate','UnitPrice','Country']
assert not raw[required].isna().any().any()
df=raw.copy();df.InvoiceNo=df.InvoiceNo.astype(str);df.StockCode=df.StockCode.astype(str)
reject=(df.UnitPrice<=0)|(df.Quantity==0)|(df.InvoiceNo.str.upper().str.startswith('C')&(df.Quantity>0))
excluded=df.loc[reject];df=df.loc[~reject].copy()
df['CustomerKey']=df.CustomerID.fillna(0).astype(int)
df['Date']=df.InvoiceDate.dt.normalize();df['DateKey']=df.Date.dt.strftime('%Y%m%d').astype(int)
# Retain repeated-looking source lines: no transaction-line identifier proves duplication.
df['NetRevenueCents']=[int((Decimal(str(q))*Decimal(str(v))*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP)) for q,v in zip(df.Quantity,df.UnitPrice)]
df['GrossRevenueCents']=df.NetRevenueCents.clip(lower=0)
df['CancellationValueCents']=(-df.NetRevenueCents).clip(lower=0)
df['SalesUnits']=df.Quantity.clip(lower=0);df['CancelledUnits']=(-df.Quantity).clip(lower=0)
country=pd.DataFrame({'Country':sorted(df.Country.unique())});country['CountryKey']=np.arange(1,len(country)+1)
products=df.sort_values('InvoiceDate').groupby('StockCode',sort=True).Description.last().fillna('Description unavailable').reset_index()
products['ProductKey']=np.arange(1,len(products)+1)
df=df.merge(country,on='Country',validate='many_to_one').merge(products[['StockCode','ProductKey']],on='StockCode',validate='many_to_one')
fact=df[['SourceRow','InvoiceNo','DateKey','CustomerKey','CountryKey','ProductKey','Quantity','SalesUnits','CancelledUnits','NetRevenueCents','GrossRevenueCents','CancellationValueCents']].copy()
lastday=df.Date.max();last_complete_month=lastday.to_period('M')-1
positive=df.loc[(df.Quantity>0)&(df.CustomerKey!=0)]
customer=positive.groupby('CustomerKey').agg(FirstPurchase=('Date','min'),LastPurchase=('Date','max'),Frequency=('InvoiceNo','nunique'),MonetaryCents=('GrossRevenueCents','sum')).reset_index()
customer['RecencyDays']=(lastday+pd.Timedelta(days=1)-customer.LastPurchase).dt.days
# Explicit rules use interpretable thresholds; segment assignments are an end-of-data snapshot.
customer['Segment']=np.select([(customer.RecencyDays<=30)&(customer.Frequency>=5),customer.RecencyDays>90],['Frequent recent','Inactive 90+ days'],default='Other known buyers')
allkeys=pd.DataFrame({'CustomerKey':sorted(df.CustomerKey.unique())})
customer=allkeys.merge(customer,on='CustomerKey',how='left',validate='one_to_one')
customer.loc[customer.CustomerKey==0,'Segment']='Anonymous'
customer.Segment=customer.Segment.fillna('No positive purchase')
customer['RecencyDays']=customer.RecencyDays.fillna(-1).astype(int)
customer['Frequency']=customer.Frequency.fillna(0).astype(int);customer['MonetaryCents']=customer.MonetaryCents.fillna(0).astype('int64')
customer['AcquisitionMonth']=customer.FirstPurchase.dt.strftime('%Y-%m').fillna('Unknown')
customer=customer[['CustomerKey','Segment','RecencyDays','Frequency','MonetaryCents','AcquisitionMonth']]
# Customer cohorts use complete months only and known customers only.
a=positive.loc[positive.Date.dt.to_period('M')<=last_complete_month].copy()
a['Month']=a.Date.dt.to_period('M');first=a.groupby('CustomerKey').Month.min();a['Cohort']=a.CustomerKey.map(first)
a['AgeMonth']=(a.Month.astype('int64')-a.Cohort.astype('int64')).astype(int)
counts=a.groupby(['Cohort','AgeMonth']).CustomerKey.nunique();sizes=first.value_counts()
cohort=[]
for month in sorted(first.unique()):
 for age in range(last_complete_month.ordinal-month.ordinal+1):
  cohort.append({'CohortMonth':str(month),'AgeMonth':age,'ActiveCustomers':int(counts.get((month,age),0)),'CohortCustomers':int(sizes[month])})
cohort=pd.DataFrame(cohort)
assert cohort.ActiveCustomers.le(cohort.CohortCustomers).all()
assert cohort.loc[cohort.AgeMonth==0,'ActiveCustomers'].eq(cohort.loc[cohort.AgeMonth==0,'CohortCustomers']).all()
# Forecast gross daily revenue. Exclude final day because the extract ends before midnight.
daily=df.groupby('Date').GrossRevenueCents.sum().div(100).reindex(pd.date_range(df.Date.min(),lastday-pd.Timedelta(days=1)),fill_value=0).rename_axis('Date').reset_index(name='ActualGBP')
f=daily.copy()
for lag in [1,7,14,28]:f[f'lag{lag}']=f.ActualGBP.shift(lag)
f['mean7']=f.ActualGBP.shift(1).rolling(7).mean();f['dow_sin']=np.sin(2*np.pi*f.Date.dt.dayofweek/7);f['dow_cos']=np.cos(2*np.pi*f.Date.dt.dayofweek/7);f['trend']=np.arange(len(f));f=f.dropna()
cols=['lag1','lag7','lag14','lag28','mean7','dow_sin','dow_cos','trend']
train,val,test=f.iloc[:-56],f.iloc[-56:-28],f.iloc[-28:]
assert train.Date.max()<val.Date.min()<test.Date.min()
candidates=[]
for alpha in [1,10,100]:
 m=make_pipeline(StandardScaler(),Ridge(alpha=alpha)).fit(train[cols],train.ActualGBP)
 vp=np.maximum(m.predict(val[cols]),0);candidates.append((mean_absolute_error(val.ActualGBP,vp),alpha,m))
_,alpha,m=min(candidates,key=lambda v:v[0]);pred=np.maximum(m.predict(test[cols]),0)
benchmark={'train_days':len(train),'validation_days':28,'test_days':28,'selected_alpha':alpha,'model_mae_gbp':mean_absolute_error(test.ActualGBP,pred),'seasonal_naive_mae_gbp':mean_absolute_error(test.ActualGBP,test.lag7)}
benchmark['mae_improvement_pct']=100*(1-benchmark['model_mae_gbp']/benchmark['seasonal_naive_mae_gbp'])
forecast=test[['Date','ActualGBP']].assign(ForecastGBP=pred,BaselineGBP=test.lag7.to_numpy(),SeriesType='Backtest')
# Refit only after fixed evaluation; recursive future predictions use their own lags.
final=make_pipeline(StandardScaler(),Ridge(alpha=alpha)).fit(f[cols],f.ActualGBP)
history=daily.ActualGBP.tolist();future=[]
for step in range(28):
 date=daily.Date.max()+pd.Timedelta(days=step+1)
 row=[history[-1],history[-7],history[-14],history[-28],float(np.mean(history[-7:])),np.sin(2*np.pi*date.dayofweek/7),np.cos(2*np.pi*date.dayofweek/7),len(history)]
 value=float(max(final.predict(pd.DataFrame([row],columns=cols))[0],0));future.append({'Date':date,'ActualGBP':np.nan,'ForecastGBP':value,'BaselineGBP':np.nan,'SeriesType':'Future scenario'});history.append(value)
forecast=pd.concat([forecast,pd.DataFrame(future)],ignore_index=True);forecast['DateKey']=forecast.Date.dt.strftime('%Y%m%d').astype(int);forecast=forecast.drop(columns='Date')
dates=pd.date_range(df.Date.min(),pd.to_datetime(str(forecast.DateKey.max())))
date=pd.DataFrame({'Date':dates});date['DateKey']=date.Date.dt.strftime('%Y%m%d').astype(int);date['Year']=date.Date.dt.year;date['MonthNumber']=date.Date.dt.month;date['YearMonth']=date.Date.dt.strftime('%Y-%m');date['MonthSort']=date.Date.dt.year*100+date.Date.dt.month;date['IsCompleteMonth']=(date.Date.dt.to_period('M')<=last_complete_month)
scenario=pd.DataFrame({'CostRatio':np.arange(30,91,5)/100})
tables={'FactTransactions':fact,'DimDate':date,'DimCountry':country,'DimProduct':products[['ProductKey','StockCode','Description']],'DimCustomer':customer,'FactCohort':cohort,'FactForecast':forecast,'CostScenario':scenario}
for name,table in tables.items():table.to_csv(OUT/(name+'.csv'),index=False,date_format='%Y-%m-%d')
# Reconciled SQL marts execute against the exact same prepared tables.
con=sqlite3.connect(':memory:')
for name,table in tables.items():table.to_sql(name,con,index=False)
query=(ROOT/'sql/revenue_mart.sql').read_text();monthly=pd.read_sql_query(query,con);con.close();monthly.to_csv(REPORT/'monthly_revenue.csv',index=False)
assert int(monthly.NetRevenueCents.sum())==int(fact.NetRevenueCents.sum())
assert int(fact.GrossRevenueCents.sum()-fact.CancellationValueCents.sum())==int(fact.NetRevenueCents.sum())
for key,dim in [('DateKey',date),('CountryKey',country),('ProductKey',products),('CustomerKey',customer)]:
 assert dim[key].is_unique
 assert fact[key].isin(dim[key]).all()
metrics={'source_rows':len(raw),'included_rows':len(df),'excluded_rows':len(excluded),'missing_customer_source_rows':int(raw.CustomerID.isna().sum()),'identical_source_rows_preserved':int(raw.drop(columns='SourceRow').duplicated().sum()),'gross_revenue_gbp':int(fact.GrossRevenueCents.sum())/100,'cancellation_value_gbp':int(fact.CancellationValueCents.sum())/100,'net_revenue_gbp':int(fact.NetRevenueCents.sum())/100,'positive_invoices':int(df.loc[df.Quantity>0,'InvoiceNo'].nunique()),'known_customer_keys':int((customer.CustomerKey!=0).sum()),'known_purchasing_customers':int(positive.CustomerKey.nunique()),'products':len(products),'countries':len(country),'last_transaction_day':str(lastday.date()),'last_complete_month':str(last_complete_month),'raw_sha256':hashlib.sha256(args.source.read_bytes()).hexdigest(),'forecast':benchmark}
(REPORT/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
excluded.assign(Reason=np.where(excluded.UnitPrice<=0,'non-positive price',np.where(excluded.Quantity==0,'zero quantity','positive quantity on credit note'))).groupby('Reason').agg(Rows=('SourceRow','size')).to_csv(REPORT/'exclusion_audit.csv')
customer.groupby('Segment').agg(Customers=('CustomerKey','size'),GrossRevenueCents=('MonetaryCents','sum')).to_csv(REPORT/'customer_segments.csv')
products_report=df.groupby('Description').agg(GrossRevenueCents=('GrossRevenueCents','sum'),CancellationValueCents=('CancellationValueCents','sum')).sort_values('GrossRevenueCents',ascending=False).head(10);products_report.to_csv(REPORT/'top_products.csv')
cohort.to_csv(REPORT/'cohort_retention.csv',index=False)
print(json.dumps(metrics,indent=2))
