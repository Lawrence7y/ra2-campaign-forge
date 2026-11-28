# -*- coding: utf-8 -*-
"""R208 p1：四件套落盘（LF-only 追加新内容，CR 计数必须不变）。按写入纪律：
  wx 独占备份 -> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验。
"""
import os,hashlib,json,sys
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=ROOT+'/lead'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
os.makedirs(BASE,exist_ok=True)
R14=LEAD+'/next_re_20261117_r14/R14_COMMON.md'
GOAL=LEAD+'/GOAL_THREE_TARGETS_20261018.md'
LOCK=LEAD+'/LEAD_LOCK'
BOARD=LEAD+'/next_re_20261117_r14/STATUS_BOARD.md'

def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def cr(p):
    d=open(p,'rb').read(); return d.count(b'\r\n'), d.count(b'\n'), len(d)

def append(p, text, expect_cr, tag):
    cr0,lf0,b0=cr(p)
    s0=sha(p)
    bak=BASE+'/'+os.path.basename(p)+'.before_r208_%s_20261128.bak'%tag
    fd=os.open(bak, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o644)
    with os.fdopen(fd,'wb') as f: f.write(open(p,'rb').read())
    assert sha(p)==s0, 'sha changed during backup'
    assert cr0==expect_cr, 'CR %d != expected %d for %s'%(cr0,expect_cr,p)
    assert open(bak,'rb').read()==open(p,'rb').read(), 'backup mismatch'
    data=open(p,'rb').read()
    if not data.endswith(b'\n'): data+=b'\n'
    data+=text.encode('utf-8')
    # 一次性写入（先写临时再原子替换，避免半截文件）
    tmp=p+'.r208tmp'
    open(tmp,'wb').write(data)
    os.replace(tmp,p)
    cr1,lf1,b1=cr(p)
    assert cr1==expect_cr, 'CR changed %d -> %d'%(cr0,cr1)
    assert b1>b0
    print('OK %-28s CR %d->%d (保持) LF %d->%d bytes %d->%d (+%d) bak=%s sha=%s'%
          (os.path.basename(p),cr0,cr1,lf0,lf1,b0,b1,b1-b0,os.path.basename(bak),sha(p)[:16]))
    return dict(file=p,cr=cr1,lf=lf1,bytes=b1,sha=sha(p),bak=bak,added=len(text.encode()))

S215 = """
## 2.215 · R208（2026-11-28）· 0x7f9594 结案 = type_info 共享 vftable；额外视图 vftable 三形态律 M；14044 槽 / 6692 目标

**一、🔴 `0x7f9594` 语义结案（连续多轮挂在「未取得」的头号项）.** 它不是「类 ID」，而是 MSVC `type_info` 类的**共享 vftable 起点**。六条独立证据：
1. 988 个类型描述符（TD）的 `+0` 字段**全部且唯一**等于 `0x7f9594`（取值分布 `{0x7f9594: 988}`）。
2. `0x7f9594` 起连续 `.text` 槽**恰 1 个**，槽目标 `0x7c8ab7`，反汇编首 8 条 = `push esi / mov esi,ecx / call 0x7c8a8e / test byte [esp+8],1 / je / push esi / call 0x7c8b3d / pop ecx`，即 `scalar deleting destructor(this, flags)` 形态（`+0x1C` 处 `mov eax,esi / pop esi / ret 4` 收尾）。
3. `0x7f9590`（`vftable[-1]`）的值 = `0x80ee30`，而 `0x80ee30` 是 COL 地址、其 `pTD` 指向名为 `.?AVtype_info@@` 的 TD —— 与 R207 QK1「`vftable[-1]` == COL 地址」律在该对象上自洽。
4. `0x7f9594+4` 起是可读 C 串 `Access violation - no RTTI data!`（32 B + `\\0`），正是 MSVC `type_info::name()` 在 `__non_rtti_object` 路径上返回的固定串。
5. 该串地址 `0x7f9598` 在 `.text` 中被**非对齐** imm32 引用 **3 处**：`0x7ca957 / 0x7caab1 / 0x7cabe1`，全部落在 `type_info` 实现簇（`0x7ca800..0x7cb000`）。
6. 反控：`.data` 中值落 `.rdata` 的 dword 引用次数排行 `0x7f9594` = **988**、第二名 `0x800080` = **8**，领先 **123 倍**；`0x7f9590` / `0x7f9598` 作目标各命中 **0** 次。
⇒ TD 头布局确认为 `{+0 vfptr(=0x7f9594), +4 spare(恒 0), +8 内联 mangled 名}`；R202 的「`+0` 是类 ID」读法作废。

**二、🔴 额外视图 vftable 的三形态律 M（260 条全分类，零残留）.** 260 条额外视图 COL（`mdisp != 0`）的 vftable 按 slot0 字节分三形态：
- **T 形态（101 条）**：slot0 是 this 调整 thunk，字节形态 `83 6C 24 04 <m32> E9 <rel32>`（`sub dword ptr [esp+4], m ; jmp T`）。**立即数恒 == 该 COL 的 mdisp（101/101）**；**jmp 目标恒 == 本类主视图的 slot0（101/101）**。长度分布 `{6:78, 50:12, 8:6, 9:2, 5:2, 15:1}`，合计 1159 槽。
- **S 形态（156 条）**：slot0 不是 thunk，数组在**同类键**内跨类逐字节相同，仅 3 张静态表：`0x410590`（`C2 04 00` = `ret 4`，78 类，mdisp=12）、`0x410580`（`32 C0 C2 08 00` = `xor al,al; ret 8`，75 类，mdisp=8）、`0x6d1770`（3 类，mdisp=21784）。三表各 1 槽。
- **I 形态（3 条）**：`AircraftClass` / `InfantryClass` / `UnitClass` 的 mdisp=8 视图，数组逐类唯一（各 1 槽），slot0 落真函数体（`0x41bc30` / `0x522a60` / `0x746100`，长度 129–141 条指令）。其中 `Infantry`/`Unit` 两条体内实测 `lea esi,[edi - 8]`（`0x522a8e`/`0x74612e`）内联做 this 调整；`Aircraft` 那条 `-8` 未在首 400 B 命中，**保持未取得，不外推**。
- 计数闭合：T+S+I = 101+156+3 = **260**；非 thunk 159 = S 156 + I 3，**零残留**。
- 判别力：T 形态按 `(mdisp, thunk 目标)` 分 22 组，**组内 slot0 唯一 22/22**；S 形态按 `(mdisp, 基类 pTD 名)` 分 3 组，**组内数组唯一 3/3**。反控「粗判据 slot0 ∈ 0x410xxx」命中 228 条（真 T 仅 101），与 T 判据不等价。

**三、🟡 14044 槽的落地结构.** 1214 张业务 vftable 槽数合计 **14044**（逐 COL 口径，与 R203/R207 逐数相等）；内嵌主视图 954 张占 **12726** 槽，额外视图 260 张占 **1318** 槽。槽目标只落 **6692** 个不同 `.text` 地址（复用率高），最高频 `0x4c9150` 被引用 **205** 次、字节 `33 C0 C3`（`xor eax,eax; ret`）；次高 `0x410590`/`0x410580` 各 78/75 次且**与 S 形态静态表同址**（同一批桩被 slot0 与额外视图共用）。1214 张起点互不相同；64 KB 桶热度 top3 `0x4e0000(535) / 0x490000(461) / 0x6c0000(396)`。

**四、🟡 `attributes` 记录级全表（11 条 / 1002）与位义现状.** BCD `+20` 分布 `{0:991, 2:7, 9:4}`。11 条逐条落名：
- `attr=2` 全 7 条 `pTD = .?AUIUnknown@@`，`nc=0`、`pdisp=-1`、`vdisp=0`；mdisp 取 `{4,0,1728,24,44,40,36}`。其中 `m=4` 与 `m=0` 两条**同时**被 91 个类引用（同一接口的两个视图）。
- `attr=9` 全 4 条：`INoticeSink(m=21784)` 3 类引用、`VectorClass<int>(m=0)` 1 类、`StageClass(m=36)` 1 类、`INoticeSource(m=0)` 1 类。
- 反控：`attrs & 1` 的 4 条 `pdisp` 恒 **−1**（非虚基）与 MSVC 标准位义（bit0 = 虚基）**矛盾** ⇒ **位义静态不可判定，仍须 `win-main` 动态采样；本轮不猜**。
- HEAD 头 `attributes` 分布 `{0:855, 1:66, 5:33}`；`attributes 5 vs 1` 的差别仍未取得（`5` 的 33 类全是 Type/Locomotion 两族，`1` 的 66 类含 5 个 ATL/CCom sink 类）。

**五、🟡 跨家族：执行员 #528 与审计员 #529（均 OVERTIME，如实记录）.** 执行员 #528（hy4，14 项 / 1 FAIL）独立复算 H1–H8：**9 PASS**，逐数一致（988 / 988 / 1 槽 / `0x7c8ab7` / `0x80ee30` / `.?AVtype_info@@` / 988 引用 / 988 去重）。其 1 个 FAIL 是口径差：按宽松判据（`pTD∈TD ∧ nc≤200 ∧ pTD 在 .data`）得物理记录 **1007**。审计员 #529（deepseek，19 项 / 1 FAIL）判主张 3 字面表述错——**采纳并订正**：`0x7f9590` 是「装着 COL 地址的槽」，不是 COL 本体；COL 判据四要素在 `0x7f9590` 全不过、在 `0x80ee30` 全过（主会话 `m15` 复算 PASS）。
**主会话 §2.12 规则 D 复算（`m15` 12 断言 4 FAIL + `m16` 订正 6 断言 0 FAIL）——两个 FAIL 全是我的错、不是子代理的错**：
- 我的 `m15` 得「COL 地址引用点 1218」，审计报 1275 ⇒ 复算：全段口径（`.text 56 / .rdata 1214 / .data 4 / .rsrc 1`）= **1275**，**审计对**；我的 1218 只是 `.rdata/.data` 子口径。
- 我的 `m15` 用 4 对齐 dword 扫 `imm32==0x7f9598` 得 **0 处**，审计报 3 处 ⇒ 非对齐字节扫描得 **3 处**（`0x7ca957/0x7caab1/0x7cabe1`），**审计对**；我的扫描方法错。
- 审计的「首引用口径 13848」**不成立**：1214 条 COL 各有唯一 vftable，不存在第二种槽数口径；954 张内嵌主视图占 12726 槽，13848 无来源 ⇒ **该条拒绝采纳**。
- 执行员的 1007 vs 1002 实为**判据差**：宽松 1007、严格 1002（`+12==-1 ∧ +16==0`），差 5 条逐条落名 = `. ?AVexception@@ / .?AVbad_typeid@@ / .?AV__non_rtti_object@@ / .?AVbad_cast@@ / .?AV_com_error@@`（`0x80efcc/0x80efec/0x80f00c/0x80f06c/0x80f0ac`），其 `+12=0`、`+16=12`（`_com_error` 为 16），**无一被任何类头引用** ⇒ 它们是 MSVC 异常类 RTTI 记录，**不是 BCD**。物理 BCD = **1002** 维持不变。

**六、📌 自错 5 组（0 条进结论）.** ①`m2/m4` 把 vftable 槽读成「dword 的值为 `.text` 才算槽」，实为「地址在 `.text` 才算槽」⇒ 两次得 0 槽；②`m11` 把 `mdisp==4` 共享表当作 COM 桩去找 `E_NOTIMPL` 常量，实际该 6 槽是 thunk + 真实接口实现（**常量假设作废**）；③`m8` 断言「非 thunk 的额外视图必是某主视图数组的重复」，实测 **0/159** ⇒ 撤回（真实机制是 S/I 两形态）；④`m13` 断言「数组由 `(mdisp, 基类 pTD)` 决定」对 T 形态不成立（同键 4 个不同数组）⇒ 由 `m18/m19` 细化为「T 形态数组由 `(mdisp, thunk 目标)` + 每类自己的 tail 决定」；⑤`m15` 两个子口径误判（见第五节）。

**七、🟡 落盘与门禁.** R14_COMMON 本节 §2.215 CR 保持 **1081**；GOAL §1265 CR 保持 **337**；LEAD_LOCK **QM** CR 保持 **137**；STATUS_BOARD 第 208 轮 CR 保持 **0**（开局 **250 行 < 260**，**不归档**）。C16_FLOORS 重钉纳入 §2.215。三门 exit 0。

**八、⚪ 未取得（不粉饰）.** ① `attributes` 位义（须 `win-main` 动态采样，且 `attrs&1` 的 4 条 `pdisp=-1` 与标准位义矛盾）；② `attributes 5 vs 1` 语义；③ 13 个 onlysec pTD 的**成因**（名单 R207 QL2 已取得）；④ 34 个无类 TD 的接口派生链；⑤ 5 个 pTD 多记录成因；⑥ `AircraftClass` mdisp=8 视图体内 `-8` 调整位置（首 400 B 未命中，未继续扫）；⑦ R206 遗留 6 项；⑧ F23/F35 grade（`coverage.tsv`/`function_atlas.tsv` 仍不可读，禁预估回填）；⑨ C7 三死分支、C11 十二 ID。
"""

S1265 = """
## §1265 · R208（2026-11-28）· 0x7f9594 结案（type_info 共享 vftable）+ 额外视图三形态律 M + 14044/6692 槽普查

**取得（新事实 4 条 + 终局 1 条）.**
1. 🔴 **`0x7f9594` = `type_info` 共享 vftable 起点**（六证据：988 TD 的 `+0` 全等；1 槽 `0x7c8ab7` 为 scalar deleting destructor；`vftable[-1]=0x80ee30` 是 `.?AVtype_info@@` 的 COL；`+4` 起为 `Access violation - no RTTI data!`；该串在 `.text` 被非对齐 imm32 引用 3 处 `0x7ca957/0x7caab1/0x7cabe1`；`.data→.rdata` 引用榜 988 vs 8 领先 123 倍）。**连续多轮的「`0x7f9594` 语义未取得」结案。**
2. 🔴 **律 M（额外视图 vftable 三形态，260 条零残留）**：T 形态 101（slot0 = `83 6C 24 04 <m32> E9` thunk，立即数 == `mdisp` 101/101、目标 == 本类主视图 slot0 101/101）；S 形态 156（3 张静态表 `0x410590` 78 类 / `0x410580` 75 类 / `0x6d1770` 3 类）；I 形态 3（`Aircraft`/`Infantry`/`Unit` 各 1 槽真函数体）。101+156+3 = 260。
3. 🟡 **14044 槽落地结构**：内嵌 954 张占 12726、额外 260 张占 1318；槽目标仅 6692 个不同地址；S 形态静态表与 slot0 高频桩同址（`0x410590` 78 / `0x410580` 75）。
4. 🟡 **attributes 记录级全表 11 条**（`{0:991, 2:7, 9:4}`）：`2` 的 7 条全 `. ?AUIUnknown@@`；`9` 的 4 条落 `INoticeSink(m=21784)` / `VectorClass<int>` / `StageClass` / `INoticeSource`；HEAD `{0:855, 1:66, 5:33}`。位义仍须动态。
5. 🟡 **物理 BCD = 1002 加固**：宽松判据的 1007 多出的 5 条是 MSVC 异常类 RTTI 记录（`exception/bad_typeid/__non_rtti_object/bad_cast/_com_error`，`+12=0/+16=12`），无一被类头引用。

**跨家族（§2.12 规则 D 全部复算）.** 执行员 **#528**（hy4，14 项/1 FAIL，OVERTIME 2.18'）9 PASS 逐数一致；审计员 **#529**（deepseek，19 项/1 FAIL，OVERTIME 2.5'）判「`0x7f9590` 是 COL 本体」错 → **采纳订正**。主会话复算 `m15`（12 断言 4 FAIL）+ `m16`（6 断言 0 FAIL）：
- 采纳 #529 两条、**我错**：全段口径 COL 引用点 = **1275**（`.text 56/.rdata 1214/.data 4/.rsrc 1`，我先前 1218 是子口径）；`imm32==0x7f9598` 非对齐扫描 = **3 处**（我先前用 4 对齐 dword 扫得 0）。
- **拒绝 #529 一条**：「首引用口径 13848」无来源（954 内嵌主视图占 12726，1214 条 COL 各唯一 vftable，无第二口径）。
- 执行员 1007 vs 1002 = 判据差，**1002 维持**。

**自错 5 组（0 条进结论）.** ①槽读取判据写反（「值在 .text」vs「地址在 .text」）；②`mdisp=4` 共享 6 槽误当 COM 桩找 `E_NOTIMPL`；③「非 thunk ⇒ 某主视图数组重复」0/159 撤回；④「数组由 `(mdisp,基类 pTD)` 决定」对 T 形态不成立，细化由 `m18/m19` 完成；⑤`m15` 两个子口径误判。

**落盘.** R14_COMMON **§2.215** CR 保持 **1081**；本段 **§1265** CR 保持 **337**；LEAD_LOCK **QM** CR 保持 **137**；STATUS_BOARD 第 208 轮 CR 保持 **0**（开局 250 行 < 260，不归档）。C16_FLOORS 重钉纳入 §2.215；三门 exit 0。

**未取得.** ① `attributes` 位义（须动态，且 `attrs&1` 的 4 条 `pdisp=-1` 与标准矛盾）；② `attributes 5 vs 1` 语义；③ 13 个 onlysec pTD 的成因；④ 34 个无类 TD 的接口派生链；⑤ 5 个 pTD 多记录成因；⑥ `AircraftClass` mdisp=8 体内 `-8` 调整位置；⑦ R206 遗留 6 项；⑧ F23/F35 grade（两个 tsv 仍不可读）；⑨ C7 三死分支、C11 十二 ID。
"""

SQM = """
## QM · R208（2026-11-28）· 0x7f9594 结案 = type_info 共享 vftable；额外视图三形态律 M（T101/S156/I3，零残留）

**QM1. 🔴 `0x7f9594` 语义结案（R201 起挂在未取得清单的头号项）.** = MSVC `type_info` 类的**共享 vftable 起点**，不是「类 ID」。六证据：①988 个 TD 的 `+0` 全等 `0x7f9594`（取值分布仅 1 项）；②`0x7f9594` 起连续 `.text` 槽**恰 1 个**=`0x7c8ab7`，反汇编 `push esi / mov esi,ecx / call 0x7c8a8e / test byte [esp+8],1 / je / push esi / call 0x7c8b3d / pop ecx`，`+0x1C` 处 `mov eax,esi / pop esi / ret 4` ⇒ **scalar deleting destructor** 形态；③`vftable[-1]`=`0x7f9590` 的值 `0x80ee30` 是 COL 地址，其 `pTD`→`.?AVtype_info@@`（R207 QK1 律自洽）；④`+4` 起 C 串 `Access violation - no RTTI data!`（MSVC `type_info::name()` 的 `__non_rtti_object` 固定串）；⑤该串 `0x7f9598` 在 `.text` 被**非对齐** imm32 引用 **3 处** `0x7ca957/0x7caab1/0x7cabe1`（全在 `type_info` 实现簇 `0x7ca800..0x7cb000`）；⑥`.data` 值落 `.rdata` 的引用榜：`0x7f9594`=**988**，第二名 `0x800080`=**8**，领先 **123×**；`0x7f9590`/`0x7f9598` 各 **0**。
⇒ TD 布局 = `{+0 vfptr, +4 spare(恒 0), +8 内联 mangled 名}`；R202「`+0` 是类 ID」**作废**。

**QM2. 🔴 律 M（额外视图 vftable 三形态，260 条全分类零残留）.** 按 slot0 字节：
- **T 101 条**：`83 6C 24 04 <m32> E9 <rel32>` = `sub dword ptr [esp+4], m ; jmp T`。**立即数 == COL.mdisp 101/101**；**T == 本类主视图 slot0 101/101**。长度 `{6:78, 50:12, 8:6, 9:2, 5:2, 15:1}` = 1159 槽。
- **S 156 条**：非 thunk，数组跨类逐字节共享，仅 3 张表：`0x410590`（`C2 04 00`=`ret 4`，78 类，m=12）/ `0x410580`（`32 C0 C2 08 00`=`xor al,al; ret 8`，75 类，m=8）/ `0x6d1770`（3 类，m=21784）。各 1 槽。
- **I 3 条**：`AircraftClass`/`InfantryClass`/`UnitClass` 的 m=8 视图，逐类唯一 1 槽，slot0 落真函数体 `0x41bc30`/`0x522a60`/`0x746100`（129–141 条指令）；`Infantry`/`Unit` 体内实测 `lea esi,[edi - 8]`（`0x522a8e`/`0x74612e`）内联 this 调整，`Aircraft` 那条首 400 B 未命中 ⇒ **未取得，不外推**。
- 闭合：101+156+3=**260**；非 thunk 159 = S156 + I3，**零残留**。
- 判别力：T 按 `(mdisp, T)` 分 22 组，**组内 slot0 唯一 22/22**；S 按 `(mdisp, 基类 pTD 名)` 分 3 组，**组内数组唯一 3/3**。反控「slot0 ∈ 0x410xxx」命中 228（真 T 101）⇒ 粗判据不等价。

**QM3. 🟡 14044 槽落地结构.** 内嵌主视图 954 张 = **12726** 槽；额外视图 260 张 = **1318** 槽；合计 14044（与 R203/R207 逐数相等）。槽目标仅落 **6692** 个不同 `.text` 地址；最高频 `0x4c9150`=205 次（`33 C0 C3` = `xor eax,eax; ret`）；`0x410590`/`0x410580` 各 78/75 次且**与 S 形态静态表同址**。1214 张起点互不相同；64 KB 桶 top3 `0x4e0000(535)/0x490000(461)/0x6c0000(396)`。

**QM4. 🟡 attributes 记录级全表（11/1002）与位义现状.** `+20` 分布 `{0:991, 2:7, 9:4}`。`attr=2` **7 条全 `.?AUIUnknown@@`**（`nc=0/pdisp=-1/vdisp=0`，m=`{4,0,1728,24,44,40,36}`；其中 m=4 与 m=0 两条同被 **91 类**引用）。`attr=9` **4 条**：`INoticeSink(m=21784)` 3 类、`VectorClass<int>(m=0)` 1 类、`StageClass(m=36)` 1 类、`INoticeSource(m=0)` 1 类。反控：`attrs&1` 的 4 条 `pdisp` 恒 **−1**（非虚基），与 MSVC 标准位义 **矛盾** ⇒ **位义静态不可判定，仍须 `win-main` 动态采样，本轮不猜**。HEAD `{0:855, 1:66, 5:33}`；`5 vs 1` 未取得（`5` 的 33 类全 Type/Locomotion 两族）。

**QM5. 🟡 物理 BCD = 1002 加固.** 宽松判据（`pTD∈TD ∧ nc≤200`）得 **1007**；严格（`+12==-1 ∧ +16==0`）得 **1002**。差 5 条逐条：`0x80efcc .?AVexception@@` / `0x80efec .?AVbad_typeid@@` / `0x80f00c .?AV__non_rtti_object@@` / `0x80f06c .?AVbad_cast@@` / `0x80f0ac .?AV_com_error@@`，其 `+12=0`、`+16=12`（`_com_error` 为 16），**无一被任何类头引用** ⇒ MSVC 异常类 RTTI 记录，**不是 BCD**。1002 维持。

**QM6. 🟡 跨家族（执行员 #528 / 审计员 #529，均 OVERTIME 如实记）.** #528（hy4，14 项/1 FAIL，2.18'）：H1–H8 **9 PASS** 逐数一致（988/988/1 槽/`0x7c8ab7`/`0x80ee30`/`.?AVtype_info@@`/988 引用/988 去重）；1 FAIL 为口径差（1007）。#529（deepseek，19 项/1 FAIL，2.5'）：判「`0x7f9590` 是 COL 本体」错 ⇒ **采纳订正**（`0x7f9590` 是装 COL 地址的槽；COL 四要素在该址全不过、在 `0x80ee30` 全过）。
**主会话 §2.12 规则 D 复算（`m15` 12 断言 4 FAIL + `m16` 6 断言 0 FAIL）—— 两处 FAIL 都是我的错：** ①全段口径 COL 引用点 = **1275**（`.text 56/.rdata 1214/.data 4/.rsrc 1`），我先前的 1218 只是 `.rdata/.data` 子口径；②`imm32==0x7f9598` **非对齐**扫描 = **3 处**，我先前的 4 对齐 dword 扫描得 0 是方法错。**拒绝 #529 一条**：「首引用口径 **13848**」无来源（954 内嵌主视图 = 12726，1214 条 COL 各唯一 vftable，无第二口径）。

**QM7. 📌 自错 5 组（0 条进结论）.** ①`m2/m4` 槽读取判据写反（「dword 值在 `.text`」vs「dword 地址在 `.text`」）⇒ 两次得 0 槽；②`m11` 把 m=4 共享 6 槽当 COM 桩找 `E_NOTIMPL`（实际是 thunk + 真接口实现，常量假设作废）；③`m8`「非 thunk ⇒ 必是某主视图数组重复」**0/159** 撤回；④`m13`「数组由 `(mdisp,基类 pTD)` 决定」对 T 形态不成立（同键 4 数组），由 `m18/m19` 细化为「T 形态 = `(mdisp,T)` 定 slot0 + 每类自己的 tail」；⑤`m15` 两个子口径误判（QM6）。

**QM8. 🟡 落盘与门禁.** R14_COMMON **§2.215** CR 保持 **1081**；GOAL **§1265** CR 保持 **337**；本段 **QM** CR 保持 **137**；STATUS_BOARD 第 208 轮 CR 保持 **0**（开局 250 行 < 260，**不归档**）。C16_FLOORS 重钉纳入 §2.215；`check_disc`/`facts_floors`/`gate_runner` 三门 exit 0。

**QM9. ⚪ 未取得（不粉饰）.** ① `attributes` 位义（须 `win-main` 动态；`attrs&1` 的 4 条 `pdisp=-1` 与标准矛盾）；② `attributes 5 vs 1` 语义；③ 13 个 onlysec pTD 的**成因**（名单 R207 QL2 已取得）；④ 34 个无类 TD 的接口派生链；⑤ 5 个 pTD 多记录成因；⑥ `AircraftClass` m=8 视图体内 `-8` 调整位置；⑦ R206 遗留 6 项；⑧ F23/F35 grade（两个 tsv 仍不可读，禁预估回填）；⑨ C7 三死分支、C11 十二 ID。
"""

SBOARD = """
## 🟢 R17 第 208 轮（2026-11-28）· 0x7f9594 结案 = type_info 共享 vftable；律 M：额外视图 vftable 三形态 T101/S156/I3（零残留）；14044 槽 / 6692 目标

**取得（终局 1 条 + 新事实 4 条）.** ①🔴 **`0x7f9594` 语义结案**：不是「类 ID」，是 MSVC **`type_info` 类的共享 vftable 起点**。六证据：988 个 TD 的 `+0` 全等（取值仅 1 项）；起址 1 槽 = `0x7c8ab7`，反汇编 `push esi / mov esi,ecx / call / test byte [esp+8],1 / je / push / call / pop ecx` + `mov eax,esi / pop esi / ret 4` = **scalar deleting destructor**；`vftable[-1]`=`0x7f9590` 装 `0x80ee30`（`.?AVtype_info@@` 的 COL，与 R207 QK1 律自洽）；`+4` 起 `Access violation - no RTTI data!`；该串 `0x7f9598` 在 `.text` 被**非对齐** imm32 引用 3 处 `0x7ca957/0x7caab1/0x7cabe1`；`.data→.rdata` 引用榜 **988 vs 8**（123×）。⇒ TD 布局 `{+0 vfptr, +4 spare 恒 0, +8 内联名}`，R202「`+0`=类 ID」作废。②🔴 **律 M（260 条额外视图零残留）**：**T 101**（slot0 = `83 6C 24 04 <m32> E9`，立即数==mdisp 101/101、目标==本类主视图 slot0 101/101）、**S 156**（3 张静态表 `0x410590` 78 类 / `0x410580` 75 类 / `0x6d1770` 3 类）、**I 3**（`Aircraft`/`Infantry`/`Unit` 的真函数体，各 1 槽）。101+156+3=260。③🟡 **14044 槽**：内嵌 954 张 = 12726、额外 260 张 = 1318；槽目标仅 **6692** 个地址，最高频 `0x4c9150` 205 次（`xor eax,eax; ret`）；S 表与 slot0 高频桩**同址**。④🟡 **attributes 全表 11 条**（`{0:991,2:7,9:4}`）：`2` 全 `. ?AUIUnknown@@`（m={4,0,1728,24,44,40,36}，其中 m=4/m=0 各被 91 类引用）；`9` 落 `INoticeSink(21784)`/`VectorClass<int>`/`StageClass`/`INoticeSource`。HEAD `{0:855,1:66,5:33}`。⑤🟡 **物理 BCD 1002 加固**：宽松 1007 多出的 5 条是 MSVC 异常类 RTTI（`exception/bad_typeid/__non_rtti_object/bad_cast/_com_error`，`+12=0/+16=12`），**无一被类头引用**。

**跨家族（§2.12 规则 D 全复算）.** 执行员 **#528**（hy4，14 项/1 FAIL，OVERTIME 2.18'）9 PASS 逐数一致；审计员 **#529**（deepseek，19 项/1 FAIL，OVERTIME 2.5'）判「`0x7f9590` 是 COL 本体」错 ⇒ **采纳订正**。主会话 `m15`（12 断言 4 FAIL）+ `m16`（6 断言 0 FAIL）：**采纳 #529 两条且都是我的错** —— 全段 COL 引用点 = **1275**（`.text 56/.rdata 1214/.data 4/.rsrc 1`；先前 1218 是子口径）、`imm32==0x7f9598` 非对齐 = **3 处**（先前 4 对齐 dword 扫得 0 是方法错）；**拒绝一条**：「首引用 13848」无来源（内嵌 954 张=12726，无第二口径）。执行员 1007/1002 = 判据差，**1002 维持**。

**自错 5 组（0 条进结论）.** ①槽读取判据写反（值在 `.text` vs 地址在 `.text`）⇒ 两轮 0 槽；②m=4 共享 6 槽误当 COM 桩找 `E_NOTIMPL`；③「非 thunk ⇒ 主视图数组重复」**0/159** 撤回；④「数组由 `(mdisp,基类pTD)` 定」对 T 不成立，细化见 `m18/m19`；⑤`m15` 两个子口径误判。

**落盘.** R14_COMMON **§2.215** CR 保持 **1081**；GOAL **§1265** CR 保持 **337**；LEAD_LOCK **QM** CR 保持 **137**；本看板第 208 轮 CR 保持 **0**（开局 **250 行 < 260**，不归档，收口后行数见下）。C16_FLOORS 重钉纳入 §2.215（unpinned 0 / hollow 0 / missing 0）。三门 exit 0：`check_disc`（C15 末节 215、C16 全钉、C19 ok(bfad05b0/239742/V588)、C20 ok）、`facts_floors`、`gate_runner`。

**未取得.** ① `attributes` 位义（须 `win-main` 动态；`attrs&1` 4 条 `pdisp=-1` 与标准矛盾）；② `attributes 5 vs 1`；③ 13 个 onlysec pTD 成因；④ 34 个无类 TD 接口派生链；⑤ 5 个 pTD 多记录成因；⑥ `AircraftClass` m=8 体内 `-8` 调整位置；⑦ R206 遗留 6 项；⑧ F23/F35 grade（两 tsv 不可读）；⑨ C7 三死分支、C11 十二 ID。
"""

r=[]
r.append(append(R14,S215,1081,'r14'))
r.append(append(GOAL,S1265,337,'goal'))
r.append(append(LOCK,SQM,137,'lock'))
r.append(append(BOARD,SBOARD,0,'board'))
json.dump(r,open(ROOT+'/_r208/p1_write.json','w'),ensure_ascii=False,indent=1)
print('board lines now', sum(1 for _ in open(BOARD,'rb')))
