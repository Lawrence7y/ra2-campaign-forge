# -*- coding: utf-8 -*-
"""由 _enum_rounds.json（实跑快照）+ 本次处置判定表生成 ROUND_GAP_DISPOSITION.csv。
枚举列（目录名/日期/类别/递归文件数/有无md/有无输出）全部取自 JSON，不手抄；
判定/理由/取代证据/建议批次为本次人工定性，内嵌于本脚本。
"""
import io
import json
import csv
import os
import sys

SELF = os.path.dirname(os.path.abspath(__file__))
with io.open(os.path.join(SELF, "_enum_rounds.json"), encoding="utf-8") as fh:
    data = json.load(fh)
records = [r for r in data["records"] if r["depth"] == 0]

# dir name -> (判定, 理由, 取代证据, 建议批次)
J = {
    # ---- B 轮（无报告）· 报告口径内 18 个 ----
    "const_exit_fix_20261110": (
        "废弃",
        "patched/ 内 18 个 py 全为他轮探针的字节副本（dup_audit PATCH_COPY 组 sha256=85cde303… 点名本目录 _reviewer_t2_rerun_mtime_probe.py/_w11_t2_mtime_probe.py 与 re_line_20261105 同件）；目录内只有 py+pyc，无任何运行输出、无 md；出口判据正本已由 exit_criterion_20261110（_ec_s4_results.json 对 263 件实跑）与 e3_unify_20261111/_e3_v3.py（第三版）承接。DISPOSITION.md:L62 判「补做」并引 VERIFY_A8.py:L824-L826 称实跑 ALL PASS，但本目录无落盘输出，实跑未验——本次改判废弃，分歧如实登记",
        "dup_audit_20261110/_da_summary.txt 尾节（PATCH_COPY 组 4 路径含 lead/const_exit_fix_20261110/patched/…）；exit_criterion_20261110/_ec_s4_results.json（263 件已跑）；DISPOSITION.md:L62（分歧登记）",
        "第三批（归档）"),
    "crit_fix_20261110": (
        "废弃",
        "E3 出口判据 v1 修补（_ec_criterion_fixed.py 46,005 B + repro/ 四件），无输出无 md；已被 e3_fix2 消费为 before 基线、最终被 e3_unify v3 统一取代",
        "e3_fix2_20261110/_before.json 头部 criterion 字段指向 lead/crit_fix_20261110/_ec_criterion_fixed.py（被消费证据）；DISPOSITION.md:L63（引 e3_unify_20261111/_e3_v3.py:L7）",
        "不适用（归档）"),
    "dup_audit_20261110": (
        "补做",
        "读数已齐：lead/ 下 2928 个 .py 只读普查、2517 个唯一 sha256、72 组重复（PATCH_COPY 13 / REVIEW_COPY 2 / BENIGN_DUP 57），落盘 _da_summary.txt+_da_groups.json；缺一页 md 结论与台账条目；输入=既有两件输出",
        "DISPOSITION.md:L64（判入账/第二批补md，引 _da_summary.txt:L2-L8）",
        "第二批（补md，工作量小）"),
    "e3_fix2_20261110": (
        "废弃",
        "E3 判据 v2 + 7 正控 3 负控跑测（_before/_after.json 各 16,742 B）；被 e3_unify v3（修七条已知缺陷）吸收终结，数据件留作过程证据",
        "e3_unify_20261111/_e3_v3.py 文档串「统一两套既有实现的正确部分，修七条已知缺陷」；DISPOSITION.md:L65",
        "不适用（归档）"),
    "e3_secondimpl_20261110": (
        "废弃",
        "独立第二实现 _ei3_e3.py（AST-only，刻意不看参考实现），背靠背对照使命完成，被 v3 吸收",
        "e3_unify_20261111/_e3_v3.py；DISPOSITION.md:L66",
        "不适用（归档）"),
    "e3_unify_20261111": (
        "补做",
        "_e3_v3.py（22,608 B）统一判据本体就绪但零跑测输出、零 md；缺 413 件全量扫描与验收报告 E3_UNIFY.md；输入=ok_falsify_20261110/_of_scope_out.json 的 413 件清单",
        "DISPOSITION.md:L67/L155/L175（列第二批补做、Top-7）",
        "第二批（高优先）"),
    "esi_caller_trace_20261111": (
        "废弃",
        "slot2 调用点首轮普查（1,392,527 条分块反汇编、1714 个 slot2 形态点、0x54A4F0/0x54A630 直接调用 0、唯一候选 0x546069）；已被 slot2_fullscan_20261111 100% 分块重验逐数复现并加固（155215 陷阱、1150117×62、1392527/65 停点、T5-final 唯一 0x546069）",
        "slot2_fullscan_20261111/_sf_scan_out.txt T1/T4/T5-final 节；DISPOSITION.md:L68（引 _sf_scan.py:L11-L15）",
        "不适用（读数被完整继承）"),
    "exit_lint_20261110": (
        "补做",
        "_el_lint.py 登记前出口 lint 路由器（PASS/REJECT/MANUAL/ERROR），判据底座仍挂旧版 _ec_criterion；缺对接 _e3_v3.py 的改造与自测记录",
        "DISPOSITION.md:L69（引 _el_lint.py:L8-L12）",
        "第三批"),
    "gate_exit_retrofit_20261110": (
        "补做",
        "出口模板对照件已实跑（_gr_template_ctl_run.txt：-1→exit 0、1→exit 1 两次「对得上」）；patched/ 24 个改造脚本缺统一回归日志与验收报告",
        "DISPOSITION.md:L70（引 _gr_template_ctl_run.txt:L37-L39）",
        "第三批"),
    "ledger_exit_census_20261110": (
        "补做",
        "读数已齐：三本台账硬编码 EXIT=0 共 76 处（分布 31/1/44），cls 计数 NO_EXIT_AT_ALL 5 / CONDITIONAL_EXIT 28 / CONSTANT_EXIT 1 / NOT_CENSUSED 2 / NO_PY_NAME 40，与 const_exit 413 普查对齐；缺 md 沉淀",
        "DISPOSITION.md:L71（判入账/第一批补md，引 _lc_out.txt:L8-L15）",
        "第二批（补md）"),
    "ok_falsify_20261110": (
        "补做",
        "读数已齐：413 件全量出口判据三维交叉表（UNKNOWN+NEEDS_FIX 分组 n=18 等），_of_scope_out.json 97,659 B；缺 md 沉淀",
        "DISPOSITION.md:L72（判入账/第二批补md，引 _of_scope_out.json:L3390-L3430）",
        "第二批（补md）"),
    "playerctrl_semantics_20261111": (
        "已入他处",
        "PlayerControl@0x824E28→HouseClass+0x1ED、PercentBuilt@0x8189A0→+0x571C 引擎零读取、8 处创建点均未测试该标志；结论已被因果链报告覆盖；DISPOSITION 原表述「实例数严格由 [Houses] 决定」已被降级为 CFG 级",
        "re_chain_synthesis_20261111/CHAIN_SYNTHESIS.md:L81-L82（⑤【已证】）；re_chain_synth_v2_20261111/RE_GRADING.md:L43（R14 维持已证）；re_chain_v2_xverify_20261112/XVERIFY.md:L84（R15）；降级口径见 re_round_batch1_20261111/ROUND_BATCH1.md:L162-L163（R3-02 已证/R3-03 未证）",
        "不适用（独立补 md 属锦上添花）"),
    "re_crashwriter_static_20261110": (
        "已入他处",
        "0x0054A56E 数据依赖链：RTTI 基类 vtable 0x7ECBFC/派生 0x7ECBDC、全局对象 0xAA1078、0x546069 全模块唯一虚派发点、0x54A56E 置 0 在 8 字节内被无条件覆盖；结论已入因果链报告",
        "re_chain_synthesis_20261111/CHAIN_SYNTHESIS.md（证据缩写 cw，LEDGER_SECTION_DRAFT_v2.md:L6）；DISPOSITION.md:L74（引 _cw_disasm_out.txt:L80-L105）",
        "不适用"),
    "re_loadbench_diff_20261110": (
        "已入他处",
        "大版 92,332 B（md5 3c47bff8…）与小版 25,604 B（生成器 2026-09-25 合成图）非同一张图；实载=222,799 B 变体（md5 11ec8ff6，1680/1120/41）以 XMP29U2.MAP 名载入；其[未决]台账指纹 93c2974b 已由 RE_PROGRESS §8 表解决（载体件 sha256 前16=93c2974b934acdc4）",
        "re_progress_check_20261111/RE_PROGRESS_20261111.md:L118-L124（§8 表）；DISPOSITION.md:L75（引 _ld_diff_out.txt:L98-L103）",
        "不适用"),
    "re_map_preset_decode_20261110": (
        "已入他处",
        "三图逐槽位解析：XMP29U2.MAP [Units]=3360（14 owner×240）、两份 yrm 均 240/160，台账声称 1680/1120 判「两份 yrm 均不符」；已入因果链报告④",
        "re_chain_synthesis_20261111/CHAIN_SYNTHESIS.md:L77（④【已证】）；DISPOSITION.md:L76（引 _md_parse_out.txt:L140-L167）",
        "不适用"),
    "re_orphan_owners_20261110": (
        "已入他处",
        "HouseClass owner 三层法：XMP29U2.MAP 14 owner 带各 400 实体（240 车+160 步）；MaxPlayer=2 与 14 owner 文件层不矛盾，运行期 meta_count=4 属引擎侧行为、文件不可证；已入因果链报告③",
        "re_chain_synthesis_20261111/CHAIN_SYNTHESIS.md:L75（③【已证】）；re_orphan_owners_20261110/_oo_map_out.txt [5c] 节；DISPOSITION.md:L77",
        "不适用"),
    "slot2_fullscan_20261111": (
        "已入他处",
        "100% 分块重验：1714 个 slot2 形态点中可能指向 0x54A4F0/0x54A630 的恰 1 个=0x546069；已被处置书与因果链报告收录",
        "DISPOSITION.md:L78（引 _sf_scan_out.txt:L1830-L1834）；re_round_batch1_20261111/ROUND_BATCH1.md:L40（R1..R5 收录）",
        "不适用"),
    "unknown_locate_20261110": (
        "补做",
        "读数已齐：263 件 NO_EXIT_AT_ALL 的 stdout 产物通道普查（11 件仅 stdout.write：9 UNKNOWN+2 ARTIFACT，GATE/PROBE 为 0）；缺 md 沉淀",
        "DISPOSITION.md:L79（引 _ul_stdout_census_out.txt:L22-L37）",
        "第二批（补md）"),
    # ---- C 轮（空）· 报告口径内 11 个 ----
    "backlog_sweep_20261110": (
        "废弃",
        "空目录（0 文件），已启动未落盘；积压清理已被全盘进度审计与 PENDING_DECISIONS 治理吸收",
        "DISPOSITION.md:L80",
        "第三批（清理）"),
    "crit_recheck_20261110": (
        "废弃",
        "空目录；判据复验已由 crit_fix→e3_fix2→e3_unify 判据链交付",
        "DISPOSITION.md:L81",
        "第三批（清理）"),
    "e3_rootcause_20261110": (
        "废弃",
        "空目录；吞没异常根因已沉淀为 _e3_v3.py 七条缺陷修复规则",
        "DISPOSITION.md:L82（e3_unify_20261111/_e3_v3.py:L7-L35）",
        "第三批（清理）"),
    "e3_triage_20261110": (
        "废弃",
        "空目录；413 件分流已由 ok_falsify 的 _of_scope_out.json 完成",
        "DISPOSITION.md:L83",
        "第三批（清理）"),
    "housecount_trace_20261111": (
        "废弃",
        "空目录；静态侧已闭环（8 处创建点未测 PlayerControl、[Houses]↔节对应、meta_count=4 文件层澄清）；动态 trace 受 D-13 PAUSE/BLOCKED 阻塞，属被阻塞而非待补",
        "DISPOSITION.md:L84（playerctrl _ps_disasm_out.txt:L636-L642）；re_progress_check_20261111/RE_PROGRESS_20261111.md:L82（D-13 阻塞）",
        "第三批（清理；D-13 解禁后如需动态 trace 再立项）"),
    "ledger_apply_prep_20261110": (
        "已入他处",
        "空目录但目标已完成：§605–§609 五笔已于 11-11 21:1x 并入主台账（追加 28,512 B，759,518→788,030 B，sha256 a2579798…）并经独立核验 PASS；DISPOSITION（21:05）判「补做 P1」早于并账落盘（21:16），本次据实修正",
        "re_ledger_apply_20261111/APPLY_RECEIPT.md:L10-L23；re_ledger_verify_20261111/VERIFY.md:L16（V1 PASS）；GOAL_THREE_TARGETS_20261018.md:L9760/L9775/L9787/L9802/L9832（§605–§609 实测在册）",
        "不适用（已完成并核验）"),
    "ledger_num_audit_20261111": (
        "废弃",
        "空目录；台账编号核验已由异族核验 VERDICT 闭环，并账与核验已由 re_ledger_apply/re_ledger_verify 完成",
        "DISPOSITION.md:L86（re_progress_xverify VERDICT §1）；re_ledger_verify_20261111/VERIFY.md:L16",
        "第三批（清理）"),
    "mapfile_1680_hunt_20261111": (
        "废弃",
        "空目录；1680/1120 载体寻源已由 re_loadbench_diff 完成（实载=222,799 B 变体以 XMP29U2.MAP 名载入；在盘 yrm 均 240/160 不符）",
        "DISPOSITION.md:L87（re_loadbench_diff_20261110/_ld_diff_out.txt:L101）；re_map_preset_decode_20261110/_md_parse_out.txt 尾节「两份 yrm 均不符」",
        "第三批（清理）"),
    "re_chain_semantics_20261110": (
        "废弃",
        "空目录；0x54A56E 链语义已由 re_crashwriter_static 全量交付并升级为因果链报告",
        "DISPOSITION.md:L88（re_crashwriter_static_20261110/_cw_disasm_out.txt:L80-L105）",
        "第三批（清理）"),
    "re_line_collapse_20261111": (
        "废弃",
        "空目录；轮次收缩治理已被 re_round_disposition 写域全盘接管",
        "DISPOSITION.md:L89（re_dispatch_20261111/BRIEF_D.md:L1）",
        "第三批（清理）"),
    "recon_20261110": (
        "废弃",
        "空目录；宽泛静态侦察已分流为 re_crashwriter_static / re_loadbench_diff / re_map_preset_decode / re_orphan_owners 四个具体轮次",
        "DISPOSITION.md:L90",
        "第三批（清理）"),
    # ---- 口径外 ----
    "re_atlas_reassess_20261112": (
        "补做（进行中）",
        "11-12 当日新轮（报告口径外）：re_atlas 全量指纹 498 件 + R-036 重算 8/8 PASS + R-035 复核 23/23 PASS（REGISTER：debug 归属 761→758 差-3；overlap 523,181/48.7%）；进行中，登记不判",
        "re_atlas_reassess_20261112/step2_r036_rerun.stderr.txt（RESULT: 8/8 PASS）；step2_verify_r035.stdout.txt（RESULT: 23/23 PASS）",
        "口径外（进行中）"),
    "round_gap_disposition_20261112": (
        "本检查写域",
        "本次处置任务的写域目录；枚举时点为空目录故入 C 类，非项目轮次",
        "本目录", "不适用"),
}

PRE = {
    "goal1_harness8_20261031": "10 月 harness8 判据/启动脚本族 + .mimosa 钩子状态件",
    "l1b_20261021": "10 月真机测量数据轮（receipt/measure/json）",
    "l1c_20261021": "10 月真机测量数据轮（receipt/measure/json）",
    "l1d_20261021": "10 月真机测量数据轮（receipt/measure/json）",
    "l1e_20261021": "10 月真机测量数据轮（receipt/measure/json）",
    "l3_20261021": "10 月真机测量数据轮（receipt/measure/json）",
    "master_backup_20261020": "母本备份（blitter_hooks.cpp/ra2render.h/.ini）",
    "qc151_carrierfix_20261020": "carrierfix.diff + report.json",
    "t55k_20261020": "10 月真机测量数据轮（T55k 全套 receipt/measure）",
}

rows = []
for r in sorted(records, key=lambda x: (x["date"], x["name"])):
    name, date, cat = r["name"], r["date"], r["category"]
    rec = r["rec_files"]
    has_md = "有(%d)" % len(r["md"]) if r["md"] else "无"
    non_code = [f for f in r["files"] if not f["rel"].lower().endswith((".py", ".pyc"))]
    has_out = "有(%d件)" % len(non_code) if non_code else "无"
    cls = {"A": "有md报告", "B": "无报告有探针或输出", "C": "递归空"}[cat]
    if name in J:
        j = J[name]
    elif cat == "A":
        j = ("已成立（有md报告，无需处置）", "递归含 md 报告，属 153/164 口径内已交付轮", "-", "-")
    elif date < "20261106":
        j = ("口径外登记", "日期 <20261106，不在报告 182 口径内；%s；是否补报告由十月线自行定" % PRE.get(name, ""), "-", "口径外")
    elif date == "20261112":
        j = ("口径外（当日新增）", "2026-11-12 当日目录，晚于报告快照（11-11 20:3x），不在 182 口径对照内；其中多目录正被实时写入", "-", "口径外")
    else:
        j = ("未覆盖", "不应出现", "-", "-")
    rows.append([name, date, cls, rec, has_md, has_out, j[0], j[1], j[2], j[3]])

out_path = os.path.join(SELF, "ROUND_GAP_DISPOSITION.csv")
with io.open(out_path, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["目录名", "日期", "类别", "递归文件数", "有无md", "有无输出", "判定", "理由", "取代证据", "建议批次"])
    w.writerows(rows)
print("rows=%d -> %s" % (len(rows), out_path))
# 快速自检：报告口径内 B/C 必须都有判定
win_bc = [r for r in records if "20261106" <= r["date"] <= "20261111" and r["category"] in ("B", "C")]
missing = [r["name"] for r in win_bc if r["name"] not in J]
print("window B+C=%d, missing_judgment=%s" % (len(win_bc), missing or "无"))
sys.exit(1 if missing else 0)
