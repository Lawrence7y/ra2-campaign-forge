# -*- coding: utf-8 -*-
"""_ms_counterexample.py — 可实跑反例：交付件绑定行只能 merged 匹配，旧门禁 PASS / 新门禁 FAIL。

用法（本会话实跑命令）：
  python -I -X utf8 -B "D:/Project/ra2-campaign-forge/lead/merged_safety_20261109/_ms_counterexample.py"

只读取既有件；新写交付件/成员均在本写域。零真机、零采样代码；-I -X utf8 -B。
门禁「改后」= 本写域候选副本 _ms_g9_candidate.py（由 _ms_probe.py 生成），
既有 _g9_gate.py 全程只读不改。
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
REPO = Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "merged_safety_20261109"
FIX = W / "_ms_fixtures"
G9 = REPO / "lead" / "gate_r9r12_20261109" / "_g9_gate.py"
CAND = W / "_ms_g9_candidate.py"
RE = REPO / "lead" / "r33e_merge_20261109" / "_re_linked.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---- 造交付件：一条无显式路径的绑定行 + 两个同 hash 成员 + 溯源声明词 ----
MEM = b"# merged member\nprint('x')\n"
A, B = FIX / "_ms_mem_a.py", FIX / "_ms_mem_b.py"
A.write_bytes(MEM)
B.write_bytes(MEM)
HEX = hashlib.sha256(MEM).hexdigest()
NB = len(MEM)
DELIV = W / "_ms_counterexample_deliverable.md"
DELIV.write_text(
    "# 交付件（反例）\n\n"
    "被核对象 SHA256 = %s，字节数 = %d\n\n"
    "两个产物：`_ms_fixtures/_ms_mem_a.py` 与 `_ms_fixtures/_ms_mem_b.py`。\n"
    "`_ms_fixtures/_ms_mem_b.py` 复制自 `_ms_fixtures/_ms_mem_a.py`。\n"
    % (HEX, NB), encoding="utf-8")

print("=" * 74)
print("反例交付件 =", DELIV)
print("绑定行 hex =", HEX, " 字节数 =", NB)
print("=" * 74)

# ---- 绑定行确实「只能 merged 匹配」：link_triple 产 merged rec ----
RE_MOD = load("_ms_ce_re", RE)
text = DELIV.read_text(encoding="utf-8")
probs, warns, rec = RE_MOD.link_triple(text, W, HEX, NB, root=REPO)
print("STEP1 link_triple: tier=%s match=%r path=%r members_n=%d problems=%r"
      % (rec.get("tier"), rec.get("match"), rec.get("path"),
         len(rec.get("members") or []), probs))
assert rec.get("tier") == "SAMEDOC_LINK_EQ" and rec.get("match") is True
assert rec.get("path") is None and len(rec.get("members") or []) == 2
assert all(k not in rec for k in ("verified_path", "recomputed", "bytes"))
print("       → 单一 path 不存在；唯一可回验路径是 members（副本群）。")

# ---- 旧/新门禁：同一交付件、同一清单，实跑 check_deliverable ----
REQ = ["被核对象", "SHA256", "字节数"]
FORB = ["已生效", "可应用母本", "放行 N-5", "已入账", "已追加"]
OLD = load("_ms_ce_old", G9)
NEWMOD = load("_ms_ce_new", CAND)


def show(tag, r):
    R = r["predicates"]["R11"]
    print("STEP2 %-3s check_deliverable: verdict=%s R11=%s reverified=%d match_true=%d problems=%s"
          % (tag, r["verdict"], R["verdict"], R["reverified"], R["match_true"], R["problems"]))
    return r


r_old = show("OLD", OLD.check_deliverable(DELIV, REQ, FORB, root=REPO, doc_dir=W))
r_new = show("NEW", NEWMOD.check_deliverable(DELIV, REQ, FORB, root=REPO, doc_dir=W))

# ---- 旧门禁对「无路径绑定行」本来就是 PASS（R3-3b 只 warning）；证明反例需注入 merged rec ----
print("STEP3 说明：:155 用 g7.r11_scan（不产 merged rec），故旧门禁对该交付件的 PASS 来自"
      " R3-3b warning 不算 problem，与 link 家族无关；要复现「merged 匹配被放行」，"
      "须按『将来门禁改接 plus』注入 rec（与 MERGED_CONSUMER_AUDIT.md:133/165 一致）。")


def inject(mod, rec_):
    mod.g7.r11_scan = lambda t, d, root=None, recompute=None: ([], [], [dict(rec_)])


inject(OLD, rec)
inject(NEWMOD, rec)
i_old = show("OLD+", OLD.check_deliverable(DELIV, REQ, FORB, root=REPO, doc_dir=W))
i_new = show("NEW+", NEWMOD.check_deliverable(DELIV, REQ, FORB, root=REPO, doc_dir=W))

print("=" * 74)
print("结论：旧门禁 OLD+ verdict=%s（PASS，reverified=0 / match_true=1 静默放行）"
      % i_old["verdict"])
print("      新门禁 NEW+ verdict=%s（FAIL，%s）"
      % (i_new["verdict"], i_new["predicates"]["R11"]["problems"][0]))
print("      返回结构 top keys 相同 =", sorted(i_old.keys()) == sorted(i_new.keys()))
print("      返回结构 R11 keys 相同 =",
      sorted(i_old["predicates"]["R11"].keys()) == sorted(i_new["predicates"]["R11"].keys()))
assert i_old["verdict"] == "PASS" and i_new["verdict"] == "FAIL"
assert sorted(i_old.keys()) == sorted(i_new.keys())
assert sorted(i_old["predicates"]["R11"].keys()) == sorted(i_new["predicates"]["R11"].keys())
print("COUNTEREXAMPLE_OK")

(W / "_ms_counterexample_out.txt").write_text(
    json.dumps({"hex": HEX, "bytes": NB, "deliverable": str(DELIV),
                "old_plus": i_old["verdict"], "new_plus": i_new["verdict"],
                "new_r11_problems": i_new["predicates"]["R11"]["problems"]},
               ensure_ascii=False, indent=2), encoding="utf-8")
