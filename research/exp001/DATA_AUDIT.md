# EXP-001 data audit

**Decision: NO-GO for the historical forecasting experiment as specified.** The published snapshots contain 20,326 unflagged attention and pending metro-month pairs across 208 county-screened candidate metros, with coverage before, during and after 2022–23. The public Zillow crosswalk predates the July 2023 OMB boundaries and does not establish the county composition of the audited Zillow series across the sample. The housing downloads also provide a single revised snapshot per metric. Historical release-time values, including the pre-2025 Realtor.com history that was later restated, were not verified. The coverage below supports feasibility screening. A forecast test needs verified boundaries and an auditable release history or a prospective archive.

## What the sources measure

| Publisher and series | Measurement | Interpretation |
| --- | --- | --- |
| Realtor.com® Economic Research, LDP Unique Viewers Per Property (vs US), `page_view_count_per_property_vs_us` | Monthly unitless ratio of listing detail page viewers for a typical property in a geography to the corresponding typical-property U.S. value in the same month. The data library draws on MLS-listed single-family and condo/townhome listings. | Platform attention per property relative to national attention. Changes can reflect the U.S. denominator, listing mix or platform usage. Buyer intent, offers and conversions are unobserved. The separate hotness score combines supply and attention rankings. |
| Zillow Research, Newly Pending Listings, raw All Homes | Monthly flow of listings transitioning from for-sale to pending on Zillow. All Homes includes single-family, condominium and co-operative homes with a county record. | Zillow listing activity. A pending transition can fail to close. Realtor.com's pending listing count instead measures the stock of pending listings on a typical day. |
| Zillow Research, For-Sale Inventory, raw All Homes | Unique listings active at any time in the month. | Inventory stock measure over a monthly window. It can include listings that also go pending that month. It differs from a month-end stock or a count of new listings. |
| Zillow Research, Median List Price, raw All Homes | Median asking price in a geography for the monthly series, in dollars. | List price mixes properties offered for sale and can move with listing composition. |
| Freddie Mac PMMS via FRED, `MORTGAGE30US` | Weekly U.S. average 30-year fixed mortgage rate, percent, unadjusted. FRED describes a Thursday cadence with observed holiday exceptions. | National control shared across metros. The conditional protocol takes the mean by actual observation date within a completed calendar month, using only releases known at the cutoff. Freddie Mac changed PMMS methodology on November 17, 2022. |

The study joins aggregate observations from two listing platforms. Listing-level populations and viewer-to-property-to-purchase links are unobserved. Definitions and cadence come from the [Realtor.com data dictionary](https://www.realtor.com/research/data/), [Zillow Research downloads](https://www.zillow.com/research/data/) and [FRED series notes](https://fred.stlouisfed.org/series/MORTGAGE30US).

## Downloads and vintages

All seven data files below returned HTTP 200 without authentication on **2026-11-13** around 21:53–21:55 UTC. A terminal request to the Zillow catalog returned 403. The catalog loaded in a browser and exposed the official CSV links through **For-sale listings → Data Type → Raw, All Homes, Monthly → Metro & U.S.** The listed Zillow files are the public CSVs. Zillow Economic Data (ZED) is a separate login-required service. The Realtor.com catalog still displayed September 2026 as the latest hotness month during inspection, while the downloaded CSV contained October 2026. Coverage uses the files. HTTP last-modified and object version IDs identify retrieved objects and do not establish the historical publication time of individual values. [Zillow Market Data](https://www.zillow.com/research/market-data/)

| Save as and source | HTTP Last-Modified (UTC) | Object version ID, if supplied | SHA-256 |
| --- | --- | --- | --- |
| [realtor.csv](https://econdata.s3-us-west-2.amazonaws.com/Reports/Hotness/RDC_Inventory_Hotness_Metrics_Metro_History.csv) | 2026-11-13 20:07:33 | `MrIvmXKjMRZbyWatNzqRIFmIJvnaAV1v` | `48bf39615060483df169516434fcef890625c6d6ad305998acdf5771743706e3` |
| [pending.csv](https://files.zillowstatic.com/research/public_csvs/new_pending/Metro_new_pending_uc_sfrcondo_month.csv) | 2026-10-16 01:46:07 | `rfPB_U8smDE4DPFqVfXPOXm7j9bDPizL` | `c45ed681977b362ee3d42c8acb3a74fe6ea7723f73e549390ca94a9150a37769` |
| [inventory.csv](https://files.zillowstatic.com/research/public_csvs/invt_fs/Metro_invt_fs_uc_sfrcondo_month.csv) | 2026-10-16 01:38:31 | `coyOZ2MVJ2.GFhjavhftMf2b71uihdde` | `99a378c2fedfd65c10b9f9996d6c7b27fe774176f6c67cd3423c236f4a24bfc5` |
| [price.csv](https://files.zillowstatic.com/research/public_csvs/mlp/Metro_mlp_uc_sfrcondo_month.csv) | 2026-10-16 01:44:29 | `gbXdPGApD0gnPsE2Ra67f_bsonXbc7u4` | `d00e510a650c17ded108cb29ca6e160843b10814bde5add1ac4ad7ad48a3e96c` |
| [rate.csv](https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US) | 2026-11-12 17:03:11 | — | `45d20db28675827f068d0534949a6c1f431c58193d2153c8fbd9435f5b2530e3` |
| [zillow-crosswalk.csv](https://files.zillowstatic.com/research/public/CountyCrossWalk_Zillow.csv) | 2022-02-14 21:44:51 | `SnEE99vhNGyIinsY96Hvs97_lj4JYUd9` | `ebfdad22e93ea0f5a5fc9bce89043a3a29947b922831872c2f09c3374524a355` |
| [omb2023.xlsx](https://www2.census.gov/programs-surveys/metro-micro/geographies/reference-files/2023/delineation-files/list1_2023.xlsx) | 2023-08-04 14:36:17 | — | `952c4b1e78acbb54e6ec9412434b7602fedacbf021736351a63c181bdb753629` |

### Attribution and use

- Attribute the attention data to **Realtor.com® Economic Research** and link its data library for digital use. The publisher also provides guidance on sharing research assets. [Data library](https://www.realtor.com/research/data/), [Asset Sharing Guide](https://rdceconomics.wpengine.com/wp-content/uploads/2023/02/realtor-research-asset-sharing.pdf)
- **Data Provided by Zillow Group.** Zillow Research offers the downloadable research data for public analysis. Its general terms describe use and display restrictions and a citation format for covered aggregate data. A blanket open redistribution license for these files was not established. [Zillow Market Data](https://www.zillow.com/research/market-data/), [Zillow Terms of Use](https://www.zillow.com/corporate/terms-of-use/)
- **Freddie Mac**, 30-Year Fixed Rate Mortgage Average in the United States [MORTGAGE30US], retrieved November 13, 2026 from FRED, Federal Reserve Bank of St. Louis. FRED marks the data as copyrighted and citation required. [FRED series notes](https://fred.stlouisfed.org/series/MORTGAGE30US)
- Metro definitions come from the U.S. Census Bureau's publication of the July 2023 OMB delineations. This repository reports derived coverage counts and keeps raw inputs local. [Census delineation files](https://www.census.gov/geographies/reference-files/time-series/demo/metro-micro/delineation-files.html)

## Observed coverage

Zillow counts exclude the U.S. aggregate. Its `msa` tag is the publisher's row type and can include regions outside the OMB metropolitan set. Missing cells count blank or explicitly missing values in an otherwise present row and month. A genuine zero stays observed. There were no absent keys within the source grids or duplicate geography-month keys in the audited files.

| Series | First–last observed | Geographic IDs | Observed | Missing cells | Quality flags |
| --- | --- | ---: | ---: | ---: | ---: |
| Realtor.com relative viewers | 2017-08–2026-10 | 300 | 33,300 | 0 | 1,202 |
| Zillow newly pending | 2018-01–2026-09 | 900 | 78,385 | 16,115 | — |
| Zillow inventory | 2018-01–2026-09 | 927 | 96,073 | 1,262 | — |
| Zillow median list price | 2018-01–2026-09 | 927 | 95,199 | 2,136 | — |
| Freddie Mac rate | 1971-04-02–2026-11-12 | 1 national | 2,903 weekly rows | 0 missing values in delivered rows | — |

### Geography join and exclusions

1. Convert Realtor.com's `month_date_yyyymm` and Zillow's calendar month-end dates to `YYYY-MM`. Join on that month and an explicit geography mapping. Realtor.com uses five-digit `cbsa_code`. Zillow uses proprietary `RegionID`, including a U.S. row to exclude. Zillow inventory and price align provisionally on the same Zillow ID and month.
2. Use the [publisher's legacy crosswalk](https://files.zillowstatic.com/research/public/CountyCrossWalk_Zillow.csv) to map `MetroRegionID_Zillow` to `CBSACode`. Require uniqueness in both directions. The [Commerce Data Service tutorial](https://commercedataservice.github.io/tutorial_zillow_acs/) documents the historical bridge. The CSV's February 2022 modification date is a file timestamp. Its underlying OMB vintage is not specified in the file.
3. Compare the full legacy Zillow county FIPS set to the official July 2023 Census county FIPS set for that CBSA. Keep only exact equality and an OMB **metropolitan** designation. This is a screen for discrepancies between the available maps. The county assignments actually used to produce Zillow's historical pending, inventory and list-price series remain unverified. No names, ranks or approximate geographic matches enter the join.

Of 900 Zillow pending IDs, 30 lacked a legacy mapping and 586 mapped to codes absent from attention. There were zero ambiguous mappings among these IDs. Sixteen of 300 attention codes lacked a legacy pending match. Of 284 code matches, five are outside the July 2023 OMB metropolitan set and 71 have a different county set. For example, Zillow's legacy New York ID `394913` maps to CBSA `35620` but includes FIPS `36027`, `36071` and `42103` that the July 2023 set excludes. Los Angeles ID `753899` maps to CBSA `31080` and passes the screen.

| Same-month join, 2018-01–2026-09 (105 months) | Legacy ID match | Exact legacy-to-2023 county screen |
| --- | ---: | ---: |
| Matched metros | 284 | 208 |
| Potential metro-months | 29,820 | 21,840 |
| Missing attention | 0 | 0 |
| Missing pending | 1,084 | 689 |
| Both values observed | 28,736 | 21,151 |
| Observed pairs with Realtor.com quality flag | 1,082 | 825 |
| Unflagged observed pairs | 27,654 | 20,326 |
| Unflagged with inventory, price and at least one rate reading in month | 27,547 | 20,239 |
| Metros with unflagged pairs in all 105 months | 50 | 34 |

The publisher flags values outside their typical range. The unflagged count conservatively excludes the entire flagged row. Of 20,326 unflagged screened pairs, 16 lack inventory and 76 lack price, with overlap between those counts. All corresponding months have FRED observations. Same-month control completeness checks data coverage only. The number of usable forecast cases depends on releases, lags and target availability.

| Window | Calendar months | Unflagged county-screened metro-months |
| --- | ---: | ---: |
| 2018-01–2021-12, pre-shift | 48 | 9,076 |
| 2022-01–2023-12, regime shift | 24 | 4,660 |
| 2024-01–2026-09, post-shift | 33 | 6,590 |
| 2025-04–2026-09, proposed later test targets (within post-shift) | 18 | 3,637 |

The screened panel has 145–208 unflagged pairs per month. Missingness and geography exclusions concentrate the sample in markets covered by both platforms and passing the screen. These counts should not be extrapolated to all U.S. markets.

## Availability at prediction time

- Realtor.com reissues the full history each month and can change earlier observations. With the January 2025 data release it restated history using the July 2023 OMB delineations. A backtest of earlier origins using today's history would see the later definitions and revisions. Even unchanged metro county sets cannot rule out revisions to inputs or the national reference value. The observed October 2026 attention CSV was available by November 13. That check cannot establish a historical series of first-release dates or values. [Realtor.com data library](https://www.realtor.com/research/data/), [January 2025 release note](https://www.realtor.com/research/january-2025-data/), [Census 2023 geography changes](https://www.census.gov/programs-surveys/acs/geography-acs/geography-boundaries-by-year/2023.html)
- Zillow's calendar lists monthly CSV updates on the 16th, including September data on October 16 and October data on November 16, 2026. On November 13, all three audited Zillow CSVs ended in September. Month-end column labels are measurement dates. The monthly calendar and raw designation supply neither historic snapshots nor evidence about revision magnitude. [Zillow release calendar](https://www.zillow.com/research/calendar/)
- The FRED download is the latest view. The [ALFRED series](https://alfred.stlouisfed.org/series?seid=MORTGAGE30US) is a route for verifying rate vintages, which this audit did not extract. Keep the November 2022 PMMS methodology change visible in interpretation. [FRED series notes](https://fred.stlouisfed.org/series/MORTGAGE30US)

Reopen the decision when Zillow's pending and any included control geographies can be tied to dated county sets and the feature values at historical cutoffs can be reconstructed from dated releases. A prospective archive could support a future test after sufficient follow-up. A later-release lag alone cannot remove retrospective revisions. The frozen [protocol](PROTOCOL.md) specifies both the release-time gate and the proposed splits within the measured span.

## Reproduce

Save the seven publisher downloads under the filenames in the provenance table in one directory outside the repository. To reproduce the precise counts, use snapshots matching the recorded SHA-256 digests. The [recorded Realtor.com object](https://econdata.s3-us-west-2.amazonaws.com/Reports/Hotness/RDC_Inventory_Hotness_Metrics_Metro_History.csv?versionId=MrIvmXKjMRZbyWatNzqRIFmIJvnaAV1v) returned matching bytes with its version ID. Requests using the recorded version IDs on Zillow's four public links returned 403. The unversioned links may serve newer vintages. New snapshots can be audited with the same script and will produce their own hashes and coverage.

From the repository root with Python 3.9+ and no dependencies:

```sh
python3 research/exp001/audit.py /path/to/snapshots
```

The script checks unique keys, Zillow month ends, missing and invalid observations, the one-to-one ID bridge and county membership. It emits aggregate coverage and SHA-256 digests as JSON. Compare `county_screened_join` and `legacy_code_join` to the join table above.
