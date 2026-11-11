#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_gen_csv.py — 生成 lead/re_round_disposition_20261111/DISPOSITION.csv

运行方式：
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/re_round_disposition_20261111/_gen_csv.py
"""

import sys
sys.dont_write_bytecode = True

import os
import csv
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENUM_JSON = os.path.join(BASE_DIR, "_enum_out.json")
CSV_PATH = os.path.join(BASE_DIR, "DISPOSITION.csv")

specials = {
  'const_exit_fix_20261110': {
    '判定': '补做',
    '理由': '缺统一测试日志落盘与交付验收报告；需输入 18 个补丁脚本的母本路径映射进行批量回归验证',
    '证据': 'lead/const_exit_fix_20261110/patched/VERIFY_A8.py:L824',
    '建议批次': '第三批'
  },
  'crit_fix_20261110': {
    '判定': '废弃',
    '理由': '系 E3 判据首轮尝试修补，已被 e3_fix2_20261110 修正并最终被 e3_unify_20261111 统一判定器取代',
    '证据': 'lead/e3_unify_20261111/_e3_v3.py:L7',
    '建议批次': '不适用（废弃）'
  },
  'dup_audit_20261110': {
    '判定': '入账',
    '理由': '完成 lead/ 下 2928 个 py 脚本物理哈希全量普查，锁定 72 组重复代码（13 补丁副本、2 评审副本、57 良性重复）',
    '证据': 'lead/dup_audit_20261110/_da_summary.txt:L2-L8',
    '建议批次': '第二批（补写 md 报告）'
  },
  'e3_fix2_20261110': {
    '判定': '废弃',
    '理由': '系 E3 第二轮过渡补丁，虽有对照数据，但已被 11-11 的第三版统一判定器 _e3_v3.py 全盘吸收',
    '证据': 'lead/e3_unify_20261111/_e3_v3.py:L7-L10',
    '建议批次': '不适用（废弃）'
  },
  'e3_secondimpl_20261110': {
    '判定': '废弃',
    '理由': 'E3 独立第二实现脚本，作为对照组实验已被 e3_unify_20261111 的统一版本吸收',
    '证据': 'lead/e3_unify_20261111/_e3_v3.py:L2-L8',
    '建议批次': '不适用（废弃）'
  },
  'e3_unify_20261111': {
    '判定': '补做',
    '理由': '统一 E3 判定器核心逻辑已就绪，但缺对全量 413 脚本的批跑扫描输出及最终验收报告；需输入全量脚本清单',
    '证据': 'lead/e3_unify_20261111/_e3_v3.py:L2-L15',
    '建议批次': '第二批'
  },
  'esi_caller_trace_20261111': {
    '判定': '废弃',
    '理由': 'slot2 调用点首轮线性扫描，存在 capstone 在 0x6F59D 截断风险，已被 100% 分块续扫且结论更严密的 slot2_fullscan_20261111 取代',
    '证据': 'lead/slot2_fullscan_20261111/_sf_scan.py:L11-L15',
    '建议批次': '不适用（废弃）'
  },
  'exit_lint_20261110': {
    '判定': '补做',
    '理由': '工具脚本；所调用的底座判据源存在过时逻辑，缺对接新版 _e3_v3.py 的改造与自身自测通过报告',
    '证据': 'lead/exit_lint_20261110/_el_lint.py:L8-L12',
    '建议批次': '第三批'
  },
  'gate_exit_retrofit_20261110': {
    '判定': '补做',
    '理由': '模板对照件虽已验证（EXIT 0/1 正确），但 patched/ 下 24 个改造脚本缺统一回归跑测产物与交付报告；需输入测试集运行验证',
    '证据': 'lead/gate_exit_retrofit_20261110/_gr_template_ctl_run.txt:L37-L39',
    '建议批次': '第三批'
  },
  'ledger_exit_census_20261110': {
    '判定': '入账',
    '理由': '完成三本台账中硬编码 EXIT=0 出现的 76 处精确位置普查（31/1/44 分布）与 413 个脚本分类对齐',
    '证据': 'lead/ledger_exit_census_20261110/_lc_out.txt:L8-L15',
    '建议批次': '第一批（补写 md 报告）'
  },
  'ok_falsify_20261110': {
    '判定': '入账',
    '理由': '完成 413 件全量脚本的分类与判定三维交叉统计（锁定 91 个门禁与 18 个未定类待修项），形成详尽 JSON 产物',
    '证据': 'lead/ok_falsify_20261110/_of_scope_out.json:L3390-L3430',
    '建议批次': '第二批（补写 md 报告）'
  },
  'playerctrl_semantics_20261111': {
    '判定': '入账',
    '理由': '静态反汇编证毕两大核心事实：HouseClass 实例严格由地图 [Houses] 节条目数决定无 PlayerControl 门控；PercentBuilt 写入后引擎零读取',
    '证据': 'lead/playerctrl_semantics_20261111/_ps_disasm_out.txt:L492-L495, L636-L642, L899-L900',
    '建议批次': '第一批（补写 md 报告）'
  },
  're_crashwriter_static_20261110': {
    '判定': '入账',
    '理由': '静态还原 0x0054A56E 数据依赖链，推翻台账「语义正常」结论（证得正常态不可达），并证得 0x0084F2BA 落在 .data 属 DEP 取指违规',
    '证据': 'lead/re_crashwriter_static_20261110/_cw_disasm_out.txt:L80-L105',
    '建议批次': '第一批（补写 md 报告）'
  },
  're_loadbench_diff_20261110': {
    '判定': '入账',
    '理由': '逐维比对澄清 LoadBench U0400 大版(92KB)与小版(25KB)不是同一张图；澄清台账所指 1680 实载图实为 222KB 变体件以 XMP29U2.MAP 载入',
    '证据': 'lead/re_loadbench_diff_20261110/_ld_diff_out.txt:L98-L103',
    '建议批次': '第一批（补写 md 报告）'
  },
  're_map_preset_decode_20261110': {
    '判定': '入账',
    '理由': '逐槽位还原三份地图预置单位，实测证明 XMP29U2.MAP 含 3360/2240 单位，在盘 yrm 含 240/160，彻底证伪两份 yrm 含 1680 单位的声称',
    '证据': 'lead/re_map_preset_decode_20261110/_md_parse_out.txt:L140-L167',
    '建议批次': '第一批（补写 md 报告）'
  },
  're_orphan_owners_20261110': {
    '判定': '入账',
    '理由': '证实 MaxPlayer=2 与 14 owner 在文件层不冲突，澄清地图声明与引擎运行期 meta_count=4 的差异',
    '证据': 'lead/re_orphan_owners_20261110/_oo_map_out.txt:L130-L151',
    '建议批次': '第一批（补写 md 报告）'
  },
  'slot2_fullscan_20261111': {
    '判定': '入账',
    '理由': '在 100% 分块覆盖与字节级普查下证得全 .text 1714 个 slot2 调用点中，可能派发至 0x54A4F0/0x54A630 的仅 0x546069 一处',
    '证据': 'lead/slot2_fullscan_20261111/_sf_scan_out.txt:L1830-L1834',
    '建议批次': '第一批（补写 md 报告）'
  },
  'unknown_locate_20261110': {
    '判定': '入账',
    '理由': '查清 263 个无出口脚本中以 sys.stdout.write/buffer.write 为唯一通道的 11 件目标（9 个 UNKNOWN、2 个 ARTIFACT）',
    '证据': 'lead/unknown_locate_20261110/_ul_stdout_census_out.txt:L22-L37',
    '建议批次': '第一批（补写 md 报告）'
  },
  'backlog_sweep_20261110': {
    '判定': '废弃',
    '理由': '已启动未落盘。积压清理工作已被 re_progress_check_20261111 及决策台账吸收，目录已无存留必要',
    '证据': 'lead/re_progress_check_20261111/RE_PROGRESS_20261111.md:§1',
    '建议批次': '第三批（归档清理）'
  },
  'crit_recheck_20261110': {
    '判定': '废弃',
    '理由': '已启动未落盘。判据复验工作已在 crit_fix_20261110 与 e3_fix2_20261110 落地，并由 e3_unify_20261111 统一吸收',
    '证据': 'lead/e3_unify_20261111/_e3_v3.py:L7',
    '建议批次': '第三批（归档清理）'
  },
  'e3_rootcause_20261110': {
    '判定': '废弃',
    '理由': '已启动未落盘。E3 吞没根因分析已直接在 e3_unify_20261111/_e3_v3.py 中沉淀为 7 条缺陷根因与修复规则',
    '证据': 'lead/e3_unify_20261111/_e3_v3.py:L7-L35',
    '建议批次': '第三批（归档清理）'
  },
  'e3_triage_20261110': {
    '判定': '废弃',
    '理由': '已启动未落盘。失败分流工作已由 ok_falsify_20261110 的 413 脚本三维交叉普查完全实现',
    '证据': 'lead/ok_falsify_20261110/_of_scope_out.json:L3390',
    '建议批次': '第三批（归档清理）'
  },
  'housecount_trace_20261111': {
    '判定': '废弃',
    '理由': '已启动未落盘。原拟跟踪 HouseClass 实例创建数量与条件，实际已在同日轮次 playerctrl_semantics_20261111 中静态反汇编闭环交付',
    '证据': 'lead/playerctrl_semantics_20261111/_ps_disasm_out.txt:L636-L642',
    '建议批次': '第三批（归档清理）'
  },
  'ledger_apply_prep_20261110': {
    '判定': '补做',
    '理由': '关键并账阻塞项。缺并账校验与执行脚本；需输入 lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md（§605–§609）安全并入主台账',
    '证据': 'lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md:L126',
    '建议批次': '第二批（P1 优先补做）'
  },
  'ledger_num_audit_20261111': {
    '判定': '废弃',
    '理由': '已启动未落盘。台账编号核验已在 re_progress_xverify_20261111/VERDICT.md 中实跑闭环，并账前审计已并入 ledger_apply_prep',
    '证据': 'lead/re_progress_xverify_20261111/VERDICT.md:§1 命题1&3',
    '建议批次': '第三批（归档清理）'
  },
  'mapfile_1680_hunt_20261111': {
    '判定': '废弃',
    '理由': '已启动未落盘。1680 预置单位地图寻源已在前一日轮次 re_loadbench_diff_20261110 彻底查清，本空目录系重复立项',
    '证据': 'lead/re_loadbench_diff_20261110/_ld_diff_out.txt:L101',
    '建议批次': '第三批（归档清理）'
  },
  're_chain_semantics_20261110': {
    '判定': '废弃',
    '理由': '已启动未落盘。崩溃写入点数据依赖链还原已由 re_crashwriter_static_20261110 全量交付',
    '证据': 'lead/re_crashwriter_static_20261110/_cw_disasm_out.txt:L80-L105',
    '建议批次': '第三批（归档清理）'
  },
  're_line_collapse_20261111': {
    '判定': '废弃',
    '理由': '已启动未落盘。轮次收敛与处置工作已被任务 D 写域（lead/re_round_disposition_20261111）全盘接管并实现',
    '证据': 'lead/re_dispatch_20261111/BRIEF_D.md:L1',
    '建议批次': '第三批（归档清理）'
  },
  'recon_20261110': {
    '判定': '废弃',
    '理由': '已启动未落盘。静态侦察已细化分流为 re_crashwriter_static、re_loadbench_diff、re_map_preset_decode、re_orphan_owners 四个具体轮次实施',
    '证据': 'lead/re_crashwriter_static_20261110/_cw_disasm.py:L1',
    '建议批次': '第三批（归档清理）'
  }
}

def main():
    with open(ENUM_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    directories = data["directories"]
    rows = []

    for d in sorted(directories.keys()):
        info = directories[d]
        dt = info["date"]
        cls_code = info["cls"]

        if cls_code == "EMPTY":
            cls_name = "完全空目录"
        elif cls_code == "PROBE_ONLY":
            cls_name = "仅探针无报告"
        else:
            cls_name = "有 md 报告"

        if d in specials:
            sp = specials[d]
            judgment = sp["判定"]
            reason = sp["理由"]
            evidence = sp["证据"]
            batch = sp["建议批次"]
        else:
            judgment = "入账"
            reason = "已交付闭环 Markdown 结论报告"
            md_name = info["md_files"][0] if info["md_files"] else "README.md"
            evidence = f"lead/{d}/{md_name}:L1"
            batch = "已交付"

        rows.append({
            "目录名": d,
            "日期": dt,
            "类别": cls_name,
            "判定": judgment,
            "理由": reason,
            "证据": evidence,
            "建议批次": batch,
        })

    fieldnames = ["目录名", "日期", "类别", "判定", "理由", "证据", "建议批次"]
    with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] DISPOSITION.csv 写入成功: {CSV_PATH} (共 {len(rows)} 行)")

if __name__ == "__main__":
    main()
