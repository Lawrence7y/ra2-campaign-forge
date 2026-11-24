#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lead 独立核查：gamemd.exe 的对话框创建路径。

目的：为 W87 的 R1（运行时改模板）提供**独立于子卡**的前提事实：
  1. gamemd 是否从 user32 导入 DialogBoxParam* / CreateDialogIndirectParam* / CreateDialogParam*；
  2. 这些 import 的 IAT 槽 VA 各是多少；
  3. .text 里有哪些 `call dword ptr [IAT槽]`（或间接）调用点，各自 VA + 字节。

不做任何写操作，只读 ra2bench/gamemd.exe 的副本。
"""
import sys
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs

EXE = Path(r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe")
WANTED = (
    "DialogBoxParamA",
    "DialogBoxParamW",
    "DialogBoxIndirectParamA",
    "DialogBoxIndirectParamW",
    "CreateDialogIndirectParamA",
    "CreateDialogIndirectParamW",
    "CreateDialogParamA",
    "CreateDialogParamW",
    "CreateDialogIndirectA",
    "CreateDialogIndirectW",
)


def main() -> int:
    data = EXE.read_bytes()
    pe = pefile.PE(data=data, fast_load=False)
    image_base = pe.OPTIONAL_HEADER.ImageBase
    print(f"file={EXE} bytes={len(data)} image_base=0x{image_base:08X}")
    print(f"entry=0x{image_base + pe.OPTIONAL_HEADER.AddressOfEntryPoint:08X}")

    hits = {}
    for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []) or []:
        dll = entry.dll.decode("ascii", "replace")
        for imp in entry.imports:
            if not imp.name:
                continue
            name = imp.name.decode("ascii", "replace")
            if name in WANTED:
                # imp.address 已经是 VA（pefile 给的是 IAT 槽的虚拟地址，含 ImageBase）
                hits[name] = {"dll": dll, "iat_va": imp.address, "hint": imp.hint}
                print(f"IMPORT {name:28s} dll={dll:16s} IAT_VA=0x{imp.address:08X} hint={imp.hint}")

    if not hits:
        print("!! 未在导入表找到任何 DialogBoxParam*/CreateDialog* 系列")
        return 0

    # 反汇编 .text，找 call [iat] 与 mov reg,[iat] / push 之前的注册用法
    text = None
    for s in pe.sections:
        n = s.Name.rstrip(b"\x00").decode("ascii", "replace")
        if n == ".text":
            text = s
            break
    if text is None:
        print("!! 无 .text")
        return 1
    base_va = image_base + text.VirtualAddress
    blob = text.get_data()
    print(f".text VA=0x{base_va:08X} size={len(blob)}")

    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True

    iat_to_name = {v["iat_va"]: k for k, v in hits.items()}
    call_sites = {k: [] for k in hits}
    # 遍历全部指令（线性扫描；只用于找 IAT 引用，不做 CFG）
    n_insn = 0
    for insn in md.disasm(blob, base_va):
        n_insn += 1
        for op in insn.operands:
            if op.type == 3 and op.mem.base == 0 and op.mem.index == 0:  # X86_OP_MEM, absolute
                target = op.mem.disp
                name = iat_to_name.get(target)
                if name:
                    call_sites[name].append(
                        {
                            "va": insn.address,
                            "file_off": insn.address - base_va,
                            "mnemonic": insn.mnemonic,
                            "op_str": insn.op_str,
                            "bytes": insn.bytes.hex(),
                        }
                    )
    print(f"scanned instructions={n_insn}")
    for name in hits:
        sites = call_sites[name]
        print(f"\n### {name}  refs={len(sites)}")
        for s in sites[:40]:
            print(
                f"  0x{s['va']:08X} (off 0x{s['file_off']:06X})  {s['mnemonic']} {s['op_str']}   [{s['bytes']}]"
            )
        if len(sites) > 40:
            print(f"  ... 还有 {len(sites)-40} 处")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
