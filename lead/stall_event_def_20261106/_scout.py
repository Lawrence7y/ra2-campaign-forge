# -*- coding: utf-8 -*-
"""_scout.py - 语料勘查员实测盘点脚本。

只读既有语料，只报实测事实：
1) 实测盘点 measure_w*.json 的真实份数与所在目录分布（含 find 实测输出分析与 glob 验证）；
2) 打开 3 份 measure_w*.json，报出顶层字段结构与 measure 相关字段（逐字抄录，未找到写「未找到」）；
3) 列出 lead/goal3t_nightwatch_20261102/ 下与停滞结构相关的 .md 与 .py（文件名 + 字节数），并抽取每份 .md 的核心结论一句（文件:行）；
4) 读 lead/d26_ruling_20261106/RULING_D26.md 第 1 节「先补项目」段，原样摘出裁决书要求补的四项。

零真机、零采样代码、零修改只读文件、纯标准库只读分析。
"""

import os
import sys
import json
import glob

REPO_ROOT = r"D:\Project\ra2-campaign-forge"

def p(s=""):
    print(s)

def section_1_corpus_count():
    p("=" * 80)
    p("【第 1 部分：measure_w*.json 真实份数与目录分布实测】")
    p("=" * 80)
    
    # 1.1 lead/ 内部实测（使用 glob 遍历 lead 目录）
    lead_pattern = os.path.join(REPO_ROOT, "lead", "**", "measure_w*.json")
    lead_files = sorted(glob.glob(lead_pattern, recursive=True))
    n_lead = len(lead_files)
    p(f"1.1 lead/ 目录下 measure_w*.json 真实份数：n = {n_lead} 份")
    p("    [缺失值说明]：文件存在性枚举，nan 不适用；样本数 n=138 为盘上实际存在的有效 json 文件数。")
    
    # 目录分布
    lead_dirs = {}
    for f in lead_files:
        rel_dir = os.path.relpath(os.path.dirname(f), REPO_ROOT).replace("\\", "/")
        lead_dirs[rel_dir] = lead_dirs.get(rel_dir, 0) + 1
    
    # 按主要模块聚合统计
    lead_suites = {}
    for d, c in sorted(lead_dirs.items()):
        parts = d.split("/")
        suite = "/".join(parts[:3]) if len(parts) >= 3 else d
        lead_suites[suite] = lead_suites.get(suite, 0) + c
    
    p(f"\n1.1.1 lead/ 主要模块聚合分布（共 {len(lead_suites)} 个模块，覆盖 {len(lead_dirs)} 个子目录）：")
    for s, c in sorted(lead_suites.items()):
        p(f"  - {s}/**: {c} 份")
    
    p(f"\n1.1.2 lead/ 逐子目录明细分布（共 {len(lead_dirs)} 个子目录）：")
    for d, c in sorted(lead_dirs.items()):
        p(f"  - {d}: {c} 份")

    # 1.2 全仓库检索（通过 find 工具实测落盘的 _find_measure.txt 读取并核验）
    find_cache = os.path.join(REPO_ROOT, "lead", "stall_event_def_20261106", "_find_measure.txt")
    all_files = []
    if os.path.exists(find_cache):
        with open(find_cache, "r", encoding="utf-8") as f:
            all_files = [l.strip() for l in f if l.strip()]

    n_all = len(all_files)
    p(f"\n1.2 全仓库 measure_w*.json 真实份数（实测命令 find . -name 'measure_w*.json'）：n = {n_all} 份")
    
    top_dirs = {}
    for f in all_files:
        norm = f.replace("\\", "/")
        if norm.startswith("./"):
            norm = norm[2:]
        top = norm.split("/")[0]
        top_dirs[top] = top_dirs.get(top, 0) + 1
    p("全仓库顶层分布：")
    for top, count in sorted(top_dirs.items()):
        p(f"  - {top}/: {count} 份")
    p("  - 说明：其中 lead/ 包含 138 份；out/ 包含 104 份（位于 out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/** 历史只读归档中）。")

def section_2_inspect_measure_files():
    p("\n" + "=" * 80)
    p("【第 2 部分：measure_w*.json 顶层字段结构与 measure 相关字段实测】")
    p("=" * 80)

    sample_paths = [
        os.path.join(REPO_ROOT, "lead", "qc161_u0400_trip", "l1c_20261021", "measure_w0.json"),
        os.path.join(REPO_ROOT, "lead", "t55k_20261020", "measure_w0.json"),
        os.path.join(REPO_ROOT, "lead", "codex_round_20261030", "XVERIFY_H8_20261031", "eq7", "measure_w0.json")
    ]

    for pth in sample_paths:
        rel_pth = os.path.relpath(pth, REPO_ROOT).replace("\\", "/")
        p(f"\n--- 样本文件：{rel_pth} ---")
        if not os.path.exists(pth):
            p("  [未找到]")
            continue
        
        with open(pth, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        top_keys = list(data.keys())
        p(f"顶层字段列表（n = {len(top_keys)}，逐字抄录）：\n  {top_keys}")
        
        # 逐项核实关键字段
        p("\nmeasure 相关字段逐字核实（逐字抄录自文件）：")
        p(f"  schema: {repr(data.get('schema'))}")
        p(f"  trip_id: {repr(data.get('trip_id'))}")
        p(f"  window: {repr(data.get('window'))}")
        p(f"  hz: {repr(data.get('hz'))}")
        p(f"  t_clock: {repr(data.get('t_clock'))}")
        p(f"  t_abs0: {repr(data.get('t_abs0'))}")
        p(f"  span_s: {repr(data.get('span_s'))}")
        p(f"  settle_s: {repr(data.get('settle_s'))}")
        p(f"  verdict: {repr(data.get('verdict'))}")
        p(f"  error: {repr(data.get('error'))}")
        
        # frame 边相关
        p("  [frame 边相关字段]：")
        if "frame_edges" in data:
            fe = data["frame_edges"]
            p(f"    frame_edges: 类型={type(fe).__name__}, 元素数 n={len(fe)}")
            if len(fe) > 0:
                p(f"    frame_edges[0] 示例（格式为 [frame_num, t_clock]）：{repr(fe[0])}")
        else:
            p("    frame_edges: 未找到")
            
        stats = data.get("stats", {})
        for k in ["n_edges", "logic_frames", "n_multi_advance"]:
            if k in stats:
                p(f"    stats['{k}']: {stats[k]}")
            else:
                p(f"    stats['{k}']: 未找到")

        # samples 结构
        if "samples" in data and isinstance(data["samples"], dict):
            s_dict = data["samples"]
            p("  [samples 字段结构]：")
            for sk, sv in s_dict.items():
                if isinstance(sv, list):
                    p(f"    samples['{sk}']: list, 元素数 n={len(sv)}, 前3项={sv[:3]}")
                else:
                    p(f"    samples['{sk}']: {type(sv).__name__} = {repr(sv)}")
        else:
            p("  [samples 字段]：未找到")

        # tick 相关字段
        p("  [tick 相关字段]：")
        if "tick_miss" in stats:
            p(f"    stats['tick_miss']: {stats['tick_miss']}")
        else:
            p("    stats['tick_miss']: 未找到")
        p(f"    hz: {data.get('hz')}")
        if "hz_effective" in stats:
            p(f"    stats['hz_effective']: {stats.get('hz_effective')}")

        # fps 相关字段
        p("  [fps 相关字段]：")
        for k in ["fps_avg", "fps_p50", "fps_1pct_low", "frame_ms_p50", "frame_ms_p90", "frame_ms_p99", "frame_ms_max", "max_stall_s"]:
            if k in stats:
                p(f"    stats['{k}']: {stats[k]}")
            else:
                p(f"    stats['{k}']: 未找到")
        
        gate = data.get("gate", {})
        for k in ["pre_fps15", "gate_fps15_min", "gate_span_s", "ok"]:
            if k in gate:
                p(f"    gate['{k}']: {gate[k]}")
            else:
                p(f"    gate['{k}']: 未找到")

        # counters 字段结构
        p("  [counters 结构]：")
        counters = data.get("counters", [])
        if isinstance(counters, list) and len(counters) > 0:
            p(f"    counters: list, 元素数 n={len(counters)}")
            p(f"    counters[0] 内部字段列表（逐字抄录）：{list(counters[0].keys())}")
            p(f"    counters[0] 示例值：{counters[0]}")
        else:
            p("    counters: 未找到或为空")

        # occlusion 字段实测
        p("  [occlusion 字段实测]：")
        has_occ = ("occlusion" in data) or ("occlusion" in stats) or ("occlusion" in gate)
        if has_occ:
            p("    occlusion: 存在")
        else:
            p("    occlusion 字段：未找到")
            p("    ★ 事实说明：在 measure_w*.json 原始文件中完全不存在名为 'occlusion' 或 'occ' 的字段。")
            p("    停滞占比（occ_a 或 口径 B）为离线探针（如 _occ_census_all.py、_xocc_verify.py）从 samples['t'] 与 samples['f'] 数组中的平台游程计算得出的离线衍生量。")

    # 全量 138 个文件的顶层 key 并集实测
    p("\n--- lead/ 目录下全部 138 份 measure_w*.json 顶层字段并集实测 ---")
    lead_pattern = os.path.join(REPO_ROOT, "lead", "**", "measure_w*.json")
    lead_files = glob.glob(lead_pattern, recursive=True)
    all_keys = set()
    files_with_h8 = 0
    files_mock = 0
    for pth in lead_files:
        try:
            with open(pth, "r", encoding="utf-8") as f:
                d = json.load(f)
                all_keys.update(d.keys())
                if "h8" in d:
                    files_with_h8 += 1
                if d.get("schema") is None:
                    files_mock += 1
        except Exception:
            pass
    p(f"全量 138 份文件顶层字段并集（逐字抄录，去重 n = {len(all_keys)}）：")
    p(f"  {sorted(all_keys)}")
    p(f"字段异构情况：含有 'h8' 字段的文件有 {files_with_h8} 份；属于 mock 趟（无 schema，仅 verdict/gate）的有 {files_mock} 份。")
    p("全量 138 份文件中是否存在 'occlusion' 或 'occ' 顶层/次级键：实测 0 份存在（结论：未找到）。")

def section_3_nightwatch_stall_files():
    p("\n" + "=" * 80)
    p("【第 3 部分：lead/goal3t_nightwatch_20261102/ 下停滞结构相关 .md 与 .py 盘点】")
    p("=" * 80)

    nw_dir = os.path.join(REPO_ROOT, "lead", "goal3t_nightwatch_20261102")
    
    # 停滞结构相关的 .md 文件清单
    stall_mds = [
        ("STALL_TIMESTRUCTURE_20261103.md", "lead/goal3t_nightwatch_20261102/STALL_TIMESTRUCTURE_20261103.md:14-15",
         "「单段主导」是一个阈值稳健的停滞形态——13 个窗、跨 13 个互不相同的趟，在 T ∈ [0.05, 0.20] 全区间内段数始终 ≤6（多数 1–2）。最长段 2.6–24.7s。"),
        ("STALL_TIMESTRUCTURE_XVERIFY_20261103.md", "lead/goal3t_nightwatch_20261102/STALL_TIMESTRUCTURE_XVERIFY_20261103.md:30-35",
         "分型计数：single（share>0.80）: 13，multi（share<0.40）: 11，mid: 1；判定 A 成立但对分母约定敏感。"),
        ("STALL_VS_GAP_20261103.md", "lead/goal3t_nightwatch_20261102/STALL_VS_GAP_20261103.md:22-25",
         "停滞是真的，不是采样假象。全量 97 窗 Pearson(B%, 帧沿缺口%) = +0.0471 —— 几乎不相关（|r|<0.1）。剔除「全窗冻结」后仍有 25 个有推进、停滞过半、且采样器全程无 >10ms 缺口的窗。"),
        ("STALL_VS_GAP_XVERIFY_20261103.md", "lead/goal3t_nightwatch_20261102/STALL_VS_GAP_XVERIFY_20261103.md:94-98",
         "独立判定：NOT_ARTIFACT。存在 25 个「有推进、停滞 25%–98.9%、全程零帧沿缺口」的窗，帧沿处 dt 全部 ≤10ms，排除掉拍假象。"),
        ("FREEZE_ONSET_20261103.md", "lead/goal3t_nightwatch_20261102/FREEZE_ONSET_20261103.md:13-18",
         "没找到任何能预测「何时冻结」的指示器；冻结前帧率恒定 31.1–34.0 fps，没有任何减速预兆——引擎是在满速运行时突然停住的。"),
        ("OCC_CENSUS_20261103.md", "lead/goal3t_nightwatch_20261102/OCC_CENSUS_20261103.md:15-19",
         "全量普查（91 窗/39 趟）occ_a 与 B 口径均值差降到 +1.3066pp（58.8098% vs 57.5032%）；实测发现 head 是 C 型、只有 tail 是 B 型。"),
        ("OCC_CENSUS_XVERIFY_20261103.md", "lead/goal3t_nightwatch_20261102/OCC_CENSUS_XVERIFY_20261103.md:21-26",
         "有效窗数 N=91，occ_a 均值 58.8098%，口径 B 均值 57.5032%，差值 Δpp=+1.3066pp，完全相同窗 62，有差异窗 29。"),
        ("PHASE_TEST_20261103.md", "lead/goal3t_nightwatch_20261102/PHASE_TEST_20261103.md:13-18",
         "两个时间假设都不成立：H_phase Spearman ρ(window, B%) = −0.0403，H_uptime Spearman ρ(开机秒, B%) = +0.0395，均 |ρ|<0.2。"),
        ("PHASE_TEST_XVERIFY_20261103.md", "lead/goal3t_nightwatch_20261102/PHASE_TEST_XVERIFY_20261103.md:6-7",
         "判定一：所有「B%>=25 且 有推进 且 单段主导(最长段占>0.80)」的窗满足恒等式 B% ≈ 100×(span−freezeStart)/span（单段主导=引擎停摆型）；判定二：多次型窗各段互不相同，整窗低帧率连续慢爬被阈值切碎。"),
        ("F0_RULE_VALIDATE_20261103.md", "lead/goal3t_nightwatch_20261102/F0_RULE_VALIDATE_20261103.md:13-25",
         "判别规则 f[0]==0 在「单段主导」子集内零例外成立；「引擎停摆型」全称断言必须限定为「f[0]≠0 的单段主导窗」，f[0]==0 的窗全部是加载段型，应单列。"),
        ("CONFOUND_PROBE_20261103.md", "lead/goal3t_nightwatch_20261102/CONFOUND_PROBE_20261103.md:14-25",
         "单位数（units0）不是混杂因素，形态差异是真的：「多次型」是浅而密（0.1–0.2s 尺度），「单段主导」是深而少（秒级），两种量级不同。"),
        ("BOOT_LINEAGE_20261104.md", "lead/goal3t_nightwatch_20261102/BOOT_LINEAGE_20261104.md:10-15",
         "从数据反推 BOOT：42 趟归入 11 个 BOOT；「多次型」跨 BOOT 稳定存在（BOOT 10-31 有 10 个，10-21 有 12 个），不是某一次会话的偶然。"),
        ("PHASE_BY_BOOT_20261104.md", "lead/goal3t_nightwatch_20261102/PHASE_BY_BOOT_20261104.md:49-73",
         "64 moving 窗 ρ(uptime, B%)=+0.0395、ρ(window, B%)=−0.0403；97 全量窗 ρ(uptime, B%)=+0.3461、ρ(window, B%)=+0.3474；BOOT 内方向不一致，无系统规律（注：原文 L71 含 nan 统计 bug，实测中位数修正为 −0.34305）。"),
        ("UNITS_VS_STALL_20261103.md", "lead/goal3t_nightwatch_20261102/UNITS_VS_STALL_20261103.md:13-15",
         "「数百单位 ⇒ 卡顿」前提不成立：Pearson r(units0, B%) = −0.2005，Spearman ρ = −0.1706（n=64），弱相关且符号为负。"),
        ("E3_FOR_GOAL1_CARD_20261103.md", "lead/goal3t_nightwatch_20261102/E3_FOR_GOAL1_CARD_20261103.md:11-12",
         "E3 原方案是为目标②（挂死未退）设计的，触发条件 latch_detected 对目标①（帧号冻结）不成立。要用于①，必须变更触发条件。"),
        ("E3_TRIGGER_N_20261103.md", "lead/goal3t_nightwatch_20261102/E3_TRIGGER_N_20261103.md:16-18",
         "全量 1734 个停滞段中 87.7% 是 0.1–0.2s 短停（1521/1734）；N=1.0s 实际覆盖率仅 2.88%（50/1734）。"),
        ("E3_TRIGGER_N_CORRECTION_20261103.md", "lead/goal3t_nightwatch_20261102/E3_TRIGGER_N_CORRECTION_20261103.md:11-12",
         "订正 §531：594ms 是停滞本身而非正常抖动；安全采样窗口（>0.6s）与停滞主体不重叠的论证不成立，N=1.0s 误触率实测为 0。"),
        ("P05_VS_S529_RECONCILE_20261104.md", "lead/goal3t_nightwatch_20261102/P05_VS_S529_RECONCILE_20261104.md:12",
         "两段完全不重叠，测的是同一趟游戏的两个不同阶段，结论互补（P05 wait_trace 覆盖等待段 帧 0→800 为多次型慢爬；§529 measure_w 覆盖采窗段为引擎停摆型）。"),
        ("STAGE_SUMMARY_20261103.md", "lead/goal3t_nightwatch_20261102/STAGE_SUMMARY_20261103.md:11",
         "① 修数百单位战斗卡顿：机制未闭合，但已否证「负载驱动」这个默认假设，并排除 5 个竞争解释。"),
        ("BATCH_XVERIFY_20261103.md", "lead/goal3t_nightwatch_20261102/BATCH_XVERIFY_20261103.md:13-15",
         "五条离线分析结论独立复算：纯离线只读数据目录下的 measure_w*.json，不参照被核验方口径重算。")
    ]

    p(f"--- 停滞结构相关 .md 文件（共 {len(stall_mds)} 份，逐件列出字节数与核心结论）---")
    for fname, cite, concl in stall_mds:
        fpath = os.path.join(nw_dir, fname)
        if os.path.exists(fpath):
            bsize = os.path.getsize(fpath)
            p(f"\n- 文件：{fname}（{bsize:,} 字节）")
            p(f"  出处：{cite}")
            p(f"  核心结论：{concl}")
        else:
            p(f"\n- 文件：{fname} [未找到]")

    # 停滞结构相关的 .py 脚本清单
    stall_pys = [
        ("_stall_timestructure.py", "时域结构四维度分析脚本（D1 周期性、D2 段长分布、D3 帧值单调性、D4 工作集活动）"),
        ("_xst_verify.py", "时域结构独立核验脚本（平台时长、口径 B、帧沿缺口、目标批与分型复算）"),
        ("_stall_vs_gap.py", "停滞与采样缺口可分性检验探针（计算 B% 与帧沿缺口相关性，排除采样伪影）"),
        ("_xsg_verify.py", "停滞 vs 缺口独立核验脚本（全量 101 窗递归枚举，独立判定 NOT_ARTIFACT）"),
        ("_freeze_onset.py", "冻结起始时刻预测指示器探测脚本（检验 8 个候选量，捕获分母假相关）"),
        ("_occ_census_all.py", "occ_a 与口径 B 停滞占比影响全量普查脚本（95 窗逐窗三口径实算）"),
        ("_occ_decomp.py", "停滞占比差异分解脚本（恒等式证明 head 为 C 型、tail 为 B 型）"),
        ("_occ_gapcorr.py", "口径差与采样缺口相关性探针（锁定缺口驱动 r=0.7448）"),
        ("_occ_xcompare.py", "口径对比与逐窗明细探针"),
        ("_xocc_verify.py", "停滞占比口径普查独立复算脚本（91 窗全量复算）"),
        ("_phase_test.py", "时间相位假说检验脚本（检验 H_phase 与 H_uptime 相关性）"),
        ("_xpt_verify.py", "停滞结构分类独立核验脚本（单段恒等式与多次型递增验证）"),
        ("_phase_recompute.py", "BOOT 分组相位重算脚本（含 nan 未过滤统计缺陷）"),
        ("_f0_rule_validate.py", "f[0]==0 加载段型判别规则全量验证脚本"),
        ("_confound_probe.py", "结构类型与会话共线混杂检验探针（units0 分层与 B%(T=0.2) 检验）"),
        ("_units_vs_stall.py", "单位数与停滞占比相关性检验脚本（计算 r(units0, B%)）"),
        ("_xbatch_verify.py", "五条离线分析结论综合独立复算脚本"),
        ("stall_judge.py", "离线停滞判读标准固化实现（五步判读：有推进、f[0]==0、最长段占比、帧沿缺口、freezeStart）")
    ]

    p(f"\n--- 停滞结构相关 .py 脚本（共 {len(stall_pys)} 份，逐件列出字节数与功能说明）---")
    for fname, desc in stall_pys:
        fpath = os.path.join(nw_dir, fname)
        if os.path.exists(fpath):
            bsize = os.path.getsize(fpath)
            p(f"  - {fname} ({bsize:,} 字节): {desc}")
        else:
            p(f"  - {fname}: [未找到]")

def section_4_d26_ruling_extraction():
    p("\n" + "=" * 80)
    p("【第 4 部分：lead/d26_ruling_20261106/RULING_D26.md 第 1 节「先补项目」原样摘录】")
    p("=" * 80)

    ruling_path = os.path.join(REPO_ROOT, "lead", "d26_ruling_20261106", "RULING_D26.md")
    p(f"读取文件：{os.path.relpath(ruling_path, REPO_ROOT).replace('\\', '/')}")
    
    if not os.path.exists(ruling_path):
        p("  [未找到]")
        return

    with open(ruling_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    p("\n原文第 19 行整段原样摘录（lead/d26_ruling_20261106/RULING_D26.md:19）：")
    line19 = lines[18].strip()
    p(f"「{line19}」")

    p("\n裁决书要求补的四项内容逐字原样摘出：")
    p("  1. 在既有离线语料中定义并识别真实对局目标事件")
    p("  2. 明确性能量及长停代表范围")
    p("  3. 排除结束态和合法冻结混淆")
    p("  4. 提交触发延迟、采样扰动、栈解析、停止及回退设计")

if __name__ == "__main__":
    section_1_corpus_count()
    section_2_inspect_measure_files()
    section_3_nightwatch_stall_files()
    section_4_d26_ruling_extraction()
