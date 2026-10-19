#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xref_scan.py — gamemd.exe 静态交叉引用扫描器（capstone 线性扫描）
用法:
  python tools/xref_scan.py xrefs  0x008B4108 0x00A83DE8 ...   # 查询哪些函数引用了这些地址
  python tools/xref_scan.py fn     0x00658780                 # 反汇编指定函数全文
  python tools/xref_scan.py bucket 0x53EB00                   # 列出落在热点桶附近的函数与引用
函数边界: 以"被 call 直呼目标"为函数起点集合, 归属规则为引用地址向前最近的函数起点。
"""
import sys, json, struct, bisect
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
SYM = r"D:\Project\ra2-campaign-forge\out\reverse\symbols.json"
IMAGE_BASE = 0x400000

def load_sections():
    data = open(EXE, 'rb').read()
    e_lfanew = struct.unpack_from('<I', data, 0x3C)[0]
    nsec = struct.unpack_from('<H', data, e_lfanew + 6)[0]
    opt_size = struct.unpack_from('<H', data, e_lfanew + 20)[0]
    sec_off = e_lfanew + 24 + opt_size
    secs = []
    for i in range(nsec):
        off = sec_off + i * 40
        name = data[off:off + 8].rstrip(b'\0').decode('ascii', 'replace')
        vsize, vaddr, rawsize, rawptr = struct.unpack_from('<IIII', data, off + 8)
        chars = struct.unpack_from('<I', data, off + 36)[0]
        secs.append(dict(name=name, va=IMAGE_BASE + vaddr, vsize=vsize,
                         raw=data[rawptr:rawptr + rawsize], exec=bool(chars & 0x20000000)))
    return secs

def load_image(secs):
    """把所有节拼进连续镜像（按 VA 排序，留洞填 0），返回 (image, base)"""
    lo = min(s['va'] for s in secs)
    hi = max(s['va'] + s['vsize'] for s in secs)
    img = bytearray(hi - lo)
    for s in secs:
        o = s['va'] - lo
        n = min(len(s['raw']), s['vsize'])
        img[o:o + n] = s['raw'][:n]
    return img, lo

def va_to_off(va, secs):
    for s in secs:
        if s['va'] <= va < s['va'] + s['vsize']:
            return va - s['va']
    return None

class Scanner:
    def __init__(self):
        self.secs = load_sections()
        self.image, self.base = load_image(self.secs)
        self.md = Cs(CS_ARCH_X86, CS_MODE_32)
        self.md.detail = True
        self.call_targets = set()   # 函数起点集合
        self.xrefs = {}             # data_addr -> set(insn_va)
        self.fstart_list = []

    def scan(self):
        import capstone as _cs
        text = next(s for s in self.secs if s['name'] == '.text')
        code = text['raw'][:text['vsize']]
        tva = text['va']
        # 第一遍: 带容错的线性反汇编（坏字节跳 1 字节续扫），收集 call 目标与数据引用
        pos = 0
        while pos < len(code):
            for insn in self.md.disasm(code[pos:], tva + pos):
                for op in insn.operands:
                    if insn.mnemonic in ('call', 'jmp') and op.type == _cs.x86.X86_OP_IMM:
                        if insn.mnemonic == 'call':
                            self.call_targets.add(op.imm & 0xFFFFFFFF)
                    elif op.type == _cs.x86.X86_OP_MEM:
                        disp = op.mem.disp & 0xFFFFFFFF
                        if IMAGE_BASE <= disp < IMAGE_BASE + 0x800000:
                            self.xrefs.setdefault(disp, set()).add(insn.address)
                pos = insn.address - tva + insn.size
            if pos < len(code):
                pos += 1  # 跳过无法解码的字节
        self.fstart_list = sorted(self.call_targets)

    def fn_of(self, va):
        i = bisect.bisect_right(self.fstart_list, va) - 1
        if i < 0:
            return None
        return self.fstart_list[i]

    def fn_end(self, fstart):
        i = bisect.bisect_right(self.fstart_list, fstart)
        return self.fstart_list[i] if i < len(self.fstart_list) else fstart + 0x4000

def disasm_fn(sc, fstart, max_len=0x2000):
    off = va_to_off(fstart, sc.secs)
    if off is None:
        print('VA 不在任何节内: 0x%08X' % fstart); return
    code = sc.image[fstart - sc.base: fstart - sc.base + max_len]
    end = sc.fn_end(fstart)
    out = []
    for insn in sc.md.disasm(code, fstart):
        out.append('%08X  %-24s %s %s' % (insn.address, insn.bytes.hex(), insn.mnemonic, insn.op_str))
        if insn.mnemonic == 'ret' or (insn.mnemonic.startswith('j') and insn.address + insn.size >= end):
            pass
        if insn.address >= end - 1:
            break
        if insn.mnemonic == 'ret':
            break
    print('\n'.join(out))

def classify_names():
    """vtable_va -> 类名, vfunc -> 类名::idx"""
    d = json.load(open(SYM, encoding='utf-8'))
    v2n, f2n = {}, {}
    extra_starts = set()
    for cname, c in d['classes'].items():
        if not c.get('vtable_va') or not c.get('vfuncs'):
            continue
        vt = int(c['vtable_va'], 16) if isinstance(c['vtable_va'], str) else int(c['vtable_va'])
        v2n[vt] = cname
        for i, f in enumerate(c['vfuncs']):
            fa = int(f, 16) if isinstance(f, str) else int(f)
            f2n.setdefault(fa, f'{cname}::v[{i}]')
            extra_starts.add(fa)
    return v2n, f2n, extra_starts

def main():
    mode = sys.argv[1]
    sc = Scanner()
    sc.scan()
    _, f2n, extra_starts = classify_names()
    sc.call_targets |= extra_starts  # 虚表函数也是函数起点
    sc.fstart_list = sorted(sc.call_targets)
    if mode == 'xrefs':
        for a in sys.argv[2:]:
            va = int(a, 16)
            refs = sorted(sc.xrefs.get(va, []))
            print('=== 引用 0x%08X 的指令 (%d 处) ===' % (va, len(refs)))
            fns = {}
            for r in refs:
                f = sc.fn_of(r)
                fns.setdefault(f, []).append(r)
            for f, rs in sorted(fns.items(), key=lambda kv: kv[0] or 0):
                sym = f2n.get(f, '')
                print('  函数 0x%08X %s <- %s' % (f, sym, ' '.join('0x%08X' % r for r in rs[:8])))
    elif mode == 'fn':
        disasm_fn(sc, int(sys.argv[2], 16))
    elif mode == 'bucket':
        for a in sys.argv[2:]:
            va = int(a, 16)
            i = bisect.bisect_right(sc.fstart_list, va) - 1
            f = sc.fstart_list[i] if i >= 0 else 0
            nxt = sc.fstart_list[i + 1] if i + 1 < len(sc.fstart_list) else 0
            print('桶 0x%08X -> 函数 0x%08X (%s)  下一函数 0x%08X' % (va, f, f2n.get(f, ''), nxt))

if __name__ == '__main__':
    main()
