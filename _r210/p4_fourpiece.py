# -*- coding: utf-8 -*-
"""R210 p4：四件套 + 归档（看板开局 253 行 < 260 ⇒ 不归档）。
  R14_COMMON §2.218（CR 保持 1081）
  GOAL §1268（CR 保持 337）
  LEAD_LOCK QS（CR 保持 137）
  STATUS_BOARD 第 210 轮（CR 保持 0，总行数 <= 300）
每处写入：wx 独占备份 -> 断言旧 CR -> 一次写入 -> 回读校验。
"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=ROOT+'/lead'; TIER=LEAD+'/next_re_20261117_r14'; BASE=LEAD+'/R17_LEAD_BASELINE'
R14=TIER+'/R14_COMMON.md'; GOAL=LEAD+'/GOAL_THREE_TARGETS_20261018.md'
LOCK=LEAD+'/LEAD_LOCK'; BOARD=TIER+'/STATUS_BOARD.md'
def backup(path,tag):
    b=open(path,'rb').read()
    bak=BASE+'/'+os.path.basename(path)+'.before_r210_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    return b
def commit(path,nb,ob,exp_cr,tag):
    assert nb.count(b'\r\n')==exp_cr,(tag,nb.count(b'\r\n'),exp_cr)
    tmp=path+'.r210tmp'; open(tmp,'wb').write(nb); os.replace(tmp,path)
    assert open(path,'rb').read()==nb
    print('OK %-22s %d -> %d B  CR %d'%(os.path.basename(path),len(ob),len(nb),nb.count(b'\r\n')))

S218='''## 2.218 · R210（2026-11-28）· 律 U（视图偏移 == {4} ∪ 本类 QI 正偏移，954/954）；律 V（thunk 通用式 imm == mT − mV 且落点 == 同类 mV 视图同槽，305/305）；mdisp→形态交叉表；V592

**一、🔴 律 U（视图偏移集合 = ({4} ∪ 本类 QI 返回的正偏移)，正偏移为空则集合为空；954/954 零失配）.** 判据：对 954 个类的**主视图（mdisp==0）slot0 函数**解析「返回 this 偏移」集合 R。解析器经三轮收紧：①函数体内必须出现 `rep` 前缀比较指令（`repe cmpsd`）才判为 QI 形态；②`lea reg,[x+K]` 的 K 只在随后 **8** 条内被写进 `mov dword ptr [out], reg` 时才计入；③非 QI 形态类的 R 强制为空。
实测分布（954 类全量）：

| R 的正偏移集合 | 类数 | T 视图偏移集合 |
|---|---|---|
| 空 | 863 | 空 |
| {4} | 83 | {4} |
| {24} | 6 | {4,24} |
| {1728} | 1 | {4,1728} |
| {36,40,44} | 1 | {4,36,40,44} |

⇒ **{4} 是「QI 至少返回一个正偏移」时附加的固定项**：对 83 类它与 QI 自返的 +4 重合（冗余），对另外 **8** 类（6 个 Locomotion + `AircraftClass` + `HouseClass`）它是**独立附加项**（这 8 类的 QI 不返回 +4）。
四项反控：把「全 QI 正偏移并集」套到 863 个空类上 ⇒ 成立数 **0**（逐类取值不可省）；去掉 {4} ⇒ 83 类仍成立说明该项对 83 冗余、对 8 必需；不先分离 QI 形态而把所有 slot0 纳入 ⇒ 出现 **1** 个假阳性（`BaseClass` slot0 `0x42ee30` 是普通工厂，其 `lea esi,[ebp+4]` 与出参无关）；QA 交叉核：v4 判出的 91 类与「slot0 落在 R209 的 12 个 QI 目标」的 91 类**完全同一**（差集 0/0）。
**未取得**：{4} 项里 IRTTITypeInfo 那一支**为什么**对这 8 类成立（见五）。

**二、🔴 {4} 的两侧分解（BCD 给名 / QI 给偏移，90/91 吻合）.** 同类 BCA 里 `mdisp==4` 的 BCD 记录恒 **2** 条（`.?AUIUnknown@@` + 真接口），91 类的真接口名分布：`.?AUIRTTITypeInfo@@` **78** / `.?AUILocomotion@@` **12** / `.?AUILinkStream@@` **1**。QI 侧返回 +4 的 IID：`0x7e9ae0`(170DAC82-…) **77 类** / `0x7ed358`(070F3290-…) **12 类** / `0x7e9530`(0D5CD78E-…) **1 类**，合计 **90**。
**唯一不匹配 = `.?AVHouseClass@@`**：BCD 侧声明 IRTTITypeInfo@+4，但其 QI `0x4f6830` 的返回偏移集合是 `{0,36,40,44}` **无 4**；该类的 +4 视图 slot0 thunk `0x510a20` 落点正是 `0x4f6830`（与主视图同一个 QI）。

**三、🔴 律 V（this 调整 thunk 通用式；305/305）.** 对每个含 thunk 的视图槽（305 处 = 303 前三槽 + HouseClass slot3/slot4），设本视图偏移 `mT`、槽号 k：
`立即数 == mT − mV` 且 `E9 落点 == 同类内偏移 mV 视图的第 k 槽地址`，且 `mV` 必在本类视图偏移集合内。**305/305 成立**。
mV 分布 `{0:303, 36:2}`；槽号分布 `{0:101, 1:101, 2:101, 3:1, 4:1}`；(mT,mV) 对 **7 种**：`(4,0) 273` / `(24,0) 18` / `(36,0) 3` / `(40,0) 3` / `(44,0) 3` / `(1728,0) 3` / `(40,36) 2`。
反控：`imm+4` ⇒ 命中 **0**；允许跨类同名 mV ⇒ 仅 241 命中（同类约束非空）。
⇒ **R209 §2.217 五「越界 2 槽 imm 是接口偏移、不遵循 thunk-imm==mdisp」被本条取代**：越界槽是 `(40,36)` 的普通实例，不是例外。

**四、🟡 mdisp → 形态交叉表（260 张额外视图全量、零残留）.** `4→T 91` / `8→{S2 75, I 3}` / `12→S1 78` / `24→T 6` / `36,40,44,1728→T 各 1` / `21784→S3 3`。⇒ **偏移决定形态**，不是形态决定偏移。附：主视图 954 表全槽 **12726**、slot≥3 槽 **9958**（执行员 #538 实测，主会话 c2 复算一致）；slot3 落点 ret 立即数 top3：`ret 510` / `ret 0x10 81` / `ret 0x1c 60`；slot3 独占 **686** 表、复用 **132** 表、短表无 slot3 **136** 张。

**五、⚪ 未取得（本轮新增/续）.** ① {4} 独立附加项对 8 类成立的**成因**（HouseClass 的 QI 不返回 +4 却在 BCD 声明 IRTTITypeInfo@+4，静态无第三条线可判）；② 12 个 QI 目标的**具名 IID**（只有 `0x7f7c90/0x7f7c80/0x7f7c70` 是 `0000…-C000-000000000046` 形态的 OLE 标准前缀，其余 8 个 Westwood 私有 GUID 无外部头文件对照）；③ 主视图 9958 个 slot≥3 槽的语义归属（本轮只给 ret 立即数分布）；④ S3 三表（`MouseClass`/`TabClass`/`ScrollClass`，mdisp 21784）的 `0x11c7`/`0x11c8` 语义；⑤ `attributes` 位义（须 `win-main` 动态）；⑥ F23/F35 grade（两 tsv 不可读，禁预估回填）；⑦ C7 三死分支、C11 十二 ID。

**六、🟡 跨家族（§2.12 规则 D 全复算）.** 执行员 **#538**（hy4，10 回合 / **2.25'** vs 预算 8.0，无 OVERTIME）：主视图 slot≥3 普查 5 项全 PASS（954 / 9958 / 686 / 132 / 136 / slot3 ret top1=ret 510），主会话 c2 逐数复算一致。执行员 **#539**（hy4，7 回合 / **0.98'**，无 OVERTIME）：6 项全 PASS（70 thunk / 303 前三槽 / 23 三元组 / 13 jmp 三元组 / 孤儿 0 / 组内 mdisp 唯一），并给出 mdisp 4 与 24 成对 **6** 组（J05/J06/J10/J11/J12/J13）。
审计员 **#540**（deepseek，36 回合 / **8.72'** vs 预算 8.0 ⇒ **[OVERTIME] 如实记**）报 `error_max_turns`，最终 `result` 为空、0 条结论采信；但其崩溃前落盘 `_r210/audit_deepseek.json` 可读：其 **G2 组（律 V）自算 305/305、imm+4 命中 0、by_k 101/101/101/1/1、distinct_thunks 70 = 与我方逐数一致**；**G3 组（主视图普查）自算 12726 / 9958 / 136 / 818 / 686 / 132 / slot3 ret top1=511**（511 vs 我方 510 差 1，因其把「无 ret」单列口径不同，主会话 c2 复算确认 510 + none 6 = 516 中 510 为 ret 形态）；其 **G1 组 FAIL 947** 是**口径错**（它把 pred 定义为 `{4}` 套到全部 954 类，未区分 QI 形态与非 QI 形态），主会话 c20 M1 用正确判据得 954/954 零失配，故 G1 不采信但记其在 `0x4f4240`（9 个类的 slot0）上的发现——该函数经 c16 判定为**非 QI 形态**（无 rep 前缀），其 9 个类视图集合全为 {0} 或 {0,21784}，与律 U 无冲突。

**七、📌 自错 6 组（0 条进结论）.** ①`c4` 用 `disasm_lite` 返回元组却取 `ins[1]` 当 mnemonic（应为 `ins[2]`）⇒ 首轮 0 命中；②`c2`/`c9` 的 `lea` 偏移正则只接受十六进制，而 capstone 对小于 0x10 的位移输出十进制 `4` ⇒ 把 `0x410260` 的 `lea ecx,[ebx+4]` 漏掉，害得我先误报「HouseClass 是律 U 唯一例外」并写进 V592 第一版（已作废重写）；③`c16` 用 `i.mnemonic=='repe'` 判 rep 前缀，而 capstone 把 `repe cmpsd` 整体作为 mnemonic `'repe cmpsd'` ⇒ 185 个 QI 形态类全判成 0；④`c15` 先按「跟进委托边」写死预期失配数，实测 **0**（6 条委托边指向的 QI 自身不返回正偏移，闭包对 T 类是 no-op）⇒ 已把该说法从 V592 中删除，改写为「无关项，不作证据」；⑤`c20` 的反控 A/B 预期值（91/10）与实测（83/83）不符，实测含义是「{4} 对 83 类冗余、对 8 类必需」，断言已按实测改写；⑥`p1` 因②的订正两次重建 V592 目录（第一版 `735a7b5b/249150` 已删除，最终 `b3327fd4/249545`），指针先指向旧值再同步。

**八、🟡 落盘与门禁.** 本段 **§2.218** CR 保持 **1081**；GOAL **§1268** CR 保持 **337**；LEAD_LOCK **QS** CR 保持 **137**；STATUS_BOARD 第 210 轮 CR 保持 **0**（开局 **253 行 < 260**，**不归档**）。**FACT_INDEX V591→V592**：把律 U / 律 V / mdisp→形态交叉表写入 **F29**（stmt 7377→10553 B、lim 21688→22603 B，其余 55 行逐字节不变；57 行 / 5 列 / grade 与第 4 列全同），sha `c529a08c`→**`b3327fd4`**、245454→**249545** B；指针 + facts_floors（EXPECT_CUR/CUR_SHA256/TOTAL_BYTES/MASTER `ba31ddc1`→`519ee33a`）+ gate_runner LEDGER 同步重钉。三门 exit 0：`check_disc`（C15 末节 218、C16 210 节全钉、C19 ok(b3327fd4/249545/V592)、C20 ok）、`facts_floors`（D8 249545、D9/D10 一致、MASTER 519ee33a）、`gate_runner`（G1=G2=G3=ok）。

'''
b=backup(R14,'r14_218')
assert b.count(b'\r\n')==1081
assert b.count(b'## 2.218')==0
nb=b+b'\n'+S218.encode('utf-8')
commit(R14,nb,b,1081,'r14_218')
