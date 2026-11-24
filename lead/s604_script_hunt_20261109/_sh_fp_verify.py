# _sh_fp_verify.py — 只读指纹核验（S604 脚本穷搜轮，2026-11-09）
# 零写入（除本写域输出件）；全部 hashlib 自算。
import os, sys, time, hashlib

REPO = r"D:\Project\ra2-campaign-forge"
OUTP = os.path.join(REPO, "lead", "s604_script_hunt_20261109", "_sh_fp_out.txt")

# 编排方交付指纹（六件）
EXPECTED = {
    "lead/s604_script_gap_20261109/S604_SCRIPT_GAP.md": (
        "593c7a3ed3b1d1d47d6da5d8277f76c9323499aa04084a86e376ab5f9d2ab740", 20271),
    "lead/s604_exclusive_20261109/S604_EXCLUSIVITY.md": (
        "823476680c4c7aab7ead279a3f47724dbd1b2fed977087ae86c35a4eef36258c", 30536),
    "lead/s604_attribution_20261108/S604_ATTRIBUTION.md": (
        "8e9a606752ce2fd4c3d279ba5bb4a54eba99bc83f8974921f3f5601aa1008237", 27182),
    "lead/slowframe_r3_20261108/S604_GAP_RECHECK.md": (
        "5d1b0ecc9f0e21ddecc38584c363afa0c758f40089ccc57749f237aeffbdf726", 19291),
    "lead/GOAL_THREE_TARGETS_20261018.md": (
        "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    "lead/PENDING_DECISIONS.md": (
        "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
}

# 候选残迹（R1/R2 命中 + R5 异常件）——只算指纹与 mtime，不预设期望值
CANDIDATES = [
    "lead/slowframe_r3_20261108/_r3_recompute_gapdiff.py",
    "lead/slowframe_r3_20261108/_s604_delta_check.py",
    "lead/slowframe_r3_20261108/_s604_fp_check.py",
    "lead/slowframe_r3_20261108/_verify_r3_gapdiff.py",
    "out/re_work/qc/W2_20261001/forge/scripts/echgap_diff.py",
    "lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md",
    "lead/s604_attribution_20261108/_sa_ATTRIBUTION_S604.md",
    "lead/o1prime_reach_20261109/_o1v_tmp/_o1v_out_is_file",
    "lead/w2_samecause_20261109/_w2v_case/outfile_as_outdir",
]

def mt(p):
    st = os.stat(p)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))

lines = []
def emit(s=""):
    lines.append(s)
    print(s)

emit("== [1] 编排方六件指纹核验 ==")
bind = None
for rel, (esha, ebytes) in EXPECTED.items():
    p = os.path.join(REPO, rel)
    try:
        with open(p, "rb") as f:
            b = f.read()
    except OSError as ex:
        emit(f"{rel} : READ-ERR {ex}")
        continue
    h = hashlib.sha256(b).hexdigest()
    ok = (h == esha) and (len(b) == ebytes)
    emit(f"{rel} | sha256={h} | bytes={len(b)} | expect_bytes={ebytes} | MATCH={ok} | mtime={mt(p)}")
    if rel.endswith("S604_SCRIPT_GAP.md"):
        bind = (h, len(b), ok)

emit()
emit("== [2] 候选残迹指纹与 mtime ==")
for rel in CANDIDATES:
    p = os.path.join(REPO, rel)
    try:
        with open(p, "rb") as f:
            b = f.read()
    except OSError as ex:
        emit(f"{rel} : READ-ERR {ex}")
        continue
    h = hashlib.sha256(b).hexdigest()
    emit(f"{rel} | sha256={h} | bytes={len(b)} | mtime={mt(p)}")

emit()
emit("== [3] 仓库根异常未跟踪件 ==")
for nm in ("GLM", "Qwen", "_tmp_pending_new.md"):
    p = os.path.join(REPO, nm)
    if os.path.isdir(p):
        try:
            ents = os.listdir(p)
            emit(f"{nm} : DIR entries={len(ents)} first10={ents[:10]}")
        except OSError as ex:
            emit(f"{nm} : DIR-LIST-ERR {ex}")
    elif os.path.isfile(p):
        with open(p, "rb") as f:
            b = f.read()
        emit(f"{nm} : FILE sha256={hashlib.sha256(b).hexdigest()} bytes={len(b)} mtime={mt(p)}")
        emit(f"  head200={b[:200]!r}")
    else:
        emit(f"{nm} : MISSING")
step_files = [x for x in os.listdir(REPO) if x.startswith("Step")]
for nm in step_files:
    p = os.path.join(REPO, nm)
    if os.path.isfile(p):
        with open(p, "rb") as f:
            b = f.read()
        emit(f"{nm!r} : FILE sha256={hashlib.sha256(b).hexdigest()} bytes={len(b)} mtime={mt(p)}")
        emit(f"  head200={b[:200]!r}")
    else:
        emit(f"{nm!r} : DIR? isdir={os.path.isdir(p)}")

emit()
if bind:
    h, n, ok = bind
    emit("== [4] 被核对象绑定行（自算值原样输出） ==")
    emit(f"被核对象 SHA256 = {h}，字节数 = {n}")
    emit(f"(与编排方指纹比对 MATCH={ok})")

with open(OUTP, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(f"\n[out] {OUTP}")
