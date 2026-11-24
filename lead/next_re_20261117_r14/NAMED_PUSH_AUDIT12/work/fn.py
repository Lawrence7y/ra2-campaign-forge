"""函数边界回溯：找到包含某地址的函数起点并线性反汇编（对齐可验证）"""
import rt
from rt import im

def try_disasm_from(start, end, maxn=4000):
    """从 start 线性反汇编，返回指令列表；失败(.byte 出现)返回 None"""
    ins = list(im.dis(start, maxn, stop_ret=False))
    prev = start
    for i in ins:
        if i.address != prev:
            return None
        if i.mnemonic == ".byte":
            return None
        prev = i.address + i.size
        if i.address >= end:
            # 必须精确落在 end 上
            return ins if i.address == end else None
    return None

def func_of(site):
    """回溯找函数起点：优先 55 8B EC 序言"""
    cands = []
    for k in range(0, 3000):
        c = site - k
        if c < 0x401000:
            break
        b = im.rd(c, 3)
        if len(b) == 3 and b[0] == 0x55 and b[1] == 0x8B and b[2] == 0xEC:
            cands.append(c)
    for c in cands:            # 由近到远
        ins = try_disasm_from(c, site)
        if ins:
            return c, ins
    # 兜底：nop 之后的函数起点
    for k in range(1, 3000):
        c = site - k
        b = im.rd(c-1, 3)
        if len(b) == 3 and b[0] == 0x90 and b[1] == 0x90 and b[2] != 0x90:
            ins = try_disasm_from(c, site)
            if ins:
                return c, ins
    return None, None

def last_n_before(site, n=14):
    c, ins = func_of(site)
    if not ins:
        return None, None
    k = [i.address for i in ins].index(site) if site in [i.address for i in ins] else -1
    if k < 0:
        return c, None
    return c, ins[max(0, k-n):]
