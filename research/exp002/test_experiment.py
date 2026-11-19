"""Minimal regression tests for the experiment's scientific controls."""

import unittest
import numpy as np
from simulator import (
    HISTORY, SPLITS, Market, examples, make_shocks, paired_scenario, simulate, step,
)


class ExperimentTests(unittest.TestCase):
    def test_repeatability_and_constraints(self):
        first = simulate(100)
        second = simulate(100)
        np.testing.assert_array_equal(first[0], second[0])
        np.testing.assert_array_equal(first[1], second[1])
        # Every simulator step also checks conservation and sale uniqueness.
        self.assertTrue((first[1] <= 32).all())
        shocks, market, sold = make_shocks(123), Market(), set()
        for week in range(96):
            _, sales = step(market, shocks, week)
            for listing, _, price, budget in sales:
                self.assertNotIn(listing, sold)
                self.assertLessEqual(price, budget)
                sold.add(listing)
            self.assertEqual(market.next_id, len(sold) + market.active.sum())

    def test_no_future_features(self):
        observations, counts, _, _ = simulate(100)
        original_x, original_y = examples(observations, counts)
        changed_obs, changed_counts = observations.copy(), counts.copy()
        changed_obs[41:] = -999
        changed_counts[40:] = 999
        changed_x, changed_y = examples(changed_obs, changed_counts)
        cutoff_index = 40 - HISTORY + 1
        np.testing.assert_array_equal(original_x[cutoff_index], changed_x[cutoff_index])
        self.assertFalse(np.array_equal(original_y[cutoff_index], changed_y[cutoff_index]))
        np.testing.assert_array_equal(original_x[cutoff_index, -1], observations[40])
        self.assertEqual(original_y[cutoff_index, 1], counts[42])

    def test_disjoint_worlds_and_shift(self):
        seeds = [seed for group in SPLITS.values() for seed in group]
        self.assertEqual(len(seeds), len(set(seeds)))
        ordinary = make_shocks(1000)
        shifted = make_shocks(1000, True)
        np.testing.assert_array_equal(ordinary.demand[:48], shifted.demand[:48])
        self.assertTrue((shifted.demand[48:] < ordinary.demand[48:]).all())
        np.testing.assert_array_equal(ordinary.view, shifted.view)

    def test_paired_shocks_and_action_cutoff(self):
        obs, _, shocks, checkpoints = simulate(1000)
        original = checkpoints[24].copy()
        shock_copy = shocks.view.copy()
        histories, outcomes = paired_scenario(obs, shocks, checkpoints[24], 24)
        histories_again, outcomes_again = paired_scenario(obs, shocks, checkpoints[24], 24)
        np.testing.assert_array_equal(histories, histories_again)
        np.testing.assert_array_equal(outcomes, outcomes_again)
        np.testing.assert_array_equal(histories[0, :-1], histories[1, :-1])
        np.testing.assert_array_equal(histories[0, -1, :-1], histories[1, -1, :-1])
        self.assertEqual(histories[1, -1, -1], np.float32(0.05))
        np.testing.assert_array_equal(checkpoints[24].prices, original.prices)
        np.testing.assert_array_equal(shocks.view, shock_copy)
        for _ in range(2):
            market = checkpoints[24].copy()
            _, sales = step(market, shocks, 24, 0)
            self.assertEqual(len(sales), outcomes[0, 0])


if __name__ == "__main__":
    unittest.main()
