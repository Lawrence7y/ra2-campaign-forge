# -*- coding: utf-8 -*-
"""手工复核：不调用 probe.py 的 vtable_start，直接按 RTTI 规则摊开字节，人工看。

用法:
    python verify_rows.py 0055A0D0            # 单行：表/COL/槽/装表点
    python verify_rows.py --notderivable      # 11 行 NOT_DERIVABLE 全列
"""
import os, sys, struct
import pefile, capstone

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
BASE = 0x400000

pe = pefile.PE(EXE, fast_load=True)
secs = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    secs.append((nm, BASE + s.VirtualAddress, s.Misc_VirtualSize,
                 s.SizeOfRawData, s.get_data()))


def sec(va):
    for nm, base, vs, rs, d in secs:
        if base <= va < base + max(vs, rs):
            return nm, base, d
    return None, None, None


def u32(va):
    nm, base, d = sec(va)
    if d is None:
        return None
    o = va - base
    if o + 4 > len(d):
        return None
    return struct.unpack_from('<I', d, o)[0]


def cstr(va, n=200):
    nm, base, d = sec(va)
    if d is None:
        return None
    o = va - base
    e = d.find(b'\x00', o, o + n)
    return d[o:e].decode('latin-1') if e >= 0 else None


def vtable_at(vt):
    """按 RTTI 逐字段摊开。"""
    col = u32(vt - 4)
    sig = u32(col)
    off = u32(col + 4)
    cdoff = u32(col + 8)
    td = u32(col + 12)
    pchd = u32(col + 16)
    name = cstr(td + 8)
    return dict(vt=vt, col=col, sig=sig, off=off, cd=cdoff, td=td, pchd=pchd,
                td_name=name, col_sec=sec(col)[0], td_sec=sec(td)[0])


def dump_vt(vt, n=8):
    return [(vt + 4 * i, u32(vt + 4 * i)) for i in range(-1, n)]


MD = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
MD.detail = True
MD.skipdata = True


def dis(va, n=48):
    nm, base, d = sec(va)
    o = va - base
    out = []
    for insn in MD.disasm(d[o:o + n], va):
        out.append('%08X  %-24s %s %s' % (insn.address,
                                          insn.bytes.hex(),
                                          insn.mnemonic, insn.op_str))
    return out


def report(entry):
    e = int(entry, 16)
    print('=' * 78)
    print('entry %08X   section=%s' % (e, sec(e)[0]))
    found = []
    for nm in ('.rdata', '.data'):
        for sname, base, vs, rs, d in secs:
            if sname != nm:
                continue
            pat = e.to_bytes(4, 'little')
            i = d.find(pat)
            while i >= 0:
                if i % 4 == 0:
                    found.append(base + i)
                i = d.find(pat, i + 1)
    print('dd %08X hits in .rdata/.data: %d -> %s'
          % (e, len(found), ['%08X' % x for x in found]))
    for hit in found:
        # 往回找表起点
        for k in range(0, 0x400):
            v = hit - 4 * k
            col = u32(v - 4)
            if col is None or sec(col)[0] is None:
                continue
            if u32(col) != 0:
                continue
            td = u32(col + 12)
            nmv = cstr(td + 8) if td else None
            if nmv and nmv.startswith('.?A'):
                info = vtable_at(v)
                print('   hit %08X -> vtable start %08X slot %d' % (hit, v, k))
                print('   COL %08X sig=%s off=%s cd=%s td=%08X(%s) td_name=%s pchd=%08X'
                      % (info['col'], info['sig'], info['off'], info['cd'],
                         info['td'], info['td_sec'], info['td_name'], info['pchd']))
                print('   vt dwords:',
                      ', '.join('%08X:%08X' % (a, b) for a, b in dump_vt(v, 6)))
                break
        else:
            print('   hit %08X: no RTTI vtable start found (raw dd, not a vtable slot)'
                  % hit)
    print('--- first 6 disasm lines at entry ---')
    for l in dis(e, 24):
        print('   ', l)


def not_derivable():
    # 注意名字冲突：D47_SURFACE\work\probe.py 与本目录 probe.py 同名。
    # 用独立模块名加载本目录的 probe.py，避免覆盖 surface.py 需要的 'probe'。
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'r4probe', os.path.join(HERE, 'probe.py'))
    P = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(P)
    cls, rows, recs = P.load_class()
    img = P.Image(EXE)
    ts = P.TextScan(img)
    for r in cls:
        a = P.analyze(img, ts, r)
        if a['form'] == 'NOT_DERIVABLE':
            print('%s %s %-46s vt=%d direct=%d textrefs=%d datarefs=%d'
                  % (a['entry'], a['subsystem'], a['name'][:46], len(a['vt']),
                     a['direct'], a['text_imm_refs'], a['data_imm_refs']))
            for hit in P.scan_dd(img, int(a['entry'], 16)):
                print('     dd hit', '%08X' % hit)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--notderivable':
        not_derivable()
    else:
        for x in sys.argv[1:]:
            report(x)
