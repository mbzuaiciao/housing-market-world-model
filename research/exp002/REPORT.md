# EXP-002 results

**NO-GO for added forecasting complexity.** The GRU reduced ordinary-world three-step MAE by **1.47%** relative to ridge, below the frozen 5% threshold. One-step MAE improved by 1.33%. Under the predefined adverse demand shift, GRU errors exceeded both simple baselines. GRU intervention estimates had higher MAE than the action-aware ridge and the zero-effect reference at both horizons. The separate intervention gate failed.

The [protocol](PROTOCOL.md) was frozen in commit `138ce16` before training. Implementation commit `d49cda3` preceded the single fixed training attempt. Validation was diagnostic only. The configuration, source hashes, per-world metrics, scenario effects and training loss trace are in [results.json](results.json). There were no training reruns or configuration changes after test inspection.

## Execution and information controls

The timed experiment took **3.161 seconds**, including its unit tests, simulations, fitting, bootstrap summaries and evaluation. This timer excludes Python/dependency import startup. It ran on macOS-27.2.1-arm64-arm-64bit with Python 3.9.6, NumPy 2.0.2 and PyTorch 2.8.0, using local CPU execution. PyTorch intra-op and inter-op thread counts were each set to one. NumPy used macOS Accelerate, whose internal thread count was unpinned. This departs from the protocol's blanket one-thread setting and limits the runtime comparison.

There were 24 training worlds and six worlds in each validation, ordinary-test and shifted-test split. Each world supplied 83 matched cutoffs, for 1,992 training examples and 498 examples per evaluation split. Seeds and simulator settings were frozen. Both learned models used the same 12 by 6 observable history, training examples and standardized targets. Ridge had 146 fitted coefficients including intercepts. The GRU had 746 parameters and trained for exactly 30 epochs.

Every cutoff precedes current-week buyer activity. Horizon 1 predicts sales in the current action week and horizon 3 predicts sales two weeks later. Inputs include previous attention and sales, current pre-action inventory and price, previous action and current announced randomized action. The models receive aggregate histories only. Hidden demand, buyer shocks and future outcomes enter simulator evaluation and labels only. Both forecasts are direct outputs.

## Simulator sanity and oracle effects

All conservation and constraint tests passed. The oracle gate passed before training. Eighteen scenarios from ordinary-test worlds at weeks 24, 48 and 72 compare a market-wide 5% permanent asking-price cut with zero action. Each pair starts from the same state and shares every exogenous shock and future action. Model predictions use the same observed history with only the current action toggled.

| Oracle outcome | Mean action effect, transactions | 95% world-bootstrap interval |
| --- | ---: | --- |
| Current-week sales | 0.333 | [0.111, 0.556] |
| Third-week sales | 0.111 | [0.000, 0.222] |
| Cumulative sales over three weeks | 0.611 | [0.278, 1.111] |

The positive immediate mean and nonnegative interval lower bound satisfy the frozen sanity gate. Oracle effects were zero in 13 of 18 immediate scenarios and 14 of 18 third-week scenarios. One scenario had a negative third-week effect because paired inventories and buyer matches can diverge after earlier sales. Oracle path differences are exact within this simulator. Their aggregate averages retain Monte Carlo uncertainty.

## Forecasting

MAE is measured in transaction counts, averaged within each world and then equally across worlds. Bracketed intervals resample six independent worlds, retaining all dependent cutoffs within a world. All bootstrap intervals use 2,000 draws and seed 19.

| Split | Model | One-step MAE [95% interval] | Three-step MAE [95% interval] |
| --- | --- | --- | --- |
| validation | persistence | 2.444 [2.307, 2.576] | 2.534 [2.299, 2.735] |
| validation | ridge | 1.805 [1.728, 1.887] | 1.970 [1.810, 2.125] |
| validation | gru | 1.788 [1.713, 1.876] | 1.930 [1.823, 2.053] |
| ordinary | persistence | 2.269 [2.004, 2.514] | 2.380 [2.249, 2.532] |
| ordinary | ridge | 1.742 [1.592, 1.887] | 1.843 [1.695, 1.991] |
| ordinary | gru | 1.719 [1.556, 1.850] | 1.816 [1.674, 1.957] |
| shifted | persistence | 1.229 [1.139, 1.299] | 1.333 [1.237, 1.430] |
| shifted | ridge | 1.179 [1.113, 1.256] | 2.308 [2.224, 2.400] |
| shifted | gru | 1.807 [1.703, 1.929] | 2.867 [2.772, 2.963] |

Ridge was the stronger ordinary-test simple reference at both horizons. GRU minus ridge paired MAE differences were -0.023 [-0.079, 0.039] for one step and -0.027 [-0.060, 0.003] for three steps. Both intervals include zero. The 1.47% three-step improvement fails the predefined 5% requirement.

The shifted-world summary covers the full evaluation span, with demand shifted from week 48 onward. Of 83 cutoffs, 37 precede the shift and 46 follow it. Three-step forecasts at cutoffs 46 and 47 cross the shift boundary. Shifted worlds use independent seeds from ordinary worlds, so their aggregate difference also includes world variation. In shifted worlds the GRU increased three-step MAE by 115.06% relative to persistence and 24.26% relative to ridge. Low activity after the adverse shift favors the persistence reference and exposes extrapolation failure in the fitted models.

### Per-world test MAE

Columns give horizon 1 / horizon 3. Seed-level values and full precision appear in the JSON artifact.

| Regime | Seed | Persistence | Ridge | GRU |
| --- | ---: | ---: | ---: | ---: |
| ordinary | 1000 | 1.651 / 2.108 | 1.470 / 1.599 | 1.587 / 1.608 |
| ordinary | 1001 | 2.096 / 2.313 | 1.469 / 1.605 | 1.363 / 1.559 |
| ordinary | 1002 | 2.578 / 2.687 | 1.954 / 2.157 | 1.848 / 2.064 |
| ordinary | 1003 | 2.229 / 2.337 | 1.822 / 1.891 | 1.807 / 1.833 |
| ordinary | 1004 | 2.627 / 2.494 | 1.854 / 1.934 | 1.821 / 1.953 |
| ordinary | 1005 | 2.434 / 2.337 | 1.882 / 1.870 | 1.886 / 1.876 |
| shifted | 2000 | 1.012 / 1.169 | 1.156 / 2.212 | 1.671 / 2.724 |
| shifted | 2001 | 1.313 / 1.494 | 1.169 / 2.397 | 1.893 / 3.030 |
| shifted | 2002 | 1.265 / 1.181 | 1.096 / 2.158 | 1.761 / 2.770 |
| shifted | 2003 | 1.253 / 1.434 | 1.351 / 2.501 | 2.076 / 3.038 |
| shifted | 2004 | 1.205 / 1.313 | 1.072 / 2.268 | 1.660 / 2.859 |
| shifted | 2005 | 1.325 / 1.410 | 1.227 / 2.310 | 1.778 / 2.785 |

## Intervention estimates

Effect MAE compares predicted action-minus-control differences to paired simulator effects at each horizon. Bias is predicted effect minus oracle effect. Signs use the frozen 1e-6 tolerance and include exact zeros.

| Model | Horizon | Predicted mean effect | Effect MAE [95% interval] | Bias | Sign accuracy |
| --- | ---: | ---: | --- | ---: | ---: |
| persistence | 1 | 0.000 | 0.333 [0.111, 0.556] | -0.333 | 72.2% |
| persistence | 3 | 0.000 | 0.222 [0.000, 0.556] | -0.111 | 77.8% |
| ridge | 1 | 0.194 | 0.419 [0.262, 0.577] | -0.140 | 27.8% |
| ridge | 3 | -0.009 | 0.230 [0.009, 0.562] | -0.120 | 5.6% |
| gru | 1 | 0.229 | 0.563 [0.396, 0.736] | -0.105 | 16.7% |
| gru | 3 | 0.061 | 0.374 [0.193, 0.566] | -0.050 | 16.7% |

The zero-effect persistence reference abstains from estimating a causal response. Its sign accuracy is high because most paired effects are zero. Ridge and GRU explicitly condition on randomized actions and can therefore supply action-response estimates for this synthetic comparison. GRU mean effects resemble the oracle aggregate means, but its scenario-level errors exceed both references.

GRU minus ridge paired effect-MAE differences were +0.144 [0.067, 0.211] immediately and +0.144 [-0.053, 0.293] at three steps. The required negative difference intervals failed. Bootstrap intervals for predicted mean effects, bias, direction accuracy and comparisons against zero-effect persistence appear in the JSON artifact.

## Uncertainty and limitations

These models produce point forecasts. Predictive calibration, interval coverage and proper probabilistic scores are unavailable. The reported bootstrap intervals describe variation in scores or average effects across simulation worlds. The experiment therefore supplies no evidence that predictive uncertainty stays calibrated under the demand shift.

Buyer budgets, view probabilities, purchase probabilities, seller arrivals and price actions are specified mechanisms. There is no bargaining, financing delay, seller strategic behavior, spatial structure or empirically estimated buyer population. Completion follows an explicit random probability and every completed sale immediately removes its listing. Actions affect all active listings and persist in their prices. These results concern that market-wide policy and its fixed random assignment distribution.

The recurrent state is learned for prediction. Its coordinates have no established interpretation as the simulator demand state. Forecast accuracy alone cannot validate intervention effects. Predictors estimate conditional averages from observed histories while the paired oracle includes path-specific shocks and unobserved states. Comparing those quantities creates irreducible scenario-level variation. Six test worlds and 18 paired scenarios give limited precision, especially when most realized effects are zero.

The ordinary and shifted test worlds are independent, and the shift is deliberately outside the training dynamics. Generalization depends on this one simulator configuration, one initialization and a small seed set. No empirical housing dataset was used in EXP-002.

## Reproduce and checks

From the repository root, use Python 3.9+ with the pinned dependencies. Install into a local virtual environment if necessary.

```sh
python3 -m pip install -r research/exp002/requirements.txt
python3 -m unittest discover -s research/exp002 -v
python3 research/exp002/experiment.py --output /tmp/exp002-results.json
git diff --check
```

The four tests cover deterministic repeatability, conservation and unique sales, buyer budget constraints, disjoint seed splits, the predetermined shift, absence of future feature leakage and paired shock/state controls. The experiment executes these tests before the oracle gate and fitting. Fresh reproduction executes the same fixed training attempt. Different CPU libraries may introduce small floating-point differences.

The recorded run passed all four tests. Source digests and the frozen protocol commit in the artifact permit integrity checks without another training run. Worlds and model weights are generated locally and excluded from the committed artifacts.
