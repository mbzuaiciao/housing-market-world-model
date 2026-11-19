"""Fixed synthetic housing market for EXP-002. No fitted models live here."""

from dataclasses import dataclass, field
import numpy as np


WEEKS = 96
SLOTS = 80
BUYERS = 32
HISTORY = 12
HORIZONS = (1, 3)
SPLITS = {
    "train": tuple(range(100, 124)),
    "validation": tuple(range(300, 306)),
    "ordinary": tuple(range(1000, 1006)),
    "shifted": tuple(range(2000, 2006)),
}
FEATURES = ("previous_views", "pre_action_price", "inventory",
            "previous_sales", "previous_action", "current_action")


def sigmoid(value):
    return 1 / (1 + np.exp(-value))


@dataclass
class Shocks:
    demand: np.ndarray
    quality: np.ndarray
    asking_noise: np.ndarray
    arrival: np.ndarray
    budget: np.ndarray
    view: np.ndarray
    preference: np.ndarray
    offer: np.ndarray
    completion: np.ndarray
    actions: np.ndarray


def make_shocks(seed, shifted=False):
    rng = np.random.default_rng(seed)
    demand = np.empty(WEEKS)
    previous = rng.normal(0, 0.3)
    for week in range(WEEKS):
        previous = 0.85 * previous + rng.normal(0, 0.25)
        if shifted and week >= 48:
            previous -= 0.6
        demand[week] = previous
    return Shocks(
        demand=demand,
        quality=rng.uniform(0.85, 1.15, (WEEKS, SLOTS)),
        asking_noise=rng.normal(0, 5, (WEEKS, SLOTS)),
        arrival=rng.random((WEEKS, BUYERS)),
        budget=rng.uniform(85, 135, (WEEKS, BUYERS)),
        view=rng.random((WEEKS, BUYERS, SLOTS)),
        preference=rng.random((WEEKS, BUYERS, SLOTS)),
        offer=rng.random((WEEKS, BUYERS)),
        completion=rng.random((WEEKS, BUYERS)),
        actions=(rng.random(WEEKS) < 0.25).astype(float) * 0.05,
    )


@dataclass
class Market:
    active: np.ndarray = field(default_factory=lambda: np.zeros(SLOTS, dtype=bool))
    prices: np.ndarray = field(default_factory=lambda: np.zeros(SLOTS))
    qualities: np.ndarray = field(default_factory=lambda: np.ones(SLOTS))
    listing_ids: np.ndarray = field(default_factory=lambda: np.full(SLOTS, -1))
    next_id: int = 0
    previous_views: int = 0
    previous_sales: int = 0
    previous_action: float = 0

    def copy(self):
        return Market(self.active.copy(), self.prices.copy(), self.qualities.copy(),
                      self.listing_ids.copy(), self.next_id, self.previous_views,
                      self.previous_sales, self.previous_action)


def step(market, shocks, week, action=None):
    """Apply one week, returning cutoff features and evaluation-only sale records."""
    before = int(market.active.sum())
    new = np.flatnonzero(~market.active)[:6]
    market.active[new] = True
    market.qualities[new] = shocks.quality[week, new]
    market.prices[new] = np.maximum(
        50, 100 * market.qualities[new] + shocks.asking_noise[week, new]
    )
    market.listing_ids[new] = np.arange(market.next_id, market.next_id + len(new))
    market.next_id += len(new)

    action = shocks.actions[week] if action is None else action
    if action not in (0, 0.05):
        raise ValueError("EXP-002 permits only zero or 5% price reduction")
    row = np.array([
        market.previous_views,
        market.prices[market.active].mean() if market.active.any() else 0,
        market.active.sum(),
        market.previous_sales,
        market.previous_action,
        action,
    ], dtype=np.float32)
    market.prices[market.active] *= 1 - action
    demand = shocks.demand[week]
    views, sales = 0, []
    for buyer in range(BUYERS):
        if shocks.arrival[week, buyer] >= 0.8 * sigmoid(demand):
            continue
        view_probability = sigmoid(
            0.5 + demand - 4 * (market.prices / market.qualities - 100) / 100
        )
        viewed = market.active & (shocks.view[week, buyer] < view_probability)
        views += int(viewed.sum())
        budget = shocks.budget[week, buyer] + 8 * demand
        candidates = np.flatnonzero(viewed & (market.prices <= budget))
        if not len(candidates):
            continue
        utility = shocks.preference[week, buyer, candidates] - market.prices[candidates] / 200
        slot = candidates[np.argmax(utility)]
        if shocks.offer[week, buyer] < 0.65 and shocks.completion[week, buyer] < 0.8:
            assert market.active[slot] and market.prices[slot] <= budget
            sales.append((int(market.listing_ids[slot]), buyer,
                          float(market.prices[slot]), float(budget)))
            market.active[slot] = False

    assert before + len(new) - len(sales) == int(market.active.sum())
    assert len({sale[0] for sale in sales}) == len(sales)
    assert len({sale[1] for sale in sales}) == len(sales)
    market.previous_views = views
    market.previous_sales = len(sales)
    market.previous_action = action
    return row, sales


def simulate(seed, shifted=False):
    shocks = make_shocks(seed, shifted)
    market = Market()
    observations, counts, checkpoints = [], [], {}
    sold_ids = set()
    for week in range(WEEKS):
        if week in (24, 48, 72):
            checkpoints[week] = market.copy()
        row, sales = step(market, shocks, week)
        assert not (sold_ids & {sale[0] for sale in sales})
        sold_ids.update(sale[0] for sale in sales)
        observations.append(row)
        counts.append(len(sales))
    return np.array(observations), np.array(counts), shocks, checkpoints


def examples(observations, counts):
    """The only supervised data path. Current and future outcomes are labels only."""
    cutoffs = range(HISTORY - 1, WEEKS - 2)
    x = np.stack([observations[t - HISTORY + 1:t + 1] for t in cutoffs])
    y = np.array([[counts[t], counts[t + 2]] for t in cutoffs], dtype=np.float32)
    return x, y


def paired_scenario(observations, shocks, checkpoint, week):
    histories, outcomes = [], []
    for action in (0, 0.05):
        market = checkpoint.copy()
        current, sales = step(market, shocks, week, action)
        history = observations[week - HISTORY + 1:week + 1].copy()
        history[-1] = current
        counts = [len(sales)]
        for future in range(week + 1, week + 3):
            _, sales = step(market, shocks, future)
            counts.append(len(sales))
        histories.append(history)
        outcomes.append(counts)
    return np.array(histories), np.array(outcomes)
