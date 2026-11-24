# -*- coding: utf-8 -*-
"""
独立复核员·T2 专享复核探针
零真机、纯只读反汇编核查
核实 T2 回件中给出的每一个指令数、地址、偏移与逻辑结论
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
    print("[1] 镜像自验...")
    with open(EXE_PATH, "rb") as f:
        data = f.read()
    size = len(data)
    h = hashlib.sha256(data).hexdigest()
    print(f"  gamemd.exe size={size}, sha256={h}")
    assert size == 4825360
    assert h == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"

    print("[2] 初始化 Engine (单次建流)...")
    eng = Engine(EXE_PATH)
    cov, n_ins, resync = eng.coverage
    print(f"  Coverage: {cov:.4f}%, insns={n_ins}, resync={resync}, IB=0x{eng.IB:X}")

    print("[3] 核实 DrawIfVisible 0x005F4B10 .. 0x005F4D10")
    succ, seq = eng._edges(0x5F4B10, 0x5F4D10)
    print(f"  DrawIfVisible insn count: {len(seq)}, bytes: {sum(i.size for i in seq)}")
    rets, _ = eng.func_rets(0x5F4B10, 0x5F4D10)
    ret_addrs = [f"0x{r.address:08X}" for r in rets]
    print(f"  DrawIfVisible rets: {ret_addrs}")

    # DFS path search
    def dfs_paths(target):
        res = []
        def dfs(cur, path):
            if cur == target:
                res.append(path + [cur])
                return
            for nxt in succ.get(cur, []):
                if nxt not in path:
                    dfs(nxt, path + [cur])
        dfs(0x5F4B10, [])
        return res

    succ_paths = dfs_paths(0x5F4D0C)
    cull_paths = dfs_paths(0x5F4B85)
    print(f"  DrawIfVisible success paths count: {len(succ_paths)}")
    lens_s = [len(p) for p in succ_paths]
    print(f"    min={min(lens_s)}, max={max(lens_s)}, avg={sum(lens_s)/len(lens_s):.2f}")
    print(f"  DrawIfVisible cull paths count: {len(cull_paths)}")
    lens_c = [len(p) for p in cull_paths]
    print(f"    min={min(lens_c)}, max={max(lens_c)}, avg={sum(lens_c)/len(lens_c):.2f}")

    print("[4] 核实 TacticalClass::IsVisible 0x006D2140 .. 0x006D2275")
    succ_iv, seq_iv = eng._edges(0x6D2140, 0x6D2275)
    print(f"  IsVisible insn count: {len(seq_iv)}, bytes: {sum(i.size for i in seq_iv)}")
    rets_iv, _ = eng.func_rets(0x6D2140, 0x6D2275)
    ret_iv_addrs = [f"0x{r.address:08X}" for r in rets_iv]
    print(f"  IsVisible rets: {ret_iv_addrs}")

    def dfs_iv(target):
        res = []
        def dfs(cur, path):
            if cur == target:
                res.append(path + [cur])
                return
            for nxt in succ_iv.get(cur, []):
                if nxt not in path:
                    dfs(nxt, path + [cur])
        dfs(0x6D2140, [])
        return res

    iv_succ = dfs_iv(0x6D226F)
    print(f"  IsVisible on-screen (0x6D226F) path count: {len(iv_succ)}, lens={[len(p) for p in iv_succ]}")
    for r in [0x6D2231, 0x6D2249, 0x6D2258]:
        p_c = dfs_iv(r)
        print(f"  IsVisible cull (0x{r:08X}) path count: {len(p_c)}, lens={[len(p) for p in p_c]}")

    print("[5] 核实 UnitClass::Draw 0x0073CEC0 .. 0x0073D450")
    succ_ud, seq_ud = eng._edges(0x73CEC0, 0x73D450)
    calls_ud = [i for i in seq_ud if i.mnemonic == "call"]
    print(f"  UnitClass::Draw insn count: {len(seq_ud)}, bytes: {sum(i.size for i in seq_ud)}, calls count: {len(calls_ud)}")

    print("[6] 核实 A39 勘误相关：0x6D8DB0 循环、0x6D909E 虚调用与 UnitClass 虚表")
    by = eng.by()
    # 检查 0x6D909E 的指令
    ins_call = by[0x6D909E]
    print(f"  0x6D909E: {ins_call.bytes.hex()} {ins_call.mnemonic} {ins_call.op_str}")
    assert ins_call.mnemonic == "call" and "[edx + 0x104]" in ins_call.op_str

    # 检查 UnitClass 虚表 0x007F5C70 + 0x104
    slot65 = eng.u32(0x7F5C70 + 0x104)
    print(f"  UnitClass vtable + 0x104 (0x{0x7F5C70 + 0x104:08X}) = 0x{slot65:08X}")
    assert slot65 == 0x73B0B0

    # 检查 UnitClass::DrawIfVisible (0x73B0B0)
    succ_ub, seq_ub = eng._edges(0x73B0B0, 0x73B140)
    calls_ub = [i for i in seq_ub if i.mnemonic == "call"]
    print(f"  UnitClass::DrawIfVisible calls: {[f'0x{c.address:08X}: call {c.op_str}' for c in calls_ub]}")
    assert any(c.address == 0x73B132 and "0x5f4b10" in c.op_str.lower() for c in calls_ub)

    print(f"[7] 全部核实完成，耗时: {time.time() - t0:.2f}s")

if __name__ == "__main__":
    main()
