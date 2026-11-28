# -*- coding: utf-8 -*-
"""R219 p3：GOAL §1277 + LEAD_LOCK QM + STATUS_BOARD 第 219 轮。"""
import os, hashlib, json
ROOT = '/home/t628/projects/ra2-campaign-forge'
BASE = ROOT + '/R17_LEAD_BASELINE'; T = ROOT + '/lead/next_re_20261117_r14'

def bak(path, tag):
    b = open(path, 'rb').read()
    base = '%s/%s.before_r219_%s' % (BASE, os.path.basename(path), tag)
    for i in range(10):
        dst = base + (('_%d' % i) if i else '') + '_20261128.bak'
        if os.path.exists(dst):
            if open(dst, 'rb').read() == b: return b
            continue
        fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, 'wb') as f: f.write(b)
        return b
    raise SystemExit('bak exhausted ' + tag)

GOAL = """
## §1277 · R219（2026-11-28）· 6 处超域位点定性 + 槽号口径 914/931 复证 + 幻影=162 记录常量表撞 COL + 0x4a1ca0 是 CRC-32；FACT_INDEX V601

- **6 处超 344 槽域位点定性（R218 待办①闭合）**：`0x7bea07`=`[esi+0x784]`、`0x7bea0f`=`[esi+0x788]`、`0x7c2f17`/`0x7c301c`=`[esi+0x77c]`、`0x7c37c7`=`[esi+0x780]` 是**对象内函数指针字段**——全 `.text` 对这三个 offset 引用 31 条，其中 imm32 写 `.text` 的写入端 **12** 条（12/12 目标在 `.text`），同 offset 还被 `fmul qword` 2 次、`fstp qword` 1 次当 double 用；`0x7cde2b`=`[esi+0x87c488]` 的 esi=edi*12，是**步长 12 B 的静态派发表**（首项 `007ce046 007f97d0 0087c370`，上界 `cmp edi,0x87c4c0`）。反控：全库无任何虚表槽数 ≥480（max 344）⇒ s=479..482 不可能对应槽。
- **槽号口径成立**：931 个 s≥256 位点做前驱分类（窗口 24）得 **A_vtable 914 / C_neither 17**；17 处再溯源为 `vtable_load 6 / indirect_ld 2 / mem_other 1 / pop 2` + 6 处字段/派发表，**无一落入虚表槽语义** ⇒ R218 的 931/91/925 不需订正。逐数复现：sweep **1,394,186** 条（末 `0x7e0fff`）/ 接受集 **18,935**（esp 9、负 disp 2、索引排除 391）/ s≥256 **931** / distinct **91** / UnitClass 域 **925** / top s 309-85-73-58-44。
- **4 个「幻影虚表」的真实载体**：`0x876ff4..0x877a03` 与 `0x87b170..0x87bb7f` **逐字节相同**（各 2576 B，sha `7b724b01…`）；记录 `f3−f2=0x00800080` **162/162** 成立（shift 4/8/12 命中 0；delta 0x800000/0x800100 命中 0）；表内是 16 位字递增序列，**`0x00800040` 是 `0x0040`/`0x0080` 两个相邻 16 位字被读成 dword，恰等于 COL 地址**（数值撞车）。表区间被 `.text` dword 引用 24 次，**全部指向表首**（`mov dx, word ptr [edx+0x87b170]`），无槽消费。幻影计数仍 **4**，排除 `.data 0x870000..0x880000` 后真表仍 **1214**（delta 0）。
- **`0x4a1ca0` 是 CRC-32 累加器**（R218 待办⑤闭合）：`cmp eax,4` 判「已缓冲 4 字节」，凑满后 `not→查表 0x81f7b4→xor→not` 存回 `[ecx]` 并清零；`0x81f7b4` 256 项表与 `0xEDB88320` 生成表 **256/256 相同**（反控 CRC-32C 1/256、Koopman 1/256）；字段 `+0 crc / +4 count / +8..+0xb buf / +0xc shadow`；`flush4` 与 `zlib.crc32` 在 15 组输入上 **15/15 一致**。
- **跨家族**：card A(#569 hy4 exec 9 回合 1.88′ vs 8) succeeded，67 diff 目标 `other 61 / push_ebp 2 / jmp_rel 4`，反查 1 次 53 / 4 次 14（宿主为 Aircraft/Foot/Infantry/Unit）；其分布与 R218 粗分布（other 58 / mov_eax_arg 4 / push_ebp 1）不同，R218 粗分布**作废**。card B(#570 hy4 exec 14 回合 7.22′ vs 8) succeeded，首次口径错（漏 `skipdata`，1,150,117 条）经指出后自我更正为 18,935/931/91/925/函数 311/unresolved 528。审计 #571 deepseek **超预算未取回，记 OVERTIME**。
- **自错 2 条**：E1 `m5` 漏 `md.skipdata=True`（155,215 条）；E2 `m4` trace() 返回标量致解包崩溃。0 条进结论。
- **落盘**：R14_COMMON §2.227 CR=1081（1934511→1941036 B）；本段 §1277 CR=337；LEAD_LOCK QM CR=137；STATUS_BOARD 第 219 轮 CR=0。**FACT_INDEX V600→V601**（仅 F29 一行）280689→**284839** B，sha `fb513cc8`→**`54ff0419`**。
"""
p = ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md'; b0 = bak(p, 'GOAL')
assert b0.endswith(b'\n') and b0.count(b'\r') == 337
new = b0 + GOAL.encode('utf-8'); assert new.count(b'\r') == 337
open(p, 'wb').write(new); chk = open(p, 'rb').read()
assert chk.startswith(b0) and chk.count(b'\r') == 337
print('[写入] GOAL bytes %d -> %d CR %d sha %s -> %s'
      % (len(b0), len(chk), chk.count(b'\r'), hashlib.sha256(b0).hexdigest()[:16], hashlib.sha256(chk).hexdigest()[:16]))

LOCK = """
**QM. 🔴 6 处「超 344 槽域」disp 位点全部定性，无一为虚表槽.** `0x7bea07`=`call [esi+0x784]`、`0x7bea0f`=`[esi+0x788]`、
`0x7c2f17`/`0x7c301c`=`[esi+0x77c]`、`0x7c37c7`=`[esi+0x780]` 五个 disp 是**对象内函数指针字段偏移**：
全 `.text` 对 `+0x77c/+0x780/+0x784` 引用 **31** 条，其中 `mov dword ptr [reg+off], imm32(.text)` **12** 条（12/12 目标在 `.text`），
同 offset 另有 `fmul qword` **2** 次（`0x4b3da6`/`0x6a33f5`）与 `fstp qword` **1** 次（`0x66f2a9`）⇒ 数据字段，非槽。
第 6 处 `0x7cde2b`=`call [esi+0x87c488]`，`esi` 由 `lea esi,[edi+edi*2]`+`shl esi,2` 得 **edi*12**，`0x87c488` 是**步长 12 B 派发表**（首项 `007ce046`，上界 `cmp edi,0x87c4c0`）。
**反控**：全库 1218 张虚表**无槽数 ≥480**（max 344）⇒ s=479/480/481/482 不可能对应任何槽。

**QM2. 🔴 槽号口径（disp//4）成立，R218 的 931/91/925 不需订正.** 931 个 s≥256 位点前驱分类（窗口 24）：**A_vtable 914 / C_neither 17**；
17 处 200 条窗口溯源 `vtable_load 6 / indirect_ld 2 / mem_other 1 / pop 2` + 6 处字段/派发表，无一落入虚表槽语义。
逐数复现：sweep **1,394,186**（末 `0x7e0fff`）/ 接受集 **18,935** / esp **9** / 负 disp **2** / 索引排除 **391** /
s≥256 **931** / distinct **91** / UnitClass 域 **925** / top s `309-85-73-58-44`。R218 的 1,394,120/0x7e0ffd 与本轮差 66 = 非法跳字节是否计为 `.byte`。

**QM3. 🔴 「4 个幻影虚表」= 162 记录 × 16 B 常量表的双份副本，f2 字段撞 COL 地址.** `0x876ff4..0x877a03` 与 `0x87b170..0x87bb7f`
**逐字节相同**（各 2576 B，sha256 `7b724b01…`）；记录 `f3−f2=0x00800080` **162/162** 成立
（反控 shift 4/8/12 命中 **0**；整 `.data` 窗口 delta `0x800000`/`0x800100` 命中 **0/0**）。
表内为 16 位字递增序列，`0x00800040` 是 `0x0040`/`0x0080` 两相邻字被读成 dword，**数值撞车** COL `0x800040`，非虚表。
表区间 `.text` dword 引用 **24** 次**全部指向表首**（`mov dx, word ptr [edx+0x87b170]`），按字访问、无槽消费。
幻影计数仍 **4**（`0x877000`/`0x877010`/`0x87b17c`/`0x87b18c`，`dw(V)=0x010000c0`）；排除 `.data 0x870000..0x880000` 后真表仍 **1214**（delta 0）。
⇒ R218「1214 真表」**保持**，成因描述**订正**。

**QM4. 🔴 `0x4a1ca0` 是 CRC-32 累加器，不是「环缓冲容量 4」.** `cmp eax,4` 判「已缓冲 4 字节」；凑满后
`not eax`(`0x4a1cf3`) → 逐字节 `xor idx`(`0x4a1d06`) → `mov ebx,[ebp*4+0x81f7b4]`(`0x4a1d0b`) → `xor eax,ebx` → `not eax`(`0x4a1d18`) → 存 `[ecx]`、清 `[ecx+4]`。
`0x81f7b4` 256 项与 CRC-32 反射 `0xEDB88320` 生成表 **256/256 相同**（反控 CRC-32C `0x82F63B78` 1/256、Koopman `0xEB31D82E` 1/256）。
字段 `+0 crc / +4 count(0..3) / +8..+0xb buf / +0xc shadow`。`flush4` 与 `zlib.crc32` 在 3×5 组 **15/15 一致**。

**QM5. 🟡 跨家族 / 自错.** card A(#569，9 回合 1.88′ vs 8，无 OVERTIME)：67 diff 目标 `other 61 / push_ebp 2 / jmp_rel 4`，
反查 1 次 **53** / 4 次 **14**（宿主恒为 Aircraft/Foot/Infantry/Unit）；与 R218 粗分布（other 58 / mov_eax_arg 4 / push_ebp 1）不同，
R218 粗分布**作废**（未留判据代码不可复现）。card B(#570，14 回合 7.22′ vs 8，无 OVERTIME)：首次漏 `skipdata` 只解 1,150,117 条（报 15472/744/739），
经指出后更正为 **18,935/931/91/925/函数 311/unresolved 528**，与主会话 m6 逐数一致。
审计 #571（deepseek，`--max-turns 50`）**超出 12 分钟预算仍在运行，结果未取回 ⇒ OVERTIME**。
主会话自错 2 条：E1 `m5` 漏 `skipdata`（155,215 条）；E2 `m4` trace() 返回标量解包崩溃。0 条进结论。

**QM6. 🟡 收口.** R14_COMMON **§2.227** CR 保持 **1081**（1934511→1941036 B）；GOAL **§1277** CR 保持 **337**；
本段 **QM** CR 保持 **137**；STATUS_BOARD 第 219 轮 CR 保持 **0**（220 行 < 260，不触发归档）。
**FACT_INDEX V600→V601**（仅 F29 一行）280689→**284839** B、sha `fb513cc8`→**`54ff0419`**。

**QM7. ⚪ 未取得.** ①162 记录常量表（2576 B × 2 副本）的语义（既非虚表也非 COL，按字访问，疑为坐标/尺寸查表）；
②67 个 diff 目标的**语义**归类（只完成前缀分类，未做「重写了哪个行为」）；
③`0x87c488` 12 B 派发表 4 项的语义（`0x7ce046` 是 `xor eax,eax/ret` 桩）；④三全局 `0x887680/84/88` 运行期初值（virt-only，须 win-main）；
⑤F23/F35 grade；⑥C7 三死分支、C11 十二 ID。
"""
p = ROOT + '/lead/LEAD_LOCK'; b0 = bak(p, 'LOCK')
assert b0.endswith(b'\n') and b0.count(b'\r') == 137
new = b0 + LOCK.encode('utf-8'); assert new.count(b'\r') == 137
open(p, 'wb').write(new); chk = open(p, 'rb').read()
assert chk.startswith(b0) and chk.count(b'\r') == 137
print('[写入] LEAD_LOCK bytes %d -> %d CR %d sha %s -> %s'
      % (len(b0), len(chk), chk.count(b'\r'), hashlib.sha256(b0).hexdigest()[:16], hashlib.sha256(chk).hexdigest()[:16]))

BOARD = """
## 第 219 轮（2026-11-28）6 处超域位点定性 + 槽号口径 914/931 复证 + 幻影 = 162 记录常量表撞 COL + 0x4a1ca0 是 CRC-32

- **6 处「超 344 槽域」位点（R218 待办①）：全部不是虚表槽。** `0x7bea07`=`[esi+0x784]`、`0x7bea0f`=`[esi+0x788]`、`0x7c2f17`/`0x7c301c`=`[esi+0x77c]`、`0x7c37c7`=`[esi+0x780]` 是**对象内函数指针字段**：全 `.text` 对该三 offset 引用 **31** 条，`mov dword ptr [reg+off], imm32(.text)` **12** 条（12/12 目标在 `.text`），同 offset 还被 `fmul qword` 2 次 / `fstp qword` 1 次当 double 用。`0x7cde2b`=`[esi+0x87c488]` 的 `esi=edi*12`，是**步长 12 B 派发表**。反控：全库无虚表槽数 ≥480（max 344）。
- **槽号口径（disp//4）成立，R218 的 931/91/925 不订正。** 931 个 s≥256 位点前驱分类（窗口 24）= **A_vtable 914 / C_neither 17**；17 处溯源 `vtable_load 6 / indirect_ld 2 / mem_other 1 / pop 2` + 6 处字段，无一入槽语义。逐数复现 sweep **1,394,186**（末 `0x7e0fff`）/ 接受集 **18,935** / esp **9** / 负 disp **2** / 索引排除 **391** / s≥256 **931** / distinct **91** / UnitClass 域 **925** / top s `309-85-73-58-44`。
- **4 个「幻影虚表」的载体（R218 待办④）：162 记录 × 16 B 常量表的双份逐字节副本。** `0x876ff4..0x877a03` 与 `0x87b170..0x87bb7f` 各 2576 B、sha256 同为 `7b724b01…`、**逐字节相同**；记录 `f3−f2=0x00800080` **162/162**（shift 4/8/12 命中 **0**；delta `0x800000`/`0x800100` 命中 **0/0**）。表内是 16 位字递增序列，**`0x00800040` 只是 `0x0040`/`0x0080` 两相邻字被读成 dword**，与 COL 地址数值撞车，不是虚表。表区间 `.text` dword 引用 **24** 次**全部指向表首**（`mov dx, word ptr [edx+0x87b170]`）。幻影计数仍 **4**，排除 `.data 0x870000..0x880000` 后真表仍 **1214**（delta 0）。
- **`0x4a1ca0` 是 CRC-32 累加器（R218 待办⑤）。** `cmp eax,4` 判「已缓冲 4 字节」，凑满后 `not→查表 0x81f7b4→xor→not` 存回并清零；`0x81f7b4` 256 项与 `0xEDB88320` 生成表 **256/256 相同**（反控 CRC-32C 1/256、Koopman 1/256）；字段 `+0 crc / +4 count / +8..+0xb buf / +0xc shadow`；`flush4` 与 `zlib.crc32` **15/15 一致**。
- **跨家族**：card A(#569 hy4 exec 9 回合 1.88′ vs 8) succeeded，67 diff 目标 `other 61 / push_ebp 2 / jmp_rel 4`，反查 1 次 **53** / 4 次 **14**（宿主恒为 Aircraft/Foot/Infantry/Unit）；R218 粗分布（other 58 / mov_eax_arg 4 / push_ebp 1）**作废**。card B(#570 hy4 exec 14 回合 7.22′ vs 8) succeeded，首轮漏 `skipdata`（1,150,117 条 → 15472/744/739），指出后自我更正为 **18,935/931/91/925/函数 311/unresolved 528**。审计 #571（deepseek 50 轮）**超预算未取回 ⇒ OVERTIME**。
- **自错 2 条**：E1 `m5` 漏 `md.skipdata=True`（155,215 条）；E2 `m4` trace() 返回标量致解包崩溃。0 条进结论。
- **建账**：FACT_INDEX **V600→V601**（仅 F29 一行）280689→**284839** B、sha `fb513cc8`→**`54ff0419`**。
- **收口**：R14 §2.227 CR 1081（1934511→1941036 B）、GOAL §1277 CR 337、本段 QM CR 137、本段 CR 0（220 行，< 260 不归档）。
"""
p = T + '/STATUS_BOARD.md'; b0 = bak(p, 'BOARD')
assert b0.endswith(b'\n') and b0.count(b'\r') == 0
lines_before = len(b0.split(b'\n')) - 1
new = b0 + BOARD.encode('utf-8'); assert new.count(b'\r') == 0
open(p, 'wb').write(new); chk = open(p, 'rb').read()
assert chk.startswith(b0) and chk.count(b'\r') == 0
lines_after = len(chk.split(b'\n')) - 1
assert lines_after <= 300, 'BOARD lines %d > 300' % lines_after
print('[写入] STATUS_BOARD bytes %d -> %d  lines %d -> %d  CR %d'
      % (len(b0), len(chk), lines_before, lines_after, chk.count(b'\r')))
json.dump(dict(goal_bytes=len(chk), board_lines=lines_after), open(ROOT + '/_r219/p3.json', 'w'), indent=1)
