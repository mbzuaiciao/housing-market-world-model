# EXP-002 frozen protocol

Freeze this file in Git before executing training. The experiment evaluates incremental predictive skill and action-effect estimation in a controlled synthetic market. The primary hypothesis is that one compact GRU improves ordinary-world three-step transaction MAE by at least 5% over the stronger of persistence and ridge, with at most 5% deterioration at one step. Synthetic evidence has no direct real-market interpretation.

## Simulator and information clock

Use 96 discrete weeks, 80 listing slots, at most 6 new sellers per week and 32 potential buyers per week. Each listing has persistent quality, asking price and a unique ID. New sellers fill vacant slots in slot order. Their quality is uniform on [0.85, 1.15] and asking price is max(50, 100 times quality plus normal noise with standard deviation 5). Unsold listings persist. Sales remove listings and each buyer can buy at most one property in a week.

Hidden demand starts at a standard normal draw times 0.3 and evolves as 0.85 times its previous value plus normal noise with standard deviation 0.25. In the shifted test regime only, the demand equation gains an intercept of -0.6 from week 48 onward. This is a persistent adverse demand shift.

Potential buyers arrive independently with probability 0.8 times sigmoid(demand). A buyer's budget is uniform on [85, 135] plus 8 times demand. For each active property the probability of a view is sigmoid(0.5 + demand - 4 times (asking price / quality - 100) / 100). Independent uniform shocks determine views. Among viewed, affordable properties, a buyer chooses the maximum of a uniform preference score minus asking price / 200. An offer occurs with probability 0.65 and completes immediately with probability 0.8. Buyers act in fixed order and already sold properties are removed from later choices. All sales close immediately at the asking price.

Each week an independent Bernoulli(0.25) action applies a permanent 5% asking-price reduction to every active listing, after new sellers list and before buyers arrive. Actions are randomized independently of demand and buyer shocks. This market-wide action is the intervention unit.

The current row contains previous-week total views, current pre-action mean asking price, current pre-action listing count, previous-week sales, previous action and current announced action. Empty-market mean price is zero. Models receive exactly the most recent 12 rows, including the current row. The targets are sales in the current action week (one step) and sales two weeks after it (three steps). Week t is a cutoff immediately before its buyer activity, so sales[t] and sales[t+2] correspond to horizons 1 and 3. Current demand, buyer budgets/preferences, future observations/actions and random arrays are inaccessible to forecasting functions.

Draw every exogenous shock up front in a fixed shape indexed by week, buyer and listing slot. Paired action and control trajectories use the same shocks and initial market state even when transactions diverge. This defines pathwise oracle effects conditional on all exogenous shocks. Inventory depletion can reverse the sign of the third-week effect. The sanity gate uses immediate effects, and also reports cumulative three-week effects.

## Fixed splits and models

World seeds are disjoint. Train on seeds 100–123 (24 worlds), validate on 300–305 (6 worlds), ordinary test on 1000–1005 (6 worlds), shifted test on 2000–2005 (6 worlds). Initial history weeks are excluded, and both horizons share cutoffs 11–93 inclusive. No trajectory crosses a split. Shifted and ordinary test worlds have independent randomness.

Use local CPU, float32 PyTorch, one thread, deterministic algorithms, NumPy seed 7 and PyTorch seed 7. No hyperparameter selection and no early stopping. Train each model once. Validation supplies diagnostics only. Training and output generation share a single script invocation after the protocol commit.

- Persistence predicts the previous-week sales for both horizons.
- Ridge flattens the same 12 by 6 observable history as the GRU, standardizes with training-only moments and fits both direct outputs. Minimize mean squared standardized target loss plus 0.1 times the squared coefficient norm, with an unpenalized intercept.
- GRU uses 12 hidden units, one recurrent layer and one linear head with two direct outputs. Standardize inputs and targets with the same training-only moments as ridge. Optimize squared standardized target error with Adam at 0.003 for exactly 30 epochs, batch size 128, sequential fixed-order batches, gradient norm clipped to 1. No dropout, extra architectures or sweeps. Clip count predictions from all models at zero.
- All training worlds, examples and cutoffs are identical across learned models. Both outputs use only origin-time information. Evaluation uses direct heads, with no future teacher forcing.

## Oracle gate and intervention evaluation

Before training, assert conservation, unique sales, buyer budget constraints, repeatability, disjoint splits, future-feature exclusion and paired shock control. Use ordinary test-world checkpoints at weeks 24, 48 and 72, giving 18 held-out scenarios. Starting immediately before each checkpoint week, compare a 5% action with zero action, then retain the same pre-generated future randomized actions and all exogenous shocks for three weeks. Report the paired difference in immediate, third-week and cumulative three-week sales.

Report a 95% bootstrap interval of the mean immediate and cumulative oracle effects, resampling entire worlds (2,000 draws, seed 19). The sanity gate requires the immediate mean effect to be strictly positive and its interval lower bound to be nonnegative, plus all constraint tests passing. Stop before training and report simulator NO-GO if this gate fails.

For each learned model evaluate its two direct heads on the same observable history with only the current action toggled. Compare predicted differences against pathwise oracle differences at horizons 1 and 3. Report effect MAE, bias, sign accuracy and the number of zero oracle effects. Sign uses a 1e-6 numerical tolerance. Include zero-effect persistence and the action-aware ridge as references, and report world-bootstrap intervals for effect MAE and mean effects.

Models predict conditional expectations while pathwise oracle effects include individual shocks. The finite-sample oracle is exact for a paired path, with Monte Carlo uncertainty for aggregate conclusions. Randomized training actions support this synthetic comparison, but predictive fit alone supplies no causal validation.

## Metrics and decision

Report MAE at each horizon separately for validation, ordinary test and shifted test. First average over cutoffs within a world and then weight worlds equally. Report all six test-world scores and 95% bootstrap intervals resampling worlds with 2,000 draws, seed 19. For GRU versus each baseline, report paired MAE differences and percent improvement. For the primary decision, use the lower-MAE simple reference separately for each horizon on the fixed ordinary test. Both references are predefined and reported, so this comparator choice creates no tuning opportunity.

GO for forecasting complexity requires at least 5% three-step improvement and no more than 5% one-step deterioration. Failure gives NO-GO and ends the experiment. Report shift results regardless of primary outcome. These are point forecasts, so predictive calibration, interval coverage and probabilistic scores are unavailable. Bootstrap score intervals quantify sampling uncertainty across worlds.

For a separate positive intervention finding, GRU effect MAE must beat both zero-effect and action-aware ridge references at both horizons, with paired bootstrap difference intervals entirely below zero. Even if these thresholds pass, the result supports this simulator and action distribution only. Do not label the model validated causal planning. Six test worlds and 18 scenarios give limited uncertainty resolution.

## Reproducibility and stopping

Commit simulator, experiment script, compact aggregate/per-world JSON results, report, dependencies and minimal unit tests. Keep generated worlds and trained weights out of Git. Record wall-clock runtime, dependency versions, seed/configuration values and protocol commit. Reproduction can verify numerical agreement within floating-point tolerance on other CPU libraries.

One training attempt per model. Fix implementation errors only when needed for correctness and document any rerun. Do not change configuration, expand data or add model classes after inspecting test metrics. Stop after the report and PR.
