# Data provenance

Chen, D. (2015). Online Retail [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5BW33.

- Official dataset: https://archive.ics.uci.edu/dataset/352/online+retail
- Download: https://archive.ics.uci.edu/static/public/352/online+retail.zip
- Licence stated by UCI: Creative Commons Attribution 4.0 International, https://creativecommons.org/licenses/by/4.0/
- Acquired: 25 October 2026.
- Extracted member: `Online Retail.xlsx`.
- SHA-256: `43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d`.

The original workbook records transactions from a UK online retailer in 2010–2011. The pipeline preserves original bytes on download, then creates adapted tables and aggregate reports. Currency is GBP. Revenue is derived from quantity multiplied by unit price; it is not a financial statement revenue figure. Generated model CSVs are excluded from git.

The source page's missing-value summary does not match observed cells: the inspected workbook contains 135,080 missing customer IDs and 1,454 missing descriptions. The project uses observed workbook values when defining its cleaning policy.

Changes: exclude non-positive unit prices and zero quantities; reject positive-quantity credit-note lines; map unknown customers to key 0; generate integer surrogate keys; retain repeated-looking lines; round line values to pence with Decimal ROUND_HALF_UP; build calendar, customer and product dimensions; calculate customer segments and cohort aggregates; construct a chronological forecast experiment.

Derived figures and charts retain this attribution. No source claim supports costs, profit, acquisition spend, current business performance or claimed savings.
