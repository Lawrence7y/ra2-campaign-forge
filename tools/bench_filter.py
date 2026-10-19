#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bench_filter.py — 采样剖析噪声过滤与归因重算引擎（解决 Q1/Q2/Q3）。

核心功能：
1. 模块分类与噪声剔除：
   - WAIT：ntdll.dll, win32u.dll, kernelbase.dll, kernel32.dll, winmm.dll
   - SHIM：acgenral.dll, acadproc.dll, aclayers.dll, acshelllayers.dll, acxtrnal.dll
   - SYS_GUI：user32.dll, gdi32.dll, gdi32full.dll, uxtheme.dll, imm32.dll
   - GPU_PRESENT：ddraw.dll, d3d9.dll, dxgi.dll, opengl32.dll
   - HOOK：ra2render.dll
   - GAMEMD：gamemd.exe
   - SYS_OTHER：binkw32.dll, wow64cpu.dll 等
2. gamemd 内部多层级地址段归因：
   - 依据已实证的 VA 区段表，将未归因热点（如 0x53EB00、0x7C9300）还原至精确功能域：
     logic.frame_timer, crt, audio, logic.main, render.tactical, render.cell 等。
3. 过滤前后对比统计与指标判定：
   - 样本总量、噪声总量、有效工作样本数、有效工作占比、归因覆盖率。
   - 自动化判定主菜单/等待态与真实对局态。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# 模块噪声分类字典（Q1H-R3 收口：口径与 tools/bench_replay.py / PROTOCOL.md §5 完全一致）
#
# 四类**无条件剔除**的噪声 + 两类**必须单列**的观察类：
#   wait   线程在系统里睡眠/等句柄（NtDelayExecution / NtWaitForSingleObject），不产出任何游戏工作
#   shim   Windows 兼容层垫片（挂钩 Sleep / DirectDrawCreate / timeGetTime，会放大噪声）
#   sys_gui 桌面窗口消息与 GDI 包装（user32/gdi32/uxtheme）
#   gpu    呈现同步（DDraw 翻页/VSync 等待）——注意：**不能断言全是等待**，cnc-ddraw 下 Blt 转发
#          也落在这里；故单列 `gpu_present` 供审计，不并入 valid（真机必须另取 ddraw 导出表归因）
#   video  Bink 视频解码（binkw32）——只出现在过场/主菜单背景，是**场景状态信号**，不是噪声也不是工作
#   hooks  本工程注入的 ra2render.dll，计入 valid（DLL 不覆盖 exe 段的归因由 VA 区间完成）
MODULE_WAIT = {
    "ntdll.dll", "win32u.dll", "kernelbase.dll", "kernel32.dll", "winmm.dll",
    "wow64cpu.dll", "wow64win.dll", "wow64.dll",
}
MODULE_WAIT_PREFIX = ("ntdll",)
MODULE_SHIM = {
    "acgenral.dll", "acadproc.dll", "aclayers.dll", "acshelllayers.dll", "acxtrnal.dll",
    "acspecfc.dll", "acwinrt.dll", "apphelp.dll",
}
MODULE_SYS_GUI = {
    "user32.dll", "gdi32.dll", "gdi32full.dll", "uxtheme.dll", "imm32.dll", "msctf.dll",
}
MODULE_GPU_PRESENT = {
    "ddraw.dll", "d3d9.dll", "dxgi.dll", "opengl32.dll",
}
MODULE_VIDEO = {
    "binkw32.dll", "binkw32h.dll",
}
MODULE_HOOKS = {
    "ra2render.dll",
}

# 由 docs/re/anchor_claims.txt（323 条）+ 本目录 claims.txt 反查：哪些 VA 区间**真的有字节级锚点**。
# 这是防误用的核心字段：覆盖率数字只说明「落进某张手写表」，不说明该表被证据支撑。
# 符号表命中（RTTI 虚表）归到 sym.* 前缀，与"区间命中"严格分账——两者证据强度不同
SYMBOL_TAGS = {"sym.blit", "sym.rtti"}

ANCHOR_FILES = (
    Path(__file__).resolve().parent.parent / "docs" / "re" / "anchor_claims.txt",
    Path(__file__).resolve().parent.parent / "out" / "re_work" / "bench_harness" / "claims.txt",
)


def load_anchor_vas(extra: list = None) -> list:
    """读全部锚点断言文件的 VA（`0xVA = HEXBYTES` 行），返回去重升序列表。"""
    vas = set()
    paths = list(ANCHOR_FILES) + list(extra or [])
    for p in paths:
        pp = Path(p)
        if not pp.is_file():
            continue
        for line in pp.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line.startswith("0x") or "=" not in line:
                continue
            va = line.split("=", 1)[0].strip()
            try:
                vas.add(int(va, 16))
            except ValueError:
                continue
    return sorted(vas)


def range_evidence(vas: list) -> dict:
    """每个 GAMEMD_FUNCTION_RANGES 区间内落了多少条字节级锚点 -> 证据等级。

    >=1 条锚点 -> `[实证-区间内有锚点]`（区间归属有字节级依据）
    0  条锚点 -> `[推演-无字节锚点]`（区间是手写假设，**不得**据此宣称"已归因"）
    """
    out = {}
    for tag, lo, hi, desc in GAMEMD_FUNCTION_RANGES:
        hits = [va for va in vas if lo <= va < hi]
        if tag in out:
            out[tag]["anchors"] += len(hits)
            out[tag]["anchor_vas"] += [hex(v) for v in hits]
            out[tag]["evidence"] = ("[实证-区间内有锚点]" if out[tag]["anchors"] > 0
                                    else "[推演-无字节锚点]")
            continue
        out[tag] = {
            "range": f"0x{lo:06X}-0x{hi:06X}",
            "desc": desc,
            "anchors": len(hits),
            "anchor_vas": [hex(v) for v in hits],
            "evidence": "[实证-区间内有锚点]" if hits else "[推演-无字节锚点]",
        }
    return out

# gamemd.exe 核心功能区间定义（基于台账与反汇编实证，VA 闭开区间 [lo, hi)）
GAMEMD_FUNCTION_RANGES: list[tuple[str, int, int, str]] = [
    # 渲染 - Blit 族
    ("render.blit", 0x007BC600, 0x007BCA00, "软件 Blit: Plain / Trans 核心循环"),
    ("render.blit", 0x00491200, 0x00493700, "软件 Blit: Xlat / Darken / Lucent / ZRead 簇"),
    ("render.blit_rle", 0x00496000, 0x00496500, "RLE 压缩格式 Blit"),
    ("render.blit_misc", 0x00499000, 0x0049A100, "辅类 Blit 渲染包装"),
    # 渲染 - 地图与单元格
    ("render.cell_fog", 0x0047EF00, 0x0047F700, "单元格黑雾/灰雾渲染"),
    ("render.cell_draw", 0x00480100, 0x00480600, "单元格地面与地形绘制"),
    ("render.cell_extra", 0x0048CE00, 0x0048D800, "单元格覆盖物与过渡层绘制"),
    # 渲染 - 战术视图与视口
    ("render.tactical", 0x006D3D00, 0x006D4900, "战术地图主视口重绘循环"),
    ("render.tactical2", 0x006DA700, 0x006DAB00, "视口裁剪与卷屏重绘"),
    ("render.tactical3", 0x006D2700, 0x006D2B00, "视口渲染缓冲调度"),
    ("render.display", 0x00531B00, 0x00532200, "DisplayClass 战术层合成与刷新"),
    # 渲染 - VXL / 3D 体素与表面
    ("render.vxl", 0x00706000, 0x00707900, "VXL 体素单位渲染核心"),
    ("render.vxl2", 0x004DAF00, 0x004DB300, "VXL 阴影与转换管线"),
    ("render.surface", 0x004BA500, 0x004BB400, "BSurface 表面内存拷贝与锁定"),
    ("render.anim_shp", 0x004AED00, 0x004AEE00, "SHP 序列动画与爆炸绘制"),
    # 渲染 - 雷达与小地图
    ("render.radar", 0x00655200, 0x00657A00, "雷达小地图刷新与点位绘制"),
    ("render.radar2", 0x00653100, 0x00654500, "雷达视口框与调色板更新"),
    # UI 交互与控件
    ("ui.sidebar", 0x006A6C00, 0x006AC000, "侧边栏建造栏绘制与点击检测"),
    ("ui.gadget", 0x00556F00, 0x00557900, "UI 控件、按钮与文本渲染"),
    ("ui.control", 0x00623000, 0x00623500, "UI 消息循环与事件派发"),
    # 逻辑 - 帧时钟与主循环
    ("logic.main", 0x0055D300, 0x0055DF00, "游戏主循环 Main_Loop"),
    ("logic.frame_timer", 0x0053E700, 0x0053EC00, "GameFrameTimer 帧定时与帧步进锁"),
    ("logic.session", 0x0054E800, 0x0054F800, "SessionClass 对局逻辑推进"),
    ("logic.loop_extra", 0x005D4A00, 0x005D5200, "引擎内部分发与上下文切换"),
    # 逻辑 - 目标扫描与决策
    ("logic.target", 0x006F8D00, 0x006FB400, "Greatest_Threat 寻敌扫描 (O(N^2))"),
    ("logic.target2", 0x00736C00, 0x00736E00, "目标射程与阻挡判定"),
    ("logic.target3", 0x00743100, 0x00743300, "交火威胁等级评估"),
    # 逻辑 - 寻路与 AI
    ("logic.path", 0x0042A500, 0x0042AF00, "LayerClass / Pathfind 寻路计算"),
    ("logic.path2", 0x0042CB00, 0x0042CD00, "网格通达性检测"),
    ("logic.path3", 0x004CBA00, 0x004CBC00, "寻路节点估价"),
    ("logic.house_ai", 0x004E6200, 0x004E6D00, "HouseClass 作战 AI 决策"),
    ("logic.object", 0x00610C00, 0x00615800, "ObjectClass / TechnoClass 状态更新"),
    # 音频与运行时
    ("audio", 0x00406F00, 0x00407C00, "Audio 音频混音与样本推送"),
    ("audio_stream", 0x00409000, 0x00409800, "音频流式解压与缓冲"),
    ("audio_play", 0x00750900, 0x00750B00, "SoundClass 触发播放"),
    ("crt", 0x007C8B00, 0x007CA000, "MSVCRT 运行时库基础函数 (memcpy/memset/qsort)"),
]
GAMEMD_FUNCTION_RANGES.sort(key=lambda x: x[1])


def classify_module(mod_name: str) -> str:
    """按模块名称归类：wait / shim / sys_gui / gpu_present / video / hooks / gamemd / other"""
    low = mod_name.lower().strip()
    if low.startswith("gamemd"):
        return "gamemd"
    if low in MODULE_WAIT or any(low.startswith(p) for p in MODULE_WAIT_PREFIX):
        return "wait"
    if low in MODULE_SHIM:
        return "shim"
    if low in MODULE_SYS_GUI:
        return "sys_gui"
    if low in MODULE_GPU_PRESENT:
        return "gpu_present"
    if low in MODULE_VIDEO:
        return "video"
    if low in MODULE_HOOKS or low.startswith("ra2render"):
        return "hooks"
    return "other"


def module_disposition(cat: str) -> str:
    """每类的处置口径（写进对比表，防止"剔了但没说"）。"""
    return {
        "wait": "剔除（内核睡眠/等句柄，不产出游戏工作）",
        "shim": "剔除（兼容层垫片轮询，非游戏逻辑）",
        "sys_gui": "剔除（桌面消息/GDI 包装）",
        "gpu_present": "剔除但单列审计（VSync/翻页等待；cnc-ddraw 下含 Blt 转发，不能断言全为等待）",
        "video": "单列观察（Bink 过场/菜单背景，作为场景状态信号）",
        "hooks": "保留（ra2render.dll，本工程注入模块）",
        "gamemd": "保留（被测量的实际工作载荷）",
        "other": "观察（未归类 DLL，需人看清单）",
    }.get(cat, "观察")


def classify_gamemd_address(va: int) -> tuple[str, str]:
    """在 gamemd 镜像内按 VA 区间归因到已知功能簇。"""
    for tag, lo, hi, desc in GAMEMD_FUNCTION_RANGES:
        if lo <= va < hi:
            return tag, desc
    return "gamemd_other", "gamemd 内部未标定代码"


def filter_and_analyze_profile(data: dict[str, Any], extra_anchors: list = None) -> dict[str, Any]:
    """对原始采样结果执行噪声剥离与重归因分析。"""
    total_samples = data.get("samples", 0)
    by_module = data.get("by_module", {})
    by_class = data.get("by_class", {})
    hot_unknown = data.get("hot_unknown", {})
    top_symbols = data.get("top_symbols", {})

    # 1. 模块噪声分类统计
    cat_counts: dict[str, int] = {
        "wait": 0,
        "shim": 0,
        "sys_gui": 0,
        "gpu_present": 0,
        "video": 0,
        "hooks": 0,
        "gamemd": 0,
        "other": 0,
    }
    for mod, cnt in by_module.items():
        cat = classify_module(mod)
        cat_counts[cat] = cat_counts.get(cat, 0) + cnt

    n_noise = (cat_counts["wait"] + cat_counts["shim"] +
               cat_counts["sys_gui"] + cat_counts["gpu_present"])
    n_gamemd = cat_counts["gamemd"]
    n_hooks = cat_counts["hooks"]
    n_valid = n_gamemd + n_hooks

    # 2. 对 gamemd 内样本（包含 hot_unknown 与 top_symbols）进行多层重标定
    gamemd_breakdown: dict[str, int] = {}
    gamemd_details: list[dict[str, Any]] = []

    # 先归入已知 top_symbols
    for sym_name, cnt in top_symbols.items():
        tag = "sym.blit" if "Blit" in sym_name else "sym.rtti"
        gamemd_breakdown[tag] = gamemd_breakdown.get(tag, 0) + cnt

    # 遍历 hot_unknown 中的 256B 分桶地址
    attributed_unknown = 0
    unattributed_unknown = 0
    for addr_str, cnt in hot_unknown.items():
        try:
            va = int(addr_str, 16)
        except ValueError:
            va = 0
        tag, desc = classify_gamemd_address(va)
        gamemd_breakdown[tag] = gamemd_breakdown.get(tag, 0) + cnt
        if tag != "gamemd_other":
            attributed_unknown += cnt
        else:
            unattributed_unknown += cnt
        gamemd_details.append({
            "bucket": addr_str,
            "va": hex(va),
            "samples": cnt,
            "tag": tag,
            "desc": desc,
        })

    # 汇总计算指标
    active_ratio = round(100.0 * n_valid / max(total_samples, 1), 2)
    noise_ratio = round(100.0 * n_noise / max(total_samples, 1), 2)
    coverage_ratio = round(100.0 * (sum(cnt for k, cnt in gamemd_breakdown.items() if k != "gamemd_other")) / max(n_gamemd, 1), 2) if n_gamemd > 0 else 0.0

    # 状态推断
    is_main_menu = (active_ratio < 2.0 or (cat_counts["wait"] + cat_counts["shim"] + cat_counts["sys_gui"]) / max(total_samples, 1) > 0.95)
    is_heavy_battle = (active_ratio > 30.0 and gamemd_breakdown.get("render.blit", 0) / max(n_gamemd, 1) > 0.15)

    # 3. 区间证据等级（防误用核心）：覆盖率只证明「落进手写表」，不证明该表被字节证据支撑
    vas = load_anchor_vas(extra_anchors)
    ev = range_evidence(vas)
    breakdown_rows = []
    anchored_samples = 0
    for tag, cnt in sorted(gamemd_breakdown.items(), key=lambda x: -x[1]):
        info = ev.get(tag)
        kind = "symbol" if tag in SYMBOL_TAGS else ("range" if info else "unattributed")
        if info and info["anchors"] > 0:
            anchored_samples += cnt
        breakdown_rows.append({
            "tag": tag,
            "samples": cnt,
            "pct_of_gamemd": round(100.0 * cnt / max(n_gamemd, 1), 2),
            "attribution_kind": kind,
            "range": info["range"] if info else "",
            "anchors_in_range": info["anchors"] if info else 0,
            "anchor_vas": info["anchor_vas"] if info else [],
            "evidence": info["evidence"] if info else "[未归因-无区间]",
            "desc": (info or {}).get("desc",
                                     "gamemd 内部未标定代码" if kind == "unattributed"
                                     else "符号表命中（RTTI 虚表）"),
        })

    # 4. 过滤前后对比表（模块级：原始样本 -> 分类 -> 处置）
    comparison_table = []
    for mod, cnt in sorted(by_module.items(), key=lambda x: -x[1]):
        cat = classify_module(mod)
        comparison_table.append({
            "module": mod,
            "raw_samples": cnt,
            "raw_pct": round(100.0 * cnt / max(total_samples, 1), 2),
            "category": cat,
            "disposition": module_disposition(cat),
            "kept_as_valid": cat in ("gamemd", "hooks"),
        })

    anchors_total = len(vas)
    anchored_pct = round(100.0 * anchored_samples / max(n_gamemd, 1), 2) if n_gamemd else 0.0

    guard = (
        "本报告数字全部来自**历史采样 JSON 的静态重排**：它只描述「那次采样采到了什么」，"
        "既不能证明任何性能达标，也不能证明某段代码是热点"
        "（功能区间归属多为 [推演]，见 gamemd_breakdown_rows 的 evidence 字段）。"
    )

    return {
        "total_samples": total_samples,
        "seconds": data.get("seconds", 0.0),
        "hz": data.get("hz", 0.0),
        "categories": cat_counts,
        "noise_samples": n_noise,
        "noise_pct": noise_ratio,
        "valid_samples": n_valid,
        "valid_pct": active_ratio,
        "gamemd_samples": n_gamemd,
        "hooks_samples": n_hooks,
        "gamemd_breakdown": dict(sorted(gamemd_breakdown.items(), key=lambda x: -x[1])),
        "gamemd_breakdown_rows": breakdown_rows,
        "coverage_pct": coverage_ratio,
        "coverage_definition": ("区间表命中率 = (N_gamemd - N_gamemd_other) / N_gamemd * 100%；"
                                "**不是**符号验证率，也不是归因正确性证明"),
        "anchored_range_pct": anchored_pct,
        "anchored_range_definition": "落在**有字节级锚点**的功能区间内的 gamemd 样本占比（诚实口径）",
        "anchors_loaded": anchors_total,
        "comparison_table": comparison_table,
        "metric_disclaimer": guard,
        "state_evaluation": {
            "is_main_menu_or_idle": is_main_menu,
            "is_heavy_battle": is_heavy_battle,
            "verdict": "MAIN_MENU_OR_WAITING" if is_main_menu else ("HEAVY_BATTLE" if is_heavy_battle else "NORMAL_IN_GAME"),
        },
        "hot_reclassified": gamemd_details[:15],
    }


def format_markdown_comparison(raw_data: dict, analysis: dict, title: str = "采样噪声过滤前后对比") -> str:
    """渲染过滤前后对比（Q2）。三段：模块级对比表 / gamemd 内部重标定（带证据等级）/ 防误用声明。"""
    a = analysis
    tot = max(a["total_samples"], 1)
    g_tot = max(a["gamemd_samples"], 1)
    lines = [
        f"### {title}",
        "",
        f"- **原始采样**：{a['total_samples']} 样本 / {a['seconds']}s（{a['hz']} Hz）",
        f"- **环境推断结论**：`{a['state_evaluation']['verdict']}`"
        "（该结论只由模块分布/类别比例推断，**不是**对局状态证据）",
        f"- **锚点库**：{a['anchors_loaded']} 条字节级断言（docs/re/anchor_claims.txt + bench_harness/claims.txt）",
        "",
        "#### 1. 过滤前后对比表（模块级，原始样本 → 分类 → 处置）",
        "",
        "| 模块 | 原始样本 | 占原始% | 分类 | 过滤处置 | 计入 valid |",
        "|---|---:|---:|---|---|---|",
    ]
    for row in a["comparison_table"]:
        lines.append(f"| `{row['module']}` | {row['raw_samples']} | {row['raw_pct']}% | "
                     f"{row['category']} | {row['disposition']} | "
                     f"{'是' if row['kept_as_valid'] else '否'} |")
    c = a["categories"]
    lines += [
        "",
        "| 分类 | 样本 | 占原始% | 处置 |",
        "|---|---:|---:|---|",
    ]
    for cat in ("wait", "shim", "sys_gui", "gpu_present", "video", "hooks", "gamemd", "other"):
        cnt = c.get(cat, 0)
        lines.append(f"| {cat} | {cnt} | {100.0 * cnt / tot:.2f}% | {module_disposition(cat)} |")
    lines += [
        "",
        f"**过滤汇总**：噪声（wait+shim+sys_gui+gpu_present）= **{a['noise_samples']}** "
        f"({a['noise_pct']}%)；有效工作（gamemd+hooks）= **{a['valid_samples']}** ({a['valid_pct']}%)。",
        "",
        "#### 2. gamemd 内部分账（符号命中 vs 区间命中，逐行标证据等级）",
        "",
        "| 功能分类 | 样本 | 占 gamemd% | 归因方式 | VA 区间 | 区间内锚点数 | 证据等级 |",
        "|---|---:|---:|---|---|---:|---|",
    ]
    for row in a["gamemd_breakdown_rows"]:
        lines.append(f"| `{row['tag']}` | {row['samples']} | {row['pct_of_gamemd']}% | "
                     f"{row['attribution_kind']} | {row['range'] or '-'} | "
                     f"{row['anchors_in_range']} | {row['evidence']} |")
    lines += [
        "",
        f"- **区间表命中率**：**{a['coverage_pct']}%** —— {a['coverage_definition']}",
        f"- **锚点支撑占比（诚实口径）**：**{a['anchored_range_pct']}%** —— {a['anchored_range_definition']}",
        "",
        "> **防误用**：" + a["metric_disclaimer"],
        "",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="bench_filter")
    ap.add_argument("profile_json", help="输入采样原始 JSON 路径")
    ap.add_argument("--out-json", default=None, help="分析结果 JSON 导出路径")
    ap.add_argument("--out-md", default=None, help="分析报告 Markdown 导出路径")
    ap.add_argument("--anchors", nargs="*", default=None,
                    help="额外的字节级锚点断言文件（默认已含 docs/re/anchor_claims.txt 与 bench_harness/claims.txt）")
    ap.add_argument("--combined", default=None,
                    help="把多个输入 JSON 的对比结果合并写入该 Markdown（Q2 汇总）")
    args = ap.parse_args(argv)

    p = Path(args.profile_json)
    if not p.is_file():
        print(f"[FAIL] 文件不存在: {p}", file=sys.stderr)
        return 1

    raw = json.loads(p.read_text(encoding="utf-8"))
    res = filter_and_analyze_profile(raw, extra_anchors=args.anchors)

    md = format_markdown_comparison(raw, res, title=f"采样过滤对比报告 — {p.name}")
    print(md)

    if args.out_json:
        out_p = Path(args.out_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] JSON 落盘: {out_p}")

    if args.out_md:
        out_m = Path(args.out_md)
        out_m.parent.mkdir(parents=True, exist_ok=True)
        out_m.write_text(md, encoding="utf-8")
        print(f"[OK] Markdown 落盘: {out_m}")

    if args.combined:
        out_c = Path(args.combined)
        out_c.parent.mkdir(parents=True, exist_ok=True)
        head = ["# 采样噪声过滤对比汇总（Q2 / Q1H-R3）", "",
                f"- 输入：`{p.name}`（{p.stat().st_size} B）",
                "- 门禁口径：`noise` = wait+shim+sys_gui+gpu_present；`valid` = gamemd.exe + ra2render.dll",
                "- 结构性提示：**历史采样 JSON 没有帧序列与单位数**，因此本文件只能证明「过滤口径可用」，",
                "  不能证明任何性能数字；性能判定见 `tools/bench_metrics.py`（会直接报 NOT_MEASURABLE）。",
                "", ""]
        out_c.write_text("\n".join(head) + md, encoding="utf-8")
        print(f"[OK] 对比汇总落盘: {out_c}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
