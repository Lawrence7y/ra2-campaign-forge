# -*- coding: utf-8 -*-
"""
HYGIENE-11 —— 11 行「全镜像 0 引用」的地址可信性核查（只读测量员）。

对 HYGIENE-11 卡片列的 11 个 entry，逐行回答四问：

  问1 该地址处是不是「像函数」的东西？（序言 / 是否 atlas entry / 体大小 / 指令数）
  问2 是否指向了函数中段（前 1–16 字节内是否有序言 → 真实起点）？
  问3 该 4 字节值在全镜像真的 0 次吗？（独立复算：.text 的 E8/E9/68/B8-BF/C7、各段裸 4 字节）
  问4 名字与地址是否对得上？（YRpp 头文件里 JMP_THIS/JMP_STD 给出的地址是「名字→地址」权威源；
       RTTI 的 pTD/pCHD 是绝对 VA，装饰名在 TD+8 是内联串；再用 vptr 装表点找 ctor 真身）

只读：不写 HYGIENE_R11\\ 以外的任何路径。
跑法：python probe.py        # 写 rows.tsv / facts.json / disasm_11.txt 并打印摘要
"""
import os
import re
import io
import sys
import json
import bisect
import hashlib
import collections

import pefile
import capstone

HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(R14))
EXE = os.path.join(ROOT, 'ra2youli', 'gamemd.exe')
ATLAS = os.path.join(ROOT, 'lead', 'next_re_20261112_r10', 'W130_atlas',
                     'function_atlas.tsv')
ALL848 = os.path.join(R14, 'R4_DERIVABILITY', 'all848.tsv')
COV = os.path.join(R14, 'COVERAGE', 'coverage.tsv')
YRPP = os.path.join(ROOT, 'YRpp')
SYMS = os.path.join(ROOT, 'out', 'reverse', 'symbols.json')

EXPECT_SHA = '73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476'
IMAGE_BASE = 0x400000

# 卡片「待查的 11 行」
ROWS = [
    ('004C52B0', 'S20', 'EMPulseClass::noinit_t'),
    ('004C6800', 'S18', 'NetworkEvents::FillEvent_Animation'),
    ('004CC680', 'S06', 'MapClass::MapClass'),
    ('004F6E70', 'S14', 'HouseClass::GetStoragePercentage'),
    ('0054E690', 'S13', 'Kamikaze::Kamikaze'),
    ('006E5850', 'S15', 'TagClass::IsOnlyInstanceOfType'),
    ('007262D0', 'S15', 'TriggerClass::HasZoneEntryByEvent'),
    ('00726310', 'S15', 'TriggerClass::HasAllowWinAction'),
    ('00726350', 'S15', 'TriggerClass::HasGlobalSetOrClearedEvent'),
    ('00726630', 'S15', 'TriggerClass::GetInstance'),
    ('00727120', 'S15', 'TriggerTypeClass::FindByNameOrID'),
]

# 每行的「同族邻居」（YRpp 声明的同组函数），用来判「是整簇都没人调，还是只有这一支没人调」
SIBLINGS = {
    '004C52B0': [0x4C52B0, 0x4C5100, 0x4C5200],
    '004C6800': [0x4C6650, 0x4C66C0, 0x4C6720, 0x4C6780, 0x4C6AE0, 0x4C6B60],
    '004CC680': [0x4CC100, 0x4CC310, 0x4CC360, 0x4CC680, 0x4CC6D0],
    '004F6E70': [0x4F9610, 0x4F9970, 0x509130],
    '0054E690': [0x54E3B0, 0x54E4D0, 0x54E590, 0x54E690, 0x54E6F0, 0x54E750,
                 0x54E7B0],
    '006E5850': [0x6E5320, 0x6E53A0, 0x6E55A0, 0x6E55B0, 0x6E5850],
    '007262D0': [0x726250, 0x726290, 0x7262D0, 0x726310, 0x726350,
                 0x726FE0, 0x727010],
    '00726310': [0x726250, 0x726290, 0x7262D0, 0x726310, 0x726350,
                 0x726FE0, 0x727010],
    '00726350': [0x726250, 0x726290, 0x7262D0, 0x726310, 0x726350,
                 0x726FE0, 0x727010],
    '00726630': [0x725FA0, 0x7263A0, 0x726400, 0x7264C0, 0x7265C0, 0x726630,
                 0x726720],
    '00727120': [0x726FE0, 0x727010, 0x727120, 0x7271E0, 0x7275D0, 0x727880],
}


# --------------------------------------------------------------------------- PE
class Image(object):
    def __init__(self, path):
        self.pe = pefile.PE(path, fast_load=True)
        self.base = self.pe.OPTIONAL_HEADER.ImageBase
        self.secs = []
        for s in self.pe.sections:
            nm = s.Name.rstrip(b'\x00').decode('latin-1')
            self.secs.append(dict(name=nm, va=self.base + s.VirtualAddress,
                                  vsize=s.Misc_VirtualSize,
                                  rsize=s.SizeOfRawData, data=s.get_data()))
        end = max(s['va'] + max(s['vsize'], s['rsize']) for s in self.secs)
        self.buf = bytearray(end - self.base + 16)
        for s in self.secs:
            off = s['va'] - self.base
            d = s['data']
            self.buf[off:off + len(d)] = d

    def sec_of(self, va):
        for s in self.secs:
            if s['va'] <= va < s['va'] + max(s['vsize'], s['rsize']):
                return s['name']
        return None

    def u32(self, va):
        off = va - self.base
        if off < 0 or off + 4 > len(self.buf):
            return None
        return int.from_bytes(self.buf[off:off + 4], 'little')

    def bytes_at(self, va, n):
        off = va - self.base
        return bytes(self.buf[off:off + n])

    def cstr(self, va, n=300):
        off = va - self.base
        if off < 0 or off >= len(self.buf):
            return None
        e = self.buf.find(b'\x00', off, min(off + n, len(self.buf)))
        if e < 0:
            return None
        return bytes(self.buf[off:e]).decode('latin-1', 'replace')

    def secs_named(self, *names):
        want = set(names)
        return [s for s in self.secs if s['name'] in want]


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest().upper()


# --------------------------------------------------------------------------- atlas
def load_atlas():
    """entry(小写) -> dict(size,n_instr,n_callers,n_callees,is_fnptr)。atlas 的 entry 是小写。"""
    out = {}
    if not os.path.exists(ATLAS):
        return out
    for i, ln in enumerate(open(ATLAS, encoding='utf-8-sig')):
        if i == 0:
            continue
        c = ln.rstrip('\n').split('\t')
        if len(c) < 2:
            continue
        try:
            a = int(c[0].strip(), 16)
        except ValueError:
            continue
        def num(k):
            try:
                return int(c[k])
            except (IndexError, ValueError):
                return -1
        out[a] = dict(size=num(1), n_instr=num(2), n_callers=num(3),
                      n_callees=num(4), is_fnptr=c[5] if len(c) > 5 else '?',
                      raw=c[0].strip())
    return out


# --------------------------------------------------------------------------- 代码扫描
REL_BRANCH_MN = ('call', 'jmp', 'jae', 'jbe', 'jcxz', 'je', 'jecxz', 'jg',
                 'jge', 'jl', 'jle', 'jna', 'jnae', 'jnb', 'jnbe', 'jnc',
                 'jne', 'jng', 'jnge', 'jnl', 'jnle', 'jno', 'jnp', 'jns',
                 'jnz', 'jo', 'jp', 'jpe', 'jpo', 'js', 'jz')


class Text(object):
    """一次 capstone 反汇编 .text（skipdata=True），供所有 entry 查表。"""

    def __init__(self, img):
        t = img.secs_named('.text')[0]
        self.lo = t['va']
        n = min(len(t['data']), t['vsize'] or len(t['data']))
        self.code = bytes(t['data'][:n])
        self.hi = self.lo + len(self.code)
        self.insns = []                     # 顺序
        self.at = {}                        # va -> insn 下标
        self.calls = collections.defaultdict(list)   # 落点 -> [site]
        self.jmps = collections.defaultdict(list)
        self.imm_ref = collections.defaultdict(list)  # imm -> [(site, form)]
        self.vptr_installs = collections.defaultdict(list)  # vt -> [site]
        md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
        md.detail = True
        md.skipdata = True
        self.n_skip = 0
        X = capstone.x86
        for ins in md.disasm(self.code, self.lo):
            if ins.id == 0:
                self.n_skip += 1
                continue
            k = len(self.insns)
            self.at[ins.address] = k
            self.insns.append(ins)
            mn = ins.mnemonic
            ops = ins.operands
            if mn in REL_BRANCH_MN and ops and ops[0].type == X.X86_OP_IMM:
                tgt = ops[0].imm & 0xFFFFFFFF
                (self.calls if mn == 'call' else self.jmps)[tgt].append(ins.address)
            for j, o in enumerate(ops):
                if o.type != X.X86_OP_IMM:
                    continue
                imm = o.imm & 0xFFFFFFFF
                if not (IMAGE_BASE <= imm < IMAGE_BASE + 0x2000000):
                    continue
                form = mn
                if mn == 'mov' and j == 0 and o.type == X.X86_OP_IMM:
                    form = 'mov_reg_imm'
                elif mn == 'mov' and ops[0].type == X.X86_OP_MEM:
                    form = 'mov_mem_imm'
                    self.vptr_installs[imm].append(ins.address)
                elif mn == 'push':
                    form = 'push_imm'
                self.imm_ref[imm].append((ins.address, form))

    def walk(self, va, max_bytes=400):
        """从 va 顺序走，遇到 ret / 已走过 / 长度上限停。返回 (指令列表, 字节数)。"""
        out = []
        k = self.at.get(va)
        if k is None:
            return out, 0
        for ins in self.insns[k:]:
            if ins.address >= va + max_bytes:
                break
            out.append(ins)
            if ins.mnemonic in ('ret', 'retf', 'iret'):
                break
        if not out:
            return out, 0
        end = out[-1].address + out[-1].size
        return out, end - va


# --------------------------------------------------------------------------- RTTI
def col_of(img, vt_start):
    """表起点-4 是 COL 指针（绝对 VA）；COL.pTypeDescriptor 也是绝对 VA；装饰名在 TD+8 内联。"""
    col_va = img.u32(vt_start - 4)
    if col_va is None or not (IMAGE_BASE <= col_va < IMAGE_BASE + len(img.buf)):
        return None
    if col_va - IMAGE_BASE + 20 > len(img.buf) or img.u32(col_va) != 0:
        return None
    td_va = img.u32(col_va + 12)
    if td_va is None or not (IMAGE_BASE <= td_va < IMAGE_BASE + len(img.buf)):
        return None
    nm = img.cstr(td_va + 8, 300)
    if not nm or not nm.startswith('.?A'):
        return None
    return dict(col=col_va, td=td_va, name=nm, pchd=img.u32(col_va + 16))


def dd_hits(img, va, secnames=('.rdata', '.data', '.detour')):
    """对齐 dd 命中（可能先只找到槽中段）。"""
    hits = []
    pat = va.to_bytes(4, 'little')
    for s in img.secs_named(*secnames):
        d = s['data']
        i = d.find(pat)
        while i >= 0:
            if i % 4 == 0:
                hits.append(s['va'] + i)
            i = d.find(pat, i + 1)
    return hits


def vtable_of(img, hit, max_slots=1024):
    """从命中往回走到表起点，返回 (起点, COL)。"""
    best = None
    for k in range(max_slots):
        v = hit - k * 4
        if v <= IMAGE_BASE + 4:
            break
        if img.sec_of(v) is None or img.sec_of(v - 4) is None:
            continue
        c = col_of(img, v)
        if c is not None:
            best = (v, c)
        elif best is not None:
            break
    return best


def raw_occurrences(img, va, secname):
    """整段裸 4 字节出现次数（任意对齐）—— ground truth。"""
    s = img.secs_named(secname)
    if not s:
        return 0
    pat = va.to_bytes(4, 'little')
    d = s[0]['data']
    n = 0
    i = d.find(pat)
    while i >= 0:
        n += 1
        i = d.find(pat, i + 1)
    return n


def rtti_by_name(img, cls):
    """在 .rdata/.data 里找 `.?AV<cls>@@` 装饰名（TD+8 内联串），返回 TD VA 列表。"""
    out = []
    for s in img.secs_named('.rdata', '.data'):
        d = s['data']
        for pat in ('\\.?AV%s@@' % cls).encode('latin-1'), \
                   ('\\.?AV%s@' % cls).encode('latin-1'):
            i = d.find(pat)
            while i >= 0:
                out.append(s['va'] + i - 8)      # 串在 TD+8
                i = d.find(pat, i + 1)
    return sorted(set(out))


# --------------------------------------------------------------------------- 序言/中段
def prologue_kind(b):
    """b 是入口字节。返回序言形状或 None。"""
    if len(b) < 4:
        return None
    if b[0] == 0x55 and b[1] == 0x8B and b[2] == 0xEC:
        return 'push ebp;mov ebp,esp'
    if b[0] == 0x8B and b[1] == 0xFF:
        return 'mov edi,edi(热补丁位)'
    if b[0] == 0x83 and b[1] == 0xEC:
        return 'sub esp,imm8'
    if b[0] == 0x81 and b[1] == 0xEC:
        return 'sub esp,imm32'
    # push <regs...> 后紧跟 mov esi/edi,ecx（VC6 thiscall）
    i = 0
    while i < len(b) and b[i] in (0x51, 0x52, 0x53, 0x55, 0x56, 0x57):
        i += 1
    if i:
        tail = b[i:i + 2]
        if tail == b'\x8b\xf1' or tail == b'\x8b\xf9' or tail == b'\x8b\xe9':
            return 'push regs;mov reg,ecx'
        if i >= 1:
            return 'push regs'
    if b[0] == 0x64 and b[1] == 0xA1:
        return 'mov eax,fs:0'
    return None


def boundary_before(img, va, atlas, n=16):
    """入口前 16 字节：前一个 atlas 函数在哪结束、是不是 ret+填充。"""
    keys = atlas_keys
    k = bisect.bisect_left(keys, va) - 1
    prev = keys[k] if k >= 0 else None
    prevend = prev + atlas[prev]['size'] if prev is not None else None
    b = img.bytes_at(va - n, n)
    rets = [i for i, x in enumerate(b) if x in (0xC3, 0xC2, 0xCB, 0xCA)]
    pad_after = None
    if rets:
        j = rets[-1]
        # c2 xx xx 是三字节 ret imm16
        tail = j + (3 if b[j] == 0xC2 and j + 2 < len(b) else 1)
        pad = b[tail:]
        if pad and all(x in (0x90, 0xCC, 0x00) for x in pad):
            pad_after = len(pad)
    return dict(prev=prev, prevend=prevend, prev_gap=(va - prevend) if prevend else None,
                head=b.hex(), pad_after=pad_after)


# --------------------------------------------------------------------------- YRpp 名字→地址
def load_yrpp_table():
    """解析 YRpp/**/*.h 的 JMP_THIS/JMP_STD(0x...) → {addr: [(cls, meth, file:line)]}
    与 {(cls,meth): [(addr, file:line)]}。YRpp 是「名字→地址」在本仓库里的权威源。"""
    addr2 = collections.defaultdict(list)
    name2 = collections.defaultdict(list)
    rx = re.compile(r'(JMP_THIS|JMP_STD|CALL_THIS|CALL_STD)\s*\(\s*0x([0-9A-Fa-f]+)\s*\)')
    rx_cls = re.compile(r'^\s*(?:class|struct)\s+(\w+)')
    rx_meth = re.compile(r'(~?\w+)\s*\(')
    files = []
    for dirpath, _dirs, fs in os.walk(YRPP):
        for f in fs:
            if f.endswith(('.h', '.hpp')):
                files.append(os.path.join(dirpath, f))
    for path in files:
        try:
            lines = open(path, encoding='utf-8', errors='replace').read().split('\n')
        except OSError:
            continue
        cur = ''
        for i, ln in enumerate(lines):
            mc = rx_cls.match(ln)
            if mc:
                cur = mc.group(1)
            m = rx.search(ln)
            if not m:
                continue
            addr = int(m.group(2), 16)
            meth = None
            for back in range(i, max(-1, i - 12), -1):
                mm = rx_meth.search(lines[back])
                if mm and 'JMP' not in lines[back] and \
                   mm.group(1) not in ('if', 'for', 'while', 'return', 'sizeof'):
                    meth = mm.group(1)
                    break
            rel = '%s:%d' % (os.path.basename(path), i + 1)
            addr2[addr].append((cur, meth, rel))
            if meth:
                name2[(cur, meth)].append((addr, rel))
    return addr2, name2


# --------------------------------------------------------------------------- 内联副本搜索
def inline_twins(img, text, va, max_bytes=400):
    """把函数体的 rel 位移字节打码，取最长静态 run 当 needle，全 .text 找同样体
    （长度 >= 8 字节）。用来解释「为什么 0 调用者」——被内联到别处了。
    返回 [(site_va, 匹配指令数)] 或 []。"""
    insns, size = text.walk(va, max_bytes)
    if len(insns) < 4:
        return [], size, len(insns)
    body = b''.join(x.bytes for x in insns)
    mask = bytearray([1]) * len(body)
    off = 0
    for x in insns:
        n = len(x.bytes)
        if x.mnemonic in REL_BRANCH_MN:
            for j in range(1, n):          # 相对位移字节打码
                mask[off + j] = 0
        elif x.mnemonic == 'mov' and x.operands and \
                x.operands[0].type == capstone.x86.X86_OP_MEM:
            pass
        off += n
    # 最长静态 run
    best, cur, start = (0, 0, 0), 0, 0
    for i, m in enumerate(mask):
        if m:
            if cur == 0:
                start = i
            cur += 1
            if cur > best[0]:
                best = (cur, start, i + 1)
        else:
            cur = 0
    run_len, run_start, run_end = best
    if run_len < 8:
        return [], size, len(insns)
    needle = body[run_start:run_end]
    text_lo = text.lo
    code = text.code
    found = []
    i = code.find(needle)
    while i >= 0:
        site = text_lo + i - run_start
        if site != va:
            # 整段核对（打码位置不比）
            ok = True
            s_off = i - run_start
            if s_off < 0 or s_off + len(body) > len(code):
                ok = False
            else:
                for j in range(len(body)):
                    if mask[j] and code[s_off + j] != body[j]:
                        ok = False
                        break
            if ok:
                found.append(site)
        i = code.find(needle, i + 1)
    return found, size, len(insns)


# --------------------------------------------------------------------------- 主
atlas = {}
atlas_keys = []


def main():
    global atlas, atlas_keys
    out = io.StringIO()

    def say(*a):
        s = ' '.join(str(x) for x in a)
        out.write(s + '\n')
        print(s)

    sha = sha256(EXE)
    say('binary sha256 :', sha, 'MATCH' if sha == EXPECT_SHA else '!! MISMATCH')
    img = Image(EXE)
    say('image base    : 0x%08X' % img.base)
    for s in img.secs:
        say('  section %-8s va=0x%08X vsize=0x%X rsize=0x%X'
            % (s['name'], s['va'], s['vsize'], s['rsize']))

    atlas = load_atlas()
    atlas_keys = sorted(atlas)
    say('atlas entries :', len(atlas))

    text = Text(img)
    say('.text insns   :', len(text.insns), '(skipdata', text.n_skip, ')')

    # all848 的原始结论（对比用）
    a848 = {}
    if os.path.exists(ALL848):
        for i, ln in enumerate(open(ALL848, encoding='utf-8')):
            if i == 0:
                continue
            c = ln.rstrip('\n').split('\t')
            if len(c) >= 15:
                a848[c[1]] = dict(vt=int(c[4]), direct=int(c[8]),
                                  tref=int(c[10]), dref=int(c[11]),
                                  form=c[13])
    # coverage 的级别/证据栏
    cov = {}
    for ln in open(COV, encoding='utf-8'):
        c = ln.rstrip('\n').split('\t')
        if len(c) >= 6 and re.match(r'^[0-9A-Fa-f]{8}$', c[0]):
            cov[c[0].upper()] = dict(grade=c[4], ev=c[5])

    yrpp_addr2, yrpp_name2 = load_yrpp_table()
    say('YRpp JMP 地址 :', len(yrpp_addr2), '个地址 /', len(yrpp_name2), '个方法名')

    syms = {}
    if os.path.exists(SYMS):
        d = json.load(open(SYMS, encoding='utf-8', errors='replace'))
        for k, v in d.get('classes', {}).items():
            syms[k.lower()] = v

    rows_out = []
    facts = {}
    dis = io.StringIO()

    for entry, sub, name in ROWS:
        va = int(entry, 16)
        f = dict(entry=entry, subsystem=sub, name=name)
        cls = name.split('::')[0] if '::' in name else ''
        meth = name.split('::')[1] if '::' in name else ''

        # ---- 问1 像不像函数
        head = img.bytes_at(va, 32)
        pk = prologue_kind(head)
        insns, body_size = text.walk(va, 400)
        inat = atlas.get(va)
        looks = bool(pk) and len(insns) >= 2

        # ---- 问2 中段/错位
        alt = []
        for back in range(1, 17):
            p = va - back
            if p in atlas and prologue_kind(img.bytes_at(p, 8)):
                alt.append((p, atlas[p]['size'], prologue_kind(img.bytes_at(p, 8))))
        bnd = boundary_before(img, va, atlas)

        # ---- 问3 独立复算引用
        e8 = len(text.calls.get(va, []))
        e9 = len(text.jmps.get(va, []))
        imm = text.imm_ref.get(va, [])
        imm_forms = collections.Counter(x[1] for x in imm)
        t_raw = raw_occurrences(img, va, '.text')
        d_raw = {s: raw_occurrences(img, va, s) for s in ('.rdata', '.data',
                                                          '.detour', '.rsrc')}
        hits = dd_hits(img, va)
        vts = []
        for h in hits:
            got = vtable_of(img, h)
            vts.append(dict(hit=h, vt=got[0] if got else None,
                            slot=((h - got[0]) // 4) if got else None,
                            col=got[1]['name'] if got else None))

        # ---- 问4 名字↔地址
        y_by_addr = yrpp_addr2.get(va, [])
        y_by_name = yrpp_name2.get((cls, meth), []) + \
            yrpp_name2.get((cls, '~' + meth), [])
        td = rtti_by_name(img, cls) if cls else []
        vt_rec = syms.get(cls.lower())
        # ctor 真身：谁装了这个类的 vptr
        ctor_sites = []
        real_cls_in_y = []
        if vt_rec:
            vtv = int(vt_rec['vtable_va'], 16) if vt_rec.get('vtable_va') else None
            if vtv:
                ctor_sites = text.vptr_installs.get(vtv, [])
                real_cls_in_y.append(vtv)
        twins, wsize, winsn = inline_twins(img, text, va)

        # ---- 名字判定
        verdict = '无法判定'
        reason = []
        if alt:
            verdict = '地址错位'
            reason.append('前 16 字节内发现序言 @0x%08X' % alt[0][0])
        elif not inat:
            verdict = '无法判定'
            reason.append('不在 atlas 且前 16B 无序言')
        else:
            # 地址是函数起点；再看名字
            ynames = set()
            for c_, m_, rel in y_by_addr:
                if m_:
                    ynames.add('%s::%s' % (c_, m_))
            claimed_ok = any(
                (c_ == cls and m_ and (m_ == meth or m_ == '~' + meth))
                for c_, m_, _ in y_by_addr)
            if claimed_ok:
                verdict = '地址可信'
                reason.append('YRpp 同一地址声明即为本名')
            elif y_by_addr:
                verdict = '名字可疑'
                reason.append('YRpp 同址声明为 ' + '/'.join(sorted(ynames)) if ynames
                              else 'YRpp 同址声明（已解析）')
            else:
                # YRpp 没有该地址：看名字-side 有没有地址
                if y_by_name:
                    addr_s = ','.join('0x%08X' % a for a, _ in y_by_name)
                    verdict = '名字可疑'
                    reason.append('YRpp 给该名声明的是 ' + addr_s)
                elif vt_rec and meth and meth == cls:
                    verdict = '名字可疑'
                    reason.append('该类 ctor 在 YRpp 里是内联体，无地址')
                else:
                    verdict = '无法判定'
                    reason.append('YRpp 无此地址亦无此名')

        f.update(
            in_atlas=('yes(%dB,n_callers=%s)' % (inat['size'], inat['n_callers'])
                      if inat else 'no'),
            looks_like_func=('yes[%s] %dB/%dinsn' % (pk, body_size, len(insns))
                             if looks else 'no'),
            prologue_within_16=('0x%08X' % alt[0][0]) if alt else 'none',
            real_func_start=('0x%08X' % alt[0][0]) if alt else entry,
            head=head[:16].hex(),
            vt_recheck='%d%s' % (len(hits), '' if not vts else
                                 '[' + ';'.join(
                                     ('vt%08X slot%s %s' % (x['vt'], x['slot'], x['col'])
                                      if x['vt'] else 'no-COL@%08X' % x['hit'])
                                     for x in vts) + ']'),
            text_refs='%d(e8=%d,e9=%d,imm=%d%s,raw=%d)' % (
                e8, e8, e9, len(imm),
                '' if not imm_forms else ':' + '/'.join(
                    '%s%d' % (k, v) for k, v in sorted(imm_forms.items())),
                t_raw),
            data_refs='%d(rdata=%d,data=%d,detour=%d,rsrc=%d)' % (
                sum(d_raw.values()), d_raw['.rdata'], d_raw['.data'],
                d_raw['.detour'], d_raw['.rsrc']),
            cls_rtti=('yes(td=0x%08X%s)' % (td[0], '' if len(td) == 1
                                            else 'x%d' % len(td))) if td
                     else ('no(non-polymorphic or missing)'),
            yrpp_same_addr='/'.join('%s::%s@%s' % (c_, m_, rel)
                                    for c_, m_, rel in y_by_addr) or '-',
            yrpp_name_addr=','.join('0x%08X@%s' % (a, rel) for a, rel in y_by_name) or '-',
            ctor_vptr_installs=','.join('0x%08X' % x for x in ctor_sites[:6]) or '-',
            twins=','.join('0x%08X' % x for x in twins[:6]) or '-',
            n_twins=len(twins),
            verdict=verdict,
            reason='; '.join(reason),
        )
        facts[entry] = f

        # ---- 落盘用细节
        dis.write('=' * 78 + '\n')
        dis.write('%s %s %s  head=%s\n' % (entry, sub, name, head.hex(' ')))
        dis.write('  atlas      : %s\n' % f['in_atlas'])
        dis.write('  prologue   : %s   body=%dB %dinsn\n' % (pk, body_size, len(insns)))
        dis.write('  boundary   : prev=0x%08X end=%s gap=%s pad_after=%s\n' % (
            bnd['prev'] or 0,
            ('0x%08X' % bnd['prevend']) if bnd['prevend'] else '-',
            bnd['prev_gap'], bnd['pad_after']))
        dis.write('  head16 = %s\n' % head[:16].hex(' '))
        for x in insns[:14]:
            dis.write('     %08X  %-20s %s %s\n' % (x.address, x.bytes.hex(),
                                                    x.mnemonic, x.op_str))
        if len(insns) > 14:
            dis.write('     ... (%d insns total, %dB to ret)\n' % (len(insns), body_size))
        dis.write('  refs       : e8=%d e9=%d imm=%d raw_text=%d data=%s\n' % (
            e8, e9, len(imm), t_raw, d_raw))
        dis.write('  dd hits    : %s\n' % (vts or 'none'))
        dis.write('  RTTI       : td=%s  vtable=%s\n' % (
            ['0x%08X' % x for x in td] or '-',
            vt_rec.get('vtable_va') if vt_rec else '-'))
        dis.write('  yrpp addr→ : %s\n' % f['yrpp_same_addr'])
        dis.write('  yrpp name→ : %s\n' % f['yrpp_name_addr'])
        dis.write('  ctor vptr install sites: %s\n' % f['ctor_vptr_installs'])
        dis.write('  inline twins (%d): %s\n' % (len(twins),
                                                 f['twins']))
        dis.write('  all848     : %s\n' % a848.get(entry, '-'))
        dis.write('  verdict    : %s   (%s)\n' % (verdict, f['reason']))

        rows_out.append(f)

    # ---- 同族邻居的调用计数
    sib = {}
    for entry, sub, name in ROWS:
        va = int(entry, 16)
        s = []
        for a in SIBLINGS.get(entry, []):
            s.append(dict(va=a, calls=len(text.calls.get(a, [])),
                          in_atlas=a in atlas,
                          atlas_callers=atlas.get(a, {}).get('n_callers')))
        sib[entry] = s
    facts['_siblings'] = sib

    # ---- rows.tsv
    hdr = ['entry', 'subsystem', 'name', 'in_atlas', 'looks_like_func',
           'prologue_within_16', 'real_func_start', 'vt_count_recheck',
           'text_refs_recheck', 'data_refs_recheck', 'class_rtti_exists',
           'name_addr_verdict', 'reason']
    with open(os.path.join(HERE, 'rows.tsv'), 'w', encoding='utf-8', newline='') as fh:
        fh.write('\t'.join(hdr) + '\n')
        for f in rows_out:
            fh.write('\t'.join([
                f['entry'], f['subsystem'], f['name'], f['in_atlas'],
                f['looks_like_func'], f['prologue_within_16'],
                f['real_func_start'], f['vt_recheck'], f['text_refs'],
                f['data_refs'], f['cls_rtti'], f['verdict'],
                (f['reason'] + ' | head=' + f['head'] +
                 ' | yrpp@addr=' + f['yrpp_same_addr'] +
                 ' | yrpp@name=' + f['yrpp_name_addr'] +
                 ' | twin=' + f['twins']).replace('\t', ' '),
            ]) + '\n')

    with open(os.path.join(HERE, 'facts.json'), 'w', encoding='utf-8') as fh:
        json.dump(facts, fh, ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(HERE, 'disasm_11.txt'), 'w', encoding='utf-8') as fh:
        fh.write(out.getvalue() + '\n\n' + dis.getvalue())

    # ---- 摘要
    say('')
    cnt = collections.Counter(f['verdict'] for f in rows_out)
    say('verdict 汇总 :', dict(cnt))
    for f in rows_out:
        say('%-9s %-38s %-8s %s' % (f['entry'], f['name'], f['verdict'],
                                    f['reason'][:70]))
    say('')
    say('同族邻居调用数（e8 call 数 / atlas n_callers）:')
    for entry in [r[0] for r in ROWS]:
        s = sib[entry]
        say('  %s : %s' % (entry, '  '.join(
            '0x%08X:c=%d(a=%s%s)' % (x['va'], x['calls'], x['atlas_callers'],
                                     '' if x['in_atlas'] else ',NOT-IN-ATLAS')
            for x in s)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
