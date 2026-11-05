# Where the bullwhip effect shows up

A replication of Cachon, Randall and Schmidt (2007), extended through 2025 with US Census data on retailers, wholesalers and manufacturers.

## The question

Supply chain courses teach the bullwhip effect. Each step up the chain orders more erratically than its own customers buy, so a small wobble at the checkout grows into a large swing at the factory. In 2007, Cachon, Randall and Schmidt (CRS from here on) looked for it in Census industry data from 1992 to 2004 and mostly didn't find it. Retailers smoothed demand, wholesalers amplified it, and manufacturers were split.

This study asks three questions of the same data, now running through 2025. Does their result still hold? Does it survive the judgment calls an analyst makes when measuring it? And what did the 2008 recession, COVID and the chip shortage do to it?

## The short answer

Retail and wholesale behave the way CRS found, as long as the seasonal pattern stays in the data. Every industry was measured 96 different ways with seasonality left in (each way is a "specification" below). Most wholesale industries amplify in 87 of those specifications. For retail, that count is 0.

Manufacturing is the tier that changed. Over the 1993 to 2004 window CRS studied, most manufacturing industries amplify in only 7 of 32 specifications. Since 2005 they amplify in 28 of 32. That later result leans on an assumption about gross margins that public data no longer pins down, so read the margin note under Limitations before quoting it.

Seasonality matters more than any other choice. Strip it out, with seasonal adjustment or a year-over-year comparison, and most industries in every tier look like amplifiers.

## Data

The study uses 112 monthly series: 110 from the US Census Bureau (the Monthly Retail Trade survey, the Monthly Wholesale Trade survey and the M3 survey of manufacturers) and two BLS price indexes. All of them come from FRED, which needs no API key, and each downloaded file is pinned by its sha256 hash in `data/manifest.json`.

The panel has 44 industries that don't overlap: 6 retail, 18 merchant wholesale and 20 manufacturing. CRS had 74. FRED carries sales but not inventories for several store types on their own (electronics and appliance stores, for instance, appear only combined with furniture stores), and broad aggregates are left out so no industry is counted twice.

## Method

In CRS's terms, production is the material that flows into an industry in a month: its sales plus its change in inventory. The amplification ratio divides the variance of production by the variance of demand, after taking logs and month-to-month differences of both. A ratio above 1 means the industry hands its suppliers more volatility than it gets from its customers. Demand is sales, or new orders where the M3 survey publishes them.

Headline ratios come with a 95% interval from a moving-block bootstrap (12-month blocks, 2,000 draws). Resampling whole blocks keeps the correlation between neighboring months from making the estimates look more precise than they are.

Two of CRS's adjustments can't be copied exactly. Census values sales at selling price and inventory at cost, so CRS converted sales to cost with monthly Census gross margins, and those margins are no longer available without a key. CRS also deflated by BEA price indexes. This study turns both into settings and varies them. Every industry runs under 3 time windows, 4 gross margins (0, 15, 30 and 45 percent), with and without a CPI or PPI deflator, 3 detrending transforms, monthly or quarterly data, and with or without seasonal adjustment. That gives 9,504 industry-level cells measured against sales, plus 1,512 against new orders for the durable goods makers that report them. The shares below count only the sales cells.

18 cells have no answer. In April 2020, closed clothing stores drew down inventory by more than that month's cost-adjusted sales, so their production came out negative and can't be logged. Those cells are left out of every share.

## Findings

### The replication holds in direction

Share of industries with a ratio above 1, 1993 to 2004, before any margin or price adjustment:

| Tier | CRS 2007, unadjusted | This data, unadjusted | CRS 2007, seasonally adjusted | This data, seasonally adjusted |
|---|---|---|---|---|
| Retail | 14% | 17% | 100% | 67% |
| Wholesale | 84% | 72% | 95% | 100% |
| Manufacturing | 38% | 10% | 70% | 70% |

Across the margin and deflator settings, the unadjusted shares run from 17% to 33% for retail, 72% to 94% for wholesale, and 10% to 45% for manufacturing. CRS's wholesale figure falls inside that range. Our manufacturing share sits below theirs at every margin except the highest.

### Seasonality decides the answer

With seasonality kept, 31% of retail cells, 72% of wholesale cells and 51% of manufacturing cells amplify. Remove it and those shares climb to 82%, 96% and 91%.

Warehouses and plants have to live with the real calendar, so the unadjusted numbers are the ones that describe what they absorb. A year-over-year chart of orders against sales will show a bullwhip that the physical flows don't have.

<!-- fig:split -->

### Seasonal industries smooth

Across the 44 industries, the more of an industry's demand variance the calendar month explains, the lower its amplification ratio (Spearman ρ = -0.66, p < 0.001). CRS predicted this as their hypothesis 1. The likely reason, and the one they gave, is that firms build ahead of peaks they can see coming, which flattens inflow relative to sales.

<!-- fig:season -->

### The tiers in aggregate

Over 1993 to 2025, unadjusted, the aggregate ratios are 0.56 for retail (95% interval 0.53 to 0.60), 1.04 for wholesale (0.99 to 1.09) and 0.66 for manufacturing (0.63 to 0.69).

Aggregate wholesale can't be told apart from 1, even though most individual wholesale industries amplify. One possible explanation, not tested here, is that industry swings partly cancel when they're added together.

<!-- fig:industries -->

### Since 2005 the tiers have moved toward 1

Median industry ratios, 1993 to 2004 against 2005 to 2025: retail went from 0.68 to 0.88, wholesale from 1.05 to 0.98, and manufacturing from 0.80 to 0.95. These medians use no margin and no deflator. On that basis the manufacturing median stays slightly under one, but with margins and deflation applied, most manufacturing industries amplify after 2005.

Retail smoothing weakened most after 2020. The 60-month aggregate retail ratio was 0.59 at the end of 2019 and peaked at 0.78 afterward.

<!-- fig:rolling -->

### Each shock hit a different tier hardest

The table shows how far each tier's seasonally adjusted inventory-to-sales ratio moved inside each window (its highest value minus its lowest), as a share of its average over the year before. The second and third windows overlap in the first half of 2021.

| Tier | 2008 to 2009 | 2020 to 2021 | 2021 to 2023 |
|---|---|---|---|
| Retail | 17% | 40% | 17% |
| Wholesale | 23% | 33% | 14% |
| Manufacturing | 21% | 28% | 9% |
| Computers and electronics makers | 18% | 8% | 25% |

Wholesale swung most in 2008 to 2009. In COVID the biggest swing was at the store end of the chain, the reverse of a textbook bullwhip. During the chip shortage and the restock that followed, computers and electronics makers built inventory up to 2.27 months of shipments by March 2023.

### Two chains up close

Motor vehicle dealers are the one retail industry that clearly amplifies: 1.53 in 1993 to 2004 and 1.26 since. CRS found the same and put it down to manufacturers pushing inventory onto dealers.

In transportation equipment since 2005, production variance is only 0.28 times new-orders variance. The swings in that industry's order book don't make it through to production. The same comparison for computers and electronics is left out, because FRED notes that its new-orders series has no semiconductor data while its shipments include semiconductors.

## What a planner can take from this

1. Measure amplification on unadjusted data, at the level where the inventory sits. In this data, seasonally adjusted and year-over-year views show far more amplification than the unadjusted flows.
2. Retail inventory buffers work. Most retail industries absorb volatility in every specification tested, and wholesale adds it back. Manufacturing absorbed it before 2005 and, under most settings, no longer does.
3. Read the order book with care. In transportation equipment the big swings are in new orders, so order volatility overstates what plants will actually build and ship.

## Limitations

- Census gross margins aren't published in a form this study could pull, so margin is a setting. Across the four margins tried, the manufacturing share of amplifying cells moves by 22 percentage points.
- The deflators are rough. CPI for retail and the all-commodities PPI elsewhere are cruder than the industry-matched BEA deflators CRS used.
- Sales stand in for demand. Where customers can backorder, sales understate demand volatility and push ratios up, a point CRS also make.
- The panel has 44 industries to CRS's 74. The 1993 to 2004 numbers also come from today's vintage of the data, not the one CRS downloaded, so revisions may explain part of any gap.
- Census new orders for computers and electronics exclude semiconductors (see the FRED notes listed in `docs/method.md`), so no orders-based ratio is reported for that industry.
- The chains aren't closed. Imports, exports and business buyers come and go between the retail, wholesale and manufacturing links.

## Sources

- Cachon, G. P., Randall, T., and Schmidt, G. M. (2007). In Search of the Bullwhip Effect. *Manufacturing & Service Operations Management* 9(4), 457 to 479. https://doi.org/10.1287/msom.1060.0149 (method and Table 1 shares read from the University of Pennsylvania repository copy, https://repository.upenn.edu/oid_papers/137).
- US Census Bureau Monthly Retail Trade, Monthly Wholesale Trade and M3 surveys, via FRED (https://fred.stlouisfed.org). Every series ID and title is in `data/registry.csv`.

## Reproduce

`make all` rebuilds everything from the cached raw files, and `make refresh` downloads the current vintage first. `make gate` runs the lint, the tests, the independent recompute and the check that every number in this memo comes from `outputs/numbers.csv`.
