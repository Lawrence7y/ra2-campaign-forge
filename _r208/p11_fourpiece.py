# -*- coding: utf-8 -*-
"""R208 p11（收口期）：四件套。
  R14_COMMON §2.216（CR 保持 1081，LF-only 追加）
  GOAL §1266（CR 保持 337）
  LEAD_LOCK QN（CR 保持 137）
  STATUS_BOARD：先归档最早 2 段到 BOARD_ARCHIVE（归档 CR 保持 2952），再给第 208 轮补记，总行 <= 300
  C16_FLOORS 纳入 §2.216（unpinned 0）
每处写入：wx 独占备份 -> 断言旧 sha/CR -> 一次写入 -> 回读校验。
"""
import os,re,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=ROOT+'/lead'; TIER=LEAD+'/next_re_20261117_r14'; BASE=LEAD+'/R17_LEAD_BASELINE'
R14=TIER+'/R14_COMMON.md'; GOAL=LEAD+'/GOAL_THREE_TARGETS_20261018.md'
LOCK=LEAD+'/LEAD_LOCK'; BOARD=TIER+'/STATUS_BOARD.md'; ARCH=TIER+'/BOARD_ARCHIVE.md'
CD=TIER+'/check_disc.py'

def backup(path,tag):
    b=open(path,'rb').read()
    bak=BASE+'/'+os.path.basename(path)+'.before_r208_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    return b,bak
def commit(path,nb,ob,exp_cr,tag):
    assert nb.count(b'\r\n')==exp_cr,(tag,nb.count(b'\r\n'),exp_cr)
    tmp=path+'.r208tmp'; open(tmp,'wb').write(nb); os.replace(tmp,path)
    d=open(path,'rb').read()
    assert d==nb
    print('OK %-34s %d -> %d B  CR %d'%(os.path.basename(path),len(ob),len(d),d.count(b'\r\n')))

# ---------- 1. R14_COMMON §2.216 ----------
S216 = '''## 2.216 · R208 收口（2026-11-28）· T 形态 thunk 双编码订正（83 为主 / 81 兜底）；AircraftClass −8 调整收官；FACT_INDEX V589→V590

**一、🔴 订正：§2.215 / QM2 的「T 形态统一为 `83 6C 24 04 <imm8> E9`」表述过强.** 本轮把 thunk 字节判据从「首 4 字节 == 83 6C 24 04」放宽为「`83` 或 `81` + `6C 24 04` + 立即数 + `E9 rel32`」后实测：额外视图 vftable 的 slot0 为 this 调整 thunk 者仍 **101** 条，但编码**不是一种**：

- **100 条** `83 6C 24 04 <imm8> E9 <rel32>`，其 mdisp 取值集合恰 **{4, 24, 36, 40, 44}**（全部装得下 imm8）。
- **1 条** `81 6C 24 04 <imm32> E9 <rel32>`：COL **0x7fb310** / `.?AVAircraftClass@@` / mdisp = **1728**（0x6C0）/ vftable **0x7e2250** / slot0 **0x41c670** / 字节 `81 6C 24 04 C0 06 00 00 E9 13 7C FF FF` / E9 目标 **0x414290**。**mdisp=1728 超出 imm8 有符号范围，编译器改用 imm32 编码**——这是编码选择的直接后果，不是新形态。
- 两条不变量在放宽判据后**仍逐条成立**：立即数 == 该 COL 的 mdisp **101/101**（100/100 + 1/1）；E9 目标 == 本类主视图 slot0 **101/101**。

**二、🟡 thunk 级常量性（本轮新证，若不做会把等式当成逐类性质）.** 100 条 A83 只映射到 **21** 个不同 thunk 地址（`0x4105e0` 单址供 75 个 COL 复用）；每个 thunk 地址的立即数**唯一**（21/21），且共享同一 thunk 的 COL 其 mdisp 也唯一（组内零冲突）。⇒ 「立即数 == mdisp」在本镜像是**thunk 级常量**的推论，不是每个 COL 独立决定；若将来出现共享 thunk 而 mdisp 不同的 COL，该等式会失效。

**三、🟡 分母口径警告（实测，防混用）.** `.text` 全域字节锚点计数 `83 6C 24 04` = **67** 处、`81 6C 24 04` = **3** 处，与「额外视图 slot0」口径的 100 / 1 **不可混用**。81 的另两处 **0x41c680 / 0x41c690** 不是任何 COL 的 slot0，而是同一 vftable **0x7e2250** 的 slot1/slot2——该表前三槽正是 `0x41c670 / 0x41c680 / 0x41c690` **三连 81 thunk**（第四槽 0x41b6a0）。主视图 954 条里 **0 条**以 A83/B81 thunk 作 slot0；其中 2 条以 `8B 44 24 04` 开头（`CD` → 0x4790e0 体首 `mov eax,[esp+4] ; cmp eax,0xFFFFFFFE`；`ProgressScreenClass` → 0x643e80 体首 `mov eax,[esp+4] ; mov [ecx+4],eax ; ret 4`），是**真函数体不是 thunk**，不得计入 T 形态。

**四、🔴 取得 QM9 ⑥：AircraftClass m=8 视图体内 −8 调整的位置.** 上一轮只搜 `lea reg,[reg-imm]` 因而 0 命中；把判据放宽为「操作数含 −m 常量负偏移」后三条全中，且**编码并不统一**：
- `AircraftClass`（0x41bc30 入口，401 B / 135 条指令）：**`add esi, -8`** @ **0x41bc8f**（入口 +0x5F）。
- `InfantryClass`（0x522a60，112 B / 39 条指令）：`lea esi,[edi - 8]` @ **0x522a8e**（入口 +0x2E）。
- `UnitClass`（0x746100，112 B / 39 条指令）：`lea esi,[edi - 8]` @ **0x74612e**（入口 +0x2E）。
- 三条函数体**互不相同**：Infantry 与 Unit 之间也差 **10** 处，分型 = 栈帧 2（`sub/add esp,0x10` vs `0x18`）/ 参数偏移 1（`[esp+0x20]` vs `[esp+0x28]`）/ 字段偏移 1（`[edi+0x6b8]` vs `[edi+0x6bc]`）/ 内部跳转 6，**无一处落在 this 调整位**。反控：Aircraft 入口 +0x400 起的 512 B 窗口内 −8 命中 **0**。

**五、📌 自错 5 组（0 条进结论）.** ①`v1` 扫 TD 时给类名串多加了「含 NUL」条件 ⇒ 0 条，去掉后 988；②`v1` 的 thunk 判据把 **slot0 地址**当函数地址读（应为 `dw(slot0)`）⇒ 得 0 条 T；③`v1` 的 `.data` 引用榜未排除值 0 ⇒ 第一名是 0（8380 次），排除后 0x7f9594=988 / 0x800080=8；④`v2` 只搜 `lea` 漏掉 `add esi,-8`（正是 QM9 ⑥ 本轮要收的项）；⑤`v3`/`v4` 把 `81 6C 24 04 <imm32> E9 rel32` 的 E9 基址算成 `va+9`，正确是 `va+13`（81 编码全长 8 B，非 4 B）——错算落点 0x41428c 处是 `90 90 90 90` 填充，可一眼辨伪。

**六、🟡 跨家族（§2.12 规则 D 全部主会话复算）.** 执行员 **#531**（hy4，1 回合 / **7.47'** vs 预算 5.0 ⇒ **[OVERTIME]** 如实记）：自报 15/15 PASS，产出 `_r208/x1_tform.json`（含 101 条 A/B 明细、shape_F 三条 I 形态、`mdisp_mismatch` 空、`jmp_fail` 空）；其自述曾起过一个用**旧引用判据**（要求引用格 +4 本身落 .text）的后台探测得 `vftable=None`，已声明作废、不参与结论。审计员 **#532**（deepseek，26 回合 / 3.57' / 无 OVERTIME）：9 断言 **1 FAIL**，FAIL 正是「统一 83」这一表述，并给出订正句（本轮全采纳）。它另提两条加强，主会话 `v5` 逐条实测均成立：①「立即数 == mdisp」实为 thunk 级常量（21 个 thunk 各一 imm，组内 mdisp 唯一）；②锚点口径 83=67 / 81=3 与 slot0 口径 100/1 分母不同，只有后者能支撑 101。**主会话复算 `v1` 13 断言 0 FAIL / `v2` 11 / `v3` 12 / `v4` 7 / `v5` 12，合计 55 断言 0 FAIL**；两子代理结论无一未经复算即入结论。

**七、🟡 FACT_INDEX 升版 V589→V590.** 把「T 形态双编码 + thunk 级常量性 + 分母口径警告 + I 形态三条 −8 调整」写入 **F29**（只增长：stmt 3435→5343 B；其余 55 行逐字节不变；57 行 / F01..F56 / 5 列 / grade 与第 4 列全同）。sha `89bb71ba`→**`e49a3edd`**，240722→**242630** B。指针、facts_floors（EXPECT_CUR/CUR_SHA256/TOTAL_BYTES/MASTER_SHA256 `96f504e7`→`940c94c0`）、gate_runner LEDGER 同步重钉。

**八、🟡 落盘与门禁.** 本段 **§2.216** CR 保持 **1081**；GOAL **§1266** CR 保持 **337**；LEAD_LOCK **QN** CR 保持 **137**；STATUS_BOARD 第 208 轮 CR 保持 **0**（开局 262 行 >= 260 ⇒ 先归档最早 2 段至 BOARD_ARCHIVE，归档 CR 保持 **2952**）。C16_FLOORS 纳入 §2.216（unpinned 0 / hollow 0 / missing 0）。三门 exit 0：`check_disc`（C15 末节 216、C16 208 节全钉、C19 ok(e49a3edd/242630/V590)、C20 ok）、`facts_floors`（D8 242630、D9/D10 一致）、`gate_runner`（G1=G2=G3=ok）。

**九、⚪ 未取得（不粉饰）.** ① `attributes` 位义（须 `win-main` 动态；`attrs&1` 的 4 条 `pdisp=-1` 与 MSVC 标准位义矛盾）；② `attributes 5 vs 1` 语义；③ 13 个 onlysec pTD 的**成因**（名单 R207 QL2 已取得）；④ 34 个无类 TD 的接口派生链；⑤ 5 个 pTD 多记录成因；⑥ R206 遗留 6 项（pad0 语义、708 run 与块边界、pTD 重复、BCA 共享成因、R205 遗留 5 项、R204 遗留 2 项）；⑦ F23/F35 grade（`coverage.tsv`/`function_atlas.tsv` 仍不可读，禁预估回填）；⑧ C7 三死分支、C11 十二 ID。

'''
b,bak=backup(R14,'r14_216')
assert b.count(b'\r\n')==1081
assert b.count(b'## 2.216')==0
nb=b+b'\n'+S216.encode('utf-8')
assert nb.count(b'\r\n')==1081
commit(R14,nb,b,1081,'r14_216')

# ---------- 2. GOAL §1266 ----------
S1266 = '''## §1266 · R208 收口（2026-11-28）· T 形态 thunk 双编码订正（83 主 / 81 兜底）+ thunk 级常量性 + 锚点口径警告 + AircraftClass −8 调整收官 + FACT_INDEX V589→V590

**订正（推翻本轮 §1265 第 2 条的措辞，不动其数字）.**
1. 🔴 **T 形态编码不是一种**：101 条 this 调整 thunk 中 **100** 条为 `83 6C 24 04 <imm8> E9 <rel32>`（mdisp ∈ {4,24,36,40,44}），**1** 条为 `81 6C 24 04 <imm32> E9 <rel32>`（COL 0x7fb310 / `.?AVAircraftClass@@` / mdisp **1728** / vftable 0x7e2250 / slot0 0x41c670 / `81 6C 24 04 C0 06 00 00 E9 13 7C FF FF` / jmp **0x414290**）。正确表述是「83 为主、81 兜底」。两条不变量仍 **101/101**（立即数 == mdisp；E9 目标 == 本类主视图 slot0）。
2. 🟡 **thunk 级常量性**：100 条 A83 只落在 **21** 个 thunk 地址（0x4105e0 单址 75 用），每址立即数唯一 21/21、组内 mdisp 唯一 ⇒「立即数 == mdisp」是 thunk 级常量推论，非逐 COL 独立性质。
3. 🟡 **分母口径**：`.text` 锚点 `83 6C 24 04`=**67**、`81 6C 24 04`=**3**，与 slot0 口径 100/1 不可混用；81 的另两处 0x41c680/0x41c690 是同一 vftable 0x7e2250 的 slot1/slot2（前三槽 0x41c670/0x41c680/0x41c690 三连）。主视图 954 条 0 条 thunk；2 条 `8B 44 24 04` 开头（CD 0x4790e0 / ProgressScreenClass 0x643e80）是真函数体。
4. 🔴 **取得 QM9 ⑥**：AircraftClass m=8 视图体内 −8 调整 = **`add esi, -8` @ 0x41bc8f**（入口 0x41bc30 +0x5F，401 B/135 条），**不是 lea**；InfantryClass `lea esi,[edi - 8]` @0x522a8e、UnitClass @0x74612e（各入口 +0x2E，112 B/39 条）。Infantry 与 Unit 体之间差 10 处（栈帧 2 / 参数 1 / 字段 1 / 内部跳转 6），无一处落在 this 调整位。反控：Aircraft +0x400 窗口 −8 命中 0。
5. 🟡 **跨家族**：#531（hy4，1 回合 / **7.47'** OVERTIME）自报 15/15 PASS 并落 `_r208/x1_tform.json`；#532（deepseek，26 回合 / 3.57' / 无 OVERTIME）9 断言 **1 FAIL**（即第 1 条措辞），另两条加强（thunk 级常量、锚点口径）均成立。主会话 `v1`13 + `v2`11 + `v3`12 + `v4`7 + `v5`12 = **55 断言 0 FAIL**，全部主张逐条复算。
6. 🟡 **FACT_INDEX V590**：写入 F29（stmt 3435→5343 B，其余 55 行逐字节不变），sha `89bb71ba`→`e49a3edd`、240722→**242630** B；指针 + facts_floors（D0/D8/D9/D10，MASTER `96f504e7`→`940c94c0`）+ gate_runner LEDGER 同步重钉。三门 exit 0。
7. 📌 **自错 5 组**（TD 名串多判 NUL / thunk 判据把地址当指针 / `.data` 引用榜含 0 / 只搜 lea 漏 add / 81 编码 E9 基址 va+9 应为 va+13），0 条进结论。
8. ⚪ **未取得**：`attributes` 位义（动态）、`attributes 5 vs 1`、13 个 onlysec pTD 成因、34 个无类 TD 派生链、5 个 pTD 多记录成因、R206 遗留 6 项、F23/F35 grade（两个 tsv 不可读，禁预估）、C7 三死分支、C11 十二 ID。

'''
b,bak=backup(GOAL,'goal_1266')
assert b.count(b'\r\n')==337
assert b.count('## §1266'.encode())==0
nb=b+b'\n'+S1266.encode('utf-8')
assert nb.count(b'\r\n')==337
commit(GOAL,nb,b,337,'goal_1266')

# ---------- 3. LEAD_LOCK QN ----------
SQN = '''## QN · R208 收口（2026-11-28）· T 形态双编码订正（83 100 / 81 1，imm==mdisp 仍 101/101）；thunk 级常量性 21 址；锚点 67/3 与 slot0 100/1 分母不同；AircraftClass −8 = add esi,-8；V590 重钉

**QN1. 🔴 订正 §2.215/QM2 措辞：T 形态编码两种.** 把 thunk 判据放宽到 `83`/`81` + `6C 24 04` + imm + `E9 rel32` 后，额外视图 slot0 仍 **101** 条 T，但 **100 条 A83**（mdisp ∈ {4,24,36,40,44}）+ **1 条 B81**（COL 0x7fb310 / `.?AVAircraftClass@@` / mdisp **1728**=0x6C0 / vftable 0x7e2250 / slot0 **0x41c670** / `81 6C 24 04 C0 06 00 00 E9 13 7C FF FF` / jmp **0x414290**）。imm8 有符号上限 127 < 1728 ⇒ 编译器选 imm32，属编码选择的直接后果。**立即数 == mdisp 101/101、E9 目标 == 本类主视图 slot0 101/101 均未动摇**；被推翻的只是「统一为 83」这一句。

**QN2. 🟡 thunk 级常量性.** A83 的 100 条只映射 **21** 个不同 thunk 地址（`0x4105e0` 一址供 **75** 个 COL 复用）；每个 thunk 地址的立即数唯一 **21/21**，共享同一 thunk 的 COL 其 mdisp 也唯一（零冲突）。⇒ 等式是 thunk 级常量的推论；审计 #532 提醒「若出现共享 thunk 而 mdisp 不同的 COL 则等式失效」，主会话 `v5` 实测该反例在本镜像 **0 个**，故等式当前成立但**不能当作逐类性质**。

**QN3. 🟡 分母口径实测（防混用）.** `.text` 全域字节锚点：`83 6C 24 04` = **67** 处、`81 6C 24 04` = **3** 处（0x41c670 / 0x41c680 / 0x41c690，imm32 全 1728）。三处中只有 0x41c670 是某个 COL 的 slot0；另两处是同一 vftable **0x7e2250** 的 slot1/slot2，该表前三槽即三连 81 thunk（第四槽 0x41b6a0）。⇒ 只有「按额外视图 slot0 取一条」口径能支撑 101；锚点口径 67/3 与它**不同分母**。主视图 954 条 **0 条** thunk；2 条 `8B 44 24 04` 开头（CD 0x4790e0 / ProgressScreenClass 0x643e80）经体首指令判定为真函数体。

**QN4. 🔴 取得 QM9 ⑥（AircraftClass m=8 视图 −8 调整位置）.** 上一轮只搜 `lea` 得 0 命中；判据放宽为「操作数含 −m 常量负偏移」后三条全中且编码不同：AircraftClass **`add esi, -8` @0x41bc8f**（入口 0x41bc30，**+0x5F**，401 B/135 条）；InfantryClass `lea esi,[edi - 8]` @**0x522a8e**（入口 0x522a60，+0x2E，112 B/39 条）；UnitClass @**0x74612e**（入口 0x746100，+0x2E，112 B/39 条）。Infantry↔Unit 体差 **10** 处 = 栈帧 2 / 参数偏移 1 / 字段偏移 1（`[edi+0x6b8]` vs `[edi+0x6bc]`）/ 内部跳转 6，**无一处落在 this 调整位**。反控：Aircraft 入口 +0x400 起 512 B 窗口 −8 命中 **0**。

**QN5. 🟡 跨家族（#531 hy4 / #532 deepseek，§2.12 规则 D 全复算）.** #531：1 回合 / **7.47'** vs 预算 5.0 ⇒ **[OVERTIME]** 如实记；自报 15/15 PASS，落 `_r208/x1_tform.json`（101 条 A/B 明细、3 条 I 形态、mismatch/jmp_fail 皆空）；它自述曾起过用旧引用判据的后台探测得 `vftable=None` 并声明作废。 #532：26 回合 / 3.57' / 无 OVERTIME；9 断言 **1 FAIL** = 「统一 83」表述，订正句本轮全采纳；两条加强（thunk 级常量、锚点口径）经 `v5` 实测成立。主会话复算合计 **55 断言 0 FAIL**（v1 13 / v2 11 / v3 12 / v4 7 / v5 12）。

**QN6. 🟡 落盘与门禁.** R14_COMMON **§2.216** CR 保持 **1081**；GOAL **§1266** CR 保持 **337**；本段 **QN** CR 保持 **137**；STATUS_BOARD 第 208 轮 CR 保持 **0**（开局 **262 行 >= 260** ⇒ 先归档最早 2 段至 BOARD_ARCHIVE，归档 CR 保持 **2952**）。C16_FLOORS 纳入 §2.216（unpinned 0 / hollow 0 / missing 0）。**FACT_INDEX V589→V590**：写入 F29（stmt 3435→5343 B，其余 55 行逐字节不变；57 行），sha `89bb71ba`→**`e49a3edd`**、240722→**242630** B；指针 + facts_floors（D0/D8/D9/D10，MASTER `96f504e7`→`940c94c0`）+ gate_runner LEDGER 同步重钉。三门 exit 0：C19 ok(e49a3edd/242630/V590)、C20 ok、G1=G2=G3=ok。

**QN7. 📌 自错 5 组（0 条进结论）.** ①`v1` TD 名串多判「含 NUL」⇒ 0 条（去掉即 988）；②`v1` thunk 判据把 slot0 **地址**当函数地址读（应 `dw(slot0)`）⇒ 0 条 T；③`v1` `.data` 引用榜未排 0 ⇒ 首位 0（8380）；④`v2` 只搜 `lea` 漏 `add esi,-8`（恰是本轮要收的 QM9 ⑥）；⑤`v3`/`v4` 81 编码 E9 基址取 `va+9`（应 `va+13`）⇒ 落点 0x41428c 全是 `90` 填充。

**QN8. ⚪ 未取得.** ① `attributes` 位义（须 `win-main` 动态；`attrs&1` 4 条 `pdisp=-1` 与标准矛盾）；② `attributes 5 vs 1`；③ 13 个 onlysec pTD 成因；④ 34 个无类 TD 接口派生链；⑤ 5 个 pTD 多记录成因；⑥ R206 遗留 6 项；⑦ F23/F35 grade（两 tsv 不可读，禁预估回填）；⑧ C7 三死分支、C11 十二 ID。

'''
b,bak=backup(LOCK,'lock_qn')
assert b.count(b'\r\n')==137
assert b.count('## QN ·'.encode())==0
nb=b+b'\n'+SQN.encode('utf-8')
assert nb.count(b'\r\n')==137
commit(LOCK,nb,b,137,'lock_qn')
print('THREE PIECES OK')
