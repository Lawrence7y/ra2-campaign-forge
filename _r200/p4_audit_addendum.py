#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R200 补落盘：审计 #503 回来后的订正追加（四件套各追加一段短块，CR 不变）。
审计 #503：deepseek，28 回合 / 15.13' / 预算 8' [OVERTIME]，逐条由 _r200/m12_audit503.py 复算（27 断言 0 FAIL）。
采纳 5 条（其中 3 条订正主会话措辞/口径），不采纳 0 条。
"""
import hashlib, io, os, sys, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
BL = os.path.join(TIER, 'R17_LEAD_BASELINE')
R14 = os.path.join(TIER, 'R14_COMMON.md')
GOAL = os.path.join(ROOT, 'lead/GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead/LEAD_LOCK')
SB = os.path.join(TIER, 'STATUS_BOARD.md')
fails = []; n = 0
def ck(nm, c, d=''):
    global n; n += 1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ') + nm + ((' | ' + str(d)) if d != '' else ''))

CORE = '''**十、审计 #503 回填（deepseek，28 回合 / 15.13 分 / 预算 8 分，[OVERTIME]）.** 其全部可复算项由 `_r200/m12_audit503.py` 独立复算 **27 断言 0 FAIL**。**采纳 5 条，其中 3 条订正本轮正文**：
① **措辞订正**：「全部 call rel32 = 68,244」应为「**全部 call rel32 指令 68,253 条，其中 target 落在 .text 内 68,244 条**（差 **9** 条，target 为 0xC0C5A07E / 0x46533E39 / 0xE2E0EC18 / 0xD45A5A67 / 0xE971FEAB / 0xE8D3E98A / 0xFA78B3A7 / 0xF07D1E7E / 0xD87E4995 九个非段内值，调用点 0x409FF2 / 0x52EB58 / 0x52EBC1 / 0x5A0074 / 0x6DFE39 / 0x70E915 / 0x783B68 / 0x7CA1D8 / 0x7DCBC8）」。
② **字节法假阳已定位**：字节法比反汇编法多出的那 1 条 **0x74836A 是假阳** —— 它落在 **`0x748368 adc edx, dword ptr [eax - 0x18]`（3 字节）的指令体内**，该指令跨过 0x74836A。⇒ **反汇编法的 4,498 是真值，字节法的 4,499 须减 1**。
③ **宿主判据的可靠性首次给数**：1,229 个「宿主」里前一字节为 **0x90 的 1,162** 个、**0xC3 的 16** 个（共 1,178 像函数边界），**0x00 的 49** 个与 **0xFF 的 2** 个（共 **51** 个不像起点）；宿主到调用点的距离 **p10 = 91 / p50 = 707 / p90 = 10,125 / max = 41,067 字节**。⇒「宿主 = 最近可被调用入口」这个判据在 **51/1,229 = 4.15%** 的宿主上不成立，且最远达 41 KB，**不能把宿主当函数**；本轮正文凡用「宿主」处一律按此边界理解。
④ **「538 是旧口径数」这个说法不成立**：严格正则与宽松正则**都是 538**（差 0），538 是**两个口径的同值**，不是旧口径的产物；同理「位移 1..9 的装表 store = 0」也是实测而非推断（位移分布 {0:532, 0x10:1, 0x14:1, 0x18:1, 0x34:1, 0x3F338:1, 0x3F550:1}）。
⑤ **「更近祖先 0 条」是同义反复**：`cat == 'other'` 的定义已经排掉 `imm == vt_d`（idx_imm 0）与 `imm == vt_b`（idx_imm 1），故 idx_imm ∈ {0,1} 处出现 0 条是**定义的算术后果**，不能当观测结论；有效的观测只有「更远祖先 21 / 不在血缘 21」这两块。
另有 4 条新事实由审计给出并经复算成立：**s0d 的 vt_b 去重只有 269**（vt_d 去重 516）⇒ 直基类主表被高度复用；**6 个无 call 实现逐一为 0x4F6830 / 0x5125A0 / 0x554400 / 0x643E80 / 0x7AC700 / 0x7AC870**；**两组对照的 z = 8.19（p<1e-15）与 z = 1.69（p≈0.091）**；**逐块口径 不过滤 55,424 / 过滤 55,419，与单次迭代差 12,829 / 12,825**。

'''

GADD = '''**十一、审计 #503 回填（[OVERTIME] 15.13' / 预算 8'，复算 27 断言 0 FAIL）.** 三处正文订正：① 「全部 call rel32 68,244」→「**68,253 条，其中 target ∈ .text 68,244**（差 9 条，非段内 target 九个已逐一列出）」；② 字节法多出的 0x74836A **是假阳**，落在 `0x748368 adc edx,[eax-0x18]`（3 字节）体内，**真值取反汇编 4,498**；③ 「538 是旧口径数」不成立，严格/宽松正则**同为 538**；④ 「更近祖先 0 条」是 `cat=='other'` 定义的算术后果，不算观测。新事实：**vt_b 去重 269**（vt_d 516）、6 个无 call 实现（0x4F6830 / 0x5125A0 / 0x554400 / 0x643E80 / 0x7AC700 / 0x7AC870）、z = 8.19 / 1.69、逐块 55,424 / 55,419。**宿主判据边界**：1,229 个宿主里 **51 个（4.15%）** 前一字节为 0x00 或 0xFF（不像函数起点），宿主到调用点距离 **p50 = 707 / max = 41,067 字节** ⇒ 宿主不可当函数用。

'''

LOCKADD = '''

**QC9. 🟡 审计 #503 回填（deepseek，28 回合 / 15.13′ / 预算 8′，`[OVERTIME]`）.** 全部可复算项由 `_r200/m12_audit503.py` 复算 **27 断言 0 FAIL**，**采纳 5 条（3 条订正正文）、不采纳 0 条**。订正：① **全部 call rel32 = 68,253 条，其中 target ∈ .text 68,244 条**（差 9 条，非段内 target 0xC0C5A07E/0x46533E39/0xE2E0EC18/0xD45A5A67/0xE971FEAB/0xE8D3E98A/0xFA78B3A7/0xF07D1E7E/0xD87E4995 已列）；② 字节法多出的 **0x74836A 是假阳**（落在 `0x748368 adc edx,[eax-0x18]` 3 字节指令体内）⇒ 0x7C8B3D 的真值取**反汇编 4,498**；③ **「538 是旧口径数」不成立** —— 严格与宽松正则**同为 538**（差 0），538 是两口径同值；④ **「更近祖先 0 条」是同义反复**（`cat=='other'` 已排掉 idx_imm 0/1），不能当观测。新事实：**vt_b 去重 269**（vt_d 去重 516，直基类主表高度复用）；**6 个无 call 实现** = 0x4F6830 HouseClass / 0x5125A0 HouseTypeClass / 0x554400 / 0x643E80 / 0x7AC700 / 0x7AC870；两组对照 **z = 8.19（p<1e-15）/ z = 1.69（p≈0.091）**；逐块口径 **不过滤 55,424 / 过滤 55,419**（与单次迭代差 12,829 / 12,825）。**宿主判据边界**：1,229 个「宿主」里前一字节 0x90 1,162 / 0xC3 16 / **0x00 49 / 0xFF 2** ⇒ **51 个（4.15%）不像函数起点**，宿主到调用点距离 p10 91 / p50 707 / p90 10,125 / **max 41,067 字节** ⇒ **宿主不可当函数**。

'''

SBADD = '''
**审计 #503 回填（deepseek，28 回合 / 15.13′ / 预算 8′，`[OVERTIME]`，复算 27 断言 0 FAIL）.** 采纳 5 条、不采纳 0 条，其中 **3 条订正本轮正文**：① 「全部 call rel32 = 68,244」应为「**68,253 条，其中 target ∈ .text 68,244**（差 9 条，九个非段内 target 已逐一列出）」；② 字节法多出的 **0x74836A 是假阳**（落在 `0x748368 adc edx,[eax-0x18]` 3 字节指令体内，该指令跨过它）⇒ 0x7C8B3D 真值取**反汇编 4,498**，字节法 4,499 须减 1；③ 「538 是旧口径数」**不成立** —— 严格与宽松正则**同为 538**（差 0），是两口径同值；④ 「更近祖先 0 条」是 `cat=='other'` 定义的**算术后果**，不算观测。新事实：**vt_b 去重只有 269**（vt_d 去重 516 ⇒ 直基类主表高度复用）；**6 个无 call 实现** = 0x4F6830 / 0x5125A0 / 0x554400 / 0x643E80 / 0x7AC700 / 0x7AC870；两组对照 **z = 8.19（p<1e-15）/ z = 1.69（p≈0.091）**；逐块口径 **不过滤 55,424 / 过滤 55,419**。**宿主判据边界**：1,229 个宿主里前一字节 0x90 1,162 / 0xC3 16 / **0x00 49 / 0xFF 2** ⇒ **51 个（4.15%）不像函数起点**，宿主到调用点距离 p10 91 / p50 707 / p90 10,125 / **max 41,067 字节** ⇒ **宿主不可当函数**。
'''
blocks = ((R14, CORE, 1081, 'R14_COMMON'), (GOAL, GADD, 337, 'GOAL'),
          (LOCK, LOCKADD, 137, 'LEAD_LOCK'), (SB, SBADD, 0, 'STATUS_BOARD'))
olds = {}
for path, blk, cr, tag in blocks:
    raw = io.open(path, 'rb').read(); olds[path] = raw
    ck('A1 %s 开局 CR == %d' % (tag, cr), raw.count(b'\r') == cr, raw.count(b'\r'))
    ck('A2 %s 块无 CR' % tag, b'\r' not in blk.encode(), True)
ck('A3 看板加后 <= 300 行', olds[SB].count(b'\n') + SBADD.count('\n') <= 300,
   olds[SB].count(b'\n') + SBADD.count('\n'))
if fails:
    print('★ fail-closed %d 条未过' % len(fails)); sys.exit(1)
stamp = time.strftime('%Y%m%d_%H%M%S')
for path, blk, cr, tag in blocks:
    old = olds[path]
    bak = os.path.join(BL, 'SUPERSEDED.before_r200_audit503_%s_%s.md' % (tag, stamp))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f: f.write(old)
    ck('W1 %s 备份 sha 一致' % tag,
       hashlib.sha256(open(bak, 'rb').read()).hexdigest() == hashlib.sha256(old).hexdigest())
    assert io.open(path, 'rb').read() == old
    new = old + blk.encode()
    io.open(path, 'wb').write(new)
    back = io.open(path, 'rb').read()
    ck('W2 %s 回读一致' % tag,
       hashlib.sha256(back).hexdigest() == hashlib.sha256(new).hexdigest() and back.count(b'\r') == cr
       and back.startswith(old), (back.count(b'\r'), len(back)))
print('\nSUMMARY asserts=%d fails=%d %s' % (n, len(fails), fails))
