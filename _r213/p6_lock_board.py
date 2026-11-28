# -*- coding: utf-8 -*-
"""R213 p6：GOAL 追加 §1271（CR 保持 337）+ LEAD_LOCK 追加 QV 段（CR 保持 137）+ STATUS_BOARD 第 213 轮（CR 保持 0）。"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/lead/R17_LEAD_BASELINE'
def wxback(path,tag):
    raw=open(path,'rb').read()
    bak=BASE+'/%s.before_r213_%s_20261128.bak'%(os.path.basename(path),tag)
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,raw); os.close(fd)
    assert open(bak,'rb').read()==raw
    return raw
# ---------- GOAL §1271 ----------
GF=ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md'
g=wxback(GF,'1271'); assert g.count(b'\r')==337, g.count(b'\r')
assert b'## \xc2\xa71271' not in g
G1271 = """
## §1271 · R213（2026-11-28）· RTTI 三角闭环重钉（1214/954/988 双射）+ 律 X 定稿（次视图 slot0 adjustor imm==mdisp，101/101，全槽 303/305）+ S3 函数体全解，0x11c7/0x11c8 真消息点 1/1；V596

**一、🔴 RTTI 三角闭环重钉（取代 F01 旧数）.** COL **1214** 条（sig 恒 0 / +8 恒 0 / +12 pTD 全 .data / +16 pCHD 全 .rdata，1214/1214 合式）；CHD **954** 个（每类恰 1 条 mdisp==0 主记录，另 260 条次记录 ⇒ 954+260=1214）；TD **988**（`.?AV` 962 + `.?AU` 26）；vftable **1214** 张。**双射**：1214 COL ↔ 1214 前驱位点 ↔ 1214 vftable，一一对应、起点两两不重复；TD+8 名 == COL 名 **1214/1214**。**口径订正**：vftable **不是** COL+4（COL+4 是 mdisp 字段）；反控按 COL+4 取连续 .text 指针在 1214 条上**全为 0**。F01 旧数「1201 被指回 / 总 1211 / 954 主」在现盘**不可复现**。

**二、🔴 律 X 定稿.** 260 张次视图按 slot0 二分：**101 张** slot0 是 this-adjustor thunk（`sub [esp+4],imm` ; `jmp rel32`），**imm 恒 == 该 COL 的 mdisp（101/101，无反例）**，mdisp→imm 观测集 `{4:[4],24:[24],36:[36],40:[40],44:[44],1728:[1728]}`；其余 **159 张** = 8(78)/12(78)/21784(3)，非 adjustor。**全槽** adjustor 合计 **305**：**303** 遵式，**2** 例外 = `?AVHouseClass@@` mdisp=**40** 的 **idx3/idx4**（imm=4，jmp `0x4f6e60`/`0x4f6950`，两目标均在本类主视图槽内）。每视图 adjustor 数 ∈ `{0:159,3:100,5:1}`；槽型模板 **7** 种且全以 AAA 打头。**反控三点**：①**954 张主视图内 adjustor 槽 = 0**；②jmp 目标 40 个全落 .text、无跳回自身；③**303/305** 目标落在本类主视图槽（多继承 forwarding），top3 `0x410260`(75)/`0x410300`(74)/`0x410310`(74)。律 X 的 305 与 R210 律 V 的 305 thunk **同源同数**，两者不互为证据。

**三、🔴 视图槽表.** 主视图 954 张 / **12726** 槽（slot≥3 计 **9958**）；次视图 260 张 / **1318** 槽；合计 **14044**。按 mdisp 长度分布（节选）`0:{7:412,5:158,3:82,9:60,1:40,24:26}` / `4:{6:78,50:12,5:1}` / `8:{1:78}` / `12:{1:78}` / `24:{8:6}` / `36:{15:1}` / `40:{9:1}` / `44:{5:1}` / `1728:{9:1}` / `21784:{1:3}`。

**四、🔴 TD+0 负控.** **988/988** 个 TD 的 +0 同为 **`0x7f9594`**（distinct=1）；首槽 `0x7c8ab7` = `push esi ; mov esi,ecx ; call 0x7c8a8e ; test byte [esp+8],1`（scalar deleting dtor）；`0x7f9598` = `Access violation - no RTTI data!`。`.text` 内 `0x7f9594` 仅 **2** 处、`0x7f9598` 仅 **3** 处 push；`.data`/`.rdata` 内 `0x7f9594` 恰 **988** 次**全部**是 TD+0 槽自身 ⇒ 共享 type_info 占位 vfptr，**禁用**作归属判据（以「TD+0==本记录 vftable」为判据命中 **0/1214**）。

**五、🔴 S3(21784) 函数体全解.** Mouse/Tab/Scroll 三表**共享同一视图**（各 1 槽，slot0 同 **`0x6d1770`**）。体：`mov eax,[esp+4]` ; `cmp eax,0x11c7` `jne` → 第二分支 ; 全局 **`0xb0cc1c`** 作序号 → `[0xb0cb78+eax*4]` → `jl 0` / `cmp eax,0x19` `jge`（**上界 25**）→ `lea ecx,[eax+eax*2]` ; `shl ecx,5`（**步长 96**）; `add ecx,0xb0c1c0` → `test ecx,ecx` `je` → `mov al,[ecx+0x2d]` → `test al,al` `jne` → `call 0x723ea0` ; `mov al,1 ; ret 8`。第二分支 `cmp eax,0x11c8` **同构反相**（`je` 跳过）并 `call 0x723eb0`；第三出口 `xor al,al ; ret 8`。`0x723ea0`/`0x723eb0` = `mov eax,[ecx]` + `mov byte [ecx+0x2d],1`(或 `,0`) + `jmp [eax+0x48]` ⇒ 对第 k 个结构**置/清 `[k+0x2d]` 标志**并转发虚槽 **+0x48**。三个全局全在 **virt-only（BSS）**，初值**属动态项**。

**六、🔴 0x11c7/0x11c8 字面陷阱.** `.text` 字面 **2 / 5** 处、`.rdata/.data` **0** 处（非 IID）；但**真消息点仅 1 / 1**：`0x11c7` 另 1 处是 `0x6379fa` 的 `push` 边界错位；`0x11c8` 的 5 处中 **2 处是 `__LINE__` 断言宏**（`0x5e0bc4`+`D:\\ra2mdpost\\netdlg2.cpp`、`0x784ed4`+`D:\\ra2mdpost\\wonline.cpp`）、另 2 处为结构体位移/传参（`0x4a87f0` `mov [esi+0x11c8],eax`、`0x637a8e` `push`）。`.rsrc` 另有 1 处 `0xb7a8bc`（载荷）。⇒ **立即数计数必须按指令边界与上下文分类**。

**七、🟡 onlysec 口径复算（推翻子代理）.** 954 个 CHD 的 pBCA **两两不同、无共享**（954/954），故「按 BCD 计」与「按 CHD 计」**完全相同**。34 条 onlysec 的引用数：`IUnknown 290` / `IPersist 90` / `IPersistStream 90` / `IClassFactory 78` / `IRTTITypeInfo 78` / `ILocomotion 12` / `IGameMap 9` / `StageClass 9` / `FlasherClass 6` / `IPiggyback 6` / `CComObjectRootEx 5` / `CComObjectRootBase 5` / 其余至 `IWOLBrowserEvent` 等。**「恰 1 次引用」= 20 条（不是 32 条）**，0 引用者 **0** 条。

**八、🟡 跨家族（§2.12 规则 D 全复算）.** #546/#547（hy4 `exec`）EX1 14 回合 / **3.22'**、EX2 19 回合 / **3.68'**，均无 OVERTIME；EX1 最大价值是**指出我方卡面 vftable=COL+4 口径错**；EX2 的 B6「恰 1 次 = 32 条」经主会话复算**推翻为 20**。#549（deepseek `audit` 只读）19 回合 / **2.20'**，**12/12 PASS**；其三条附注（位点全在 .rdata、`.rsrc` 有 1 处 0x11c8、按记录地址计会误得全 0）经 `d1_recheck.py` **13 断言 0 FAIL** 复算**成立**，但**其 G12 附注「32 条」不成立**（实测 **20**）。主会话 `xa.py` 单一复算源 **51 断言 0 FAIL**。

**九、📌 自错 5 组（0 条进结论）.** ①调度卡与 `x0.py` 把 vftable 写成 **COL+4**（EX1 指出，反控 0/1214）；②`xa.py` T2-6 断言「32 条」**直接采信子代理报数未复算**，实测 **20**；③T5-8 断言「模板 6 种」，实测 **7**；④T6 反汇编窗口 40 条截断第二分支，误报 2 FAIL，扩到 64 条后 PASS；⑤`d1_recheck.py` 首版把审计员 32 与「BCA 共享」当断言写死，复算后改为**反证其附注错**。

**十、🟡 落盘与门禁.** R14_COMMON **§2.221**（CR 保持 **1081**，+10256 B）；本段 **§1271** CR 保持 **337**；LEAD_LOCK **QV** CR 保持 **137**；STATUS_BOARD 第 213 轮 CR 保持 **0**（开局 **251 行 < 260**，**不归档**）。**FACT_INDEX V595→V596**（F01 + F29 各追加，其余 **56 行逐字节不变**），sha `9ffc56c9`→**`fd18fe6a`**、257435→**264072** B（+6637）；指针 + `facts_floors`（MASTER `835e4388`→**`ea10885c`**）+ `gate_runner.LEDGER` 重钉 V596；`check_disc.py` `C16_FLOORS` 纳入 **221**（213 pins，sha `e6d1058e`→**`f3b881dd`**）。

**十一、⚪ 未取得.** ①`0xb0cb78`/`0xb0cc1c`/`0xb0c1c0` 三全局的运行期初值与 0x19 元素结构全字段（**virt-only BSS，须 win-main 动态**）；②`[ecx+0x2d]` 标志位的语义归属；③虚槽 `+0x48` 的目标函数族（`0x723ea0`/`0x723eb0` 的转发落点）；④`?AVINoticeSink@@` 被以 8 / 21784 两偏移引用的**选择规则**；⑤HouseClass mdisp=40 的 idx3/idx4 两处 imm=4 例外的成因（为何不是 40）；⑥主视图 9958 个 slot≥3 槽语义归属；⑦F23/F35 grade（两 tsv 不可读，禁预估回填）；⑧C7 三死分支、C11 十二 ID。
"""
nb=(g.decode('utf-8')+G1271).encode('utf-8')
open(GF,'wb').write(nb); assert open(GF,'rb').read()==nb
print('GOAL: bytes %d->%d CR=%d (期望 337)'%(len(g),len(nb),open(GF,'rb').read().count(b'\r')))
assert open(GF,'rb').read().count(b'\r')==337
# ---------- LEAD_LOCK QV ----------
LF=ROOT+'/lead/LEAD_LOCK'
l=wxback(LF,'qv'); assert l.count(b'\r')==137, l.count(b'\r')
assert b'## QV ' not in l
QV = """## QV · R213（2026-11-28）· MSVC RTTI 三角闭环重钉（COL 1214 / CHD 954 / vftable 1214 / TD 988，三向双射无缺，vftable ≠ COL+4）；律 X 定稿（次视图 slot0 adjustor imm == mdisp，101/101；全槽 305 中 303 遵式、2 例 HouseClass mdisp=40）；S3(21784) 函数体全解；0x11c7/0x11c8 真消息点 1/1；V596

**QV1. 🔴 RTTI 三角闭环（重钉 F01 旧数）.** COL **1214**（+0 sig 恒 0、+8 恒 0、+12 pTD 全 .data、+16 pCHD 全 .rdata，**1214/1214** 合式）；CHD **954**（每类恰 1 条 mdisp==0 主记录 **954/954**，另 260 条次记录 ⇒ **954+260=1214**）；TD **988**（`.?AV` **962** + `.?AU` **26**，和 == 全集）；vftable **1214** 张。**双射**：1214 COL ↔ 1214 前驱位点 ↔ 1214 vftable，一一对应、无一对多、起点两两不重复；**TD+8 名 == COL 名 1214/1214**。

**QV2. 🟡 口径订正（自错，vftable ≠ COL+4）.** vftable 起点 = 「`.rdata` 中某 word == COL 地址、且下一 word ∈ `.text`」的**位点 + 4**。**反控**：按 COL+4 口径取连续 `.text` 指针在 **1214 条上全为 0**（0/1214）。本轮调度卡与 `_r213/x0.py` 首版均写成 COL+4，由 EX1 子代理（hy4，14 回合 / 3.22'）当场指出，主会话重写 `x1.py`/`xa.py` 后闭环。F01 正文旧数「**1201** 被指回 / 总 **1211** / 954 主」在现盘**不可复现**，本轮为 **1214/1214/954**。

**QV3. 🔴 律 X 定稿（本轮主成果）.** 260 张次视图按 slot0 **二分**：①**101 张** slot0 为 **this-adjustor thunk**（`sub dword ptr [esp+4], imm` ; `jmp rel32`），**imm 恒等于该 COL 的 mdisp**（**101/101**，无反例），mdisp→imm 观测集 `{4:[4],24:[24],36:[36],40:[40],44:[44],1728:[1728]}`；②其余 **159 张** = **8**(78)/**12**(78)/**21784**(3)，均非 adjustor。**全体 adjustor 槽**（非仅 slot0）**305** 个：**303** 遵式，**2** 例外 = `?AVHouseClass@@` **mdisp=40** 的 **idx=3/idx=4**（`imm=4`，jmp `0x4f6e60`/`0x4f6950`，两目标均在本类主视图槽内）。每视图 adjustor 数 ∈ `{0:159, 3:100, 5:1}`；槽型模板 **7** 种且**全以 AAA 打头**。

**QV4. 🟡 律 X 反控三点.** ①**954 张主视图内 adjustor 槽 = 0**（0 例外）；②adjustor 的 jmp 目标 **40** 个、**全部**落 `.text`、**无**跳回自身；③**303/305** 目标落在**本类主视图槽**（多继承 forwarding），top3 `0x410260`(**75** 类)/`0x410300`(**74**)/`0x410310`(**74**)。律 X 的 305 与 R210 律 V 的 **305 thunk 同源同数**，两者**不互为证据**。

**QV5. 🔴 视图槽表.** 主视图 954 张 / **12726** 槽（slot≥3 计 **9958**）；次视图 260 张 / **1318** 槽；合计 **14044**。长度分布（节选）：`0:{7:412,5:158,3:82,9:60,1:40,24:26}` / `4:{6:78,50:12,5:1}` / `8:{1:78}` / `12:{1:78}` / `24:{8:6}` / `36:{15:1}` / `40:{9:1}` / `44:{5:1}` / `1728:{9:1}` / `21784:{1:3}`。mdisp 非零分布 `{4:91,8:78,12:78,24:6,36:1,40:1,44:1,1728:1,21784:3}`。

**QV6. 🔴 TD+0 负控（禁用为归属判据）.** **988/988** 个 TD 的 +0 同为 **`0x7f9594`**（distinct=**1**）；首槽 `0x7c8ab7` = `push esi ; mov esi,ecx ; call 0x7c8a8e ; test byte [esp+8],1`（scalar deleting dtor）；`0x7f9598` = `Access violation - no RTTI data!`。引用面：`.text` 内 `0x7f9594` **2** 处（`0x7c8a93`/`0x7c8b2f` 的 `mov [..],0x7f9594`）、`0x7f9598` **3** 处 push（`0x7ca956`/`0x7caab0`/`0x7cabe0`）；`.data`/`.rdata` 内 `0x7f9594` 恰 **988** 次且**全部**为 TD+0 槽自身。**反控**：以「TD+0 == 本记录 vftable」为判据命中 **0/1214**。

**QV7. 🔴 S3(21784) 函数体全解.** Mouse/Tab/Scroll **共享同一视图**（各 1 槽，slot0 同 **`0x6d1770`**）。`mov eax,[esp+4]` ; `cmp eax,0x11c7` `jne` → 第二分支 ; 全局 **`0xb0cc1c`** 作序号 → `[0xb0cb78+eax*4]` → `jl 0` / `cmp eax,0x19` `jge`（**上界 25**）→ `lea ecx,[eax+eax*2]` ; `shl ecx,5`（**步长 96**）; `add ecx,0xb0c1c0` → `test ecx,ecx` `je` → `mov al,[ecx+0x2d]` → `test al,al` `jne` → `call 0x723ea0` ; `mov al,1 ; ret 8`。第二分支 `cmp eax,0x11c8` **同构反相**（`je` 跳过）+ `call 0x723eb0`；第三出口 `xor al,al ; ret 8`。`0x723ea0`/`0x723eb0` = `mov eax,[ecx]` + `mov byte [ecx+0x2d],1`(或 `,0`) + `jmp dword [eax+0x48]` ⇒ **对第 k 个结构置/清 `[k+0x2d]` 标志并转发虚槽 +0x48**。三个全局（`0xb0cb78`/`0xb0cc1c`/`0xb0c1c0`）**全在 virt-only（BSS）**，初值**属动态项，静态轮禁填**。

**QV8. 🔴 0x11c7/0x11c8 字面陷阱.** `.text` 字面 **2 / 5** 处，`.rdata/.data` **0** 处（⇒ **非** IID/GUID）；但**真消息点仅 1 / 1**。`0x11c7`：`0x6d1775` 真 `cmp`，另 1 处 `0x6379fb` 属 `0x6379fa` 的 `push`（**边界错位**）。`0x11c8`：`0x6d17b2` 真 `cmp`；**2 处 `__LINE__` 断言宏**（`0x5e0bc4` `push 0x11c8` + `push 0x831288` = `D:\\ra2mdpost\\netdlg2.cpp`；`0x784ed4` 同形 + `push 0x84a430` = `D:\\ra2mdpost\\wonline.cpp`）；另 2 处为结构体位移/传参（`0x4a87f0` `mov [esi+0x11c8],eax`；`0x637a8e` `push 0x11c8`）。`.rsrc` 另有 1 处 `0xb7a8bc`（资源载荷）。

**QV9. 🟡 onlysec 引用面复算（推翻子代理报数）.** 954 个 CHD 的 pBCA **两两不同、无共享**（**954/954**）⇒「按 BCD 计」与「按 CHD 计」**完全相同**。34 条 onlysec 引用数：`IUnknown 290`(189 CHD) / `IPersist 90` / `IPersistStream 90` / `IClassFactory 78` / `IRTTITypeInfo 78` / `ILocomotion 12` / `IGameMap 9` / `StageClass 9` / `FlasherClass 6` / `IPiggyback 6` / `CComObjectRootEx 5` / `CComObjectRootBase 5` / 其余含 `IWOLBrowserEvent`、`INetUtilEvent@WOL`(2)、`IChatEvent@WOL`(2) 等。**「恰 1 次引用」= 20 条（不是 32 条）**；0 引用者 **0** 条（34/34 全被引用）。

**QV10. 🟡 跨家族（§2.12 规则 D 全复算）.** #546/#547（hy4 `exec`）：EX1 14 回合 / **3.22'** vs 8.0、EX2 19 回合 / **3.68'** vs 8.0，**均无 OVERTIME**；EX1 最大价值是**指出我方卡面 vftable=COL+4 口径错**并给出两口径实测数；EX2 的 B6「恰 1 次 = 32 条」经主会话复算**推翻为 20**。#549（deepseek `audit` 只读）19 回合 / **2.20'** vs 8.0、无 OVERTIME、**12/12 PASS**：其三条附注（位点全在 `.rdata`、`.rsrc` 有 1 处 `0x11c8`、按**记录地址**计 BCA 会误得「34 条全 0 引用」）经 `_r213/d1_recheck.py` **13 断言 0 FAIL** 复算**全部成立**，但**其 G12 附注「32 条恰 1 次」不成立**（实测 **20**）。主会话 `_r213/xa.py` 单一复算源 **51 断言 0 FAIL**；`x8.py` 11 断言 0 FAIL。

**QV11. 📌 自错 5 组（0 条进结论）.** ①调度卡与 `x0.py` 把 vftable 起点写成 **COL+4**（EX1 指出，反控 0/1214）；②`xa.py` T2-6 断言「恰 1 次引用 = 32 条」**直接采信子代理报数未先复算**，实测 **20**；③`xa.py` T5-8 断言「槽型模板 6 种」，实测 **7**；④`xa.py` T6 反汇编窗口仅 40 条致第二分支截断，误报 T6-4/T6-8 两 FAIL，扩到 64 条后 PASS；⑤`d1_recheck.py` 首版把审计员的 32 与「BCA 共享」当断言写死（D2/D4），复算后改为**反证其两条附注错**。

**QV12. 🟡 落盘与门禁.** R14_COMMON **§2.221** CR 保持 **1081**（1884605→**1894861** B，+10256）；GOAL **§1271** CR 保持 **337**；本段 **QV** CR 保持 **137**；STATUS_BOARD 第 213 轮 CR 保持 **0**（开局 **251 行 < 260**，**不归档**）。**FACT_INDEX V595→V596**：F01 + F29 各追加，其余 **56 行逐字节不变**（57 行 / 5 列），sha `9ffc56c9`→**`fd18fe6a`**、257435→**264072** B（+6637）；指针 + `facts_floors`（EXPECT_CUR/CUR_SHA256/TOTAL_BYTES/MASTER `835e4388`→**`ea10885c`**）+ `gate_runner.LEDGER` 重钉 V596；`check_disc.py` `C16_FLOORS` 纳入 **221**（**213** pins，sha `e6d1058e`→**`f3b881dd`**）。

**QV13. ⚪ 未取得.** ①`0xb0cb78`/`0xb0cc1c`/`0xb0c1c0` 三全局运行期初值与 **0x19 元素结构**全字段（**virt-only BSS ⇒ 须 win-main 动态**）；②`[ecx+0x2d]` 标志位语义归属；③虚槽 **`+0x48`** 的目标函数族（`0x723ea0`/`0x723eb0` 的转发落点）；④`?AVINoticeSink@@` 被以 **8 / 21784** 两偏移引用的**选择规则**；⑤**HouseClass mdisp=40 的 idx3/idx4 两处 imm=4 例外成因**（为何不是 40）；⑥主视图 **9958** 个 slot≥3 槽语义归属；⑦F23/F35 grade（两 tsv 不可读，禁预估回填）；⑧C7 三死分支、C11 十二 ID。
"""
nb=(l.decode('utf-8')+QV).encode('utf-8')
open(LF,'wb').write(nb); assert open(LF,'rb').read()==nb
print('LEAD_LOCK: bytes %d->%d CR=%d (期望 137)'%(len(l),len(nb),open(LF,'rb').read().count(b'\r')))
assert open(LF,'rb').read().count(b'\r')==137
