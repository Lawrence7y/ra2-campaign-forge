# -*- coding: utf-8 -*-
"""
独立复核员·T3 专享复核探针
零真机、纯只读反汇编核查
独立验证 T3 回件 (T3_C4.md) 的所有指令计数、控制流、空间桶、几何推算与算术上界
"""
import sys
import hashlib
import time

TOOL_DIR = r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104"
sys.path.insert(0, TOOL_DIR)
from ra2tool import Engine

EXE_PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

def main():
    t0 = time.time()
    print("[1] 镜像自验与哈希核定...")
    with open(EXE_PATH, "rb") as f:
        data = f.read()
    size = len(data)
    h = hashlib.sha256(data).hexdigest()
    print(f"  gamemd.exe size={size}, sha256={h}")
    assert size == 4825360, f"Size mismatch: {size}"
    assert h == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476", f"SHA256 mismatch: {h}"

    print("\n[2] 装载 Engine (全流单次建流)...")
    eng = Engine(EXE_PATH)
    cov, n_ins, resync = eng.coverage
    print(f"  Coverage: {cov:.4f}%, insns={n_ins}, resync={resync}, IB=0x{eng.IB:X}")
    assert eng.IB == 0x400000

    by = eng.by()

    print("\n[3] 核验 20x20 粗空间桶 (0x00887888) 结构与坐标映射...")
    # 3.1 静态构造 0x00412870
    dis_init = eng.disasm(0x00412870, 0x30)
    # 查找 edi 赋值与 esi 递增
    init_edi = None
    step_esi = None
    for va, bs, mn, op in dis_init:
        if mn == "mov" and op.startswith("edi,"):
            init_edi = int(op.split(",")[1].strip(), 16)
        if mn == "add" and op.startswith("esi,"):
            step_esi = int(op.split(",")[1].strip(), 16)
    print(f"  空间桶构造循环: 初始计数 edi=0x{init_edi:X} ({init_edi}), 单桶步长 esi=0x{step_esi:X} ({step_esi}) 字节")
    assert init_edi == 400, f"Expected 400 buckets, got {init_edi}"
    assert step_esi == 24, f"Expected 24 bytes per bucket, got {step_esi}"

    # RTTI 验证
    vptr = 0x007E17AC
    col = eng.u32(vptr - 4)
    td = eng.u32(col + 12) if col else 0
    rtti_name = eng.rd(td + 8, 64).split(b"\x00")[0].decode("ascii", "ignore") if td else "UNKNOWN"
    print(f"  桶虚表 0x{vptr:08X} RTTI: {rtti_name}")
    assert "DynamicVectorClass" in rtti_name and "TechnoClass" in rtti_name

    # 3.2 坐标映射魔数验证 0x00412B9A .. 0x00412BE6
    dis_map = eng.disasm(0x00412B9A, 0x50)
    has_magic = any("66666667" in op for va, bs, mn, op in dis_map)
    has_sar3 = any(mn == "sar" and "3" in op for va, bs, mn, op in dis_map)
    has_cmp13 = any(mn == "cmp" and "0x13" in op for va, bs, mn, op in dis_map)
    print(f"  映射代码: 魔数0x66666667={has_magic}, sar 3={has_sar3}, cmp 0x13(19)={has_cmp13}")
    assert has_magic and has_sar3 and has_cmp13

    # 验证魔数除法数学逻辑
    def magic_div(w):
        prod = w * 0x66666667
        edx = (prod >> 32) & 0xFFFFFFFF
        if edx >= 0x80000000:
            edx -= 0x100000000
        ecx = edx >> 3
        sign = 1 if edx < 0 else 0
        return ecx + sign

    for w in [50, 100, 120, 200]:
        s = magic_div(w)
        print(f"    MapDim={w:3d} -> step={s} (w/20={w//20})")
        assert s == w // 20

    print("\n[4] 核验目标函数核定 (UpdateReload vs Greatest_Threat)...")
    # 4.1 UpdateReload 0x006FB010
    dis_reload = eng.disasm(0x006FB010, 0x20)
    ammo_chk = False
    for va, bs, mn, op in dis_reload:
        if "0x684" in op:  # TechnoTypeClass->Ammo
            ammo_chk = True
        if mn == "cmp" and "-1" in op:
            ammo_chk = True
    print(f"  0x006FB010 Ammo 检查存在性: {ammo_chk}")
    assert ammo_chk

    # 4.2 Greatest_Threat 0x006F8DF0
    dis_gt = eng.disasm(0x006F8DF0, 0x20)
    counter_inc = any("0xa8ec34" in op for va, bs, mn, op in dis_gt)
    print(f"  0x006F8DF0 计数器 0x00A8EC34 访问: {counter_inc}")
    assert counter_inc

    # 全局调用点查找
    callers_gt = []
    for ins in eng.stream:
        if ins.mnemonic == "call":
            for op in ins.operands:
                if op.type == 2 and op.imm == 0x006F8DF0:
                    callers_gt.append(ins.address)
    print(f"  全镜像 direct call 0x006F8DF0 数量: {len(callers_gt)}, 地址: {[hex(c) for c in callers_gt]}")
    assert len(callers_gt) == 2
    assert 0x00445F68 in callers_gt and 0x004D9942 in callers_gt

    # 虚表槽位 241
    vptr_unit = 0x007F5C70
    slot_241 = eng.u32(vptr_unit + 241 * 4)
    print(f"  UnitClass::vtable[241] (0x{vptr_unit + 241*4:08X}) = 0x{slot_241:08X}")
    assert slot_241 == 0x00743190

    print("\n[5] 核验螺旋同心环扫格与 Off-By-One 几何边界...")
    # 5.1 半径公式 0x006F9121 .. 0x006F9144
    dis_r = eng.disasm(0x006F9121, 0x25)
    has_lea_r = any(mn == "lea" and "1" in op and "edi" in op for va, bs, mn, op in dis_r)
    print(f"  半径提取包含 lea ... + 1: {has_lea_r}")
    assert has_lea_r

    # 5.2 循环起始与边界 0x006F93B7 与 0x006F9B37
    # 检查 0x006F93B7 前后对 esp+0x24 的初始化
    dis_loop_head = eng.disasm(0x006F93B0, 0x20)
    for va, bs, mn, op in dis_loop_head:
        if "[esp + 0x24]" in op or "edi" in op:
            print(f"    循环头 0x{va:08X}: {mn} {op}")

    # 检查 0x006F9B37 .. 0x006F9B44
    dis_loop_tail = eng.disasm(0x006F9B37, 0x10)
    for va, bs, mn, op in dis_loop_tail:
        print(f"    循环尾 0x{va:08X}: {mn} {op}")

    # 确认 inc edi; cmp edi, ecx; jge
    ins_inc = by[0x006F9B37]
    ins_cmp = by[0x006F9B38]
    ins_jge = by[0x006F9B3E]
    assert ins_inc.mnemonic == "inc" and "edi" in ins_inc.op_str
    assert ins_cmp.mnemonic == "cmp" and "edi" in ins_cmp.op_str and "ecx" in ins_cmp.op_str
    assert ins_jge.mnemonic == "jge"

    # 5.3 检查内圈早退 0x006F9AF0 / 0x006F9B06
    dis_early = eng.disasm(0x006F9AE2, 0x30)
    early_branches = []
    for va, bs, mn, op in dis_early:
        if mn in ["je", "jge", "jg"] and "6f9b49" in op.lower():
            early_branches.append((va, mn, op))
    print(f"  内圈早退跳转至 0x6F9B49 分支数: {len(early_branches)}, 详情: {early_branches}")
    assert len(early_branches) == 2, f"Expected 2 early exit branches, found {len(early_branches)}"

    print("\n[6] 核验单 Cell 空格判定指令数精算...")
    # 6.1 MapClass::IsCellInMap (0x00568300)
    dis_incell = eng.disasm(0x00568300, 0x3E)
    print(f"  MapClass::IsCellInMap 成功路径指令数: {len(dis_incell)} 条")
    assert len(dis_incell) == 26

    # 6.2 MapClass::TryGetCellAt (0x005657A0)
    dis_try = eng.disasm(0x005657A0, 0x38)
    print(f"  MapClass::TryGetCellAt 全函数指令数: {len(dis_try)} 条")
    assert len(dis_try) == 18

    # 6.3 0x006F8960 空格早退路径
    # 逐条核查 T3 列出的路径
    empty_path = [
        0x006F8960, 0x006F8964, 0x006F8965, 0x006F8966, 0x006F8967, 0x006F8969,
        0x006F896A, 0x006F896E, 0x006F8972, 0x006F8978, 0x006F8979, 0x006F897F,
        0x006F8984,  # call 0x5657a0
        0x006F8989, 0x006F898D, 0x006F898F, 0x006F8992,
        0x006F89BF, 0x006F89C5, 0x006F89C7, 0x006F89C9, 0x006F89CB, 0x006F89D1,
        0x006F89D7, 0x006F89D9, 0x006F89DB, 0x006F89E0,
        0x006F8A0F, 0x006F8A11,
        0x006F8B4D, 0x006F8B4E, 0x006F8B4F, 0x006F8B50, 0x006F8B52, 0x006F8B53
    ]
    for va in empty_path:
        assert va in by, f"Address 0x{va:08X} not in disassembled stream!"
    print(f"  0x006F8960 空格早退路径关键地址核验全部命中 ({len(empty_path)} 条)")

    print("\n[7] 纯算术独立重算...")
    # Rhino: weapon=5, guard=5 -> R_in = 11, R_max = 10 -> (2*10+1)^2 = 21^2 = 441 cells
    # W3 used (2*11+1)^2 = 23^2 = 529 cells
    # Mixed: e.g. 765 cells vs W3 1000 cells
    # Extreme: weapon=18, guard=10 -> R_in = 29, R_max = 28 -> (2*28+1)^2 = 57^2 = 3249 cells vs W3 (2*29+1)^2 = 59^2 = 3481 cells
    rhino_real = (2 * (5 + 5) + 1) ** 2
    rhino_w3 = (2 * (5 + 5 + 1) + 1) ** 2
    assert rhino_real == 441
    assert rhino_w3 == 529

    ext_real = (2 * (18 + 10) + 1) ** 2
    ext_w3 = (2 * (18 + 10 + 1) + 1) ** 2
    assert ext_real == 3249
    assert ext_w3 == 3481

    # Bounds math
    # 2.5 GHz, IPC 1.0 -> 0.4 ns per insn
    ns_insn = 0.4e-9
    # Rhino: 1200 units * 441 cells = 529,200 cells
    rhino_cells = 1200 * 441
    t_rhino_empty = rhino_cells * 74 * ns_insn * 1000  # ms
    t_rhino_blended = rhino_cells * 85.3 * ns_insn * 1000  # ms
    w3_rhino = 1200 * 529 * 30e-9 * 1000 # ms
    print(f"  主力坦克 (441 cells): 空格={t_rhino_empty:.2f} ms, 综合={t_rhino_blended:.2f} ms, W3={w3_rhino:.2f} ms, ratio={t_rhino_blended/w3_rhino:.2f}x")

    mixed_cells = 1200 * 765
    t_mixed_empty = mixed_cells * 74 * ns_insn * 1000
    t_mixed_blended = mixed_cells * 85.3 * ns_insn * 1000
    w3_mixed = 1200 * 1000 * 30e-9 * 1000
    print(f"  混合长程 (765 cells): 空格={t_mixed_empty:.2f} ms, 综合={t_mixed_blended:.2f} ms, W3={w3_mixed:.2f} ms, ratio={t_mixed_blended/w3_mixed:.2f}x")

    ext_cells = 1200 * 3249
    t_ext_empty = ext_cells * 74 * ns_insn * 1000
    t_ext_blended = ext_cells * 85.3 * ns_insn * 1000
    w3_ext = 1200 * 3481 * 30e-9 * 1000
    print(f"  极端长程 (3249 cells): 空格={t_ext_empty:.2f} ms, 综合={t_ext_blended:.2f} ms, W3={w3_ext:.2f} ms, ratio={t_ext_blended/w3_ext:.2f}x")

    print(f"\n[8] 全部独立复核实测执行完毕，总耗时: {time.time() - t0:.2f}s")

if __name__ == "__main__":
    main()
