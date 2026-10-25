# Verification record

Executed in Python 3.12 on 25 October 2026:

- Original source workbook read successfully; source SHA-256 and 541,909 rows recorded.
- Transformation produced 539,392 retained lines with explicit exclusions.
- Revenue reconciled at integer-pence line grain and after SQL aggregation.
- Eight tests passed: row accounting, currency, dimension keys, purchasing-customer denominator, cohort censoring, SQL totals, chronological forecast benchmark and model/visual references.
- Thirty-nine native project/report metadata files validated against Microsoft's official public JSON schemas. Microsoft's declared canonical schema IDs are resolved to already-downloaded, unchanged official documents when their IDs differ from the retrieval URL.
- Four design previews rendered from calculated outputs; they are not screenshots from Desktop.

Not executed: Power BI Desktop opening, native DAX engine, Power Query refresh, native visual bindings/rendering, Power BI Service publishing or access-control enforcement. The TMSL model is structurally inspected by the project tests; it has not been loaded by an Analysis Services engine. Native acceptance checks and expected DAX query values are supplied for the next verification stage.

Dependency versions are pinned. Source download, generation and verification scripts are included; raw workbook/model CSVs and local schema cache are not committed. A GitHub workflow reruns data preparation and Python checks when project source changes. Workflow success establishes pipeline checks, not Desktop verification.
