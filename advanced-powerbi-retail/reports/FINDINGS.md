# Findings and decisions

The retained transaction lines yield £10,666,684.54 of positive value and £896,812.49 of negative value, reconciling to £9,769,872.05 of net line revenue. Cancellation value is about 8.4% of positive line value, but negative lines can be credits or corrections; a physical-return rate cannot be inferred.

Missing customer IDs are substantial: 135,080 original rows lack an identifier. Keep anonymous revenue in the executive report while excluding it from customer retention denominators. There are 4,338 identified purchasing customers under the eligibility policy. There are another 33 identified keys with no retained positive purchase; these do not count as purchasing customers.

November 2011 has the highest observed monthly net line revenue. December 2011 is partial and must not be compared as a full month. The dataset provides little year-over-year coverage, so broad YoY growth claims would be weak.

Customer cohorts support active-in-month retention, not continuous survival or true lifetime acquisition. Complete-month cohorts end in November 2011. Some apparently inactive customers can return later; do not label snapshot recency segments as confirmed churn.

The trained forecast is not selected for operational use. Holdout MAE is £12,286.93/day versus £11,119.16/day for lag-7: a 10.5% deterioration. Keep the baseline and investigate trading-day effects, holiday demand and large wholesale orders before further modelling. Recursive scenario values beyond the observation boundary have no observed accuracy measurement.

The cost-ratio control is purely hypothetical. At an assumed 60% variable-cost ratio, contribution is £3,907,948.82. This is neither observed profit nor evidence of an efficiency gain. A real margin report needs product costs, fulfilment costs, tax definitions and properly matched cancellations.
