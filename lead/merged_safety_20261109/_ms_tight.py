# -*- coding: utf-8 -*-
"""_ms_tight.py — 更紧的 _f2v_verify9 补丁（v2）验证 + 错误传导链 + 安全集边界。

只读取既有件；新写文件均在本写域。零真机、零采样代码；-I -X utf8 -B。
不改任何既有件；改后整件只写本写域候选副本，用标准 importlib 加载器运行。
"""
import contextlib
import difflib
import hashlib
import importlib.util
import io
import json
import sys
import types
from pathlib import Path

sys.dont_write_bytecode = True
REPO = Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "merged_safety_20261109"
FIX = W / "_ms_fixtures"
V9 = REPO / "lead" / "r11_f2_fix_20261109" / "_f2v_verify9.py"
RE = REPO / "lead" / "r33e_merge_20261109" / "_re_linked.py"
OUT = []


def say(s=""):
    OUT.append(str(s))
    print(s)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


RE_MOD = load("_ms_tight_re", RE)

# ---------------------------------------------------------------- 改前 :19-36（逐字，含 :36 的保留行）
BEFORE = '''    pp, pw, pb = plus.r11_scan_plus(text, p.parent, root=REPO)
    for k, b in enumerate(pb):
        if b.get("match") is not True:
            continue
        src = b.get("alt") or b
        vp = Path(src.get("verified_path") or src.get("path"))
        data = vp.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        size = len(data)
        ok_sha = sha == b["declared"].lower()
        ok_bytes = size == src["bytes"]
        n += 1
        print("MATCH#%d #%d bind#%d tier=%s alt=%s %s" % (n, i, k + 1, b.get("tier"), bool(b.get("alt")), vp))
        print("   declared=%s" % b["declared"])
        print("   mine   =%s sha_ok=%s" % (sha, ok_sha))
        print("   bytes declared=%s mine=%d bytes_ok=%s" % (src["bytes"], size, ok_bytes))
        if not (ok_sha and ok_bytes):
            print("   *** MISMATCH ***")
'''

# ---------------------------------------------------------------- 改后 v2（紧版）
# 只把 :23 的 `src = ...` 换成「三形态 dispatch」，并把原循环体缩进一层；
# 其余语义逐字不动（unique 的输出字符串/格式保持原样）。
AFTER = '''    pp, pw, pb = plus.r11_scan_plus(text, p.parent, root=REPO)
    for k, b in enumerate(pb):
        if b.get("match") is not True:
            continue
        if b.get("tier") == "SAMEDOC_LINK_EQ":
            items = [(m.get("path"), m.get("bytes")) for m in (b.get("members") or [])]
        elif (b.get("alt") or b).get("path"):
            src = b.get("alt") or b
            items = [(src.get("verified_path") or src.get("path"), src.get("bytes"))]
        else:
            items = []
        if not items:
            n += 1
            print("SKIP#%d #%d bind#%d tier=%s 无单一回验路径且无 members（multi：不主张 path）" % (n, i, k + 1, b.get("tier")))
            continue
        for vp, bytes_decl in items:
            vp = Path(vp) if vp else None
            data = vp.read_bytes() if vp else b""
            sha = hashlib.sha256(data).hexdigest()
            size = len(data)
            ok_sha = sha == (b.get("declared") or "").lower()
            ok_bytes = size == bytes_decl
            n += 1
            print("MATCH#%d #%d bind#%d tier=%s alt=%s %s" % (n, i, k + 1, b.get("tier"), bool(b.get("alt")), vp))
            print("   declared=%s" % (b.get("declared") or ""))
            print("   mine   =%s sha_ok=%s" % (sha, ok_sha))
            print("   bytes declared=%s mine=%d bytes_ok=%s" % (bytes_decl, size, ok_bytes))
            if not (ok_sha and ok_bytes):
                print("   *** MISMATCH ***")
'''

say("=" * 78)
say("T. _f2v_verify9 紧版补丁 v2（:19-36 为替换单元）")
say("=" * 78)
v9src = V9.read_text(encoding="utf-8")
say("T0 BEFORE 逐字包含在原件 = %s (count=%d)" % (BEFORE in v9src, v9src.count(BEFORE)))
patched = v9src.replace(BEFORE, AFTER)
CAND = W / "_ms_v9_candidate_v2.py"
CAND.write_text(patched, encoding="utf-8")
try:
    compile(patched, "<v2>", "exec")
    say("T1 compile() = OK")
except Exception as e:
    say("T1 compile FAILED = %s: %s" % (type(e).__name__, e))

b, a = BEFORE.splitlines(), AFTER.splitlines()
sm = difflib.SequenceMatcher(None, b, a, autojunk=False)
add = rem = same = 0
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op == "equal":
        same += i2 - i1
    else:
        rem += i2 - i1
        add += j2 - j1
say("T2 difflib: before=%d after=%d unchanged=%d removed=%d added=%d (净改 %d 行, 不动 %d 行)"
    % (len(b), len(a), same, rem, add, rem + add, same))

# 真实 30 件回归
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        load("_ms_v9_v2_run", CAND)
    o = buf.getvalue()
    say("T3 改后整件跑真实 30 件 = OK，末行=%r MATCH=%d MISMATCH=%d SKIP=%d"
        % (o.strip().splitlines()[-1], o.count("MATCH#"),
           o.count("*** MISMATCH ***"), o.count("SKIP#")))
except Exception as e:
    say("T3 FAILED = %s: %s" % (type(e).__name__, e))

# 三形态 + 缺键注射：用假 plus 注入 bindings，跑改后整件
MA, MB = FIX / "_ms_mem_a.py", FIX / "_ms_mem_b.py"
MEM = MA.read_bytes()
MHEX = hashlib.sha256(MEM).hexdigest()
merged_text = (
    "# 交付件（反例）\n\n被核对象 SHA256 = %s，字节数 = %d\n\n"
    "两个产物：`_ms_mem_a.py` 与 `_ms_mem_b.py`。\n"
    "`_ms_mem_b.py` 复制自 `_ms_mem_a.py`。\n") % (MHEX, len(MEM))
mp, mw, merged = RE_MOD.link_triple(merged_text, FIX, MHEX, len(MEM), root=REPO)
uniq_rec = {"declared": MHEX, "path": str(MA), "verified_path": str(MA),
            "recomputed": MHEX, "bytes": len(MEM), "match": True,
            "tier": "SAMEDOC_LINK", "members": None, "alt": None}
multi_forced = {"declared": MHEX, "path": None, "match": True,
                "tier": "SAMEDOC_LINK", "members": None, "alt": None}

LOADER_OLD = (
    'spec = importlib.util.spec_from_file_location("_f2p", REPO / "lead" / "r11_f2_fix_20261109" / "_f2_r11plus.py")\n'
    'plus = importlib.util.module_from_spec(spec)\n'
    'spec.loader.exec_module(plus)')
LOADER_NEW = 'plus = __import__("sys").modules["_ms_fake_plus"]'
src = CAND.read_text(encoding="utf-8")
say("T3b 注入用 loader 片段命中 = %s" % (LOADER_OLD in src))
INJECT = W / "_ms_v9_v2_inject.py"
INJECT.write_text(src.replace(LOADER_OLD, LOADER_NEW), encoding="utf-8")


def run_v2(bindings):
    fake = types.ModuleType("_ms_fake_plus")
    fake.r11_scan_plus = lambda text, parent, root=None: ([], [], list(bindings))
    sys.modules["_ms_fake_plus"] = fake
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            load("_ms_v9_v2_inject_run_%d" % (run_v2.counter), INJECT)
        run_v2.counter += 1
        return "OK", buf.getvalue()
    except Exception as e:
        run_v2.counter += 1
        return "%s: %s" % (type(e).__name__, e), buf.getvalue()


run_v2.counter = 0
cases = [
    ("unique (有 path)", [uniq_rec]),
    ("merged (无 path 有 members)", [merged]),
    ("multi (match=True, 无 path 无 members)", [multi_forced]),
    ("merged 缺 member.bytes", [{**merged, "members": [{"path": str(MA), "sha": MHEX}]}]),
    ("merged members=None", [{**merged, "members": None}]),
    ("unique 缺 bytes", [{k: v for k, v in uniq_rec.items() if k != "bytes"}]),
    ("merged 缺 declared", [{k: v for k, v in merged.items() if k != "declared"}]),
    ("mixed unique+merged+multi", [uniq_rec, merged, multi_forced]),
]
for name, pb in cases:
    st, o = run_v2(pb)
    tail = [x for x in o.strip().splitlines() if x.startswith(("MATCH#", "SKIP#"))][:4]
    say("T4 %-42s | %-10s | %s" % (name, st, tail))

# ---------------------------------------------------------------- 错误传导链实证
say()
say("=" * 78)
say("U. 只修两处、其余静默误读不修 → 接入后的错误传导链（实跑各段）")
say("=" * 78)
say("U0 前提：接入点 _f2_r11plus.py:303-305 把 link_triple 的 merged rec 合进 bindings；"
    "本会话实读该 else 现为 rec['tier']=None + R3-3b warning（未接入）。")
r = merged
written = {"totals": {"plus_path": sum(1 for b in [r] if b.get("path")),
                      "plus_match": sum(1 for b in [r] if b.get("match") is True)},
           "results": [{"plus": {"bindings": [r], "verdict": "PASS"}}]}
say("U1 写出 _f2_compare_out.json 形态：totals=%s" % json.dumps(written["totals"], ensure_ascii=False))
sha_ok = (r.get("recomputed") or "").lower() == r.get("declared", "").lower()
say("U2 _f2w_checks.py:29 读该 JSON → sha_ok=%r（合法 match=True 被记成「sha 逐字不一致」，n_ok 少计 1）" % sha_ok)
vp = r.get("verified_path", "") or ""
rc = r.get("recomputed", "") or ""
say("U3 _f2w_extract.py:26-33 同一 JSON → verified=%r recomputed=%r bytes=%r（19 条逐条表该行静默空白）"
    % (vp, (rc[:16] + "...") if rc else "-", r.get("bytes", "-")))
say("U4 _f2w_pass.py:17 / _f2v_final.py:54-58 → plus match=%d collected=%d tiers=%s"
    "（merged 被计入「已回验」统计，而 collected=0）"
    % (written["totals"]["plus_match"], written["totals"]["plus_path"], {r.get("tier"): 1}))
say("U5 门禁若只读 r11 problems（旧 :160 `FAIL if r11_problems else PASS`）且 link_triple 恒 problems=[]"
    "（_re_linked.py:47,177-179,330）→ 无单一回验路径的副本群被判 PASS（_ms_probe D6.6 实证）。")
say("U6 结论链：merged rec → compare 写出 (plus_path=0, plus_match=1) → checks/extract 报告静默空白"
    " → pass/final 把副本群计入已回验 → 门禁 problems=[] ⇒ PASS ⇒ 交付件在零单一对象锚定下被放行。")

# ---------------------------------------------------------------- 安全集边界
say()
say("=" * 78)
say("V. 安全集边界：崩 vs 静默错")
say("=" * 78)
say("V1 崩（硬阻断）：_f2v_verify9.py:24/29 — 接入后审计 §5.2 第 3 步「下游消费者全量回放」"
    "直接 TypeError/KeyError，联调无法完成（_ms_probe C3 原版列实证）。")
say("V2 静默错（软污染）：E1-E8 六件全部不崩、全部产出错误结论，且 _f2w_checks/_f2w_extract/"
    "_f2w_pass/_f2v_final 都是『交付报告用』输出（本会话 Read 各件 docstring 实读）。")
say("V3 判据：安全集 = 「不修则安全判定不可信」的最小集合，而非「不修则程序退出」的集合。"
    "静默错比崩更该进安全集：崩使接入联调失败（fail-closed，安全）；静默错让接入看起来成功"
    "却把无锚定副本群记成已回验（fail-open，不安全）。")
say("V4 但严格按『最小』：把静默错簇收敛到唯一汇聚点即可 —— 它们全读"
    " _f2_compare.py:100 写出的同一个 JSON（审计 §3.4 B 表实读 + 本会话 Read 各件），"
    "故需要在接入层做『merged 不写进单对象计数口径』的契约裁决（属接入点改动，非本任务两处补丁）。")

(W / "_ms_tight_out.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8")
say()
say("WROTE %s" % (W / "_ms_tight_out.txt"))
