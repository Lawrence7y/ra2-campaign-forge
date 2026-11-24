from pathlib import Path
import hashlib
import sys

root = Path(sys.argv[1])
if not root.is_absolute():
    raise SystemExit("repository argument must be an absolute path")

expected = {
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md": ("c364467dea909da66bca16b98d12d1d625edb80dfbf831ea9e8a1077e9dad24c", 27225),
    "lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md": ("5b933fe2fcb3cc35c5026cb57b45f29da29c90b67a618346af248744ed3ccdb9", 32281),
    "lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md": ("e0c00683fb23b0b3777d71639f3d7d265208057969073e53fd2b7195d0c3e1f7", 28648),
    "lead/p11_stations_20261108/P11_STATION_NAMING.md": ("d328e4f99d428daf86047ca420d0c84668d4827865ec62296904f467f9ee4b9e", 24636),
    "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md": ("c0dfb0d17edab4d0d89c43dc48bce4b84354fd13bd89cae7277aa15e82cf65f2", 54351),
    "lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md": ("7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0", 29619),
    "lead/d13d14_cards_20261108/DECISION_QUESTIONS.md": ("0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f", 27172),
    "lead/direction_ruling_20261108/RULING_DIRECTION.md": ("0ebd68dd11a2a54a33e30c6c658d12656fb1af77f14ef4c5724f829d3d90c653", 16514),
    "lead/n9_erratum_20261108/N9_SPEC_ERRATUM.md": ("61446db581a273725010e9b09cf3ebeba0d1412fc8666c0c6b8c660e4f7d22b4", 20630),
}
extra_expected = {
    "lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md": ("20e4eeac49254b274a8382e94505525a614ec5bf24ccb89316fcd8f914406262", 26485),
    "ra2youli/gamemd.exe": ("73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476", 4825360),
}
additional = [
    "lead/n10c04_ruling_20261108/_ro_RULING_N10C04_Q3.md",
    "lead/re_line_20261105/W8_STATIC_LOCATE/F7_TARGETING.md",
    "lead/re_line_20261105/W8_STATIC_LOCATE/F8_VISIBILITY.md",
    "lead/re_line_20261105/D24_RULING/RULING_D24.md",
]
all_ok = True
for rel in [*expected, *extra_expected, *additional]:
    data = (root / rel).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    actual = (digest, len(data))
    reference = expected.get(rel, extra_expected.get(rel))
    matched = actual == reference if reference is not None else None
    if matched is False:
        all_ok = False
    print(f"FILE {rel} | SHA256={digest} | bytes={len(data)} | lines={len(data.splitlines())} | MATCH={matched}")
    if rel.endswith("_ro_RULING_N10C04_Q3.md"):
        print(f"被核对象 SHA256 = {digest}，字节数 = {len(data)}")
print(f"ORCHESTRATOR_MATCHED={sum((hashlib.sha256((root / rel).read_bytes()).hexdigest(), (root / rel).stat().st_size) == ref for rel, ref in expected.items())}/{len(expected)}")
print(f"ALL_EXPECTED_MATCH={all_ok}")

lead = root / "lead"
names = [entry.name for entry in lead.iterdir()]
print("CURRENT_N10C04_ENTRIES=" + repr(sorted(name for name in names if name.casefold().startswith("n10c04"))))
proposals = [
    "n10c04_q3_t1_p11_residue_20261108",
    "n10c04_q3_t2_p6_input_chain_20261108",
    "n10c04_q3_t3_s4_mix_decomp_20261108",
    "n10c04_q3_t4_s1_phase_uptrace_20261108",
]
for name in proposals:
    path = lead / name
    folded = [entry for entry in names if entry.casefold() == name.casefold()]
    print(f"PROPOSED lead/{name}/ | exists={path.exists()} | is_dir={path.is_dir()} | casefold_matches={folded}")
for name in ["p11_stations_20261108", "n9_erratum_20261108", "spec_static_closure_20261108", "n10c04_ruling_20261108"]:
    path = lead / name
    print(f"EXISTING lead/{name}/ | is_dir={path.is_dir()} | files={sorted(child.name for child in path.iterdir())}")

raise SystemExit(0 if all_ok else 1)
