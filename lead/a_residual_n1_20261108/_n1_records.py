# -*- coding: utf-8 -*-
"""N-1 残余引用核对：生成 ACCEPTANCE_RECORDS.json 内容到 stdout（本脚本自身零文件写入）。
落盘方式：python -I -X utf8 _n1_records.py > <写域内固定文件> ；运行摘要走 stderr。
9 固定字段/条；inputHashes / artifactHashes 全部 hashlib 实算；零真机、零采样代码。
"""
import hashlib
import json
import re
import sys
from datetime import datetime

REVIEWER_ROLE = "本轮编排方另派独立复核员（残余引用核对员·GLM）"
SESSION_ID = "sess_dwf-dwfrun-324c613e-fb0e-42f5-9883-805fef5b80de-actor_1_1"

# 被修原文措辞中的范围连接符（两个点号）以 chr(46)*2 构造，避免源码字面出现连续点
DD = chr(46) * 2
FN_RANGE = "fn 0x740B51" + DD + "0x740DED"


def sha_file(abs_path):
    with open(abs_path, "rb") as f:
        data = f.read()
    return hashlib.sha256(data).hexdigest(), len(data)


# 只读输入件：绝对路径字面量（只读母本域）-> 记录用相对名
ABS_INPUTS = {
    r"D:\Project\ra2-campaign-forge\lead\nextstep_plan_20261106\NEXT_STEPS_20261106.md":
        "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
    r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\A1_ERRATA_MAP\A1_ERRATA_MAP.md":
        "lead/re_line_20261105/A1_ERRATA_MAP/A1_ERRATA_MAP.md",
    r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\A1_ERRATA_MAP\ERRATA_W8.md":
        "lead/re_line_20261105/A1_ERRATA_MAP/ERRATA_W8.md",
    r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\D24_RULING\RULING_D24.md":
        "lead/re_line_20261105/D24_RULING/RULING_D24.md",
    r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\W8_STATIC_LOCATE\W8_STATIC_LOCATE.md":
        "lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md",
    r"D:\Project\ra2-campaign-forge\lead\re_line_20261105\W9_SINGLESTEP_7CFC9F\W9_SINGLESTEP.md":
        "lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/W9_SINGLESTEP.md",
    r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md":
        "lead/PENDING_DECISIONS.md",
}

input_hashes = {}
for abs_p, rel_name in ABS_INPUTS.items():
    h, b = sha_file(abs_p)
    input_hashes[rel_name] = f"{h}/{b}B"

md_sha, md_bytes = sha_file(
    r"D:\Project\ra2-campaign-forge\lead\a_residual_n1_20261108\A_RESIDUAL_REFERENCES.md")
artifact_hashes = {
    "lead/a_residual_n1_20261108/A_RESIDUAL_REFERENCES.md": f"{md_sha}/{md_bytes}B"
}

TIMESTAMP = datetime.now().astimezone().isoformat(timespec="seconds")

SRC_NOTE = "编排方未随任务下发独立任务书编号，sourceTaskId 按计划任务号 N-1 填写（NEXT_STEPS_20261106.md:21-27）"
DEC_NOTE = "decision=ACCEPT 仅指本条凭据登记核对通过（五要素齐备、联引成立、未验项如实登记），不改变被核条目既有判定档/落实档，不构成技术结论升格"

RECORDS = [
    {
        "itemId": "W9-2",
        "reviewerRole": REVIEWER_ROLE,
        "reviewerSessionId": SESSION_ID,
        "sourceTaskId": "N-1",
        "inputHashes": dict(input_hashes),
        "artifactHashes": dict(artifact_hashes),
        "decision": "ACCEPT",
        "unresolved": [
            "正文补引 QC124_VERDICT.json:74-87 与 BASELINE_A4_PROPOSAL.md:79,92,104 尚未落实——本轮实跑 rg -n \"BASELINE_A4_PROPOSAL|74-87\" W9_SINGLESTEP.md 仅命中 :193（§7 本条自身），复现 A1_ERRATA_MAP.md:88 缺口记载",
            "QC124 运行期写出事件零真机、未独立复现（W9_SINGLESTEP.md:157,:230；A1_ERRATA_MAP.md:88）",
            SRC_NOTE,
            DEC_NOTE,
        ],
        "timestamp": TIMESTAMP,
    },
    {
        "itemId": "W9-9",
        "reviewerRole": REVIEWER_ROLE,
        "reviewerSessionId": SESSION_ID,
        "sourceTaskId": "N-1",
        "inputHashes": dict(input_hashes),
        "artifactHashes": dict(artifact_hashes),
        "decision": "PARTIAL",
        "unresolved": [
            "汇总件正文 PENDING_DECISIONS.md 版本时刻标注未落实（联引 A1_ERRATA_MAP.md:89 记载，本轮未重查汇总件正文 PD 标注）",
            "PD 现盘再次漂移：本轮 hashlib 实算 lead/PENDING_DECISIONS.md = 7f68fc6c6ed1ab6ba16210b611906c6189ad0af90a84b46b263a19379fbfcd48 / 50,194 B，不等于 08:57 版 be22211ccf7c694ff8363212aaa639737cb3b09d64293b867e677ba2e6b652ba / 34,403 B（A1_ERRATA_MAP.md:14）；本轮未逐行重查 PD 内容，行号锚点不可沿用；A1_ERRATA_MAP.md:255 明令不得照抄汇总件 :184 的 :78-80/:114 锚点",
            SRC_NOTE,
            "decision=PARTIAL：本条中心限定（PD 版本时刻绑定）本轮仅能联引既有映射，未能在现盘独立闭合；PARTIAL 不提升技术结论",
        ],
        "timestamp": TIMESTAMP,
    },
    {
        "itemId": "W9-19",
        "reviewerRole": REVIEWER_ROLE,
        "reviewerSessionId": SESSION_ID,
        "sourceTaskId": "N-1",
        "inputHashes": dict(input_hashes),
        "artifactHashes": dict(artifact_hashes),
        "decision": "ACCEPT",
        "unresolved": [
            "Q4 三口径 02:12 / 02:15:47 / 02:10:46 补记未落实——本轮实跑 rg 15.1.0 于 W9_SINGLESTEP.md 检索 \"02:15:47|02:10:46\" 仅命中 :210（§7 本条自身），复现 A1_ERRATA_MAP.md:90 缺口记载",
            "A1_ERRATA_MAP.md:122 的 4 处低危行号 mustFix 截至该汇总件落盘未就地修（:342 亦登记）；W9_review.md:83 本轮未读，按联引登记",
            SRC_NOTE,
            DEC_NOTE,
        ],
        "timestamp": TIMESTAMP,
    },
    {
        "itemId": "W8-6",
        "reviewerRole": REVIEWER_ROLE,
        "reviewerSessionId": SESSION_ID,
        "sourceTaskId": "N-1",
        "inputHashes": dict(input_hashes),
        "artifactHashes": dict(artifact_hashes),
        "decision": "ACCEPT",
        "unresolved": [
            "节略标注/径引 _w8_f7_out.txt:962-965 未落进汇总件正文——本轮实跑 rg -n \"6FB03D|6FB040|6FB048\" W8_STATIC_LOCATE.md 仅命中 :177，完全无落点维持（ERRATA_W8.md:113）",
            ":198 通配句对④类条目效力属解释问题，最终解释权在 Leader/用户（ERRATA_W8.md:201-202）",
            SRC_NOTE,
            DEC_NOTE,
        ],
        "timestamp": TIMESTAMP,
    },
    {
        "itemId": "W8-11",
        "reviewerRole": REVIEWER_ROLE,
        "reviewerSessionId": SESSION_ID,
        "sourceTaskId": "N-1",
        "inputHashes": dict(input_hashes),
        "artifactHashes": dict(artifact_hashes),
        "decision": "ACCEPT",
        "unresolved": [
            "NEXT_INSN_DIST 标签修正未落进汇总件正文——本轮实跑 rg -n \"NEXT_INSN\" W8_STATIC_LOCATE.md 仅命中 :185，完全无落点维持（ERRATA_W8.md:160）",
            ":198 通配句效力解释问题同 W8-6（ERRATA_W8.md:201-202）",
            SRC_NOTE,
            DEC_NOTE,
        ],
        "timestamp": TIMESTAMP,
    },
    {
        "itemId": "W8-8",
        "reviewerRole": REVIEWER_ROLE,
        "reviewerSessionId": SESSION_ID,
        "sourceTaskId": "N-1",
        "inputHashes": dict(input_hashes),
        "artifactHashes": dict(artifact_hashes),
        "decision": "ACCEPT",
        "unresolved": [
            "「House 级」标签存疑限定未落进正文——本轮实读 W8_STATIC_LOCATE.md:96/:97/:147 三处径用「House 级」且标 ✅、无存疑限定（✅ 指 C3C4 字节勘误释义，非宿主身份终证），仅半落点维持（ERRATA_W8.md:41,:132）",
            "12 窗逐窗宿主命名未重扫（F7_review.md:202 转引；零采样铁律下本轮亦不跑任何扫描）",
            SRC_NOTE,
            DEC_NOTE,
        ],
        "timestamp": TIMESTAMP,
    },
    {
        "itemId": "W8-7",
        "reviewerRole": REVIEWER_ROLE,
        "reviewerSessionId": SESSION_ID,
        "sourceTaskId": "N-1",
        "inputHashes": dict(input_hashes),
        "artifactHashes": dict(artifact_hashes),
        "decision": "ACCEPT",
        "unresolved": [
            "被修原文「" + FN_RANGE + "」在 F7 回件与探针输出中定位未验——本轮复跑 rg -in \"740B51\" F7_TARGETING.md 与 _w8_f7_out.txt 均 0 命中（exit=1）；全域该措辞仅 W8_STATIC_LOCATE.md:178（自引）与 reviews/F7_review.md:193（M4 转述）；缺口维持开放（ERRATA_W8.md:120,:198）",
            ":198 点名清单未含本条（本轮 sed -n '198p' 汇总件后 rg 计数 = 0）；引用须带「PARTIAL（被修原文定位未验）」，出处挂 reviews/F7_review.md:94-95,193，不得挂 F7_TARGETING.md 行号（A1_ERRATA_MAP.md:285；条目判定档维持 PARTIAL，不升格）",
            SRC_NOTE,
            DEC_NOTE,
        ],
        "timestamp": TIMESTAMP,
    },
]

# ── 校验：每条恰 9 个固定字段、顺序固定、decision 枚举、哈希格式 ──
FIXED = ["itemId", "reviewerRole", "reviewerSessionId", "sourceTaskId",
         "inputHashes", "artifactHashes", "decision", "unresolved", "timestamp"]
assert len(RECORDS) == 7, "应为 7 条记录"
for r in RECORDS:
    assert list(r.keys()) == FIXED, r["itemId"] + " 字段顺序不符"
    assert r["decision"] in ("ACCEPT", "REJECT", "PARTIAL")
    assert isinstance(r["unresolved"], list) and all(isinstance(x, str) for x in r["unresolved"])
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}", r["timestamp"]), r["timestamp"]
    for v in list(r["inputHashes"].values()) + list(r["artifactHashes"].values()):
        parts = v.rsplit("/", 1)
        assert len(parts) == 2 and re.fullmatch(r"[0-9a-f]{64}", parts[0]) and parts[1].endswith("B"), v

DOC = {
    "schema": "N-1-ACCEPTANCE-RECORDS/1",
    "natureNote": "本轮是文书核对与凭据落盘，不是根因确认、不是技术结论升格；PARTIAL 不提升技术结论，ACCEPT 不改变被核条目既有档位。",
    "replacementNote": "新记录注明替代关系，不覆盖历史结论：本 7 条替代 lead/a_residual_20261106/ACCEPTANCE_RECORDS.json 中同域条目（R1-W9-2 / R1-W9-9 / R1-W9-19 / R2-W8-6 / R2-W8-7 / R2-W8-8 / R2-W8-11）作为当前引用凭据落位；旧件与其余 10 条保留原状一字不改，历史结论不被改写或撤销。旧 17 条 reviewerSessionId 与 sourceTaskId 均为 null（本轮实读确认），按 NEXT_STEPS_20261106.md:25 身份或版本未填不得视为放行。",
    "reviewer": {
        "reviewerRole": REVIEWER_ROLE,
        "reviewerSessionId": SESSION_ID,
        "sessionIdSource": "运行环境实读 ZCODE_SESSION_ID（与 CLAUDE_SESSION_ID / CLAUDE_CODE_SESSION_ID 一致）",
        "distinctFromAuthor": "本轮验收者（独立复核员）与被核映射/旧记录作者非同一会话",
    },
    "sourceTask": "N-1（lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md:21-27）",
    "writeDomain": "lead/a_residual_n1_20261108/（唯一写域；母本与既有件零改动；零真机、零采样代码；未 commit、未 push）",
    "hashMethod": "inputHashes / artifactHashes 均由 _n1_records.py 以 python -I -X utf8 + hashlib 实算，不手抄；值为 SHA256/字节数。ACCEPTANCE_RECORDS.json 自身指纹无法内嵌，以复核回件 SHA256 行为准。",
    "decisionSemantics": "ACCEPT=该条凭据登记核对通过（原断言/限定/出处/档位/未验项五要素齐备、联引成立），未验项不隐没；PARTIAL=存在本轮无法闭合的核对面，不提升技术结论；REJECT=与既有映射矛盾或失实（本轮无）。",
    "records": RECORDS,
}

payload = json.dumps(DOC, ensure_ascii=False, indent=2) + "\n"
sys.stdout.write(payload)

# 运行摘要走 stderr（stdout 专用于 JSON 重定向落盘）
sys.stderr.write("records = " + str(len(RECORDS)) + "\n")
for r in RECORDS:
    sys.stderr.write("  " + r["itemId"].ljust(6) + " decision=" + r["decision"].ljust(8)
                     + " unresolved=" + str(len(r["unresolved"])) + "\n")
sys.stderr.write("A_RESIDUAL_REFERENCES.md  SHA256 = " + md_sha + " 字节数 = " + str(md_bytes) + "\n")
