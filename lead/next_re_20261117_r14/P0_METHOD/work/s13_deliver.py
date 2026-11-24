"""S13 · 交付：CHANNELS.tsv / TIERS.tsv / EVIDENCE 抽样（每档 ≥10 行，带字节证据）/ 正负对照。"""
import json
import os
import pickle
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p0m_common import ATLAS, CARD, EVIDENCE, HERE, RESIDUAL_ADJ, load_lines, norm_addr
import s3_channels as s3

img = s3.img
md = s3.md
chan = pickle.load(open(os.path.join(HERE, "channels.pkl"), "rb"))
fin = pickle.load(open(os.path.join(HERE, "final.pkl"), "rb"))
F_pool, F_rand, F_init = fin["F_pool"], fin["F_rand"], fin["F_init"]
num = json.load(open(os.path.join(EVIDENCE, "s12_final.json"), encoding="utf-8"))
A_call, A_jmp, B, C, JCC = chan["A_call"], chan["A_jmp"], chan["B"], chan["C"], chan["jcc"]

T = {k: [f for f in F_pool if f["tier"] == k] for k in ("T1", "T2", "T3")}

# ---------------------------------------------------------------- CHANNELS.tsv
def mk(name, desc, p_hit, r_hit, rand_note="", verdict_override=None):
    p, r = p_hit / len(F_pool) * 100, r_hit / len(F_rand) * 100
    enr = (p / r) if r > 0 else None
    if enr is None:
        verdict = "UNDEFINED（随机侧 0 命中）"
    elif enr < 1:
        verdict = "无区分力（反富集 %.2f×）" % enr
    elif enr < 2:
        verdict = "无区分力（%.2f× < 2）" % enr
    else:
        verdict = "有区分力（%.2f×）" % enr
    if verdict_override:
        verdict = verdict_override
    return [name, desc, str(p_hit), "%.2f%%" % p, str(r_hit), "%.2f%%" % r,
            ("%.2f" % enr) if enr is not None else "n/a", verdict, rand_note]


rows = [
    mk("A_call", "指令边界 E8 call rel32 目标", num["pool_hits"]["A_call"], num["random_hits"]["A_call"]),
    mk("A_jmp", "指令边界 E9 jmp rel32 目标（§8.1② 不得直当真入口）",
       num["pool_hits"]["A_jmp"], num["random_hits"]["A_jmp"],
       "随机侧仅 1 例（0.10%），比值 4.19× 无统计意义，不可据此判有区分力",
       verdict_override="不可判（随机侧 n=1，倍数不可用）"),
    mk("A_any", "A_call ∪ A_jmp", sum(1 for f in F_pool if f["A_call"] or f["A_jmp"]),
       sum(1 for f in F_rand if f["A_call"] or f["A_jmp"])),
    mk("B", "自写 RTTI 定界的虚表槽值（1214 表 / 14044 槽）",
       num["pool_hits"]["B"], num["random_hits"]["B"]),
    mk("C", ".data 4B 初值指向该地址（全部）", num["pool_hits"]["C"], num["random_hits"]["C"]),
    mk("C_FN", "C 精化：函数指针表形态（剔除跳表）",
       num["pool_hits"]["C_ok"], num["random_hits"]["C_ok"]),
    mk("D1", "硬边界：前驱 ret/retf/int3/hlt/ud2，可隔 ≤15B 90/CC padding（不含 jmp）",
       num["pool_hits"]["d1"], num["random_hits"]["d1"], "池=建池条件邻近形态，见 PROGRESS §5"),
    mk("D2", "体自洽：≥2 指令、≤4096B 到 ret、无 jmp-out",
       num["pool_hits"]["d2"], num["random_hits"]["d2"]),
    mk("D", "D1 ∧ D2（卡面通道 D）", num["pool_hits"]["d"], num["random_hits"]["d"]),
]
with open(os.path.join(CARD, "CHANNELS.tsv"), "w", encoding="utf-8") as f:
    f.write("channel\tdescription\tpool_hits(1,669)\tpool_rate\trandom_hits(1,000)\trandom_rate\tenrichment\tverdict\tnote\n")
    for r in rows:
        f.write("\t".join(r) + "\n")

# ---------------------------------------------------------------- TIERS.tsv
tiers = [
    ("T1", len(T["T1"]), "A_call ∨ B ∨ C_FN：有独立外部证据（指令边界 call 目标 / RTTI 虚表槽 / 函数指针表项）指向该地址", "可判 FUNC"),
    ("T2", len(T["T2"]), "仅结构证据（D1 硬边界 ∧ D2 体自洽，或 padding 后接 jmp / 尾跳桩 / 裸 ret）：**疑似入口，不得判 FUNC**", "不可裁（疑似）"),
    ("T3", len(T["T3"]), "¬bnd ∨ 是指令边界 jcc 的目的地（体内标签）∨ 前驱非终止符且顺流可达：**可判 NOT_FUNC**", "可判 NOT_FUNC"),
]
with open(os.path.join(CARD, "TIERS.tsv"), "w", encoding="utf-8") as f:
    f.write("tier\trows\tcriterion\tdecidable\n")
    for t in tiers:
        f.write("%s\t%d\t%s\t%s\n" % t)

# ---------------------------------------------------------------- 抽样证据
jcc_sites = {}
code = img.read(img.text_start, img.text["raw_size"])
for insn in md.disasm(code, img.text_start):
    if insn.address >= img.text_end:
        break
    if insn.id and insn.mnemonic.startswith("j") and insn.mnemonic != "jmp" and insn.operands \
            and insn.operands[0].type == 2:
        jcc_sites.setdefault(insn.operands[0].imm & 0xFFFFFFFF, []).append(
            (insn.address, insn.mnemonic))


def prev_line(va):
    r = s3.insn_ending_at(va)
    if r is None:
        return "(非指令边界)", ""
    mn = s3._mnemonic(r[0], r[1])
    return "%08X %s" % (r[0], mn), img.bytes_hex(r[0], r[1])


def sample(rows_, k, step=None):
    if not rows_:
        return []
    if len(rows_) <= k:
        return rows_
    if step is None:
        step = max(1, len(rows_) // k)
    out = [rows_[i] for i in range(0, min(len(rows_), k * step), step)][:k]
    return out


def emit(path, title, rows_, reason_fn, k=12):
    with open(os.path.join(EVIDENCE, path), "w", encoding="utf-8") as f:
        f.write("# %s\n" % title)
        f.write("# address\tprev_insn\tprev_bytes\thex_16B\td1/pad\td2\tC_kind\treason\n")
        for f_ in sample(rows_, k):
            va = f_["va"]
            pl, pb = prev_line(va)
            f.write("%08X\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                va, pl, pb, img.bytes_hex(va, 16),
                "%d/%d" % (int(f_["d1"]), f_["pad"]), f_["d2_why"],
                f_["C_kind"], reason_fn(f_)))


emit("samples_T1.tsv", "T1 可判 FUNC（全部 %d 行，含 7 个被降级的 C_LABEL 供对照）" % len(T["T1"]),
     T["T1"] + [f for f in F_pool if f["C"] and not f["C_ok"]],
     lambda f: "C_FN slot=%s run=%s L=%d cov=%.2f%%" % (
         f["C_detail"].get("slot"), f["C_detail"].get("run"), f["C_detail"].get("L", 0),
         f["C_detail"].get("pct_cov", 0)) if f["C_ok"] else
     "【降级依据】C_LABEL: run=%s L=%d cov=%.2f%% aligned=%.2f%%" % (
         f["C_detail"].get("run"), f["C_detail"].get("L", 0),
         f["C_detail"].get("pct_cov", 0), f["C_detail"].get("pct_aligned", 0)),
     k=20)


def t2_reason(f):
    if f["d1"] and f["d2"]:
        return "D1∧D2 成立，无 A/B/C 正证据 ⇒ 仅疑似"
    if f["d1"] and f["d2_why"] == "jmp_out":
        return "硬边界 + 尾跳桩（thunk 形态，按契约是入口）⇒ 仅疑似"
    if f["d1"] and f["d2_why"] == "single_insn_ret":
        return "硬边界 + 裸 ret（可能是极短函数或共享尾声）⇒ 仅疑似"
    if f["pad_jmp"]:
        return "padding 后接 jmp（建池条件弱形态）⇒ 仅疑似"
    return "D1/d2=%s/%s ⇒ 仅疑似" % (int(f["d1"]), f["d2_why"])


emit("samples_T2.tsv", "T2 疑似入口（%d 行中确定性等距抽 12）" % len(T["T2"]), T["T2"], t2_reason, k=12)


def t3_reason(f):
    if f["jcc"]:
        sites = jcc_sites.get(f["va"], [])
        if sites:
            s = min(sites, key=lambda x: abs(x[0] - f["va"]))
            return "jcc 目的（%08X %s，距 %d B）⇒ 函数体内标签" % (s[0], s[1], abs(s[0] - f["va"]))
        return "jcc 目的 ⇒ 函数体内标签"
    return "前驱 %s 非终止符且顺流可达 ⇒ 非入口" % f["prev_mn"]


emit("samples_T3.tsv", "T3 可判 NOT_FUNC（%d 行中确定性等距抽 12）" % len(T["T3"]), T["T3"], t3_reason, k=12)

# ---------------------------------------------------------------- 正负对照（重做：不挑命中者，按地址确定性取）
atlas = sorted({int(norm_addr(ln.split("\t")[0]), 16) for ln in load_lines(ATLAS)[1:] if ln.strip()})
pos_a = atlas[:5]                                    # 地址最低的 5 个 atlas 入口（不预筛）
pos_b = [v for v in atlas if v in B][:5]              # 5 个"确实是虚表槽"的 atlas 入口

neg = []
for ln in load_lines(RESIDUAL_ADJ)[1:]:
    p = ln.split("\t")
    if len(p) >= 4 and p[2].strip() == "NOT_FUNC" and "internal" in p[3].strip().lower():
        neg.append(int(norm_addr(p[0]), 16))
neg = sorted(set(neg))[:5]


def ctl(kind, va):
    d = s3.chan_d(va)
    return dict(kind=kind, va="%08X" % va, A_call=int(va in A_call), A_jmp=int(va in A_jmp),
                B=int(va in B), C=int(va in C), D1=int(d["d1"]), D2=int(d["d2"]),
                D=int(d["d"]), bytes=img.bytes_hex(va, 12))


ctrl = [ctl("POS_atlas_low5", v) for v in pos_a] + [ctl("POS_atlas_vtslot5", v) for v in pos_b] + \
       [ctl("NEG_residual_notfunc5", v) for v in neg]
with open(os.path.join(EVIDENCE, "controls.tsv"), "w", encoding="utf-8") as f:
    f.write("kind\taddress\tA_call\tA_jmp\tB\tC\tD1\tD2\tD\tbytes12\n")
    for c in ctrl:
        f.write("\t".join(str(c[k]) for k in
                          ("kind", "va", "A_call", "A_jmp", "B", "C", "D1", "D2", "D", "bytes")) + "\n")

summ = dict(
    pos_atlas_low5_AB_or_C=sum(1 for c in ctrl if c["kind"] == "POS_atlas_low5" and (c["A_call"] or c["B"] or c["C"])),
    pos_atlas_vtslot5_AB_or_C=sum(1 for c in ctrl if c["kind"] == "POS_atlas_vtslot5" and (c["A_call"] or c["B"] or c["C"])),
    neg_notfunc5_no_ABC=sum(1 for c in ctrl if c["kind"] == "NEG_residual_notfunc5" and not (c["A_call"] or c["B"] or c["C"])),
)
json.dump(summ, open(os.path.join(EVIDENCE, "controls_summary.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print(json.dumps(summ, ensure_ascii=False, indent=2))
print(open(os.path.join(EVIDENCE, "controls.tsv"), encoding="utf-8").read())
