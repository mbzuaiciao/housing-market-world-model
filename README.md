# Housing market world model

**EXP-001** asks whether lagged online listing attention improves monthly metro forecasts of newly pending listings beyond a regularized autoregression with market controls.

**Status:** Data feasibility audit complete. **NO-GO** for the proposed historical forecasting experiment until metro boundaries and historical feature availability can be verified. See the [data audit and reproduction steps](research/exp001/DATA_AUDIT.md) and the [conditional protocol](research/exp001/PROTOCOL.md).

Attention data from [Realtor.com® Economic Research](https://www.realtor.com/research/data/). Data Provided by Zillow Group via [Zillow Research](https://www.zillow.com/research/data/). Mortgage rates from Freddie Mac's Primary Mortgage Market Survey®, [MORTGAGE30US via FRED, Federal Reserve Bank of St. Louis](https://fred.stlouisfed.org/series/MORTGAGE30US). Metro delineations from the [U.S. Census Bureau](https://www.census.gov/geographies/reference-files/time-series/demo/metro-micro/delineation-files.html).

**EXP-002** tests forecasting and randomized price interventions in a controlled synthetic market with known ground truth. The fixed CPU experiment reached **NO-GO** for added model complexity. The GRU improved ordinary-world three-step MAE by 1.47%, below the 5% threshold, and intervention-effect errors exceeded the simple references. See the [frozen protocol](research/exp002/PROTOCOL.md), [actual results and reproduction commands](research/exp002/REPORT.md), and [compact result artifact](research/exp002/results.json). This study has its own simulation scope and provides no real-world validation.
