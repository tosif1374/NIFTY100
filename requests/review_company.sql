SELECT 'profit_and_loss' AS source, year, sales, net_profit, eps
FROM profit_and_loss WHERE company_id = :cid
UNION ALL
SELECT 'balance_sheet', year, total_assets, total_liabilities, NULL
FROM balance_sheet WHERE company_id = :cid
UNION ALL
SELECT 'cash_flow', year, operating_activity, net_cash_flow, NULL
FROM cash_flow WHERE company_id = :cid
ORDER BY source, year;
