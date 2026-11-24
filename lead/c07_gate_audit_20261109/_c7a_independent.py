# -*- coding: utf-8 -*-
# _c7a_independent.py — C07 身份补登件【独立实现】校验器（门禁审计专用）。
# 依据：任务书给出的三身份字段填写规则 + _c7_record_template.json 固定值口径，独立重写；
#       未参考 _c7_selfcheck.py 的实现。编号用 I 系列，避免与被审门禁的 H 系列混淆。
# 用法：python -I -X utf8 _c7a_independent.py <已填JSON路径>
# 退出码：0 = 全部 I 检查通过；1 = 存在 FAIL；2 = 用法/目标错误。
# 边界：ID 真值真伪（是否真是来源会话运行态 ID）无法离线代证，由来源会话自证；
#       本器在形制层把「不像运行态 ID 的值」判 FAIL，其余真伪不自证。
import hashlib
import json
import os
import re
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # lead/c07_gate_audit_20261109 -> lead -> repo root
TPL_PATH = os.path.join(ROOT, "lead", "c07_slot_20261109", "_c7_record_template.json")

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
# 任务书规则：这些域是既有只读域，writeDomain 不得指向它们。
READONLY_PREFIXES = (
    "lead/a_residual_20261106",
    "lead/a_residual_n1_20261108",
    "lead/pending_factpack_20261108",
    "lead/d13d14_cards_20261108",
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
)
# 任务书规则：照抄 PERF:151 内部角色冒充签发角色 = 冒签。
INTERNAL_ROLES = ("卡顿分流员·GLM", "分流报告撰写员", "独立复核员")
REJECT_EXACT = {"", "unknown", "n/a", "na", "none", "null", "todo", "待补", "待定",
                "xxx", "tbd", "tbc", "未填", "empty"}
REJECT_WORD = re.compile(r"(?i)\b(unknown|todo|tbd|n/a|null|none)\b")
PH_PAIR = re.compile(r"<[^<>]*>")        # 半角占位符 <...>
PH_FULLPAIR = re.compile(r"＜[^＜＞]*＞")  # 全角占位符 ＜...＞
PH_BARE = re.compile(r"[<>＜＞]")          # 任何裸角括号字符
SES_SHAPE = re.compile(r"sess_dwf-dwfrun-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                       r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}-actor_\d+_\d+")  # 盘上先例形制
PLAN = re.compile(r"N-\d+")              # 计划号（全文匹配与子串命中都算）
MUST_PHRASE = "正式任务书编号未落实"
HASHSTR = re.compile(r"([0-9a-fA-F]{64})/(\d+)")


def parse_hv(v):
    if isinstance(v, str):
        m = HASHSTR.fullmatch(v.strip())
        if m:
            return m.group(1).lower(), int(m.group(2))
        return None
    if isinstance(v, dict):
        h, b = v.get("sha256"), v.get("bytes")
        if isinstance(h, str) and re.fullmatch(r"[0-9a-fA-F]{64}", h) \
                and isinstance(b, int) and not isinstance(b, bool):
            return h.lower(), b
    return None


def iter_kv(o, prefix=""):
    if isinstance(o, str):
        yield prefix, o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from iter_kv(k, prefix + ".<键>")
            yield from iter_kv(v, prefix + "." + str(k))
    elif isinstance(o, (list, tuple)):
        for i, v in enumerate(o):
            yield from iter_kv(v, prefix + "[%d]" % i)


def known_ids():
    out = []
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
                out.append(r["reviewerSessionId"])
    return out


def norm(s):
    return re.sub(r"\s+", "", s).casefold() if isinstance(s, str) else None


def run_checks(path):
    out = []  # (tag, verdict, line)

    def chk(tag, name, ok, note=""):
        out.append((tag, "FAIL" if not ok else "PASS", name + (("  — " + note) if note else "")))

    def info(tag, name, note=""):
        out.append((tag, "INFO", name + (("  — " + note) if note else "")))

    with open(path, "rb") as f:
        raw = f.read()
    digest = hashlib.sha256(raw).hexdigest()
    size = len(raw)

    obj = None
    try:
        obj = json.loads(raw.decode("utf-8"))
        chk("I01", "JSON可解析", True)
    except Exception as e:
        chk("I01", "JSON可解析", False, repr(e))

    if isinstance(obj, dict):
        # I02 容器键集合精确相等（缺、多都拦）
        missing = [k for k in CONTAINER13 if k not in obj]
        extra = [k for k in obj if k not in CONTAINER13]
        chk("I02", "容器键集合==13键精确相等", not missing and not extra,
            ("缺=%s " % missing if missing else "") + ("多=%s" % extra if extra else ""))
        chk("I03", "schema==N-1-ACCEPTANCE-RECORDS/2", obj.get("schema") == "N-1-ACCEPTANCE-RECORDS/2",
            repr(obj.get("schema")))
        recs = obj.get("records")
        rec = recs[0] if isinstance(recs, list) and len(recs) == 1 and isinstance(recs[0], dict) else None
        chk("I04", "records恰1条dict", rec is not None,
            "len=%s" % (len(recs) if isinstance(recs, list) else type(recs).__name__))

        # I07/I08 全件扫描（含键、含容器层与记录层）
        ph_hits = ["%s=%s" % (p, s[:60]) for p, s in iter_kv(obj)
                   if PH_PAIR.search(s) or PH_FULLPAIR.search(s) or PH_BARE.search(s)]
        chk("I07", "全件无占位符残留（半角/全角/裸角括号）", not ph_hits, "残留=%s" % ph_hits[:3])
        bads = ["%s=%s" % (p, s[:60]) for p, s in iter_kv(obj)
                if s.strip().lower() in REJECT_EXACT or REJECT_WORD.search(s)]
        chk("I08", "全件无unknown/TODO等拒填值", not bads, "命中=%s" % bads[:3])

        known = known_ids()
        sid = rec.get("reviewerSessionId") if rec else None
        stid = rec.get("sourceTaskId") if rec else None
        role = rec.get("reviewerRole") if rec else None

        if rec is not None:
            chk("I05", "9字段名与顺序精确相等", list(rec.keys()) == FIELDS9, "实际=%s" % list(rec.keys()))
            for f3 in ("reviewerRole", "reviewerSessionId", "sourceTaskId"):
                v = rec.get(f3)
                bad = (not isinstance(v, str)) or v.strip() == "" \
                    or v.strip().lower() in REJECT_EXACT or REJECT_WORD.search(v)
                chk("I06", "%s非空非拒填值" % f3, not bad, repr(v))
            # I09 冒用面：精确 + 归一化近似（去空白/忽略大小写）
            if not isinstance(sid, str):
                chk("I09", "sessionId不冒用他件已登ID", False, "非字符串")
            else:
                dup = sid in known
                near = (not dup) and norm(sid) in {norm(k) for k in known}
                chk("I09", "sessionId不冒用他件已登ID（精确+归一化近似）", not dup and not near,
                    "精确照抄已登ID" if dup else ("近似照抄（去空白/忽略大小写后同已登ID）" if near
                                                  else "对照基数=%d" % len(known)))
            # I10 运行态形制（先例 sess_dwf-dwfrun-<UUID>-actor_<n>_<m>）
            if isinstance(sid, str):
                chk("I10", "sessionId符合运行态先例形制", SES_SHAPE.fullmatch(sid) is not None,
                    "真值真伪仍由来源会话自证；本项只拦「不像运行态ID」的值")
            # I11 冒签面：记录层角色
            rbad = isinstance(role, str) and (role.strip().casefold() in {r.strip().casefold() for r in INTERNAL_ROLES}
                                              or any(nm in role for nm in INTERNAL_ROLES))
            # I12 计划号（裸值或带装饰变体）必须逐条登记缺口语
            if isinstance(stid, str) and PLAN.search(stid.strip()):
                entries = rec.get("unresolved") if isinstance(rec.get("unresolved"), list) else []
                has = any(isinstance(e, str) and MUST_PHRASE in e for e in entries)
                chk("I12", "计划号须在unresolved登记「正式任务书编号未落实」",
                    isinstance(rec.get("unresolved"), list) and len(entries) > 0 and has,
                    "sourceTaskId=%r" % stid)
            else:
                chk("I12", "sourceTaskId非计划号（规则未触发）", True, repr(stid)[:80])
            # I13 inputHashes：必绑四件 + 全部键实算复核
            notes = []
            ih = rec.get("inputHashes")
            if not isinstance(ih, dict) or not ih:
                notes.append("inputHashes须为非空dict")
            else:
                for rel in REQUIRED_INPUTS:
                    if rel not in ih:
                        notes.append("缺必绑件:%s" % rel)
                for rel, v in ih.items():
                    pv = parse_hv(v)
                    if pv is None:
                        notes.append("格式错(需64hex/字节数):%s" % rel)
                        continue
                    p = os.path.join(ROOT, rel.replace("/", os.sep))
                    if not os.path.exists(p):
                        notes.append("文件不存在:%s" % rel)
                        continue
                    with open(p, "rb") as f:
                        data = f.read()
                    if (hashlib.sha256(data).hexdigest(), len(data)) != pv:
                        notes.append("复算不符:%s 记=%s…/%d 实=%s…/%d"
                                     % (rel, pv[0][:12], pv[1], hashlib.sha256(data).hexdigest()[:12], len(data)))
            chk("I13", "inputHashes全键实算复核（含额外键）", not notes, "; ".join(notes))
            # I14 artifactHashes：若有条目，全键实算复核
            notes = []
            ah = rec.get("artifactHashes")
            if not isinstance(ah, dict):
                notes.append("artifactHashes须为dict")
            else:
                for rel, v in ah.items():
                    pv = parse_hv(v)
                    if pv is None:
                        notes.append("格式错:%s" % rel)
                        continue
                    p = os.path.join(ROOT, rel.replace("/", os.sep))
                    if not os.path.exists(p):
                        notes.append("文件不存在:%s" % rel)
                        continue
                    with open(p, "rb") as f:
                        data = f.read()
                    if (hashlib.sha256(data).hexdigest(), len(data)) != pv:
                        notes.append("复算不符:%s" % rel)
            chk("I14", "artifactHashes全键实算复核（模板口径为空{}）", not notes, "; ".join(notes))
            # I15 timestamp
            ts = rec.get("timestamp")
            ts_ok, yr = False, ""
            if isinstance(ts, str):
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    ts_ok = True
                    if dt.year < 2020 or dt.year > 2100:
                        yr = "年份=%d 越出合理域（仅INFO，不拦）" % dt.year
                except ValueError:
                    ts_ok = False
            chk("I15", "timestamp ISO8601可解析", ts_ok, repr(ts))
            if yr:
                info("I15", "timestamp合理域未强制", yr)
            # I16 decision 值域（模板 decisionSemantics 固定口径：REGISTERED / PARTIAL）
            dec = rec.get("decision")
            chk("I16", "decision∈{REGISTERED,PARTIAL}", isinstance(dec, str) and dec in ("REGISTERED", "PARTIAL"),
                repr(dec))
        else:
            for tag, name in (("I05", "9字段名与顺序"), ("I06", "三身份字段"), ("I09", "sessionId冒用面"),
                              ("I10", "sessionId形制"), ("I12", "计划号登记"), ("I13", "inputHashes"),
                              ("I14", "artifactHashes"), ("I15", "timestamp"), ("I16", "decision值域")):
                chk(tag, name, False, "记录缺失，未检")

        # I11 冒签面（容器层 reviewer.role 也查）
        crole = obj.get("reviewer").get("role") if isinstance(obj.get("reviewer"), dict) else None
        cbad = isinstance(crole, str) and crole.strip() not in ("", "无") and \
            (crole.strip().casefold() in {r.strip().casefold() for r in INTERNAL_ROLES}
             or any(nm in crole for nm in INTERNAL_ROLES))
        rbad_rec = isinstance(role, str) and (role.strip().casefold() in {r.strip().casefold() for r in INTERNAL_ROLES}
                                              or any(nm in role for nm in INTERNAL_ROLES))
        chk("I11", "签发角色不冒用内部角色（记录层+容器reviewer.role）",
            not rbad_rec and not cbad,
            "; ".join(x for x in [("记录层=%r" % role if rbad_rec else ""),
                                  ("容器reviewer.role=%r" % crole if cbad else "")] if x))
        # I17 grade
        gr = obj.get("grade")
        gbad = (not isinstance(gr, str)) or gr.strip() == "" or bool(re.search(r"(?i)approve|放行", gr))
        chk("I17", "grade非空且无APPROVE/放行语汇", not gbad, repr(gr))
        if isinstance(gr, str) and gr.strip() != "" and gr not in ("REGISTERED", "PARTIAL"):
            info("I17", "grade未取REGISTERED/PARTIAL", repr(gr))
        # I18 六固定字段与模板逐字一致
        try:
            with open(TPL_PATH, "rb") as f:
                tpl = json.loads(f.read().decode("utf-8"))
            notes = [f6 for f6 in ("schemaNote", "natureNote", "replacementNote",
                                   "sourceTask", "hashMethod", "decisionSemantics")
                     if obj.get(f6) != tpl.get(f6)]
            chk("I18", "六固定字段与模板逐字一致（照抄）", not notes, "; ".join(notes) if notes else "")
        except Exception as e:
            info("I18", "模板不可读，跳过固定值比对", repr(e))
        # I19 writeDomain
        wd = obj.get("writeDomain")
        wd_hit = None
        if isinstance(wd, str) and wd.strip() != "":
            wdn = wd.replace("\\", "/").strip()
            for pref in READONLY_PREFIXES:
                if wdn.startswith(pref):
                    wd_hit = pref
                    break
        chk("I19", "writeDomain非空且非既有只读域",
            isinstance(wd, str) and wd.strip() != "" and wd_hit is None,
            ("指向只读域:%s" % wd_hit) if wd_hit else repr(wd)[:80])
        # I20 revisionOf
        rv = obj.get("revisionOf")
        if rv is None:
            chk("I20", "revisionOf=null（不替代既有件）", True)
        elif isinstance(rv, str):
            chk("I20", "revisionOf不声称替代a_residual两件且无占位符",
                (not ("a_residual" in rv)) and (not (PH_PAIR.search(rv) or PH_FULLPAIR.search(rv))),
                repr(rv)[:120])
        else:
            chk("I20", "revisionOf须为null或字符串", False, repr(rv))
        # I21 容器 reviewer.sessionId 冒用面 + 一致性（INFO）
        if isinstance(obj.get("reviewer"), dict):
            csid = obj["reviewer"].get("sessionId")
            if isinstance(csid, str) and csid.strip() not in ("", "无"):
                dup = csid in known
                chk("I21", "容器reviewer.sessionId不冒用已登ID且符合形制",
                    (not dup) and (SES_SHAPE.fullmatch(csid) is not None),
                    "冒用已登ID" if dup else ("形制不符" if SES_SHAPE.fullmatch(csid) is None else
                                              ("与记录层一致" if csid == sid else "与记录层不一致（另见INFO）")))
                if csid != sid:
                    info("I21", "容器reviewer.sessionId与记录层不一致",
                         ("容器=%r 记录=%r" % (csid, sid))[:160])
    else:
        for tag, name in (("I02", "容器13键"), ("I03", "schema"), ("I04", "records恰1条"),
                          ("I07", "占位符"), ("I08", "拒填值"), ("I17", "grade"),
                          ("I18", "固定字段"), ("I19", "writeDomain"), ("I20", "revisionOf")):
            chk(tag, name, False, "顶层非dict")

    print("== C07 身份补登件独立校验器（审计实现 I 系列）==")
    for tag, verdict, line in out:
        print("  [%s] %s %s" % (verdict, tag, line))
    failed = sum(1 for _, v, _ in out if v == "FAIL")
    print("I-GATE %s checks=%d failed=%d" % ("PASS" if failed == 0 else "FAIL", len(out), failed))
    print("被核对象 SHA256 = %s，字节数 = %d" % (digest, size))
    print("独立实现口径：任务书填写规则 + 模板固定值；ID 真值真伪由来源会话自证，本器不代证。")
    return 0 if failed == 0 else 1


def main(argv):
    if len(argv) < 2:
        print("用法：python -I -X utf8 _c7a_independent.py <已填JSON路径>")
        return 2
    target = os.path.abspath(argv[1])
    if not os.path.exists(target):
        print("目标不存在：%s" % target)
        return 2
    return run_checks(target)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
