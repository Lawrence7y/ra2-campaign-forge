"""函数边界启发式：从 va 向前找对齐/C3/C2/int3 边界，向后找第一个 ret/int3 块或 jmp。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C


def _is_pad(b):
    return b == 0xCC or b == 0x90


def fn_start(va, back=0x400):
    """向前扫：找 padding 块之后的第一条指令，或已解码指令里覆盖 va 的那条函数首。
    简化且安全：返回 <= va 的最大 '候选边界'（C3/C2/int3 之后的对齐点）。"""
    lo = max(C.TLO, va - back)
    # 候选：lo..va 间所有 (ret 结束 + 对齐) 位置
    cands = [lo]
    i = lo
    while i < va:
        b = C.read(i, 1)
        if b is None:
            break
        if b[0] in (0xC3,):
            cands.append(i + 1)
            i += 1
            continue
        if b[0] == 0xC2:
            cands.append(i + 3)
            i += 3
            continue
        if b[0] == 0xCC:
            j = i
            while j < va and (C.read(j, 1) or b"\x00")[0] == 0xCC:
                j += 1
            cands.append(j)
            i = j
            continue
        i += 1
    # 取能线性解码到 va 的最大候选
    best = cands[0]
    for c in sorted(cands):
        if c > va:
            break
        # 线性解码 c..va 是否正好落在 va 边界上
        ok = True
        pos = c
        for ins in C.disasm(c, 10 ** 6, nbytes=va - c + 15):
            if ins.address + ins.size == va:
                ok = True
                break
            if ins.address + ins.size > va:
                ok = False
                break
        else:
            ok = False
        if ok:
            best = c
    return best


def fn_range(va, back=0x400, fwd=0x800):
    lo = fn_start(va, back)
    end = None
    for ins in C.disasm(lo, 10 ** 6, nbytes=lo and (va - lo + fwd)):
        if ins.address + ins.size > va + fwd:
            break
        if ins.mnemonic in ("ret",) or (ins.mnemonic == "ret" ):
            end = ins.address + ins.size
            if ins.address >= va:
                break
    return lo, end


if __name__ == "__main__":
    for s in sys.argv[1:]:
        va = int(s, 16)
        lo, end = fn_range(va)
        print(f"{va:08X}: fn~{lo:08X} .. {end if end is None else format(end, '08X')}")
        print(C.show_range(lo, min((end or va + 0x60) + 1, C.THI), f"window {s}"))
