# -*- coding: utf-8 -*-
"""_nc2_rule_coverage.py —— 规则可达性门禁（不靠自觉：机器枚举 RULES 逐条要求命中）。

复核破口(8)：旧版 10/10 自检只覆盖 18 条声明规则中的 6 条。
本脚本对 _nc2_lint.RULES 里的**每一条**构造最小输入，要求 lint 报出该规则码；
`RULES` 新增一条而没写探针 -> 本脚本直接 FAIL。

只读加载模块；输出 stdout。
用法：python -I -X utf8 <绝对路径>/_nc2_rule_coverage.py > <绝对路径>/_nc2_rule_coverage_out.json
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import os

ROOT = r"D:\Project\ra2-campaign-forge"
D = os.path.join(ROOT, "lead", "number_channel_20261109")


def load(name, fname):
    spec = importlib.util.spec_from_file_location(name, os.path.join(D, fname))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ph = load("nc2ph_cov", "_nc2_placeholder.py")
ln = load("nc2ln_cov", "_nc2_lint.py")
claims = ph.build_demo(ROOT)


def src_of(cs, *, version=1, history=None, prev_hashes=None, prev="", block=None):
    s = {"version": version, "prev_sha256": prev,
         "prev_hashes": prev_hashes if prev_hashes is not None else [],
         "history": history if history is not None else [],
         "claims": [dict(c) for c in cs], "block_sha256": "", "binding_line": ""}
    s["block_sha256"] = block or hashlib.sha256(ph.chain_block_bytes(s)).hexdigest()
    s["binding_line"] = ph.binding_line(ph.chain_block_bytes(s))
    for c in s["claims"]:
        c["source_block_sha256"] = s["block_sha256"]
    return s


src = src_of(claims)
hdr = "【数字源】version=1\n" + src["binding_line"]


def arr(body):
    return hdr + "\nconst ASK_ANALYST = [\n" + body + "\n].join(\"\\n\");\n"


def hit_rule(text, cs=None, source=None, dir_hint="", rendered=False):
    r = ln.lint(text, cs if cs is not None else claims,
                source=source, dir_hint=dir_hint, rendered=rendered)
    return {f["rule"] for f in r["findings"]}


def hdr_with(version=1, sha=None, block_src=None):
    b = block_src or src
    s = sha if sha is not None else b["block_sha256"]
    return "【数字源】version=%d\n被核对象 SHA256 = %s，字节数 = 1" % (version, s)


cases = {}

# --- 散文/口径类 ---
cases["BARE_ARABIC"] = lambda: hit_rule(arr('  "【背景】实测 13 个域。",'), source=src)
cases["BARE_CJK_NUMERAL"] = lambda: hit_rule(
    arr('  "【背景】十个域仍报问题。",'), source=src)
cases["AMBIGUOUS_SCOPE"] = lambda: hit_rule(
    arr('  "【背景】实测 13 个域。",'), source=src)

# --- 跨域 ---
def _cross():
    return hit_rule(arr('  "【背景】{{N.domains_nonempty}}。",'),
                    source=src, dir_hint="some_other_dir")
cases["CROSS_DOMAIN_LEAK"] = _cross

# --- 设计实验 ---
cases["DESIGN_EXPERIMENT_UNMARKED"] = lambda: hit_rule(
    arr('  "【背景】这是 Shim 设计实验数值。",'), source=src)
cases["DESIGN_EXPERIMENT_IN_ACCEPTANCE"] = lambda: hit_rule(
    arr('  "【交付】Shim 设计实验数值须达成。",'), source=src)

# --- 估算 ---
cases["ESTIMATE_NOT_DEGRADED"] = lambda: hit_rule(
    arr('  "【背景】估算 25% 的工作量。",'), source=src)
cases["ESTIMATE_IN_ACCEPTANCE"] = lambda: hit_rule(
    arr('  "【交付】{{N.est_effort}} 必须达成。",'), source=src)

# --- 占位符 ---
cases["UNRESOLVED_PLACEHOLDER"] = lambda: hit_rule(
    arr('  "【背景】{{N.no_such_id}}。",'), source=src)
cases["NONCONFORMING_MUSTACHE"] = lambda: hit_rule(
    arr('  "【背景】{{NAME_INJECT}}。",'), source=src)

# --- 声明校验类（构造坏 claim） ---
def _bad_kind():
    c = dict(claims[0]); c["source_kind"] = "拍脑袋"
    return hit_rule(arr('  "【背景】{{N.domains_nonempty}}。",'), cs=[c] + claims[1:])
cases["BAD_SOURCE_KIND"] = _bad_kind

def _missing():
    c = dict(claims[0]); c.pop("command")
    return hit_rule(arr('  "【背景】{{N.domains_nonempty}}。",'), cs=[c] + claims[1:])
cases["MISSING_FIELDS"] = _missing

def _bad_sha():
    c = dict(claims[0]); c["sha256"] = "x"
    return hit_rule(arr('  "【背景】{{N.domains_nonempty}}。",'), cs=[c] + claims[1:])
cases["BAD_SHA256"] = _bad_sha

def _bad_digest():
    c = dict(claims[0]); c["value"] = 999   # 不重封
    return hit_rule(arr('  "【背景】{{N.domains_nonempty}}。",'), cs=[c] + claims[1:])
cases["BAD_CLAIM_DIGEST"] = _bad_digest

def _evidence():
    c = dict(claims[0]); c["stdout_path"] = "no/such.txt"; c = ph.seal_claim(c)
    return hit_rule(arr('  "【背景】{{N.domains_nonempty}}。",'), cs=[c] + claims[1:])
cases["EVIDENCE_UNVERIFIED"] = _evidence

def _dangling():
    c = dict([x for x in claims if x["source_kind"] == "推导"][0])
    c["depends_on"] = ["no_such_dep"]; c = ph.seal_claim(c)
    return hit_rule(arr('  "【背景】{{N.ratio_32768}}。",'), cs=[c])
cases["DANGLING_DEP"] = _dangling

# --- 链类 ---
def _stale_source():
    t = hdr_with(version=1, sha="0" * 64) + \
        '\nconst ASK_ANALYST = [\n  "【背景】{{N.domains_nonempty}}。",\n].join("\\n");\n'
    return hit_rule(t, source=src)
cases["STALE_NUMBER_SOURCE"] = _stale_source

def _stale_version():
    t = hdr_with(version=2) + \
        '\nconst ASK_ANALYST = [\n  "【背景】{{N.domains_nonempty}}。",\n].join("\\n");\n'
    return hit_rule(t, source=src)
cases["STALE_VERSION"] = _stale_version

def _block_mismatch():
    bad = src_of(claims, block="1" * 64)
    t = hdr + '\nconst ASK_ANALYST = [\n  "【背景】{{N.domains_nonempty}}。",\n].join("\\n");\n'
    return hit_rule(t, source=bad)
cases["BLOCK_HASH_MISMATCH"] = _block_mismatch

def _history_broken():
    hist = [{"id": "bindings_zero", "from": 5, "to": 6,
             "evidence": "x", "at_version": 2}]
    ph3 = "a" * 64
    bad = src_of(claims, version=3, history=hist, prev=ph3,
                 prev_hashes=["b" * 64, ph3])
    t = hdr_with(version=3, block_src=bad) + \
        '\nconst ASK_ANALYST = [\n  "【背景】{{N.domains_nonempty}}。",\n].join("\\n");\n'
    return hit_rule(t, source=bad)
cases["HISTORY_CHAIN_BROKEN"] = _history_broken

def _prev_broken():
    hist = [{"id": "bindings_zero", "from": 5, "to": 6,
             "evidence": "x", "at_version": 2},
            {"id": "domains_nonempty", "from": 10, "to": 13,
             "evidence": "y", "at_version": 3}]
    bad = src_of(claims, version=3, history=hist, prev="0" * 64,
                 prev_hashes=["b" * 64, "c" * 64])
    t = hdr_with(version=3, block_src=bad) + \
        '\nconst ASK_ANALYST = [\n  "【背景】{{N.domains_nonempty}}。",\n].join("\\n");\n'
    return hit_rule(t, source=bad)
cases["PREV_SHA256_BROKEN"] = _prev_broken

def _claim_block():
    cs = [dict(c) for c in claims]
    cs[0]["source_block_sha256"] = "f" * 64
    bad = src_of(cs)
    bad["claims"][0]["source_block_sha256"] = "f" * 64
    t = hdr + '\nconst ASK_ANALYST = [\n  "【背景】{{N.domains_nonempty}}。",\n].join("\\n");\n'
    return hit_rule(t, cs=cs, source=bad)
cases["CLAIM_BLOCK_HASH_MISMATCH"] = _claim_block

# --- 跨段 / 未渲染 ---
def _cross_section():
    # 机器段用运行时拼接形态（含已渲染数值 token），散文段不引用任何值
    t = hdr + '\nconst ASK_ANALYST = [\n  "【复核数据】" + vfText + " 32768 0.14013134",\n  "【背景】什么都没引用。",\n].join("\\n");\n'
    return hit_rule(t, source=src, rendered=True)
cases["CROSS_SECTION_VALUE_NOT_USED"] = _cross_section

def _unrendered():
    t = hdr + '\nconst ASK_ANALYST = [\n  "【复核数据】" + vfText,\n  "【背景】{{N.ratio_32768}}。",\n].join("\\n");\n'
    return hit_rule(t, source=src, rendered=True)
cases["UNRENDERED_MACHINE_SEGMENT"] = _unrendered

# --- 验收段裸数字且证据未闭合 ---
def _unproven():
    c = dict(claims[0]); c["stdout_path"] = "no/such.txt"; c = ph.seal_claim(c)
    cs = [c] + claims[1:]
    t = hdr + '\nconst ASK_ANALYST = [\n  "【交付】实测 13 个域。",\n].join("\\n");\n'
    return hit_rule(t, cs=cs, source=src)
cases["UNPROVEN_ACCEPTANCE_NUMBER"] = _unproven


def main():
    rows, fired = [], set()
    for rule in sorted(ln.RULES):
        if rule not in cases:
            rows.append({"rule": rule, "has_probe": False, "fired": False,
                         "pass": False, "note": "RULE_WITHOUT_PROBE"})
            continue
        got = cases[rule]()
        ok = rule in got
        if ok:
            fired.add(rule)
        rows.append({"rule": rule, "has_probe": True, "fired": ok,
                     "pass": ok, "all_rules_hit": sorted(got)[:8]})
    out = {
        "n_declared_rules": len(ln.RULES),
        "n_rules_with_probe": len(cases),
        "n_rules_fired": len(fired),
        "all_declared_rules_reachable": len(fired) == len(ln.RULES),
        "rules_without_probe": sorted(set(ln.RULES) - set(cases)),
        "rules_not_fired": sorted(set(ln.RULES) - fired),
        "rows": rows,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
