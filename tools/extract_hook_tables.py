#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/extract_hook_tables.py
============================
遍历扫描 docs/re/*.md（目前 24 份逆向文档）中所有提出的 Hook 建议、挂载点地址、虚表项、
调用约定与替换指令，并与现网 ra2render/blitter_hooks.cpp 已安装项交叉对照。

抽取结果保存至 out/re_work/hook_matrix/hooks.json。
"""

import os
import sys
import glob
import re
import json

WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(WORKSPACE, "docs", "re")
OUT_DIR = os.path.join(WORKSPACE, "out", "re_work", "hook_matrix")
BLITTER_HOOKS_CPP = os.path.join(WORKSPACE, "ra2render", "blitter_hooks.cpp")
RA2RENDER_H = os.path.join(WORKSPACE, "ra2render", "ra2render.h")

# 已知现网安装的 Hook 点特征（用于交叉标注）
# 依据 ra2render/blitter_hooks.cpp 与 ra2render.h 实机代码
INSTALLED_HOOKS_MAP = {
    # 1. HighColor Blitter VTables (L1)
    "0x007E56F4": {"status": "已装", "impl": "BlitterHooks::Hook_BlitTransXlatAlphaZRead (0x007E56F0 + 4)", "category": "VTable_Overwrite"},
    "0x007E5A24": {"status": "已装", "impl": "BlitterHooks::Hook_BlitTransXlat_G (0x007E5A20 + 4)", "category": "VTable_Overwrite"},
    "0x007E55C4": {"status": "已装", "impl": "BlitterHooks::Hook_RLEBlitTransXlat_G (0x007E55C0 + 4)", "category": "VTable_Overwrite"},
    "0x007F7BF8": {"status": "已装", "impl": "BlitterHooks::Hook_BlitTrans_G (0x007F7BF4 + 4)", "category": "VTable_Overwrite"},
    "0x007E59F4": {"status": "已装", "impl": "BlitterHooks::Hook_BlitTransDarken_G (0x007E59F0 + 4)", "category": "VTable_Overwrite"},
    "0x007F7BC8": {"status": "已装", "impl": "BlitterHooks::Hook_BlitPlain_G (0x007F7BC4 + 4)", "category": "VTable_Overwrite"},

    # 2. Target Scanning VTables (L2)
    "0x007F4D84": {"status": "已装", "impl": "TargetHooks::Hook_Techno_SelectAutoTarget (vtable[265])", "category": "VTable_Overwrite"},
    "0x007F6094": {"status": "已装", "impl": "TargetHooks::Hook_Unit_SelectAutoTarget (vtable[265])", "category": "VTable_Overwrite"},
    "0x007F4D24": {"status": "已合并", "impl": "已被 0x006F8DF0 Inline Hook 全面取代（无需虚表补装）", "category": "VTable_Overwrite"},
    "0x007F6034": {"status": "已合并", "impl": "已被 0x006F8DF0 Inline Hook 全面取代（无需虚表补装）", "category": "VTable_Overwrite"},
    "0x006F8DF0": {"status": "已装", "impl": "InstallGreatestThreatHook (9字节 Inline Hook + 14字节跳板)", "category": "Inline_Trampoline"},

    # 3. ObjectClass::Draw 槽 69 (L3/L5)
    "0x007F5D84": {"status": "已装", "impl": "FogHooks::Hook_Unit_Draw (UnitClass vtable[69])", "category": "VTable_Overwrite"},
    "0x007EB16C": {"status": "已装", "impl": "FogHooks::Hook_Infantry_Draw (InfantryClass vtable[69])", "category": "VTable_Overwrite"},
    "0x007E23B8": {"status": "已装", "impl": "FogHooks::Hook_Aircraft_Draw (AircraftClass vtable[69])", "category": "VTable_Overwrite"},
    "0x007E3FD0": {"status": "已装", "impl": "FogHooks::Hook_Building_Draw (BuildingClass vtable[69], v1.6.0)", "category": "VTable_Overwrite"},
    "0x007E47F8": {"status": "已装", "impl": "FogHooks::Hook_Bullet_Draw (BulletClass vtable[69], v1.6.0)", "category": "VTable_Overwrite"},

    # 4. CellClass::Draw & Fog Blending & Viewport Redraw (L3/L4)
    "0x004801F0": {"status": "已装", "impl": "Hook_CellClass_Draw_Proxy (5字节 Inline Hook + 跳板)", "category": "Inline_Trampoline"},
    "0x0047F40F": {"status": "已装", "impl": "Hook_FogBlendB1_Stub (49字节动态混色补丁)", "category": "Byte_Patch"},
    "0x0047F4AE": {"status": "已装", "impl": "Hook_FogBlendB2_Stub (51字节动态混色补丁)", "category": "Byte_Patch"},
    "0x006D3D99": {"status": "已装", "impl": "s_newTacticalRedrawBytes (jge -> jmp 0x006D3E37 全量视口刷新)", "category": "Byte_Patch"},

    # 5. Radar / Minimap (L5 v1.6.0)
    "0x006574C3": {"status": "已装", "impl": "ADDR_RADAR_PLOT_CALLSITE (0x00656EC0 循环内 call 0x655C50 代理覆写)", "category": "Callsite_Replace"},
    "0x0065719A": {"status": "已装", "impl": "ADDR_RADAR_PENDING_CALLSITE (call 0x660530 跳帧判定覆写)", "category": "Callsite_Replace"},
    "0x00655C50": {"status": "已装", "impl": "ADDR_RADAR_PLOT (序言 5 字节偷取跳板)", "category": "Inline_Trampoline"},
    "0x00655F48": {"status": "冲突废弃", "impl": "方案由 0x006574C3 代理覆写取代（无需改 0x655F48 点过滤）", "category": "Inline_Trampoline"},

    # 6. SpySat BuildingType 内存属性修改
    "0x00A83C68": {"status": "已装", "impl": "PatchSpySatBuildingTypes (内存属性清零 SpySat=0)", "category": "Memory_Patch"},
}

def normalize_addr(addr_str):
    if not addr_str:
        return ""
    m = re.search(r'0x00[0-9a-fA-F]{6}|0x[0-9a-fA-F]{6,8}', addr_str)
    if m:
        val = int(m.group(0), 16)
        return f"0x{val:08X}"
    return addr_str.strip()

def scan_markdown_files():
    records = []
    doc_paths = sorted(glob.glob(os.path.join(DOCS_DIR, "*.md")))

    for path in doc_paths:
        fname = os.path.basename(path)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        in_table = False
        table_headers = []
        table_start_line = 0

        for line_no, raw_line in enumerate(lines, 1):
            line = raw_line.strip()

            # 检测 Markdown 表格行
            if line.startswith("|") and line.endswith("|"):
                cells = [c.strip() for c in line.split("|")[1:-1]]
                if not in_table:
                    in_table = True
                    table_headers = [c.lower() for c in cells]
                    table_start_line = line_no
                    continue
                else:
                    if all(set(c).issubset({'-', ':', ' '}) for c in cells):
                        continue

                    row_data = {}
                    for idx, h in enumerate(table_headers):
                        if idx < len(cells):
                            row_data[h] = cells[idx]

                    record = try_parse_table_hook_row(fname, line_no, row_data, cells, raw_line)
                    if record:
                        records.append(record)
            else:
                in_table = False
                table_headers = []

                text_record = try_parse_text_hook_line(fname, line_no, raw_line)
                if text_record:
                    records.append(text_record)

    return records

def try_parse_table_hook_row(fname, line_no, row_data, cells, raw_line):
    addrs = re.findall(r'0x[0-9a-fA-F]{6,8}', raw_line)
    if not addrs:
        return None

    is_hook_relevant = any(k in raw_line.lower() for k in [
        'hook', 'vtable', '虚表', '槽', 'slot', '入口', '挂载', '拦截', '补丁', 'patch',
        'rleblit', 'blit', 'draw', 'threat', 'radar', 'fog', 'loco', 'path', 'vector',
        'h-', 'p0', 'p1', 'p2', 'p3', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'h9', 'h10', 'h11',
        '修改', '机器码', 'nop', 'reveal', 'reshroud', 'spysat', 'gap', '跳板', 'trampoline'
    ])
    if not is_hook_relevant:
        return None

    norm_addrs = [normalize_addr(a) for a in addrs]
    primary_addr = norm_addrs[0]

    symbol = ""
    for c in cells:
        clean = re.sub(r'[`\*\[\]]', '', c).strip()
        if any(token in clean for token in ['::', '?', 'Draw', 'Blit', 'Plot', 'Threat', 'Target', 'Update', 'Process', 'Move']):
            symbol = clean
            break
        elif clean.startswith(('H-', 'P0', 'P1', 'P2', 'P3', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'H11')):
            symbol = clean

    if not symbol and len(cells) > 1:
        symbol = re.sub(r'[`\*\[\]]', '', cells[0] if not '0x' in cells[0] else cells[1]).strip()

    vtable_base = ""
    vtable_slot = ""
    for c in cells:
        slot_m = re.search(r'(?:槽|slot|v\[)\s*(\d+)\]?', c, re.IGNORECASE)
        if slot_m:
            vtable_slot = slot_m.group(1)
        for a in norm_addrs:
            if a in c and (a.startswith("0x007E") or a.startswith("0x007F")):
                vtable_base = a
                break

    calling_conv = "__thiscall"
    if "__fastcall" in raw_line or "fastcall" in raw_line.lower():
        calling_conv = "__fastcall"
    elif "__cdecl" in raw_line or "cdecl" in raw_line.lower():
        calling_conv = "__cdecl"
    elif "inline" in raw_line.lower():
        calling_conv = "inline_asm"

    subsystem = classify_subsystem(fname, raw_line, symbol)

    status = "未装"
    impl_details = ""
    category = "未定义"
    for a in norm_addrs:
        if a in INSTALLED_HOOKS_MAP:
            status = INSTALLED_HOOKS_MAP[a]["status"]
            impl_details = INSTALLED_HOOKS_MAP[a]["impl"]
            category = INSTALLED_HOOKS_MAP[a]["category"]
            primary_addr = a
            break

    conflict_group = classify_conflict_group(primary_addr, norm_addrs, symbol, vtable_slot)

    # 提取替换指令或说明
    replaced_instruction = ""
    for c in cells:
        if any(kw in c for kw in ['ret', 'jmp', 'call', 'nop', 'mov', 'xor', 'test', 'E9', '0F 8D']):
            replaced_instruction = re.sub(r'[`\*]', '', c).strip()
            break

    return {
        "source_doc": f"docs/re/{fname}",
        "source_line": line_no,
        "symbol": symbol,
        "primary_address": primary_addr,
        "all_addresses": norm_addrs,
        "vtable_base": vtable_base,
        "vtable_slot": vtable_slot,
        "calling_convention": calling_conv,
        "replaced_instruction": replaced_instruction,
        "subsystem": subsystem,
        "hook_category": category,
        "status": status,
        "installed_impl": impl_details,
        "conflict_group": conflict_group,
        "raw_text": raw_line.strip()
    }

def try_parse_text_hook_line(fname, line_no, raw_line):
    addrs = re.findall(r'0x[0-9a-fA-F]{6,8}', raw_line)
    if not addrs:
        return None

    if not any(k in raw_line for k in [
        'Hook', 'hook', 'H-FX', 'H-VXL', 'P0', 'P1', 'P2', 'P3',
        'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H10', 'H11',
        '0x006D3D99', '0x00655F48', '0x006574C3', '0x006F8DF0',
        '0x0073B0B0', '0x0073B470', '0x0073CEC0', '0x006D8DB0'
    ]):
        return None

    norm_addrs = [normalize_addr(a) for a in addrs]
    primary_addr = norm_addrs[0]

    symbol = ""
    sym_match = re.search(r'[`\*]([A-Za-z0-9_:\?@]+)[`\*]', raw_line)
    if sym_match:
        symbol = sym_match.group(1)
    else:
        symbol = raw_line.strip()[:40]

    vtable_slot = ""
    slot_m = re.search(r'(?:槽|slot|v\[)\s*(\d+)\]?', raw_line, re.IGNORECASE)
    if slot_m:
        vtable_slot = slot_m.group(1)

    calling_conv = "__thiscall"
    if "__fastcall" in raw_line:
        calling_conv = "__fastcall"
    elif "__cdecl" in raw_line:
        calling_conv = "__cdecl"
    elif "inline" in raw_line.lower():
        calling_conv = "inline_asm"

    subsystem = classify_subsystem(fname, raw_line, symbol)

    status = "未装"
    impl_details = ""
    category = "未定义"
    for a in norm_addrs:
        if a in INSTALLED_HOOKS_MAP:
            status = INSTALLED_HOOKS_MAP[a]["status"]
            impl_details = INSTALLED_HOOKS_MAP[a]["impl"]
            category = INSTALLED_HOOKS_MAP[a]["category"]
            primary_addr = a
            break

    conflict_group = classify_conflict_group(primary_addr, norm_addrs, symbol, vtable_slot)

    replaced_instruction = ""
    if any(kw in raw_line for kw in ['ret', 'jmp', 'call', 'nop', 'mov', 'xor', 'test', 'E9', '0F 8D']):
        inst_m = re.search(r'(?:jmp|call|ret|nop|mov|xor|test|E9|0F 8D)[^`\|]+', raw_line)
        if inst_m:
            replaced_instruction = inst_m.group(0).strip()

    return {
        "source_doc": f"docs/re/{fname}",
        "source_line": line_no,
        "symbol": symbol,
        "primary_address": primary_addr,
        "all_addresses": norm_addrs,
        "vtable_base": "",
        "vtable_slot": vtable_slot,
        "calling_convention": calling_conv,
        "replaced_instruction": replaced_instruction,
        "subsystem": subsystem,
        "hook_category": category,
        "status": status,
        "installed_impl": impl_details,
        "conflict_group": conflict_group,
        "raw_text": raw_line.strip()
    }

def classify_subsystem(fname, line, symbol):
    fn = fname.lower()
    l = line.lower()
    s = symbol.lower()
    if 'blit' in fn or 'blit' in l or 'blit' in s:
        return "Render_Blitter"
    elif 'vxl' in fn or 'vxl' in l or 'vxl' in s:
        return "Render_VXL"
    elif 'fx' in fn or 'laser' in l or 'ebolt' in l or 'beam' in l:
        return "Render_FX"
    elif 'fog' in fn or 'shroud' in l or 'vision' in l or 'gap' in fn or 'spysat' in fn:
        return "Render_Fog_Visibility"
    elif 'target' in fn or 'threat' in l or 'target' in l:
        return "Logic_Targeting"
    elif 'dirty' in fn or 'viewport' in l or '0x006d3' in l or 'redraw' in l:
        return "Render_DirtyRect_Viewport"
    elif 'radar' in fn or 'minimap' in l or '0x00655' in l or '0x00657' in l:
        return "UI_Minimap_Radar"
    elif 'audio' in fn or 'vocclass' in l or 'sound' in l:
        return "Audio_Engine"
    elif 'path' in fn or 'loco' in fn:
        return "Logic_Pathfinding"
    elif 'sidebar' in fn or 'mouse' in l or 'cameo' in l:
        return "UI_Sidebar"
    elif 'crt' in fn or 'memory' in fn or 'pool' in fn:
        return "System_Memory_CRT"
    elif 'sync' in fn or 'checksum' in fn:
        return "Network_Determinism"
    elif 'ai' in fn or 'house' in fn or 'team' in fn:
        return "Logic_AI_Team"
    return "Other"

def classify_conflict_group(primary_addr, addrs, symbol, slot):
    tokens = set([primary_addr.upper()] + [a.upper() for a in addrs] + [symbol.upper(), str(slot)])

    # 冲突 1: VXL 与 FX 绘制链重叠 (0x73B0B0 / 0x73B470 / 0x73CEC0 / 0x6D8DB0)
    c1_addrs = {'0X0073B0B0', '0X0073B470', '0X0073CEC0', '0X006D8DB0', '0X005F4B10', '0X004DAF10', '0X006D97D0', '0X006D9920'}
    if tokens.intersection(c1_addrs) or 'H-VXL' in symbol or 'H-FX' in symbol:
        if any(a in tokens for a in ['0X0073B0B0', '0X0073B470', '0X0073CEC0', '0X006D8DB0', '0X005F4B10', '0X004DAF10']):
            return "CONFLICT_1_VXL_FX_CHAIN"

    # 冲突 2: 虚表槽 69 ObjectClass::Draw 族
    c2_addrs = {
        '0X007E47F8', '0X007E3FD0', '0X007F5D84', '0X007EB16C', '0X007E23B8',
        '0X007EFA68', '0X007EFCB0', '0X007E3468', '0X007F6D08', '0X007F642C',
        '0X00468090', '0X0043D290', '0X0073CEC0', '0X00518F90', '0X004144B0',
        '0X0062CEC0', '0X0062E280', '0X00422CA0', '0X0075F9F0', '0X00749B70'
    }
    if slot == '69' or tokens.intersection(c2_addrs):
        return "CONFLICT_2_SLOT_69_DRAW"

    # 冲突 3: 寻敌 Greatest_Threat Inline Hook vs 虚表劫持 (0x006F8DF0)
    c3_addrs = {'0X006F8DF0', '0X007F4D24', '0X007F6034', '0X00743190', '0X00445F00', '0X0051E140', '0X004D9920', '0X00412B40', '0X00887888'}
    if tokens.intersection(c3_addrs) or 'GREATEST_THREAT' in symbol.upper():
        return "CONFLICT_3_TARGETING_THREAT"

    # 冲突 4: 视口刷新 0x006D3D99
    c4_addrs = {'0X006D3D99', '0X006D3E37', '0X006DA7D0', '0X00486E70', '0X006D2790', '0X006D3D10'}
    if tokens.intersection(c4_addrs) or '0X006D3D99' in tokens:
        return "CONFLICT_4_VIEWPORT_REDRAW"

    # 冲突 5: 雷达小地图 DrawCell 点过滤 vs RadarPlot_Cell 代理覆写
    c5_addrs = {'0X00655F48', '0X006574C3', '0X00655C50', '0X0065719A', '0X00655DEB', '0X0065336D'}
    if tokens.intersection(c5_addrs) or 'RADAR' in symbol.upper() and any(a in tokens for a in ['0X00655F48', '0X006574C3', '0X00655C50']):
        return "CONFLICT_5_MINIMAP_RADAR"

    # 冲突 6: 裂缝保护与超武间谍卫星
    c6_addrs = {'0X00568273', '0X00577EC5', '0X00577B60', '0X00A83C68', '0X006CD70C', '0X004555D0', '0X006FB170', '0X006FB470'}
    if tokens.intersection(c6_addrs) or 'GAP' in symbol.upper():
        return "CONFLICT_6_GAP_SPYSAT"

    return "STANDALONE"

def deduplicate_and_enrich(records):
    unique_map = {}
    for r in records:
        key = (r["symbol"], r["primary_address"], r["source_doc"], r["source_line"])
        if key not in unique_map:
            unique_map[key] = r
    return list(unique_map.values())

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    raw_records = scan_markdown_files()
    deduped = deduplicate_and_enrich(raw_records)

    subsystem_counts = {}
    status_counts = {}
    conflict_counts = {}

    for r in deduped:
        subsystem_counts[r["subsystem"]] = subsystem_counts.get(r["subsystem"], 0) + 1
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
        conflict_counts[r["conflict_group"]] = conflict_counts.get(r["conflict_group"], 0) + 1

    out_file = os.path.join(OUT_DIR, "hooks.json")
    payload = {
        "metadata": {
            "total_extracted_hooks": len(deduped),
            "source_documents_count": 24,
            "subsystem_distribution": subsystem_counts,
            "status_distribution": status_counts,
            "conflict_group_distribution": conflict_counts,
        },
        "hooks": deduped
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    sys.stdout.reconfigure(encoding='utf-8')
    print("Hook 提取完成！")
    print(f"有效扫描文档数: 24")
    print(f"提取 Hook 建议总数: {len(deduped)}")
    print(f"状态统计: {status_counts}")
    print(f"子系统分布: {subsystem_counts}")
    print(f"冲突组统计: {conflict_counts}")
    print(f"已保存至: {out_file}")

if __name__ == "__main__":
    main()
