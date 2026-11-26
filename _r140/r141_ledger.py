import os, hashlib, re
P='/home/t628/projects/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md'
BAK='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14_real/R17_LEAD_BASELINE/GOAL_THREE_TARGETS.md.before_R140_1194_20261126_2102.bak'
A=1
def chk(n,c,x=''):
    global A
    print('  %s %-70s %s'%('PASS' if c else 'FAIL',n,x)); assert c,n; A+=1
raw=open(P,'rb').read()
print('  bytes %d  CR %d' % (len(raw), raw.count(b'\r')))
chk('CR count is 337', raw.count(b'\r')==337, str(raw.count(b'\r')))
s=raw.decode('utf-8')
chk('has section 1193', '## §1193' in s)
chk('no section 1194 yet', '## §1194' not in s)
chk('max section is 1193', s.count('## §1193')==1)

SEC = """## §1194 R140 · F01 的 RTTI 三表：结构现值 1214/1214，1211 定位到阈值口径，1201 仍不可复现；「两个 954」不是同一批 COL

**目标**：R139 收口把「F01 总 COL 1211 / 被指回 1201 与实测 1214 不符」登记为未取得，并试过 8 种口径。本轮不再猜口径，改成「先按结构定义重算，再解释旧数来源」。

**一 · 结构重算（`_r140/r140n_f01_final.py` 10 断言 + `r140o`/`r140p`/`r140q`/`r140r` 共 14 断言）。** TD **988**（`.?AV` 962 + `.?AU` 26）、COL 候选 **1216**（TD 指针引用 2221、被 `+0!=0` 否掉 1005、被 `+12` 不匹配否掉 0）、结构合法 COL **1214**、主 COL（`dword[COL+4]==0`，每类恰 1 个，分布 `{1: 954}`）**954**、无 COL 指向的 TD **34**。⇒ **988 / 954 / 34 与 F01 完全一致；总 COL 与「被指回」实测都是 1214**。

**二 · 结构剔除的 2 个是同一集合的三重同一性。** `dword[COL+16]==0`、`dword[COL+4]==COL-0x18`（自指）、无虚表 `dword[vt-4]==COL` 三谓词**逐元素相同**（A∩B∩C=2，A-only/B-only/C-only 全 0），是 `.?AVbad_cast@@`(0x80F060) 与 `.?AV_com_error@@`(0x80F0A0)。

**三 · 1211 = 阈值产物，阈值本身无意义。** `dword[COL+4] <= 0x1000` 恰得 1211，去掉 3 个 `==0x5518`（MouseClass / TabClass / ScrollClass，三者的虚表都有效）。实测 `COL+4` 只有 10 种取值，**0x6c0 与 0x5518 之间无任何取值** ⇒ 任何 `T ∈ [0x6c0, 0x5517]` 都给 1211，`T >= 0x5518` 给 1214。**1211 只等价于「排除那 3 个 0x5518」，与 0x1000 无关。**

**四 · 一条被撤回的路径（本轮自错，审计员抓到）。** 曾提出「不依赖数值阈值的第二条复现」：not-AU 且只被恰好一张虚表指回 = 1211。审计员指其对虚表定义敏感，主会话复算**成立**：换 6 种判据给出 **1203 / 1211 / 1212 / 1212 / 1212 / 1015**，只有「`.data/.rdata` 内命中」给 1211，而它把 `.data` 里同值操作数当虚表（`DropPodLocomotionClass` 5 处命中只有 1 处 slot0 落 `.text`，另 4 处 slot0 是 `0xfebae900` 类越界值）。⇒ 已撤回，FACT_INDEX v5.37 → v5.38。

**五 · 1201 仍不可复现，且已排除「事后阈值」方向。** 单谓词 30 余 + 两谓词组合 400 余全扫，只有「虚表前 64 槽落 `.text` 个数 ≥ k」这一族给 1201（k=8、9 双点），邻域 `k=0..14` = `1214,1214,1213,1212,1209,1208,1206,1206,1201,1201,1199,1194,1193,1193,1189`，**无拐点**；换 objdump 起始集则 1201 消失（变 1200/1200）。审计员另报「任意可执行节」判据下 1201 落 k=11 —— 这**支持**结论：1201 的位置随尺子移动，不属任何结构口径。

**六 · 新事实：F01 的 954 与 F29 的 954 不是同一批 COL。** F01 括注 = 「每类 lowest-VA 主 COL」；F29 = 「`mdisp==0`」。两者基数都是 954，但对称差 **94+94=188**。机制：94 个多 COL 类的 COL 按 mdisp **严格递减**排列（94 递减 / 0 递增 / 0 全等 / 0 混合）⇒ `mdisp==0` 恒为类内**最高** VA，F01 说的是**最低**。反控：highest-VA 与 `mdisp==0` 集合完全相同（差 0）；`mdisp==4`（91 个）与 lowest-VA 差 84。审计员独立同得，并另验 `B−A` 恰为 94 个多 COL 类的最高 VA COL、`A−B` 恰为最低 VA COL。

**七 · 边界（不粉饰）。** ① 1201 判据仍不可复现（R89 与本轮两次独立扫描一致）；② `0x1000` 出处仍不可考；③ **不改 F01 的 statement 与 grade**，只在其 `limitations` 追加（v5.36 → 5.37 → 5.38）；④ `.data` 虚拟尾部约 3.4 MB 不落盘，本链前提在本镜像成立（落盘外 COL 0、虚表 0），换镜像会静默漏算；⑤ F29 的 63/77 四数不依赖 COL 总数，本条不影响 F29。

**八 · 自错 6 条，全由断言抓出。** S-270 `r140b` 复发 R139 的 S-267（节表 VA 当绝对 VA 又减 ImageBase，整表归零）；S-271 `r140o` 断言猜「递减类 >= 100」实测恰 94；S-272 `r140r` k=0 预期写 1216 实际基集 1214；S-273 `r140s` 把 `_cards/` 的反引号禁令套用到 FACT_INDEX（该文件已有 7 行含反引号）；S-274 `r140w` 误设「DropPod 只 1 处 `.data/.rdata` 命中」实测 5 处；S-275 `r140z` 断言要求撤回段比原句短，实测 2473→2848 B。
"""
chk('new section has no CR', '\r' not in SEC)
newraw=raw+SEC.encode('utf-8')
chk('CR unchanged 337', newraw.count(b'\r')==337, str(newraw.count(b'\r')))
chk('old content is a byte prefix', newraw[:len(raw)]==raw)
chk('exactly one new heading', newraw.count(b'## \xc2\xa71194')==1 and raw.count(b'## \xc2\xa71194')==0)
fd=os.open(BAK, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o644); os.write(fd,raw); os.close(fd)
chk('backup wx created', os.path.getsize(BAK)==len(raw))
open(P,'wb').write(newraw)
back=open(P,'rb').read()
chk('readback identical', back==newraw)
chk('readback CR 337', back.count(b'\r')==337)
print()
print('LEDGER: %d -> %d B (+%d)  CR 337' % (len(raw), len(back), len(back)-len(raw)))
print('ASSERTIONS: %d PASS' % (A-1))
