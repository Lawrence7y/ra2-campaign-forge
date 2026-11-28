# -*- coding: utf-8 -*-
"""R210 p5：GOAL §1268 + LEAD_LOCK QS + STATUS_BOARD 第 210 轮。"""
import os
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=ROOT+'/lead'; TIER=LEAD+'/next_re_20261117_r14'; BASE=LEAD+'/R17_LEAD_BASELINE'
GOAL=LEAD+'/GOAL_THREE_TARGETS_20261018.md'; LOCK=LEAD+'/LEAD_LOCK'; BOARD=TIER+'/STATUS_BOARD.md'
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
    print('OK %-22s %d -> %d B  CR %d  lines %d'%(os.path.basename(path),len(ob),len(nb),nb.count(b'\r\n'),nb.count(b'\n')))

G1268='''## §1268 · R210（2026-11-28）· 律 U：视图偏移集合 = ({4} ∪ 本类 QI 正偏移)，954/954 零失配；律 V：thunk 通用式 imm == mT − mV 且落点 == 同类 mV 视图同槽，305/305；mdisp→形态交叉表；FACT_INDEX V592

**一、🔴 律 U（954/954）.** 对 954 个类的主视图 slot0 函数解析「返回 this 偏移」集合 R（判据三重收紧：体内须有 `rep` 前缀比较指令；`lea reg,[x+K]` 的 K 仅在随后 8 条内写进 `mov dword ptr [out],reg` 时计入；非 QI 形态类 R 强制为空）。实测分布：R 空 **863** 类 ⇒ T 视图空；R={4} **83** 类 ⇒ T 视图 {4}；R={24} **6** ⇒ {4,24}；R={1728} **1** ⇒ {4,1728}；R={36,40,44} **1**（HouseClass）⇒ {4,36,40,44}。**公式：(R 非空) ? ({4} ∪ R) : 空集，零失配。**
⇒ {4} 是「QI 至少返回一个正偏移」时附加的固定项，对 83 类与 QI 自返 +4 重合（冗余），对另外 **8** 类（6 Locomotion + AircraftClass + HouseClass）是独立附加项。
反控四条：全并集套到 863 空类 ⇒ 成立 **0**；去掉 {4} ⇒ 83 类仍成立（冗余性实证）；不先分离 QI 形态 ⇒ 1 个假阳性（`BaseClass` slot0 `0x42ee30` 普通工厂，`lea esi,[ebp+4]` 与出参无关）；v4 的 91 类与 R209「slot0 落在 12 个 QI 目标」的 91 类**完全同一**（差集 0/0）。

**二、🔴 {4} 两侧分解（90/91）.** 同类 BCA 里 `mdisp==4` 恒 **2** 条 BCD（`.?AUIUnknown@@` + 真接口）；91 类真接口名 `.?AUIRTTITypeInfo@@` **78** / `.?AUILocomotion@@` **12** / `.?AUILinkStream@@` **1**。QI 侧返回 +4 的 IID：`0x7e9ae0` **77** / `0x7ed358` **12** / `0x7e9530` **1** = **90**。**唯一不匹配 = HouseClass**（BCD 声明 IRTTITypeInfo@+4，其 QI `0x4f6830` 偏移集 {0,36,40,44} 无 4；该类 +4 视图 slot0 thunk `0x510a20` 落点即 `0x4f6830`）。

**三、🔴 律 V（305/305）.** 含 thunk 的 305 槽（303 前三槽 + HouseClass slot3/slot4）满足 `imm == mT − mV` 且 `E9 落点 == 同类内 mV 视图第 k 槽`，`mV` 必在本类视图偏移集合内。mV 分布 `{0:303, 36:2}`；槽号 `{0:101,1:101,2:101,3:1,4:1}`；(mT,mV) 七种：`(4,0)273/(24,0)18/(36,0)3/(40,0)3/(44,0)3/(1728,0)3/(40,36)2`。反控 `imm+4` 命中 **0**。⇒ 取代 R209 §2.217 五「越界 2 槽不遵循 thunk-imm==mdisp」：越界槽是 (40,36) 普通实例。

**四、🟡 mdisp→形态交叉表（260 全量零残留）.** `4→T91` / `8→{S2 75,I 3}` / `12→S1 78` / `24→T6` / `36,40,44,1728→T 各1` / `21784→S3 3`。主视图 954 表全槽 **12726**、slot≥3 **9958**；slot3 独占 **686** / 复用 **132** / 短表 **136**；slot3 ret top `ret 510 / 0x10 81 / 0x1c 60`。

**五、🟡 跨家族（§2.12 规则 D 全复算）.** #538（hy4，10 回合/2.25'，无 OVERTIME）5/5 PASS，主会话 c2 复算一致。#539（hy4，7 回合/0.98'）6/6 PASS，另给 4/24 成对 **6** 组。#540（deepseek，36 回合/**8.72' vs 8.0 ⇒ OVERTIME 如实记**）`error_max_turns`、result 空、0 条采信；其崩溃前落盘 JSON 的 G2 组（律 V）**305/305、imm+4=0、by_k 101/101/101/1/1、distinct 70** 与我方逐数一致，G3 组 **12726/9958/136/818/686/132** 一致（slot3 ret top 511 vs 510 为「无 ret」口径差，c2 复算确认 510）；G1 组 FAIL 947 是**口径错**（把 `{4}` 套全部 954 类），主会话 c20 M1 用正确判据得 954/954，故不采信 G1，但记其在 `0x4f4240`（9 类 slot0）上的发现——该函数经 c16 判为**非 QI 形态**（无 rep 前缀），其 9 类视图集合为 {0} 或 {0,21784}，与律 U 无冲突。

**六、📌 自错 6 组（0 条进结论）.** ①`c4` 取 `disasm_lite` 元组 `ins[1]` 当 mnemonic（应 `ins[2]`）；②`lea` 偏移正则只收十六进制，capstone 对 <0x10 位移输出十进制 `4` ⇒ 漏 `0x410260` 的 `lea ecx,[ebx+4]`，使我先误报「HouseClass 是唯一例外」并写进 V592 第一版（已作废重写）；③`c16` 用 `mnemonic=='repe'` 判前缀，capstone 实际给出 `'repe cmpsd'` ⇒ 185 个 QI 类全判 0；④`c15` 预设「跟进委托边会失配」，实测 **0**（6 条边指向的 QI 自身不返回正偏移，闭包对 T 类是 no-op）⇒ 该说法已从 V592 删除；⑤`c20` 反控 A/B 预期 91/10 实测 83/83，含义改为「{4} 对 83 冗余、对 8 必需」；⑥`p1` 因②两次重建 V592（旧 `735a7b5b/249150` 已删，最终 `b3327fd4/249545`）。

**七、🟡 落盘与门禁.** R14_COMMON **§2.218** CR 保持 **1081**；本段 **§1268** CR 保持 **337**；LEAD_LOCK **QS** CR 保持 **137**；STATUS_BOARD 第 210 轮 CR 保持 **0**（开局 253 行 < 260，不归档）。**FACT_INDEX V591→V592**：F29 stmt 7377→10553 B、lim 21688→22603 B（其余 55 行逐字节不变），sha `c529a08c`→**`b3327fd4`**、245454→**249545** B；指针 + facts_floors（D0/D8/D9/D10，MASTER `ba31ddc1`→`519ee33a`）+ gate_runner LEDGER 同步重钉。三门 exit 0：C19 ok(b3327fd4/249545/V592)、C20 ok、G1=G2=G3=ok。

**八、⚪ 未取得.** ①{4} 独立附加项对 8 类成立的成因（HouseClass 为唯一反例）；②12 个 QI 目标的具名 IID（仅 3 个是 OLE 标准前缀形态，其余 8 个 Westwood 私有 GUID 无外部头文件）；③主视图 9958 个 slot≥3 槽的语义归属；④S3 三表的 `0x11c7`/`0x11c8` 语义；⑤`attributes` 位义（须 win-main 动态）；⑥F23/F35 grade（两 tsv 不可读，禁预估回填）；⑦C7 三死分支、C11 十二 ID。
'''
b=backup(GOAL,'goal1268'); assert b.count(b'\r\n')==337
assert b.count('## §1268'.encode('utf-8'))==0
commit(GOAL,b+b'\n'+G1268.encode('utf-8'),b,337,'goal1268')

LQS='''## QS · R210（2026-11-28）· 律 U 定稿：视图偏移 == ({4} ∪ 本类 QI 正偏移)，954/954 零失配；律 V thunk 通用式 305/305 取代「越界槽例外」；mdisp→形态交叉表；V592

**QS1. 🔴 律 U（954/954 零失配）.** 判据三重收紧：①主视图 slot0 函数体内须有 `rep` 前缀比较指令才判 QI 形态；②`lea reg,[x+K]` 的 K 仅在随后 **8** 条内写进 `mov dword ptr [out],reg` 时计入返回偏移；③非 QI 形态类返回偏移集合强制为空。分布：R 空 **863** / {4} **83** / {24} **6** / {1728} **1** / {36,40,44} **1**。公式 **(R 非空) ? ({4} ∪ R) : 空集**，与 T 视图偏移集合逐类相等。⇒ **视图不是「按接口表逐条生成」，而是「QI 能返回哪些 this 偏移」的函数**。

**QS2. 🟡 {4} 的性质判定.** 对 **83** 类它与 QI 自返的 +4 重合（冗余），对 **8** 类（6 Locomotion + `AircraftClass` + `HouseClass`）是**独立附加项**。反控：去掉 {4} ⇒ 83 类仍成立；只留 {4} ⇒ 83 类仍成立、需走正偏移的 8 类失配；全并集套到 863 空类 ⇒ 成立 **0**。

**QS3. 🔴 {4} 两侧分解 90/91 与唯一反例.** BCD 侧真接口名 `.?AUIRTTITypeInfo@@` 78 / `.?AUILocomotion@@` 12 / `.?AUILinkStream@@` 1；QI 侧返 +4 的 IID `0x7e9ae0` 77 / `0x7ed358` 12 / `0x7e9530` 1。**HouseClass 是唯一不匹配**：BCD 声明 IRTTITypeInfo@+4、QI `0x4f6830` 偏移集 `{0,36,40,44}` 无 4，而该类 +4 视图 slot0 thunk `0x510a20` 落点就是 `0x4f6830`。成因**未取得、不外推**。

**QS4. 🔴 律 V（305/305）取代 R209 §2.217 五.** `imm == mT − mV` 且 `E9 落点 == 同类 mV 视图第 k 槽`，mV 必在本类视图偏移集合内。mV `{0:303,36:2}`；槽号 `{0:101,1:101,2:101,3:1,4:1}`；(mT,mV) 七种 `(4,0)273/(24,0)18/(36,0)3/(40,0)3/(44,0)3/(1728,0)3/(40,36)2`。反控 `imm+4`=0。⇒ **HouseClass slot3/slot4 不是「越界例外」，是 (40,36) 的普通实例**；R209 的措辞已在本轮订正。

**QS5. 🟡 mdisp→形态交叉表（260 全量零残留）.** `4→T91` / `8→{S2 75,I 3}` / `12→S1 78` / `24→T6` / `36,40,44,1728→T 各1` / `21784→S3 3` ⇒ **偏移决定形态**。附主视图全量：全槽 **12726** / slot≥3 **9958** / slot3 独占 686 / 复用 132 / 短表 136 / slot3 ret top `ret 510, 0x10 81, 0x1c 60`。

**QS6. 🟡 跨家族（§2.12 规则 D 全复算）.** #538（hy4，10 回合 / 2.25' / 无 OVERTIME）5/5 PASS。#539（hy4，7 回合 / 0.98' / 无 OVERTIME）6/6 PASS，另给 4/24 成对 **6** 组（J05/J06/J10/J11/J12/J13）。#540（deepseek，36 回合 / **8.72' vs 8.0 ⇒ [OVERTIME] 如实记**）`error_max_turns`、**result 空、0 条结论采信**；其崩溃前落盘 `_r210/audit_deepseek.json` 的 G2（律 V）**305/305、imm+4=0、by_k 101/101/101/1/1、distinct_thunks 70** 与我方逐数一致；G3（主视图普查）**12726/9958/136/818/686/132** 一致、slot3 ret top **511 vs 510** 是「无 ret」口径差（c2 复算 510）；**G1 FAIL 947 口径错**（把 `{4}` 套全部 954 类），c20 M1 正确判据 954/954，故不采信 G1，但记其在 `0x4f4240`（9 类 slot0）上的发现：该函数经 c16 判为**非 QI 形态**（无 rep 前缀），9 类视图集为 {0} 或 {0,21784}，与律 U 无冲突。

**QS7. 📌 自错 6 组（0 条进结论）.** ①`c4` 用 `disasm_lite` 元组 `ins[1]` 当 mnemonic（应 `ins[2]`）；②`lea` 正则只收十六进制，capstone 对 <0x10 位移输出十进制 `4` ⇒ 漏 `0x410260` 的 `lea ecx,[ebx+4]`，先误报「HouseClass 唯一例外」并写进 V592 第一版（已作废重建）；③`c16` 用 `mnemonic=='repe'` 判前缀，实际是 `'repe cmpsd'` ⇒ 185 个 QI 类全判 0；④`c15` 预设「跟进委托边会失配」实测 0（6 条边指向的 QI 自身不返正偏移，闭包对 T 是 no-op）⇒ 该说法已从 V592 删除；⑤`c20` 反控 A/B 预期 91/10 实测 83/83，含义改写为「{4} 对 83 冗余、对 8 必需」；⑥`p1` 两次重建 V592（旧 `735a7b5b/249150` 已删，最终 `b3327fd4/249545`）。

**QS8. 🟡 落盘与门禁.** R14_COMMON **§2.218** CR 保持 **1081**；GOAL **§1268** CR 保持 **337**；本段 **QS** CR 保持 **137**；STATUS_BOARD 第 210 轮 CR 保持 **0**（开局 **253 行 < 260**，不归档）。**FACT_INDEX V591→V592**：F29 stmt 7377→10553 B、lim 21688→22603 B（其余 55 行逐字节不变；57 行 / 5 列 / grade 与第 4 列全同），sha `c529a08c`→**`b3327fd4`**、245454→**249545** B；指针 + facts_floors（D0/D8/D9/D10，MASTER `ba31ddc1`→`519ee33a`）+ gate_runner LEDGER 同步重钉。三门 exit 0：C19 ok(b3327fd4/249545/V592)、C20 ok、G1=G2=G3=ok。

**QS9. ⚪ 未取得.** ①{4} 独立附加项对 8 类成立的成因（HouseClass 唯一反例）；②12 个 QI 目标具名 IID（仅 3 个 OLE 标准前缀形态可判）；③主视图 9958 个 slot≥3 槽语义归属；④S3 三表 `0x11c7`/`0x11c8` 语义；⑤`attributes` 位义（须 win-main）；⑥F23/F35 grade（两 tsv 不可读）；⑦C7 三死分支、C11 十二 ID。
'''
b=backup(LOCK,'lock_qs'); assert b.count(b'\r\n')==137
assert b.count(b'## QS ')==0
commit(LOCK,b+b'\n'+LQS.encode('utf-8'),b,137,'lock_qs')
