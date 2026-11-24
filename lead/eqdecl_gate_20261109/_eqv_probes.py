# -*- coding: utf-8 -*-
# _eqv_probes.py — 可疑行上下文探查（只读）
import importlib.util, json, pathlib, re

HERE = pathlib.Path(r"D:/Project/ra2-campaign-forge/lead/eqdecl_gate_20261109")
ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
spec = importlib.util.spec_from_file_location("_eq_detector_theirs", HERE / "_eq_detector.py")
eq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eq)

def show(rel, a, b):
    p = ROOT / rel
    lines = p.read_bytes().decode("utf-8", errors="replace").split("\n")
    print(f"----- {rel}:{a}-{b}")
    for n in range(a, b + 1):
        if 1 <= n <= len(lines):
            print(f"{n}\t{lines[n-1]}")

def which(rel, ln, pats_map):
    p = ROOT / rel
    lines = p.read_bytes().decode("utf-8", errors="replace").split("\n")
    for n in range(ln - 2, ln + 3):
        if 1 <= n <= len(lines):
            hits = eq._hits(lines[n - 1], [q for ps in pats_map.values() for q in ps])
            if hits:
                print(f"  {rel}:{n} hits={hits}")

UNIV = eq.UNIVERSAL_CLAIM
INTENS = eq.INTENSITY
print("=== LI:223 为什么 F3？局部 ±2 行的 UNIVERSAL_CLAIM / INTENSITY 命中 ===")
show("lead/layer_identity_20261109/LAYER_IDENTITY.md", 220, 226)
which("lead/layer_identity_20261109/LAYER_IDENTITY.md", 223, {"UNIVERSAL_CLAIM": UNIV, "INTENSITY": INTENS})

print("\n=== LI:242 F1 的窗口内 E_EQ_STRICT 命中 ===")
show("lead/layer_identity_20261109/LAYER_IDENTITY.md", 238, 246)
w = eq._hits("\n".join((ROOT / "lead/layer_identity_20261109/LAYER_IDENTITY.md").read_bytes().decode("utf-8", errors="replace").split("\n")[233:250]), eq.E_EQ_STRICT)
print("  window E_EQ_STRICT hits:", w)

print("\n=== LI:52（输出回显行被 F1）===")
show("lead/layer_identity_20261109/LAYER_IDENTITY.md", 48, 56)

print("\n=== METRIC:21 空表头 F1 窗口 ===")
show("lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 19, 29)

print("\n=== KEFF:430-443（:432/434/440 整改清单语境）===")
show("lead/keff_calc_20261109/KEFF_CALC.md", 428, 444)

print("\n=== _ma:77 ===")
show("lead/metric_audit_20261109/_ma_METRIC_AUDIT.md", 74, 79)

print("\n=== LI:336-340（:338 F3 语境）===")
show("lead/layer_identity_20261109/LAYER_IDENTITY.md", 336, 340)

print("\n=== M1c 声称 GOAL_THREE_TARGETS_20261018.md:9200 含 ⇔ ===")
gl = (ROOT / "lead/GOAL_THREE_TARGETS_20261018.md").read_bytes().decode("utf-8", errors="replace").split("\n")
print("  n_lines =", len(gl))
for n in (9199, 9200, 9201):
    if n <= len(gl):
        print(f"  :{n}\t{gl[n-1][:160]}")

print("\n=== 台账两件中被他们的形态表命中会怎样？（仅为上下文参照，不在 full run 范围）===")
for rel in ("lead/GOAL_THREE_TARGETS_20261018.md", "lead/PENDING_DECISIONS.md"):
    t = (ROOT / rel).read_bytes().decode("utf-8", errors="replace")
    n_hengid = len(re.findall(r"恒等", t))
    print(f"  {rel}: 「恒等」出现 {n_hengid} 次（TAUTOLOGY_AUDIT.md:609 自记 GOAL 46 行）")
