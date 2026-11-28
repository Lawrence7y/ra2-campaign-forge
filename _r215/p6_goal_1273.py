# -*- coding: utf-8 -*-
"""R215 p6：lead/GOAL_THREE_TARGETS_20261018.md 追加 §1273（CR 保持 337）。"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
F=ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md'
b=open(F,'rb').read()
print('before sha=%s bytes=%d CR=%d LF=%d'%(hashlib.sha256(b).hexdigest()[:8],len(b),b.count(b'\r'),b.count(b'\n')))
assert b.count(b'\r')==337, b.count(b'\r')
assert len(b)==5456181, len(b)
bak=BASE+'/GOAL_THREE_TARGETS_20261018.md.before_r215_1273_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
assert open(bak,'rb').read()==b

SEC = """
## §1273 · R215（2026-11-28）· 虚槽 +0x48 落点归因：137 视图闭合为 9 多类组 + 18 单类组；0x4104c0 = 基类 12 字节描述符取值器；931 处消费位点归并 273 函数；四处口径订正；FACT_INDEX V598

**一 · 组结构.** 槽数 > 18 的 137 张视图，其 slot18 目标 = **9 个多类组（覆盖 119 视图）+ 18 个单类组**= 137。
9 组 = `0x4104c0`×56 / `0x5f65a0`×19 / `0x4e1960`×17 / `0x4c9150`×9 / `0x5d6450`×8 / `0x7ba8c0`×3 / `0x557fd0`×3 / `0x7aa6a0`×2 / `0x7b1740`×2。
18 单类组 = 12 张 `*LocomotionClass@@`（mdisp=4 次视图）+ Anim / Building / Cell / IPXManager / IPXGlobalConn / UDPInterface 各 1。

**二 · 0x4104c0 语义.** 在 14044 槽里**只出现在 slot18（槽号集合 = {18}，56 次）**。函数体 9 条：
`mov eax,[esp+4]` → 三次「从全局 0x887680/0x887684/0x887688 各读 1 dword 写 [eax+0]/[+4]/[+8]」→ `ret 4`。
**三个全局全落 .data virt-only（r2o=None，BSS）** ⇒ 运行期初值须 win-main。宿主基类 = `?AVAbstractClass@@` 主视图 `0x7e1f50`（24 槽）。

**三 · +0x48 = 返回 3 dword 的虚槽.** 全 .text `call/jmp [reg+0x48]` = **931**（capstone skipdata 分块 lite；字节口径交叉核对
非 SIB 928 + SIB 1 + jmp 2 = 931，两口径一致）。按「所属函数 = ≤ 位点的最大 vftable 槽目标」归并：**677 位点 → 273 函数**，
其余 **254** 位点距最近槽函数 > 4096 B（下界口径）。slot19 桩 `0x4104f0`（73 视图）与 slot22 桩 `0x410540`（77 视图）
体内各 1 处 `ff 50 48`，形态 `mov eax,[ecx] / sub esp,0xc / lea edx,[esp] / push esi / push edx / call [eax+0x48] / 拷 3 dword 给出参`。
27 落点中仅 **5** 个自身符合「写 3 dword 到 0/4/8」⇒ **「同槽同语义」只在组内成立，跨组不成立**。

**四 · 特异性反控.** disp8 邻值 `FF /2|/4` 非 SIB：0x44→133、**0x47→0**、**0x48→930**、**0x49→1**、0x4c→124。
0x48 是邻值的约 7 倍且紧邻近乎空；但全段 disp8 热度 **0x48 仅第 6**（0x0c 1359 / 0x08 1305 / 0x10 1086 / 0x2c 864 / 0x84 819 / **0x48 764**）⇒ 特异但非唯一热点。

**五 · 三条判据被判死.** ①「目标只出现在本槽号」在 slot17/18/19 = 96.4/96.3/96.3%，而 slot0..6 = **99.7–99.9%** ⇒ 非 slot18 特有；
②「组内 slot18 distinct=1」与组内 2–12 个其它槽号**并列**（0x4e1960 组并列 12、0x557fd0 组并列 20）⇒ 非唯一未覆写槽；
③前缀聚簇 slot0 单/二/三元组一致簇 = 47/48/48（簇 50/51/51）⇒ 一致性由 slot0 决定，前缀加长几乎无增量。

**六 · 口径订正 4 条（审计 #557，主会话 `_r215/m15_audit_fix.py` 8 断言 0 FAIL 复算成立）.**
①「305」双口径同值巧合：adjustor 出现次数 305 与 `call [eax+0x48]` 站点 305 数值同、**地址集合交集 0**；adjustor **distinct 桩仅 70**
（imm8 `83 6c 24 04` **67**，IMM `{4:40, 0x18:18, 0x24:3, 0x28:3, 0x2c:3}`；imm32 `81 6c 24 04` **3**，IMM 全 `0x6c0`）。
②Locomotion 组 = **11 派生 + 基类**（非 12 派生）；12 张 mdisp=4 视图逐槽**仅 [21,22] 全同**（0x55ab90 / 0x55a8f0），其余 48 槽各异；
主视图 **11 张 10 槽 + Teleport 12 槽** ⇒ 无一有 slot18。③`0x4104f0` 体内 `ff 50 48` **仅 1 处**（0x4104fb），宽窗口扫会并入 0x410540 的 0x41054b。
④三全局 **virt-only**，文件内无字节。

**七 · INoticeSink / Aircraft 收口.** `?AVINoticeSink@@` **仅 1 视图**（0x7e1fbc，mdisp=0，1 槽 0x4c9150）；mdisp==8 → **78** 视图、
mdisp==21784 → **3** 视图（Mouse 0x7e195c / Tab 0x7edfac / Scroll 0x7f108c）；**70 个桩 IMM 不含 8 也不含 21784** ⇒
「8/21784 双偏移」猜想**不成立**。`?AVAircraftClass@@` 五视图 `0x7e2250`(1728,9) / `0x7e2278`(12,1) / `0x7e2280`(8,1) / `0x7e2288`(4,6) / `0x7e22a4`(0,**341**)；
1728 视图 slot0/1/2 = `0x41c670` / `0x41c680` / `0x41c690`（三条 8 字节 `81 6c 24 04 c0 06 00 00 e9 ..`，IMM `0x6c0`），
jmp 落主视图 `0x7e22a4` slot0/1/2（`0x414290` / `0x4142f0` / `0x414300`），律 X **3/3 成立**；`0x7e2250/54/58` 不作任何槽值。

**八 · 跨家族.** #555（hy4 exec）24 回合 / 1.92' vs 10 无 OVERTIME；#556（hy4 exec）7 回合 / 2.62' vs 10 无 OVERTIME；
#557（deepseek audit 只读）13 回合 / 3.95' vs 20 无 OVERTIME，4 条订正全成立。主会话独立复算：`m9_recheck_exec2.py` 11/0、
`m12_claims.py` 17/0、`m15_audit_fix.py` 8/0（不复用子代理代码）。

**九 · 自错 4 组（0 条进结论）.** ①`m7` 的「与主导签名逐槽等 18/18」恒真（主导签名即多数类自身前 18 槽），该组数字作废；
②`m12` 首版 SIB 扫描漏 `reg∈{2,4}` ⇒ SIB=3 误报 FAIL，加过滤后 =1；③`m14` owner 判定退化为「命中点自身」⇒ 931 个"函数"恒真，改二分后 273；
④`p3_repin598.py` 备份已存在（首跑已改三常量）⇒ FileExistsError，改 `p3c_master598.py` 单独重钉 MASTER。

**十 · 落盘与门禁.** FACT_INDEX **V597→V598**（仅 F29，其余 57 行逐字节不变），sha `42762bfb`→`45d366ae`、270750→**275368** B（+4618）；
R14_COMMON **§2.223**（CR 保持 **1081**，1904851→**1913694** B）；本段 **CR 保持 337**；LEAD_LOCK **QR**（CR 保持 **137**）。
指针 + `facts_floors`（MASTER `09558a11`→**`87f42300`**）+ `gate_runner.LEDGER` 重钉 V598；`C16_FLOORS` 纳入 **223**（**215** pins，sha `0d51c0d9`→**`d1d2aa6e`**）。
三门实测：`check_disc.py` exit 0（live checks 31）/ `facts_floors.py` exit 0（D0–D10 全 PASS）/ `gate_runner.py` exit 0（G1/G2/G3a–G3f 全 PASS）。

**十一 · 未取得.** ①主视图 9958 个 slot≥3 槽语义（本轮只解 slot18 一槽）；②三全局 0x887680/84/88 运行期初值（virt-only，须 win-main）；
③`0xb0cb78`/`0xb0cc1c`/`0xb0c1c0` 初值与 0x19 元素结构；④`[ecx+0x2d]` 位义；⑤254 个未归并 +0x48 消费位点；⑥21 个落点的语义族归属；
⑦F23/F35 grade；⑧C7 三死分支、C11 十二 ID。
"""
out = b + SEC.encode('utf-8')
open(F,'wb').write(out)
r=open(F,'rb').read()
print('after  sha=%s bytes=%d (+%d) CR=%d'%(hashlib.sha256(r).hexdigest()[:8],len(r),len(r)-5456181,r.count(b'\r')))
assert r.count(b'\r')==337
