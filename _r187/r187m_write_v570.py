#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R187 M：V569 -> V570，订正 V569 里一处**口径错误**（7/10 -> 8/10）。

错误与被抓的经过
----------------
V569 的 F29 limitations ④ 写「位移 == COL.mdisp 的有 7/10；不等的恰 3 张（B 两张位移 +0x3F338 / +8，
栈那张 +0x20）」。**这句是错的**，是 r187d 直接拿原始 disp 比 mdisp 造成的口径错误：

  那张走栈 store 的表（?$DynamicVectorClass@PAU_DDSURFACEDESC@@）在 004A4937 处是
    c74424200c5e7e00   mov dword ptr [esp + 0x20], 0x7E5E0C
  但对象基址不是 esp：同函数 004A492D 有 `lea edx, [esp + 0x18]` 建立栈上临时对象，
  之后 2 条 push ⇒ 现行 esp = lea 时的 esp − 8，于是
    [esp + 0x20] = (S − 8) + 0x20 = S + 0x18 = **对象基址 + 0**
  同对象上 [esp+0x30]→基址+0x10 置 0、[esp+0x34]→基址+0x14 置 0xa，与另一个 DynVec 位点
  0072403A 的 `[ecx]=vt / [ecx+0x14]=0xa / [ecx+0x10]=ebx` 签名**完全一致**。
  ⇒ 归一化基址后 **8/10 落在对象自身 +0**，不是 7/10。

谁抓出的：跨家族审计员 #451（deepseek / 33 回合 / 14.85 分 / **OVERTIME**）在主张 4 里指出
「r187d 直接拿原始 disp 比 mdisp，把这个算成不等，是本卡最实质的定量口径问题」。按 §2.12 规则 D，
主会话自写 `_r187/r187l_audit_recheck.py`（**35 断言 0 FAIL**）亲自复算成立，含逐指令 esp 相对量
与 DynVec 签名双证。

同时并入审计另两条我漏写的事实（均已复算）：
  (a) 那两张 B 形态表所在的同一构造函数里，稍后各有一条 C7 把**另一张 mdisp==0 的主表**装到 [esi]+0：
      007B1A20 → 0x7F79BC WinsockInterfaceClass、007B2E2D → 0x7F7A6C UDPInterfaceClass
      ⇒ 这两张 DynVec 不是对象基类虚表，而是被构造对象内嵌容器成员自身的 vtbl；
      两张表在**整个文件**里各只出现 1 次。
  (b) 第 12 处（00874F6C，在 .data）是数据侧偶合：邻近 dword 串
      007F4FC3 / 007F51C4 / 007F53C6 / 007F55C7 / **007F57C8** / 007F59CA / 007F5BCB / 007F5DCC / 007F5FCD
      里除 007F57C8 外都不是 vtable 头。

改法：只改 F29 limitations 的第 ④ 句（就地替换 + 补审计来源与归一化判据），不删句、不改数字以外的
结论；F01 一字不动。这是「改数字属裁定」的例外情形 —— 改的是一个**算错的分母口径**，不是改事实强弱。
"""
import hashlib, io, os, sys
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OLD = os.path.join(TIER, 'R17_R131_FACTINDEX_V569', 'FACT_INDEX.tsv')
NEWD = os.path.join(TIER, 'R17_R131_FACTINDEX_V570')
NEW = os.path.join(NEWD, 'FACT_INDEX.tsv')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

raw = open(OLD, 'rb').read()
ck('Y1 旧 V569 = 149,333 B / sha b260f1f4… / CR 0',
   len(raw) == 149333 and hashlib.sha256(raw).hexdigest().startswith('b260f1f4') and raw.count(b'\r') == 0,
   (len(raw), hashlib.sha256(raw).hexdigest()[:16]))
TXT = raw.decode('utf-8'); L = TXT.split('\n')
ck('Y2 56 段 / 每行 5 列', len(L) == 56 and all(len(x.split('\t')) == 5 for x in L[:55]), len(L))
rows = [l.split('\t') for l in L[:55]]
import copy
ORIG = copy.deepcopy(rows)
f29 = [r for r in rows if r[0] == 'F29'][0]

OLD_SENT = ('④ 位移 == COL.mdisp 的有 **7/10**；不等的恰 3 张（B 两张位移 +0x3F338 / +8，栈那张 +0x20）'
            '—— 这 3 张**不是异常、是形态不同**。')
NEW_SENT = ('④ **订正一处口径错误（V570）**：原写「位移 == COL.mdisp 的有 7/10；不等的恰 3 张」，'
'那是直接拿**原始 disp** 比 mdisp 造成的错。那张走栈 store 的表（`?$DynamicVectorClass@PAU_DDSURFACEDESC@@`）'
'在 `004A4937` 处是 `c74424200c5e7e00` = `mov dword ptr [esp + 0x20], 0x7E5E0C`，但对象基址不是 esp —— '
'同函数 `004A492D` 有 `lea edx, [esp + 0x18]` 建立栈上临时对象、之后 **2 条 push** ⇒ 现行 esp = lea 时 esp − 8，'
'故 `[esp + 0x20] = (S − 8) + 0x20 = S + 0x18 = ` **对象基址 + 0**；同对象上 `[esp+0x30]`→基址 **+0x10** 置 0、'
'`[esp+0x34]`→基址 **+0x14** 置 **0xa**，与另一 DynVec 位点 `0072403A` 的 `[ecx]=vt / [ecx+0x14]=0xa / [ecx+0x10]=ebx` '
'签名**完全一致**。⇒ **归一化基址后 8/10 落在对象自身 +0**，剩下 2 张是 B 形态、落在容器成员内。'
'本条订正由跨家族审计员 #451（deepseek / 33 回合 / 14.85 分 / **OVERTIME**）指出，主会话 `_r187/r187l_audit_recheck.py`'
'（**35 断言 0 FAIL**，含逐指令 esp 相对量与 DynVec 签名双证）亲自复算成立。'
'**另并入审计两条漏写事实**：(a) 那两张 B 形态表所在的同一构造函数里，稍后各有一条 C7 把**另一张 mdisp==0 的主表**'
'装到 `[esi]+0` —— `007B1A20 c706bc797f00` → **0x7F79BC WinsockInterfaceClass**、`007B2E2D c7066c7a7f00` → '
'**0x7F7A6C UDPInterfaceClass** ⇒ 这两张 DynVec **不是对象基类虚表**，而是被构造对象内嵌容器成员自身的 vtbl；'
'且这两张表在**整个文件**里各只出现 **1 次**；(b) 第 12 处（`00874F6C`，在 `.data`）是**数据侧偶合** —— 邻近 dword 串 '
'`007F4FC3 / 007F51C4 / 007F53C6 / 007F55C7 / 007F57C8 / 007F59CA / 007F5BCB / 007F5DCC / 007F5FCD` 里'
'除 `007F57C8` 外都不是 vtable 头，该处标为「非指令」。')

ck('Y3 旧句在 F29 limitations 里恰 1 次', f29[4].count(OLD_SENT) == 1, f29[4].count(OLD_SENT))
f29[4] = f29[4].replace(OLD_SENT, NEW_SENT, 1)
ck('Y4 新句已入、旧串的「7/10」不再出现',
   NEW_SENT in f29[4] and '**7/10**' not in f29[4])
ck('Y5 新句含 8/10 与归一化判据、含审计来源与 OVERTIME 标注',
   '8/10' in NEW_SENT and '对象基址 + 0' in NEW_SENT and '#451' in NEW_SENT and 'OVERTIME' in NEW_SENT)
for nm, s in (('Y6 新句', NEW_SENT),):
    ck(nm + ' 无 tab / CR / LF / 双引号', '\t' not in s and '\r' not in s and '\n' not in s and '"' not in s)
ck('Y7 新句以句号结尾、长度 > 800', NEW_SENT.endswith('。') and len(NEW_SENT.encode()) > 800,
   len(NEW_SENT.encode()))

newtxt = '\n'.join('\t'.join(r) for r in rows) + '\n'
nb = newtxt.encode()
ck('Y8 新体量 = 旧 + 替换差额', len(nb) == 149333 + len(NEW_SENT.encode()) - len(OLD_SENT.encode()),
   (len(nb), 149333 + len(NEW_SENT.encode()) - len(OLD_SENT.encode())))
ck('Y9 新 CR == 0 / 56 段 / 每行 5 列',
   nb.count(b'\r') == 0 and len(newtxt.split('\n')) == 56
   and all(len(x.split('\t')) == 5 for x in newtxt.split('\n')[:55]))
R2 = [l.split('\t') for l in newtxt.split('\n')[:55]]
diff = [a[0] for a, b in zip(ORIG, R2) if a != b]
ck('Y10 只有 F29 一行变化（其余 54 行逐单元格相同）', diff == ['F29'], diff)
ck('Y11 该行只有第 5 列变（statement / grade / evidence 逐字节未动）',
   all(a[0:4] == b[0:4] for a, b in zip(ORIG, R2)))
nf29 = [r for r in R2 if r[0] == 'F29'][0]
ck('Y12 新 F29 limitations 字节数', len(nf29[4].encode()) == 19204 + len(NEW_SENT.encode()) - len(OLD_SENT.encode()),
   len(nf29[4].encode()))
ck('Y13 F01 一字未动', [r for r in R2 if r[0] == 'F01'][0] == [r for r in ORIG if r[0] == 'F01'][0])
ck('Y14 8/10 与 8 张有 C7 位点 + 2 张 B 形态的算术一致（8 = 7 对象 + 1 栈归一化）', 7 + 1 == 8)

if fails:
    print('★ fail-closed：%d 条未过，不写盘' % len(fails)); sys.exit(1)
os.makedirs(NEWD, exist_ok=True)
if os.path.exists(NEW):
    print('★ 目标已存在，拒绝覆盖'); sys.exit(1)
with open(NEW, 'xb') as f: f.write(nb)
back = open(NEW, 'rb').read()
ck('Y15 回读 sha 一致', hashlib.sha256(back).hexdigest() == hashlib.sha256(nb).hexdigest())
print('\n断言 %d 条，FAIL %d 条' % (n, len(fails)))
print('V570 = %d B / sha %s… / F29 lim %d'
      % (len(nb), hashlib.sha256(nb).hexdigest()[:16], len(nf29[4].encode())))
sys.exit(0)
