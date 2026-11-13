"""Summarize local publisher snapshots without fitting models or exporting raw values."""

import argparse
import calendar
import csv
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile


ATTENTION = "page_view_count_per_property_vs_us"
PERIODS = {
    "pre_shift": ("2018-01", "2021-12"),
    "shift": ("2022-01", "2023-12"),
    "post_shift": ("2024-01", "2026-09"),
    "later_test": ("2025-04", "2026-09"),
}


def rows(path, encoding="utf-8-sig"):
    with path.open(encoding=encoding, newline="") as source:
        yield from csv.DictReader(source)


def observed(raw):
    if raw.strip() in {"", ".", "NA", "NaN", "NULL"}:
        return False
    value = float(raw)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"Invalid observation {raw!r}")
    return True


def insert(data, key, value):
    if key in data:
        raise ValueError(f"Duplicate key {key}")
    data[key] = value


def month_range(first, last):
    start_year, start_month = map(int, first.split("-"))
    end_year, end_month = map(int, last.split("-"))
    return [
        f"{year:04d}-{month + 1:02d}"
        for year, month in (
            divmod(i, 12)
            for i in range(12 * start_year + start_month - 1, 12 * end_year + end_month)
        )
    ]


def coverage(keys, present):
    if not present:
        raise ValueError("No observed values")
    ids, months = map(set, zip(*keys))
    observed_ids, observed_months = map(set, zip(*present))
    return {
        "ids": len(ids),
        "ids_observed": len(observed_ids),
        "first": min(observed_months),
        "last": max(observed_months),
        "observed": len(present),
        "missing_cells": len(keys) - len(present),
        "absent_keys": len(ids) * len(month_range(min(months), max(months))) - len(keys),
    }


def read_attention(path):
    data = {}
    for row in rows(path):
        period = row["month_date_yyyymm"]
        if not re.fullmatch(r"[0-9]{6}", period):
            raise ValueError(f"Invalid Realtor month {period!r}")
        month = date(int(period[:4]), int(period[4:]), 1).isoformat()[:7]
        code, flag = row["cbsa_code"], row["quality_flag"]
        if not re.fullmatch(r"[0-9]{5}", code) or flag not in {"0", "1"}:
            raise ValueError(f"Invalid Realtor key or quality flag for {code}, {month}")
        insert(data, (code, month), (observed(row[ATTENTION]), flag == "1"))
    return data


def read_zillow(path):
    data, regions = {}, {}
    for row in rows(path):
        if row["RegionType"] == "country":
            continue
        if row["RegionType"] != "msa":
            raise ValueError(f"Unexpected Zillow region type {row['RegionType']}")
        region = row["RegionID"]
        insert(regions, region, row["RegionName"])
        for column, value in row.items():
            if column in {"RegionID", "SizeRank", "RegionName", "RegionType", "StateName"}:
                continue
            day = date.fromisoformat(column)
            if day.day != calendar.monthrange(day.year, day.month)[1]:
                raise ValueError(f"Zillow date is not a month end: {column}")
            insert(data, (region, column[:7]), observed(value))
    return data, regions


def omb_metros(path):
    """Read CBSA, area type and county FIPS columns from the July 2023 workbook."""
    with ZipFile(path) as workbook:
        shared = [
            "".join(node.itertext())
            for node in ElementTree.fromstring(workbook.read("xl/sharedStrings.xml"))
        ]
        sheet = ElementTree.fromstring(workbook.read("xl/worksheets/sheet1.xml"))

    counties = defaultdict(set)
    for row in sheet.findall(".//{*}row"):
        cells = {}
        for cell in row.findall("{*}c"):
            value = cell.findtext("{*}v")
            if value is not None:
                column = cell.attrib["r"].rstrip("0123456789")
                cells[column] = shared[int(value)] if cell.get("t") == "s" else value
        if cells.get("E") == "Metropolitan Statistical Area":
            counties[cells["A"]].add(cells["J"].zfill(2) + cells["K"].zfill(3))
    if not counties:
        raise ValueError("No metropolitan county delineations in the Census workbook")
    return counties


def crosswalk(path, pending_ids, attention_ids, omb):
    codes, counties, reverse = defaultdict(set), defaultdict(set), defaultdict(set)
    for row in rows(path, encoding="cp1252"):
        region, code = row["MetroRegionID_Zillow"], row["CBSACode"]
        if region == "NULL" and code == "NULL":
            continue
        if not region.isdecimal() or not re.fullmatch(r"[0-9]{5}", code):
            raise ValueError(f"Invalid Zillow crosswalk row for {region}, {code}")
        codes[region].add(code)
        counties[region].add(row["FIPS"].zfill(5))
        reverse[code].add(region)

    candidates, screened, exclusions = {}, {}, Counter()
    for region in sorted(pending_ids):
        if region not in codes:
            exclusions["no_legacy_mapping"] += 1
            continue
        if len(codes[region]) != 1:
            exclusions["ambiguous_mapping"] += 1
            continue
        code = next(iter(codes[region]))
        if len(reverse[code]) != 1:
            exclusions["ambiguous_mapping"] += 1
        elif code not in attention_ids:
            exclusions["no_attention_code"] += 1
        else:
            candidates[region] = code
            if code not in omb:
                exclusions["not_2023_omb_msa"] += 1
            elif counties[region] != omb[code]:
                exclusions["county_set_differs"] += 1
            else:
                screened[region] = code
    return candidates, screened, exclusions


def read_rates(path):
    weekly = {}
    for row in rows(path):
        day = date.fromisoformat(row["observation_date"])
        insert(weekly, day, observed(row["MORTGAGE30US"]))
    return weekly


def overlap(mapping, zillow, attention, rate_months):
    pending = zillow["pending"]
    months = {month for _, month in attention} & {month for _, month in pending}
    possible = {(region, month) for region in mapping for month in months}
    attention_ok = {key for key in possible if attention.get((mapping[key[0]], key[1]), (False, False))[0]}
    pending_ok = {key for key in possible if pending.get(key, False)}
    pair = attention_ok & pending_ok
    clean = {key for key in pair if not attention[(mapping[key[0]], key[1])][1]}
    controls = {
        key for key in clean
        if key[1] in rate_months and all(zillow[name].get(key, False) for name in ("inventory", "price"))
    }
    monthly_counts = Counter(month for _, month in clean)
    return {
        "possible": len(possible),
        "missing_attention": len(possible - attention_ok),
        "missing_pending": len(possible - pending_ok),
        "both_observed": coverage(possible, pair),
        "flagged_pairs": len(pair - clean),
        "unflagged_pairs": len(clean),
        "unflagged_with_controls": len(controls),
        "missing_control_among_unflagged": {
            name: sum(not zillow[name].get(key, False) for key in clean)
            for name in ("inventory", "price")
        } | {"rate": sum(month not in rate_months for _, month in clean)},
        "unflagged_metros_per_month": [
            min(monthly_counts[month] for month in months),
            max(monthly_counts[month] for month in months),
        ],
        "clean_by_period": {
            name: sum(first <= month <= last for _, month in clean)
            for name, (first, last) in PERIODS.items()
        },
        "complete_unflagged_metros": sum(
            count == len(months) for count in Counter(region for region, _ in clean).values()
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, help="Directory of snapshots named as in DATA_AUDIT.md")
    inputs = parser.parse_args().inputs

    names = ("pending", "inventory", "price")
    files = {name: inputs / f"{name}.csv" for name in (*names, "realtor", "rate", "zillow-crosswalk")}
    files["omb2023"] = inputs / "omb2023.xlsx"
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in files.items()}
    attention = read_attention(files["realtor"])
    omb = omb_metros(files["omb2023"])
    zillow, regions = {}, {}
    for name in names:
        zillow[name], regions[name] = read_zillow(files[name])
    weekly = read_rates(files["rate"])
    rate_months = {day.isoformat()[:7] for day, present in weekly.items() if present}
    candidates, screened, exclusions = crosswalk(
        files["zillow-crosswalk"], regions["pending"], {code for code, _ in attention}, omb
    )
    result = {
        "sha256": hashes,
        "attention": coverage(attention, {key for key, (present, _) in attention.items() if present}),
        "attention_quality_flags": sum(flagged for _, flagged in attention.values()),
        "attention_ids_without_legacy_pending_match": len({code for code, _ in attention} - set(candidates.values())),
        "omb_2023_msa_count": len(omb),
        "zillow": {
            name: coverage(values, {key for key, present in values.items() if present})
            for name, values in zillow.items()
        },
        "rate": {
            "first": min(day for day, present in weekly.items() if present).isoformat(),
            "last": max(day for day, present in weekly.items() if present).isoformat(),
            "observed_weeks": sum(weekly.values()),
            "missing_weeks": len(weekly) - sum(weekly.values()),
        },
        "legacy_code_join": overlap(candidates, zillow, attention, rate_months),
        "county_screened_join": overlap(screened, zillow, attention, rate_months),
        "pending_region_exclusions": exclusions,
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
