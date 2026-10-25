# Model architecture and metric contract

## Pipeline

`UCI workbook → validated pandas transformation → CSV star schema → SQL marts → Power Query imports → DAX measures → PBIR report`

| Table | Grain | Relationship |
| --- | --- | --- |
| FactTransactions | One retained source transaction line | Many-to-one to Date, Country, Product, Customer |
| DimDate | One calendar day, including scenario horizon | Single-direction filters to transactions and forecast |
| DimCountry | One observed country | Single-direction filter to transactions |
| DimProduct | One stock code, latest non-null description | Single-direction filter to transactions |
| DimCustomer | One observed customer key, including anonymous 0 | Single-direction filter to transactions |
| FactCohort | First-purchase month and eligible age-month | Disconnected aggregate, all countries |
| FactForecast | Day within backtest or scenario horizon | Many-to-one to DimDate |
| CostScenario | Assumed cost ratios from 30% to 90%, steps of 5 points | Disconnected what-if selector |
| Metrics | One hidden placeholder row | Measure container |

No bidirectional or many-to-many relationships are required. FactCohort is intentionally disconnected because transaction-level filters cannot be applied correctly to a pre-aggregated global cohort without rebuilding its eligible denominators. Native page titles expose this behaviour. Forecast is global and also ignores product/customer/country selections.

## Cleaning and accounting

- Keep source row numbers as stable line identifiers. Preserve 5,268 identical-looking source rows because a repeated feature combination does not prove a duplicate transaction.
- Exclude 2,517 rows under the rule in `build_data.py`. The exclusion audit shows counts by reason. Unknown customer IDs do not remove revenue.
- Round each quantity × unit-price line to pence using decimal half-up rounding. Store money as signed integers and convert to GBP only in measures.
- Gross value uses positive line values; cancellation value uses absolute negative values. Every row satisfies `gross − cancellation = net`.
- Positive invoices are distinct invoice numbers with positive quantity. AOV uses gross value divided by positive invoices; cancellation invoice IDs are separate.
- Purchasing customers require an identified customer and a positive line. Identified keys with only negative lines do not enter that denominator.
- Descriptions may change across time. The product dimension uses the last non-null observed description for each stock code; some codes represent postage or adjustments.

## Customer analysis

Segments are a **fixed snapshot at the end of the extract**, not recalculated historical RFM: frequent recent means recency ≤30 days and ≥5 positive invoice IDs; inactive means recency >90 days; remaining identified buyers form a third segment. Recency references the day after the last transaction. Unknown and negative-only customer keys have separate labels.

Cohorts use the first observed positive purchase, not true lifetime acquisition. Cohort membership and active-month counts exclude anonymous customers. Only complete months through November 2011 enter the cohort table. Missing future exposure months are omitted, not filled with zero. Month-1 retention weights by eligible cohort size. The retention matrix intentionally blanks totals across incompatible age/month cells.

## Forecast protocol

Daily **gross** revenue is reindexed to a continuous calendar; dates without retained positive sales have zero. The final extract day is excluded because the snapshot ends before midnight. Features use lag 1/7/14/28, a shifted seven-day mean, weekday trigonometry and a time trend. No current target or contemporaneous unavailable feature enters the model.

Chronological split: initial 289 usable days for training, 28 validation days for Ridge alpha selection, then 28 untouched test days. The model stays frozen during test evaluation. One-step-ahead testing uses the previous day's observed outcome; it is not a multi-day forecast from one origin. After reporting the fixed test result, a final model fits all observed usable days and generates a separate 28-day **recursive historical scenario**. Its future errors are unknown. No confidence band is claimed.

## Hypothetical contribution

`Net Revenue × (1 − selected assumed variable-cost ratio)` is a sensitivity calculation. The default ratio is 60%; changing the disconnected selector updates the measure. Neither the ratio nor the resulting contribution is an observed margin or profit. No taxes, acquisition costs, overheads or cancellation matching are available.

