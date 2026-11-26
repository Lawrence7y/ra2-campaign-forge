import os, hashlib
P='/home/t628/projects/ra2-campaign-forge/lead/LEAD_LOCK'
BAK='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14_real/R17_LEAD_BASELINE/LEAD_LOCK.before_R140_NX4_20261126_2104.bak'
A=1
def chk(n,c,x=''):
    global A
    print('  %s %-70s %s'%('PASS' if c else 'FAIL',n,x)); assert c,n; A+=1
raw=open(P,'rb').read()
print('  bytes %d  CR %d  LF %d' % (len(raw), raw.count(b'\r'), raw.count(b'\n')))
chk('CR count is 137', raw.count(b'\r')==137, str(raw.count(b'\r')))
chk('bytes 924021', len(raw)==924021, str(len(raw)))
s=raw.decode('utf-8')
chk('last lock code NW3 present', 'NW3.' in s)
chk('NX3 does not exist yet', 'NX3.' not in s)

SEC = """NX4. 🔴 **开局先按结构重算 F01 的三张表，而不是继续猜口径.** R139 的 EOI 把「F01 总 COL 1211 / 被指回 1201 与实测 1214 不符」记成未取得、试过 8 种口径。本轮改为「先按结构定义重算，再解释旧数来源」：TD **988**（`.?AV` 962 + `.?AU` 26）、COL 候选 **1216**（TD 指针引用 2221、被 `dword[+0]!=0` 否掉 1005、被 `dword[+12]` 不匹配否掉 **0**）、结构合法 COL **1214**、主 COL **954**（每类恰 1 个 `dword[COL+4]==0`，分布 `{1:954}`）、无 COL 指向的 TD **34**。⇒ **988/954/34 三个与 F01 完全一致，总 COL 与被指回实测都是 1214。**

NY4. ✅ **结构剔除的 2 个是「三重同一性」，不是三个独立判据.** `dword[COL+16]==0`、`dword[COL+4]==COL-0x18`（自指）、无虚表 `dword[vt-4]==COL` 三谓词**逐元素相同**（A∩B∩C=2；A-only/B-only/C-only 全 0），是 `.?AVbad_cast@@`(0x80F060) 与 `.?AV_com_error@@`(0x80F0A0) —— 其 `+4` 是自指编译期指针、`+16` 为空，本就不是完整对象定位器。

NZ4. ✅ **1211 是阈值产物，且阈值本身无意义（R89 结论的本轮加强版）.** `dword[COL+4] <= 0x1000` 恰得 **1211**，去掉 3 个 `==0x5518`（MouseClass 0x7FA9B8 / TabClass 0x805E48 / ScrollClass 0x809008）。关键实测：`COL+4` 全部取值只有 **10 种**，**0x6c0 与 0x5518 之间一个取值都没有** ⇒ 任何 `T ∈ [0x6c0, 0x5517]` 都给 1211、`T >= 0x5518` 都给 1214。**1211 只等价于「把那 3 个 0x5518 排除」，与 0x1000 这个数完全无关。** 且这 3 个类的虚表都有效（vt 在 `.rdata`、前 64 槽 `.text` 计数 62/56/56、cmplr 链齐全）⇒ (a) 砍掉的是真实多重继承类，**无结构含义**。

NA4. 🔴 **一条被撤回的路径（本轮自错，跨家族审计员抓到，复算成立）.** 我曾提出「不依赖数值阈值的第二条复现」：在 1216 候选上取「类名不以 `.?AU` 开头」且「只被恰好一张虚表指回」= 1211。审计员 #306 指出该式对「虚表」定义敏感。主会话复算**指控成立**：换 6 种同样合理的虚表判据，「被指回次数 == 1」给出 **1203 / 1211 / 1212 / 1212 / 1212 / 1015** 四个互不相同的值（`_r140/r140y_c4b_invariance.py`）——全节命中 1203、仅 `.rdata` 1212、`dword[vt]` 落 `.text` 1212、再加落盘数据节 1212、slot0+slot1 都落 `.text` 1015，**只有「`.data/.rdata` 内命中」给 1211**，而它把 `.data` 里与 COL VA 同值的**操作数**也当虚表。反证：`DropPodLocomotionClass` 的 5 处 `.data/.rdata` 命中里只有 **1** 处 `dword[vt]` 落 `.text`，另 4 处 slot0 是 `0xfebae900` 一类越界值。⇒ **(b) 已撤回，1211 只剩 (a) 一条路径且 (a) 无结构含义**。FACT_INDEX v5.37 → **v5.38**（79,224 → 79,845 B，只改 F01 的 limitations 一句）。

NB4. ✅ **1201 仍不可复现，且已排除「事后阈值」这条解释方向.** 单谓词 30 余种 + 两谓词组合 400 余种（阈值类 / pCD 是否为空 / 是否 AU 侧 / 每类 COL 个数 / 虚表槽数 / 名字形态 / 是否最低 VA）全扫，**只有「虚表前 64 槽落 `.text` 的个数 ≥ k」这一族能给出 1201**，且在 k=8、k=9 双点出现，邻域 `k=0..14` = `1214,1214,1213,1212,1209,1208,1206,1206,1201,1201,1199,1194,1193,1193,1189`，**逐级落差最大 5、1201 处无拐点**；换 objdump 起始集这一更严的尺子，同族给出 `…,1206,1206,1200,1200`，**1201 直接消失**。审计员独立复跑同族得同序列，并另报「任意可执行节」判据下 1201 落 k=11 —— 这**支持**而不是削弱结论：**1201 的位置随尺子移动，不属任何结构口径**。

NC4. ✅ **新测得一条 F01 未写、且与 F29 直接相关的口径歧义.** F01 括注把主 COL 定义为「每类一个 **lowest-VA** 主 COL」；F29 的 limitations 把主表规则定义为「**mdisp==0**」。两者**都得 954**，但**不是同一批 COL** —— 实测两个 954 元集合的对称差 **94 + 94 = 188**。机制：94 个多 COL 类的 COL 按 mdisp **严格递减**排列（94 严格递减 / 0 递增 / 0 全等 / 0 混合），故 `mdisp==0` 恒为类内 **最高 VA**，而 F01 说的是 **最低 VA**。反控：改取 highest-VA 与 `mdisp==0` 集合**完全相同**（差 0）；改取 `mdisp==4`（91 个）与 lowest-VA 差 84 ⇒ 两规则非同义反复。审计员独立同得 954/954/188，并另验出 `B−A` 恰是 94 个多 COL 类的最高 VA COL、`A−B` 恰是它们的最低 VA COL。⇒ **两处正文不能以「954 相等」互相引证**：数字巧合相等、所指对象不同。

ND4. ✅ **规则 D：执行员 #305（hy4）盲测独立复算，八项与主会话逐项一致.** 卡面明确禁止读 `_r140/r140*.py`，它自写 `_r140/sub/r140_f01_blind.py` 得 TD 988 / `.?AV` 962 / `.?AU` 26 / TD 引用 2221 / COL 1216 / 否掉 1005 / `+12` 不匹配 0 / 虚表 1218 / distinct 1214 / 未指回 2（bad_cast、_com_error）/ mdisp==0 954 / 无 COL 指向 TD 34 / `mdisp<=0x1000` 1211 —— **逐项与主会话相同**。

NE4. 🔴 **审计员 #306（deepseek）status 见看板；它的一条指控成立、两条披露我复核后接受.** 成立项即 NA4 的 (b) 不变量问题（这是本轮唯一被审计员推翻的主张，已撤回并改写正文）。它另报两条我复算接受：① `dword[COL+8]`（cdOffset）对全部 **1216** 恒为 0 ⇒ 该字段在判据里零判别力，1216→1214 的收敛**只**由 `COL+16` 完成（我的正文未声明这点，已在 2.144 补正）；② 在 base=1216（含 2 个坏 COL）上重算，那 2 个坏 COL 会成为各自类的最高 VA，令「mdisp==0 是类内最高 VA」出现 **2** 个反例 ⇒ 这反证 **1214 才是正确基集**。它判 UNSURE 的部分：我给它的卡面里「k=6..10 依次 1206/1206/1200/1200/1198」那组数它没能复现（它用「任意可执行节」得 1208/1208/1204/1204/1203）—— **该组数是我卡面写错的一种槽定义残留，正文已不再引用该组，只用 `.text` 判据的 1206/1201/1201/1199 与 objdump 判据两组**，如实记。

NF4. 📌 **未取得（不粉饰）.** ① **1201 的判据仍不可复现**（R89 与本轮两次独立扫描一致）；② **`0x1000` 的出处仍不可考**；③ F01 的 `evidence_paths` 指向「看板第 7–9 轮段（审计 R13）」，属另一条证据链，**本轮不改 F01 的 statement 与 grade 一个字**，只在其 `limitations` 追加；④ `.data` 虚拟尾部约 3.4 MB 不落盘，本链前提是「全部 TD/COL/虚表恰在落盘区」（实测落盘外 COL 0、虚表 0），换一份压缩不同的镜像会**静默漏算**；⑤ F29 的 63/77 四数**不依赖** COL 总数，本条不影响 F29。

NG4. 📌 **自错 6 条（全由断言抓出，未进结论）.** **S-270** `r140b` 复发 R139 的 S-267：把节表 `VirtualAddress` 当绝对 VA 又减了一次 `ImageBase`，`dw()` 全返回 `None`、整表归零；**S-271** `r140o` 断言写「递减类 >= 100」，实测恰 **94**，改成「全递减且无一递增/混合」这一更强形式；**S-272** `r140r` 把 k=0 的预期值写成 1216，实际基集是 1214；**S-273** `r140s` 断言要求「写入串不含反引号」，但该禁令只约束 `_cards/`，`FACT_INDEX` 本身已有 7 行含反引号、全文 444 个；**S-274** `r140w` 断言要求「DropPod 只有 1 处 `.data/.rdata` 命中」，实测 5 处全在其中（真分歧在 `.data` 算不算虚表区）；**S-275** `r140z` 断言要求「撤回段比原句短」，实测 2473 → 2848 B，撤回说明本就可以更长。

NH4. ✅ **落盘.** FACT_INDEX **v5.36 → v5.37 → v5.38**：75,107 → 79,224 → **79,845 B**，三次都只改 **F01 一行**、其余 54 行逐字节相同，`grade` 列一字未动，全 LF 55 行；每次写入前 wx 独占建 `.bak`、写后回读校验、源版本 sha 未被修改。v5.37 的断言 **30 项**、v5.38 的断言 **23 项**全部 PASS。
"""
chk('new block has no CR', '\r' not in SEC)
newraw=raw+SEC.encode('utf-8')
chk('CR unchanged 137', newraw.count(b'\r')==137, str(newraw.count(b'\r')))
chk('old content is a byte prefix', newraw[:len(raw)]==raw)
chk('exactly one NX4 block', newraw.count(b'NX4.')==1 and raw.count(b'NX4.')==0)
fd=os.open(BAK, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o644); os.write(fd,raw); os.close(fd)
chk('backup wx created', os.path.getsize(BAK)==len(raw))
open(P,'wb').write(newraw)
back=open(P,'rb').read()
chk('readback identical', back==newraw)
chk('readback CR 137', back.count(b'\r')==137)
print()
print('LEAD_LOCK: %d -> %d B (+%d)  CR 137  LF %d' % (len(raw), len(back), len(back)-len(raw), back.count(b'\n')))
print('ASSERTIONS: %d PASS' % (A-1))
