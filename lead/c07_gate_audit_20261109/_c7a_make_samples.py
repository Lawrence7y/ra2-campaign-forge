# -*- coding: utf-8 -*-
# _c7a_make_samples.py — 构造攻样本（只写本任务写域 _c7a_samples/；不动任何既有件）。
# 写法说明：为满足本机写路径门禁，本脚本所有 open(...,"wb") 的路径参数均为单个
# 字符串字面量（无 join、无拼接、无变量）；读路径一律经 resolve() 校验。
import copy
import hashlib
import json
import os

ROOT_ABS = os.path.abspath(r"D:\Project\ra2-campaign-forge")
TPL_REL = "lead/c07_slot_20261109/_c7_record_template.json"
REQUIRED = [
    "lead/d13d14_cards_20261108/DECISION_QUESTIONS.md",
    "lead/pending_factpack_20261108/_fp_N10-C07_Q6.md",
    "lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md",
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
]


def resolve(rel):
    # 读路径规范化 + containment：禁止上级目录片段，realpath + commonpath 双校验。
    parts = [p for p in rel.replace("/", os.sep).split(os.sep) if p not in ("", ".")]
    if any(p == os.pardir for p in parts):
        raise SystemExit("读路径越界（含上级目录片段）")
    p = os.path.realpath(os.path.join(ROOT_ABS, *parts))
    if os.path.commonpath([p, ROOT_ABS]) != ROOT_ABS:
        raise SystemExit("读路径越界（逃出仓库根）")
    return p


with open(resolve(TPL_REL), "rb") as f:
    TPL_OBJ = json.loads(f.read().decode("utf-8"))


def sha_pair(rel):
    with open(resolve(rel), "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest(), len(data)


REAL_IH = {rel: "%s/%d" % sha_pair(rel) for rel in REQUIRED}

KNOWN_IDS = []
for rel in ("lead/a_residual_20261106/ACCEPTANCE_RECORDS.json",
            "lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json"):
    with open(resolve(rel), "rb") as f:
        obj = json.loads(f.read().decode("utf-8"))
    recs = obj if isinstance(obj, list) else obj.get("records", [])
    for r in recs:
        if isinstance(r, dict) and isinstance(r.get("reviewerSessionId"), str):
            KNOWN_IDS.append(r["reviewerSessionId"])
KNOWN_N1_R2 = KNOWN_IDS[1] if len(KNOWN_IDS) > 1 else KNOWN_IDS[0]

SID = "sess_dwf-dwfrun-9f1c2d3e-4a5b-4c6d-8e7f-0a1b2c3d4e5f-actor_1_1"   # 样本测试造值
ROLE = "C07 身份补登签发员·GLM"                                            # 样本测试造值


def base_obj():
    rec = {
        "itemId": "N10-C07-Q6-identity",
        "reviewerRole": ROLE,
        "reviewerSessionId": SID,
        "sourceTaskId": "TASK-20261108-C07-01",
        "inputHashes": dict(REAL_IH),
        "artifactHashes": {},
        "decision": "REGISTERED",
        "unresolved": [],
        "timestamp": "2026-11-09T12:00:00+08:00",
    }
    return {
        "schema": TPL_OBJ["schema"],
        "schemaNote": TPL_OBJ["schemaNote"],
        "natureNote": TPL_OBJ["natureNote"],
        "grade": "REGISTERED",
        "revisionOf": None,
        "independentReview": "未做",
        "replacementNote": TPL_OBJ["replacementNote"],
        "reviewer": {"role": ROLE, "sessionId": SID, "note": "无"},
        "sourceTask": TPL_OBJ["sourceTask"],
        "writeDomain": "lead/c07_slot_20261109",
        "hashMethod": TPL_OBJ["hashMethod"],
        "decisionSemantics": TPL_OBJ["decisionSemantics"],
        "records": [rec],
    }


def with_rec(o, **kw):
    o2 = copy.deepcopy(o)
    o2["records"][0].update(kw)
    return o2


B = base_obj()
S = {}

# ---- T1：三身份字段全空 ----
S["T01_empty_trio"] = with_rec(B, reviewerRole="", reviewerSessionId="", sourceTaskId="")
# ---- T2：sessionId 拒填值 ----
S["T02a_sid_unknown"] = with_rec(B, reviewerSessionId="unknown")
S["T02b_sid_todo"] = with_rec(B, reviewerSessionId="TODO")
S["T02c_sid_na"] = with_rec(B, reviewerSessionId="N/A")
# ---- T3：照抄 a_residual_n1 r2 已登 ID（明确失败条件）----
S["T03_sid_copied_n1r2"] = with_rec(B, reviewerSessionId=KNOWN_N1_R2)
# ---- T4：计划号且未登记缺口（明确失败条件）----
S["T04_n11_no_registration"] = with_rec(B, sourceTaskId="N-11", unresolved=[])
# ---- T5：计划号但已按规登记（应 PASS）----
S["T05_n11_registered_gap"] = with_rec(
    B, sourceTaskId="N-11",
    unresolved=["正式任务书编号未落实，暂以计划号 N-11 代替（YI_SUPERSEDE 先例口径）"])
# ---- T6：照抄 PERF:151 内部角色 = 冒签（明确失败条件）----
S["T06a_role_kadun"] = with_rec(B, reviewerRole="卡顿分流员·GLM")
S["T06b_role_fenliu"] = with_rec(B, reviewerRole="分流报告撰写员")
S["T06c_role_fuhe"] = with_rec(B, reviewerRole="独立复核员")
# ---- T7：占位符残留 ----
S["T07_sid_placeholder"] = with_rec(B, reviewerSessionId="<来源会话sessionId>")
# ---- T8：records 条数 != 1 ----
o8a = copy.deepcopy(B); o8a["records"] = []
S["T08a_records_zero"] = o8a
o8b = copy.deepcopy(B)
r2dup = copy.deepcopy(o8b["records"][0]); r2dup["itemId"] = "N10-C07-Q6-identity-2"
o8b["records"] = [o8b["records"][0], r2dup]
S["T08b_records_two"] = o8b
# ---- T9：容器缺键 / 多键 ----
o9a = copy.deepcopy(B); del o9a["grade"]
S["T09a_container_missing_grade"] = o9a
o9b = copy.deepcopy(B)
o9b["extraApprovalClaim"] = "本件同时构成 APPROVE_SCOPE 签署（附加声明）"
S["T09b_container_extra_key"] = o9b
# ---- T10：字段顺序错乱 ----
o10 = copy.deepcopy(B)
r10 = o10["records"][0]
order10 = ["itemId", "timestamp", "reviewerRole", "reviewerSessionId", "sourceTaskId",
           "decision", "unresolved", "inputHashes", "artifactHashes"]
o10["records"] = [{k: r10[k] for k in order10}]
S["T10_field_order"] = o10
# ---- T11：timestamp 非 ISO8601 ----
S["T11a_ts_bad"] = with_rec(B, timestamp="2026-11-09 40:70:00")
S["T11b_ts_int"] = with_rec(B, timestamp=20261109)
S["T11c_ts_text"] = with_rec(B, timestamp="不是时间")
# ---- T12：指纹伪造 ----
o12a = with_rec(B)
v12a = o12a["records"][0]["inputHashes"][REQUIRED[0]]
o12a["records"][0]["inputHashes"][REQUIRED[0]] = ("f" if v12a[0] != "f" else "0") + v12a[1:]
S["T12a_hash_wrong_hex"] = o12a
o12b = with_rec(B)
hex12b, n12b = REAL_IH[REQUIRED[0]].split("/")
o12b["records"][0]["inputHashes"][REQUIRED[0]] = "%s/%d" % (hex12b, int(n12b) + 1)
S["T12b_hash_wrong_bytes"] = o12b
o12c = with_rec(B)
del o12c["records"][0]["inputHashes"][REQUIRED[2]]
S["T12c_hash_missing_binding"] = o12c
# ---- T13：完全合法正样本（应 PASS）----
S["T13_positive"] = B
# ---- T14：decision 冒签（核心冒签面）----
S["T14_decision_approve_scope"] = with_rec(B, decision="APPROVE_SCOPE")
# ---- T16：固定说明字段被篡改（decisionSemantics 语义掉包）----
o16 = copy.deepcopy(B)
o16["decisionSemantics"] = TPL_OBJ["decisionSemantics"].replace(
    "decision=REGISTERED 指", "decision=APPROVE_SCOPE 指", 1)
S["T16_decisionsemantics_tampered"] = o16
# ---- T17：artifactHashes 伪造指纹（对现有文件填假指纹）----
S["T17_artifacthash_fake"] = with_rec(
    B, artifactHashes={"lead/d13d14_cards_20261108/DECISION_QUESTIONS.md": "ff" * 32 + "/123"})
# ---- T18：sessionId 非运行态垃圾值 ----
S["T18a_sid_dash"] = with_rec(B, reviewerSessionId="-")
S["T18b_sid_digits"] = with_rec(B, reviewerSessionId="12345")
# ---- T19：近似照抄已登 ID（尾随空格）----
S["T19_sid_nearcopy"] = with_rec(B, reviewerSessionId=KNOWN_N1_R2 + " ")
# ---- T20：计划号带装饰绕过 ----
S["T20_n11_decorated"] = with_rec(B, sourceTaskId="N-11（计划号）", unresolved=[])
# ---- T22：全角占位符 ----
S["T22_fullwidth_placeholder"] = with_rec(B, reviewerSessionId="＜来源会话sessionId＞")
# ---- T23：计划号已登记但登记语缺失/无关 ----
S["T23_unresolved_wrong_phrase"] = with_rec(
    B, sourceTaskId="N-11",
    unresolved=["本条说明与正式任务书编号无关，仅示意占位文字"])
# ---- T24：inputHashes 夹带额外伪造绑定 ----
o24 = with_rec(B)
o24["records"][0]["inputHashes"]["lead/c07_gate_audit_20261109/_c7a_nonexistent_binding.md"] = "ee" * 32 + "/7"
S["T24_inputhash_extra_fake"] = o24
# ---- T26：容器 reviewer.role 冒签（记录层角色合法）----
o26 = copy.deepcopy(B); o26["reviewer"]["role"] = "独立复核员"
S["T26_container_role_fuhe"] = o26
# ---- T27：grade 冒签 ----
o27 = copy.deepcopy(B); o27["grade"] = "APPROVE_SCOPE"
S["T27_grade_approve_scope"] = o27
# ---- T29：形制合规但编造的 sessionId（边界样本：真值无法离线证）----
S["T29_sid_fabricated_shape"] = with_rec(
    B, reviewerSessionId="sess_dwf-dwfrun-00000000-0000-0000-0000-000000000000-actor_9_9")

# ---- 逐样本字面量路径写出（无任何动态写路径）----
_W = r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples"
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T01_empty_trio.json", "wb") as f:
    f.write((json.dumps(S["T01_empty_trio"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T02a_sid_unknown.json", "wb") as f:
    f.write((json.dumps(S["T02a_sid_unknown"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T02b_sid_todo.json", "wb") as f:
    f.write((json.dumps(S["T02b_sid_todo"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T02c_sid_na.json", "wb") as f:
    f.write((json.dumps(S["T02c_sid_na"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T03_sid_copied_n1r2.json", "wb") as f:
    f.write((json.dumps(S["T03_sid_copied_n1r2"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T04_n11_no_registration.json", "wb") as f:
    f.write((json.dumps(S["T04_n11_no_registration"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T05_n11_registered_gap.json", "wb") as f:
    f.write((json.dumps(S["T05_n11_registered_gap"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T06a_role_kadun.json", "wb") as f:
    f.write((json.dumps(S["T06a_role_kadun"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T06b_role_fenliu.json", "wb") as f:
    f.write((json.dumps(S["T06b_role_fenliu"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T06c_role_fuhe.json", "wb") as f:
    f.write((json.dumps(S["T06c_role_fuhe"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T07_sid_placeholder.json", "wb") as f:
    f.write((json.dumps(S["T07_sid_placeholder"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T08a_records_zero.json", "wb") as f:
    f.write((json.dumps(S["T08a_records_zero"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T08b_records_two.json", "wb") as f:
    f.write((json.dumps(S["T08b_records_two"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T09a_container_missing_grade.json", "wb") as f:
    f.write((json.dumps(S["T09a_container_missing_grade"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T09b_container_extra_key.json", "wb") as f:
    f.write((json.dumps(S["T09b_container_extra_key"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T10_field_order.json", "wb") as f:
    f.write((json.dumps(S["T10_field_order"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T11a_ts_bad.json", "wb") as f:
    f.write((json.dumps(S["T11a_ts_bad"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T11b_ts_int.json", "wb") as f:
    f.write((json.dumps(S["T11b_ts_int"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T11c_ts_text.json", "wb") as f:
    f.write((json.dumps(S["T11c_ts_text"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T12a_hash_wrong_hex.json", "wb") as f:
    f.write((json.dumps(S["T12a_hash_wrong_hex"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T12b_hash_wrong_bytes.json", "wb") as f:
    f.write((json.dumps(S["T12b_hash_wrong_bytes"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T12c_hash_missing_binding.json", "wb") as f:
    f.write((json.dumps(S["T12c_hash_missing_binding"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T13_positive.json", "wb") as f:
    f.write((json.dumps(S["T13_positive"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T14_decision_approve_scope.json", "wb") as f:
    f.write((json.dumps(S["T14_decision_approve_scope"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T16_decisionsemantics_tampered.json", "wb") as f:
    f.write((json.dumps(S["T16_decisionsemantics_tampered"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T17_artifacthash_fake.json", "wb") as f:
    f.write((json.dumps(S["T17_artifacthash_fake"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T18a_sid_dash.json", "wb") as f:
    f.write((json.dumps(S["T18a_sid_dash"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T18b_sid_digits.json", "wb") as f:
    f.write((json.dumps(S["T18b_sid_digits"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T19_sid_nearcopy.json", "wb") as f:
    f.write((json.dumps(S["T19_sid_nearcopy"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T20_n11_decorated.json", "wb") as f:
    f.write((json.dumps(S["T20_n11_decorated"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T22_fullwidth_placeholder.json", "wb") as f:
    f.write((json.dumps(S["T22_fullwidth_placeholder"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T23_unresolved_wrong_phrase.json", "wb") as f:
    f.write((json.dumps(S["T23_unresolved_wrong_phrase"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T24_inputhash_extra_fake.json", "wb") as f:
    f.write((json.dumps(S["T24_inputhash_extra_fake"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T26_container_role_fuhe.json", "wb") as f:
    f.write((json.dumps(S["T26_container_role_fuhe"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T27_grade_approve_scope.json", "wb") as f:
    f.write((json.dumps(S["T27_grade_approve_scope"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
with open(r"D:\Project\ra2-campaign-forge\lead\c07_gate_audit_20261109\_c7a_samples\T29_sid_fabricated_shape.json", "wb") as f:
    f.write((json.dumps(S["T29_sid_fabricated_shape"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

print("KNOWN_N1_R2=%r  known_ids_total=%d" % (KNOWN_N1_R2, len(KNOWN_IDS)))
print("written=%d" % len(S))
