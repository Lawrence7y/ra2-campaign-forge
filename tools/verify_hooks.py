#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_hooks.py — 已装 Hook 静态覆盖率自证脚本（只读）

对 ra2render/blitter_hooks.cpp + ra2render.h + ra2render.ini 做静态计数：
  1. Hook 实现符号（Hook_* / *_Stub / *_Proxy）清单
  2. PatchVTablePointer 安装点 vs RemoveVTableHooks 还原点（Install/Remove 对称）
  3. Inline patch 区（s_orig*Bytes）备份/还原对称
  4. ini 开关键 vs LoadConfig GetPrivateProfileIntA 读取键
  5. v1.6.0 四键（EnableBuildingFog / EnableBulletFog / FadeFogTransition / EnableMinimapFog）强制覆盖检查
  6. 「定义但未安装」/「装了但 Remove 未还原」候选清单

用法（只读，不写任何游戏/源码文件）：
  python tools/verify_hooks.py
  python tools/verify_hooks.py --json out/re_work/hook_audit/verify_hooks.json

退出码：0 = 覆盖率自证通过；1 = 发现缺口/不对称；2 = 输入文件缺失。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CPP = ROOT / "ra2render" / "blitter_hooks.cpp"
HDR = ROOT / "ra2render" / "ra2render.h"
INI = ROOT / "ra2render" / "ra2render.ini"
INI_COPY = ROOT / "ra2youli" / "ra2render.ini"

# v1.6.0 强制覆盖的四键
V160_KEYS = [
    "EnableBuildingFog",
    "EnableBulletFog",
    "FadeFogTransition",
    "EnableMinimapFog",
]


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def extract_hook_impls(cpp: str) -> list[dict]:
    """Hook 实现符号：类内 Hook_*、裸函数 *Proxy/*Stub。"""
    pat = re.compile(
        r"^(?:void(?:\s+__thiscall|\s+__stdcall)?|void\*\s+__thiscall)\s+"
        r"(?:\w+::)?(Hook_\w+)\s*\(",
        re.M,
    )
    naked = re.compile(r"__declspec\(naked\)\s+void\s+(\w+)\s*\(")
    names: list[str] = []
    for m in pat.finditer(cpp):
        names.append(m.group(1))
    for m in naked.finditer(cpp):
        names.append(m.group(1))
    # 去重保序
    seen: set[str] = set()
    out: list[dict] = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append({"symbol": n})
    return out


def extract_vtable_installs(cpp: str) -> list[dict]:
    """InstallVTableHooks 内的 PatchVTablePointer 调用。"""
    body_m = re.search(
        r"bool\s+InstallVTableHooks\s*\(\s*\)\s*\{(.*?)\n\}", cpp, re.S
    )
    if not body_m:
        return []
    body = body_m.group(1)
    calls = re.findall(
        r"PatchVTablePointer\s*\(\s*([^,]+),\s*([^,]+),\s*[^,]+,\s*\"([^\"]+)\"\s*\)",
        body,
    )
    out = []
    for target, hook_expr, name in calls:
        out.append(
            {
                "name": name.strip(),
                "target_expr": " ".join(target.split()),
                "hook_expr": " ".join(hook_expr.split()),
            }
        )
    return out


def extract_vtable_removes(cpp: str) -> list[dict]:
    """RemoveVTableHooks 内的还原 PatchVTablePointer 调用。"""
    body_m = re.search(
        r"void\s+RemoveVTableHooks\s*\(\s*\)\s*\{(.*?)\n\}", cpp, re.S
    )
    if not body_m:
        return []
    body = body_m.group(1)
    calls = re.findall(
        r"PatchVTablePointer\s*\(\s*([^,]+),\s*[^,]+,\s*nullptr,\s*\"([^\"]+)\"\s*\)",
        body,
    )
    out = []
    for target, name in calls:
        out.append({"name": name.strip(), "target_expr": " ".join(target.split())})
    return out


def extract_inline_pairs(cpp: str) -> list[dict]:
    """Inline patch：s_orig*Bytes 备份 + 对应 Remove 里的 memcpy 还原。"""
    save_pats = re.findall(
        r"memcpy\(\s*(s_orig\w+)\s*,", cpp
    )
    restore_pats = re.findall(
        r"memcpy\(\s*(?:reinterpret_cast<[^>]+>\([^)]+\)|[^,]+)\s*,\s*(s_orig\w+)\s*,",
        cpp,
    )
    saves = sorted(set(save_pats))
    restores = sorted(set(restore_pats))
    return [
        {
            "backup_var": s,
            "saved": s in saves,
            "restored": s in restores,
        }
        for s in saves
    ]


def extract_install_remove_fns(cpp: str) -> dict:
    """成对的 static bool Install* / static void Remove*。"""
    installs = re.findall(r"static\s+bool\s+(Install\w+)\s*\(\s*\)", cpp)
    removes = re.findall(r"static\s+void\s+(Remove\w+)\s*\(\s*\)", cpp)
    return {"installs": installs, "removes": removes}


def extract_ini_keys(ini_text: str) -> dict[str, list[str]]:
    keys: dict[str, list[str]] = {}
    section = "(top)"
    for line in ini_text.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        sm = re.match(r"\[(.+)\]", line)
        if sm:
            section = sm.group(1)
            keys.setdefault(section, [])
            continue
        km = re.match(r"([A-Za-z0-9_]+)\s*=", line)
        if km:
            keys.setdefault(section, []).append(km.group(1))
    return keys


def extract_loadconfig_reads(cpp: str) -> list[str]:
    """提取「被读取的 ini 键」。

    [Lead 2026-09-28 修订] 原实现只在 LoadConfig() 体内找 `GetPrivateProfileIntA(sec, key)`，
    漏掉本项目实际使用的助手函数 `GetIniStringEx` / `GetIniIntEx`（23 处调用，内部再调
    `GetPrivateProfileStringA`）⇒ 20 个键被误报「ini 提供但读取处不读」，产生**假 FAIL**
    （ZC-10B 交付时即被此假 FAIL 拖累，须自证"与本卡无关"）。

    现口径：① 全文件扫 `GetPrivateProfileIntA/StringA` 的字面键；② 全文件扫
    `GetIni{String,Int}Ex(sec, key, ...)` 的第二个字符串实参；③ 保留 LoadConfig 体内扫描（向后兼容）。

    边界声明：本函数只回答「有没有读取点」，**不回答**「读到的值是否被实际使用」——后者属真机验收范围。
    """
    keys: list[str] = []
    body_m = re.search(r"void\s+LoadConfig\s*\(\s*\)\s*\{(.*?)\n\}", cpp, re.S)
    if body_m:
        keys += re.findall(r"GetPrivateProfileIntA\s*\(\s*\"[^\"]+\"\s*,\s*\"([^\"]+)\"", body_m.group(1))
    keys += re.findall(r"GetPrivateProfileIntA\s*\(\s*\"[^\"]+\"\s*,\s*\"([^\"]+)\"", cpp)
    keys += re.findall(r"GetPrivateProfileStringA\s*\(\s*\"[^\"]+\"\s*,\s*\"([^\"]+)\"", cpp)
    keys += re.findall(r"GetIni(?:String|Int)Ex\s*\(\s*\"[^\"]+\"\s*,\s*\"([^\"]+)\"", cpp)
    return sorted(set(keys))


def extract_header_addrs(hdr: str) -> list[dict]:
    return [
        {"name": m.group(1), "addr": m.group(2)}
        for m in re.finditer(r"#define\s+(ADDR_\w+)\s+(0x[0-9A-Fa-f]+)", hdr)
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="已装 Hook 静态覆盖率自证（只读）")
    ap.add_argument("--json", dest="json_out", help="额外输出 JSON 报告路径")
    args = ap.parse_args()

    for p in (CPP, HDR, INI):
        if not p.is_file():
            print(f"[FATAL] 缺少输入文件: {p}", file=sys.stderr)
            return 2

    cpp = read_text(CPP)
    hdr = read_text(HDR)
    ini = read_text(INI)

    hook_impls = extract_hook_impls(cpp)
    vt_installs = extract_vtable_installs(cpp)
    vt_removes = extract_vtable_removes(cpp)
    inline_pairs = extract_inline_pairs(cpp)
    fns = extract_install_remove_fns(cpp)
    ini_keys = extract_ini_keys(ini)
    cfg_reads = extract_loadconfig_reads(cpp)
    addrs = extract_header_addrs(hdr)

    flat_ini_keys = sorted({k for ks in ini_keys.values() for k in ks})
    # LoadConfig 读取但 ini 未提供的键（有默认值，算软缺口）
    missing_in_ini = sorted(set(cfg_reads) - set(flat_ini_keys))
    # ini 提供但 LoadConfig 不读的键
    unused_in_cfg = sorted(set(flat_ini_keys) - set(cfg_reads))

    # Install/Remove 对称：按 target_expr 配对
    inst_targets = {e["target_expr"]: e["name"] for e in vt_installs}
    rem_targets = {e["target_expr"]: e["name"] for e in vt_removes}
    installed_not_removed = sorted(set(inst_targets) - set(rem_targets))
    removed_not_installed = sorted(set(rem_targets) - set(inst_targets))

    # Inline 对称
    inline_unrestored = [p["backup_var"] for p in inline_pairs if p["saved"] and not p["restored"]]

    # Install*/Remove* 函数名对称
    inst_names = set(fns["installs"])
    rem_names = {n.replace("Remove", "Install", 1) for n in fns["removes"]}
    pair_missing_remove = sorted(inst_names - rem_names)
    pair_missing_install = sorted(rem_names - inst_names)

    # v1.6.0 四键
    v160_status = []
    for k in V160_KEYS:
        in_ini = k in flat_ini_keys
        in_cfg = k in cfg_reads
        v160_status.append({"key": k, "in_ini": in_ini, "in_loadconfig": in_cfg, "ok": in_ini and in_cfg})

    # 「定义但未安装」：header ADDR_VTABLE_ENTRY_* 是否出现在 InstallVTableHooks
    vt_entry_defs = [a for a in addrs if "VTABLE_ENTRY" in a["name"]]
    used_targets = " ".join(e["target_expr"] for e in vt_installs)
    defined_not_installed = []
    for a in vt_entry_defs:
        if a["name"] not in used_targets and a["addr"].lower() not in used_targets.lower():
            # 还要检查源码里是否被引用（inline 可能直接用 ADDR_ORIG_*）
            if a["name"] not in cpp:
                defined_not_installed.append(a)

    # 宏名被引用但不在 InstallVTableHooks（可能是 inline / 死代码）
    addr_refs: dict[str, int] = {}
    for a in addrs:
        addr_refs[a["name"]] = len(re.findall(rf"\b{a['name']}\b", cpp))

    report = {
        "inputs": {
            "cpp": str(CPP.relative_to(ROOT)),
            "hdr": str(HDR.relative_to(ROOT)),
            "ini": str(INI.relative_to(ROOT)),
            "ini_copy": str(INI_COPY.relative_to(ROOT)),
            "ini_copy_exists": INI_COPY.is_file(),
        },
        "counts": {
            "hook_impl_symbols": len(hook_impls),
            "vtable_patch_installs": len(vt_installs),
            "vtable_patch_removes": len(vt_removes),
            "inline_backup_vars": len(inline_pairs),
            "ini_keys": len(flat_ini_keys),
            "loadconfig_reads": len(cfg_reads),
            "header_addr_defines": len(addrs),
            "install_fns": len(fns["installs"]),
            "remove_fns": len(fns["removes"]),
        },
        "hook_impls": hook_impls,
        "vtable_installs": vt_installs,
        "vtable_removes": vt_removes,
        "inline_pairs": inline_pairs,
        "install_remove_fns": fns,
        "ini_keys_by_section": ini_keys,
        "loadconfig_reads": cfg_reads,
        "missing_in_ini": missing_in_ini,
        "unused_in_cfg": unused_in_cfg,
        "installed_not_removed": installed_not_removed,
        "removed_not_installed": removed_not_installed,
        "inline_unrestored": inline_unrestored,
        "pair_missing_remove": pair_missing_remove,
        "pair_missing_install": pair_missing_install,
        "v160_keys": v160_status,
        "header_addrs_unused_in_cpp": [
            a["name"] for a in addrs if addr_refs.get(a["name"], 0) == 0
        ],
        "defined_vtable_entry_not_in_install": defined_not_installed,
    }

    # ---- 控制台摘要 ----
    print("=" * 72)
    print("ra2render 已装 Hook 静态覆盖率自证 (verify_hooks.py)")
    print("=" * 72)
    print(f"Hook 实现符号        : {report['counts']['hook_impl_symbols']}")
    print(f"虚表安装 / 还原调用  : {report['counts']['vtable_patch_installs']} / {report['counts']['vtable_patch_removes']}")
    print(f"Inline 备份变量      : {report['counts']['inline_backup_vars']}")
    print(f"ini 键 / LoadConfig  : {report['counts']['ini_keys']} / {report['counts']['loadconfig_reads']}")
    print(f"Install* / Remove*   : {report['counts']['install_fns']} / {report['counts']['remove_fns']}")
    print("-" * 72)

    ok = True

    print("[1] 虚表 Install/Remove 对称")
    if installed_not_removed:
        ok = False
        for t in installed_not_removed:
            print(f"    !! 装了未还原: {t} ({inst_targets[t]})")
    else:
        print(f"    OK  {len(vt_installs)} 个虚表槽均有对应还原")
    if removed_not_installed:
        ok = False
        for t in removed_not_installed:
            print(f"    !! 还原了但未安装: {t} ({rem_targets[t]})")

    print("[2] Inline 备份/还原对称 (s_orig*Bytes)")
    if inline_unrestored:
        ok = False
        for v in inline_unrestored:
            print(f"    !! 备份未见还原 memcpy: {v}")
    else:
        print(f"    OK  {len(inline_pairs)} 个备份变量均有还原路径")

    print("[3] Install*/Remove* 函数配对")
    if pair_missing_remove:
        ok = False
        for n in pair_missing_remove:
            print(f"    !! 有 {n} 无对应 Remove")
    if pair_missing_install:
        ok = False
        for n in pair_missing_install:
            print(f"    !! 有 {n} 无对应 Install")
    if not pair_missing_remove and not pair_missing_install:
        print(f"    OK  {len(fns['installs'])} 对 Install/Remove 配对完整")

    print("[4] ini 键 vs LoadConfig")
    if missing_in_ini:
        ok = False
        print(f"    !! LoadConfig 读取但 ini 未列出: {missing_in_ini}")
    if unused_in_cfg:
        ok = False
        print(f"    !! ini 提供但 LoadConfig 不读: {unused_in_cfg}")
    if not missing_in_ini and not unused_in_cfg:
        print(f"    OK  {len(flat_ini_keys)} 键双向对齐")

    print("[5] v1.6.0 四键强制覆盖")
    for s in v160_status:
        flag = "OK " if s["ok"] else "!! "
        print(f"    {flag}{s['key']}: ini={s['in_ini']} loadconfig={s['in_loadconfig']}")
        if not s["ok"]:
            ok = False

    print("[6] 头文件 ADDR_* 在 cpp 零引用（死宏/仅头文件注释）")
    unused = report["header_addrs_unused_in_cpp"]
    if unused:
        for n in unused:
            print(f"    ?  {n}  (头文件定义，cpp 未引用——死宏或待接线)")
        # 死宏本身不判失败，列入「装了但可能没生效」候选
    else:
        print("    OK  无零引用 ADDR_* 宏")

    print("-" * 72)
    print(f"结论: {'PASS' if ok else 'FAIL（存在缺口/不对称，见上）'}")
    print("=" * 72)

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON 报告: {out}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
