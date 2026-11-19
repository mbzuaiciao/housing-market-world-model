"""Run the single frozen EXP-002 configuration on a local CPU."""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torch import nn

from simulator import FEATURES, HORIZONS, SPLITS, examples, paired_scenario, simulate


HERE = Path(__file__).resolve().parent


def interval(world_values):
    """Resample independent worlds, preserving all within-world dependence."""
    values = np.asarray(world_values)
    rng = np.random.default_rng(19)
    indices = rng.integers(0, len(values), (2000, len(values)))
    draws = values[indices].mean(axis=1)
    return np.quantile(draws, [0.025, 0.975], axis=0).T.tolist()


def summarize(world_values):
    values = np.asarray(world_values)
    return {"mean": values.mean(axis=0).tolist(), "ci95": interval(values),
            "per_world": values.tolist()}


def signs(values):
    return np.where(np.abs(values) <= 1e-6, 0, np.sign(values))


class GRU(nn.Module):
    def __init__(self):
        super().__init__()
        self.recurrent = nn.GRU(len(FEATURES), 12, batch_first=True)
        self.head = nn.Linear(12, 2)

    def forward(self, history):
        _, state = self.recurrent(history)
        return self.head(state[-1])


def dataset(seeds, shifted=False):
    worlds = []
    for seed in seeds:
        observations, counts, _, _ = simulate(seed, shifted)
        worlds.append(examples(observations, counts))
    return worlds


def oracle_scenarios():
    features, effects, cumulative = [], [], []
    for seed in SPLITS["ordinary"]:
        obs, _, shocks, checkpoints = simulate(seed)
        world_features, world_effects, world_cumulative = [], [], []
        for week in (24, 48, 72):
            histories, counts = paired_scenario(obs, shocks, checkpoints[week], week)
            world_features.append(histories)
            world_effects.append((counts[1] - counts[0])[[0, 2]])
            world_cumulative.append(int(counts[1].sum() - counts[0].sum()))
        features.append(world_features)
        effects.append(world_effects)
        cumulative.append(world_cumulative)
    return np.array(features), np.array(effects), np.array(cumulative)


def fit_models(train):
    x = np.concatenate([world[0] for world in train])
    y = np.concatenate([world[1] for world in train])
    x_mean, x_scale = x.mean(axis=(0, 1)), x.std(axis=(0, 1))
    y_mean, y_scale = y.mean(axis=0), y.std(axis=0)
    x_scale[x_scale == 0] = 1
    y_scale[y_scale == 0] = 1
    standardized_x = (x - x_mean) / x_scale
    standardized_y = (y - y_mean) / y_scale

    design = standardized_x.reshape(len(x), -1).astype(np.float64)
    # Explicit intercept centering also handles nonzero means at individual lags.
    design_mean, target_mean = design.mean(axis=0), standardized_y.mean(axis=0)
    centered = design - design_mean
    weights = np.linalg.solve(
        centered.T @ centered / len(x) + 0.1 * np.eye(design.shape[1]),
        centered.T @ (standardized_y - target_mean) / len(x),
    )
    intercept = target_mean - design_mean @ weights

    model = GRU().cpu()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.003)
    train_x = torch.from_numpy(standardized_x)
    train_y = torch.from_numpy(standardized_y)
    losses = []
    model.train()
    for _ in range(30):
        total = 0
        for start in range(0, len(x), 128):
            optimizer.zero_grad()
            target = train_y[start:start + 128]
            loss = nn.functional.mse_loss(model(train_x[start:start + 128]), target)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1)
            optimizer.step()
            total += loss.item() * len(target)
        losses.append(total / len(x))
    model.eval()

    def predict(history):
        history = np.asarray(history, dtype=np.float32)
        scaled = (history - x_mean) / x_scale
        ridge = scaled.reshape(len(history), -1) @ weights + intercept
        with torch.no_grad():
            recurrent = model(torch.from_numpy(scaled)).numpy()
        return {
            "persistence": np.repeat(history[:, -1, 3:4], 2, axis=1),
            "ridge": np.maximum(0, ridge * y_scale + y_mean),
            "gru": np.maximum(0, recurrent * y_scale + y_mean),
        }

    return predict, {
        "training_examples": len(x), "gru_parameters": sum(p.numel() for p in model.parameters()),
        "ridge_parameters": weights.size + intercept.size,
        "gru_epoch_mse_standardized": losses,
        "input_mean": x_mean.tolist(), "input_scale": x_scale.tolist(),
        "target_mean": y_mean.tolist(), "target_scale": y_scale.tolist(),
    }


def forecast_metrics(worlds, predict):
    errors = {name: [] for name in ("persistence", "ridge", "gru")}
    for x, y in worlds:
        predictions = predict(x)
        for name in errors:
            errors[name].append(np.abs(predictions[name] - y).mean(axis=0))
    metrics = {name: summarize(values) for name, values in errors.items()}
    metrics["gru_vs_reference"] = {}
    for name in ("persistence", "ridge"):
        gru, baseline = np.array(errors["gru"]), np.array(errors[name])
        metrics["gru_vs_reference"][name] = {
            "paired_mae_difference": summarize(gru - baseline),
            "percent_improvement": (100 * (1 - gru.mean(axis=0) / baseline.mean(axis=0))).tolist(),
        }
    return metrics


def intervention_metrics(features, oracle, predict):
    shape = features.shape
    predictions = predict(features.reshape(-1, shape[-2], shape[-1]))
    metrics, errors = {}, {}
    for name, values in predictions.items():
        paired = values.reshape(shape[0], shape[1], 2, 2)
        effects = paired[:, :, 1] - paired[:, :, 0]
        errors[name] = np.abs(effects - oracle).mean(axis=1)
        metrics[name] = {
            "predicted_effect": summarize(effects.mean(axis=1)),
            "effect_mae": summarize(errors[name]),
            "bias": summarize((effects - oracle).mean(axis=1)),
            "sign_accuracy": summarize((signs(effects) == signs(oracle)).mean(axis=1)),
            "scenario_effects": effects.tolist(),
        }
    metrics["gru_paired_mae_difference"] = {
        name: summarize(errors["gru"] - errors[name]) for name in ("persistence", "ridge")
    }
    return metrics


def run():
    started = time.perf_counter()
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(7)
    np.random.seed(7)
    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(HERE), "-v"],
        capture_output=True, text=True, check=True,
    )
    print(tests.stderr, flush=True)
    features, oracle, cumulative = oracle_scenarios()
    oracle_summary = summarize(oracle.mean(axis=1))
    cumulative_summary = summarize(cumulative.mean(axis=1))
    gate = oracle_summary["mean"][0] > 0 and oracle_summary["ci95"][0][0] >= 0
    result = {
        "protocol_commit": subprocess.check_output(
            ["git", "log", "-1", "--format=%H", "--", str(HERE / "PROTOCOL.md")], text=True
        ).strip(),
        "source_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(HERE.iterdir()) if path.suffix == ".py" or path.name == "PROTOCOL.md"
        },
        "environment": {
            "python": platform.python_version(), "numpy": np.__version__, "torch": torch.__version__,
            "platform": platform.platform(), "device": "cpu", "threads": 1,
        },
        "configuration": {
            "world_seeds": SPLITS, "weeks": 96, "history": 12, "features": FEATURES,
            "horizons": HORIZONS, "ridge_penalty": 0.1, "gru_hidden": 12,
            "epochs": 30, "learning_rate": 0.003, "batch_size": 128,
            "training_seed": 7, "bootstrap_seed": 19, "bootstrap_draws": 2000,
            "intervention_checkpoints": [24, 48, 72],
        },
        "oracle": {
            "gate_passed": bool(gate), "effect": oracle_summary,
            "cumulative_three_week_effect": cumulative_summary,
            "scenario_effects": oracle.tolist(), "scenario_cumulative_effects": cumulative.tolist(),
            "zero_effect_scenarios": (oracle == 0).sum(axis=(0, 1)).tolist(),
        },
        "tests": tests.stderr.strip(),
    }
    print("Oracle gate:", result["oracle"], flush=True)
    if gate:
        predict, fit = fit_models(dataset(SPLITS["train"]))
        result["fit"] = fit
        result["forecasts"] = {
            split: forecast_metrics(dataset(SPLITS[split], split == "shifted"), predict)
            for split in ("validation", "ordinary", "shifted")
        }
        result["interventions"] = intervention_metrics(features, oracle, predict)
        ordinary = result["forecasts"]["ordinary"]
        stronger = np.minimum(ordinary["persistence"]["mean"], ordinary["ridge"]["mean"])
        improvement = 100 * (1 - np.array(ordinary["gru"]["mean"]) / stronger)
        result["decision"] = {
            "forecast": "GO" if improvement[1] >= 5 and improvement[0] >= -5 else "NO-GO",
            "stronger_simple_baseline": [
                min(("persistence", "ridge"), key=lambda name: ordinary[name]["mean"][h])
                for h in range(2)
            ],
            "percent_improvement_vs_stronger_simple": improvement.tolist(),
            "positive_intervention_finding": bool(all(
                np.all(np.array(result["interventions"]["gru_paired_mae_difference"][name]["ci95"])[:, 1] < 0)
                for name in ("persistence", "ridge")
            )),
        }
    else:
        result["decision"] = {"forecast": "NO-GO", "reason": "Simulator oracle sanity gate failed"}
    result["elapsed_seconds"] = time.perf_counter() - started
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "results.json")
    args = parser.parse_args()
    output = run()
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"decision": output["decision"], "elapsed_seconds": output["elapsed_seconds"]}, indent=2))
