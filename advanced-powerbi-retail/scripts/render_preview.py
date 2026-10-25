"""Render actual analytical outputs as clearly labelled dashboard design previews."""
from pathlib import Path
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'reports';D=ROOT/'data/model'
m=json.loads((R/'metrics.json').read_text());monthly=pd.read_csv(R/'monthly_revenue.csv');fact=pd.read_csv(D/'FactTransactions.csv');country=pd.read_csv(D/'DimCountry.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#CDD5E1','text.color':'#17243B','axes.labelcolor':'#536279','xtick.color':'#536279','ytick.color':'#536279','axes.titleweight':'bold','axes.titlesize':13})
TEAL='#167D8D';BLUE='#4275B5';RED='#C86464';BG='#F3F5F9'
def canvas(title,subtitle):
 fig=plt.figure(figsize=(16,9),facecolor=BG)
 fig.text(.04,.945,title,fontsize=25,weight='bold');fig.text(.04,.907,subtitle,fontsize=11,color='#536279')
 fig.text(.04,.022,'UCI Online Retail · Historical 2010–2011 data · Python-rendered design preview, not a Power BI screenshot',fontsize=9,color='#68788F')
 return fig
def panel(fig,rect,title):
 ax=fig.add_axes(rect,facecolor='white');ax.set_title(title,loc='left',pad=18);ax.grid(axis='y',color='#E8ECF2',zorder=0);ax.set_axisbelow(True);return ax
def cards(fig,items):
 for i,(label,value,note) in enumerate(items):
  ax=fig.add_axes([.04+i*.235,.725,.22,.14],facecolor='white');ax.set_xticks([]);ax.set_yticks([])
  for sp in ax.spines.values():sp.set_visible(False)
  ax.text(.07,.76,label,fontsize=11,color='#536279');ax.text(.07,.36,value,fontsize=25,weight='bold',color=TEAL);ax.text(.07,.12,note,fontsize=9,color='#68788F')
fig=canvas('Retail Intelligence','Revenue overview | Line eligibility and rounding policy documented in the project')
cards(fig,[('Net line revenue',f"£{m['net_revenue_gbp']/1e6:.2f}m",'positive less negative eligible lines'),('Gross line revenue',f"£{m['gross_revenue_gbp']/1e6:.2f}m",'positive eligible lines'),('Cancellation value',f"£{m['cancellation_value_gbp']/1e3:.0f}k",'negative eligible lines, absolute value'),('Positive invoices',f"{m['positive_invoices']:,}",'distinct invoice identifiers')])
a=panel(fig,[.065,.18,.535,.46],'Monthly net revenue (£ thousands)');x=np.arange(len(monthly));colors=[TEAL if v else '#C3CDDA' for v in monthly.IsCompleteMonth];a.bar(x,monthly.NetRevenueCents/1e5,color=colors);a.set_xticks(x);a.set_xticklabels(monthly.YearMonth,rotation=45,ha='right',fontsize=9);a.text(.01,.96,'December 2011 is partial',transform=a.transAxes,va='top',color='#536279')
c=fact.groupby('CountryKey').NetRevenueCents.sum().reset_index().merge(country,on='CountryKey').sort_values('NetRevenueCents',ascending=False);c=c.loc[c.Country!='United Kingdom'].head(7).iloc[::-1]
a=panel(fig,[.68,.18,.265,.46],'Largest markets excluding the UK');a.barh(c.Country,c.NetRevenueCents/1e5,color=BLUE);a.set_xlabel('Net line revenue (£ thousands)');a.grid(False)
fig.savefig(R/'dashboard-preview.png',dpi=120);fig.savefig(R/'dashboard-preview.svg');plt.close(fig)
fig=canvas('Customer Retention','Known customers only | Cohorts use complete months and active-in-month retention')
cohort=pd.read_csv(R/'cohort_retention.csv');pivot=cohort.assign(Retention=cohort.ActiveCustomers/cohort.CohortCustomers).pivot(index='CohortMonth',columns='AgeMonth',values='Retention')
a=fig.add_axes([.10,.14,.55,.68],facecolor='white');im=a.imshow(pivot,aspect='auto',vmin=0,vmax=1,cmap='GnBu');a.set_yticks(range(len(pivot)));a.set_yticklabels(pivot.index);a.set_xticks(range(len(pivot.columns)));a.set_xticklabels(pivot.columns);a.set_xlabel('Months since first observed purchase');a.set_title('Eligible cohort retention (future months blank)',loc='left',pad=16)
for i in range(len(pivot)):
 for j in range(len(pivot.columns)):
  v=pivot.iloc[i,j]
  if pd.notna(v):a.text(j,i,f'{v:.0%}',ha='center',va='center',fontsize=8,color='white' if v>.65 else '#17243B')
seg=pd.read_csv(R/'customer_segments.csv');a=panel(fig,[.75,.3,.2,.45],'Snapshot customer segments');a.barh(seg.Segment,seg.Customers,color=TEAL);a.tick_params(axis='y',labelsize=9);a.set_xlabel('Customer keys')
fig.savefig(R/'cohort-preview.png',dpi=120);fig.savefig(R/'cohort-preview.svg');plt.close(fig)
fig=canvas('Products and Cancellations','Cancellation value describes negative lines; it does not establish confirmed physical returns')
prod=pd.read_csv(R/'top_products.csv').iloc[::-1];a=panel(fig,[.30,.14,.61,.66],'Highest gross-value stock descriptions');a.barh(prod.Description.str.slice(0,38),prod.GrossRevenueCents/1e5,color=TEAL,label='Gross');a.barh(prod.Description.str.slice(0,38),-prod.CancellationValueCents/1e5,color=RED,label='Cancellation value');a.set_xlabel('Line value (£ thousands)');a.grid(False);a.legend()
fig.savefig(R/'product-preview.png',dpi=120);fig.savefig(R/'product-preview.svg');plt.close(fig)
fig=canvas('Forecast Evaluation and Cost Scenario','The trained model fails to beat lag-7 on the held-out period; retain the baseline for this benchmark')
bench=m['forecast'];cards(fig,[('Model MAE',f"£{bench['model_mae_gbp']:,.0f}",'28-day one-step-ahead backtest'),('Lag-7 MAE',f"£{bench['seasonal_naive_mae_gbp']:,.0f}",'lower error is better'),('Improvement',f"{bench['mae_improvement_pct']:.1f}%",'negative means model is worse'),('Assumed contribution',f"£{m['net_revenue_gbp']*.4/1e6:.2f}m",'illustration at 60% cost ratio')])
f=pd.read_csv(D/'FactForecast.csv');f['Date']=pd.to_datetime(f.DateKey.astype(str));b=f.loc[f.SeriesType=='Backtest'];a=panel(fig,[.065,.17,.56,.46],'Untouched test period: actual vs forecast');a.plot(b.Date,b.ActualGBP,color='#17243B',label='Actual');a.plot(b.Date,b.ForecastGBP,color=TEAL,label='Model');a.plot(b.Date,b.BaselineGBP,color=RED,alpha=.65,label='Lag 7');a.legend();a.tick_params(axis='x',rotation=35,labelsize=9);a.set_ylabel('Daily gross revenue GBP')
a=panel(fig,[.72,.17,.22,.46],'Hypothetical cost sensitivity');cost=np.arange(.3,.91,.05);a.plot(cost,(1-cost)*m['net_revenue_gbp']/1e6,color=BLUE);a.set(xlabel='Assumed variable cost ratio',ylabel='Illustrative contribution (£m)');a.text(.04,.93,'No observed costs or profit\nin the source dataset',transform=a.transAxes,va='top',fontsize=10)
fig.savefig(R/'forecast-preview.png',dpi=120);fig.savefig(R/'forecast-preview.svg');plt.close(fig)
print('Rendered four labelled design previews')
