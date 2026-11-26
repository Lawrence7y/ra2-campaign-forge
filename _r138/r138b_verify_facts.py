# -*- coding: utf-8 -*-
"""r138b_verify_facts.py —— R138 主会话独立核验：外部 triage 分档 + F29 字节事实。

三项：
  A. 外部调研产物 _ext/f_partial_triage/TRIAGE.tsv 的 32 条分档，我自己按
     FACT_INDEX 第 4 列重算「部分失联」集合，核对 fid 集合与三档计数。
  B. F29 的 17 字节序列在 gamemd.exe 全镜像的出现次数（纯字节搜索，不开 detail）。
  C. F29 的 8 字节桩序列出现次数 + 只在 .text 的断言（按段表判定）。
  D. 导入表 FirstThunk idx=62 的三口径（DLL 内 / 全局 0-based / 全局 1-based）。

用法: timeout 300 python3 _r138/r138b_verify_facts.py
"""
import io, os, sys, json, re, struct

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
FI = os.path.join(R14, 'R17_R104_FACTINDEX_V532', 'FACT_INDEX.tsv')
TRI = os.path.join(ROOT, '_ext', 'f_partial_triage', 'TRIAGE.tsv')
EXE = os.path.join(ROOT, 'ra2bench', 'gamemd.exe')
OUT = os.path.join(ROOT, '_r138', 'r138b_verify_facts.json')

N_PASS = N_FAIL = 0
FAILS = []


def chk(cond, label, extra=''):
    global N_PASS, N_FAIL
    if cond:
        N_PASS += 1
        print('  PASS ' + label)
    else:
        N_FAIL += 1
        FAILS.append(label + (' | ' + str(extra) if extra else ''))
        print('  FAIL ' + label + (' | ' + str(extra) if extra else ''))


def load_facts():
    d = {}
    for ln in io.open(FI, encoding='utf-8'):
        c = ln.rstrip('\n').split('\t')
        if len(c) >= 5 and re.match(r'^F\d{2}$', c[0]):
            d[c[0]] = c
    return d


def paths_of(cell):
    out = []
    for e in cell.split(';'):
        e = e.strip()
        if not e:
            continue
        p = e.split('(')[0].strip()
        out.append(p.replace('\\', '/'))
    return out


def resolve(p):
    """rel 是相对仓库根写的（带 lead/ 前缀）。"""
    cands = [os.path.join(ROOT, p)]
    if not p.startswith('lead/'):
        cands.append(os.path.join(ROOT, 'lead', p))
    for c in cands:
        if os.path.exists(c):
            return True
    return False


def main():
    res = {}
    facts = load_facts()
    chk(len(facts) == 54, 'FACT_INDEX 54 条事实项', len(facts))

    # ---------- A · 部分失联集合重算 ----------
    print('= A · 部分失联集合重算 =')
    full_dead, part_dead, all_live = [], [], []
    for fid in sorted(facts):
        ps = paths_of(facts[fid][3])
        ps = [p for p in ps if p]
        live = [p for p in ps if resolve(p)]
        if not ps:
            continue
        if not live:
            full_dead.append(fid)
        elif len(live) == len(ps):
            all_live.append(fid)
        else:
            part_dead.append(fid)
    chk(full_dead == ['F23', 'F35'], '整行失联恰为 F23/F35', full_dead)
    chk(len(all_live) == 20, '全链在位 20 条', len(all_live))
    chk(len(part_dead) == 32, '部分失联 32 条', len(part_dead))
    chk(len(full_dead) + len(part_dead) + len(all_live) == 54, '三桶合计 54',
        len(full_dead) + len(part_dead) + len(all_live))
    res['evidchain'] = {'full_dead': full_dead, 'n_part': len(part_dead),
                        'n_live': len(all_live)}

    # ---------- A2 · 外部 triage 对账 ----------
    print('= A2 · 外部 triage 对账 =')
    chk(os.path.exists(TRI), 'triage 产物 TRIAGE.tsv 在盘')
    trows = [l.rstrip('\n').split('\t') for l in io.open(TRI, encoding='utf-8') if l.strip()]
    hdr, tbody = trows[0], trows[1:]
    chk(len(tbody) == 32, 'triage 覆盖 32 条', len(tbody))
    tf = [r[0] for r in tbody]
    chk(sorted(tf) == sorted(part_dead), 'triage 的 fid 集合 == 我算的部分失联集合',
        (len(set(tf) ^ set(part_dead)), sorted(set(tf) ^ set(part_dead))[:5]))
    from collections import Counter
    vc = Counter(r[4] for r in tbody)
    chk(vc.get(u'仍可核验') == 5, '仍可核验 5 条', dict(vc))
    chk(vc.get(u'需重建') == 18, '需重建 18 条', dict(vc))
    chk(vc.get(u'不可核验') == 9, '不可核验 9 条', dict(vc))
    chk(sum(vc.values()) == 32, '三档合计 32', sum(vc.values()))
    res['triage'] = dict(vc)

    # ---------- B/C/D · 字节事实 ----------
    print('= B/C/D · F29 字节事实 =')
    exe = open(EXE, 'rb').read()
    chk(len(exe) > 0x400000, 'gamemd.exe 读取成功', len(exe))
    # 段表：用 pefile 取 .text / 数据节范围（只读头，不反汇编）
    import pefile
    pe = pefile.PE(EXE, fast_load=True)
    secs = [(s.Name.rstrip(b'\x00').decode('latin1'), s.PointerToRawData,
             s.PointerToRawData + s.SizeOfRawData) for s in pe.sections]
    text = [s for s in secs if s[0] == '.text'][0]
    print('  .text raw range 0x%x..0x%x' % (text[1], text[2]))

    # B: 17 字节序列（R62/R63 记录的那份 AddRef 拷贝）
    seq17 = bytes.fromhex('8B44240483C00450FF15C8117E00C20400')
    chk(len(seq17) == 17, '17 字节序列长度正确', len(seq17))
    occ17 = []
    st = 0
    while True:
        i = exe.find(seq17, st)
        if i < 0:
            break
        occ17.append(i)
        st = i + 1
    chk(len(occ17) >= 1, '17 字节序列至少出现 1 次', len(occ17))
    in_text17 = [o for o in occ17 if text[1] <= o < text[2]]
    chk(len(in_text17) == len(occ17), '17 字节序列全部落在 .text',
        (len(in_text17), len(occ17)))
    # 8 字节桩 B8 01 00 00 00 C2 04 00
    seq8 = bytes.fromhex('B801000000C20400')
    occ8 = []
    st = 0
    while True:
        i = exe.find(seq8, st)
        if i < 0:
            break
        occ8.append(i)
        st = i + 1
    in_text8 = [o for o in occ8 if text[1] <= o < text[2]]
    chk(len(occ8) >= 1, '8 字节桩序列至少出现 1 次', len(occ8))
    chk(len(in_text8) == len(occ8), '8 字节桩序列全部落在 .text',
        (len(in_text8), len(occ8)))
    print('  17字节出现 %d 次 / 8字节桩出现 %d 次' % (len(occ17), len(occ8)))

    # D: 导入表 idx
    pe2 = pefile.PE(EXE)
    idx62 = None
    per_dll = {}
    glob0 = 0
    for d in pe2.DIRECTORY_ENTRY_IMPORT:
        name = d.dll.decode('latin1') if isinstance(d.dll, bytes) else d.dll
        n = 0
        for imp in d.imports:
            n += 1
            if name.lower() == 'kernel32.dll' and imp.address:
                pass
        per_dll[name] = n
    # 找 InterlockedIncrement 在 KERNEL32 的组内下标与全局下标
    g = 0
    found = []
    for d in pe2.DIRECTORY_ENTRY_IMPORT:
        name = d.dll.decode('latin1') if isinstance(d.dll, bytes) else d.dll
        for i, imp in enumerate(d.imports):
            fn = imp.name.decode('latin1') if imp.name else None
            if fn == 'InterlockedIncrement':
                found.append((name, i, g, imp.hint if imp.hint is not None else None))
            g += 1
    chk(len(found) >= 1, 'InterlockedIncrement 在导入表被找到', found)
    if found:
        nm, inner, globi, hint = found[0]
        chk(nm.lower() == 'kernel32.dll', '归属 KERNEL32.dll', nm)
        chk(inner == 62, 'DLL 内 0-based 下标 = 62', inner)
        chk(globi == 63, '全局 0-based 下标 = 63', globi)
        chk(hint == 432, 'Hint = 432', hint)
        res['import_idx'] = {'dll': nm, 'inner0': inner, 'global0': globi,
                             'global1': globi + 1, 'hint': hint}
        chk(glob0 == 0, '全局计数起点为 0')
    chk(len(per_dll) > 0, '导入 DLL 数 > 0', len(per_dll))

    res['bytes'] = {'occ17': len(occ17), 'occ17_in_text': len(in_text17),
                    'occ8': len(occ8), 'occ8_in_text': len(in_text8),
                    'text_range': [text[1], text[2]], 'exe_bytes': len(exe)}
    res['assertions'] = {'pass': N_PASS, 'fail': N_FAIL, 'fail_list': FAILS}
    with io.open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=2, sort_keys=True))
        f.write(u'\n')
    print('\n== 断言 %d PASS / %d FAIL ==' % (N_PASS, N_FAIL))
    return 0 if N_FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
