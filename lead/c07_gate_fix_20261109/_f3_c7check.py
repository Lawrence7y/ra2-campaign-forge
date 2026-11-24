# -*- coding: utf-8 -*-
# _f3_c7check.py — C07 身份补登件填写门禁【增强版 F3】（离线文书校验；零真机、零采样、无动态内存解析）。
# 用法：python -I -X utf8 _f3_c7check.py <已填JSON路径>
#      python -I -X utf8 _f3_c7check.py --selftest   （函数级自测，不涉及任何身份值）
# 与原版 _c7_selfcheck.py 的关系：H01–H13（15 个打印项）逐字镜像原判据，方向只收紧不放松；
# 新增 N01–N21 对应审计缺口 G1–G15（见 C07_SELFCHECK_AUDIT.md §4.4）：
#   N01-N03=G1 内部角色黑名单（记录层+容器层+两层一致）
#   N04=G2 decision 值域；N05=G3 grade 值域；N06=G4 六固定字段与模板逐字一致
#   N07-N09=G5/G14 sessionId 运行态形制（记录层+容器层+两层一致）
#   N10=G6 冒用面归一化比对（对照集不可用即 FAIL）；N11=G7 计划号子串触发；N12=G8 登记语必验
#   N13=G9 容器键集合精确相等；N14=G10 占位符扩展面（全角/裸角）；N15-N16=G11 inputHashes/artifactHashes 全键实算
#   N17=G15 itemId 固定值；N18-N19=G12 timestamp 合理域/unresolved 形制；N20=G14 容器 reviewer 形制；N21=G9补 writeDomain 只读域面
#   G13（原门禁绑定行带反引号）在本器输出形制中修正：绑定行无反引号（selftest 内有断言）。
# 只验格式/一致性/冒用面；ID 真值真伪由来源会话自证（本门禁无法也不应代证）——
# N07/N08 的形制校验只保证「值长得像运行态 ID」，绝不保证「值就是真 ID」（T29 边界）。
import hashlib
import json
import os
import re
import sys
import unicodedata
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # lead/c07_gate_fix_20261109 -> lead -> repo root
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
PLACEHOLDER_PAT = re.compile(r"<[^>]*>")
BAD_VALUES = {"unknown", "n/a", "na", "none", "null", "todo", "待补", "xxx", "tbd", ""}

# ---- 增强常量（出处在注释标注） ----
# G1：PERF_REPAIR_HANDOFF.md:151 实文三内部角色（词干子串，防「卡顿分流员·GLM（代签）」类变体）。
# 注意黑名单只收这三个词干，不得收「GLM」「撰写员」等宽子串（合法签发角色如「C07 身份补登签发员·GLM」含 ·GLM）。
INTERNAL_ROLE_STEMS = ["卡顿分流员", "分流报告撰写员", "独立复核员"]
# G2/G3：DECISION_QUESTIONS.md:121「非技术裁决——行政动作」+ 模板 decisionSemantics/grade 占位口径。
DECISION_DOMAIN = {"REGISTERED", "PARTIAL"}
GRADE_DOMAIN = {"REGISTERED", "PARTIAL"}
SIGN_WORDS = ["approve", "放行", "签署"]  # 只用于 decision/grade 值，不做全文扫描（固定字段 natureNote 合法含「签署」字样）
# G5/G14：运行态先例形制（a_residual_n1_20261108 已登 ID sess_dwf-dwfrun-324c613e-…-actor_3_1 实文口径）。
SESSION_RE = re.compile(
    r"sess_dwf-dwfrun-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}-actor_\d+_\d+")
NIL_UUID = "0" * 32
# G4：模板中标注「（固定格式值，照抄）」的六个固定字段。
FIXED6 = ["schemaNote", "natureNote", "replacementNote", "sourceTask", "hashMethod", "decisionSemantics"]
# G8：登记语（模板 unresolved 占位符 + YI_SUPERSEDE 先例口径 + T05 合规登记语实文）。
REGISTRATION_PHRASE = "正式任务书编号未落实"
# G10：占位符扩展面——半角对由 PLACEHOLDER_PAT 拦；本正则拦全角对与任何裸角字符。
BRACKET_PAT = re.compile(r"[<>＜＞]")
# G12：timestamp 合理域（本仓登记件均在 2026 年；区间放宽到 2020-2040，须含时间成分）。
TS_YEAR_MIN, TS_YEAR_MAX = 2020, 2040
TS_TIME_PAT = re.compile(r"\d{1,2}:\d{2}")
# G13：本器绑定行形制（无反引号）。
BINDING_FMT = "被核对象 SHA256 = %s，字节数 = %d"
# G11 的 writeDomain 只读域面（不得把补登件写进这些既有只读域；c07_slot 不在列——模板建议就地填用）。
READONLY_DOMAIN_PREFIXES = [
    "lead/pending_factpack_20261108", "lead/d13d14_cards_20261108",
    "lead/perf_repair_n11_20261108", "lead/nextstep_plan_20261106",
    "lead/a_residual_20261106", "lead/a_residual_n1_20261108",
    "lead/c07_gate_audit_20261109", "lead/c07_gate_fix_20261109",
]


def parse_hash_value(v):
    # 接受 "64hex/字节数" 字符串 或 {"sha256": .., "bytes": n}（与原版逐字一致）
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
    # 与原版逐字一致（H09 用）
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


def load_known_ids_ext():
    # N10 用：返回（原始ID集合, 归一化ID集合, 成功装载的对照源数）
    known, known_norm, loaded = set(), set(), 0
    for rel in ANTI_COPY_SOURCES:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(p):
            continue
        try:
            with open(p, "rb") as f:
                obj = json.loads(f.read().decode("utf-8"))
        except (OSError, ValueError):
            continue
        loaded += 1
        recs = obj if isinstance(obj, list) else obj.get("records", []) if isinstance(obj, dict) else []
        for r in recs:
            if isinstance(r, dict) and isinstance(r.get("reviewerSessionId"), str):
                known.add(r["reviewerSessionId"])
                known_norm.add(normalize_id(r["reviewerSessionId"]))
    return known, known_norm, loaded


def load_template():
    try:
        with open(TPL_PATH, "rb") as f:
            return json.loads(f.read().decode("utf-8")), None
    except Exception as e:  # 模板不可读 → 依赖模板的检查一律 FAIL（fail-closed）
        return None, str(e)


def normalize_id(s):
    # G6 归一化：NFKC + 去空白 + 去格式字符（零宽等 Cf）+ casefold —— 防 T19 尾随空格/大小写变体照抄。
    t = unicodedata.normalize("NFKC", s)
    return "".join(ch for ch in t if not ch.isspace() and unicodedata.category(ch) != "Cf").casefold()


def nfkc(s):
    return unicodedata.normalize("NFKC", s)


def role_stem_hits(role):
    # G1：NFKC 归一后做词干子串匹配（「卡顿分流员·GLM（代签）」命中「卡顿分流员」）。
    if not isinstance(role, str):
        return []
    t = nfkc(role)
    return [stem for stem in INTERNAL_ROLE_STEMS if stem in t]


def sign_word_hits(v):
    t = nfkc(v).casefold()
    return [w for w in SIGN_WORDS if w in t]


def session_shape(sid):
    # G5：返回 (ok, note)。只验形制与「非 nil UUID」，不验真值。
    if not isinstance(sid, str):
        return False, "非字符串"
    if not SESSION_RE.fullmatch(sid):
        return False, "不符 sess_dwf-dwfrun-<UUID>-actor_<n>_<m> 运行态形制"
    m = re.search(r"([0-9a-fA-F]{8})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{12})", sid)
    if m and "".join(m.groups()).lower() == NIL_UUID:
        return False, "UUID 为全零（nil UUID），非运行态可生成值"
    return True, "形制相符（只验形制，不验真值；真值须来源会话自证）"


def resolve_repo_path(rel):
    # G11：键必须是仓库相对路径，拒绝绝对路径与 .. 越界。
    if not isinstance(rel, str) or not rel.strip():
        return None
    if os.path.isabs(rel):
        return None
    parts = rel.replace("\\", "/").split("/")
    if any(p == ".." for p in parts):
        return None
    p = os.path.abspath(os.path.join(ROOT, rel.replace("/", os.sep)))
    rootn = os.path.normcase(os.path.abspath(ROOT))
    pn = os.path.normcase(p)
    if pn != rootn and not pn.startswith(rootn + os.sep):
        return None
    return p


def verify_binding(d, key, notes):
    # 对 d[key]（路径→指纹值）做全键实算复核；失败往 notes 追加原因。
    pv = parse_hash_value(d.get(key))
    if pv is None:
        notes.append("格式错(需 64hex/字节数):%s" % key)
        return False
    p = resolve_repo_path(key)
    if p is None:
        notes.append("路径非法/越出仓库根:%s" % key)
        return False
    if not os.path.exists(p):
        notes.append("文件不存在:%s" % key)
        return False
    with open(p, "rb") as f:
        data = f.read()
    got = (hashlib.sha256(data).hexdigest(), len(data))
    if got != pv:
        notes.append("复算不符:%s 记=%s 实=%s/%d" % (key, pv[0][:12] + "…", got[0][:12] + "…", got[1]))
        return False
    return True


def run_checks(path):
    results = []

    def chk(name, ok, note=""):
        results.append((name, bool(ok), note))

    raw = open(path, "rb").read()
    digest = hashlib.sha256(raw).hexdigest()
    size = len(raw)

    tpl, tpl_err = load_template()
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

        # ============ 增强校验 N 系列（G1–G15；方向只收紧） ============
        rv = obj.get("reviewer") if isinstance(obj.get("reviewer"), dict) else None
        c_role = rv.get("role") if rv is not None else None
        c_sid = rv.get("sessionId") if rv is not None else None
        r_role = rec.get("reviewerRole") if rec is not None else None
        r_sid = rec.get("reviewerSessionId") if rec is not None else None

        # N01/N02/N03 — G1 内部角色黑名单（记录层+容器层）与两层一致
        if rec is None:
            chk("N01 [G1] 记录层reviewerRole非内部角色", False, "记录缺失，未检")
            chk("N03 [G1] 记录层与容器层reviewer.role一致", False, "记录缺失，未检")
        else:
            hits = role_stem_hits(r_role) if isinstance(r_role, str) else []
            chk("N01 [G1] 记录层reviewerRole非内部角色", isinstance(r_role, str) and not hits,
                "命中内部角色词干=%s" % hits if hits else repr(r_role))
            same = isinstance(r_role, str) and isinstance(c_role, str) and r_role == c_role
            chk("N03 [G1] 记录层与容器层reviewer.role一致", same,
                "" if same else "记录层=%r 容器层=%r" % (r_role, c_role))
        hits_c = role_stem_hits(c_role) if isinstance(c_role, str) else []
        chk("N02 [G1] 容器reviewer.role非内部角色", isinstance(c_role, str) and not hits_c,
            "命中内部角色词干=%s" % hits_c if hits_c else repr(c_role))

        # N04 — G2 decision 值域；N05 — G3 grade 值域（禁 APPROVE/放行/签署 字样）
        if rec is None:
            chk("N04 [G2] decision值域{REGISTERED,PARTIAL}且禁签署语汇", False, "记录缺失，未检")
        else:
            dv = rec.get("decision")
            d_ok = isinstance(dv, str) and dv in DECISION_DOMAIN and not sign_word_hits(dv)
            chk("N04 [G2] decision值域{REGISTERED,PARTIAL}且禁签署语汇", d_ok, repr(dv))
        gv = obj.get("grade")
        g_ok = isinstance(gv, str) and gv in GRADE_DOMAIN and not sign_word_hits(gv)
        chk("N05 [G3] grade值域{REGISTERED,PARTIAL}且禁签署语汇", g_ok,
            "grade缺失" if gv is None and "grade" not in obj else repr(gv))

        # N06 — G4 六固定字段与模板逐字一致
        if tpl is None:
            chk("N06 [G4] 六固定字段与模板逐字一致", False, "模板不可读:%s" % tpl_err)
        else:
            diffs = []
            for f6 in FIXED6:
                if f6 not in obj:
                    diffs.append("%s:缺失" % f6)
                elif obj[f6] != tpl.get(f6):
                    diffs.append("%s:与模板不符" % f6)
            chk("N06 [G4] 六固定字段与模板逐字一致", not diffs, "; ".join(diffs[:4]))

        # N07/N08/N09 — G5/G14 sessionId 运行态形制（记录层+容器层）与两层一致
        if rec is None:
            chk("N07 [G5] 记录层sessionId运行态形制", False, "记录缺失，未检")
            chk("N09 [G14] 容器sessionId与记录层一致", False, "记录缺失，未检")
        else:
            ok7, note7 = session_shape(r_sid)
            chk("N07 [G5] 记录层sessionId运行态形制", ok7, note7 if not ok7 else note7 + " 值=%r" % (r_sid[:24] + "…" if isinstance(r_sid, str) and len(r_sid) > 24 else r_sid))
            same_s = isinstance(r_sid, str) and isinstance(c_sid, str) and r_sid == c_sid
            chk("N09 [G14] 容器sessionId与记录层一致", same_s,
                "" if same_s else "记录层=%r 容器层=%r" % (
                    r_sid[:40] if isinstance(r_sid, str) else r_sid,
                    c_sid[:40] if isinstance(c_sid, str) else c_sid))
        ok8, note8 = session_shape(c_sid)
        chk("N08 [G5/G14] 容器sessionId运行态形制", ok8, note8 if not ok8 else "")

        # N10 — G6 冒用面归一化比对（记录层+容器层；对照集不可用即 FAIL）
        _, known_norm, loaded = load_known_ids_ext()
        if loaded == 0:
            chk("N10 [G6] sessionId冒用面归一化比对（记录层+容器层）", False, "对照集不可用（0件装载），无法排除冒用")
        else:
            hitn = []
            if isinstance(r_sid, str) and normalize_id(r_sid) in known_norm:
                hitn.append("记录层")
            if isinstance(c_sid, str) and normalize_id(c_sid) in known_norm:
                hitn.append("容器层")
            chk("N10 [G6] sessionId冒用面归一化比对（记录层+容器层）", not hitn,
                ("归一化命中已登ID:%s" % "+".join(hitn)) if hitn else "对照源=%d件 归一化基数=%d 未命中" % (loaded, len(known_norm)))

        # N11/N12 — G7 计划号子串触发 + G8 登记语必验
        if rec is None:
            chk("N11 [G7] 计划号子串触发（含N-数字即须登记）", False, "记录缺失，未检")
            chk("N12 [G8] 触发时unresolved必含登记语「正式任务书编号未落实」", False, "记录缺失，未检")
        else:
            stid = rec.get("sourceTaskId")
            unr = rec.get("unresolved")
            trig = isinstance(stid, str) and re.search(r"N-\d+", nfkc(stid)) is not None
            if not trig:
                chk("N11 [G7] 计划号子串触发（含N-数字即须登记）", True, "子串未命中(NFKC归一后)")
                chk("N12 [G8] 触发时unresolved必含登记语「正式任务书编号未落实」", True, "未触发，免验")
            else:
                chk("N11 [G7] 计划号子串触发（含N-数字即须登记）", isinstance(unr, list) and len(unr) > 0,
                    "命中计划号子串但unresolved为空" if not (isinstance(unr, list) and len(unr) > 0) else "命中，unresolved非空")
                phrase_ok = isinstance(unr, list) and any(
                    isinstance(x, str) and REGISTRATION_PHRASE in nfkc(x) for x in unr)
                chk("N12 [G8] 触发时unresolved必含登记语「正式任务书编号未落实」", phrase_ok,
                    "unresolved内无登记语" if not phrase_ok else "登记语在")

        # N13 — G9 容器键集合精确相等（缺+多都拦）
        extra = [k for k in obj if k not in CONTAINER13]
        chk("N13 [G9] 容器键集合与13键精确相等（缺+多都拦）", not missing and not extra,
            ("缺=%s " % missing if missing else "") + ("多=%s" % extra if extra else ""))

        # N14 — G10 全件占位符残留扩展面（全角＜＞与裸角字符）
        resid2 = [s[:60] for s in iter_strings(obj) if BRACKET_PAT.search(s)]
        chk("N14 [G10] 全件无占位符残留（扩展面：全角＜＞与裸角字符）", not resid2, "命中=%s" % resid2[:3])

        # N15/N16 — G11 inputHashes / artifactHashes 全键实算
        if rec is None:
            chk("N15 [G11] inputHashes全键实算（含额外键；路径限仓库内）", False, "记录缺失，未检")
            chk("N16 [G11] artifactHashes全键实算（空dict合法）", False, "记录缺失，未检")
        else:
            ih = rec.get("inputHashes")
            n_ok, n_notes = isinstance(ih, dict), []
            if not isinstance(ih, dict):
                n_notes.append("inputHashes须为dict")
            else:
                for k in ih:
                    verify_binding(ih, k, n_notes)
            chk("N15 [G11] inputHashes全键实算（含额外键；路径限仓库内）", n_ok and not n_notes, "; ".join(n_notes))
            ah = rec.get("artifactHashes")
            a_ok, a_notes = isinstance(ah, dict), []
            if not isinstance(ah, dict):
                a_notes.append("artifactHashes须为dict（模板口径为{}）")
            else:
                for k in ah:
                    verify_binding(ah, k, a_notes)
            chk("N16 [G11] artifactHashes全键实算（空dict合法）", a_ok and not a_notes,
                "; ".join(a_notes) if a_notes else "键数=%d" % len(ah))

        # N17 — G15 itemId 固定值
        if rec is None:
            chk("N17 [G15] itemId固定值与模板一致", False, "记录缺失，未检")
        elif tpl is None:
            chk("N17 [G15] itemId固定值与模板一致", False, "模板不可读:%s" % tpl_err)
        else:
            try:
                expect = tpl["records"][0]["itemId"]
            except Exception:
                expect = None
            iv = rec.get("itemId")
            chk("N17 [G15] itemId固定值与模板一致", expect is not None and iv == expect,
                "本件=%r 模板=%r" % (iv, expect))

        # N18 — G12 timestamp 合理域（须含时间成分 + 年份区间）
        if rec is None:
            chk("N18 [G12] timestamp合理域（含时间成分，年份2020-2040）", False, "记录缺失，未检")
        else:
            ts = rec.get("timestamp")
            t_ok, t_note = False, repr(ts)
            if isinstance(ts, str):
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if not TS_TIME_PAT.search(ts):
                        t_note = "缺时间成分(仅日期)"
                    elif not (TS_YEAR_MIN <= dt.year <= TS_YEAR_MAX):
                        t_note = "年份超出合理域[%d,%d]:%d" % (TS_YEAR_MIN, TS_YEAR_MAX, dt.year)
                    else:
                        t_ok = True
                        t_note = "合理域内"
                except ValueError:
                    t_note = "不可解析(H12已拦)"
            else:
                t_note = "非字符串(H12已拦)"
            chk("N18 [G12] timestamp合理域（含时间成分，年份2020-2040）", t_ok, t_note)

        # N19 — G12 unresolved 形制（字符串列表）
        if rec is None:
            chk("N19 [G12] unresolved为字符串列表", False, "记录缺失，未检")
        else:
            u = rec.get("unresolved")
            u_ok = isinstance(u, list) and all(isinstance(x, str) for x in u)
            chk("N19 [G12] unresolved为字符串列表", u_ok, repr(u)[:80])

        # N20 — G14 容器 reviewer 形制（role/sessionId 非空字符串）+ writeDomain 不落只读域
        r_ok = (rv is not None and isinstance(c_role, str) and c_role.strip().lower() not in BAD_VALUES
                and isinstance(c_sid, str) and c_sid.strip().lower() not in BAD_VALUES)
        chk("N20 [G14] 容器reviewer形制（role/sessionId非空字符串）", r_ok,
            "reviewer缺失或role/sessionId非字符串/拒填值" if not r_ok else "")
        wd = obj.get("writeDomain")
        wd_hits = []
        if isinstance(wd, str):
            wdn = nfkc(wd).strip().strip("/").replace("\\", "/").lower()
            wd_hits = [d0 for d0 in READONLY_DOMAIN_PREFIXES if wdn.startswith(d0.lower())]
        chk("N21 [G9补] writeDomain不得指向既有只读域", isinstance(wd, str) and wd.strip() != "" and not wd_hits,
            "指向只读域=%s" % wd_hits if wd_hits else repr(wd))
    else:
        for name in ("H02", "H03", "H04", "H05", "H06", "H07", "H08", "H09", "H10", "H11", "H12", "H13"):
            chk(name, False, "顶层非dict")
        for n in ("N01 [G1] 记录层reviewerRole非内部角色",
                  "N02 [G1] 容器reviewer.role非内部角色",
                  "N03 [G1] 记录层与容器层reviewer.role一致",
                  "N04 [G2] decision值域{REGISTERED,PARTIAL}且禁签署语汇",
                  "N05 [G3] grade值域{REGISTERED,PARTIAL}且禁签署语汇",
                  "N06 [G4] 六固定字段与模板逐字一致",
                  "N07 [G5] 记录层sessionId运行态形制",
                  "N08 [G5/G14] 容器sessionId运行态形制",
                  "N09 [G14] 容器sessionId与记录层一致",
                  "N10 [G6] sessionId冒用面归一化比对（记录层+容器层）",
                  "N11 [G7] 计划号子串触发（含N-数字即须登记）",
                  "N12 [G8] 触发时unresolved必含登记语「正式任务书编号未落实」",
                  "N13 [G9] 容器键集合与13键精确相等（缺+多都拦）",
                  "N14 [G10] 全件无占位符残留（扩展面：全角＜＞与裸角字符）",
                  "N15 [G11] inputHashes全键实算（含额外键；路径限仓库内）",
                  "N16 [G11] artifactHashes全键实算（空dict合法）",
                  "N17 [G15] itemId固定值与模板一致",
                  "N18 [G12] timestamp合理域（含时间成分，年份2020-2040）",
                  "N19 [G12] unresolved为字符串列表",
                  "N20 [G14] 容器reviewer形制（role/sessionId非空字符串）",
                  "N21 [G9补] writeDomain不得指向既有只读域"):
            chk(n, False, "顶层非dict，未检")

    print("== C07 身份补登件门禁（增强版 F3：原15项 + N01-N21 增强项）==")
    for name, ok, note in results:
        print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name, ("  — " + note) if note else ""))
    failed = sum(1 for _, ok, _ in results if not ok)
    print("GATE %s checks=%d failed=%d" % ("PASS" if failed == 0 else "FAIL", len(results), failed))
    print(BINDING_FMT % (digest, size))
    print("注：ID 真值真伪由来源会话自证；N07/N08 形制校验只保证形制不保证真值（T29 边界）。")
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
    # ---- 增强逻辑自测（G1-G15 判定函数；不含任何真实 sessionId 值） ----
    # G1：词干命中防变体；合法角色面不得被误伤
    assert role_stem_hits("卡顿分流员·GLM（代签）") == ["卡顿分流员"]
    assert role_stem_hits("独立复核员") == ["独立复核员"]
    assert role_stem_hits("分流报告撰写员") == ["分流报告撰写员"]
    assert role_stem_hits("C07 身份补登签发员·GLM") == []  # 宽子串（如「GLM」「撰写员」）不得入黑名单
    assert role_stem_hits(123) == []
    # G2/G3：值域与签署语汇
    assert "APPROVE_SCOPE" not in DECISION_DOMAIN and sign_word_hits("APPROVE_SCOPE") == ["approve"]
    assert sign_word_hits("REGISTERED") == [] and sign_word_hits("PARTIAL") == []
    assert "REGISTERED" in GRADE_DOMAIN and "PARTIAL" in GRADE_DOMAIN
    # G5：形制（合成形制串，非真实 ID）；nil UUID 拒绝
    synthetic = "sess_dwf-dwfrun-0123abcd-1234-5678-9abc-def012345678-actor_1_2"
    assert session_shape(synthetic)[0] is True
    assert session_shape("-")[0] is False
    assert session_shape("12345")[0] is False
    assert session_shape("sess_dwf-dwfrun-00000000-0000-0000-0000-000000000000-actor_9_9")[0] is False
    # G6：归一化比对（尾随空格/全角/大小写/零宽变体必须命中同值）
    base = "sess_dwf-dwfrun-0123abcd-1234-5678-9abc-def012345678-actor_1_2"
    assert normalize_id("SeSS_dwf-DWFRUN-0123ABCD-1234-5678-9ABC-DEF012345678-actor_1_2 ") == base
    assert normalize_id("sess_dwf-dwfrun-0123abcd-1234-5678-9abc-def012345678-actor_1_2\u200b") == base
    assert normalize_id("sess＿dwf…x") != base
    # G7：计划号子串触发（装饰变体必须命中；普通任务号不触发）
    assert re.search(r"N-\d+", nfkc("N-11（计划号）")) is not None
    assert re.search(r"N-\d+", nfkc("TASK-20261108-C07-01")) is None
    # G8：登记语
    assert REGISTRATION_PHRASE in nfkc("正式任务书编号未落实，暂以计划号 N-11 代替")
    # G10：占位符扩展面（全角/裸角）
    assert BRACKET_PAT.search("＜来源会话sessionId＞") is not None
    assert BRACKET_PAT.search("a>b") is not None
    assert not BRACKET_PAT.search("正式任务书编号未落实")
    # G11：路径解析（拒绝绝对路径与 .. 越界）
    assert resolve_repo_path("lead/d13d14_cards_20261108/DECISION_QUESTIONS.md") is not None
    assert resolve_repo_path("../../etc/passwd") is None
    assert resolve_repo_path("C:/Windows/system32/config") is None
    # G13：本器绑定行无反引号
    assert "`" not in BINDING_FMT and BINDING_FMT.startswith("被核对象 SHA256 = ")
    tpl, err = load_template()
    assert tpl is not None and isinstance(tpl.get("decisionSemantics"), str), err
    print("SELFTEST PASS（解析/占位/计划号/黑名单/形制/归一化/路径判定逻辑正常；对照已登ID基数=%d）" % len(known))
    return 0


def main(argv):
    if len(argv) >= 2 and argv[1] == "--selftest":
        return selftest()
    if len(argv) < 2:
        print("用法：python -I -X utf8 _f3_c7check.py <已填JSON路径> | --selftest")
        return 2
    target = os.path.abspath(argv[1])
    if not os.path.exists(target):
        print("目标不存在：%s" % target)
        return 2
    return run_checks(target)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
