#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""facts_floors.py —— FACT_INDEX 守门脚本（R160 v2 生成，勿手改；改请改 _r160/r160c_gen_guard.py）。

存在理由（实测）：主门禁 check_disc.py 从不读 FACT_INDEX.tsv —— 它是这两条纪律的
C7 证据产物之外的**零接触**。所以台账的任何改动对既有门禁完全不可见。本脚本补此缺口。

检查项（v2 全部收紧；每条都经破坏性沙箱证明能 FAIL）：
  D0  sha256 指针。**无论 argv 指向哪里都比**（v1 在 argv 模式下恒不触发，是假门）。
  D1  LF-only。
  D2  表头 5 列逐字。
  D3  56 数据行 / 每行恰 5 列。
  D4  fact_id 恰为 F01..F56 有序无重。
  D5  **逐 fid 的 grade**（v1 只钉普查，F01<->F13 互换可过）。
  D6  **逐 fid 的 statement/limitations 字节不许缩**（v1 用一半为下界，截断一半可过）。
  D7  **逐 fid 的证据项清单** + 第 4 列字节不许缩 + 失联多重集（v1 只钉全局计数）。
  D8  总字节不许缩（v1 用一半为下界）。
  D9  **单一主指纹覆盖全部常量**（含 grade/EVID/EVIDB/字节/GATE 计数）。
  D10 **当前版指针**必须与本文件 CUR_SHA256/TOTAL_BYTES 及 CUR 实物 sha 一致。
      （R180 新增：此前该指针在 check_disc / gate_runner / 本脚本三者中读取次数各 0，
      静默漂移时三门全绿；判据是两条独立事实的相等，不是文本相似。）

如实声明的边界：
  1) 所有 pin 都是本文件里的常量。**同时改数据与常量**仍能过 —— 这是所有指纹/下界类
     门禁的共同上限（与主门禁 C10/C16 同族）。本脚本的价值不是「不可能绕过」，而是把
     「完全不被读」变成「任何缩水/换归/改 grade 都会撞到一条会 FAIL 的断言」。
  2) D6/D7/D8 采用「不许缩」而非「不许改」：允许追加、允许等长改写，禁止变短。
     若某轮确需缩短，必须**显式重钉**（与 GATE_VER 重钉同纪律），不得静默。
  3) 本脚本**不判断事实真假**，只判断台账结构与规模没有被静默削减。
  4) --ignore-pin 仅供破坏性自测使用，且会大声打印警告；生产调用不得带它。

退出码：0 全通过；1 有 FAIL。
"""
import csv
import hashlib
import io
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.isdir(os.path.join(ROOT, 'lead')):
    ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
EXPECT_CUR = os.path.join(TIER, 'R17_R131_FACTINDEX_V576', 'FACT_INDEX.tsv')
CUR = EXPECT_CUR
IGNORE_PIN = False
for a in sys.argv[1:]:
    if a == '--ignore-pin': IGNORE_PIN = True
    elif not a.startswith('-'): CUR = a
if IGNORE_PIN:
    print('  !! WARNING --ignore-pin: sha256/master-pin assertions DISABLED (self-test only)')

CUR_SHA256 = '50efc7281c9a20ecb7d37f1006dc34425e225f4a5ad233fde93e289407d81485'
TOTAL_BYTES = 171758
GRADES = {
    'F01': '[已证]',
    'F02': '[已证]',
    'F03': '[已证]',
    'F04': '[已证]',
    'F05': '[已证]',
    'F06': '[已证]',
    'F07': '[已证]',
    'F08': '[静态推断]',
    'F09': '未取得',
    'F10': '[已证]',
    'F11': '[已证]',
    'F12': '[已证]',
    'F13': '[流程]',
    'F14': '[已证]',
    'F15': '[已证]',
    'F16': '未取得',
    'F17': '[已证]',
    'F18': '[已证]',
    'F19': '[已证]',
    'F20': '[流程]',
    'F21': '[已证]',
    'F22': '[已证]',
    'F23': '未取得',
    'F24': '[已证]',
    'F25': '[流程]',
    'F26': '[流程]',
    'F27': '[已证]',
    'F28': '[流程]',
    'F29': '[已证]',
    'F30': '[流程]',
    'F31': '[已证]',
    'F32': '[已证]',
    'F33': '[已证]',
    'F34': '[流程]',
    'F35': '[流程]',
    'F36': '[流程]',
    'F37': '[流程]',
    'F38': '[流程]',
    'F39': '[流程]',
    'F40': '[流程]',
    'F41': '[流程]',
    'F42': '[流程]',
    'F43': '[流程]',
    'F44': '[流程]',
    'F45': '[已证]',
    'F46': '[流程]',
    'F47': '[流程]',
    'F48': '[流程]',
    'F49': '[已证]',
    'F50': '[流程]',
    'F51': '[已证]',
    'F52': '[流程]',
    'F53': '[流程]',
    'F54': '[流程]',
    'F55': '[已证]',
    'F56': '[流程]',
}
FLOORS = {
    'F01': (458, 14490),
    'F02': (292, 192),
    'F03': (287, 217),
    'F04': (317, 226),
    'F05': (327, 199),
    'F06': (381, 125),
    'F07': (345, 211),
    'F08': (490, 2079),
    'F09': (468, 308),
    'F10': (512, 336),
    'F11': (274, 300),
    'F12': (445, 371),
    'F13': (459, 237),
    'F14': (143, 124),
    'F15': (389, 346),
    'F16': (447, 231),
    'F17': (337, 281),
    'F18': (433, 320),
    'F19': (518, 202),
    'F20': (427, 56),
    'F21': (318, 252),
    'F22': (377, 91),
    'F23': (1785, 8200),
    'F24': (11419, 37746),
    'F25': (301, 125),
    'F26': (190, 73),
    'F27': (230, 146),
    'F28': (348, 193),
    'F29': (3435, 20898),
    'F30': (305, 169),
    'F31': (221, 291),
    'F32': (246, 216),
    'F33': (196, 133),
    'F34': (348, 174),
    'F35': (1751, 12435),
    'F36': (367, 320),
    'F37': (349, 154),
    'F38': (175, 176),
    'F39': (216, 212),
    'F40': (219, 138),
    'F41': (216, 3),
    'F42': (126, 3),
    'F43': (165, 3),
    'F44': (165, 3),
    'F45': (120, 110),
    'F46': (179, 97),
    'F47': (186, 3),
    'F48': (136, 3),
    'F49': (515, 467),
    'F50': (516, 246),
    'F51': (143, 325),
    'F52': (337, 90),
    'F53': (251, 377),
    'F54': (375, 211),
    'F55': (10455, 7691),
    'F56': (519, 1601),
}
EVID = {
    'F01': ['lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/R17_R50_ADJ_PSELF/VERDICT.md'],
    'F02': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md'],
    'F03': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md'],
    'F04': ['lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md'],
    'F05': ['lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/R14_COMMON.md'],
    'F06': ['lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md', 'lead/next_re_20261117_r14/R14_COMMON.md'],
    'F07': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md'],
    'F08': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md'],
    'F09': ['lead/next_re_20261117_r14/R17_LEDGER_1065/SECTION.md', 'lead/next_re_20261117_r14/R17_LEDGER_1063/SECTION.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/R14_COMMON.md'],
    'F10': ['lead/next_re_20261117_r14/R17_LEDGER_1065/SECTION.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md'],
    'F11': ['lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md'],
    'F12': ['lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md'],
    'F13': ['lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/R17_LEDGER_1063/SECTION.md', 'lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md', 'lead/next_re_20261117_r14/R14_COMMON.md'],
    'F14': ['lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/GOAL_THREE_TARGETS_20261018.md', 'lead/next_re_20261117_r14/R17_R19_RTTI_XCHECK/reconcile.tsv', 'lead/next_re_20261117_r14/R17_R24_RECON_FINAL/reconcile_final.tsv', 'lead/next_re_20261117_r14/R17_R17_SLOT73_MAP/reverse_map.tsv', 'lead/next_re_20261117_r14/R17_R70_T2_RTTIONLY/REPORT.md'],
    'F15': ['lead/next_re_20261117_r14/R17_LEDGER_1063R/SECTION.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/R17_LEDGER_1063/SUPERSEDED.md'],
    'F16': ['lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/R17_LEDGER_1063/SECTION.md', 'lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md'],
    'F17': ['lead/next_re_20261117_r14/R14_COMMON.md'],
    'F18': ['lead/next_re_20261117_r14/GATE_BEHAV/CASES.tsv', 'lead/next_re_20261117_r14/GATE_BEHAV/PROGRESS.md', 'lead/next_re_20261117_r14/R14_COMMON.md'],
    'F19': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/R17_R8_RESIDUAL/REPORT.md', 'lead/next_re_20261117_r14/R17_AUDIT_R9/VERDICT.md', 'lead/next_re_20261117_r14/R17_R10_DISPATCH/REPORT.md', 'lead/next_re_20261117_r14/R17_AUDIT_R10/VERDICT.md', 'lead/next_re_20261117_r14/R17_R26_HOST_ROLE/REPORT.md', 'lead/next_re_20261117_r14/R17_R29_UPSTREAM/REPORT.md', 'lead/next_re_20261117_r14/R17_AUDIT_FACTINDEX/missing_entries.md'],
    'F20': ['lead/LEAD_LOCK', 'lead/next_re_20261117_r14/R17_R36_VERIFY_TABLEBASE/VERDICT.md', 'lead/next_re_20261117_r14/R17_AUDIT_FACTINDEX/VERDICT.md'],
    'F21': ['lead/next_re_20261117_r14/R17_R35_V5657A0_TABLE/REPORT.md', 'lead/next_re_20261117_r14/R17_R36_VERIFY_TABLEBASE/VERDICT.md'],
    'F22': ['lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md', 'lead/next_re_20261117_r14/COVERAGE/PANEL.md', 'lead/next_re_20261117_r14/R14_COMMON.md'],
    'F23': ['lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md', 'lead/next_re_20261117_r14/COVERAGE/PANEL.md'],
    'F24': ['lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md', 'lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/R16_MEASURE_EVID675/REPORT.md', 'lead/next_re_20261117_r14/R16_AUDIT_EVID675/VERDICT.md', 'lead/GOAL_THREE_TARGETS_20261018.md', 'lead/next_re_20261117_r14/R16_MEASURE_EVID675/mev675.py', 'lead/next_re_20261117_r14/R17_R72_T1_CLEANSCALE/REPORT.md', 'lead/next_re_20261117_r14/R17_R72_T1_CLEANSCALE/files_tier_A_snap2.tsv', 'lead/next_re_20261117_r14/R17_R72_T1_CLEANSCALE/files_tier_C.tsv', 'lead/next_re_20261117_r14/R17_R75_T2_DRIFT/REPORT.md', 'lead/next_re_20261117_r14/R17_R75_T1_AUDITSELF/REPORT.md', 'lead/next_re_20261117_r14/R17_R78_T4_AUDIT30/REPORT.md', 'lead/next_re_20261117_r14/R17_R78_T1_RECLASS/REPORT.md', 'lead/next_re_20261117_r14/R17_R78_T1_RECLASS/files_tier_Cprime.tsv', 'lead/next_re_20261117_r14/R17_R81_T4_AUDIT32/REPORT.md', 'lead/next_re_20261117_r14/R17_R81_T1_AUDITCP/REPORT_AUDITCP.md', 'lead/next_re_20261117_r14/R17_R84_T4_AUDIT34/REPORT.md', 'lead/next_re_20261117_r14/R17_R84_T2_EVID2/REPORT.md', 'lead/next_re_20261117_r14/R17_R84_T1_NARRATIVE/REPORT.md', 'lead/next_re_20261117_r14/R17_R88_T1_SEMDEF/REPORT.md', 'lead/next_re_20261117_r14/R17_R88_T1_SEMDEF/tier_final.tsv', 'lead/next_re_20261117_r14/R17_R92_T1_REJUDGE/REPORT.md', 'lead/next_re_20261117_r14/R17_R92_T1_REJUDGE/rejudge1242.tsv', 'lead/next_re_20261117_r14/R17_R92_T1_REJUDGE/q3_matrix.tsv', 'lead/next_re_20261117_r14/R17_R96_TIER_FINAL_4413/tier_final_4413.tsv', 'lead/next_re_20261117_r14/R17_R97_TIER_FINAL_4413B/tier_final_4413b.tsv', 'lead/next_re_20261117_r14/R17_R95_T1_A2SITES/REPORT.md', 'lead/next_re_20261117_r14/R17_R99_TIER_FINAL_4416/tier_final_4416.tsv', 'lead/next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv'],
    'F25': ['lead/next_re_20261117_r14/RULING_R15_20261119/work/strict_panel.py', 'lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md', 'lead/next_re_20261117_r14/COVERAGE/PANEL.md'],
    'F26': ['lead/PENDING_DECISIONS.md', 'lead/next_re_20261117_r14/R14_COMMON.md'],
    'F27': ['lead/LEAD_LOCK', 'lead/next_re_20261117_r14/HANDOFF_R16.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/GOAL_THREE_TARGETS_20261018.md', 'lead/next_re_20261117_r14/R17_R56_FACTINDEX_V53/lead_byte_checks.tsv'],
    'F28': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/LEAD_LOCK', 'lead/next_re_20261117_r14/NAMED_PUSH_AUDIT10/VERDICT.md', 'lead/next_re_20261117_r14/COVERAGE/PANEL.md'],
    'F29': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/LEAD_LOCK', 'lead/next_re_20261117_r14/COVERAGE/PANEL.md', 'lead/next_re_20261117_r14/R17_R52_ADJ_D4/VERDICT.md', 'lead/next_re_20261117_r14/R17_R68_T1_IAT/REPORT.md', '_r139/r139e_f29_6377.py', '_r139/r139f_f29_family.py', '_r139/r139a_f29_bytes.py'],
    'F30': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/LEAD_LOCK'],
    'F31': ['lead/LEAD_LOCK', 'lead/GOAL_THREE_TARGETS_20261018.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/R17_R50_ADJ_PSELF/VERDICT.md'],
    'F32': ['lead/LEAD_LOCK', 'lead/GOAL_THREE_TARGETS_20261018.md'],
    'F33': ['lead/LEAD_LOCK'],
    'F34': ['lead/LEAD_LOCK', 'lead/next_re_20261117_r14/COVERAGE/PANEL.md'],
    'F35': ['lead/next_re_20261117_r14/COVERAGE/PANEL.md', 'lead/next_re_20261117_r14/RULING_R15_20261119/work/strict_panel.py', 'lead/next_re_20261117_r14/_cards/M59-MERGE/precheck.py', 'lead/next_re_20261117_r14/_cards/M59-MERGE/simulate.py', 'lead/next_re_20261117_r14/_cards/M59-MERGE/verify.py'],
    'F36': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/COVERAGE/PANEL.md'],
    'F37': ['lead/next_re_20261117_r14/R14_COMMON.md'],
    'F38': ['lead/next_re_20261117_r14/R14_COMMON.md'],
    'F39': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/BOARD_ARCHIVE.md', 'lead/next_re_20261117_r14/HANDOFF_R14_R3.md'],
    'F40': ['lead/next_re_20261117_r14/R14_COMMON.md'],
    'F41': ['lead/next_re_20261117_r14/R14_COMMON.md'],
    'F42': ['lead/next_re_20261117_r14/R14_COMMON.md'],
    'F43': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/S13_K10/_audit/VERDICT.md'],
    'F44': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/S13_K10/_audit/VERDICT.md'],
    'F45': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/S13_K10/_audit/VERDICT.md'],
    'F46': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/S10_KPROVED/_audit/VERDICT.md', 'lead/next_re_20261117_r14/S13_K12/_audit/VERDICT.md'],
    'F47': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/S13_K12/_audit/VERDICT.md'],
    'F48': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/S10_KPROVED/_audit/VERDICT.md'],
    'F49': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/HANDOFF_R14_R3.md', 'lead/next_re_20261117_r14/R17_R52_ADJ_D4/VERDICT.md'],
    'F50': ['lead/next_re_20261117_r14/R17_R36_VERIFY_TABLEBASE/VERDICT.md', 'lead/next_re_20261117_r14/R17_R56_FACTINDEX_V53/lead_byte_checks.tsv'],
    'F51': ['lead/next_re_20261117_r14/R17_AUDIT_FI_V5/VERDICT.md', 'lead/GOAL_THREE_TARGETS_20261018.md'],
    'F52': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/NAMED_PUSH_AUDIT10/VERDICT.md'],
    'F53': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/R17_R56_FACTINDEX_V53/lead_byte_checks.tsv'],
    'F54': ['lead/next_re_20261117_r14/R14_COMMON.md', 'lead/next_re_20261117_r14/NAMED_PUSH_AUDIT15/VERDICT.md'],
    'F55': ['lead/next_re_20261117_r14/R14_COMMON.md', '_r188/r188d_resync.py', '_r188/r188d.log', '_r188/r188d.json', '_r188/r188c.log', '_r189/r189c_adjacency.py', '_r189/r189d_packing.py', '_r189/r189e_thunk_oob.py', '_r190/r190a_groups.py', '_r190/r190b_thunks.py', '_r190/r190c_rtti.py', '_r191/r191g_deliver.py', '_r191/r191d_td.py', '_r191/r191b_recheck.py'],
    'F56': ['lead/next_re_20261117_r14/R14_COMMON.md', '_r188/r188d_resync.py', '_r188/r188d.log', '_r186/r186d_audit_recheck.py', '_r186/r186d.log'],
}
EVIDB = {
    'F01': 183,
    'F02': 112,
    'F03': 116,
    'F04': 187,
    'F05': 139,
    'F06': 187,
    'F07': 187,
    'F08': 125,
    'F09': 300,
    'F10': 252,
    'F11': 124,
    'F12': 187,
    'F13': 250,
    'F14': 492,
    'F15': 181,
    'F16': 299,
    'F17': 61,
    'F18': 160,
    'F19': 431,
    'F20': 146,
    'F21': 119,
    'F22': 183,
    'F23': 118,
    'F24': 1719,
    'F25': 197,
    'F26': 81,
    'F27': 324,
    'F28': 256,
    'F29': 459,
    'F30': 111,
    'F31': 250,
    'F32': 130,
    'F33': 109,
    'F34': 154,
    'F35': 355,
    'F36': 118,
    'F37': 54,
    'F38': 61,
    'F39': 174,
    'F40': 54,
    'F41': 54,
    'F42': 88,
    'F43': 154,
    'F44': 151,
    'F45': 130,
    'F46': 238,
    'F47': 152,
    'F48': 123,
    'F49': 157,
    'F50': 130,
    'F51': 127,
    'F52': 196,
    'F53': 126,
    'F54': 145,
    'F55': 311,
    'F56': 122,
}
LOST = {
    'lead/next_re_20261117_r14/COVERAGE/PANEL.md': 8,
    'lead/next_re_20261117_r14/GATE_BEHAV/PROGRESS.md': 1,
    'lead/next_re_20261117_r14/HANDOFF_R14_R3.md': 2,
    'lead/next_re_20261117_r14/HANDOFF_R16.md': 1,
    'lead/next_re_20261117_r14/NAMED_PUSH_AUDIT10/VERDICT.md': 2,
    'lead/next_re_20261117_r14/R17_AUDIT_FI_V5/VERDICT.md': 1,
    'lead/next_re_20261117_r14/R17_AUDIT_R9/VERDICT.md': 1,
    'lead/next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md': 4,
    'lead/next_re_20261117_r14/R17_LEDGER_1062/SECTION.md': 5,
    'lead/next_re_20261117_r14/R17_LEDGER_1063/SECTION.md': 3,
    'lead/next_re_20261117_r14/R17_LEDGER_1063R/SECTION.md': 1,
    'lead/next_re_20261117_r14/R17_LEDGER_1064/SECTION.md': 5,
    'lead/next_re_20261117_r14/R17_LEDGER_1065/SECTION.md': 2,
    'lead/next_re_20261117_r14/S10_KPROVED/_audit/VERDICT.md': 2,
    'lead/next_re_20261117_r14/S13_K10/_audit/VERDICT.md': 3,
    'lead/next_re_20261117_r14/S13_K12/_audit/VERDICT.md': 2,
}
LOST_ITEMS = 43
LOST_UNIQ = 16
ITEMS = 197
UNIQ = 89
MASTER_SHA256 = '86874cbe556744085a13eb4d7ae7c1fd9bc0780a574f0aaf0ef8e4339ae86281'

fails = []
def F(m): fails.append(m)

def strip_note(s):
    s = s.strip()
    if s.endswith(')'):
        d = 0
        for i in range(len(s) - 1, -1, -1):
            if s[i] == ')': d += 1
            elif s[i] == '(':
                d -= 1
                if d == 0: return s[:i].strip()
    return s

def norm(p): return p.replace('\\', '/').strip()

def resolvable(p):
    for c in (p, 'lead/' + p, TIER + '/' + p):
        if os.path.exists(os.path.join(ROOT, c)): return True
    return False

def canon_g(d):   return '\n'.join("    '%s': '%s'," % (k, d[k]) for k in sorted(d))
def canon_f(d):   return '\n'.join("    '%s': (%d, %d)," % (k, d[k][0], d[k][1]) for k in sorted(d))
def canon_e(d):   return '\n'.join("    '%s': [%s]," % (k, ', '.join("'%s'" % x for x in d[k])) for k in sorted(d))
def canon_eb(d):  return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))
def canon_l(d):   return '\n'.join("    '%s': %d," % (k, d[k]) for k in sorted(d))

print('--- facts_floors.py (R160 v2) ---')
if not os.path.exists(CUR):
    print('  FAIL  D0 ledger not found: %s' % CUR); print('[exit 1]'); sys.exit(1)

raw = open(CUR, 'rb').read()
sha = hashlib.sha256(raw).hexdigest()

# ---- D0：v2 无论路径是否等于 EXPECT_CUR 都比 sha ----
if not IGNORE_PIN and sha != CUR_SHA256:
    F('D0 sha256 drifted: %s != pinned %s (file=%s; deliberate re-pin required)'
      % (sha[:16], CUR_SHA256[:16], os.path.basename(os.path.dirname(CUR))))
print('  D0 sha=%s pinned=%s %s' % (sha[:16], CUR_SHA256[:16],
                                   'skip(--ignore-pin)' if IGNORE_PIN else ''))

cr = raw.count(b'\r')
if cr: F('D1 CR bytes present: %d (must be LF-only)' % cr)
print('  D1 LF-only: CR=%d' % cr)
if cr:
    print('[exit 1] cannot parse safely'); sys.exit(1)

txt = io.open(CUR, encoding='utf-8', newline='').read()
rows = list(csv.reader(io.StringIO(txt), delimiter='\t'))
hdr, data = rows[0], rows[1:]

EXP = ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations']
if hdr != EXP: F('D2 header differs: %r' % (hdr,))
print('  D2 header: %s' % ('ok' if hdr == EXP else 'MISMATCH'))

if len(data) != 56: F('D3 data rows = %d != 56' % len(data))
bad = [i for i, r in enumerate(data) if len(r) != 5]
if bad: F('D3 rows with !=5 cols at %r' % bad[:8])
print('  D3 rows=%d all-5-col=%s' % (len(data), 'yes' if not bad else 'NO'))

ids = [r[0] for r in data]
exp_ids = ['F%02d' % i for i in range(1, 57)]
if ids != exp_ids:
    F('D4 fact_id sequence broke at %r'
      % next((('idx%d %s!=%s' % (i, a, b)) for i, (a, b) in enumerate(zip(ids, exp_ids)) if a != b), 'length'))
print('  D4 fact_id F01..F56: %s' % ('ok' if ids == exp_ids else 'BROKEN'))

# ---- D5 v2：逐 fid 钉 grade ----
g_now = {r[0]: r[2] for r in data}
g_diff = [(k, GRADES[k], g_now.get(k)) for k in sorted(GRADES) if g_now.get(k) != GRADES[k]]
if g_diff: F('D5 per-fact grade changed: %r' % g_diff[:6])
print('  D5 per-fact grade: %d facts, %d changed' % (len(GRADES), len(g_diff)))

# ---- D6 v2：不许缩 ----
sh_ = []
for r in data:
    fid = r[0]
    if fid not in FLOORS: continue
    fs, fl = FLOORS[fid]
    s, l = len(r[1].encode()), len(r[4].encode())
    if s < fs: sh_.append('%s.stmt %d<%d' % (fid, s, fs))
    if l < fl: sh_.append('%s.lim %d<%d' % (fid, l, fl))
if sh_: F('D6 per-fact bytes SHRANK (growth is allowed, shrinkage is not): %s' % sh_[:10])
print('  D6 per-fact no-shrink: %d facts, %d breaches' % (len(FLOORS), len(sh_)))

# ---- D7 v2：逐 fid 证据清单 + 第4列字节不许缩 ----
items = []
ed = []
for r in data:
    fid = r[0]
    if fid not in EVID: continue
    cur = [norm(strip_note(x)) for x in r[3].split(';') if x.strip()]
    if cur != EVID[fid]:
        only_new = [x for x in cur if x not in EVID[fid]]
        only_gone = [x for x in EVID[fid] if x not in cur]
        ed.append('%s (+%r -%r)' % (fid, only_new[:3], only_gone[:3]))
    if len(r[3].encode()) < EVIDB[fid]:
        ed.append('%s col4 %dB<%dB' % (fid, len(r[3].encode()), EVIDB[fid]))
    items.extend((fid, p) for p in cur)
if ed: F('D7 per-fact evidence list/bytes changed: %s' % ed[:8])
uniq = set(p for _, p in items)
lost = [p for _, p in items if not resolvable(p)]
lostc = Counter(lost)
if len(items) != ITEMS: F('D7 evidence items = %d != %d' % (len(items), ITEMS))
if len(uniq) != UNIQ: F('D7 distinct paths = %d != %d' % (len(uniq), UNIQ))
if len(lost) != LOST_ITEMS: F('D7 lost items = %d != %d' % (len(lost), LOST_ITEMS))
if dict(lostc) != LOST:
    F('D7 lost multiset changed: new=%r gone=%r'
      % (sorted(set(lostc) - set(LOST))[:5], sorted(set(LOST) - set(lostc))[:5]))
print('  D7 evidence: items=%d uniq=%d lost_items=%d lost_uniq=%d per-fact-changes=%d'
      % (len(items), len(uniq), len(lost), len(lostc), len(ed)))

# ---- D8 v2：总字节不许缩 ----
if len(raw) < TOTAL_BYTES:
    F('D8 total bytes SHRANK: %d < %d (lost >= %d B)'
      % (len(raw), TOTAL_BYTES, TOTAL_BYTES - len(raw)))
print('  D8 total bytes: %d (no-shrink floor %d)' % (len(raw), TOTAL_BYTES))

# ---- D9 v2：单一主指纹覆盖全部常量 ----
_master = hashlib.sha256(('\n'.join([CUR_SHA256, str(TOTAL_BYTES), canon_g(GRADES), canon_f(FLOORS),
                                      canon_e(EVID), canon_eb(EVIDB), canon_l(LOST),
                                      str(ITEMS), str(UNIQ), str(LOST_ITEMS), str(LOST_UNIQ)])).encode()).hexdigest()
if not IGNORE_PIN and _master != MASTER_SHA256:
    # R180 修正（审计 #429 的 D1/D2，主会话 r180f 复算成立）：原文只打前 16 位且 FAIL
    # 消息完全不含 sha ⇒ 末位被改的漂移在日志里与基线逐字相同。此处补全文。
    F('D9 MASTER pin drifted: recomputed %s != pinned %s (constants were edited together with data)'
      % (_master, MASTER_SHA256))
print('  D9 master pin: %s (pinned %s)' % (_master, MASTER_SHA256))

# ---- D10 [R180 新增] 当前版指针必须与 CUR 常量/实物一致 ----
# 存在理由（实测，连续 8 轮登记未闭合）：D0/D9 只钉 CUR 指向的那份文件；
# FACT_INDEX_CURRENT.md 承载「哪一份是当前版」的声明，却在 check_disc / gate_runner /
# 本脚本三者中读取次数各 0（_r180/r180a A 段实测）⇒ 指针静默漂移时三门全绿。
# 判据是两条**独立**事实的相等，不是文本相似：
#   (A) 指针声明的 sha256 == CUR 这份文件**现盘实测** sha256（声明 vs 实物）
#   (B) 指针声明的字节数 == 本文件 TOTAL_BYTES（规模声明 vs 规模常量）
# 另有第三条 (C) 指针 sha256 == 本文件 CUR_SHA256，但它**不独立**：D0 已保证
#   sha(CUR) == CUR_SHA256，故 (A) 绿 + D0 绿 ⇒ (C) 必绿，三者同真同假。
#   R180 审计 #429 的 B4 指出卡面写「三条相等」夸大了独立性，主会话 r180f 复算成立，
#   此处按源码口径订正为「两条独立 + 一条连带」，判定逻辑不变（多留一条是防御性冗余）。
# 任一条不等即 FAIL。文件缺失同样 FAIL（不得因读不到就跳过而假通过）。
PTR_FILE = os.path.join(TIER, 'FACT_INDEX_CURRENT.md')
print('  D10 pointer file: %s' % ('present' if os.path.exists(PTR_FILE) else 'MISSING'))
if not os.path.exists(PTR_FILE):
    F('D10 pointer file missing: %s' % PTR_FILE)
else:
    _pt = io.open(PTR_FILE, encoding='utf-8', newline='').read()
    _ms = re.search(r'\| sha256 \| ([0-9a-f]{64}) \|', _pt)
    _mb = re.search(r'\| 字节数 \| (\d+) \|', _pt)
    if not _ms or not _mb:
        F('D10 pointer fields unparseable (sha256_found=%r bytes_found=%r)' % (bool(_ms), bool(_mb)))
    else:
        _ps, _pb = _ms.group(1), int(_mb.group(1))
        _ds = hashlib.sha256(open(CUR, 'rb').read()).hexdigest()
        # 打印与 FAIL 消息一律用**全文** sha：R180 自测发现只打前 16 位时，
        # 末位被改的漂移在日志里与基线逐字相同（判据仍会 FAIL，但事后无法从日志分辨）。
        if not IGNORE_PIN and _ps != CUR_SHA256:
            F('D10 pointer sha %s != CUR_SHA256 %s (pointer names a different version)'
              % (_ps, CUR_SHA256))
        if not IGNORE_PIN and _pb != TOTAL_BYTES:
            F('D10 pointer bytes %d != TOTAL_BYTES %d' % (_pb, TOTAL_BYTES))
        if not IGNORE_PIN and _ps != _ds:
            F('D10 pointer sha %s != on-disk sha of CUR %s (declared version is not this file)'
              % (_ps, _ds))
        print('  D10 pointer sha=%s bytes=%d vs CUR %s/%d (on-disk %s)'
              % (_ps, _pb, CUR_SHA256, TOTAL_BYTES, _ds))

if fails:
    for m in fails: print('  FAIL  ' + m)
    print('[exit 1] %d FAIL' % len(fails)); sys.exit(1)
print('  PASS  structure/scale/ownership/evidence-chain all ok')
print('  BOUNDARY: pins STRUCTURE and SCALE, not truth; and a same-edit of data+constants')
print('            would still pass (common ceiling of all digest-based gates).')
print('[exit 0]'); sys.exit(0)
