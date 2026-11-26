import os, hashlib, json, re, io
P='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R14_COMMON.md'
BAK='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14_real/R17_LEAD_BASELINE/R14_COMMON.md.before_R140_2.144_20261126_2100.bak'
A=1
def chk(n,c,x=''):
    global A
    print('  %s %-70s %s'%('PASS' if c else 'FAIL',n,x)); assert c,n; A+=1
raw=open(P,'rb').read()
chk('bytes 1195865', len(raw)==1195865, str(len(raw)))
chk('CR 1081', raw.count(b'\r')==1081)
chk('LF 12093', raw.count(b'\n')==12093)
s=raw.decode('utf-8')
chk('section 2.143 exists', '## 2.143' in s)
chk('section 2.144 does NOT exist yet', '## 2.144' not in s)
chk('ends with single LF', s.endswith('\n') and not s.endswith('\n\n'))

SEC = """## 2.144 【R140】F01 的 RTTI 三表复算：1214/1214 是现值，1211 定位到阈值口径，1201 仍不可复现；另测得「两个 954 不是同一批 COL」

**背景.** `FACT_INDEX` 的 F01 一行写「总 COL 1211、1201 条 COL 被 vtable 指回、主 COL 954、TD 988、34 个 TD 无 vtable 指向」。R139 的 EOI 把「总 COL 1211 vs 实测 1214/1216」登记为未取得，试 8 种口径无一对上。本轮换做法：不再猜口径，先按**结构定义**把三张表重算一遍，再回过头解释两个旧数的来源。

**一 · 结构与现值（脚本 `_r140/r140n_f01_final.py`，10 断言；`ra2bench/gamemd.exe` 4,825,360 B、sha256 前缀 `73201cc0`）.**

判据链与 F01 相同，但每一环都写成可失败的形式：
1. **TD**：`.data/.rdata` 落盘字节里 `.?AV`/`.?AU` 开头、`@@` 结尾的可打印串，取串首 `S`，要求 `dword[S-8]` 落在 `.data/.rdata` 内且 `dword[S-4]==0`，TD VA `= S-8` ⇒ **988**（`.?AV` 962 + `.?AU` 26），与 F01 一致。
2. **COL 候选**：值为某 TD VA 的 4 字节对齐 dword，位置 −12 ⇒ 要求 `dword[COL+0]==0` 且 `dword[COL+12]==该 TD VA` ⇒ **1216**；其中 TD 指针引用 2221 处、被 `dword[+0]!=0` 否掉 1005 处、被 `+12` 不匹配否掉 **0** 处。
3. **结构剔除**：`dword[COL+16]==0` 的 2 个不是 COL。这三件事**逐元素同一集合**（实测 A∩B∩C = 2，且 A-only/B-only/C-only 全为 0）：`dword[COL+16]==0`、`dword[COL+4]==COL-0x18`（自指）、无任何虚表满足 `dword[vt-4]==COL`。两个是 `.?AVbad_cast@@`(0x80F060) 与 `.?AV_com_error@@`(0x80F0A0)，其 `+4` 是自指的编译期指针、`+16` 为空，本就不是完整对象定位器。⇒ **结构合法 COL = 1214**。
4. **主 COL**：每类恰有 **1** 个 `dword[COL+4]==0`（分布 `{1: 954}`，无 0 个也无 2 个）⇒ **954**，与 F01 一致。
5. **无 COL 指向的 TD = 34**，与 F01 一致。

⇒ 五个数里 **988 / 954（主 COL）/ 34 三个与 F01 完全一致**；**总 COL 实测 1214**（F01 写 1211）、**被 vtable 指回的 distinct COL 实测 1214**（F01 写 1201，指回 1218 次、重复全来自 `DropPodLocomotionClass` 一类的 5 处命中）。

**二 · 1211 是阈值产物，且阈值本身无意义.**

在 1214 上加 `dword[COL+4] <= 0x1000` 恰得 **1211**，去掉的是 3 个 `dword[COL+4]==0x5518`（`MouseClass` 0x7FA9B8 / `TabClass` 0x805E48 / `ScrollClass` 0x809008）。关键实测：`COL+4` 的全部取值只有 **10 种** `{0, 4, 8, 0xc, 0x18, 0x24, 0x28, 0x2c, 0x6c0, 0x5518}`，**0x6c0 与 0x5518 之间一个取值都没有** ⇒ 任何 `T ∈ [0x6c0, 0x5517]` 都给出 1211，任何 `T >= 0x5518` 都给出 1214。**1211 只等价于「把 0x5518 排除」这一件事，与 0x1000 这个数完全无关**（R89 已记 `0x1000` 出处不可考，本轮把「为何任意 T 都行」实测钉住）。这 3 个类的虚表都是有效虚表（vt 在 `.rdata`、前 64 槽 `.text` 计数 62/56/56、cmplr 链齐全），所以 (a) 砍掉的是真实的多重继承类，**没有结构含义**。

**三 · 一条被撤回的「第二条路径」（自错，如实记）.**

本轮一度认为 1211 还有一条不依赖数值阈值的复现：在 1216 候选上取「类名不以 `.?AU` 开头」且「只被恰好一张虚表指回」。跨家族审计员（deepseek，只读）指出该式对「虚表」的定义敏感，主会话复算 **证实指控成立** —— 换 6 种同样合理的虚表判据，「被指回次数 == 1」给出 **1203 / 1211 / 1212 / 1212 / 1212 / 1015** 四个互不相同的值（`_r140/r140y_c4b_invariance.py`）：

| 虚表判据 | (b) 的值 |
|---|---|
| 任意节的 dword 命中 | **1203** |
| 命中位于 `.data/.rdata` | **1211** |
| 命中位于 `.rdata` | 1212 |
| `dword[vt]` 落在 `.text` | 1212 |
| 落盘数据节 且 `dword[vt]` 落 `.text` | 1212 |
| slot0 与 slot1 都落 `.text` | 1015 |

只有「`.data/.rdata` 内命中」这一种给 1211，而它把 `.data` 里与 COL VA 同值的操作数也算作虚表 —— 反证：`DropPodLocomotionClass` 的 5 处命中里只有 1 处 `dword[vt]` 落 `.text`，另 4 处 slot0 是 `0xfebae900` 一类越界值。⇒ **(b) 不是可引用口径，已从 `FACT_INDEX` 撤回（v5.37 → v5.38），1211 只剩 (a) 一条复现路径，而 (a) 本身也无结构含义。**

**四 · 1201 仍不可复现，且已排除「事后阈值」这条解释方向.**

单谓词 30 余种、两谓词组合 400 余种（阈值类 / pCD 是否为空 / 是否 AU 侧 / 每类 COL 个数 / 虚表槽数 / 名字形态 / 是否最低 VA）全扫，**只有「虚表前 64 槽里落 `.text` 的个数 ≥ k」这一族能给出 1201**，且该族在 k=8、k=9 两处同为 1201，邻域 `k=0..14` → `1214,1214,1213,1212,1209,1208,1206,1206,1201,1201,1199,1194,1193,1193,1189`，**逐级落差最大 5、1201 处无拐点**；换成 objdump 起始集这一更严的尺子，同族给出 `1214,1214,1213,1212,1209,1208,1206,1206,1200,1200`，**1201 直接消失**。⇒ 1201 是「尺子 + 事后阈值」的产物。审计员独立复跑同族得同序列，并另报「任意可执行节」判据下 1201 落到 k=11 —— 这条**支持**而不是削弱结论：**1201 的出现位置随槽判据定义而移动，故它不属于任何结构口径**。

**五 · 新测得一条 F01 未写、且与 F29 直接相关的口径歧义.**

F01 括注把主 COL 定义为「每类一个 **lowest-VA** 主 COL」；F29 的 limitations 把主表规则定义为「`mdisp==0`」。两者**都得 954**，但**不是同一批 COL**：实测两个 954 元集合的对称差 **94 + 94 = 188**。机制是「多 COL 类的 COL 按 mdisp **严格递减**排列」——全部 94 个多 COL 类**没有一个**是递增或混合（94 严格递减 / 0 递增 / 0 全等 / 0 混合），故 `mdisp==0` 的 COL 恒为类内 **最高 VA**，而 F01 括注说的是 **最低 VA**。反控：改取 highest-VA 与 `mdisp==0` 集合**完全相同**（差 0）；改取 `mdisp==4`（91 个）与 lowest-VA 差 84 ⇒ 两条规则不是同义反复。审计员独立复算同得 954/954/188，并另验出一条更强的等式：`B − A` 恰是 94 个多 COL 类的最高 VA COL、`A − B` 恰是它们的最低 VA COL。⇒ **两处正文不能以「954 相等」互相引证**；数字巧合相等、所指对象不同。

**六 · 边界与未取得（不粉饰）.**

① **1201 的判据仍不可复现**，R89 与本轮两次独立扫描一致；② **`0x1000` 的出处仍不可考**；③ F01 的 `evidence_paths` 指向「看板第 7–9 轮段（审计 R13）」，属另一条证据链，**本轮不改 F01 的 statement 与 grade 一个字**，只在其 `limitations` 追加实测与口径说明（v5.36 → v5.37 → v5.38）；④ 本镜像 `.data` 虚拟尾部约 3.4 MB 不落盘，本轮链的前提是「全部 TD/COL/虚表恰在落盘区」——实测落盘外 COL 0 个、虚表 0 个，前提在本镜像成立，换一份 `.data` 压缩不同的镜像会**静默漏算**；⑤ F29 的 63/77 等四数**不依赖** COL 总数，故本条不影响 F29 结论。

**七 · 自错（全由断言抓出，未进结论）.** **S-270** `r140b` 首版把节表 `VirtualAddress` 当绝对 VA 又减了一次 `ImageBase`，`dw()` 全返回 `None`，整表归零（与 R139 的 S-267 同类，写脚本时复发了）；**S-271** `r140o` 断言写「递减类 >= 100」，实测恰 94，改成「全递减且无一递增/混合」这一更强形式；**S-272** `r140r` 把 k=0 的预期值写成 1216，实际基集是 1214；**S-273** `r140s` 断言要求「写入串不含反引号」，但该禁令只约束 `_cards/`，`FACT_INDEX` 本身已有 7 行含反引号、全文 444 个；**S-274** `r140w` 断言要求「DropPod 只有 1 处 `.data/.rdata` 命中」，实测 5 处全在其中（真分歧在 `.data` 算不算虚表区）；**S-275** `r140z` 断言要求「撤回段比原句短」，实测 2473 → 2848 B，撤回说明本就可以更长。
"""
chk('new section has no CR', '\r' not in SEC)
chk('new section is LF-only', SEC.count('\n')>=1)
newraw=raw+SEC.encode('utf-8')
chk('CR count unchanged at 1081', newraw.count(b'\r')==1081, str(newraw.count(b'\r')))
chk('LF grew by the number of lines added', newraw.count(b'\n')==12093+SEC.count('\n'),
    '%d -> %d (+%d)'%(12093,newraw.count(b'\n'),SEC.count('\n')))
chk('old content is a byte-prefix of new content', newraw[:len(raw)]==raw)
chk('exactly one new section heading added', newraw.count(b'## 2.144')==1 and raw.count(b'## 2.144')==0)
secs0=len(re.findall(rb'(?m)^##\s*(\d+(?:\.\d+)*)', raw))
secs1=len(re.findall(rb'(?m)^##\s*(\d+(?:\.\d+)*)', newraw))
chk('section count 154 -> 155', secs1==secs0+1, '%d -> %d'%(secs0,secs1))
fd=os.open(BAK, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o644); os.write(fd,raw); os.close(fd)
chk('backup wx created', os.path.getsize(BAK)==1195865)
open(P,'wb').write(newraw)
back=open(P,'rb').read()
chk('readback identical', back==newraw)
chk('readback CR 1081', back.count(b'\r')==1081)
print()
print('R14_COMMON: %d -> %d B (+%d)  CR 1081  LF %d  sections %d' % (1195865,len(back),len(back)-1195865,back.count(b'\n'),secs1))
print('ASSERTIONS: %d PASS' % (A-1))
