# Where the bullwhip actually cracks

A replication and extension of Cachon, Randall and Schmidt (2007) on US Census retail, wholesale and manufacturing data, 1992 to 2026.

## The question

Supply chain textbooks teach the bullwhip effect: each step upstream orders more erratically than its customers buy, so a small wobble at the checkout becomes a large swing at the factory. Cachon, Randall and Schmidt (CRS) tested this on 1992 to 2004 Census data and mostly did not find it. Retailers smoothed, wholesalers amplified, manufacturers were mixed. This project asks three things. Does their result hold on today's data, extended through 2025? Does it survive the measurement choices an analyst has to make? And what did the 2008, 2020 and 2021 to 2023 shocks do to it?

## The answer

For retail and wholesale, the CRS pattern holds and is stable as long as the seasonal pattern stays in the data. Most wholesale industries amplify in {{cellmaj_n_wholesale}} of {{n_spec_kept}} measurement specifications. Most retail industries amplify in {{cellmaj_n_retail}} of {{n_spec_kept}}. Manufacturing is the tier that changed. In the 1993 to 2004 window CRS studied, most manufacturing industries amplify in only {{mfg_maj_crs}} of {{mfg_specs_crs}} specifications. Since 2005 they amplify in {{mfg_maj_post}} of {{mfg_specs_post}}, though that verdict leans on a gross-margin assumption that public data no longer pin down. Remove seasonality, by seasonal adjustment or by year-over-year comparison, and most industries in every tier look like amplifiers.

## Data

{{n_series}} monthly series: {{n_series_census}} from the US Census Bureau (Monthly Retail Trade, Monthly Wholesale Trade, and the M3 manufacturers' survey) and two BLS price indexes, pulled keyless from FRED and pinned by sha256 in `data/manifest.json`. The panel has {{n_ind_total}} non-overlapping industries: {{n_ind_retail}} retail, {{n_ind_wholesale}} merchant wholesale and {{n_ind_manufacturing}} manufacturing. CRS had {{crs_paper_n_industries}}. FRED carries sales but not inventories for several store types on their own (electronics and appliance stores appear only combined with furniture stores), and overlapping aggregates are left out so no industry is counted twice.

## Method

Following CRS: production (material inflow) = sales + this month's inventory − last month's inventory. The amplification ratio is the variance of production over the variance of demand, after logging and first-differencing both, with no seasonal adjustment. A ratio above 1 means the industry passes on more volatility than it receives. Demand is sales, or new orders where the M3 survey publishes them. Each headline ratio carries a 95% moving-block bootstrap interval (12-month blocks, 2,000 draws), so serial correlation does not overstate precision.

CRS made two adjustments this project cannot reproduce exactly. Sales are at selling price but inventories are at cost, so CRS scaled sales by monthly Census gross margins, which are no longer published in a keyless form. They also deflated by BEA price indexes. Both became grid dimensions instead of fixed choices. The full grid runs every industry under 3 time windows, 4 gross margins (0, 15, 30 and 45 percent), with and without a CPI or PPI deflator, 3 detrending transforms, monthly or quarterly data, and with or without seasonal adjustment: {{n_cells}} industry-level cells against sales, plus {{n_cells_orders}} against new orders for the durable manufacturers that report them. Shares below count the sales cells only. {{n_undefined}} cells are undefined because clothing stores' production went negative in April 2020: store closures drew inventory down by more than the month's cost-adjusted sales. Undefined cells are left out of every share's denominator.

## Findings

**1. The replication holds in direction.** Share of industries with a ratio above 1, 1993 to 2004, no margin or price adjustment:

| Tier | CRS 2007, unadjusted | This data, unadjusted | CRS 2007, seasonally adjusted | This data, seasonally adjusted |
|---|---|---|---|---|
| Retail | {{crs_paper_nsa_retail}} | {{rep_nsa_retail}} | {{crs_paper_sa_retail}} | {{rep_sa_retail}} |
| Wholesale | {{crs_paper_nsa_wholesale}} | {{rep_nsa_wholesale}} | {{crs_paper_sa_wholesale}} | {{rep_sa_wholesale}} |
| Manufacturing | {{crs_paper_nsa_manufacturing}} | {{rep_nsa_manufacturing}} | {{crs_paper_sa_manufacturing}} | {{rep_sa_manufacturing}} |

Across the margin and deflator settings, the unadjusted shares range from {{rep_lo_retail}} to {{rep_hi_retail}} for retail, {{rep_lo_wholesale}} to {{rep_hi_wholesale}} for wholesale, and {{rep_lo_manufacturing}} to {{rep_hi_manufacturing}} for manufacturing. The CRS wholesale figure sits inside our band. Our manufacturing share is below theirs at every margin except the highest one tried.

**2. Seasonality is the choice that decides the answer.** With seasonality kept, {{robust_kept_retail}} of retail cells, {{robust_kept_wholesale}} of wholesale cells and {{robust_kept_manufacturing}} of manufacturing cells amplify. With it removed, those become {{robust_removed_retail}}, {{robust_removed_wholesale}} and {{robust_removed_manufacturing}}. Physical flows have to follow the real calendar, so the unadjusted numbers describe what warehouses and plants actually absorb. A year-over-year chart of orders against sales will show a bullwhip that the physical flows do not have.

<!-- fig:split -->

**3. Seasonal industries smooth.** Across the {{seas_n}} industries, the share of demand variance explained by the calendar month correlates with the log amplification ratio at Spearman ρ = {{seas_rho}} (p {{seas_p}}). This is CRS hypothesis 1. The likely mechanism, theirs too, is that predictable peaks get built ahead of time, which flattens inflow relative to sales.

<!-- fig:season -->

**4. The aggregate tiers.** 1993 to 2025, unadjusted: retail {{agg_retail}} (95% interval {{agg_retail_lo}} to {{agg_retail_hi}}), wholesale {{agg_wholesale}} ({{agg_wholesale_lo}} to {{agg_wholesale_hi}}), manufacturing {{agg_manufacturing}} ({{agg_manufacturing_lo}} to {{agg_manufacturing_hi}}). Aggregate wholesale cannot be told apart from 1, even though most wholesale industries amplify. One reading, not tested here, is that industry swings partly offset when they are added together.

<!-- fig:industries -->

**5. Since 2005 the tiers have converged toward 1.** Median industry ratio, 1993 to 2004 against 2005 to 2025: retail {{med_crs_retail}} to {{med_post_retail}}, wholesale {{med_crs_wholesale}} to {{med_post_wholesale}}, manufacturing {{med_crs_manufacturing}} to {{med_post_manufacturing}}. These medians use no margin and no deflator. The manufacturing median stays slightly under one on that basis, while with margins and deflation applied most manufacturing industries amplify after 2005. Retail smoothing weakened most after 2020: the 60-month aggregate retail ratio was {{roll_retail_2019}} at the end of 2019 and peaked at {{roll_retail_peak}} afterwards.

<!-- fig:rolling -->

**6. Each shock hit a different tier hardest.** Range of the seasonally adjusted inventory-to-sales ratio inside each window (highest minus lowest), as a share of the prior year's average. The second and third windows overlap in the first half of 2021.

| Tier | 2008 to 2009 | 2020 to 2021 | 2021 to 2023 |
|---|---|---|---|
| Retail | {{swing_gfc_retail}} | {{swing_covid_retail}} | {{swing_chips_retail}} |
| Wholesale | {{swing_gfc_wholesale}} | {{swing_covid_wholesale}} | {{swing_chips_wholesale}} |
| Manufacturing | {{swing_gfc_manufacturing}} | {{swing_covid_manufacturing}} | {{swing_chips_manufacturing}} |
| Computers and electronics mfg | {{swing_gfc_electronics}} | {{swing_covid_electronics}} | {{swing_chips_electronics}} |

In 2008 to 2009 wholesale swung most. In COVID the largest swing was at the store end of the chain, the reverse of a classic bullwhip. In the chip shortage and restock, computers and electronics manufacturers built inventory to {{chips_elec_peak}} months of shipments by {{chips_elec_peak_ym}}.

**7. Two chains up close.** Motor vehicle dealers are the one retail industry that clearly amplifies: {{chain_auto_dealers_crs}} in 1993 to 2004 and {{chain_auto_dealers_post}} since. CRS found the same and explained it by manufacturers pushing inventory onto dealers. For transportation equipment since 2005, production variance is only {{chain_transport_orders_post}} times new-orders variance. The whip is real in that industry's order book, but it does not reach production. The same comparison for computers and electronics is left out: FRED's notes say that industry's new-orders series has no semiconductor data, while its shipments include semiconductors, so the two series cover different industries.

## What a planner should take from this

1. Measure amplification on unadjusted data at the level where inventory actually sits. In this data, seasonally adjusted and year-over-year views show far more amplification than the unadjusted flows do.
2. Retail inventory buffers work: most retail industries absorb volatility in every specification tried. Wholesale adds volatility back. Manufacturing absorbed it before 2005 and, under most settings, no longer does.
3. Read the order book with care. In transportation equipment the largest swings are in new orders, not production, so order volatility overstates what plants will actually build and ship.

## Limitations

- **Margins.** Census no longer publishes keyless monthly gross margins, so margin is a grid dimension. The manufacturing share of amplifying cells moves by {{margin_swing_manufacturing}} across the four margins.
- **Deflators.** CPI for retail and the all-commodities PPI elsewhere are crude next to the industry-matched BEA deflators CRS used.
- **Sales as a stand-in for demand.** Where customers can backorder, sales understate demand volatility, which biases ratios upward (CRS make the same point).
- **Coverage and vintage.** {{n_ind_total}} industries instead of {{crs_paper_n_industries}}. The 1993 to 2004 numbers come from today's vintage of the data, not the one CRS downloaded, so revisions can explain part of any gap.
- **Orders coverage.** Census new orders for computers and electronics exclude semiconductors (per the FRED notes on its new-orders and shipments series, listed in `docs/method.md`), so orders-based ratios for that industry are not reported.
- **Chains are not closed.** Imports, exports and business buyers enter and leave between the retail, wholesale and manufacturing links.

## Sources

- Cachon, G. P., Randall, T., and Schmidt, G. M. (2007). In Search of the Bullwhip Effect. *Manufacturing & Service Operations Management* 9(4), 457 to 479. https://doi.org/10.1287/msom.1060.0149 (method and Table 1 shares read from the University of Pennsylvania repository copy, https://repository.upenn.edu/oid_papers/137).
- US Census Bureau Monthly Retail Trade, Monthly Wholesale Trade and M3 surveys, via FRED (https://fred.stlouisfed.org). Every series ID and title is in `data/registry.csv`.

## Reproduce

`make all` rebuilds everything from the cached raw files. `make refresh` downloads the current vintage. `make gate` runs lint, tests, the independent reconcile and this memo's number check.
