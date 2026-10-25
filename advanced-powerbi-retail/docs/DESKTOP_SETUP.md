# Open and verify in Power BI Desktop

## Prerequisites

Use a recent Power BI Desktop build on Windows that supports PBIP and PBIR. This project is source-form; there is no `.pbix` or preloaded VertiPaq cache. Power BI Desktop is not a native macOS application.

1. Clone/download the repository and enter this project folder.
2. Install `requirements.txt` in a Python 3.12 virtual environment.
3. Run the download, data-build and Power BI-build scripts in README order.
4. Run `python scripts/configure_powerbi.py` **on Windows**. It writes the absolute local `data/model` folder to the Power Query `SourceFolder` parameter. Do not commit a machine-specific path.
5. Open `powerbi/RetailIntelligence.pbip`. Enable relevant project/enhanced-report options if your Desktop build requires them.
6. Refresh the import model. The imports use only the generated local CSVs; confirm file paths if prompted.
7. Optionally import `powerbi/RetailTheme.json` from View → Themes.
8. Save a local `.pbix` only after the validation steps below pass.

The source uses the documented TMSL `model.bim` semantic-model format and PBIR report definitions. JSON-schema validation checks structure; it cannot guarantee that Desktop will bind every visual role or evaluate every DAX expression identically. Resolve any surfaced Desktop errors before representing the dashboard as tested.

## Native acceptance checks

- Model view: verify five one-direction relationships; DimDate is a date table with unique Date values; scenario and cohort tables are disconnected.
- DAX Query view: run `docs/VERIFY_IN_DESKTOP.dax`. Compare values with `reports/metrics.json` under no report filters. Revenue reconciliation must be zero.
- Refresh: verify no Power Query cell errors or missing files. Date import uses an explicit culture.
- Executive page: change country and month. Transaction cards and charts must respond consistently.
- Customer page: cohort totals must remain independent of segment selection as labelled. Matrix totals should be blank. Month 0 should read 100% for each cohort.
- Product page: verify only ranked nonblank product values appear in the top-product chart and that country filtering changes the ranking.
- Scenario page: select one cost ratio and verify contribution changes. A cleared or multi-selected ratio uses the documented 60% fallback. It must never be labelled actual profit.
- Forecast page: compare MAE to the committed metrics. Negative improvement must remain visible. Country and product filters must not be presented as slicing global forecast rows.
- Inspect all four pages at normal zoom for clipped text, invalid visuals, unwanted blank categories and readable currency/percentage formats. Python previews are design references, not proof of Desktop appearance.

Publishing to Power BI Service, gateways, scheduled refresh, workspace access and row-level security are outside this source delivery and have not been configured.

## Microsoft format references

- Report folder and PBIR: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report
- Semantic-model folder, TMSL and `definition.pbism`: https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-dataset
