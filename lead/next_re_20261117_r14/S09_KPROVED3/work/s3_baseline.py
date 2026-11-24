"""S09-KPROVED3 step 3: D-42 ③b strict/loose base rate, same-subsystem random-8 baseline."""
from __future__ import annotations

import csv
import json
import random
import re

import k3lib as k

EV = k.OUT / "EVIDENCE"
CLS = k.BASE / "lead" / "next_re_20261117_r14" / "SURVEY_RING24" / "EVIDENCE" / "classification.tsv"

HEX = re.compile(r"0x([0-9A-Fa-f]+)")
STORE = re.compile(r"^mov\s+(?:byte|word|dword)\s+ptr\s+\[[^\]]+\]")


def is_jcc(ins) -> bool:
    return ins.mnemonic.startswith("j") and ins.mnemonic != "jmp"


def block_calls(insns, start: int, steps: int = 18):
    seq = [i for i in insns if start <= i.address < start + 0x100][:steps]
    out = []
    for i in seq:
        if i.mnemonic == "call" and i.op_str.startswith("0x"):
            out.append(int(i.op_str, 16))
    return tuple(out)


def block_ends_ret(insns, start: int, steps: int = 18) -> bool:
    seq = [i for i in insns if start <= i.address < start + 0x100][:steps]
    return any(i.mnemonic.startswith("ret") for i in seq)


def store_disp(ins) -> int | None:
    if not STORE.match(ins.op_str):
        return None
    m = HEX.findall(ins.op_str)
    return int(m[-1], 16) if m else None


def detect(entry: int):
    lo, hi, insns = k.cfg_extent(entry)
    sorted_ins = sorted(insns, key=lambda i: i.address)
    addrs = [i.address for i in sorted_ins]
    addr_set = set(addrs)

    # strict hard conditions
    jmp_table = False
    for i in sorted_ins:
        if i.mnemonic == "jmp" and "[" in i.op_str:
            nums = HEX.findall(i.op_str)
            if nums:
                tab = int(nums[-1], 16)
                vals = [k.u32(tab + 4 * n) for n in range(8)]
                if sum(1 for v in vals if k.is_text(v)) >= 3:
                    jmp_table = True

    bounded_loop = False
    for i in sorted_ins:
        if not is_jcc(i) and i.mnemonic != "jmp":
            continue
        tgt = k.imm_target(i)
        if tgt is None or tgt > i.address or tgt not in addr_set:
            continue
        body = [x for x in sorted_ins if tgt <= x.address <= i.address]
        has_read = any(x.mnemonic == "mov" and "[" in x.op_str and not STORE.match(x.op_str) for x in body)
        has_write = any(STORE.match(x.op_str) for x in body)
        has_advance = any(
            x.mnemonic in ("inc", "dec", "add", "sub") and x.op_str.split(",")[0].strip() in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp")
            for x in body
        )
        if is_jcc(i) and has_read and has_write and has_advance:
            bounded_loop = True

    error_return = False
    # A: cmp reg,-1/0 followed by setcc into al/dl then ret (falsifiable return convention)
    for idx, i in enumerate(sorted_ins):
        if i.mnemonic == "cmp" and i.op_str.endswith(", -1"):
            for j in sorted_ins[idx + 1 : idx + 5]:
                if j.mnemonic.startswith("set") and j.op_str in ("al", "dl"):
                    if any(x.mnemonic.startswith("ret") for x in sorted_ins[idx + 1 : idx + 9]):
                        error_return = True
    # B: call -> test/cmp eax -> jcc to a small block that returns eax=0
    for idx, i in enumerate(sorted_ins):
        if i.mnemonic != "call" or not i.op_str.startswith("0x"):
            continue
        for j in sorted_ins[idx + 1 : idx + 5]:
            if j.mnemonic in ("cmp", "test") and "eax" in j.op_str:
                for t in sorted_ins[idx + 1 : idx + 8]:
                    if not is_jcc(t):
                        continue
                    tgt = k.imm_target(t)
                    if tgt not in addr_set:
                        continue
                    blk = [x for x in sorted_ins if tgt <= x.address < tgt + 0x40][:8]
                    if any(x.mnemonic == "xor" and x.op_str == "eax, eax" for x in blk) and any(
                        x.mnemonic.startswith("ret") for x in blk
                    ):
                        error_return = True

    field_disp = set()
    vt_writes = 0
    for i in sorted_ins:
        d = store_disp(i)
        if d is not None and d >= 0:
            field_disp.add(d)
        if i.mnemonic == "mov" and "dword ptr [" in i.op_str and "," in i.op_str:
            rhs = i.op_str.split(",", 1)[1].strip()
            if rhs.startswith("0x") and k.u32(int(rhs, 16)) in {t["vt"] for t in TABLES}:
                vt_writes += 1
    memory_shape = len(field_disp) >= 10 or vt_writes >= 2

    # strict linearized switch: same compared register, >=3 distinct jccs, >=3 distinct branch call sets
    groups = {}
    for idx, i in enumerate(sorted_ins):
        if i.mnemonic != "cmp":
            continue
        parts = [p.strip() for p in i.op_str.split(",")]
        if len(parts) != 2 or parts[0] not in ("eax", "ebx", "ecx", "edx", "esi", "edi", "ebp"):
            continue
        jcc = None
        for j in sorted_ins[idx + 1 : idx + 4]:
            if is_jcc(j):
                jcc = j
                break
        if jcc is None:
            continue
        tgt = k.imm_target(jcc)
        if tgt is None or tgt not in addr_set:
            continue
        groups.setdefault(parts[0], []).append((parts[1], block_calls(sorted_ins, tgt)))
    linear_switch = any(
        len(v) >= 3
        and len({second for second, _ in v}) >= 3
        and len({calls for _, calls in v if calls}) >= 3
        for v in groups.values()
    )

    # loose-only guard chain: >=3 conditional branches to terminal blocks with distinct direct-call actions
    sigs = []
    for i in sorted_ins:
        if not is_jcc(i):
            continue
        tgt = k.imm_target(i)
        if tgt is None or tgt not in addr_set or not block_ends_ret(sorted_ins, tgt):
            continue
        calls = block_calls(sorted_ins, tgt)
        if calls:
            sigs.append(calls[:3])
    guard_chain = len(set(sigs)) >= 3

    strict = jmp_table or bounded_loop or error_return or memory_shape or linear_switch
    loose = strict or guard_chain
    return {
        "lo": lo,
        "hi": hi,
        "jmp_table": int(jmp_table),
        "loop": int(bounded_loop),
        "error_return": int(error_return),
        "memory_shape": int(memory_shape),
        "linear_switch": int(linear_switch),
        "guard_chain": int(guard_chain),
        "strict": int(strict),
        "loose": int(loose),
    }


TABLES = k.rtti_tables()
with CLS.open(encoding="utf-8") as f:
    pop = [r["entry"] for r in csv.DictReader(f, delimiter="\t") if r["subsystem"] == "S09"]

features = []
for es in pop:
    f = detect(int(es, 16))
    features.append([es] + [str(f[key]) for key in ("lo", "hi", "jmp_table", "loop", "error_return", "memory_shape", "linear_switch", "guard_chain", "strict", "loose")])

write_header = [
    "entry",
    "ext_lo",
    "ext_hi",
    "f_jump_table",
    "f_loop",
    "f_error_return",
    "f_memory_shape",
    "f_linear_switch",
    "f_guard_chain",
    "is_3b_strict",
    "is_3b_loose",
]
with (EV / "BASELINE_3B_FEATURES.tsv").open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, delimiter="\t", lineterminator="\n")
    w.writerow(write_header)
    w.writerows(features)

strict_set = {r[0] for r in features if r[9] == "1"}
loose_set = {r[0] for r in features if r[10] == "1"}
rng = random.Random(20261119)
N, S = 2000, 8
tot_s = tot_l = 0
for _ in range(N):
    sample = rng.sample(pop, S)
    tot_s += sum(e in strict_set for e in sample)
    tot_l += sum(e in loose_set for e in sample)

stats = {
    "card": "S09-KPROVED3",
    "predicate": "D-42 ③b",
    "subsystem": "S09",
    "population_rows": len(pop),
    "seed": 20261119,
    "iterations": N,
    "sample_size_per_trial": S,
    "strict_definition": "jump table OR bounded read/judge/write/advance loop OR falsifiable error/return convention OR memory-shape assertion OR single-variable linearized switch",
    "loose_definition": "strict OR >=3 mutually exclusive guard branches with distinct action signatures (D-42 细则#1 level)",
    "strict_population_hits": len(strict_set),
    "loose_population_hits": len(loose_set),
    "strict_base_rate": len(strict_set) / len(pop),
    "loose_base_rate": len(loose_set) / len(pop),
    "STRICT": {
        "total_hits": tot_s,
        "total_sampled_rows": N * S,
        "K_per_trial_avg": tot_s / N,
        "mean_per_row": tot_s / (N * S),
        "analytic_expected_K": S * len(strict_set) / len(pop),
    },
    "LOOSE": {
        "total_hits": tot_l,
        "total_sampled_rows": N * S,
        "K_per_trial_avg": tot_l / N,
        "mean_per_row": tot_l / (N * S),
        "analytic_expected_K": S * len(loose_set) / len(pop),
    },
    "note": "K = 8 × mean_per_row is an arithmetic identity, not an independent validation (L3); this baseline is the ③b base rate, not the ②∧④ selection rate.",
}
(EV / "BASELINE_3B.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
with (EV / "BASELINE_3B.txt").open("w", encoding="utf-8") as f:
    f.write("S09-KPROVED3 · D-42 ③b 基率（不是 ②∧④ 入选率）\n")
    f.write(f"population=S09 rows={len(pop)} seed=20261119 iters={N} sample={S}\n")
    f.write(stats["strict_definition"] + "\n")
    f.write(stats["loose_definition"] + "\n")
    f.write(f"strict: hits={len(strict_set)} base_rate={stats['strict_base_rate']:.6f} K={stats['STRICT']['K_per_trial_avg']:.4f} mean={stats['STRICT']['mean_per_row']:.6f}\n")
    f.write(f"loose : hits={len(loose_set)} base_rate={stats['loose_base_rate']:.6f} K={stats['LOOSE']['K_per_trial_avg']:.4f} mean={stats['LOOSE']['mean_per_row']:.6f}\n")
    f.write("K=8×均值 is identity, not a check.\n")

print(json.dumps(stats, indent=2, ensure_ascii=False))
