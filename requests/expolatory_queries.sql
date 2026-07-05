-- ==========================================================
-- exploratory_queries.sql
-- Sprint 1 – Data Foundation | Nifty 100 ETL Pipeline
-- ==========================================================

-- ==========================================================
-- Q1. Row count for all major tables
-- ==========================================================
SELECT 'companies' AS table_name, COUNT(*) AS row_count FROM companies
UNION ALL
SELECT 'profit_and_loss', COUNT(*) FROM profit_and_loss
UNION ALL
SELECT 'balance_sheet', COUNT(*) FROM balance_sheet
UNION ALL
SELECT 'cash_flow', COUNT(*) FROM cash_flow
UNION ALL
SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'sector_mapping', COUNT(*) FROM sector_mapping
UNION ALL
SELECT 'index_history', COUNT(*) FROM index_history
UNION ALL
SELECT 'corporate_actions', COUNT(*) FROM corporate_actions
UNION ALL
SELECT 'shareholding_pattern', COUNT(*) FROM shareholding_pattern;

-- ==========================================================
-- Q2. Companies with no Profit & Loss data
-- ==========================================================
SELECT
    c.id,
    c.company_name
FROM companies c
LEFT JOIN profit_and_loss p
    ON c.id = p.company_id
WHERE p.company_id IS NULL;

-- ==========================================================
-- Q3. Year coverage per company (Profit & Loss)
-- ==========================================================
SELECT
    company_id,
    COUNT(*) AS years_present,
    MIN(year) AS earliest_year,
    MAX(year) AS latest_year
FROM profit_and_loss
GROUP BY company_id
ORDER BY years_present ASC
LIMIT 20;

-- ==========================================================
-- Q4. Null audit – Profit & Loss
-- ==========================================================
SELECT
    SUM(CASE WHEN sales IS NULL THEN 1 ELSE 0 END) AS null_sales,
    SUM(CASE WHEN net_profit IS NULL THEN 1 ELSE 0 END) AS null_net_profit,
    SUM(CASE WHEN eps IS NULL THEN 1 ELSE 0 END) AS null_eps,
    SUM(CASE WHEN dividend_payout IS NULL THEN 1 ELSE 0 END) AS null_dividend_payout,
    COUNT(*) AS total_rows
FROM profit_and_loss;

-- ==========================================================
-- Q5. Null audit – Balance Sheet
-- ==========================================================
SELECT
    SUM(CASE WHEN total_assets IS NULL THEN 1 ELSE 0 END) AS null_total_assets,
    SUM(CASE WHEN cwip IS NULL THEN 1 ELSE 0 END) AS null_cwip,
    SUM(CASE WHEN investments IS NULL THEN 1 ELSE 0 END) AS null_investments,
    COUNT(*) AS total_rows
FROM balance_sheet;

-- ==========================================================
-- Q6. Companies missing stock price data
-- ==========================================================
SELECT
    c.id,
    c.company_name
FROM companies c
LEFT JOIN stock_prices sp
    ON c.id = sp.company_id
WHERE sp.company_id IS NULL;

-- ==========================================================
-- Q7. Balance Sheet imbalance check
-- ==========================================================
SELECT
    company_id,
    year,
    total_assets,
    total_liabilities,
    ROUND(ABS(total_assets - total_liabilities), 2) AS imbalance
FROM balance_sheet
WHERE ABS(total_assets - total_liabilities) >
      (0.01 * ABS(total_assets))
ORDER BY imbalance DESC
LIMIT 15;

-- ==========================================================
-- Q8. Companies with most complete data
-- ==========================================================
SELECT
    c.id,
    c.company_name,

    (SELECT COUNT(*)
     FROM profit_and_loss
     WHERE company_id = c.id) AS pnl_years,

    (SELECT COUNT(*)
     FROM balance_sheet
     WHERE company_id = c.id) AS bs_years,

    (SELECT COUNT(*)
     FROM cash_flow
     WHERE company_id = c.id) AS cf_years,

    (SELECT COUNT(*)
     FROM stock_prices
     WHERE company_id = c.id) AS price_rows

FROM companies c
ORDER BY
    pnl_years DESC,
    bs_years DESC,
    cf_years DESC,
    price_rows DESC
LIMIT 10;

-- ==========================================================
-- Q9. Average ROE / ROCE by sector
-- ==========================================================
SELECT
    s.sector,
    ROUND(AVG(c.roe_percentage), 2) AS avg_roe,
    ROUND(AVG(c.roce_percentage), 2) AS avg_roce,
    COUNT(*) AS n_companies
FROM companies c
JOIN sector_mapping s
    ON c.id = s.company_id
GROUP BY s.sector
ORDER BY avg_roe DESC;

-- ==========================================================
-- Q10. Load audit summary
-- ==========================================================
SELECT
    file_name,
    SUM(rows_attempted) AS total_attempted,
    SUM(rows_loaded) AS total_loaded,
    SUM(rows_rejected) AS total_rejected,
    ROUND(
        100.0 * SUM(rows_rejected) / SUM(rows_attempted),
        2
    ) AS reject_pct
FROM load_audit
GROUP BY file_name
ORDER BY reject_pct DESC;

-- ==========================================================
-- END OF FILE
-- ==========================================================