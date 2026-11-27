#!/usr/bin/env python3
"""R143 X：共用工具（地址换算 + capstone 流式扫描 + 归一化解析）。

关键：capstone 的位移打印不统一 —— 小位移印十进制（[esi + 4]），大位移印十六进制
（[esi + 0x2c]）。R143 首轮我的解析器只认 +0xNN 与 -NN，把 +4/+8 全丢了，
导致「位移 4/8 的装载数 = 0」这一假事实。本模块把两种形态都归一成 int。
"""
import struct, re, collections
import pefile

P = 'ra2bench/gamemd.exe'

class Bin:
    def __init__(self, path=P):
        self.path = path
        self.data = open(path, 'rb').read(); self.N = len(self.data)
        pe = pefile.PE(path, fast_load=True); self.IB = pe.OPTIONAL_HEADER.ImageBase
        self.secs = [(s.Name.decode().rstrip('\x00'), s.VirtualAddress, s.Misc_VirtualSize,
                      s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
        t = [s for s in self.secs if s[0] == '.text'][0]
        self.T = t

    def va2off(self, va):
        for nm, ava, vs, raw, rs in self.secs:
            lo = self.IB + ava
            if lo <= va < lo + max(vs, rs):
                d = va - lo
                return raw + d if d < rs else None
        return None

    def rd(self, va, l):
        o = self.va2off(va)
        if o is None or o + l > self.N: return None
        return self.data[o:o + l]

    def dw(self, va):
        b = self.rd(va, 4)
        return None if b is None else struct.unpack('<I', b)[0]

    def sec_of(self, va):
        for nm, ava, vs, raw, rs in self.secs:
            lo = self.IB + ava
            if lo <= va < lo + max(vs, rs): return nm
        return None

    # ---------- 虚表集合（R140/r140n 同法） ----------
    def vtset(self):
        pat = re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
        TDs = {}
        for nm, ava, vs, raw, rs in self.secs:
            if nm in ('.data', '.rdata'):
                for m in pat.finditer(self.data[raw:raw + rs]):
                    s = self.IB + ava + m.start()
                    if (self.dw(s - 8) is not None and self.dw(s - 4) == 0
                            and self.sec_of(self.dw(s - 8)) in ('.data', '.rdata')):
                        TDs[s - 8] = m.group()
        tdset = set(TDs)
        COL = set()
        for nm, ava, vs, raw, rs in self.secs:
            if nm in ('.data', '.rdata'):
                blob = self.data[raw:raw + rs]
                for i in range(len(blob) // 4):
                    v = struct.unpack_from('<I', blob, i * 4)[0]
                    if v in tdset:
                        c = self.IB + ava + i * 4 - 12
                        if self.dw(c) == 0 and self.dw(c + 12) == v and self.dw(c + 16) != 0:
                            COL.add(c)
        VTS = set()
        for nm, ava, vs, raw, rs in self.secs:
            if nm in ('.data', '.rdata'):
                blob = self.data[raw:raw + rs]
                for i in range(len(blob) // 4):
                    v = struct.unpack_from('<I', blob, i * 4)[0]
                    if v in COL:
                        vt = self.IB + ava + i * 4 + 4
                        if self.dw(vt - 4) == v:
                            VTS.add(vt)
        return TDs, COL, VTS

    # ---------- 流式反汇编 ----------
    def sweep(self, md, chunk=65536):
        off = self.T[3]; end = off + self.T[4]; base_vs = self.T[1]
        while off < end:
            chunkb = self.data[off:min(off + chunk, end)]
            base = self.IB + (base_vs + (off - self.T[3]))
            consumed = 0
            for a, sz, mn, op in md.disasm_lite(chunkb, base):
                if a - base + sz > len(chunkb): break
                consumed = a - base + sz
                yield a, sz, mn, norm(op)
            off += consumed if consumed else 1

DIS_RE = re.compile(r'\[([a-z0-9]+)((?:\s*[+-]\s*(?:0x[0-9a-f]+|\d+))|(?:\s*\+\s*[a-z0-9]+\s*\*\s*\d+))*\]')

def norm(op):
    """归一化：只压逗号/加号/星号两侧空白（保留 'dword ptr' 内的单个空格）；
    并把十进制位移统一成十六进制（capstone 对 <10 的位移印十进制 [esi + 4]）。"""
    if not op: return ''
    op = re.sub(r'\s*([+,*])\s*', r'\1', op)
    op = re.sub(r'([+-])(\d+)(?![\dx])', lambda m: '%s0x%x' % (m.group(1), int(m.group(2))), op)
    return op

def disp_of(s):
    if not s: return 0
    s = s.strip()
    if s.startswith('+0x'): return int(s[3:], 16)
    if s.startswith('-0x'): return -int(s[3:], 16)
    if s.startswith('+'): return int(s[1:])
    if s.startswith('-'): return -int(s[1:])
    return int(s, 0)

RE_STORE = re.compile(r'^dword ptr \[([a-z0-9]+)([+-]0x[0-9a-f]+)?\](?:,([^,]+))?$')
RE_LOAD = re.compile(r'^([a-z0-9]+),dword ptr \[([a-z0-9]+)([+-]0x[0-9a-f]+)?\]$')
RE_CALL = re.compile(r'^dword ptr \[([a-z0-9]+)([+-]0x[0-9a-f]+)?\]$')
RE_IMM = re.compile(r'^(0x[0-9a-f]+|\d+)$')

def immval(t):
    return (int(t, 16) if t.startswith('0x') else int(t)) & 0xFFFFFFFF

GEN = ('eax', 'ebx', 'ecx', 'edx', 'esi', 'edi')
STK = ('esp', 'ebp')
W_MN = {'mov', 'movzx', 'movsx', 'lea', 'add', 'sub', 'adc', 'sbb', 'and', 'or', 'xor',
        'inc', 'dec', 'neg', 'not', 'shl', 'shr', 'sar', 'sal', 'rol', 'ror', 'imul',
        'pop', 'xchg', 'bswap', 'mul', 'div', 'idiv'}
