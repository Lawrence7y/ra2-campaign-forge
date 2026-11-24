# -*- coding: utf-8 -*-
# _c7_selfcheck.py — C07 身份补登件填写门禁（离线文书校验；零真机、零采样、无动态内存解析）。
# 用法：python -I -X utf8 _c7_selfcheck.py <已填JSON路径>
#      python -I -X utf8 _c7_selfcheck.py --selftest   （函数级自测，不涉及任何身份值）
# 只验格式/一致性/冒用面；ID 真值真伪由来源会话自证（门禁无法也不应代证）。
import hashlib
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # lead/c07_slot_20261109 -> lead -> repo root

FIELDS9 = ["itemId", "reviewerRole", "reviewerSessionId", "sourceTaskId",
           "inputHashes", "artifactHashes", "decision", "unresolved", "timestamp"]
CONTAINER13 = ["schema", "schemaNote", "natureNote", "grade", "revisionOf",
               "independentReview", "replacementNote", "reviewer", "sourceTask",
               "writeDomain", "hashMethod", "decisionSemantics", "records"]
REQUIRED_INPUTS = [
    "lead/d13d14_cards_20261108/DECISION_QUESTIONS.md",
    "lead/pending_factpack_20261108/_fp_N10-C07_Q6.md",
    "lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md",
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
]
ANTI_COPY_SOURCES = [
    "lead/a_residual_20261106/ACCEPTANCE_RECORDS.json",
    "lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json",
]
PLACEHOLDER_PAT = re.compile(r"<[^>]*>")
BAD_VALUES = {"unknown", "n/a", "na", "none", "null", "todo", "待补", "xxx", "tbd", ""}


def parse_hash_value(v):
    # 接受 "64hex/字节数" 字符串 或 {"sha256": .., "bytes": n}
    if isinstance(v, str):
        m = re.fullmatch(r"([0-9a-fA-F]{64})/(\d+)", v.strip())
        if not m:
            return None
        return m.group(1).lower(), int(m.group(2))
    if isinstance(v, dict):
        h = v.get("sha256")
        b = v.get("bytes")
        if isinstance(h, str) and re.fullmatch(r"[0-9a-fA-F]{64}", h) and isinstance(b, int):
            return h.lower(), b
    return None


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


def load_known_session_ids():
    known = set()
    for rel in ANTI_COPY_SOURCES:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(p):
            continue
        try:
            with open(p, "rb") as f:
                obj = json.loads(f.read().decode("utf-8"))
        except (OSError, ValueError):
            continue
        recs = obj if isinstance(obj, list) else obj.get("records", []) if isinstance(obj, dict) else []
        for r in recs:
            if isinstance(r, dict) and isinstance(r.get("reviewerSessionId"), str):
                known.add(r["reviewerSessionId"])
    return known


def run_checks(path):
    results = []

    def chk(name, ok, note=""):
        results.append((name, bool(ok), note))

    raw = open(path, "rb").read()
    digest = hashlib.sha256(raw).hexdigest()
    size = len(raw)

    obj = None
    try:
        obj = json.loads(raw.decode("utf-8"))
        chk("H01 JSON可解析", True)
    except Exception as e:
        chk("H01 JSON可解析", False, str(e))

    if isinstance(obj, dict):
        missing = [k for k in CONTAINER13 if k not in obj]
        chk("H02 容器13键齐（N-1/2形制）", not missing, "缺=%s" % missing if missing else "")
        chk("H03 schema=N-1-ACCEPTANCE-RECORDS/2", obj.get("schema") == "N-1-ACCEPTANCE-RECORDS/2",
            repr(obj.get("schema")))
        recs = obj.get("records")
        chk("H04 records恰1条", isinstance(recs, list) and len(recs) == 1,
            "len=%s" % (len(recs) if isinstance(recs, list) else "?"))
        rec = recs[0] if isinstance(recs, list) and len(recs) == 1 and isinstance(recs[0], dict) else None
        if rec is not None:
            keys = list(rec.keys())
            chk("H05 9字段名与顺序==NEXT:23实文", keys == FIELDS9, "实际=%s" % keys)
            for f3 in ("reviewerRole", "reviewerSessionId", "sourceTaskId"):
                v = rec.get(f3)
                ok = isinstance(v, str) and v.strip().lower() not in BAD_VALUES
                chk("H06 %s非空非拒填值" % f3, ok, repr(v))
            resid = [s[:60] for s in iter_strings(rec) if PLACEHOLDER_PAT.search(s)]
            chk("H07 记录内无占位符残留", not resid, "残留=%s" % resid[:3])
            bad = [s[:60] for s in iter_strings(rec) if s.strip().lower() in BAD_VALUES]
            chk("H08 记录内无unknown/TODO等拒填值", not bad, "命中=%s" % bad[:3])
            known = load_known_session_ids()
            sid = rec.get("reviewerSessionId")
            chk("H09 sessionId不冒用他件已登ID", isinstance(sid, str) and sid not in known,
                "与a_residual两件已登ID冲突" if sid in known else "对照基数=%d" % len(known))
            stid = rec.get("sourceTaskId")
            unr = rec.get("unresolved")
            if isinstance(stid, str) and re.fullmatch(r"N-\d+", stid.strip()):
                ok = isinstance(unr, list) and len(unr) > 0
                chk("H10 sourceTaskId为计划号时unresolved必非空", ok,
                    "计划号须在unresolved登记「正式任务书编号未落实」（先例教训 YI_SUPERSEDE:90）")
            else:
                chk("H10 sourceTaskId非裸计划号（或已按规登记）", True, "计划号规则未触发")
            ih = rec.get("inputHashes")
            ih_ok, ih_notes = True, []
            if not isinstance(ih, dict) or not ih:
                ih_ok = False
                ih_notes.append("inputHashes须为非空dict")
            else:
                for rel in REQUIRED_INPUTS:
                    if rel not in ih:
                        ih_ok = False
                        ih_notes.append("缺必绑件:%s" % rel)
                        continue
                    pv = parse_hash_value(ih[rel])
                    if pv is None:
                        ih_ok = False
                        ih_notes.append("格式错(需 64hex/字节数):%s" % rel)
                        continue
                    p = os.path.join(ROOT, rel.replace("/", os.sep))
                    if not os.path.exists(p):
                        ih_ok = False
                        ih_notes.append("文件不存在:%s" % rel)
                        continue
                    with open(p, "rb") as f:
                        data = f.read()
                    got = (hashlib.sha256(data).hexdigest(), len(data))
                    if got != pv:
                        ih_ok = False
                        ih_notes.append("复算不符:%s 记=%s 实=%s/%d" % (rel, pv[0][:12] + "…", got[0][:12] + "…", got[1]))
            chk("H11 inputHashes四件实算复核", ih_ok, "; ".join(ih_notes))
            ts = rec.get("timestamp")
            ts_ok = False
            if isinstance(ts, str):
                try:
                    datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    ts_ok = True
                except ValueError:
                    ts_ok = False
            chk("H12 timestamp ISO8601可解析", ts_ok, repr(ts))
        else:
            for name in ("H05", "H06", "H07", "H08", "H09", "H10", "H11", "H12"):
                chk(name, False, "记录缺失，未检")
        top_resid = [s[:60] for s in iter_strings({k: v for k, v in obj.items() if k != "records"})
                     if PLACEHOLDER_PAT.search(s)]
        chk("H13 容器层无占位符残留", not top_resid, "残留=%s" % top_resid[:3])
    else:
        for name in ("H02", "H03", "H04", "H05", "H06", "H07", "H08", "H09", "H10", "H11", "H12", "H13"):
            chk(name, False, "顶层非dict")

    print("== C07 身份补登件门禁 ==")
    for name, ok, note in results:
        print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name, ("  — " + note) if note else ""))
    failed = sum(1 for _, ok, _ in results if not ok)
    print("GATE %s checks=%d failed=%d" % ("PASS" if failed == 0 else "FAIL", len(results), failed))
    print("被核对象 SHA256 = `%s`，字节数 = %d" % (digest, size))
    print("注：ID 真值真伪由来源会话自证；本门禁只验格式、一致性与冒用面。")
    return 0 if failed == 0 else 1


def selftest():
    # 函数级自测：不构造任何身份值，仅验解析与判定逻辑。
    assert parse_hash_value("0" * 64 + "/123") == ("0" * 64, 123)
    assert parse_hash_value({"sha256": "a" * 64, "bytes": 5}) == ("a" * 64, 5)
    assert parse_hash_value("nothex/5") is None
    assert parse_hash_value("0" * 63 + "/5") is None
    assert list(iter_strings({"a": ["x", {"b": "y"}]})) == ["a", "x", "b", "y"]
    assert PLACEHOLDER_PAT.search("<来源会话sessionId>") is not None
    assert PLACEHOLDER_PAT.search("sess_dwf-dwfrun-<UUID>-actor_1_1 说明形") is not None  # 格式描述亦会被拦（用于说明，不用于填值）
    known = load_known_session_ids()
    assert isinstance(known, set)
    assert re.fullmatch(r"N-\d+", "N-11") is not None
    assert re.fullmatch(r"N-\d+", "TASK-20261108-01") is None
    print("SELFTEST PASS（解析/占位/计划号判定逻辑正常；对照已登ID基数=%d）" % len(known))
    return 0


def main(argv):
    if len(argv) >= 2 and argv[1] == "--selftest":
        return selftest()
    if len(argv) < 2:
        print("用法：python -I -X utf8 _c7_selfcheck.py <已填JSON路径> | --selftest")
        return 2
    target = os.path.abspath(argv[1])
    if not os.path.exists(target):
        print("目标不存在：%s" % target)
        return 2
    return run_checks(target)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
