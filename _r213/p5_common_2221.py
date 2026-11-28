# -*- coding: utf-8 -*-
"""R213 p5：R14_COMMON.md 追加 ## 2.221（全 LF，CR 保持 1081）。"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
F=ROOT+'/lead/next_re_20261117_r14/R14_COMMON.md'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
raw=open(F,'rb').read()
CR=raw.count(b'\r')
print('before: bytes=%d CR=%d sha=%s'%(len(raw),CR,hashlib.sha256(raw).hexdigest()[:16]))
assert CR==1081,CR
bak=BASE+'/R14_COMMON.md.before_r213_2221_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,raw); os.close(fd)
assert open(bak,'rb').read()==raw
SEC = """## 2.221 · R213（2026-11-28）· MSVC RTTI 三角闭环重钉（COL 1214 / CHD 954 / vftable 1214 / TD 988，双射无缺）；律 X 定稿（次视图 slot0 的 this-adjustor 立即数 == mdisp，101/101；全槽 305 中 303 遵式、2 例为 HouseClass mdisp=40 的 idx3/idx4）；S3(21784) 函数体全解 + 0x11c7/0x11c8 真消息点 1/1；V596

### 一 · RTTI 三角闭环（重钉 F01 旧数）

以字节直接重建 MSVC RTTI 三结构，不引用任何历史轮次数字：

- **COL（Complete Object Locator）1214 条**：+0 signature 恒 **0**（单一取值）、+4 int32 mdisp、+8 恒 **0**、+12 pTD 全落 **.data**、+16 pCHD 全落 **.rdata**；四条合式率 **1214/1214**。
- **CHD（Class Hierarchy Descriptor）954 个**：每类恰 **1** 条 mdisp==0 主记录（954/954），另有 **260** 条次记录 ⇒ 954+260 = **1214** = COL 数。
- **TypeDescriptor 988 个**：`.?AV` **962** + `.?AU` **26**（和 == 全集，无第三类前缀）。
- **vftable 1214 张**：定位口径 = 「.rdata 中某 word 等于某 COL 地址、且下一 word 落在 .text」的位点 **+4**。

**双射闭环**：1214 条 COL ↔ 1214 个前驱位点 ↔ 1214 张 vftable，一一对应、无一对多、起点两两不重复；TD+8 内联名 == COL 名 **1214/1214**。

**口径订正（本条为 R213 自错）**：vftable **不是** COL+4。COL 是 .rdata 里 20 字节记录，其 +4 是 mdisp 字段。反控：按 COL+4 口径取「连续 .text 指针」在 **1214 条上全部为 0**（0/1214）。本轮调度卡与 `x0.py` 首版均写成 COL+4，由 EX1 子代理当场指出，主会话重写为 `x1.py` / `xa.py` 后闭环。

**取代关系**：F01 正文旧数「1201 条 COL 全被指回 / 总 COL 1211 / 954 主 COL」在现盘**不可复现**；本轮实测为 **1214 / 1214 / 954**，pTD 命中率 **1214/1214**（非 1201）。V596 已把此订正写入 F01 limitations 列。

### 二 · 视图槽表（定长口径）

| 口径 | 张数 | 槽数 |
|---|---|---|
| 主视图（mdisp==0） | 954 | **12726**（其中 slot≥3 计 **9958**） |
| 次视图（mdisp≠0） | 260 | **1318** |
| 合计 | 1214 | **14044** |

按 mdisp 的长度分布：`0:{7:412, 5:158, 3:82, 9:60, 1:40, 24:26, …}` / `4:{6:78, 50:12, 5:1}` / `8:{1:78}` / `12:{1:78}` / `24:{8:6}` / `36:{15:1}` / `40:{9:1}` / `44:{5:1}` / `1728:{9:1}` / `21784:{1:3}`。

mdisp 非零分布：`{4:91, 8:78, 12:78, 24:6, 36:1, 40:1, 44:1, 1728:1, 21784:3}`（合计 260）。

### 三 · 律 X 定稿（本轮主成果）

**律 X**：260 张次视图按 slot0 形态二分 ——

1. **101 张**的 slot0 是 **this-adjustor thunk**，形态 `sub dword ptr [esp+4], imm` ; `jmp rel32`，且 **imm 恒等于该 COL 记录的 mdisp**（**101/101**，无反例）。mdisp→imm 观测集：`{4:[4], 24:[24], 36:[36], 40:[40], 44:[44], 1728:[1728]}`。
2. 其余 **159 张** = mdisp **8**(78) / **12**(78) / **21784**(3)，均非 adjustor（8 = `xor al,al ; ret 8` 桩或 3 个真函数体；12 = `ret 4`；21784 = `0x6d1770`）。

**全体 adjustor 槽**（不只 slot0）合计 **305** 个：**303** 个 imm==mdisp，**2** 个例外 —— `?AVHouseClass@@` mdisp=**40** 的 **idx=3** 与 **idx=4**，`imm=4`，jmp `0x4f6e60` / `0x4f6950`（两目标均在本类主视图槽内）。

每张次视图的 adjustor 数 ∈ `{0:159, 3:100, 5:1}`；槽型模板共 **7** 种且**全部以 AAA 打头**（`AAAFFF:78 / AAA+47F:12 / AAAFFFFF:6 / AAAFF:2 / AAAFFFFFF:1 / AAAAAFFFF:1 / AAA+13F:1`）。

**反控（三点）**：①**954 张主视图内 adjustor 槽 = 0**（0 例外）；②adjustor 的 jmp 目标共 **40** 个、**全部**落 .text、无跳回自身；③**303/305** 的目标落在**本类主视图槽**内（多继承 forwarding），最高频三目标 `0x410260`(75 类) / `0x410300`(74) / `0x410310`(74)。

**与既有律的关系**：律 X 的 305 与 R210 律 V 的 305 thunk **同源同数**；律 X 是律 V 在「次视图 slot0」这一具体位置上的独立性补充（律 V 讲 thunk 通用式 `imm == mT − mV`，律 X 讲次视图 slot0 处 `imm == mdisp`），两者不互为证据。

### 四 · TD+0 负控（禁止用作归属判据）

**988/988 个 TypeDescriptor 的 +0 是同一个值 `0x7f9594`**（distinct=**1**）。该址首槽 `0x7c8ab7` = `push esi ; mov esi,ecx ; call 0x7c8a8e ; test byte [esp+8],1`（scalar deleting dtor 形态）；`0x7f9598` 即 ASCII `Access violation - no RTTI data!`。

引用面：`.text` 内 `0x7f9594` 仅 **2** 处（`0x7c8a93` / `0x7c8b2f` 的 `mov [..],0x7f9594`）、`0x7f9598` 字符串仅 **3** 处 push（`0x7ca956` / `0x7caab0` / `0x7cabe0`）；`.data`/`.rdata` 内 `0x7f9594` 恰 **988** 次且**全部**是 TD+0 槽位本身。

⇒ TD+0 是**共享 type_info 占位 vfptr**，**禁止**用 TD+0 判类归属或视图归属。反控：若以「TD+0 == 本记录 vftable」为判据，命中 **0/1214**。

### 五 · S3（mdisp=21784）函数体全解

mdisp=21784 的 3 条（`MouseClass 0x7fab28` / `TabClass 0x805e90` / `ScrollClass 0x809050`）共享**同一张视图**（各 1 槽，slot0 同为 **`0x6d1770`**）。

函数体 `0x6d1770 .. 0x6d17f3` 逐条：`mov eax,[esp+4]` ; `cmp eax,0x11c7` `jne` → 第二分支 ; 取全局 **`0xb0cc1c`** 作序号 → 读 int 数组 **`[0xb0cb78 + eax*4]`** → `jl 0` / `cmp eax,0x19` `jge`（**上界 25**）→ `lea ecx,[eax+eax*2]` ; `shl ecx,5`（**元素步长 96**）; `add ecx,0xb0c1c0` → `test ecx,ecx` `je` → 读 **byte [ecx+0x2d]** → `test al,al` `jne` 跳过 → `call 0x723ea0` ; 出口 `mov al,1 ; ret 8`。第二分支 `cmp eax,0x11c8` 结构**同构**但判据**反相**（`je` 跳过）并 `call 0x723eb0`，同样 `mov al,1 ; ret 8`。第三出口 `xor al,al ; ret 8`（消息 ID 既非 0x11c7 也非 0x11c8）。

两个被调 `0x723ea0` / `0x723eb0` = `mov eax,[ecx]` + `mov byte [ecx+0x2d],1`（或 `,0`）+ `jmp dword [eax+0x48]` ⇒ 语义为「对第 k 个结构**置/清** `[k+0x2d]` 标志位并转发虚槽 **+0x48**」。

三个全局 `0xb0cb78` / `0xb0cc1c` / `0xb0c1c0` **全部落在 virt-only（BSS，未初始化）**，初值须运行期取（**属动态项，静态轮不得填**）。

### 六 · 0x11c7 / 0x11c8 字面普查与陷阱反控

| 立即数 | .text 字面 | .rdata/.data | 真消息点 | 假阳性构成 |
|---|---|---|---|---|
| `0x11c7` | **2** 处 | **0** | **1**（`0x6d1775` `cmp eax,0x11c7`） | `0x6379fb` 属 `0x6379fa` 的 `push 0x11c7`，字面与指令边界错位 |
| `0x11c8` | **5** 处 | **0** | **1**（`0x6d17b2` `cmp eax,0x11c8`） | **2 处 `__LINE__` 断言宏**（`0x5e0bc4` `push 0x11c8` + `push 0x831288` = `D:\\ra2mdpost\\netdlg2.cpp`；`0x784ed4` 同形 + `push 0x84a430` = `D:\\ra2mdpost\\wonline.cpp`）+ 2 处结构体位移/传参（`0x4a87f0` `mov [esi+0x11c8],eax`；`0x637a8e` `push 0x11c8`） |

另有 `.rsrc` 1 处 `0xb7a8bc`（资源载荷，非立即数）。⇒ **任何「立即数出现 N 次」的结论必须先按指令边界与上下文分类**；本轮 N=2/5 对应的真消息点为 **1/1**。

### 七 · onlysec 引用面（口径复算，推翻子代理报数）

34 个 onlysec TD 的 BCA 引用次数：按 **BCD 记录**计与按**不同 CHD** 计**完全相同** —— 因为 954 个 CHD 的 pBCA **两两不同、无共享**（**954/954**）。

明细（BCD 次数 = CHD 数）：`IUnknown 290` / `IPersist 90` / `IPersistStream 90` / `IClassFactory 78` / `IRTTITypeInfo 78` / `ILocomotion 12` / `IGameMap 9` / `StageClass 9` / `FlasherClass 6` / `IPiggyback 6` / `CComObjectRootEx 5` / `CComObjectRootBase 5` / 其余含 `IWOLBrowserEvent`/`DiskSwap`/`INetUtilEvent@WOL`(2)/`IChatEvent@WOL`(2) 等。

**「恰被 1 条 BCD 引用」= 20 条**（**不是 32 条**）。0 引用者 **0** 条（34/34 全被引用）。

### 八 · 自错与订正（5 组，0 条进结论）

1. 调度卡与 `x0.py` 把 vftable 起点写成 **COL+4**；EX1 子代理当场指出，重写为「前驱位点+4」后闭环（反控 0/1214）。
2. `xa.py` T2-6 断言「恰 1 次引用 = 32 条」**直接采信子代理报数未先复算**；主会话 `d1_recheck.py` 实测 **20** 条。
3. `xa.py` T5-8 断言「槽型模板 6 种」，实测 **7** 种。
4. `xa.py` T6 反汇编窗口只取 40 条导致第二分支被截断，误报 T6-4 / T6-8 两个 FAIL；扩窗到 64 条后 **PASS**（`ins(f,64,maxb=400)`）。
5. `d1_recheck.py` 首版把审计员报的 32 与「BCA 共享」当断言写死（D2/D4），复算后改为**反证其两条附注错**。

### 九 · 跨家族（§2.12 规则 D 全复算）

**#546 / #547（hy4 `exec`，EX1/EX2）**：EX1 14 回合 / 3.22' vs 8.0、EX2 19 回合 / 3.68' vs 8.0，均**无 OVERTIME**。EX1 交付 A1–A11（其最大价值是**指出我方卡面 vftable 口径错**，并列两种口径的实测数）；EX2 交付 B1–B9，其 B6 报「恰 1 次 = 32 条」经主会话复算**推翻为 20**。

**#549（deepseek `audit` 只读）**：19 回合 / **2.20'** vs 8.0，无 OVERTIME，**12/12 PASS**。其三条附注经 `d1_recheck.py` **13 断言 0 FAIL** 逐条复算：

- 附注①「vftable 位点全在 .rdata、.data 内 0」：**成立**（`{.rdata:1214, .data:0}`）。
- 附注②「`.rsrc` 另有 0x11c8 一处 `0xb7a8bc`」：**成立**（确为资源载荷）。
- 附注③「按记录地址计 BCA 会得『34 条全 0 引用』」：**成立**，但**不是**我方口径；我方按 BCA 元素指向的 TD 计（1002 个 distinct 元素地址、988 个被引用 TD），已复核。
- **其 G12 附注「32 条恰被 1 条 BCD 引用」不成立**：实测 **20** 条。

### 十 · 落盘与门禁

`_r213/xa.py` 主会话单一复算源（**51 断言 0 FAIL**）、`_r213/x1.py`（14 断言，含 5 FAIL 的中间态，已由 xa 取代）、`_r213/x7.py`（10 断言 2 FAIL 中间态）、`_r213/x8.py`（11 断言 0 FAIL）、`_r213/d1_recheck.py`（**13 断言 0 FAIL**）。

**FACT_INDEX V595 → V596**：F01 与 F29 各追加（其余 **56 行逐字节不变**），sha `9ffc56c9` → **`fd18fe6a`**、257435 → **264072** B（+6637）；指针文件 + `facts_floors.py`（EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / MASTER `835e4388` → **`ea10885c`**）+ `gate_runner.LEDGER` 同步重钉 V596；`check_disc.py` 的 `C16_FLOORS` 纳入 **221**。
"""
assert '## 2.221' not in raw.decode('utf-8',errors='replace'),'already exists'
nb=(raw.decode('utf-8')+('\n' if not raw.endswith(b'\n') else '')+SEC).encode('utf-8')
open(F,'wb').write(nb)
r2=open(F,'rb').read()
assert r2==nb
print('after: bytes=%d CR=%d'%(len(r2),r2.count(b'\r')))
assert r2.count(b'\r')==1081,r2.count(b'\r')
print('OK §2.221 appended, CR still 1081')
