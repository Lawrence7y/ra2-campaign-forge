# -*- coding: utf-8 -*-
"""R215 p5：R14_COMMON.md 追加 §2.223（全 LF，CR 保持 1081）。"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/lead/R17_LEAD_BASELINE'
F=TIER+'/R14_COMMON.md'
b=open(F,'rb').read()
OLD_SHA=hashlib.sha256(b).hexdigest(); OLD_B=len(b)
print('before sha=%s bytes=%d CR=%d LF=%d'%(OLD_SHA[:8],OLD_B,b.count(b'\r'),b.count(b'\n')))
assert b.count(b'\r')==1081, b.count(b'\r')
assert OLD_B==1904851, OLD_B
bak=BASE+'/R14_COMMON.md.before_r215_2223_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
assert open(bak,'rb').read()==b

SEC = """
## 2.223 R215（2026-11-28）· 虚槽 +0x48 落点归因：27 落点 = 9 多类组 + 18 单类组；0x4104c0 = 基类 12 字节描述符取值器；931 处消费位点归并 273 函数；四处口径订正

### 一 · 组结构严格闭合

R214 只给 slot18 的 27 个落点分布与复用度，本轮做归因。槽数 > 18 的视图 137 张，其 slot18 目标严格闭合为
**9 个多类组（覆盖 119 视图）+ 18 个单类组 = 137**。9 组 = `0x4104c0`×**56** / `0x5f65a0`×**19** / `0x4e1960`×**17** /
`0x4c9150`×**9** / `0x5d6450`×**8** / `0x7ba8c0`×**3** / `0x557fd0`×**3** / `0x7aa6a0`×**2** / `0x7b1740`×**2**。

### 二 · 0x4104c0 = 基类 12 字节描述符取值器

该地址在 14044 槽里**只出现在 slot18（56/56，槽号集合 = {18}）**。函数体 9 条指令：

    004104c0  8b442404          mov eax, dword ptr [esp + 4]
    004104c4  8b1580768800      mov edx, dword ptr [0x887680]
    004104ca  8bc8              mov ecx, eax
    004104cc  8911              mov dword ptr [ecx], edx
    004104ce  8b1584768800      mov edx, dword ptr [0x887684]
    004104d4  895104            mov dword ptr [ecx + 4], edx
    004104d7  8b1588768800      mov edx, dword ptr [0x887688]
    004104dd  895108            mov dword ptr [ecx + 8], edx
    004104e0  c20400            ret 4

即「取 [esp+4] 出参指针 + 从三个全局各读 1 dword 写入 [eax+0]/[+4]/[+8]」。**三个全局 0x887680 / 0x887684 / 0x887688
全部落 .data 的 virt-only 区（r2o == None，BSS，文件内无字节）** ⇒ 运行期初值须 win-main 动态取证。
其宿主基类为 `?AVAbstractClass@@` 主视图 `0x7e1f50`（24 槽）的 slot18。

### 三 · 配套消费者：+0x48 = 返回 3 dword 的虚槽

全 .text 的 `call/jmp [reg+0x48]` 以 capstone `skipdata=True` 分块 `disasm_lite` 扫得 **931** 处
（call 929 / jmp 2）；纯字节口径交叉核对 = 非 SIB `FF /2|mod=01|disp8=0x48` **928** + SIB `FF /2|rm=100|[esp+0x48]` **1**
+ `FF /4`（jmp）**2** = **931**，两口径完全一致。按「所属函数 = ≤ 该位点的最大 vftable 槽目标」归并：
**677 位点归入 273 个函数**，其余 **254** 位点距最近槽函数 > 4096 B（口径声明：该归并是下界，不是全集）。

slot19 默认桩 `0x4104f0`（73 视图）与 slot22 默认桩 `0x410540`（77 视图）**体内各含 1 处 `ff 50 48`**（0x4104fb / 0x41054b），
形态一致：`mov eax,[ecx]` / `sub esp,0xc` / `lea edx,[esp]` / `push esi` / `push edx` / `call [eax+0x48]` /
把返回指针的 3 个 dword 拷给出参 ⇒ **+0x48 是「返回 3 dword 描述符」的虚槽**，与 0x4104c0 写 0/4/8 三 dword 同型。
27 个落点中**只有 5 个**自身符合「写 3 dword 到偏移 0/4/8」（0x4104c0 / 0x5f65a0 / 0x422be0 / 0x447ac0 / 0x486840），
其余落点形态各异（纯桩、单字节置位、40 条以上长体）⇒ **「同槽同语义」在 27 落点上不成立**，只有 9 个多类组内部成立。

### 四 · +0x48 的特异性反控

disp8 邻值对照（`FF /2|/4`，非 SIB 口径）：0x44 → **133**、0x47 → **0**、**0x48 → 930**、0x49 → **1**、0x4c → **124**。
0x48 是同量级邻值（133 / 124）的约 **7 倍**，且紧邻的 0x47 / 0x49 近乎空 ⇒ 该 disp8 非通用噪声，但**也不是唯一热点**
（0x0c 1359 / 0x08 1305 / 0x10 1086 / 0x2c 864 / 0x84 819 均更高，0x48 全段热度排名 **第 6**，764 次）。

### 五 · 显式失效判据（两条判据被判死）

1. **「目标只出现在本槽号」不是 slot18 特有信息**：该比例在 slot17/18/19 上为 96.4% / 96.3% / 96.3%，而同法在
   slot0..slot6 上为 **99.7–99.9%** ⇒ 越低反而说明「目标被别的槽号复用」，不可作 slot18 语义证据。
2. **「组内 slot18 distinct == 1」不是 slot18 独有**：各组内 slot18 的 distinct=1 与 2–12 个其它槽号**并列**
   （0x4e1960 组并列 12 个、0x557fd0 组并列 20 个）⇒ slot18 不是组内唯一未覆写槽。
3. **「前缀聚簇一致性」同型失效**：按 `slot0` 单元组 / `slot0..1` 二元组 / `slot0..2` 三元组聚簇，
   slot18 一致簇 = 47 / 48 / 48（簇数 50 / 51 / 51）⇒ 前缀从 1 加到 3 只多 1 个一致簇，**一致性基本由 slot0 决定**。

### 六 · 四处口径订正（审计 #557 指出，主会话全部复算成立）

1. **「305」是双口径同值巧合**：adjustor **出现次数** 305 与 `call [eax+0x48]` **字节口径站点数** 305 数值相同，
   但两个地址集合**交集 = 0**，不可互相充当论据。adjustor 的 **distinct 桩地址只有 70**：
   imm8 形式 `83 6c 24 04` **67** 个（IMM 分布 `{4:40, 0x18:18, 0x24:3, 0x28:3, 0x2c:3}`）、
   imm32 形式 `81 6c 24 04 ..` **3** 个（IMM 全 `0x6c0`）。
2. **Locomotion 组 = 11 派生 + 基类**：mdisp=4 的 50 槽视图共 **12** 张（含基类 `?AVLocomotionClass@@`，非 12 个派生类）；
   12 张逐槽比对**只有 [21, 22] 全同**（值 `0x55ab90` / `0x55a8f0`），其余 **48** 槽各异。主视图槽数 **11 个是 10 槽、
   `?AVTeleportLocomotionClass@@` 是 12 槽** ⇒ 该组 12 张主视图**无一有 slot18**，slot18 落点全在 mdisp=4 次视图。
3. **0x4104f0 体内 `ff 50 48` 只有 1 处**（0x4104fb）；用 +0x120 宽窗口扫会把相邻 0x410540 的 0x41054b 计入，须按函数边界收窄。
4. **三个全局 0x887680/84/88 全为 virt-only**，文件内无字节可给（R215 卡面曾要求给出字节内容，属不可满足要求）。

### 七 · INoticeSink / AircraftClass 收口

- `?AVINoticeSink@@` 只有 **1** 张视图（`0x7e1fbc`，mdisp=0，1 槽 `0x4c9150`）；mdisp==8 的视图 **78** 张、
  mdisp==21784 的视图 **3** 张（Mouse `0x7e195c` / Tab `0x7edfac` / Scroll `0x7f108c`）。
  **全体 70 个 adjustor 桩的 IMM 不含 8 也不含 21784** ⇒ 「INoticeSink 被 8/21784 两偏移引用」的原始猜想**不成立**（无隐藏反例）。
- `?AVAircraftClass@@`（无 I）五视图：`0x7e2250`(1728, 9 槽) / `0x7e2278`(12,1) / `0x7e2280`(8,1) / `0x7e2288`(4,6) /
  `0x7e22a4`(0, **341** 槽)。mdisp=1728 视图 slot0/1/2 值 `0x41c670` / `0x41c680` / `0x41c690` 为三条 **8 字节**桩
  （`81 6c 24 04 c0 06 00 00 e9 ..`，IMM = `0x6c0`），jmp 落 mdisp=0 主视图 `0x7e22a4` 的 slot0/1/2
  （`0x414290` / `0x4142f0` / `0x414300`），律 X `imm == mdisp_self − mdisp_target` = 1728 − 0 **3/3 成立**；
  `0x7e2250/54/58` **不作为任何视图槽值**。

### 八 · 跨家族（§2.12 规则 D 全复算）

| 任务 | 家族 / 角色 | 回合 | 用时 | 预算 | OVERTIME |
|---|---|---|---|---|---|
| #555 | hy4 exec | 24 | **1.92'** | 10 | 无 |
| #556 | hy4 exec | 7 | **2.62'** | 10 | 无 |
| #557 | deepseek audit（只读） | 13 | **3.95'** | 20 | 无 |

审计 #557 的 4 条订正**全部经主会话复算成立**（`_r215/m15_audit_fix.py` **8 断言 0 FAIL**）：305 双口径、Locomotion 11+1、
0x4104f0 单处、三全局 virt-only。主会话独立复算源（不复用子代理代码）：`_r215/m1_recheck.py` 3 断言、
`m9_recheck_exec2.py` **11/0**、`m12_claims.py` **17/0**、`m15_audit_fix.py` **8/0**；exec 的 ex1.json / ex2.json 均已重算一致。

### 九 · 自错（0 条进结论）

1. `m7_family_inherit.py` 的「与主导签名逐槽等 = 18/18」是**恒真**（主导签名就是多数类自己的前 18 槽），该组数字作废。
2. `m12_claims.py` 首版 SIB 扫描漏加 `reg∈{2,4}` 过滤 ⇒ SIB=3（含 2 条 `/0` 的 `test`）误报 FAIL，加过滤后 =1。
3. `m14_consumers.py` 的 owner 判定把「命中点自身」当函数起点 ⇒ 931 个"函数"（恒真），改用槽目标集合二分后得 273。
4. `p3_repin598.py` 的 wx 备份已存在（p3 首次运行已改三常量）⇒ 重跑报 FileExistsError，改走 `p3c_master598.py` 单独重钉 MASTER。

### 十 · 落盘与门禁

- **FACT_INDEX V597 → V598**：仅 F29 追加，其余 **57 行逐字节不变**，sha `42762bfb` → **`45d366ae`**、270750 → **275368** B（+4618）。
- 指针文件 + `facts_floors.py`（EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / MASTER `09558a11` → **`87f42300`**）+ `gate_runner.LEDGER`（V598）同步重钉。
- `check_disc.py` 的 `C16_FLOORS` 纳入 **223**。

### 十一 · 未取得

1. 主视图 **9958** 个 slot≥3 槽的语义归属（本轮只解了 slot18 一个槽）。
2. 三个全局 `0x887680/84/88` 的运行期初值（**virt-only BSS ⇒ 须 win-main**）。
3. `0xb0cb78` / `0xb0cc1c` / `0xb0c1c0` 三全局初值与 0x19 元素结构（同上）。
4. `[ecx+0x2d]` 标志位语义。
5. 254 个未归并的 +0x48 消费位点（距最近槽函数 > 4096 B）。
6. 21 个落点（27 − 5 同型 + 1 桩）的语义族归属：仅知形态，未知语义。
7. F23/F35 grade；C7 三死分支、C11 十二 ID。
"""
SEC_LF = SEC.replace('\n','\n')   # 全 LF
new = b + SEC_LF.encode('utf-8')
nb = SEC_LF.encode('utf-8')
out = b + nb
open(F,'wb').write(out)
assert open(F,'rb').read()==out
r=open(F,'rb').read()
print('after  sha=%s bytes=%d (+%d) CR=%d LF=%d'%(hashlib.sha256(r).hexdigest()[:8],len(r),len(r)-OLD_B,r.count(b'\r'),r.count(b'\n')))
assert r.count(b'\r')==1081, r.count(b'\r')
open(ROOT+'/_r215/p5_out.txt','w').write('2.223 %d\n'%len(nb))
