"""Generate native PBIP/PBIR report source and a TMSL import semantic model."""
from pathlib import Path
import json,uuid
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];PBI=ROOT/'powerbi';MODEL=PBI/'RetailIntelligence.SemanticModel';REPORT=PBI/'RetailIntelligence.Report'
MODEL.mkdir(parents=True,exist_ok=True);REPORT.mkdir(exist_ok=True)
def write(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
CURRENCY='£#,0.00;(£#,0.00);£0.00';INTEGER='#,0';PERCENT='0.0%'
measures=[]
def measure(name,expression,folder,fmt=CURRENCY,description=''):
 measures.append({'name':name,'expression':expression,'formatString':fmt,'displayFolder':folder,'description':description})
measure('Gross Revenue','SUM(FactTransactions[GrossRevenueCents]) / 100','Revenue')
measure('Cancellation Value','SUM(FactTransactions[CancellationValueCents]) / 100','Revenue',description='Absolute value of negative retained lines. Not confirmed physical returns.')
measure('Net Revenue','SUM(FactTransactions[NetRevenueCents]) / 100','Revenue')
measure('Revenue Reconciliation','[Gross Revenue] - [Cancellation Value] - [Net Revenue]','Quality')
measure('Positive Orders','CALCULATE(DISTINCTCOUNT(FactTransactions[InvoiceNo]), FactTransactions[Quantity] > 0)','Orders',INTEGER)
measure('Cancelled Invoices','CALCULATE(DISTINCTCOUNT(FactTransactions[InvoiceNo]), FactTransactions[Quantity] < 0)','Orders',INTEGER)
measure('Average Order Value','DIVIDE([Gross Revenue], [Positive Orders])','Orders')
measure('Sales Units','SUM(FactTransactions[SalesUnits])','Orders',INTEGER)
measure('Cancelled Units','SUM(FactTransactions[CancelledUnits])','Orders',INTEGER)
measure('Cancellation Value Rate','DIVIDE([Cancellation Value], [Gross Revenue])','Revenue',PERCENT,description='Period negative-line value divided by positive-line value. No invoice matching is implied.')
measure('Known Customers','CALCULATE(DISTINCTCOUNT(FactTransactions[CustomerKey]), FactTransactions[CustomerKey] <> 0, FactTransactions[Quantity] > 0)','Customers',INTEGER)
measure('Anonymous Revenue','CALCULATE([Gross Revenue], FactTransactions[CustomerKey] = 0)','Customers')
measure('Anonymous Revenue Share','DIVIDE([Anonymous Revenue], [Gross Revenue])','Customers',PERCENT)
measure('Repeat Buyers','COUNTROWS(FILTER(CALCULATETABLE(VALUES(DimCustomer[CustomerKey]), DimCustomer[CustomerKey] <> 0), CALCULATE([Positive Orders]) > 1))','Customers',INTEGER)
measure('Repeat Buyer Share','DIVIDE([Repeat Buyers], [Known Customers])','Customers',PERCENT,description='Repeat in the current transaction filter context. Segment labels are a fixed end-of-data snapshot.')
measure('Net Revenue MTD','TOTALMTD([Net Revenue], DimDate[Date])','Time intelligence')
measure('Net Revenue Previous Month','CALCULATE([Net Revenue], DATEADD(DimDate[Date], -1, MONTH))','Time intelligence')
measure('Net Revenue MoM %','DIVIDE([Net Revenue] - [Net Revenue Previous Month], [Net Revenue Previous Month])','Time intelligence',PERCENT,description='Use in a month-grain visual; final source month is partial.')
measure('Net Revenue Rolling 28D','VAR EndDate = MAX(DimDate[Date]) RETURN CALCULATE([Net Revenue], DATESINPERIOD(DimDate[Date], EndDate, -28, DAY))','Time intelligence')
measure('Complete Month Revenue','CALCULATE([Net Revenue], DimDate[IsCompleteMonth] = TRUE())','Time intelligence')
measure('Product Revenue Rank','RANKX(ALLSELECTED(DimProduct[Description]), [Net Revenue], , DESC, DENSE)','Products',INTEGER)
measure('Top 10 Product Revenue','IF([Product Revenue Rank] <= 10, [Net Revenue])','Products')
measure('Product Revenue Share','DIVIDE([Net Revenue], CALCULATE([Net Revenue], ALLSELECTED(DimProduct)))','Products',PERCENT)
measure('Cohort Active Customers','SUM(FactCohort[ActiveCustomers])','Cohorts',INTEGER)
measure('Cohort Base Customers','SUM(FactCohort[CohortCustomers])','Cohorts',INTEGER)
measure('Cohort Retention %','IF(HASONEVALUE(FactCohort[CohortMonth]) && HASONEVALUE(FactCohort[AgeMonth]), DIVIDE([Cohort Active Customers], [Cohort Base Customers]))','Cohorts',PERCENT,description='Complete-month, known-customer active retention. Matrix totals intentionally blank.')
measure('Month 1 Retention %','VAR Active = CALCULATE(SUM(FactCohort[ActiveCustomers]), FactCohort[AgeMonth] = 1) VAR Eligible = CALCULATE(SUM(FactCohort[CohortCustomers]), FactCohort[AgeMonth] = 1) RETURN DIVIDE(Active, Eligible)','Cohorts',PERCENT,description='Weighted month-1 retention across eligible cohorts; all countries and complete months only.')
measure('Backtest Actual','CALCULATE(SUM(FactForecast[ActualGBP]), FactForecast[SeriesType] = "Backtest")','Forecast')
measure('Backtest Forecast','CALCULATE(SUM(FactForecast[ForecastGBP]), FactForecast[SeriesType] = "Backtest")','Forecast')
measure('Future Scenario Forecast','CALCULATE(SUM(FactForecast[ForecastGBP]), FactForecast[SeriesType] = "Future scenario")','Forecast',description='Historical-origin recursive scenario after the last complete source day, not a forecast of current business conditions.')
measure('Forecast MAE','AVERAGEX(FILTER(FactForecast, FactForecast[SeriesType] = "Backtest"), ABS(FactForecast[ActualGBP] - FactForecast[ForecastGBP]))','Forecast')
measure('Baseline MAE','AVERAGEX(FILTER(FactForecast, FactForecast[SeriesType] = "Backtest"), ABS(FactForecast[ActualGBP] - FactForecast[BaselineGBP]))','Forecast')
measure('Forecast Improvement %','1 - DIVIDE([Forecast MAE], [Baseline MAE])','Forecast',PERCENT,description='Negative values mean the model is worse than the lag-7 baseline.')
measure('Selected Cost Ratio','SELECTEDVALUE(CostScenario[CostRatio], 0.60)','Hypothetical scenario',PERCENT)
measure('Scenario Contribution','[Net Revenue] * (1 - [Selected Cost Ratio])','Hypothetical scenario',description='Illustrative contribution only. No cost, margin or profit observations exist in the source.')
measure('Scenario Contribution Rate','1 - [Selected Cost Ratio]','Hypothetical scenario',PERCENT)
measure('Data Lines','COUNTROWS(FactTransactions)','Quality',INTEGER)

# Model types derive from build outputs but field names and semantics are explicit.
names=['FactTransactions','DimDate','DimCountry','DimProduct','DimCustomer','FactCohort','FactForecast','CostScenario']
tables=[]
for name in names:
 df=pd.read_csv(ROOT/'data/model'/f'{name}.csv')
 columns=[];transforms=[]
 for col in df:
  if name=='DimDate' and col=='Date':dtype='dateTime';mtype='type date'
  elif name=='DimDate' and col=='IsCompleteMonth':dtype='boolean';mtype='type logical'
  elif pd.api.types.is_integer_dtype(df[col]):dtype='int64';mtype='Int64.Type'
  elif pd.api.types.is_float_dtype(df[col]):dtype='double';mtype='type number'
  else:dtype='string';mtype='type text'
  c={'name':col,'dataType':dtype,'sourceColumn':col,'summarizeBy':'none' if dtype in ['string','dateTime','boolean'] or col.endswith('Key') or col in ['Year','MonthNumber','MonthSort','AgeMonth'] else 'sum'}
  if col.endswith('Key') or col.endswith('Cents') or col in ['SourceRow','MonthSort']:c['isHidden']=True
  if name=='CostScenario' and col=='CostRatio':c['formatString']='0%'
  if col.endswith('GBP'):c['formatString']=CURRENCY
  if name=='DimDate' and col=='Date':c.update(isKey=True,formatString='yyyy-MM-dd')
  if name=='DimDate' and col=='YearMonth':c['sortByColumn']='MonthSort'
  columns.append(c);transforms.append('{"'+col+'", '+mtype+'}')
 expr='let\n Source = Csv.Document(File.Contents(SourceFolder & "\\'+name+'.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),\n Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n Typed = Table.TransformColumnTypes(Headers, {'+', '.join(transforms)+'}, "en-GB")\nin Typed'
 t={'name':name,'columns':columns,'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':expr}}]}
 if name=='DimDate':t['dataCategory']='Time'
 tables.append(t)
tables.append({'name':'Metrics','columns':[{'name':'Placeholder','dataType':'int64','sourceColumn':'Placeholder','isHidden':True}],'partitions':[{'name':'Metrics','mode':'import','source':{'type':'m','expression':'#table(type table [Placeholder = Int64.Type], {{1}})'}}],'measures':measures})
rels=[]
for source,col,target in [('FactTransactions','DateKey','DimDate'),('FactTransactions','CountryKey','DimCountry'),('FactTransactions','ProductKey','DimProduct'),('FactTransactions','CustomerKey','DimCustomer'),('FactForecast','DateKey','DimDate')]:
 rels.append({'name':str(uuid.uuid5(uuid.NAMESPACE_DNS,source+col+target)),'fromTable':source,'fromColumn':col,'toTable':target,'toColumn':col,'crossFilteringBehavior':'oneDirection','fromCardinality':'many','toCardinality':'one'})
model={'name':'RetailIntelligence','compatibilityLevel':1567,'model':{'culture':'en-GB','defaultPowerBIDataSourceVersion':'powerBI_V3','sourceQueryCulture':'en-GB','dataAccessOptions':{'legacyRedirects':True,'returnErrorValuesAsNull':True},'expressions':[{'name':'SourceFolder','kind':'m','expression':'"C:\\RetailIntelligence\\data\\model" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}],'tables':tables,'relationships':rels,'annotations':[{'name':'__PBI_TimeIntelligenceEnabled','value':'0'}]}}
write(MODEL/'model.bim',model)
write(MODEL/'definition.pbism',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{}})
write(PBI/'RetailIntelligence.pbip',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json','version':'1.0','artifacts':[{'report':{'path':'RetailIntelligence.Report'}}],'settings':{'enableAutoRecovery':True}})
write(REPORT/'definition.pbir',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../RetailIntelligence.SemanticModel'}}})
write(REPORT/'definition/report.json',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/2.0.0/schema.json','themeCollection':{}})
write(PBI/'RetailTheme.json',{'name':'Retail Intelligence','dataColors':['#167D8D','#4275B5','#E6A23C','#C86464','#7C70A8','#65A990'],'background':'#F4F6FA','foreground':'#17243B','tableAccent':'#167D8D'})

def field(table,column,measure=False):return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':column}}
def proj(table,column,is_measure=False):return {'field':field(table,column,is_measure),'queryRef':table+'.'+column,'nativeQueryRef':column}
def lit(value):return {'expr':{'Literal':{'Value':value}}}
pages=[];visual_count=0
# Built-in visuals only. Query roles use explicit semantic model references.
def page(name,title):
 pages.append(name);p=REPORT/'definition/pages'/name
 write(p/'page.json',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json','name':name,'displayName':title,'displayOption':'FitToPage','height':800,'width':1440})
 return p
def visual(p,name,kind,title,x,y,w,h,roles):
 global visual_count
 visual_count+=1
 q={role:{'projections':[proj(*v) for v in vals]} for role,vals in roles.items()}
 v={'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.0.0/schema.json','name':name,'position':{'x':x,'y':y,'width':w,'height':h,'z':visual_count,'tabOrder':visual_count},'visual':{'visualType':kind,'query':{'queryState':q},'visualContainerObjects':{'title':[{'properties':{'show':lit('true'),'text':lit("'"+title.replace("'","''")+"'"),'fontSize':lit('14D')}}]}}}
 write(p/'visuals'/name/'visual.json',v)
def card(p,i,title,m,x):visual(p,'kpi'+str(i),'card',title,x,15,325,115,{'Values':[('Metrics',m,True)]})
p=page('Executive','01 Revenue overview')
for i,(title,m) in enumerate([('Gross revenue GBP','Gross Revenue'),('Net revenue GBP','Net Revenue'),('Cancellation value rate','Cancellation Value Rate'),('Positive invoices','Positive Orders')]):card(p,i,title,m,20+i*350)
visual(p,'monthtrend','lineChart','Net revenue by month (December 2011 is partial)',20,150,890,350,{'Category':[('DimDate','YearMonth')],'Y':[('Metrics','Net Revenue',True)]})
visual(p,'countryrevenue','barChart','Revenue by country',930,150,480,350,{'Category':[('DimCountry','Country')],'Y':[('Metrics','Net Revenue',True)]})
visual(p,'countryslicer','slicer','Country',20,530,420,235,{'Values':[('DimCountry','Country')]})
visual(p,'monthslicer','slicer','Month',460,530,450,235,{'Values':[('DimDate','YearMonth')]})
visual(p,'reconciliation','card','Revenue reconciliation (must be zero)',930,530,480,235,{'Values':[('Metrics','Revenue Reconciliation',True)]})
p=page('Customer','02 Customers and cohorts')
for i,(title,m) in enumerate([('Known purchasing customers','Known Customers'),('Repeat buyer share','Repeat Buyer Share'),('Month 1 cohort retention','Month 1 Retention %'),('Anonymous revenue share','Anonymous Revenue Share')]):card(p,i,title,m,20+i*350)
visual(p,'segments','barChart','End-of-data customer segments',20,150,630,310,{'Category':[('DimCustomer','Segment')],'Y':[('Metrics','Known Customers',True)]})
visual(p,'cohortmatrix','pivotTable','Complete-month cohorts: all countries, known customers',670,150,740,610,{'Rows':[('FactCohort','CohortMonth')],'Columns':[('FactCohort','AgeMonth')],'Values':[('Metrics','Cohort Retention %',True)]})
visual(p,'customersegment','slicer','Customer snapshot segment (does not filter cohort matrix)',20,490,630,270,{'Values':[('DimCustomer','Segment')]})
p=page('Products','03 Products and cancellations')
for i,(title,m) in enumerate([('Cancellation value GBP','Cancellation Value'),('Cancelled units','Cancelled Units'),('Gross order value GBP','Average Order Value'),('Cancelled invoices','Cancelled Invoices')]):card(p,i,title,m,20+i*350)
visual(p,'topproducts','barChart','Top 10 product descriptions by net revenue',20,150,850,600,{'Category':[('DimProduct','Description')],'Y':[('Metrics','Top 10 Product Revenue',True)]})
visual(p,'producttable','tableEx','Product value and cancellation analysis',890,150,520,420,{'Values':[('DimProduct','Description'),('Metrics','Net Revenue',True),('Metrics','Cancellation Value',True),('Metrics','Cancellation Value Rate',True)]})
visual(p,'productcountry','slicer','Country',890,590,520,160,{'Values':[('DimCountry','Country')]})
p=page('Forecast','04 Forecast and cost scenario')
for i,(title,m) in enumerate([('Model backtest MAE GBP','Forecast MAE'),('Lag-7 baseline MAE GBP','Baseline MAE'),('Improvement vs baseline','Forecast Improvement %'),('Hypothetical contribution GBP','Scenario Contribution')]):card(p,i,title,m,20+i*350)
visual(p,'forecastline','lineChart','28-day test and recursive scenario (historical 2011 origin)',20,150,1000,420,{'Category':[('DimDate','Date')],'Y':[('Metrics','Backtest Actual',True),('Metrics','Backtest Forecast',True),('Metrics','Future Scenario Forecast',True)]})
visual(p,'costslider','slicer','Assumed variable cost ratio (no observed costs in source)',1040,150,370,420,{'Values':[('CostScenario','CostRatio')]})
visual(p,'forecasttable','tableEx','Backtest errors and scenario assumptions',20,590,1390,165,{'Values':[('Metrics','Selected Cost Ratio',True),('Metrics','Scenario Contribution Rate',True),('Metrics','Forecast Improvement %',True)]})
write(REPORT/'definition/pages/pages.json',{'$schema':'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':pages,'activePageName':pages[0]})
(ROOT/'docs/MEASURES.dax').write_text('\n\n'.join('// '+m['displayFolder']+'\n'+m['name']+' =\n'+m['expression'] for m in measures)+'\n')
print(f'Generated {len(tables)} tables, {len(rels)} relationships, {len(measures)} measures, {len(pages)} pages, {visual_count} visuals')
