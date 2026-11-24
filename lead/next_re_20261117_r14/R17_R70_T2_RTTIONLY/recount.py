#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R17_R70_T2_RTTIONLY / recount.py
独立路径直接数 FACT_INDEX F14 的 RTTI_ONLY（口径 S / C）。

只读源文件（不修改）：
  - R17_R19_RTTI_XCHECK/rtti_names.tsv          : RTTI 侧 bare_class / prefix / td_VA（分母 988）
  - R17_R13_NAME_TABLE/names.tsv                : 名字表装饰名（Q1 比对是否同一个 988）
  - COVERAGE/coverage.tsv                       : 第4列 one_line_semantics（独立抽 token）
  - R17_R24_RECON_FINAL/reconcile_final.tsv     : 权威表 S_bucket/C_bucket（Q4 正控自检）

过滤条件：
  - rtti_names.tsv / names.tsv / reconcile_final.tsv : 跳过表头，取非空数据行；
    BOTH / COVERAGE_ONLY / RTTI_ONLY 仅按 S_bucket/C_bucket 列取值，不做文本 grep。
  - coverage.tsv : 第4列按 Class 后缀正则抽取，每行去重后按行计数。

三种数法交叉验证 RTTI_ONLY：
  A（权威推导）        : 988 - |被覆盖 TD 集合 cv|
  B（RTTI侧逐个判/tdVA）: 遍历 988 个 TD tdVA，逐个累加"不在 cv 中"者
  C（RTTI侧纯 bare 名）  : 对每个 RTTI bare 名直接判是否存在 coverage 对应项，完全不碰 cv
Q4 正控：token 侧 BOTH 数（我的实现）对照权威表 S_bucket/C_bucket==BOTH。
产物只写本脚本目录：recount_out.txt。
"""
import pathlib, re, collections

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14")
OUT = pathlib.Path(__file__).resolve().parent
F_RTTI  = ROOT / r"R17_R19_RTTI_XCHECK\rtti_names.tsv"
F_NAMES = ROOT / r"R17_R13_NAME_TABLE\names.tsv"
F_COV   = ROOT / r"COVERAGE\coverage.tsv"
F_RECON = ROOT / r"R17_R24_RECON_FINAL\reconcile_final.tsv"
CLASS_RE = re.compile(r"(?<![A-Za-z0-9_])[A-Za-z_][A-Za-z0-9_]*Class(?![A-Za-z0-9_])")


def read_tsv(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    rows = [ln.split("\t") for ln in lines[1:] if ln.strip() != ""]
    return lines[0].split("\t"), rows


def normalize_decorated(s):
    """把 names.tsv 的 .?AV...@@ / .?AU...@@ 装饰名归一化为裸名。"""
    for p in (".?AV", ".?AU", ".?AW"):
        if s.startswith(p):
            s = s[len(p):]
            break
    return s[:-2] if s.endswith("@@") else s


def pvs(s):
    """权威口径：返回 s 的所有 P/A/V 前缀剥离候选（长度1..4）。"""
    return [s[i:] for i in range(1, min(4, len(s) - 1) + 1)
            if s[:i] and all(c in "PAV" for c in s[:i])]


def main():
    log = []
    def P(msg=""):
        print(msg)
        log.append(str(msg))

    # ---------- Q1: RTTI 侧分母 ----------
    _, rtti_rows = read_tsv(F_RTTI)
    rtti_rows = [r for r in rtti_rows if r and r[0].strip()]
    rtti_bare = [r[0] for r in rtti_rows]
    rtti_va = [int(r[2], 16) if len(r) > 2 and r[2].lower().startswith("0x") else None
               for r in rtti_rows]
    P(f"[Q1] rtti_names.tsv 数据行={len(rtti_rows)} 唯一bare={len(set(rtti_bare))}")

    _, name_rows = read_tsv(F_NAMES)
    name_rows = [r for r in name_rows if r and r[0].strip()]
    name_bare = [normalize_decorated(r[0]) for r in name_rows]
    P(f"[Q1] names.tsv 数据行={len(name_rows)} 归一化唯一bare={len(set(name_bare))}")
    s_r, s_n = set(rtti_bare), set(name_bare)
    P(f"[Q1] 同一988(集合相等)={s_r == s_n} rtti独有={len(s_r - s_n)} names独有={len(s_n - s_r)}")
    if s_r != s_n:
        P(f"[Q1] rtti独有样例={sorted(s_r - s_n)[:8]}")
        P(f"[Q1] names独有样例={sorted(s_n - s_r)[:8]}")

    # ---------- 从 RTTI 侧独立构建匹配索引 ----------
    ex, pl, tp = {}, {}, {}
    for bare, va in zip(rtti_bare, rtti_va):
        ex.setdefault(bare.lower(), (bare, va))
        if bare.startswith("?$") and "@" in bare:
            tp.setdefault(bare[2:].split("@", 1)[0].lower(), []).append((bare, va))
        elif (not bare.startswith("?$")) and "@" in bare:
            pl.setdefault(bare.lower(), []).append((bare, va))
    P(f"[build] 精确键={len(ex)} 模板基名键={len(tp)} 模板TD={sum(len(v) for v in tp.values())} "
      f"非模板复合键={len(pl)} 非模板复合TD={sum(len(v) for v in pl.values())}")

    # ---------- 独立从 coverage.tsv 抽 token ----------
    clines = F_COV.read_text(encoding="utf-8").splitlines()
    counts = collections.Counter()
    nrows = 0
    for ln in clines[1:]:
        if not ln:
            continue
        nrows += 1
        c = ln.split("\t")
        sem = c[3] if len(c) > 3 else ""
        for z in dict.fromkeys(CLASS_RE.findall(sem)):
            counts[z] += 1
    toks = sorted(counts, key=lambda n: (-counts[n], n))
    P(f"[cov] coverage.tsv 数据行={nrows} 抽取token={len(toks)} (权威429)")

    cov_exact = {z.lower() for z in toks}
    cov_pref = {y.lower() for z in toks for y in pvs(z)}
    cov_comp = {z.replace("_", "@").lower() for z in toks}

    # 权威 resolve 语义（大小写不敏感；优先级 exact>prefix>compound>template_base）
    def resolve(z, mode):
        seeds = [z] + ([z[1:]] if z.startswith("?") else [])
        for x in seeds:
            if x.lower() in ex:
                return ("exact", ex[x.lower()][1])
        for x in seeds:
            for y in pvs(x):
                if y.lower() in ex:
                    return ("prefix", ex[y.lower()][1])
        if mode == "C":
            k = z.replace("_", "@").lower()
            if k in pl:
                return ("compound", [va for _, va in pl[k]])
        if z.lower() in tp:
            return ("template_base", [va for _, va in tp[z.lower()]])
        return None

    # 纯 RTTI 侧判定：bare 名是否存在 coverage 对应项（不经过 cv / 不做减法）
    def has_counterpart(bare, mode):
        lo = bare.lower()
        if lo in cov_exact:
            return True
        if lo in cov_pref:
            return True
        if bare.startswith("?$") and "@" in bare:
            if bare[2:].split("@", 1)[0].lower() in cov_exact:
                return True
        if mode == "C" and (not bare.startswith("?$")) and "@" in bare:
            if lo in cov_comp:
                return True
        return False

    # ---------- Q2/Q3/Q4：两种口径 ----------
    for mode in ("S", "C"):
        res = {z: resolve(z, mode) for z in toks}
        res = {k: v for k, v in res.items() if v}
        mech = collections.Counter(r[0] for r in res.values())
        cv = set()
        for m, td in res.values():
            if m in ("exact", "prefix"):
                cv.add(td)
            else:
                cv.update(td)
        both = len(res)
        covonly = len(toks) - len(res)
        ri_a = len(rtti_bare) - len(cv)
        ri_b = sum(1 for va in rtti_va if va not in cv)
        ri_c = sum(1 for b in rtti_bare if not has_counterpart(b, mode))
        P(f"[{mode}] BOTH(我的token侧)={both} COVERAGE_ONLY={covonly} 机制={dict(mech)}")
        P(f"[{mode}] 覆盖TD|cv|={len(cv)} | A减法988-cv={ri_a} | "
          f"B RTTI侧逐个判(tdVA in cv)={ri_b} | C RTTI侧逐个判(bare名,不碰cv)={ri_c}")

    # 优先级重叠边界诊断（确认 C 法与权威等价的前提）
    ov_ep = sum(1 for z in toks if z.lower() in ex and any(y.lower() in ex for y in pvs(z)))
    ov_et = sum(1 for z in toks if z.lower() in ex and z.lower() in tp)
    ov_ec = sum(1 for z in toks if z.lower() in ex and z.replace("_", "@").lower() in pl)
    P(f"[边界] exact∩prefix token={ov_ep} exact∩模板基名={ov_et} exact∩compound={ov_ec}")

    # ---------- Q4 正控：权威表按列取值 ----------
    _, recon = read_tsv(F_RECON)
    recon = [r for r in recon if r and r[0].strip()]
    sb = collections.Counter(r[2] for r in recon if len(r) > 2)
    cb = collections.Counter(r[4] for r in recon if len(r) > 4)
    P(f"[权威reconcile_final.tsv] 数据行={len(recon)} S_bucket={dict(sb)} C_bucket={dict(cb)}")

    (OUT / "recount_out.txt").write_text("\n".join(log) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
