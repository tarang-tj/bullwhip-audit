# Method notes

## Source of the method

Cachon, Randall and Schmidt (2007), *In Search of the Bullwhip Effect*, MSOM 9(4) 457-479, read from the University of Pennsylvania repository copy (https://repository.upenn.edu/oid_papers/137) on 2026-11-05. Taken from the text:

- Production: Y_t = S_t + (I_t - I_{t-1}), with S sales and I inventory (p.6).
- Sales are multiplied by (1 - margin) so they share the cost units of inventory. Monthly retail and wholesale margins came from Census, and manufacturing margins from the 1997 Economic Census (p.6).
- Sales and inventories are deflated by BEA implicit price deflators (p.6).
- Series are logged and first-differenced, with no seasonal adjustment (p.7-8).
- Amplification ratio = V[production] / V[demand] (eq. 1). Demand is sales, or new orders for durable manufacturers that report them.
- Seasonal adjustment, when used, is the residual from regressing the differenced series on month dummies (p.13).
- Predictable seasonality ratio = (V[demand] - V[SA demand]) / V[demand] (eq. 2).
- Brown-Forsythe test for equal variances.
- Headline shares (p.13): 86% of retail ratios are below 1; 84% of wholesale and 38% of manufacturing are above 1. With seasonal adjustment, all retail, 95% of wholesale and 70% of manufacturing are above 1. Motor vehicle dealers are the only retail category that amplifies (footnote 10).

## Departures, and why

| CRS | Here | Reason |
|---|---|---|
| Monthly Census margins | Margin as a grid dimension: 0, 15, 30, 45% | No keyless margin table found on the Census ARTS or AWTS pages (checked 2026-11-05) |
| BEA deflators matched by industry | CPI (retail) and PPI all commodities (wholesale, manufacturing), on and off | BEA API needs a key; FRED CPIAUCNS and PPIACO are keyless |
| 74 industries | 44 | FRED lacks several retail inventory series (443, 446, 4413 probed and missing); overlapping aggregates (44000, 4400A, 4521E) dropped |
| Data through 2004 | Through 2025-12 (latest full year) | Extension |
| Brown-Forsythe p-value | Same, plus a 12-month moving-block bootstrap interval | Monthly growth rates are serially correlated, and a test that treats them as independent overstates precision |

## Edge cases

- **Undefined cells.** Clothing stores (448) in April 2020: under 30 and 45% margins, imputed production is negative and cannot be logged. Those cells are recorded as undefined, never patched. They affect only windows that include 2020.
- **Windows.** Levels are cut at the window end before transforming. Months before the window start stay in, so the first difference has a lag.
- **Quarterly.** Monthly flows are summed to complete calendar quarters only.

## Series probe (2026-11-05)

Wholesale `S{naics}SM144NCEN` / `I{naics}IM144NCEN`. Retail `MRTSSM{naics}USN` / `MRTSIM{naics}USN`. Manufacturing M3 NSA `U{code}VS` (shipments), `U{code}TI` (total inventories), `U{code}NO` (new orders, published for 31S to 37S). Each of these returned at least 398 monthly rows starting 1992-01. The full list with titles is in `data/registry.csv`.
