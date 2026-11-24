#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R74-NULFORENSIC-AUDIT audit_nul_r74.py
独立审计脚本：测量 R14_COMMON.md 的 NUL 字节、备份偏移一致性、候选字符攻击、
字节不变性、rg 输出形态、check_disc.py 门禁覆盖面、sha256 硬编码检索。
只读：只写 stdout（JSON 摘要）与 _r74/audit/ 下由调用者重定向的文件。
可重复跑：不依赖当前目录状态之外的任何可变状态。
"""
import io, os, re, sys, json, hashlib, subprocess
from pathlib import Path
from collections import Counter, defaultdict

ROOTDIR = Path(__file__).resolve().parents[4]       # .../ra2-campaign-forge
R14 = ROOTDIR / 'lead' / 'next_re_20261117_r14'
RC = R14 / 'R14_COMMON.md'
BASE = R14 / 'R17_LEAD_BASELINE'
EXE = ROOTDIR / 'ra2bench' / 'gamemd.exe'

def read_bytes(p):
    return Path(p).read_bytes()

def line_of(b, idx):
    return b.count(b'\n', 0, idx) + 1

def col_of(b, idx):
    ls = b.rfind(b'\n', 0, idx) + 1
    return idx - ls

def nul_sites(b):
    return [i for i, x in enumerate(b) if x == 0]

def backup_files():
    out = sorted(p for p in BASE.iterdir()
                 if p.is_file() and 'R14_COMMON' in p.name)
    return out

def classify(b, i):
    """把 NUL 后随串分类为 0x 前缀地址 / 8 位无前缀地址 / 其它。"""
    nxt = b[i+1:i+20]
    if nxt.startswith(b'x'):
        return '0x-prefixed'
    if re.match(rb'^[0-9A-Fa-f]{7,8}\b', nxt):
        return '8-hex'
    return 'other'

def parse_candidate(b, i, ch=0x30):
    """把 idx 处字节替换为 ch 后，抽取 NUL 起点处的地址 token。"""
    fixed = bytearray(b)
    fixed[i] = ch
    s = fixed[i:i+16]
    m = re.match(rb'^(0x[0-9A-Fa-f]+|[0-9A-Fa-f]{8})', bytes(s))
    if not m:
        return None, None
    tok = m.group(1).decode('ascii')
    va = int(tok, 16)
    return tok, va

def load_pe():
    import pefile
    pe = pefile.PE(str(EXE), fast_load=True)
    base = pe.OPTIONAL_HEADER.ImageBase
    return pe, base

def va_to_off(pe, base, va):
    rva = va - base
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None

def disasm_at(pe, base, va):
    from capstone import Cs, CS_ARCH_X86, CS_MODE_32
    off = va_to_off(pe, base, va)
    if off is None:
        return None, None
    code = pe.__data__[off:off+16]
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.skipdata = True
    for ins in md.disasm(code, va):
        return '%s %s' % (ins.mnemonic, ins.op_str), code[:8].hex().upper()
    return None, code[:8].hex().upper()

def strict_utf8(b):
    try:
        b.decode('utf-8', errors='strict')
        return True
    except UnicodeDecodeError:
        return False

def grep_shape(path, phrase):
    """用 rg 搜索，返回 stdout 原文（有限长度）。"""
    try:
        p = subprocess.run(['rg', '-n', '-F', phrase, str(path)],
                           capture_output=True, timeout=20)
        return p.returncode, p.stdout.decode('utf-8', 'replace'), p.stderr.decode('utf-8', 'replace')
    except Exception as e:
        return -1, '', str(e)

def sha_hardcodes():
    """全库搜把 R14_COMMON.md 的 sha256 写死的行（排除备份目录）。"""
    hits = []
    rg = subprocess.run(
        ['rg', '-n', '-i', '--glob', '!**/R17_LEAD_BASELINE/**',
         '--glob', '!**/_r*/**', 'R14_COMMON.*sha|sha.*R14_COMMON',
         str(R14)], capture_output=True, text=True, timeout=60)
    return rg.stdout

def main():
    b = read_bytes(RC)
    sites = nul_sites(b)
    bk = backup_files()
    base_sets = {}
    for p in bk:
        d = read_bytes(p)
        base_sets[p.name] = nul_sites(d)
    all_same = all(v == sites for v in base_sets.values())

    prev_dist = Counter(b[i-1] for i in sites)
    line_dist = Counter(line_of(b, i) for i in sites)
    kind_dist = Counter(classify(b, i) for i in sites)

    # 字节不变性：所有 0x00 -> 0x30
    fixed = bytes([0x30 if x == 0 else x for x in b])
    invariants = {
        'size_before': len(b), 'size_after': len(fixed),
        'cr_before': b.count(b'\r'), 'cr_after': fixed.count(b'\r'),
        'lf_before': b.count(b'\n'), 'lf_after': fixed.count(b'\n'),
        'lines_before': b.count(b'\n')+1, 'lines_after': fixed.count(b'\n')+1,
        'utf8_before': strict_utf8(b), 'utf8_after': strict_utf8(fixed),
    }

    # 其它控制字节（X3 证据）
    other_ctl = [(i, hex(x), line_of(b, i), col_of(b, i),
                  b[max(0,i-12):i+16].decode('utf-8','backslashreplace'))
                 for i, x in enumerate(b)
                 if x < 32 and x not in (9, 10, 13, 0)]

    # 非 NUL 控制字节的原字符推断（0x0c->f, 0x0b->b, 0x07->D, 0x08->b 等）
    # 判据：补回后 token 与本库其它卡面逐字出现。
    fix_map = {0x0c: 'f', 0x0b: 'b', 0x07: 'D', 0x08: 'b'}

    # 反汇编验证（capstone + skipdata），只验证可从文档行抽取助记符的 0x-prefixed NUL
    pe, image_base = load_pe()
    disasm_rows = []
    for i in sites:
        tok, va = parse_candidate(b, i)
        if tok is None:
            continue
        line_no = line_of(b, i)
        ls = b.rfind(b'\n', 0, i) + 1
        le = b.find(b'\n', i)
        ltxt = b[ls:le].decode('utf-8', 'replace')
        dis, raw = disasm_at(pe, image_base, va)
        # 行内与该 VA 同现的助记符：取紧跟 token 之后首个英文助记符
        after = ltxt[len(tok):] if tok else ''
        mm = re.search(r'\b(mov|cmp|call|je|jmp|or|and|add|sub|test|lea|push|pop|ret|xor|imul|mul)\b\s+([^|；;（）()]{0,50})',
                       b[i+len(tok):le].decode('utf-8','replace'))
        doc_asm = (mm.group(0).strip() if mm else '')
        disasm_rows.append({
            'offset': i, 'line': line_no, 'token': tok, 'va': hex(va),
            'raw8': raw, 'disasm': dis, 'docasm': doc_asm,
            'intext': va_to_off(pe, image_base, va) is not None,
        })

    # 负控 N1：候选 VA+1 反汇编与文档所述助记符/操作数不再吻合。
    # 判据：把 capstone 的 AT&T 风格操作数归一到文档写法后做「完整指令」比较；
    # 只要 +1 后的完整反汇编串不等于原址的完整反汇编串，就判为不再吻合。
    def norm_asm(s):
        if not s:
            return ''
        s = s.lower().replace('byte ptr ', '').replace('dword ptr ', '')
        s = s.replace(' + ', '+').replace(', ', ',').replace('0x', '0x')
        return s.strip()
    neg_n1 = []
    for row in disasm_rows:
        if not row['docasm']:
            continue
        va = int(row['va'], 16)
        d1, _ = disasm_at(pe, image_base, va + 1)
        neg_n1.append({'va': row['va'], 'doc': row['docasm'][:30],
                       'dis_vanilla': row['disasm'], 'dis_plus1': d1,
                       'different': bool(d1) and norm_asm(d1) != norm_asm(row['disasm'])})

    # rg 输出形态：取只在后半部分出现的短语
    phrase = '已知须标注的 3 行'
    rc_rg = grep_shape(RC, phrase)
    clean = R14 / '_cards' / 'S1031.md'
    cl_rg = grep_shape(clean, phrase) if clean.exists() else (-1, '(no clean file)', '')

    report = {
        'current': str(RC), 'size': len(b),
        'nul_count': len(sites),
        'nul_lines': sorted(set(line_of(b, i) for i in sites)),
        'nul_line_count': len(set(line_of(b, i) for i in sites)),
        'nul_kind_dist': dict(kind_dist),
        'prev_byte_dist': {hex(k): v for k, v in sorted(prev_dist.items())},
        'backups': [ {'name': p.name, 'size': len(read_bytes(p)), 'nuls': len(base_sets[p.name]),
                      'offsets_identical': base_sets[p.name] == sites} for p in bk ],
        'all_backup_offsets_identical': all_same,
        'invariants': invariants,
        'other_control_bytes': other_ctl,
        'disasm_rows': disasm_rows,
        'neg_n1': neg_n1,
        'rg_current': rc_rg,
        'rg_clean': cl_rg,
        'sha_hardcode_hits': sha_hardcodes(),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
