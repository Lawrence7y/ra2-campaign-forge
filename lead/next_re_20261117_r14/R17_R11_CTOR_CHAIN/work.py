#!/usr/bin/env python3
# work.py - 可复跑（R17-R11-CTOR-CHAIN）。只读 gamemd.exe，不建进程、不调试。
# 依赖: python3 + capstone (pip install capstone)
import capstone, struct, sys

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
BASE = 0x400000
d = open(EXE, 'rb').read()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True

def hexs(va, n): return ' '.join('%02x' % b for b in d[va-BASE: va-BASE+n])
def u32(va): return struct.unpack_from('<I', d, va-BASE)[0]

def func(va, limit=0x2000, maxn=4000):
    out = []
    for ins in md.disasm(d[va-BASE: va-BASE+limit], va):
        out.append(ins)
        if len(out) >= maxn: break
        if ins.mnemonic in ('ret', 'retn'): break
    return out

def ctorshape(va):
    f = func(va); vts = []
    for i in f:
        if i.mnemonic == 'mov' and '[' in i.op_str:
            t = i.op_str.split(',')[-1].strip()
            if t.startswith('0x'):
                v = int(t, 16)
                if 0x7E0000 <= v < 0x7FF000: vts.append((i.address, v))
    tail = f[-3:] if f else []
    returns_this = any(i.mnemonic == 'mov' and i.op_str == 'eax, esi' for i in tail)
    calls = [(i.address, int(i.op_str, 16)) for i in f if i.mnemonic == 'call' and i.op_str.startswith('0x')]
    return dict(start=f[0].address if f else None, end=f[-1].address if f else None,
                n=len(f), vts=vts, calls=calls, returns_this=returns_this)

def anchors():
    print('--- 锚点 ---')
    print('0x6F2B38 pre-entry fill:', hexs(0x6F2B38, 8))
    print('0x43B67E host1 prev fn tail:', hexs(0x43B67E, 2))
    print('0x43BCDE host2 tail anchor:', hexs(0x43BCDE, 8))

def hosts():
    print('--- host prologues: direct calls ---')
    for va, name, end in ((0x43B680, 'host1', 0x43B740), (0x43B740, 'host2', 0x43BD40), (0x43BCF0, 'host3', 0x43BCF0+0xB0)):
        f = func(va, end-va)
        cs = [(i.address, i.op_str) for i in f if i.mnemonic == 'call']
        print('%s 0x%X: %d calls' % (name, va, len(cs)))
        for a, o in cs: print('   0x%X call %s   bytes=%s' % (a, o, hexs(a, 5)))

def main():
    anchors(); hosts()
    for va in (0x6F2B40, 0x6F4300, 0x65A750, 0x65A7E0, 0x5B2DA0, 0x5F3B50):
        s = ctorshape(va)
        print('== 0x%X n=%d end=0x%X returns_this=%s' % (va, s['n'], s['end'], s['returns_this']))
        print('   vts:', [(hex(a), hex(v)) for a, v in s['vts']])
        print('   calls:', [(hex(a), hex(t)) for a, t in s['calls']])
    print('0x6F322F bytes:', hexs(0x6F322F, 10))
    print('0x6F322F in [0x6F2B40,0x6F3267):', 0x6F2B40 <= 0x6F322F < 0x6F3267)
    # install sites of 0x7E3EBC
    sites = [0x401000 + i - 0x1000 for i in range(0x1000, 0x3e1000) if u32(0x401000 + i - 0x1000) == 0x7E3EBC]
    print('0x7E3EBC imm32 sites:', [hex(s) for s in sites])
    # callers of key ctors
    txt = d[0x1000:0x3e1000]
    for tgt in (0x6F2B40, 0x6F4300):
        hs = []
        for i in range(len(txt)-5):
            if txt[i] == 0xE8:
                rel = int.from_bytes(txt[i+1:i+5], 'little', signed=True)
                if 0x401000 + i + 5 + rel == tgt: hs.append(0x401000 + i)
        print('callers of 0x%X:' % tgt, [hex(h) for h in hs])

if __name__ == '__main__': main()
