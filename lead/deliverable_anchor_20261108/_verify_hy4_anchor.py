# -*- coding: utf-8 -*-
"""独立复核脚本：不导入、不调用审计员任何实现；全部 hashlib 实算 + 自行按行读取。
用法: python -I -X utf8 <绝对路径> <section>
section: fp | orch | table | agg | anchor | grep | lines1 | lines2
"""
import hashlib
import os
import sys

ROOT = "D:/Project/ra2-campaign-forge"
LEAD = os.path.join(ROOT, "lead")
WD = os.path.join(LEAD, "deliverable_anchor_20261108")
SPEC = os.path.join(WD, "_da_ANCHOR_AUDIT_AND_SPEC_20261108.md")
DOMAINS = [
    "a_residual_n1_20261108",
    "perf_repair_n11_20261108",
    "d13d14_cards_20261108",
    "matrix_binding_20261108",
    "slowframe_r3_20261108",
    "criteria_r3_verify_20261108",
    "deliverable_anchor_20261108",
]


def sha(p):
    with open(p, "rb") as f:
        b = f.read()
    return hashlib.sha256(b).hexdigest(), len(b), b


def R(p):
    return "lead/" + os.path.relpath(p, LEAD).replace("\\", "/")


def files_in(d):
    dd = os.path.join(LEAD, d)
    return [os.path.join(dd, n) for n in sorted(os.listdir(dd))
            if os.path.isfile(os.path.join(dd, n))]


def all_files():
    out = []
    for d in DOMAINS:
        out.extend(files_in(d))
    return out


# 任务书【编排方指纹】11 项（材料给定）
ORCH = {
    "lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md": ("1209ca4c8149722fffd1731a0f435637a2988a6e90993f87ef632eb4763b585e", 33431),
    "lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json": ("d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b", 27965),
    "lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md": ("7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0", 29619),
    "lead/perf_repair_n11_20261108/_n11_PERF_REPAIR_HANDOFF.md": ("cf73fd80edbc538cd7fa5f2f6b69a759f8c00eeac903153146d533dd74a73269", 22745),
    "lead/d13d14_cards_20261108/DECISION_QUESTIONS.md": ("0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f", 27172),
    "lead/d13d14_cards_20261108/_n10_D13D14_CARDS_20261108.md": ("8a36d60a98ab6f19d3bc5229952e0318f492c2091d0bdc3b58b7d83cd9a12a7c", 30122),
    "lead/matrix_binding_20261108/MATRIX_BINDING_FACTS.md": ("dbe00c859bb2627a4be930cdc4f9065ed371faa42eea7c92a015cf4495805f8b", 19663),
    "lead/slowframe_r3_20261108/S604_GAP_RECHECK.md": ("5d1b0ecc9f0e21ddecc38584c363afa0c758f40089ccc57749f237aeffbdf726", 19291),
    "lead/slowframe_r3_20261108/_r3_GAPDIFF_RECHECK.md": ("98cd612f63210182f1f6aa9f1c4d664e711d7616e79bc9805d450695a919cf6e", 11215),
    "lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md": ("bf426786db82c34dd6b6d21e3022678285e3e22f52dbdaa5085d85c3b6f8fbde", 22351),
    "lead/criteria_r3_verify_20261108/_r3_CLOSURE_VERIFY_20261108.md": ("80c472acf6a902fcf29c628e305aa57ba96df9d3cdc9dcd2f312378ba15200e9", 13597),
}

# 审计员 §3.1 表 16 行（材料给定，取前 8 位 + 字节数；个别给全值者用全值）
TABLE = {
    "lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md": ("1209ca4c8149722fffd1731a0f435637a2988a6e90993f87ef632eb4763b585e", 33431),
    "lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json": ("d847de88bb0c0c04290c877180a9c45c502df773ba297a36406bffecbe66796b", 27965),
    "lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md": ("7a617a43b32fc2e38c7e46ff9d436f903810ad9cae919fc0eb891a0f9f5796e0", 29619),
    "lead/perf_repair_n11_20261108/_n11_PERF_REPAIR_HANDOFF.md": ("cf73fd80edbc538cd7fa5f2f6b69a759f8c00eeac903153146d533dd74a73269", 22745),
    "lead/d13d14_cards_20261108/DECISION_QUESTIONS.md": ("0a709f2da12e0234cd94ff0baf521652e7d1aed6cfd04929b9728adbfd85bf5f", 27172),
    "lead/d13d14_cards_20261108/_n10_D13D14_CARDS_20261108.md": ("8a36d60a98ab6f19d3bc5229952e0318f492c2091d0bdc3b58b7d83cd9a12a7c", 30122),
    "lead/matrix_binding_20261108/MATRIX_BINDING_FACTS.md": ("dbe00c859bb2627a4be930cdc4f9065ed371faa42eea7c92a015cf4495805f8b", 19663),
    "lead/matrix_binding_20261108/_m_MATRIX_DIFF_20261108.md": ("aa6aa58f", 10077),
    "lead/matrix_binding_20261108/_m_CHAIN_VERIFY_20261108.md": ("636551f7", 7813),
    "lead/matrix_binding_20261108/_m_DECISION_POINTS_20261108.md": ("a8a7d2eb", 4939),
    "lead/matrix_binding_20261108/_m_rebuild.py": ("77c091d9", 8329),
    "lead/matrix_binding_20261108/_m_rebuild_out.txt": ("e768a2d3", 2199),
    "lead/slowframe_r3_20261108/S604_GAP_RECHECK.md": ("5d1b0ecc9f0e21ddecc38584c363afa0c758f40089ccc57749f237aeffbdf726", 19291),
    "lead/slowframe_r3_20261108/_r3_GAPDIFF_RECHECK.md": ("98cd612f63210182f1f6aa9f1c4d664e711d7616e79bc9805d450695a919cf6e", 11215),
    "lead/criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md": ("bf426786db82c34dd6b6d21e3022678285e3e22f52dbdaa5085d85c3b6f8fbde", 22351),
    "lead/criteria_r3_verify_20261108/_r3_CLOSURE_VERIFY_20261108.md": ("80c472acf6a902fcf29c628e305aa57ba96df9d3cdc9dcd2f312378ba15200e9", 13597),
}

CLAIM_FULL = "4ab44028140a878dcaf815b60debddcc5c0939334af6b27fdc4438aafe0376f9"
CLAIM_ANCHOR = "eba320ec7f74aba09b5568d138f284b70d60241fe94fac7ece763f6b4e2fc96b"
CLAIM_AGG = "524a98ca80b2bb8112a0e0c6b9a8608103964cebaf2168da59f49d7e0594cd4d"


def dump_lines(p, ranges):
    with open(p, "rb") as f:
        b = f.read()
    lines = b.split(b"\n")
    print("--- " + R(p) + " (total lines=" + str(len(lines)) + ") ---")
    for a, z in ranges:
        for i in range(a, min(z, len(lines)) + 1):
            txt = lines[i - 1].decode("utf-8", "replace")
            print("%s:%d|%s" % (R(p), i, txt))
        print("---")


def sec_fp():
    print("=== fp: 七目录逐件 hashlib 实算（绝对路径，rb 原样字节流） ===")
    for p in all_files():
        h, n, _ = sha(p)
        print("%s\t%s\t%d" % (R(p), h, n))


def sec_orch():
    print("=== orch: 任务书【编排方指纹】11 项逐位核对 ===")
    ok = 0
    for k, (h0, n0) in ORCH.items():
        h, n, _ = sha(os.path.join(ROOT, k.replace("/", os.sep)))
        v = "MATCH" if (h == h0 and n == n0) else "MISMATCH"
        if v == "MATCH":
            ok += 1
        print("%s\t%s\tcalc=%s/%d\tgiven=%s/%d" % (v, k, h, n, h0, n0))
    print("orch MATCH=%d/%d" % (ok, len(ORCH)))


def sec_table():
    print("=== table: 审计员 §3.1 表 16 行核对（全值或前8位+字节数） ===")
    ok = 0
    for k, (h0, n0) in TABLE.items():
        h, n, _ = sha(os.path.join(ROOT, k.replace("/", os.sep)))
        hit = (h == h0) if len(h0) == 64 else h.startswith(h0)
        v = "MATCH" if (hit and n == n0) else "MISMATCH"
        if v == "MATCH":
            ok += 1
        print("%s\t%s\tcalc=%s/%d\tclaim=%s/%d" % (v, k, h, n, h0, n0))
    print("table MATCH=%d/%d" % (ok, len(TABLE)))
    print("table row count =", len(TABLE))
    print("分类 5+1+11 声称 = 17 件；分类逐件列举实际 = 5+1+10 = 16 件")


def sec_agg():
    dd = os.path.join(LEAD, "matrix_binding_20261108")
    names = ["_m_CHAIN_VERIFY_20261108.md", "_m_DECISION_POINTS_20261108.md",
             "_m_MATRIX_DIFF_20261108.md", "_m_rebuild.py", "_m_rebuild_out.txt"]
    paths = [os.path.join(dd, n) for n in names]
    asc = sorted(names)
    print("=== agg: matrix 五件主产出拼接指纹独立复算 ===")
    for tag, order in [("file-name-asc", asc), ("file-name-desc", list(reversed(asc))),
                       ("table-order", ["_m_MATRIX_DIFF_20261108.md", "_m_CHAIN_VERIFY_20261108.md",
                                        "_m_DECISION_POINTS_20261108.md", "_m_rebuild.py", "_m_rebuild_out.txt"])]:
        buf = b""
        for n in order:
            with open(os.path.join(dd, n), "rb") as f:
                buf += f.read()
        h = hashlib.sha256(buf).hexdigest()
        print("%s\t%s\t%d bytes\tclaim=%s\t%s" % (tag, h, len(buf), CLAIM_AGG, "MATCH" if h == CLAIM_AGG else "MISMATCH"))
    for n in asc:
        h, b, _ = sha(os.path.join(dd, n))
        print("  part\t%s\t%s\t%d" % (n, h, b))


def sec_anchor():
    print("=== anchor: 规范件 R1 自锚独立实现（不调用 _da_anchor_selfcheck.py） ===")
    with open(SPEC, "rb") as f:
        raw = f.read()
    h_full = hashlib.sha256(raw).hexdigest()
    lines = raw.split(b"\n")
    hits = [(i + 1, l) for i, l in enumerate(lines) if l.startswith(b"DA-ANCHOR: sha256=")]
    print("full-file sha256 = %s" % h_full)
    print("full-file bytes  = %d" % len(raw))
    print("claim full-file  = %s -> %s" % (CLAIM_FULL, "MATCH" if h_full == CLAIM_FULL else "MISMATCH"))
    print("DA-ANCHOR line count = %d" % len(hits))
    for ln, l in hits:
        print("line %d | %s" % (ln, l.decode("utf-8", "replace")))
    if len(hits) != 1:
        print("anchor check = FAIL (not exactly one anchor line)")
        return
    ln, l = hits[0]
    field = l[18:82]
    nb = int(l[l.index(b"bytes=") + 6:l.index(b"bytes=") + 16], 10)
    canon = raw.replace(l, l[:18] + b"0" * 64 + l[82:], 1)
    h_canon = hashlib.sha256(canon).hexdigest()
    print("anchor line no = %d" % ln)
    print("sha256 field = %s" % field.decode())
    print("bytes field = %d ; len(raw) = %d ; equal = %s" % (nb, len(raw), nb == len(raw)))
    print("canon length = %d ; unchanged = %s" % (len(canon), len(canon) == len(raw)))
    print("canon sha256 = %s" % h_canon)
    print("claim anchor = %s -> %s" % (CLAIM_ANCHOR, "MATCH" if h_canon == CLAIM_ANCHOR else "MISMATCH"))
    print("field == canon sha256 -> %s" % (field.decode() == h_canon))
    print("full-file sha256 == anchor value -> %s" % (h_full == h_canon))


def grep_domain(d, needles):
    dd = os.path.join(LEAD, d)
    print("--- grep domain: %s ---" % d)
    for name in sorted(os.listdir(dd)):
        p = os.path.join(dd, name)
        if not os.path.isfile(p):
            continue
        with open(p, "rb") as f:
            data = f.read()
        low = data.lower()
        for tag, needle in needles:
            nb = needle.encode()
            idxs = []
            start = 0
            while True:
                j = low.find(nb.lower(), start)
                if j < 0:
                    break
                idxs.append(data[:j].count(b"\n") + 1)
                start = j + 1
            if idxs:
                print("  HIT\t%s\t%s:%s" % (tag, name, ",".join(str(x) for x in idxs)))
        # 被核对象行
        for i, l in enumerate(data.split(b"\n"), 1):
            if b"\xe8\xa2\xab\xe6\xa0\xb8\xe5\xaf\xb9\xe8\xb1\xa1 SHA256" in l:
                print("  BIND\t%s:%d|%s" % (name, i, l.decode("utf-8", "replace")))


def sec_grep():
    print("=== grep: 各写域内自身指纹前缀命中 + 「被核对象 SHA256」行清单（自行实现，不用 shell grep） ===")
    grep_domain("a_residual_n1_20261108", [
        ("r2-MD-self 1209ca4c", "1209ca4c"), ("r2-JSON-self d847de88", "d847de88"),
        ("r1-MD-old 3343cfbe", "3343cfbe"), ("r1-JSON-old 15e4731c", "15e4731c")])
    grep_domain("perf_repair_n11_20261108", [
        ("zhengben 7a617a43", "7a617a43"), ("caogao cf73fd80", "cf73fd80")])
    grep_domain("d13d14_cards_20261108", [
        ("zhengben 0a709f2d", "0a709f2d"), ("dengji 8a36d60a", "8a36d60a")])
    grep_domain("matrix_binding_20261108", [
        ("zhengben dbe00c85", "dbe00c85"), ("agg 524a98ca", "524a98ca")])
    grep_domain("slowframe_r3_20261108", [
        ("zhengben 5d1b0ecc", "5d1b0ecc"), ("gapdiff 98cd612f", "98cd612f")])
    grep_domain("criteria_r3_verify_20261108", [
        ("zhengben bf426786", "bf426786"), ("closure 80c472ac", "80c472ac"),
        ("hy4-old 0614af13", "0614af13"), ("hy4-now f38adf59", "f38adf59")])
    grep_domain("deliverable_anchor_20261108", [
        ("spec-full 4ab44028", "4ab44028"), ("spec-anchor eba320ec", "eba320ec")])


def sec_lines1():
    print("=== lines1: 实例一 N-1 / 实例二 N-11 关键行实读 ===")
    dump_lines(os.path.join(LEAD, "a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md"),
               [(1, 6), (25, 40), (124, 133), (155, 161)])
    dump_lines(os.path.join(LEAD, "a_residual_n1_20261108/ACCEPTANCE_RECORDS.json"),
               [(48, 55), (68, 73)])
    dump_lines(os.path.join(LEAD, "a_residual_n1_20261108/_n1_records_out.txt"), [(1, 12)])
    dump_lines(os.path.join(LEAD, "perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md"),
               [(1, 11), (113, 121), (129, 135), (186, 192)])
    dump_lines(os.path.join(LEAD, "perf_repair_n11_20261108/_n11_PERF_REPAIR_HANDOFF.md"),
               [(1, 11), (152, 158)])
    dump_lines(os.path.join(LEAD, "perf_repair_n11_20261108/_deliver_hash_post_out.txt"), [(1, 10)])


def sec_lines2():
    print("=== lines2: 实例三 N-10 / 全量盘点相关行实读 ===")
    dump_lines(os.path.join(LEAD, "d13d14_cards_20261108/DECISION_QUESTIONS.md"),
               [(1, 5), (16, 20), (30, 36), (126, 133)])
    dump_lines(os.path.join(LEAD, "d13d14_cards_20261108/_n10_D13D14_CARDS_20261108.md"),
               [(236, 243)])
    dump_lines(os.path.join(LEAD, "d13d14_cards_20261108/_n10_fingerprint_out.txt"), [(1, 10)])
    dump_lines(os.path.join(LEAD, "matrix_binding_20261108/MATRIX_BINDING_FACTS.md"), [(86, 92)])
    dump_lines(os.path.join(LEAD, "slowframe_r3_20261108/S604_GAP_RECHECK.md"), [(118, 123)])
    dump_lines(os.path.join(LEAD, "criteria_r3_verify_20261108/R2_BREAKPOINTS_CLOSURE.md"), [(96, 101)])
    dump_lines(os.path.join(LEAD, "criteria_r3_verify_20261108/_r3_CLOSURE_VERIFY_20261108.md"), [(108, 113)])
    dump_lines(os.path.join(LEAD, "criteria_r3_verify_20261108/_verify_hy4_out.txt"), [(1, 3)])


SECS = {
    "fp": sec_fp, "orch": sec_orch, "table": sec_table, "agg": sec_agg,
    "anchor": sec_anchor, "grep": sec_grep, "lines1": sec_lines1, "lines2": sec_lines2,
}

if __name__ == "__main__":
    s = sys.argv[1] if len(sys.argv) > 1 else ""
    if s not in SECS:
        print("unknown section: " + s)
        sys.exit(2)
    SECS[s]()
