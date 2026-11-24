# -*- coding: utf-8 -*-
# _c7v_independent.py — C07 登记件独立校验器（复核员自实现，未参考撰写人实现）。
# 依据：_c7_SLOT_PREP.md §5 规格表 + §6 模板固定值 + NEXT:119 身份原则。
# 用法：python -I -X utf8 _c7v_independent.py <已填JSON路径>
import hashlib
import json
import os
import re
import sys
from datetime import datetime

ROOT = "D:/Project/ra2-campaign-forge"
TPL_PATH = ROOT + "/lead/c07_slot_20261109/_c7_record_template.json"
REQUIRED = [
    "lead/d13d14_cards_20261108/DECISION_QUESTIONS.md",
    "lead/pending_factpack_20261108/_fp_N10-C07_Q6.md",
    "lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md",
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
]
ANTI_COPY = [
    "lead/a_residual_20261106/ACCEPTANCE_RECORDS.json",
    "lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json",
]
FIELDS9 = ["itemId", "reviewerRole", "reviewerSessionId", "sourceTaskId",
           "inputHashes", "artifactHashes", "decision", "unresolved", "timestamp"]
CONTAINER13 = ["schema", "schemaNote", "natureNote", "grade", "revisionOf",
               "independentReview", "replacementNote", "reviewer", "sourceTask",
               "writeDomain", "hashMethod", "decisionSemantics", "records"]
BAD = {"", "unknown", "n/a", "na", "none", "null", "todo", "待补", "xxx", "tbd"}
INTERNAL_ROLES = ["卡顿分流员·GLM", "分流报告撰写员", "独立复核员"]
SID_RE = re.compile(
    r"^sess_dwf-dwfrun-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}-actor_\d+_\d+$")
WORD_BAD = re.compile(r"\b(unknown|todo|tbd|xxx|n/a)\b", re.IGNORECASE)
FIXED6 = ["schemaNote", "natureNote", "replacementNote", "sourceTask",
          "hashMethod", "decisionSemantics"]

checks = []


def chk(name, ok, note=""):
    checks.append((name, bool(ok), note))


def iter_strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from iter_strings(k)
            yield from iter_strings(v)
    elif isinstance(o, (list, tuple)):
        for v in o:
            yield from iter_strings(v)


def load_known():
    known, known_norm = set(), set()
    for rel in ANTI_COPY:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(p):
            continue
        try:
            o = json.loads(open(p, "rb").read().decode("utf-8"))
        except (OSError, ValueError):
            continue
        rs = o if isinstance(o, list) else o.get("records", []) if isinstance(o, dict) else []
        for r in rs:
            if isinstance(r, dict) and isinstance(r.get("reviewerSessionId"), str):
                known.add(r["reviewerSessionId"])
                known_norm.add(r["reviewerSessionId"].strip().casefold())
    return known, known_norm


def load_tpl():
    return json.loads(open(TPL_PATH, "rb").read().decode("utf-8"))


def value_basics(label, v):
    probs = []
    if not isinstance(v, str):
        return ["%s非字符串:%r" % (label, v)]
    if v.strip().lower() in BAD:
        probs.append("%s拒填值:%r" % (label, v))
    if WORD_BAD.search(v):
        probs.append("%s词级拒填:%r" % (label, v[:40]))
    if "待补" in v:
        probs.append("%s含「待补」:%r" % (label, v[:40]))
    if re.search(r"[<>＜＞〈〉]", v):
        probs.append("%s占位/角字符残留:%r" % (label, v[:40]))
    return probs


def role_problems(label, v):
    probs = value_basics(label, v)
    if isinstance(v, str):
        for role in INTERNAL_ROLES:
            if role in v:
                probs.append("%s内部角色冒签(命中%s):%r" % (label, role, v))
    return probs


def sid_problems(label, v, known, known_norm):
    probs = value_basics(label, v)
    if not isinstance(v, str):
        return probs
    s = v.strip()
    if s in known:
        probs.append("%s照抄已登ID(精确):%s…" % (label, s[:24]))
    elif s.casefold() in known_norm:
        probs.append("%s近似照抄已登ID(归一化):%s…" % (label, s[:24]))
    if not SID_RE.match(s):
        probs.append("%s非运行态形制(需 sess_dwf-dwfrun-<UUID>-actor_<n>_<m>):%r" % (label, s[:32]))
    return probs


def verify_hash_entry(rel, v):
    if isinstance(v, str):
        m = re.fullmatch(r"([0-9a-fA-F]{64})/(\d+)", v.strip())
        if not m:
            return "格式错(需64hex/字节数):%s" % rel
        h, n = m.group(1).lower(), int(m.group(2))
    elif isinstance(v, dict):
        h, n = v.get("sha256"), v.get("bytes")
        if not (isinstance(h, str) and re.fullmatch(r"[0-9a-fA-F]{64}", h) and isinstance(n, int)):
            return "格式错(dict):%s" % rel
        h = h.lower()
    else:
        return "类型错:%s" % rel
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.exists(p):
        return "文件不存在:%s" % rel
    data = open(p, "rb").read()
    got = (hashlib.sha256(data).hexdigest(), len(data))
    if got != (h, n):
        return "复算不符:%s" % rel
    return None


def run(path):
    raw = open(path, "rb").read()
    digest = hashlib.sha256(raw).hexdigest()
    size = len(raw)
    obj = None
    try:
        obj = json.loads(raw.decode("utf-8"))
        chk("I01 JSON可解析", True)
    except Exception as e:
        chk("I01 JSON可解析", False, str(e))

    if isinstance(obj, dict):
        missing = [k for k in CONTAINER13 if k not in obj]
        extra = [k for k in obj if k not in CONTAINER13]
        chk("I02 容器键恰13(无缺无多)", not missing and not extra,
            "缺=%s 多=%s" % (missing, extra))
        chk("I03 schema精确串", obj.get("schema") == "N-1-ACCEPTANCE-RECORDS/2",
            repr(obj.get("schema")))
        recs = obj.get("records")
        ok4 = isinstance(recs, list) and len(recs) == 1 and isinstance(recs[0], dict)
        chk("I04 records恰1条", isinstance(recs, list) and len(recs) == 1,
            "len=%s" % (len(recs) if isinstance(recs, list) else "?"))
        tpl = load_tpl()
        known, known_norm = load_known()
        if ok4:
            rec = recs[0]
            chk("I05 9字段名与顺序", list(rec.keys()) == FIELDS9, "实际=%s" % list(rec.keys()))
            probs = role_problems("记录reviewerRole", rec.get("reviewerRole"))
            chk("I06 记录层角色非拒填/非占位/非内部角色", not probs, "; ".join(probs))
            res = []
            for s in iter_strings(obj):
                if re.search(r"[<>＜＞]", s) or "〈" in s or "〉" in s:
                    res.append(s[:40])
            chk("I07 全件无占位/角字符残留(半角+全角)", not res, "残留=%s" % res[:3])
            bad = []
            for s in iter_strings(rec):
                st = s.strip().lower()
                if st in BAD or WORD_BAD.search(s) or "待补" in s:
                    bad.append(s[:40])
            chk("I08 记录内无拒填值(精确+词级)", not bad, "命中=%s" % bad[:3])
            probs = sid_problems("记录sessionId", rec.get("reviewerSessionId"), known, known_norm)
            chk("I09/I10 记录层sessionId非冒用(精确+归一)且运行态形制", not probs, "; ".join(probs))
            rev = obj.get("reviewer")
            crole = rev.get("role") if isinstance(rev, dict) else None
            probs = role_problems("容器reviewer.role", crole)
            chk("I11 容器role非拒填/非占位/非内部角色", not probs, "; ".join(probs))
            stid = rec.get("sourceTaskId")
            unr = rec.get("unresolved")
            probs = value_basics("sourceTaskId", stid)
            if isinstance(stid, str) and re.search(r"\bN-\d+\b", stid):
                ok = isinstance(unr, list) and any(
                    isinstance(u, str) and "正式任务书编号未落实" in u for u in unr)
                if not ok:
                    probs.append("计划号须在unresolved登记「正式任务书编号未落实」:%r" % (unr,))
            chk("I12 计划号登记(子串触发+登记语必验)", not probs, "; ".join(probs))
            ih = rec.get("inputHashes")
            errs = []
            if not isinstance(ih, dict) or not ih:
                errs.append("inputHashes须非空dict")
            else:
                for rel in REQUIRED:
                    if rel not in ih:
                        errs.append("缺必绑:%s" % rel)
                for rel, v in ih.items():
                    e = verify_hash_entry(rel, v)
                    if e:
                        errs.append(e)
            chk("I13 inputHashes全键实算(含额外键)", not errs, "; ".join(errs[:5]))
            ah = rec.get("artifactHashes")
            errs = []
            if not isinstance(ah, dict):
                errs.append("artifactHashes须dict")
            else:
                for rel, v in ah.items():
                    e = verify_hash_entry(rel, v)
                    if e:
                        errs.append(e)
            chk("I14 artifactHashes全键实算", not errs, "; ".join(errs[:5]))
            ts = rec.get("timestamp")
            ok15, note15 = False, repr(ts)
            if isinstance(ts, str):
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    ok15 = ("T" in ts or " " in ts) and (2020 <= dt.year <= 2035)
                    if not ok15:
                        note15 = "缺时间成分或年份异常:" + repr(ts)
                except ValueError:
                    ok15 = False
            chk("I15 timestamp ISO8601且含时间成分", ok15, note15)
            d = rec.get("decision")
            ok16 = isinstance(d, str) and (d.strip().startswith("REGISTERED")
                                           or d.strip().startswith("PARTIAL"))
            chk("I16 decision值域{REGISTERED,PARTIAL}", ok16, repr(d))
            g = obj.get("grade")
            ok17 = (isinstance(g, str)
                    and not re.search(r"[<＜>＞]", g)
                    and (g.strip().startswith("REGISTERED") or g.strip().startswith("PARTIAL"))
                    and not re.search(r"APPROVE|放行|签署", g, re.IGNORECASE))
            chk("I17 grade定档{REGISTERED,PARTIAL}且禁签署语汇", ok17, repr(g))
            diffs = [k for k in FIXED6 if obj.get(k) != tpl.get(k)]
            chk("I18 六固定字段与模板逐字一致", not diffs, "不一致=%s" % diffs)
            wd = obj.get("writeDomain")
            ok19 = (isinstance(wd, str) and wd.strip().startswith("lead/")
                    and not re.search(r"[<＜>＞]", wd) and wd.strip().lower() not in BAD)
            chk("I19 writeDomain形制合法", ok19, repr(wd))
            chk("I20 revisionOf==null", obj.get("revisionOf") is None,
                repr(obj.get("revisionOf")))
            csid = rev.get("sessionId") if isinstance(rev, dict) else None
            probs = sid_problems("容器sessionId", csid, known, known_norm)
            rsid = rec.get("reviewerSessionId")
            if (isinstance(csid, str) and isinstance(rsid, str)
                    and SID_RE.match(csid.strip()) and SID_RE.match(rsid.strip())
                    and csid.strip() != rsid.strip()):
                probs.append("容器与记录sessionId不一致")
            chk("I21 容器sessionId非冒用/运行态形制/与记录一致", not probs, "; ".join(probs))
            chk("I22 itemId固定值", rec.get("itemId") == "N10-C07-Q6-identity",
                repr(rec.get("itemId")))
            probs23 = []
            if not isinstance(unr, list):
                probs23.append("unresolved须list:%r" % (unr,))
            else:
                for u in unr:
                    if not isinstance(u, str):
                        probs23.append("非字符串项:%r" % (u,))
            chk("I23 unresolved为字符串列表", not probs23, "; ".join(probs23))
        else:
            for nm in ("I05", "I06", "I07", "I08", "I09/I10", "I12", "I13", "I14",
                       "I15", "I16", "I22", "I23"):
                chk(nm, False, "记录缺失，未检")
            chk("I11 容器role非拒填/非占位/非内部角色",
                not role_problems("容器reviewer.role",
                                  obj.get("reviewer", {}).get("role")
                                  if isinstance(obj.get("reviewer"), dict) else None))
            chk("I17 grade定档且禁签署语汇", False, "记录缺失")
            chk("I18 六固定字段与模板逐字一致", False, "记录缺失")
            chk("I19 writeDomain形制合法", False, "记录缺失")
            chk("I20 revisionOf==null", obj.get("revisionOf") is None)
            chk("I21 容器sessionId校验", False, "记录缺失")
    else:
        for i in range(2, 24):
            chk("I%02d 顶层非dict，未检" % i, False)

    print("== C07 独立复核校验器（_c7v_independent）==")
    for name, ok, note in checks:
        print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name, ("  — " + note) if note else ""))
    failed = sum(1 for _, ok, _ in checks if not ok)
    print("INDEP %s checks=%d failed=%d" % ("PASS" if failed == 0 else "FAIL",
                                            len(checks), failed))
    print("被核对象 SHA256 = %s，字节数 = %d" % (digest, size))
    return 0 if failed == 0 else 1


def main(argv):
    if len(argv) < 2:
        print("用法：python -I -X utf8 _c7v_independent.py <已填JSON路径>")
        return 2
    target = os.path.abspath(argv[1])
    if not os.path.exists(target):
        print("目标不存在：%s" % target)
        return 2
    return run(target)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
