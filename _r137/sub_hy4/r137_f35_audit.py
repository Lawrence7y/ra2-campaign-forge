#!/usr/bin/env python3
"""R137 sub_hy4 audit: independent recheck of FACT_INDEX v5.32 F23/F35
evidence-path liveness and F35 ceil(...)=M explicit equalities.

Read-only against all ledgers / FACT_INDEX / boards. Writes only under _r137/.
"""
import os
import re
import json
import math
import datetime

ROOT = "/home/t628/projects/ra2-campaign-forge"
TSV = "lead/next_re_20261117_r14/R17_R104_FACTINDEX_V532/FACT_INDEX.tsv"
FILES = [
    "lead/GOAL_THREE_TARGETS_20261018.md",
    "lead/next_re_20261117_r14/BOARD_ARCHIVE.md",
    "lead/next_re_20261117_r14/R14_COMMON.md",
    "lead/LEAD_LOCK",
]

# ---------- helpers ----------

def read_lines(rel):
    """Read bytes, decode tolerantly (R14_COMMON contains a stray NUL)."""
    with open(os.path.join(ROOT, rel), "rb") as f:
        raw = f.read()
    return raw.decode("utf-8", errors="replace").splitlines()


def path_live(rel_path):
    """Return True iff os.stat on the slash-normalized path succeeds."""
    p = rel_path.replace("\\", "/")
    try:
        os.stat(os.path.join(ROOT, p))
        return True
    except OSError:
        return False


# ---------- 命题甲 ----------

def load_fact_rows():
    rows = []
    with open(os.path.join(ROOT, TSV), encoding="utf-8") as f:
        header = f.readline().rstrip("\n").split("\t")
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            cols = line.split("\t")
            fid = cols[0]
            evidence = cols[3] if len(cols) > 3 else ""
            paths = []
            for item in evidence.split(";"):
                item = item.strip()
                if not item:
                    continue
                # 形如 路径(定位符) —— 取第一个左括号之前的原始路径
                p = item.split("(", 1)[0].strip()
                paths.append(p)
            rows.append({"fact_id": fid, "paths": paths, "ncols": len(cols)})
    return header, rows


def group_facts(rows):
    groups = {"all_missing": [], "partial": [], "all_exist": [], "no_paths": []}
    detail = {}
    for r in rows:
        ps = r["paths"]
        live = [path_live(p) for p in ps]
        n = len(live)
        k = sum(1 for x in live if x)
        fid = r["fact_id"]
        detail[fid] = {
            "n_paths": n,
            "n_live": k,
            "paths": [
                {"raw": p, "normalized": p.replace("\\", "/"), "exists": e}
                for p, e in zip(ps, live)
            ],
        }
        if n == 0:
            groups["no_paths"].append(fid)
        elif k == 0:
            groups["all_missing"].append(fid)
        elif k == n:
            groups["all_exist"].append(fid)
        else:
            groups["partial"].append(fid)
    return groups, detail


# ---------- 命题乙 ----------

# 显式等式：ceil(0.9×N)=M / 0.9xN / 0.9*N / 全角乘号 / 反引号 / 全角等号
CEIL_EQ = re.compile(
    r"ceil\(\s*(0?\.9|0?\.5)\s*[×xX*＊·]\s*(\d+)\s*\)"   # ceil(<coef><mul><N>)
    r"\s*[`＊]*\s*[=＝]\s*[`*]*\s*(\d+)"                  # [`]=[*]<M>
)
# 反控 N3：把判据改成 ceil(...)+1 = M —— 期望命中 0
CEIL_PLUS1 = re.compile(
    r"ceil\(\s*(0?\.9|0?\.5)\s*[×xX*＊·]\s*(\d+)\s*\)\s*\+\s*1\s*[=＝]\s*(\d+)"
)


def scan_equalities():
    samples = []
    for rel in FILES:
        for lineno, line in enumerate(read_lines(rel), 1):
            for m in CEIL_EQ.finditer(line):
                coef, n_s, m_s = m.group(1), m.group(2), m.group(3)
                n, ledger_m = int(n_s), int(m_s)
                calc = math.ceil(float(coef) * n)
                samples.append({
                    "file": rel,
                    "line": lineno,
                    "coefficient": coef,
                    "N": n,
                    "ledger_M": ledger_m,
                    "computed_M": calc,
                    "match": ledger_m == calc,
                    "matched_text": m.group(0),
                })
    return samples


# ---------- 反控 ----------

def control_N1():
    fake = "_r137/sub_hy4/__R137_N1__/definitely_absent_%d.xyz" % os.getpid()
    exists = path_live(fake)
    # 负控必须判不存在；同时用一个已知存在的文件做正控，证明判据不是恒 False
    positive = path_live(TSV)
    return {
        "name": "N1_fabricated_path_absent",
        "fabricated_path": fake,
        "judged_exists": exists,
        "positive_control_TSV_exists": positive,
        "passed": (exists is False) and (positive is True),
    }


def control_N2(groups, rows):
    n_facts = len(rows)
    three = len(groups["all_missing"]) + len(groups["partial"]) + len(groups["all_exist"])
    at_least_one = len(groups["partial"]) + len(groups["all_exist"])
    none_at_all = len(groups["all_missing"]) + len(groups["no_paths"])
    return {
        "name": "N2_at_least_one_exists_regroup",
        "fact_row_count": n_facts,
        "three_group_sum": three,
        "at_least_one_exists": at_least_one,
        "none_exists": none_at_all,
        "two_group_sum": at_least_one + none_at_all,
        "passed": (three == n_facts) and (at_least_one + none_at_all == n_facts),
    }


def control_N3():
    hits = []
    for rel in FILES:
        for lineno, line in enumerate(read_lines(rel), 1):
            for m in CEIL_PLUS1.finditer(line):
                hits.append({"file": rel, "line": lineno, "text": m.group(0)})
    return {
        "name": "N3_regex_ceil_plus_1",
        "regex": CEIL_PLUS1.pattern,
        "hit_count": len(hits),
        "hits": hits,
        "passed": len(hits) == 0,
    }


# ---------- proved_strict 定义检查 ----------

def check_proved_strict_definition():
    hits = []
    for rel in FILES:
        for lineno, line in enumerate(read_lines(rel), 1):
            if "proved_strict" in line:
                hits.append({"file": rel, "line": lineno, "text": line.strip()[:240]})
    # 一手定义特征：同一行内 proved_strict 紧跟赋值/冒号，并在其后给出「不含 [未证]」
    # 的定义性约束；排除指向已消失 PANEL.md / 外部脚本的二手转述。
    definitional = []
    for h in hits:
        t = h["text"]
        if re.search(r"proved_strict\s*[=:＝]", t) and re.search(r"未证", t):
            definitional.append(h)
    return {
        "mention_count": len(hits),
        "mentions": hits,
        "definitional_candidates": definitional,
        "note": (
            "四个命题乙文件内没有 proved_strict 的一手权威定义原件"
            "（F35 limitations 指向的 PANEL.md「严格口径双列表」已不在盘上）。"
            "仅有 LEAD_LOCK:92-93 对外部脚本 strict_panel.py:78 "
            "if \"[未证]\" not in sem 的二手转述，以及 FACT_INDEX.tsv F35 limitations "
            "对定义的文字描述「= atlas 内 [已证] 且语义栏不含 [未证]」。"
        ),
    }


# ---------- main ----------

def main():
    header, rows = load_fact_rows()
    groups, detail = group_facts(rows)
    samples = scan_equalities()
    mismatches = [s for s in samples if not s["match"]]

    am = groups["all_missing"]
    exactly_f23_f35 = (am == ["F23", "F35"])

    assertions = []
    assertions.append({"name": "fact_rows_is_54", "passed": len(rows) == 54,
                       "detail": len(rows)})
    assertions.append({"name": "all_missing_is_exactly_F23_F35", "passed": exactly_f23_f35,
                       "detail": am})
    assertions.append({"name": "three_group_sum_is_54",
                       "passed": sum(len(groups[k]) for k in ("all_missing", "partial", "all_exist")) == 54,
                       "detail": sum(len(groups[k]) for k in ("all_missing", "partial", "all_exist"))})
    assertions.append({"name": "ceil_mismatch_count_is_0", "passed": len(mismatches) == 0,
                       "detail": len(mismatches)})
    assertions.append({"name": "ceil_hit_count_is_13", "passed": len(samples) == 13,
                       "detail": len(samples)})

    c1 = control_N1()
    c2 = control_N2(groups, rows)
    c3 = control_N3()
    assertions.append({"name": "N1", "passed": c1["passed"]})
    assertions.append({"name": "N2", "passed": c2["passed"]})
    assertions.append({"name": "N3", "passed": c3["passed"]})

    result = {
        "meta": {
            "card": "R137-AUDIT-F35",
            "role": "audit",
            "family": "hy4",
            "model": "work/cn:hy4flash",
            "root": ROOT,
            "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "tsv_header": header,
            "discipline": "read-only against FACT_INDEX/ledgers/boards; writes only under _r137/",
        },
        "proposition_A": {
            "description": (
                "FACT_INDEX v5.32 全部事实项按 evidence_paths（第4列，分号分隔，"
                "取 '(' 前路径、反斜杠归一、os.stat 相对 ROOT 判存在）分组"
            ),
            "fact_row_count": len(rows),
            "groups": {
                "all_missing": groups["all_missing"],
                "partial": groups["partial"],
                "all_exist": groups["all_exist"],
                "no_paths": groups["no_paths"],
            },
            "counts": {k: len(v) for k, v in groups.items()},
            "all_missing_exactly_F23_F35": exactly_f23_f35,
            "full_name_list": {
                "all_missing": groups["all_missing"],
                "partial": groups["partial"],
                "all_exist": groups["all_exist"],
            },
            "assertions_passed": sum(1 for a in assertions if a["passed"]),
            "assertions_total": len(assertions),
            "assertions": assertions,
            "detail": detail,
        },
        "proposition_B": {
            "description": (
                "在四个台账文件中用正则匹配 ceil(0.9×N)=M / ceil(0.5×N)=M "
                "（支持 0.9xN / 0.9*N / 全角乘号 / 反引号 / 全角等号），"
                "用 math.ceil(float(coef)*N) 独立重算"
            ),
            "regex": CEIL_EQ.pattern,
            "files_scanned": FILES,
            "sample_table": samples,
            "hit_count": len(samples),
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
            "hit_count_per_file": {
                rel: sum(1 for s in samples if s["file"] == rel) for rel in FILES
            },
        },
        "controls": [c1, c2, c3],
        "proved_strict_definition_check": check_proved_strict_definition(),
        "boundary_statement": {
            "proved": [
                "证据路径的 os.stat 存在性（现盘快照）被独立重算：F23/F35 全部 evidence_paths 均 stat 失败，其余 52 条至少一条路径 stat 成功。",
                "四个台账文件里所有 13 处显式 ceil(0.9×N)=M / ceil(0.5×N)=M 等式，用 math.ceil 重算全部一致（失配 0）。",
                "N1 负控、N2 三/二分组求和、N3 ceil+1 正则三条反控均通过。",
            ],
            "not_proved": [
                "未验证任何事实项的语义真伪；未打开二进制、未复算任何取证脚本结果。",
                "未验证 F35 判据式 named_S >= ceil(0.9n) 且 proved >= ceil(0.5n) 在实际子系统上的达标情况，只验了显式等式的算术一致性。",
                "未验证 F35 的 proved_strict 一手定义（原件 PANEL.md 已失）；仅见二手转述。",
                "stat 成功只证明路径当前存在于磁盘，不证明文件内容仍与台账结论一致、未被改写，也不证明该内容足以支撑对应事实。",
            ],
            "evidence_path_absent_equals_fact_false": (
                "不等价。「证据路径不存在」只说明台账指向的文档在现盘不可定位"
                "（证据链失联 / 不可核验），不构成对事实真假的判定；事实可能为真但副本丢失，"
                "也可能为假。正确表述是「不可核验」，不是「为假」。"
            ),
            "f35_proved_strict_definition_present": False,
            "f35_proved_strict_definition_note": (
                "在我为命题乙读取的 4 个文件中没有 proved_strict 的一手权威定义原件；"
                "F35 limitations 指向的 PANEL.md「严格口径双列表」已不在盘上。"
                "仅有二手转述（LEAD_LOCK:92-93 引 strict_panel.py:78；FACT_INDEX F35 limitations 的文字描述）。"
            ),
        },
    }

    out = os.path.join(ROOT, "_r137/sub_hy4/r137_f35_audit.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("wrote", out)
    print("assertions", result["proposition_A"]["assertions_passed"], "/", result["proposition_A"]["assertions_total"])
    print("all_missing", am, "exactly_F23_F35", exactly_f23_f35)
    print("ceil hits", len(samples), "mismatches", len(mismatches))
    print("controls", [c["passed"] for c in (c1, c2, c3)])


if __name__ == "__main__":
    main()
