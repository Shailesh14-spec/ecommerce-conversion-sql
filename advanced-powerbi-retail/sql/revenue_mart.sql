-- Fact grain: one retained source transaction line; money stored as signed pence.
WITH monthly AS (
 SELECT d.YearMonth,d.MonthSort,d.IsCompleteMonth,
 SUM(f.GrossRevenueCents) AS GrossRevenueCents,
 SUM(f.CancellationValueCents) AS CancellationValueCents,
 SUM(f.NetRevenueCents) AS NetRevenueCents,
 COUNT(DISTINCT CASE WHEN f.Quantity>0 THEN f.InvoiceNo END) AS PositiveOrders
 FROM FactTransactions f JOIN DimDate d ON f.DateKey=d.DateKey
 GROUP BY d.YearMonth,d.MonthSort,d.IsCompleteMonth
)
SELECT *,NetRevenueCents-LAG(NetRevenueCents) OVER (ORDER BY MonthSort) AS MoMChangeCents
FROM monthly ORDER BY MonthSort;
