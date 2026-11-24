# -*- coding: utf-8 -*-
r"""_v12_verify.py -- 独立复核 + 正负样本回归（实跑件，v2）。

跑法：python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_v1v2_20261109\_v12_verify.py
零真机、零采样；只读两域与谓词模块；输出 print 到 stdout（外层 tee 落 _v12_verify_out.txt）。
"""
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_v1v2_20261109"
sys.path.insert(0, str(WD))

DOCS = [
    ("c07_slot_20261109", ROOT / "lead" / "c07_slot_20261109" / "C07_IDENTITY_SLOT.md",
     "05ecdfca451476bb80d84281068fcd9c59d1364b2247cb5482943de6417781fc", 20651,
     ["已补登", "已填入", "已填", "已代填"]),
    ("c07_truth_protocol_20261109", ROOT / "lead" / "c07_truth_protocol_20261109" / "C07_TRUTH_SELF_PROOF.md",
     "5102beae1ecf4952862d4ff1319283df816c53a49bdc81bae38d9709bef974e3", 38232,
     ["已填", "已代填", "已提交"]),
]
PRED = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
PRED_SHA = "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120"
PRED_BYTES = 11743


def fp(p):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def load_pred():
    sha, n = fp(PRED)
    print("[PRED-FP] %s = %s/%d ; MATCH=%s" % (PRED.name, sha, n, sha == PRED_SHA and n == PRED_BYTES))
    spec = importlib.util.spec_from_file_location("_g7_predicates_v12", PRED)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def orig_line(text, pos):
    a = text.rfind("\n", 0, pos) + 1
    b = text.find("\n", pos)
    if b == -1:
        b = len(text)
    return text[a:b]


def scan_doc(doc):
    import _v12_rule as R
    name, path, sha0, n0, bans = doc
    raw = path.read_bytes()
    sha, n = hashlib.sha256(raw).hexdigest(), len(raw)
    text = raw.decode("utf-8")
    print("\n" + "=" * 100)
    print("[DOC] %s / %s" % (name, path.name))
    print("[DOC-FP] sha256 = %s, bytes = %d ; MATCH_BASELINE=%s" % (sha, n, sha == sha0 and n == n0))
    problems, warnings, hits = G7.r10_scan(text, bans)
    r12p, r12h = G7.r12_scan(text, bans)
    print("[R10] problems=%d warnings=%d occurrences=%d ; [R12] problems=%d" %
          (len(problems), len(warnings), len(hits), len(r12p)))
    for p in problems:
        print("  R10-PROBLEM: " + p)
    for w in warnings:
        print("  R10-WARNING: " + w)
    print("[HITS] 逐处回算（行号 + 原句 + R10 kind + V12 判定）")
    out = []
    for h in hits:
        tok, pos = h["token"], h["pos"]
        ctx = G7.r10_context(text, pos, pos + len(tok))
        v = R.classify_v12(text, pos, pos + len(tok), tok)
        rec = {"domain": name, "line": line_of(text, pos), "token": tok,
               "orig": orig_line(text, pos), "r10_kind": h["kind"],
               "r10_neg": h["neg_count"], "r10_in_span": h["in_span"],
               "r10_dbl": ctx["dbl"], "v12": v["verdict"],
               "hard": v["hard"], "weak": v["weak"], "override": v["override"],
               "review_flag": v["review_flag"], "reason": v["reason"],
               "unit": v["unit"]}
        out.append(rec)
        tag = ",".join(v["hard"] + v["weak"]) or v["override"] or "DEFAULT_V2+REVIEW"
        print("  L%-4d tok=%-6s R10=%-13s neg=%d span=%s dbl=%s => V12=%s [%s]" %
              (rec["line"], tok, h["kind"], h["neg_count"], h["in_span"], ctx["dbl"],
               v["verdict"], tag))
        print("       ORIG: " + rec["orig"].replace("\n", "\\n")[:260])
        print("       UNIT: " + rec["unit"].replace("\n", "\\n")[:200])
    return {"doc": name, "sha": sha, "bytes": n, "bans": bans,
            "r10_problems": problems, "r10_warnings": warnings,
            "r12_problems": r12p, "hits": out}


# ================= 正样本集 V1（应当放过） =================
# 真实行文取两域逐字原句/截断句（标行号）；[构造] 为贴近形态，注明来源形态。
# 来源标注：[逐字] = 两域原文照抄；[改写] = 取真实行骨架并补入命中词（如实标注，不冒充逐字）；
#           [构造] = 本任务构造。真实逐字样本 9 条（两域禁用词命中全量 9 处即全部逐字样本），
#           改写 4 条、构造 9 条，合计 22 条。
V1_SAMPLES = [
    ("slot:79", "**填用流程**：① 复制 `_c7_record_template.json` 到落点名 `ACCEPTANCE_RECORDS_C07.json`；② 仅替换 `<…>` 占位符与定档字段（grade/decision/independentReview/writeDomain）；③ `python -I -X utf8 _c7_selfcheck.py <已填件路径>` 须 GATE PASS exit 0；④ 回件含绑定行（§6.2 格式）。", "已填", "V1", "M7/H4 完成词做定语：命令参数尖括号占位"),
    ("slot:103", "1. 三个身份字段已填、全件无 `<` 占位残留（含容器层）；2. `reviewerSessionId` 是**本会话**运行态 ID，非他件 ID；3. `sourceTaskId` 若只能给计划号 → `unresolved` 已如实登记「正式任务书编号未落实」；4. 9 字段名与顺序 == NEXT:23 实文 == r2 schemaNote；5. `inputHashes` 四件为填时实算（python -I -X utf8 + hashlib）；6. `timestamp` 为填时实生成；7. 填用过", "已填", "V1", "M8/W1 人工自检清单第 1 项（编号核对项）"),
    ("slot:110", "### 5.4 多处同步排查表（哪件/哪行/需什么字段/是否已填）", "已填", "V1", "M2/H1 疑问式表题"),
    ("slot:112", "| # | 件 | 行 | 需什么字段 | 是否已填 |", "已填", "V1", "M6/H3 表格列头"),
    ("slot:114 [改写]", "| 1 | `DECISION_QUESTIONS.md`（C07 卡登记面） | :118-122（:120 问题原文、:121 非技术裁决、:122 proposed 待补登） | 三值补登本身；补登后状态行同步（属 N-10 域） | **未填**（是否已填 = 否） |", "已填", "V1", "取 slot:114 逐字行骨架，补入「（是否已填 = 否）」检验疑问式；非逐字原文"),
    ("slot:120", "| 7 | `a_residual_n1_20261108/ACCEPTANCE_RECORDS.json`（先例件，非 C07 落点） | 7 条 `sourceTaskId` 全 = `N-1`（计划号）；`reviewerSessionId` 已填 | 其自身任务的签发身份（非 C07 主体） | 部分（session 已填、任务号仍计划号——先例与反例） |", "已填", "V1", "M4/M6 H2/H3 先例与反例排查表（第 1 处命中）"),
    ("slot:120b", "| 7 | `a_residual_n1_20261108/ACCEPTANCE_RECORDS.json`（先例件，非 C07 落点） | 7 条 `sourceTaskId` 全 = `N-1`（计划号）；`reviewerSessionId` 已填 | 其自身任务的签发身份（非 C07 主体） | 部分（session 已填、任务号仍计划号——先例与反例） |", "已填", "V1", "M4/M6 H2/H3 同表第 2 处命中（部分（session 已填…）"),
    ("truth:151", "- 处置：已填 → 见证同为声明、非密码学证明，但其价值在独立性（记账方 ≠ 值的主张方，满足 NEXT:23「验收者与作者不得相同」）与可交叉检索性——伪造从「单方改文本」变成「两方合谋 + 两处可互查痕迹」；未填且缺席声明如实 → 通过档不可达，登记最高 PARTIAL + unresolved「运行标识无独立见证/独立记载」。", "已填", "V1", "M5/H6 配对分支处置（已填 → …；未填 → …）"),
    ("truth:228", "| G 见证与两处落笔 | 3 | 见证槽已填（见证人≠来源会话≠核验者）；见证缺席处置；两处落笔同值复用 | 代填见证→**拒绝**；N-4 同值复用失败→**拒绝** |", "已填", "V1", "M6/H3 清单表格「核什么」列 + H6 拒绝分支"),
    ("truth:240", "| **通过** | A-G 全部可核项 PASS、无未验残留、（G1 见证已填 或 S1 有 ≥1 处先于补登的外部独立记载）、无存疑项 | C07 行政登记完成（Q6 补登动作闭合）；不升格技术结论、不构成 APPROVE_SCOPE 签署或 N-5 放行 |", "已填", "V1", "M6/H3 判定条件列 + H6 选言（或 ≥1）"),
    ("truth:22 [改写]", "核验者不得代补、不得代填、不得以自身会话标识补位、不得以「看起来合理」放行；以上情形一律不得视为已填。", "已填", "V1", "取 truth:22 逐字行骨架，补入「不得视为已填」检验禁止管辖；非逐字原文"),
    ("truth:208 [改写]", "- **P5 §D 见证请求**：向派发本任务的工作流编排方发出见证请求；§D 槽位留空待编排方填写（**代填 = 拒绝项**），已填见证属拒绝情形。", "已填", "V1", "取 truth:208 逐字行骨架，补入「已填见证属拒绝情形」检验拒绝项语境；非逐字原文"),
    ("truth:204 [改写]", "- **P1 登记件三值补登**：复制 `_c7_record_template.json` → `ACCEPTANCE_RECORDS_C07.json`，仅替换占位符与定档字段（C07_IDENTITY_SLOT.md:79 填用流程）；三值 = 本会话运行态实际取得，已填件须按 9 字段形制不动。", "已填", "V1", "取 truth:204 逐字行骨架，补入「已填件须按 9 字段形制不动」检验定语；非逐字原文"),
    ("构造-V1-01 [规定式]", "来源会话须把三值已填件路径写入回件绑定行后交核验者。", "已填", "V1", "须 + 完成词做定语"),
    ("构造-V1-02 [否定式]", "三个身份字段未已填，本件不代填任何身份值。", "已填", "V1", "紧邻否定 + 禁止"),
    ("构造-V1-03 [疑问式]", "§5.4 排查表逐行核对：是否已填？", "已填", "V1", "疑问式"),
    ("构造-V1-04 [引述式]", "任务书要求把「已填」这类词报为越权断言，故本句只作引述。", "已填", "V1", "引证跨度内提及"),
    ("构造-V1-05 [表格]", "| 件 | 是否已填 | 需什么字段 |", "已填", "V1", "表格列头"),
    ("构造-V1-06 [条件式]", "若见证槽已填，则查 G1/G2 并对见证记载做 D2/D3/D4 交叉检索。", "已填", "V1", "若…则"),
    ("构造-V1-07 [做定语]", "复制 _c7_record_template.json 到落点名后，对 <已填件路径> 跑门禁。", "已填", "V1", "尖括号占位 + 命令语境"),
    ("构造-V1-08 [禁止完成]", "本件只备落点，不代填任何身份值；已填见证槽 = 拒绝项。", "已填", "V1", "禁止 + 拒绝项"),
    ("构造-V1-09 [规定式+完成词]", "填用流程规定：应按模板把已填件的四路 SHA256 实算复核。", "已填", "V1", "应 + 已填件 定语"),
]

# ================= 负样本集 V2（应当抓住） =================
# 两域真实行文内无真 V2（见结论），故全部为构造；说明现实中会在什么件里出现。
V2_SAMPLES = [
    ("构造-V2-01", "三个身份字段已填，reviewerSessionId = sess_dwf-…。", "已填", "V2", "来源会话补登回件自述完成"),
    ("构造-V2-02", "现已填三值并过增强门禁 exit 0。", "已填", "V2", "完成补登后回件的宣称"),
    ("构造-V2-03", "C07 登记件已填，SHA256 已实算并写入绑定行。", "已填", "V2", "把完成动作写进交付件"),
    ("构造-V2-04", "见证槽已填且见证语句已由编排方签字。", "已填", "V2", "越权代填见证后自述"),
    ("构造-V2-05", "C07 三值已填，登记闭合。", "已填", "V2", "台账登记行"),
    ("构造-V2-06", "本会话已提交 ACCEPTANCE_RECORDS_C07.json 与自证声明件。", "已提交", "V2", "交付完成宣称"),
    ("构造-V2-07", "reviewerRole 已填入登记件，值 = 项目负责人来源会话。", "已填入", "V2", "代填身份后自述"),
    ("构造-V2-08", "两处落笔已补登，N-4 任务书同值复用已复核。", "已补登", "V2", "完成断言"),
    ("构造-V2-09", "登记件指纹已填，14/14 MATCH 的绑定行已交付。", "已填", "V2", "含硬性宣称 已交付"),
    ("构造-V2-10", "§D 见证槽已代填，来源会话顺手补了编排方 run 标识。", "已代填", "V2", "明确禁止的行为被写成已完成"),
    ("构造-V2-11", "三值已填毕，未验项清零。", "已填", "V2", "硬性宣称 填毕"),
    ("构造-V2-12", "台账 :5906 已补登 Q6 责任身份，归档完毕。", "已补登", "V2", "台账归档行"),
    ("构造-V2-13", "门禁 PASS，C07 行政登记已填，Q6 补登动作闭合已如实照录。", "已填", "V2", "把判定档结果误写为已完成动作"),
    ("构造-V2-14", "已填完 13 键容器与 9 字段记录，落盘 ACCEPTANCE_RECORDS_C07.json。", "已填", "V2", "完成宣称 已填完"),
]

# ================= 同句混合 / 优先级对照 =================
MIXED_SAMPLES = [
    ("MIX-01 V1硬+V2硬", "是否已填？现已填三值并过门禁。", "已填", "V2", "整句聚合：疑问句（放过）+ 独立完成宣称（抓住）=> 句子级 V2"),
    ("MIX-02 规定式混入完成宣称", "填用流程规定应按模板核对，但三值已实算已交付。", "已填", "V2", "W1 前缀规定式不得压过 V2_OVERRIDE（本条 token 取 已交付，见下）"),
    ("MIX-03 分支+V2", "若见证槽已填，则查 G1/G2；现已填三值。", "已填", "V2", "同句既有条件分支又有独立完成宣称 => 句子级 V2"),
    ("MIX-04 纯V1混合", "排查表列头「是否已填」；若见证槽已填，则查 G1/G2。", "已填", "V1", "同句两处皆 V1 => V1"),
]


def run_sample(sid, text, token, expected, note):
    import _v12_rule as R
    s = text.find(token)
    if s < 0:
        print("  [SAMPLE-ERR] %s 找不到 token %s" % (sid, token))
        return False
    v = R.classify_v12(text, s, s + len(token), token)
    ok = v["verdict"] == expected
    tag = ",".join(v["hard"] + v["weak"]) or v["override"] or "DEFAULT_V2+REVIEW"
    print("  %-26s expect=%s got=%s %s | %s" %
          (sid, expected, v["verdict"], "PASS" if ok else "FAIL", tag))
    print("       TEXT: " + text[:160])
    print("       NOTE: " + note[:120])
    return ok


def run_mixed():
    import _v12_rule as R
    print("\n[MIXED] 同句混合处理：逐命中分类 + 句子级聚合（任一独立 V2 => 整句 V2）")
    rows = []
    # MIX-01
    t = "是否已填？现已填三值并过门禁。"
    cls = [(m.start(), R.classify_v12(t, m.start(), m.end(), "已填")["verdict"])
           for m in re.finditer("已填", t)]
    agg = "V2" if any(v == "V2" for _, v in cls) else "V1"
    rows.append(("MIX-01", cls, agg, "V2"))
    # MIX-02：规定式前缀 + 硬性完成宣称（用 已实算/已交付 检验，token=已交付）
    t = "填用流程规定应按模板核对，但三值已实算，绑定行已交付。"
    s = t.find("已交付")
    v = R.classify_v12(t, s, s + len("已交付"), "已交付")
    rows.append(("MIX-02", [(s, v["verdict"])], v["verdict"], "V2"))
    # MIX-03
    t = "若见证槽已填，则查 G1/G2；现已填三值。"
    cls = [(m.start(), R.classify_v12(t, m.start(), m.end(), "已填")["verdict"])
           for m in re.finditer("已填", t)]
    agg = "V2" if any(v == "V2" for _, v in cls) else "V1"
    rows.append(("MIX-03", cls, agg, "V2"))
    # MIX-04
    t = "排查表列头「是否已填」；若见证槽已填，则查 G1/G2。"
    cls = [(m.start(), R.classify_v12(t, m.start(), m.end(), "已填")["verdict"])
           for m in re.finditer("已填", t)]
    agg = "V2" if any(v == "V2" for _, v in cls) else "V1"
    rows.append(("MIX-04", cls, agg, "V1"))
    ok = 0
    for sid, cls, got, exp in rows:
        good = got == exp
        ok += good
        print("  %-8s hits=%s agg=%s expect=%s %s" %
              (sid, [v for _, v in cls], got, exp, "PASS" if good else "FAIL"))
    return ok, len(rows)


def main():
    global G7
    G7 = load_pred()
    print("[FIXTURE-FP] 谓词模块与两域指纹逐件实算（hashlib）：")
    for name, path, sha0, n0, bans in DOCS:
        sha, n = fp(path)
        print("  %-42s sha256 = %s bytes = %d MATCH=%s" %
              (name + "/" + path.name, sha, n, sha == sha0 and n == n0))
    for extra in [ROOT / "lead" / "c07_truth_protocol_20261109" / "_tp_C07_TRUTH_PROTOCOL.md",
                  ROOT / "lead" / "PENDING_DECISIONS.md",
                  ROOT / "lead" / "GOAL_THREE_TARGETS_20261018.md",
                  ROOT / "lead" / "gate_r9r12_20261109" / "_g9_gate.py",
                  ROOT / "lead" / "gate_doc_name_fix_20261109" / "_dn_regate_out.json"]:
        if extra.is_file():
            sha, n = fp(extra)
            print("  %-42s sha256 = %s bytes = %d" % (str(extra.relative_to(ROOT)), sha, n))
        else:
            print("  %-42s MISSING" % str(extra.relative_to(ROOT)))

    docs = [scan_doc(d) for d in DOCS]

    print("\n" + "=" * 100)
    print("[SAMPLES] V1 正样本（应放过）共 %d 条" % len(V1_SAMPLES))
    v1ok = sum(run_sample(*s) for s in V1_SAMPLES)
    print("[SAMPLES] V2 负样本（应抓住）共 %d 条" % len(V2_SAMPLES))
    v2ok = sum(run_sample(*s) for s in V2_SAMPLES)
    mok, mtotal = run_mixed()

    print("\n" + "=" * 100)
    print("[REGRESSION] V1 %d/%d PASS ; V2 %d/%d PASS ; MIXED %d/%d PASS" %
          (v1ok, len(V1_SAMPLES), v2ok, len(V2_SAMPLES), mok, mtotal))
    for d in docs:
        v1 = [h for h in d["hits"] if h["v12"] == "V1"]
        v2 = [h for h in d["hits"] if h["v12"] == "V2"]
        print("[DOMAIN] %s : R10 problems=%d warnings=%d ; 命中 %d 处 => V1=%d V2=%d (改判后残留 V2=%d)" %
              (d["doc"], len(d["r10_problems"]), len(d["r10_warnings"]), len(d["hits"]),
               len(v1), len(v2), len(v2)))
        for h in d["hits"]:
            print("    L%-4d %-6s R10=%-13s -> V12=%s %s" %
                  (h["line"], h["token"], h["r10_kind"], h["v12"],
                   ",".join(h["hard"] + h["weak"]) or h["override"] or "DEFAULT_V2+REVIEW"))

    out = {"docs": docs, "v1_samples": len(V1_SAMPLES), "v2_samples": len(V2_SAMPLES),
           "v1_pass": v1ok, "v2_pass": v2ok, "mixed_pass": mok, "mixed_total": mtotal}
    (WD / "_v12_regression.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("[WROTE] " + str(WD / "_v12_regression.json"))
    print("[SELF-CHECK] V1+V2+MIXED 须 100%% 双向成立；不足则不得据以宣称通过。")


if __name__ == "__main__":
    main()

    # ---------- 出口追加（仅追加；原件 1-259 行一字未改）----------
    # 本件是「库本体 + 自检主流程」混合形态：_v12v_fair.py:23 / _v12v_adv.py:21
    # 均以 import _v12_verify as W 复用 V1_SAMPLES/V2_SAMPLES/MIXED_SAMPLES。
    # 故 :1-257 库本体与 :258-259 的 __main__ 守卫逐字保留；新增代码全部写在守卫内部，
    # 只在以脚本方式运行时执行；被 import 时守卫不执行，不向库里新增任何全局名字
    # （ok/check/_report_path/_report/_rdocs/_i/_j/_d/_name/_path/_sha0/_n0/_bans
    #   均不进入被导入模块的命名空间），不覆盖调用方同名符号；未新增 import。
    #
    # 原件对【本脚本自身】的检查及产物通道（非对被测对象的领域词判定）：
    #   :38   [PRED-FP]    MATCH=sha==PRED_SHA and n==PRED_BYTES       -> print(stdout)
    #   :65   [DOC-FP]     MATCH_BASELINE=sha==sha0 and n==n0           -> print(stdout)
    #   :166-167 / :204-205 逐条 "PASS" if ok else "FAIL"            -> print(stdout)
    #   :213-216 [FIXTURE-FP] MATCH=...                                 -> print(stdout)
    #   :232/:234/:235 v1ok/v2ok/mok 为上述逐条 ok 的合取计数
    #   :238-239 [REGRESSION] V1/V2/MIXED 汇总                           -> print(stdout)
    #   :251-253 同一批计数写盘 WD/_v12_regression.json（:254 打印 [WROTE]）
    #   :255 [SELF-CHECK] 明文「V1+V2+MIXED 须 100% 双向成立；不足则不得据以宣称通过」-> print(stdout)
    #   全件无 assert、无 sys.exit/SystemExit；:258-259 只调用 main()，退出码恒 0
    #   （EXIT_CRITERION.md:500 登记为 E0；CONST_EXIT_CENSUS.md:735 登记 NO_EXIT_AT_ALL）。
    # main() 的局部变量在模块级不可见；为不重跑、不重复打印、不改库本体，
    # 取 main() 自己刚写出的 _v12_regression.json 作为同一判定的记录读取。
    # [DOMAIN] :243-249 的 R10 problems / V12=V1,V2 是对被测两域文档的领域统计，非脚本自检，不纳入出口。
    ok = True

    def check(name, cond, detail=""):
        global ok
        ok = ok and bool(cond)          # 合取聚合：全部检查通过才真
        print(("  [PASS] " if cond else "  [FAIL] ") + name + ((" | " + detail) if detail else ""))

    _report_path = WD / "_v12_regression.json"
    _report = json.loads(_report_path.read_text(encoding="utf-8")) if _report_path.is_file() else None
    check("[WROTE] 回归结果件存在且可读", _report is not None, str(_report_path))
    check("PRED-FP 谓词模块指纹匹配基线", fp(PRED) == (PRED_SHA, PRED_BYTES))
    for _i, (_name, _path, _sha0, _n0, _bans) in enumerate(DOCS, 1):
        check("FIXTURE-FP[%d] %s 指纹匹配基线" % (_i, _name), fp(_path) == (_sha0, _n0))

    if _report is not None:
        _rdocs = _report.get("docs", [])
        check("DOC-FP 两域回算指纹匹配基线",
              len(_rdocs) == len(DOCS) and all(
                  (_d.get("sha"), _d.get("bytes")) == (DOCS[_j][2], DOCS[_j][3])
                  for _j, _d in enumerate(_rdocs)))
        check("V1 正样本 100%% (%s/%s)" % (_report.get("v1_pass"), _report.get("v1_samples")),
              _report.get("v1_pass") == _report.get("v1_samples") == len(V1_SAMPLES))
        check("V2 负样本 100%% (%s/%s)" % (_report.get("v2_pass"), _report.get("v2_samples")),
              _report.get("v2_pass") == _report.get("v2_samples") == len(V2_SAMPLES))
        check("MIXED 混合样本 100%% (%s/%s)" % (_report.get("mixed_pass"), _report.get("mixed_total")),
              _report.get("mixed_pass") == _report.get("mixed_total") == len(MIXED_SAMPLES))

    print("核验结论: " + ("ALL PASS" if ok else "FAIL"))
    raise SystemExit(0 if ok else 1)
