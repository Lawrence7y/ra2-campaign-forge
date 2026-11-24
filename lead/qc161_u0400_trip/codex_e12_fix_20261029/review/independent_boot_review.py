"""Offline E12 boot gate review. Never binds real operations or launches a game."""
import argparse
import importlib.util
import json
import os
import ast
import hashlib
import inspect
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    args = ap.parse_args()
    directory = Path(args.directory).resolve()
    sys.path.insert(0, str(directory))
    spec = importlib.util.spec_from_file_location("independent_fixture", directory / "_drive_c2_x_e12_selftest.py")
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    driver = fixture.D
    results = []

    def check(name, ok, evidence):
        results.append({"name": name, "ok": bool(ok), "evidence": evidence})
        print(json.dumps(results[-1], ensure_ascii=False, default=str), flush=True)

    def tripfail(fn, prefix):
        try:
            fn()
        except driver.V2.TripFail as exc:
            return str(exc).startswith(prefix)
        return False

    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in directory.glob("*.py")}
    print(json.dumps({"driver": str(driver.__file__), "hashes": hashes}, ensure_ascii=False), flush=True)
    # Fixture provides mocked OS actions. Both clock seams are independently supplied here.
    ops = fixture.make_ops("hang")
    state = ops["__st"]
    epoch = {"offset": 0, "correction": 0}
    ops["boot_ms"] = lambda: 200000 + int(state["t"] * 1000) - epoch["offset"]
    ops["wallclock_ms"] = lambda: 1800000000000 + int(state["t"] * 1000) + epoch["correction"]
    popen = ops["popen"]
    launches = []

    def launch(*a):
        launches.append(len(launches))
        return popen(*a)

    ops["popen"] = launch
    saved = fixture._install(ops, driver.V2)
    try:
        reference = driver.capture_boot()
        immutable = dict(reference)
        first = driver.run_trip(971, reference, watch_s=3.0)
        state.update(t=state["t"] + 137.0, launched=False, killed=False, t_close=None)
        second = driver.run_trip(972, reference, watch_s=3.0)
        check("actual_same_session_two_trips", first["verdict"] == second["verdict"] == "OK" and len(launches) == 2,
              {"verdicts": [first["verdict"], second["verdict"]], "fail": [first.get("fail"), second.get("fail")], "mock_launches": len(launches)})
        check("raw_uptime_and_immutable_reference", second["boot_ms_at_start"] > first["boot_ms_at_start"] and reference == immutable,
              {"uptime": [first["boot_ms_at_start"], second["boot_ms_at_start"]], "reference": reference})
        state.update(launched=False, killed=False, t_close=None)
        epoch["offset"] = int(state["t"] * 1000) + 199000  # reboot -> uptime = 1000ms
        third = driver.run_trip(973, reference, watch_s=3.0)
        check("actual_reboot_stops_before_launch", third["verdict"] == "FAIL" and third.get("fail", "").startswith("stop_condition:boot_changed_between_trips") and len(launches) == 2,
              {"verdict": third["verdict"], "fail": third.get("fail"), "mock_launches": len(launches)})
    finally:
        fixture._uninstall(saved)

    for delta in (-2001, -2000, -1999, 0, 1999, 2000, 2001):
        current = {"boot_ms": 999999, "boot_wallclock_ms": 12345678 + delta}
        reference = {"boot_ms": 1000, "boot_wallclock_ms": 12345678}
        blocked = tripfail(lambda: driver.assert_same_boot(current, reference), "stop_condition:boot_changed_between_trips")
        check("tolerance_%s" % delta, blocked == (abs(delta) > 2000), {"delta": delta, "blocked": blocked})

    function = inspect.getsource(driver.assert_same_boot)
    anchor = 'if abs(current["boot_wallclock_ms"] - reference["boot_wallclock_ms"]) > BOOT_TOLERANCE_MS:'
    if function.count(anchor) != 1:
        raise AssertionError("mutation anchor changed")
    for name, replacement in (("raw_uptime", 'if current["boot_ms"] != reference["boot_ms"]:'), ("deleted_check", "if False:")):
        ns = {"V2": driver.V2, "math": __import__("math"), "BOOT_TOLERANCE_MS": driver.BOOT_TOLERANCE_MS}
        exec(compile(function.replace(anchor, replacement), "independent_mutation_" + name, "exec"), ns)
        guard = ns["assert_same_boot"]
        same_blocked = tripfail(lambda: guard({"boot_ms": 120000, "boot_wallclock_ms": 10000}, {"boot_ms": 1000, "boot_wallclock_ms": 10000}), "stop_condition:boot_changed_between_trips")
        reboot_blocked = tripfail(lambda: guard({"boot_ms": 1000, "boot_wallclock_ms": 40000}, {"boot_ms": 1000, "boot_wallclock_ms": 10000}), "stop_condition:boot_changed_between_trips")
        check("mutation_" + name, (same_blocked, reboot_blocked) != (False, True), {"same_blocked": same_blocked, "reboot_blocked": reboot_blocked})

    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
    rejected = subprocess.run([sys.executable, "-B", str(directory / "_drive_c2_x_e12.py"), "--live"], env=env, capture_output=True, timeout=30)
    check("live_without_approval_rc3", rejected.returncode == 3, {"rc": rejected.returncode, "out": rejected.stdout.decode("utf-8", "replace")})
    # Copy-only tampering. Import must refuse before any real operations are bound.
    tamper_dir = Path(tempfile.mkdtemp(prefix="e12review_tamper_"))
    try:
        for name in ("_drive_c2_x_e12.py", "_drive_c2_x_probe_v2.py", "_drive_c2_x_earlyclose.py"):
            shutil.copy2(directory / name, tamper_dir / name)
        for master in ("_drive_c2_x_probe_v2.py", "_drive_c2_x_earlyclose.py"):
            target = tamper_dir / master
            original = target.read_bytes()
            target.write_bytes(original + b"\n# tampered copy\n")
            refused = subprocess.run([sys.executable, "-B", str(tamper_dir / "_drive_c2_x_e12.py")], env=env, capture_output=True, timeout=30)
            check("tampered_master_" + master, refused.returncode != 0 and b"RuntimeError" in refused.stderr,
                  {"rc": refused.returncode, "stderr": refused.stderr.decode("utf-8", "replace")[-800:]})
            target.write_bytes(original)
    finally:
        # All paths are under this process's independently created temporary directory.
        shutil.rmtree(tamper_dir)

    check("candidate_files_unchanged", all(hashlib.sha256((directory / p).read_bytes()).hexdigest() == h for p, h in hashes.items()), hashes)
    print(json.dumps({"total": len(results), "failed": sum(not x["ok"] for x in results)}, ensure_ascii=False), flush=True)
    shutil.rmtree(fixture._SANDBOX, ignore_errors=True)
    return 1 if any(not x["ok"] for x in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
