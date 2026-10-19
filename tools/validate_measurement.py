#!/usr/bin/env python3
"""
validate_measurement.py - IMPL001-PERF Real Workload Metadata Validator

Implements specification in:
out/re_work/work_chain/IMPL001/perf/control/spec/measurement_contract.md

集成信息（PERF-INT01-IMPL）:
- 原型路径: out/re_work/work_chain/IMPL001/perf/worker/validate_measurement.py
- 集成路径: tools/validate_measurement.py
- 改动: 仅文件头注释；算法、schema、退出码语义与原版保持一致。
"""

import argparse
import json
import math
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SHA256_REGEX = re.compile(r"^[0-9a-fA-F]{64}$")
VALID_TARGET_EXES = ("game.exe", "gamemd.exe")
SCHEMA_VERSION_EXPECTED = 1
NOTE_MESSAGE = (
    "元数据校验通过不代表输入数据真实；"
    "declared_units 仅为地图名义负载，不生成实际单位数；"
    "各 run 保持独立，不合并曲线、不宣称收益。"
)


def is_strict_int(val: Any) -> bool:
    """Check if value is an integer and not a boolean."""
    return isinstance(val, int) and not isinstance(val, bool)


def compute_run_stats(index: int, run_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute statistical metrics for a single run according to §5 of measurement_contract.md.
    - Ascending sort of tick_ms without interpolation.
    - Median: odd -> (n+1)/2 (1-based); even -> arithmetic mean of middle two elements.
    - Nearest-rank percentile: rank = ceil(p/100 * n) (1-based) clipped to [1, n].
    - Retain original precision (JSON number).
    """
    ticks = run_dict["tick_ms"]
    sorted_ticks = sorted(ticks)
    n = len(sorted_ticks)

    # Median
    if n % 2 == 1:
        median = sorted_ticks[(n + 1) // 2 - 1]
    else:
        v1 = sorted_ticks[n // 2 - 1]
        v2 = sorted_ticks[n // 2]
        if is_strict_int(v1) and is_strict_int(v2) and (v1 + v2) % 2 == 0:
            median = (v1 + v2) // 2
        else:
            median = (v1 + v2) / 2.0

    # Nearest-rank P95 and P99
    rank_p95 = min(max(math.ceil(0.95 * n), 1), n)
    p95 = sorted_ticks[rank_p95 - 1]

    rank_p99 = min(max(math.ceil(0.99 * n), 1), n)
    p99 = sorted_ticks[rank_p99 - 1]

    actual_units = run_dict["actual_units"]
    declared_units = run_dict.get("declared_units")

    return {
        "index": index,
        "actual_units": actual_units,
        "declared_units": declared_units,
        "samples": n,
        "median": median,
        "p95": p95,
        "p99": p99,
        "percentile_method": "nearest-rank",
        "median_method": "odd->middle, even->mean of two middle",
    }


def validate_data(data: Any) -> Tuple[bool, List[Dict[str, str]], List[Dict[str, Any]]]:
    """
    Validate data against specification.
    Returns: (is_valid, errors, run_stats)
    """
    errors: List[Dict[str, str]] = []
    run_stats: List[Dict[str, Any]] = []

    if not isinstance(data, dict):
        errors.append({
            "path": "root",
            "message": f"Top-level JSON value must be an object (dict), got {type(data).__name__}",
        })
        return False, errors, run_stats

    # 1. schema_version
    if "schema_version" not in data:
        errors.append({
            "path": "schema_version",
            "message": "Field 'schema_version' is required",
        })
    else:
        sv = data["schema_version"]
        if not is_strict_int(sv):
            errors.append({
                "path": "schema_version",
                "message": f"Field 'schema_version' must be an integer (boolean not allowed), got {type(sv).__name__}",
            })
        elif sv != SCHEMA_VERSION_EXPECTED:
            errors.append({
                "path": "schema_version",
                "message": f"Field 'schema_version' must equal {SCHEMA_VERSION_EXPECTED}, got {sv}",
            })

    # 2. target_exe
    if "target_exe" not in data:
        errors.append({
            "path": "target_exe",
            "message": "Field 'target_exe' is required",
        })
    else:
        te = data["target_exe"]
        if not isinstance(te, str) or te not in VALID_TARGET_EXES:
            errors.append({
                "path": "target_exe",
                "message": f"Field 'target_exe' must be one of {list(VALID_TARGET_EXES)}, got {te!r}",
            })

    # 3. exe_sha256
    if "exe_sha256" not in data:
        errors.append({
            "path": "exe_sha256",
            "message": "Field 'exe_sha256' is required",
        })
    else:
        h = data["exe_sha256"]
        if not isinstance(h, str) or not SHA256_REGEX.fullmatch(h):
            errors.append({
                "path": "exe_sha256",
                "message": f"Field 'exe_sha256' must be a 64-character hexadecimal SHA256 string, got {h!r}",
            })

    # 4. config_sha256
    if "config_sha256" not in data:
        errors.append({
            "path": "config_sha256",
            "message": "Field 'config_sha256' is required",
        })
    else:
        h = data["config_sha256"]
        if not isinstance(h, str) or not SHA256_REGEX.fullmatch(h):
            errors.append({
                "path": "config_sha256",
                "message": f"Field 'config_sha256' must be a 64-character hexadecimal SHA256 string, got {h!r}",
            })

    # 5. map_sha256
    if "map_sha256" not in data:
        errors.append({
            "path": "map_sha256",
            "message": "Field 'map_sha256' is required",
        })
    else:
        h = data["map_sha256"]
        if not isinstance(h, str) or not SHA256_REGEX.fullmatch(h):
            errors.append({
                "path": "map_sha256",
                "message": f"Field 'map_sha256' must be a 64-character hexadecimal SHA256 string, got {h!r}",
            })

    # 6. hardware
    if "hardware" not in data:
        errors.append({
            "path": "hardware",
            "message": "Field 'hardware' is required",
        })
    else:
        hw = data["hardware"]
        if not isinstance(hw, str) or len(hw.strip()) == 0:
            errors.append({
                "path": "hardware",
                "message": "Field 'hardware' must be a non-empty string after stripping whitespace",
            })

    # 7. scenario
    if "scenario" not in data:
        errors.append({
            "path": "scenario",
            "message": "Field 'scenario' is required",
        })
    else:
        sc = data["scenario"]
        if not isinstance(sc, str) or len(sc.strip()) == 0:
            errors.append({
                "path": "scenario",
                "message": "Field 'scenario' must be a non-empty string after stripping whitespace",
            })

    # 8. runs
    runs_valid_container = True
    if "runs" not in data:
        errors.append({
            "path": "runs",
            "message": "Field 'runs' is required",
        })
        runs_valid_container = False
    else:
        runs = data["runs"]
        if not isinstance(runs, list):
            errors.append({
                "path": "runs",
                "message": f"Field 'runs' must be an array, got {type(runs).__name__}",
            })
            runs_valid_container = False
        else:
            if len(runs) < 3:
                errors.append({
                    "path": "runs",
                    "message": f"Field 'runs' must contain at least 3 runs, got {len(runs)}",
                })

    # Validate each run if runs is a list
    if runs_valid_container:
        runs = data["runs"]
        for i, run in enumerate(runs):
            if not isinstance(run, dict):
                errors.append({
                    "path": f"runs[{i}]",
                    "message": f"Run item at index {i} must be an object, got {type(run).__name__}",
                })
                continue

            # actual_units
            if "actual_units" not in run:
                errors.append({
                    "path": f"runs[{i}].actual_units",
                    "message": "Field 'actual_units' is required",
                })
            else:
                au = run["actual_units"]
                if not is_strict_int(au) or au < 1:
                    errors.append({
                        "path": f"runs[{i}].actual_units",
                        "message": f"Field 'actual_units' must be a positive integer (>= 1, boolean not allowed), got {au!r}",
                    })

            # count_source
            if "count_source" not in run:
                errors.append({
                    "path": f"runs[{i}].count_source",
                    "message": "Field 'count_source' is required",
                })
            else:
                cs = run["count_source"]
                if not isinstance(cs, dict):
                    errors.append({
                        "path": f"runs[{i}].count_source",
                        "message": f"Field 'count_source' must be an object, got {type(cs).__name__}",
                    })
                else:
                    # count_source.kind
                    if "kind" not in cs:
                        errors.append({
                            "path": f"runs[{i}].count_source.kind",
                            "message": "Field 'count_source.kind' is required",
                        })
                    else:
                        kind = cs["kind"]
                        if not isinstance(kind, str) or kind != "runtime":
                            errors.append({
                                "path": f"runs[{i}].count_source.kind",
                                "message": f"Field 'count_source.kind' must equal 'runtime', got {kind!r}",
                            })

                    # count_source.evidence
                    if "evidence" not in cs:
                        errors.append({
                            "path": f"runs[{i}].count_source.evidence",
                            "message": "Field 'count_source.evidence' is required",
                        })
                    else:
                        ev = cs["evidence"]
                        if not isinstance(ev, str) or len(ev.strip()) == 0:
                            errors.append({
                                "path": f"runs[{i}].count_source.evidence",
                                "message": "Field 'count_source.evidence' must be a non-empty string after stripping whitespace",
                            })

            # tick_ms
            if "tick_ms" not in run:
                errors.append({
                    "path": f"runs[{i}].tick_ms",
                    "message": "Field 'tick_ms' is required",
                })
            else:
                tms = run["tick_ms"]
                if not isinstance(tms, list):
                    errors.append({
                        "path": f"runs[{i}].tick_ms",
                        "message": f"Field 'tick_ms' must be an array, got {type(tms).__name__}",
                    })
                elif len(tms) == 0:
                    errors.append({
                        "path": f"runs[{i}].tick_ms",
                        "message": "Field 'tick_ms' must be a non-empty array",
                    })
                else:
                    for j, tv in enumerate(tms):
                        if isinstance(tv, bool):
                            errors.append({
                                "path": f"runs[{i}].tick_ms[{j}]",
                                "message": f"Element at tick_ms[{j}] must not be a boolean, got {tv!r}",
                            })
                        elif not isinstance(tv, (int, float)):
                            errors.append({
                                "path": f"runs[{i}].tick_ms[{j}]",
                                "message": f"Element at tick_ms[{j}] must be a number, got {type(tv).__name__}",
                            })
                        elif not math.isfinite(tv):
                            errors.append({
                                "path": f"runs[{i}].tick_ms[{j}]",
                                "message": f"Element at tick_ms[{j}] must be a finite number, got {tv!r}",
                            })
                        elif tv <= 0:
                            errors.append({
                                "path": f"runs[{i}].tick_ms[{j}]",
                                "message": f"Element at tick_ms[{j}] must be strictly positive (> 0), got {tv!r}",
                            })

            # declared_units (optional)
            if "declared_units" in run:
                du = run["declared_units"]
                if not is_strict_int(du) or du < 1:
                    errors.append({
                        "path": f"runs[{i}].declared_units",
                        "message": f"Field 'declared_units' if present must be a positive integer (>= 1, boolean not allowed), got {du!r}",
                    })

    if errors:
        return False, errors, []

    # If valid, compute stats for each run
    for i, run in enumerate(data["runs"]):
        run_stats.append(compute_run_stats(i, run))

    return True, [], run_stats


def format_human_readable(data: Dict[str, Any], run_stats: List[Dict[str, Any]]) -> str:
    lines = [
        f"[OK] schema_version={data['schema_version']} target_exe={data['target_exe']} runs={len(data['runs'])}"
    ]
    for st in run_stats:
        decl = st["declared_units"] if st["declared_units"] is not None else "absent"
        lines.append(
            f"run[{st['index']}]: actual_units={st['actual_units']} "
            f"samples={st['samples']} median={st['median']} "
            f"p95={st['p95']} p99={st['p99']} declared_units={decl}"
        )
    lines.append(f"NOTE: {NOTE_MESSAGE}")
    return "\n".join(lines)


def format_human_readable_fail(errors: List[Dict[str, str]]) -> str:
    lines = [f"[FAIL] {len(errors)} 个字段错误"]
    for err in errors:
        lines.append(f" - {err['path']}: {err['message']}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate measurement metadata according to IMPL001-PERF contract v1."
    )
    parser.add_argument("input_file", help="Path to input JSON measurement file")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    args = parser.parse_args()

    # Read and parse file
    if not os.path.exists(args.input_file):
        sys.stderr.write(f"Error: File '{args.input_file}' not found.\n")
        sys.exit(2)

    try:
        with open(args.input_file, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except OSError as e:
        sys.stderr.write(f"Error: Unable to read file '{args.input_file}': {e}\n")
        sys.exit(2)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Error: JSON syntax error in '{args.input_file}': {e}\n")
        sys.exit(2)

    is_valid, errors, run_stats = validate_data(data)

    if is_valid:
        if args.json:
            out = {
                "valid": True,
                "errors": [],
                "schema_version": data["schema_version"],
                "target_exe": data["target_exe"],
                "run_count": len(data["runs"]),
                "runs": run_stats,
                "notes": [NOTE_MESSAGE],
            }
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            print(format_human_readable(data, run_stats))
        sys.exit(0)
    else:
        if args.json:
            out = {
                "valid": False,
                "errors": errors,
            }
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            print(format_human_readable_fail(errors))
        sys.exit(1)


if __name__ == "__main__":
    main()
