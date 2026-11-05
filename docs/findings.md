# Where the bullwhip actually cracks

A replication and extension of Cachon, Randall and Schmidt (2007) on US Census retail, wholesale and manufacturing data, 1992 to 2026.

## The question

Supply chain textbooks teach the bullwhip effect: each step upstream orders more erratically than its customers buy, so a small wobble at the checkout becomes a large swing at the factory. Cachon, Randall and Schmidt (CRS) tested this on 1992 to 2004 Census data and mostly did not find it. Retailers smoothed, wholesalers amplified, manufacturers were mixed. This project asks three things. Does their result hold on today's data, extended through 2025? Does it survive the measurement choices an analyst has to make? And what did the 2008, 2020 and 2021 to 2023 shocks do to it?

## The answer

The CRS pattern holds, and it is stable as long as the seasonal pattern stays in the data. Most wholesale industries amplify in 87 of 96 measurement specifications. Most retail industries amplify in 0 of 96. Remove seasonality, by seasonal adjustment or by year-over-year comparison, and every tier looks like a bullwhip. The manufacturing verdict also depends on a gross-margin assumption that public data no longer pin down.

## Data

112 monthly series from the US Census Bureau (Monthly Retail Trade, Monthly Wholesale Trade, and the M3 manufacturers' survey), pulled keyless from FRED and pinned by sha256 in `data/manifest.json`. The panel has 44 non-overlapping industries: 6 retail, 18 merchant wholesale and 20 manufacturing. CRS had 74. FRED carries sales but not inventories for several store types on their own (electronics and appliance stores appear only combined with furniture stores), and overlapping aggregates are left out so no industry is counted twice.

## Method

Following CRS: production (material inflow) = sales + this month's inventory − last month's inventory. The amplification ratio is the variance of production over the variance of demand, after logging and first-differencing both, with no seasonal adjustment. A ratio above 1 means the industry passes on more volatility than it receives. Demand is sales, or new orders where the M3 survey publishes them. Each headline ratio carries a 95% moving-block bootstrap interval (12-month blocks, 2,000 draws), so serial correlation does not overstate precision.

CRS made two adjustments this project cannot reproduce exactly. Sales are at selling price but inventories are at cost, so CRS scaled sales by monthly Census gross margins, which are no longer published in a keyless form. They also deflated by BEA price indexes. Both became grid dimensions instead of fixed choices. The full grid runs every industry under 3 time windows, 4 gross margins (0, 15, 30 and 45 percent), with and without a CPI or PPI deflator, 3 detrending transforms, monthly or quarterly data, and with or without seasonal adjustment: 11,016 industry-level cells. 18 cells are undefined because clothing stores' production went negative in April 2020: store closures drew inventory down by more than the month's cost-adjusted sales.

## Findings

**1. The replication holds in direction.** Share of industries with a ratio above 1, 1993 to 2004, no margin or price adjustment:

| Tier | CRS 2007, unadjusted | This data, unadjusted | CRS 2007, seasonally adjusted | This data, seasonally adjusted |
|---|---|---|---|---|
| Retail | 14% | 17% | 100% | 67% |
| Wholesale | 84% | 72% | 95% | 100% |
| Manufacturing | 38% | 10% | 70% | 70% |

Across the margin and deflator settings, the unadjusted shares range from 17% to 33% for retail, 72% to 94% for wholesale, and 10% to 45% for manufacturing. The CRS wholesale figure sits inside our band. Our manufacturing share is below theirs at every margin except the highest one tried.

**2. Seasonality is the choice that decides the answer.** With seasonality kept, 31% of retail cells, 72% of wholesale cells and 41% of manufacturing cells amplify. With it removed, those become 83%, 96% and 75%. Physical flows have to follow the real calendar, so the unadjusted numbers describe what warehouses and plants actually absorb. A year-over-year chart of orders against sales will show a bullwhip that the physical flows do not have.

<!-- fig:split -->

**3. Seasonal industries smooth.** Across the 44 industries, the share of demand variance explained by the calendar month correlates with the log amplification ratio at Spearman ρ = -0.66 (p < 0.001). This is CRS hypothesis 1. The likely mechanism, theirs too, is that predictable peaks get built ahead of time, which flattens inflow relative to sales.

<!-- fig:season -->

**4. The aggregate tiers.** 1993 to 2025, unadjusted: retail 0.56 (95% interval 0.53 to 0.60), wholesale 1.04 (0.99 to 1.09), manufacturing 0.66 (0.63 to 0.69). Aggregate wholesale cannot be told apart from 1, even though most wholesale industries amplify. Adding industries together cancels part of their individual swings.

<!-- fig:industries -->

**5. Since 2005 the tiers have converged toward 1.** Median industry ratio, 1993 to 2004 against 2005 to 2025: retail 0.68 to 0.88, wholesale 1.05 to 0.98, manufacturing 0.80 to 0.95. Retail smoothing weakened most after 2020: the 60-month aggregate retail ratio was 0.59 at the end of 2019 and peaked at 0.78 afterwards.

<!-- fig:rolling -->

**6. In the shocks, retail absorbed the most inventory swing.** Trough-to-peak swing in the seasonally adjusted inventory-to-sales ratio, as a share of the prior year's average:

| Tier | 2008-09 | 2020-21 | 2021-23 |
|---|---|---|---|
| Retail | 17% | 40% | 17% |
| Wholesale | 23% | 33% | 14% |
| Manufacturing | 21% | 28% | 9% |
| Computers and electronics mfg | 18% | 8% | 25% |

In COVID the largest swing was at the store end of the chain, the reverse of a classic bullwhip. In the chip shortage and restock, computers and electronics manufacturers built inventory to 2.27 months of shipments by March 2023.

**7. Two chains up close.** Motor vehicle dealers are the one retail industry that amplifies: 1.53 in 1993 to 2004 and 1.26 since. CRS found the same and explained it by manufacturers pushing inventory onto dealers. For computers and electronics manufacturing since 2005, new-orders variance is 5.9 times production variance (ratio 0.17). The whip is real in that industry's order book, but it does not reach production. Transportation equipment shows the same gap (ratio 0.28 against orders).

## What a planner should take from this

1. Measure amplification on unadjusted data at the level where inventory actually sits. Seasonally adjusted or year-over-year views overstate it.
2. Inventory buffers work. Most retail and manufacturing industries absorb volatility, and wholesale is where it gets added back.
3. Read the order book with care. In durable goods the largest swings are in new orders, not production, so order volatility overstates what plants will actually build and ship.

## Limitations

- **Margins.** Census no longer publishes keyless monthly gross margins, so margin is a grid dimension. The manufacturing share of amplifying cells moves by 18% across the four margins.
- **Deflators.** CPI for retail and the all-commodities PPI elsewhere are crude next to the industry-matched BEA deflators CRS used.
- **Sales as a stand-in for demand.** Where customers can backorder, sales understate demand volatility, which biases ratios upward (CRS make the same point).
- **Coverage and vintage.** 44 industries instead of 74. The 1993 to 2004 numbers come from today's vintage of the data, not the one CRS downloaded, so revisions can explain part of any gap.
- **Chains are not closed.** Imports, exports and business buyers enter and leave between the retail, wholesale and manufacturing links.

## Sources

- Cachon, G. P., Randall, T., and Schmidt, G. M. (2007). In Search of the Bullwhip Effect. *Manufacturing & Service Operations Management* 9(4), 457 to 479. https://doi.org/10.1287/msom.1060.0149 (method and Table 1 shares read from the University of Pennsylvania repository copy, https://repository.upenn.edu/oid_papers/137).
- US Census Bureau Monthly Retail Trade, Monthly Wholesale Trade and M3 surveys, via FRED (https://fred.stlouisfed.org). Every series ID and title is in `data/registry.csv`.

## Reproduce

`make all` rebuilds everything from the cached raw files. `make refresh` downloads the current vintage. `make gate` runs lint, tests, the independent reconcile and this memo's number check.
