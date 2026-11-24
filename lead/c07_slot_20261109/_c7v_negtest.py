# -*- coding: utf-8 -*-
# _c7v_negtest.py — 复核员门禁负测：填错样例逐项验证。真实已登 ID 只在内存中出现
# （monkeypatch open 使 run_checks 读内存件），不写盘、不打印；输出行对 sess_* 形态一律脱敏。
import builtins, contextlib, hashlib, importlib.util, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("c7selfcheck", os.path.join(HERE, "_c7_selfcheck.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ROOT = os.path.dirname(os.path.dirname(HERE))

SESS_MASK = re.compile(r"sess[_-][A-Za-z0-9_.\-]{4,}")
def scrub(s):
    return SESS_MASK.sub("sess_<SCRUBBED>", s)

# ---- 0. a_residual 两件结构审计（只读，值脱敏）----
p_r2 = os.path.join(ROOT, "lead", "a_residual_n1_20261108", "ACCEPTANCE_RECORDS.json")
p_r1 = os.path.join(ROOT, "lead", "a_residual_20261106", "ACCEPTANCE_RECORDS.json")
obj2 = json.loads(open(p_r2, "rb").read().decode("utf-8"))
print("== r2 结构 ==")
print("top=dict", isinstance(obj2, dict), "| schema =", obj2.get("schema"))
print("topKeys=", list(obj2.keys()))
recs2 = obj2.get("records", [])
print("records=", len(recs2))
kcounts = {len(r) for r in recs2 if isinstance(r, dict)}
print("每条键数集合=", kcounts)
orders = {tuple(r.keys()) for r in recs2 if isinstance(r, dict)}
print("键序==FIELDS9 全部一致 =", orders == {tuple(mod.FIELDS9)})
stid = {r.get("sourceTaskId") for r in recs2}
print("sourceTaskId 取值集合=", stid)
sids = {r.get("reviewerSessionId") for r in recs2}
print("reviewerSessionId 唯一值个数 =", len(sids), "| 格式形(脱敏)=", scrub(sorted(sids)[0][:20] + "…") if sids else None)
obj1 = json.loads(open(p_r1, "rb").read().decode("utf-8"))
print("== r1 结构 ==")
print("top=list", isinstance(obj1, list), "| records=", len(obj1))
miss = set()
for r in obj1:
    if isinstance(r, dict):
        for k in ("reviewerRole", "reviewerSessionId"):
            if k not in r:
                miss.add(k)
print("r1 身份两键缺位情况 =", sorted(miss) if miss else "均存在")

known = mod.load_known_session_ids()
known_id = sorted(known)[0] if known else None
print("anti-copy 已登 ID 基数 =", len(known))

# ---- 1. 构造 fixtures（全部内存件）----
def real_hashes():
    out = {}
    for rel in mod.REQUIRED_INPUTS:
        data = open(os.path.join(ROOT, rel.replace("/", os.sep)), "rb").read()
        out[rel] = "%s/%d" % (hashlib.sha256(data).hexdigest(), len(data))
    return out

IH = real_hashes()
FIX_TS = "2026-11-09T01:30:00+08:00"

def container(sid, role):
    return {
        "schema": "N-1-ACCEPTANCE-RECORDS/2",
        "schemaNote": "固定格式值照抄",
        "natureNote": "固定格式值照抄",
        "grade": "REGISTERED",
        "revisionOf": None,
        "independentReview": "未做",
        "replacementNote": "固定格式值照抄",
        "reviewer": {"role": role, "sessionId": sid, "note": "无"},
        "sourceTask": "C07 来源 N-11",
        "writeDomain": "lead/c07_slot_20261109/",
        "hashMethod": "固定格式值照抄",
        "decisionSemantics": "固定格式值照抄",
        "records": [],
    }

def record(sid="sess_FAKE-TEST-VALUE-0000-actor_9_9", role="测试用占位角色R", stid="NT-11", unr=None, ih=None, ts=FIX_TS, fields=None):
    rec = {
        "itemId": "N10-C07-Q6-identity",
        "reviewerRole": role,
        "reviewerSessionId": sid,
        "sourceTaskId": stid,
        "inputHashes": dict(ih if ih is not None else IH),
        "artifactHashes": {},
        "decision": "REGISTERED——来源会话身份补登完成（Q6 行政动作）",
        "unresolved": list(unr) if unr is not None else [],
        "timestamp": ts,
    }
    if fields is not None:
        rec = {k: rec[k] for k in fields}
    return rec

def run_fixture(name, obj, expect_fail):
    fixture_abs = os.path.join(HERE, "_c7v_inmem_fixture.json")
    raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    real_open = builtins.open
    def fake_open(p, *a, **k):
        if os.path.abspath(str(p)) == fixture_abs:
            return io.BytesIO(raw)
        return real_open(p, *a, **k)
    builtins.open = fake_open
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = mod.run_checks(fixture_abs)
        out = buf.getvalue()
    finally:
        builtins.open = real_open
    failed = [l.strip() for l in out.splitlines() if "[FAIL]" in l]
    gate = [l.strip() for l in out.splitlines() if l.startswith("GATE")]
    okset = expect_fail - set(x.split("]")[1].split()[0] for x in failed)
    print("-- %s: exit=%d %s" % (name, rc, gate[0] if gate else "?"))
    for f in failed:
        nm = f.split("]")[1].split()[0]
        print("     FAIL-> %s | %s" % (nm, scrub(f[:110])))
    verdict = "符合预期" if (set(x.split("]")[1].split()[0] for x in failed) == expect_fail and rc == (1 if expect_fail else 0)) else "★不符预期"
    print("     预期失败集=%s 实际=%s => %s" % (sorted(expect_fail), sorted(x.split(']')[1].split()[0] for x in failed), verdict))
    return rc

F9 = mod.FIELDS9
FIXTURES = [
    ("A 照抄他件已登ID(内存值)", {**container(known_id, "R"), "records": [record(sid=known_id)]}, {"H09"}),
    ("B sessionId=unknown", {**container("unknown", "R"), "records": [record(sid="unknown")]}, {"H06", "H08"}),
    ("C 计划号N-11且unresolved空", {**container("s", "R"), "records": [record(stid="N-11")]}, {"H10"}),
    ("D 冒签内部角色(卡顿分流员·GLM)", {**container("s", "卡顿分流员·GLM"), "records": [record(role="卡顿分流员·GLM")]}, set()),
    ("E inputHashes错一字符", {**container("s", "R"), "records": [record(ih={k: (v[:-1] + ("0" if v[-1] != "0" else "1")) if i == 0 else v for i, (k, v) in enumerate(IH.items())})]}, {"H11"}),
    ("F timestamp非ISO", {**container("s", "R"), "records": [record(ts="2026-11-09 01:30:00 上午")]}, {"H12"}),
    ("G 9字段顺序错", {**container("s", "R"), "records": [record(fields=[F9[1], F9[0]] + F9[2:])]}, {"H05"}),
    ("H 占位残留", {**container("s", "R"), "records": [record(sid="<来源会话sessionId>")]}, {"H07"}),
]
print("\n== 门禁负测 ==")
for name, obj, exp in FIXTURES:
    run_fixture(name, obj, exp)
print("\n== 说明 ==")
print("A 样例的 sessionId 为内存中读出的已登 ID：不落盘、不打印（输出已脱敏）。")
