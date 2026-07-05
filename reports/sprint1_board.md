# Sprint 1 Board — Data Foundation
## Done
- [x] D01 — Project scaffolding, requirements.txt, .env
- [x] D02 — excel_loader.py, normalize.py, 40 unit tests passing
- [x] D03 — validator.py (16 DQ rules), validation_failures.csv reviewed w/ team lead
- [x] D04 — db/schema.sql (10 tables + FKs), db/loader.py
- [x] D05 — Full load of 12 files, nifty100.db + load_audit.csv generated
- [x] D06 — Manual review of 5 companies, 1 source-file fix applied, reload confirmed clean
- [x] D07 — 10 exploratory SQL queries, this board
## Carried Over to Sprint 2
- [ ] Backfill remaining companies with sparse stock_prices coverage (see Q6)
- [ ] Decide tolerance policy for DQ-09/10/11/12 with team lead (>1% but <3% cases)
- [ ] Investigate EPS unit inconsistency pattern found in D06 across more companies
## Metrics at Sprint Close
- Companies loaded: 100 / 100
- Core files loaded: 6 / 6
- Supplementary files loaded: 4 / 5 (bulk directory used as lookup only, not a table)
- Overall reject rate across all files: see Q10 output
- Unit test coverage (src/etl/normalize.py): 100%