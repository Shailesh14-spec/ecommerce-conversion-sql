from pathlib import Path
import json,sqlite3,unittest
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
class RetailTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.d={p.stem:pd.read_csv(p) for p in (ROOT/'data/model').glob('*.csv')}
  cls.f=cls.d['FactTransactions'];cls.metrics=json.loads((ROOT/'reports/metrics.json').read_text());cls.model=json.loads((ROOT/'powerbi/RetailIntelligence.SemanticModel/model.bim').read_text())['model']
 def test_row_accounting(self):
  self.assertEqual(self.metrics['source_rows'],self.metrics['included_rows']+self.metrics['excluded_rows']);self.assertEqual(len(self.f),self.metrics['included_rows']);self.assertTrue(self.f.SourceRow.is_unique)
 def test_currency_reconciliation(self):
  np.testing.assert_array_equal(self.f.GrossRevenueCents-self.f.CancellationValueCents,self.f.NetRevenueCents)
  self.assertAlmostEqual(self.f.NetRevenueCents.sum()/100,self.metrics['net_revenue_gbp'])
 def test_dimension_keys_and_referential_integrity(self):
  for key,name in [('DateKey','DimDate'),('CountryKey','DimCountry'),('ProductKey','DimProduct'),('CustomerKey','DimCustomer')]:
   self.assertTrue(self.d[name][key].is_unique);self.assertTrue(self.f[key].isin(self.d[name][key]).all())
 def test_customer_denominator(self):
  actual=self.f.loc[(self.f.CustomerKey!=0)&(self.f.Quantity>0),'CustomerKey'].nunique()
  self.assertEqual(actual,self.metrics['known_purchasing_customers'])
 def test_cohort_censoring(self):
  c=self.d['FactCohort'];self.assertTrue(c.ActiveCustomers.le(c.CohortCustomers).all())
  self.assertTrue(c.loc[c.AgeMonth==0,'ActiveCustomers'].eq(c.loc[c.AgeMonth==0,'CohortCustomers']).all())
  end=pd.Period(self.metrics['last_complete_month'],freq='M')
  self.assertTrue(all(pd.Period(r.CohortMonth,freq='M').ordinal+int(r.AgeMonth)<=end.ordinal for r in c.itertuples()))
 def test_sql_totals(self):
  with sqlite3.connect(':memory:') as con:
   self.f.to_sql('FactTransactions',con,index=False);self.d['DimDate'].to_sql('DimDate',con,index=False)
   result=pd.read_sql_query((ROOT/'sql/revenue_mart.sql').read_text(),con)
  self.assertEqual(result.NetRevenueCents.sum(),self.f.NetRevenueCents.sum())
 def test_forecast_holdout(self):
  f=self.d['FactForecast'];test=f.loc[f.SeriesType=='Backtest'];future=f.loc[f.SeriesType=='Future scenario']
  self.assertEqual(len(test),28);self.assertEqual(len(future),28);self.assertTrue(future.ActualGBP.isna().all());self.assertLess(test.DateKey.max(),future.DateKey.min())
  self.assertAlmostEqual(float(np.abs(test.ActualGBP-test.ForecastGBP).mean()),self.metrics['forecast']['model_mae_gbp'])
  daily=self.f.groupby('DateKey').GrossRevenueCents.sum()/100
  daily.index=pd.to_datetime(daily.index.astype(str));daily=daily.reindex(pd.date_range(daily.index.min(),daily.index.max()),fill_value=0)
  dates=pd.to_datetime(test.DateKey.astype(str));np.testing.assert_allclose(test.BaselineGBP.to_numpy(),daily.reindex(dates-pd.Timedelta(days=7)).to_numpy())
 def test_model_and_visual_references(self):
  tables={t['name']:t for t in self.model['tables']}
  columns={name:{c['name'] for c in t['columns']} for name,t in tables.items()}
  measures={m['name'] for t in tables.values() for m in t.get('measures',[])}
  for relationship in self.model['relationships']:
   for prefix in ['from','to']:self.assertIn(relationship[prefix+'Column'],columns[relationship[prefix+'Table']])
  for p in (ROOT/'powerbi/RetailIntelligence.Report').rglob('visual.json'):
   v=json.loads(p.read_text());self.assertLessEqual(v['position']['x']+v['position']['width'],1440);self.assertLessEqual(v['position']['y']+v['position']['height'],800)
   for role in v['visual']['query']['queryState'].values():
    for projection in role['projections']:
     key=next(iter(projection['field']));ref=projection['field'][key];table=ref['Expression']['SourceRef']['Entity'];self.assertIn(table,tables)
     self.assertIn(ref['Property'],measures if key=='Measure' else columns[table])
if __name__=='__main__':unittest.main()
