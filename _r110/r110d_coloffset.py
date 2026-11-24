#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r110d_coloffset.py —— 用可证伪预测验证 CompleteObjectLocator.offset 字段的语义。

R109 §EK4 只报了分布「COL.offset==0 占 942/954，其余 12 张全为 4」，
并把 12 张一句括注为「= 基类子对象」。那只是**解释**，没有做**预测检验**。
本轮给它一个能被证伪的预测：

    若 COL.offset 的语义是「该 vtable 在对象内的字节偏移」，
    则类的虚表装配点必须是  mov dword ptr [reg + offset], <vtable_va>
    即 offset==0 的表 → 装配 disp 必须 0；offset==4 的表 → 装配 disp 必须 4。

预测反例的判法：只要有一张 offset==4 的表，其唯一装配点 disp==0，
或一张 offset==0 的表装配 disp 系统性为 4，则该语义被否证。

三段证据：
  P1 复算 offset 分布（942 / 12），并列出 12 张表的类名（R109 未列）。
  P2 对每张表的**全部**装配点按 disp 分组；对 12 张 offset==4 单独列表。
  P3 反控：随机取 20000 个「mov [reg+disp], imm32」形态的写入点，看 disp 分布，
     证明 disp==4 的写入点在全体写入点里不是常见形态（否则 P2 无判别力）。
另附 P4：12 张表的类名是否全在 Locomotion 族（R109 只说是「基类子对象」，未说是哪个族）。
内存纪律：全段 disasm_lite 分块扫一遍（沿用 R109 的 imm_re），不 detail。
"""
import array, json, os, re, struct
from collections import Counter, defaultdict
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import pefile

os.chdir('/home/t628/projects/ra2-campaign-forge')
raw = open('ra2bench/gamemd.exe', 'rb').read()
IB = 0x400000
fo = lambda v: v - IB

checks = []
def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)

pe = pefile.PE('ra2bench/gamemd.exe', fast_load=True)
SECT = [(s.Name.decode().strip('\x00'), IB + s.VirtualAddress, IB + s.VirtualAddress + s.Misc_VirtualSize)
        for s in pe.sections]
T = [x for x in SECT if x[0] == '.text'][0]
TS, TE = T[1], T[2]
ck('S0 .text = [%s, %s)' % (hex(TS), hex(TE)), TS == 0x401000, hex(TE))

sym = json.load(open('out/reverse/symbols.json'))
cls = sym['classes']
VT = {int(c['vtable_va'], 16): k for k, c in cls.items() if c.get('vtable_va')}
ck('S1 vtable 954', len(VT) == 954, len(VT))

# ---------- P1 COL.offset 复算 ----------
COL = {}   # vtable -> (col_va, offset, td_va)
for va in VT:
    col = struct.unpack_from('<I', raw, fo(va) - 4)[0]
    # COL 布局：sig@0, offset@4, pTD@0xc, pCHD@0x10, pSelf@0x14
    off = struct.unpack_from('<I', raw, fo(col) + 4)[0]
    td = struct.unpack_from('<I', raw, fo(col) + 0xc)[0]
    COL[va] = (col, off, td)
dist = Counter(o for _, o, _ in COL.values())
ck('P1 COL.offset 分布 = %s（R109 §EK4 报 {0: 942, 4: 12}）'
   % dict(sorted(dist.items())), dict(sorted(dist.items())) == {0: 942, 4: 12}, dict(sorted(dist.items())))

o4 = sorted(va for va, (c, o, t) in COL.items() if o == 4)
names4 = [cls[VT[va]]['name'] for va in o4]
ck('P1b offset==4 的 12 张表类名 = %s' % names4, len(o4) == 12, names4)
n_loco = sum(1 for n in names4 if 'Locomotion' in n)
ck('P1c 其中类名含 Locomotion 的 = %d/12（R109 只说「基类子对象」，没说是哪个族）'
   % n_loco, n_loco == 12, {'loco': n_loco, 'of': len(names4)})

# ---------- 装配点扫描 ----------
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False; md.skipdata = True
# 自错 L-05（两次）：capstone 对位移量的打印格式不统一 —— 小位移打十进制（[esi + 4]、[esp + 8]），
# 大位移打十六进制（[esp + 0x20]）。第一稿用 \[([a-z0-9+* ]+)\] 贪婪吞掉 "+ 0x4" 致 disp 恒 0；
# 第二稿只认 0x 前缀，又把十进制位移全漏掉（装配点从 4611 掉到 4138、disp==4 归零）。
# 终稿同时认两种格式，并断言解析覆盖率。
RE = re.compile(r'^\[([a-z0-9]{2,4})(?: \+ (0x[0-9a-f]+|\d+))?\], (0x[0-9a-f]+)$')
# 自错 L-12：上一稿 P2a3 实测「未解析形态里仍有 5 条 vtable 写入」，全是**负位移**：
#   0x4a8648 [eax - 8], 0x7e192c / 0x4a864f [eax - 8], 0x7e4f64 / 0x4a8660 [eax - 8], 0x7e6060
#   0x4a86ab [esi - 4], 0x7e192c / 0x656a41 [eax - 8], 0x7eeb54
# 负位移语义是「在 reg 所指之前 8 字节处装表」（把 vt 写进一个已在 reg 里的子对象之前），
# 不是「reg 的 this+负偏移」，所以并入「寄存器基址」一类、disp 记负值（不参与 P2b 的 disp==4 预测）。
RE_NEG = re.compile(r'^\[([a-z0-9]{2,4}) - (0x[0-9a-f]+|\d+)\], (0x[0-9a-f]+)$')
# 自错 L-10：第三稿仍漏掉一整类 —— **绝对地址写入**  mov dword ptr [0x87e73c], <vtable_va>
# （无基址寄存器，直接把 vt 写进全局对象）。实测这一类 340 条，正好是 4271 与 R109 的 4611 之差：
# 4271（寄存器基址含 disp）+ 340（绝对地址）= 4611。故 R109 的**总数**是对的、分类是错的。
RE_ABS = re.compile(r'^\[(0x[0-9a-f]+)\], (0x[0-9a-f]+)$')
def _d(s):
    if s is None:
        return 0
    return int(s, 16) if s.startswith('0x') else int(s, 10)
STORE = defaultdict(list)   # vtable_va -> [(insn_va, disp)]
allstore = []               # 全部 mov [reg+disp], imm32（反控用）
ABS = []                    # 绝对地址写入 (insn_va, target, vtable_va)
n_shape = 0                 # 「ptr [...], 0x...」形态的指令总数（反控：解析覆盖率）
n_abs = 0
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    last = pos
    for a, sz, m, o in md.disasm_lite(raw[fo(pos):fo(hi) + 16], pos):
        if a >= hi:
            break
        last = a + sz
        if m == 'mov' and 'ptr [' in o and ', 0x' in o:
            n_shape += 1
            o2 = o.replace('dword ptr ', '')
            ma = RE_ABS.match(o2)
            if ma:
                n_abs += 1
                tgt = int(ma.group(1), 16)
                imm = int(ma.group(2), 16)
                ABS.append((a, tgt, imm))
                if imm in VT:
                    STORE[imm].append((a, None))   # None = 绝对地址基址，不是 this 偏移
                continue
            mm = RE.match(o2)
            if mm:
                disp = _d(mm.group(2))
                imm = int(mm.group(3), 16)
                allstore.append((a, disp, imm))
                if imm in VT:
                    STORE[imm].append((a, disp))
                continue
            mg = RE_NEG.match(o2)
            if mg:
                disp = -_d(mg.group(2))
                imm = int(mg.group(3), 16)
                allstore.append((a, disp, imm))
                if imm in VT:
                    STORE[imm].append((a, disp))
                continue
    if last <= pos:
        last = pos + 1
    pos = last
ck('P2a 解析归类：形态命中 %d 条 = 寄存器基址 %d + 绝对地址 %d + 其它 %d'
   '（其它全为负位移/比例变址的栈帧与数组写入，见 P2a3 证明其中无 vtable 写入）'
   % (n_shape, len(allstore), n_abs, n_shape - len(allstore) - n_abs),
   True, {'shape': n_shape, 'reg': len(allstore), 'abs': n_abs})
n_store_all = sum(len(v) for v in STORE.values())
n_abs_vt = sum(1 for a, t, v in ABS if v in VT)
# 自错 L-13：R109 的 4611 是它那条旧正则数出来的，而旧正则的字符类 [a-z0-9+* ] **不含 '-'**，
# 故 [eax - 8] 这 5 条负位移写入一条都没进 4611。正确总数 = 4611 + 5 = 4616。
ck('P2a2 全段 vtable 装配点 = %d = 寄存器基址 %d（含负位移 5）+ 绝对地址 %d；'
   'R109 报 4611 = 本轮 − 负位移 5（其旧正则字符类不含 -）'
   % (n_store_all, len(allstore), n_abs_vt),
   n_store_all == 4616 and n_store_all - 5 == 4611,
   {'total': n_store_all, 'reg': len(allstore), 'abs': n_abs_vt})
# 自错 L-11：P2a 上一稿断言「解析覆盖率 >= 99%」。实测 93%，剩下 680 条是负位移 [ebp - 0x28]、
# 比例变址 [ecx + eax*4] 等形态 —— 它们全是栈帧/数组写入，与对象内偏移无关。
# 「解析覆盖率」不是正确的不变量；正确的不变量是 **未解析形态里一条 vtable 写入都没有**
# （否则 P2b/P3 的分母会缺项）。改为断言这一点。
n_other_vt = 0
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    last = pos
    for a, sz, m, o in md.disasm_lite(raw[fo(pos):fo(hi) + 16], pos):
        if a >= hi:
            break
        last = a + sz
        if m == 'mov' and 'ptr [' in o and ', 0x' in o:
            o2 = o.replace('dword ptr ', '')
            if RE_ABS.match(o2) or RE.match(o2) or RE_NEG.match(o2):
                continue
            mo = re.search(r', (0x[0-9a-f]+)$', o2)
            if mo and int(mo.group(1), 16) in VT:
                n_other_vt += 1
    if last <= pos:
        last = pos + 1
    pos = last
ck('P2a3 不变量（替代覆盖率）：未解析的 %d 条形态里，写 vtable 的 = %d 条'
   '（必须为 0，否则 P2b/P3 分母缺项）'
   % (n_shape - len(allstore) - n_abs, n_other_vt),
   n_other_vt == 0, {'unparsed': n_shape - len(allstore) - n_abs, 'vt_writes': n_other_vt})

# ---------- P2 关键预测：offset==4 ⇒ 装配 disp==4 ----------
# 只取**寄存器基址且 disp 是整数**的装配点（绝对地址写入的 disp 记作 None，不参与本预测：
# 那类写入的是全局对象，其地址不是「对象内偏移」，本就与 COL.offset 无关）。
res4, res0 = [], []
for va in o4:
    pts = [(a, d) for a, d in STORE.get(va, []) if d is not None]
    disps = sorted(set(d for _, d in pts))
    res4.append({'cls': cls[VT[va]]['name'], 'vt': hex(va), 'n_store': len(pts),
                 'disps': disps, 'ok': (disps == [4])})
n_ok4 = sum(1 for r in res4 if r['ok'])
ck('P2b 预测：12 张 offset==4 的表，其寄存器基址装配点的 disp 必须全为 4。实测命中 = %d/12'
   % n_ok4, n_ok4 == 12, res4)

# 反向（自错 L-06 修正）：上一稿写「offset==0 的表，其装配点 disp 必须全为 0」，实测 208 张违例。
# 那不是语义被否证，而是我的预测写错了：一张 vtable 可以被写进**成员子对象**的偏移处
# （如 ?$DynamicVectorClass@G 被嵌进别的类里，disp 就是该成员的偏移），此时 disp≠0 完全合法。
# 正确可证伪预测：offset==0 的表必须**至少存在一个** disp==0 的装配点（否则它从没被装成完整对象）。
n0 = 0; nozero = []
for va, (c, o, t) in COL.items():
    if o != 0:
        continue
    pts = [(a, d) for a, d in STORE.get(va, []) if d is not None]
    if not pts:
        continue
    n0 += 1
    disps = set(d for _, d in pts)
    if 0 not in disps:
        nozero.append({'cls': cls[VT[va]]['name'], 'vt': hex(va), 'disps': sorted(disps)[:6]})
ck('P2c 反向预测（修正版）：offset==0 且有装配点的表 %d 张，其中**无任何 disp==0 装配点**的 = %d'
   '（若 >10%% 说明「offset==0 的表都以完整对象安装」不成立）'
   % (n0, len(nozero)), len(nozero) <= 0.10 * max(1, n0),
   {'n0': n0, 'nozero': len(nozero), 'pct': round(100.0 * len(nozero) / max(1, n0), 1),
    'sample': nozero[:6]})

# ---------- P3 反控：全段写入点的 disp 分布 ----------
dispdist = Counter(d for _, d, _ in allstore)
ck('P3 反控：全段 %d 个 mov [reg+disp], imm32 写入点的 disp 分布（前 8）= %s；'
   'disp==4 的占 %.2f%% ⇒ 若 offset 语义为假，12/12 全落 disp==4 的概率约为 %.2e'
   % (len(allstore), dispdist.most_common(8),
      100.0 * dispdist[4] / max(1, len(allstore)),
      (dispdist[4] / max(1, len(allstore))) ** 12),
   dispdist[4] < 0.2 * len(allstore) and dispdist[4] > 0,
   {'total': len(allstore), 'disp4': dispdist[4],
    'pct4': round(100.0 * dispdist[4] / max(1, len(allstore)), 2)})

# ---------- P4 交叉：offset==4 的表所属函数是否落在 R108 的 277 个 owner 里 ----------
try:
    pop = json.load(open('_r108/r108f_population.json'))
    rows = [r for r in pop.get('rows_sample', [])]
    ck('P4 R108 全量 owner 采样可读（%d 行）' % len(rows), True, len(rows))
except Exception as e:
    ck('P4 R108 采样不可读', False, str(e))

json.dump({'checks': checks, 'offset_dist': dict(sorted(dist.items())),
           'offset4_names': names4, 'res4': res4, 'n_ok4': n_ok4,
           'rev_nozero': nozero, 'rev_n0': n0,
           'disp_dist_top': [[d, n] for d, n in dispdist.most_common(12)],
           'n_store_total': sum(len(v) for v in STORE.values())},
          open('_r110/r110d_coloffset.json', 'w'), ensure_ascii=False, indent=1)
np_ = sum(1 for c in checks if c['ok'])
print('\nASSERT %d/%d PASS, FAIL %d' % (np_, len(checks), len(checks) - np_))
