"""Assemble final VERDICT.md into the output directory root."""
import io, os

OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT6"
rows_md = io.open('verdict_rows.md', encoding='utf-8').read()

HEAD = """# NAMED_PUSH_AUDIT6 — S22_B2 全 18 行逐行裁定（异族独立审计）

## 0. 身份与材料

- 审计员：**异族独立审计**（非本批执行器）。本文件每一个结论都由我自己反汇编 `gamemd.exe` 字节得出；执行器 `EVIDENCE\\ROW_*.txt`、`REPORT.md`、`work\\*` **未作任何一条证据引用**（仅用于事后比对锚点是否诚实，比对结果见 §4）。
- 镜像：`D:\\Project\\ra2-campaign-forge\\ra2youli\\gamemd.exe`，`Get-FileHash -Algorithm SHA256` 实测
  `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（与卡面期望逐字一致），大小 4,825,360 B。
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`（VirtualSize 4,060,045）。
- 工具：Python 3.12.10 + capstone 5.0.7（**`skipdata=True`**）+ pefile 2024.8.26；无 venv、未 `pip install`。
- 扫描规模（自建索引，`work\\sweep.py`）：全 `.text` 线性扫描 **1,392,592** 条指令、**6,728** 个 direct-call 目标、**124,621** 个 imm32 引用。
- 写域：只写 `NAMED_PUSH_AUDIT6\\`。未改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `NAMED_PUSH_*` 下任何文件。

## 1. 本批范围与 entry 取法

`NAMED_PUSH_S22_B2\\delta.tsv` 表头 6 列（`entry / subsystem / name / one_line_semantics / grade / evidence_path`），数据行 **18 行**，`subsystem` 全为 `S22`，`grade` 全为 `[已证]`。取法：按表头逐行解析，**全取 18 行**（本轮派单即「delta.tsv 全部 18 行」），不筛不减。
逐行 `entry`（升序，与我实测的 `.text` 区间自洽）：
`006C1010 006C1190 006C1310 006C1490 006C1610 006C1790 006C1910 006C1A90 006C1C10 006C1D90 006C1F10 006C2090 006C2210 006C2390 006C2510 006C2690 006C2810 006C2990`
交叉自洽（只作行数校验、不作证据）：同目录 `base_rate.tsv` 记 `rows_checked=18 / ring2_ok=18 / ring3b_ok=18 / ring4_ok=18 / all_four=18 / rate=1.0000`，与本批 18 行口径一致。

18 行全部是 `TClassFactory<T>::slot3` 同族模板槽。名字里的 `T` 与槽号 `slot3` **只当线索**，一律由字节复算（见每行 ②）。

## 2. 判定口径（沿用上一批五点，宁严不宽）

1. **② 类身份独立成立**：entry 作 4B VA 在 `.rdata` 的**唯一**命中 → 回扫该表基址 `vt`，`(slot-vt)/4` 必须等于名字线索槽号；`[vt-4]` 必须是 RTTI COL（`sig=0`），`[COL+0xC]`→TD，`[TD+8]` 内联名串。槽号由 offset/4 **复算**，不反推。
2. **③b 具体形态**：只认 ③b；本批 18 行实测全为 **③b②（可伪证的错误码/返回约定）**：给出失败/成功返回值、被调出口常量表、以及**调用方拿它的哪条指令分支**（含跳转地址与两路动作差异）。禁止以「被调用者内部的写」充当 ③b④ 的循环内非栈写；禁止 ③a 形态。
3. **④ 使用见证独立成立**：按 `R14_COMMON.md:594` 的「活 vtable 槽位」形态（构造器装的活表 + `vt[slot]==entry` + 写点在行体外 + site 不共用）与 `:739-743` **D-43 宽读法**（不要求存在真实 `call [reg+disp]` 派发点；本批 18 行 direct 调用者实测均为 0，属纯虚派发）。
4. **④ 与 ② 不同源**：同一虚表槽不得既证类身份又证被使用。**㉓ 成对陷阱强制检查**：活 vptr 必须由**构造器**写入，`push <dtor>; call 0x7C978A`(atexit) 装的表不算；④ 锚点不得落在析构器里。
5. **⑤ 语义与实测相符**：第 4 列的读写方向、子型标注必须与字节一致；方向写反或子型标错一律 `FAIL`。

> **边界口径提醒**：函数定界用「本函数起点 → 下一个已知被调 entry」，因此一个「构造器族」（`Ctor` / `Ctor2` / 带 `noinit` 标记的变体紧邻排放）可能落在同一定界区内。所以每行「同构造器写入的成员/次级表」一列里，个别成员表可能来自同区域的**另一个**构造器变体（例如第 5 行混入 `CCFileClass`/`CDFileClass` 的表）。这一列的作用是**排除**（证明那些表不是主表），不影响主表判定——主表判据只看 `[this+0]` 的写且 `vt0` 必须等于 `00410260`。

## 3. 逐行裁定

"""
TAIL = """
## 4. 与执行器锚点的事后比对（仅校验其数字是否诚实，不作我的证据）

把 `REPORT.md` 的「每行自身四环锚点表」18 行 × 9 个地址与**我独立测出的同一组量**逐格比对（脚本 `work\\repdiff.py`）：

| 比对项 | 结果 |
|---|---|
| ② 槽 / vt / COL / TD | 18/18 **逐格相同** |
| ③ 主站点 / 对象构造器 / 对象主 vt / 释放点 | 18/18 **逐格相同** |
| ④ alloc / ctor 调用点 / 注册点 / CLSID | 18/18 **逐格相同** |

⇒ 本批执行器给出的地址**没有编造**（这与上一批 B1 的 16 行里 2 行假不同）。但「地址对」不等于「环成立」：上一批两行假的原因正是**取错了虚表**（把构造器里的内嵌成员表当对象主虚表），地址本身也是真的。所以本批我不是比地址，而是**逐行重算主虚表归属**，见 §5。

## 5. 本轮重点：18 行的 vtable 到底是不是对象主虚表（不是内嵌成员表）

卡的警告指向上一批 2 行假行的成因：构造函数里 `mov [reg+disp], <成员表>` 被误当 `mov [this], <主表>`；真主虚表槽 0 是 `00410260`。**我逐行用三条独立硬判据复核，18/18 通过**：

1. **写偏移**：对象构造器里对 `this` 寄存器（从 `ecx` 取到，逐行不同：多为 `esi`，`006C2210` 行为 `ebp`@`006E5B69 mov ebp,ecx`）的 `mov [this+0], imm` 才是主表；`[this+4]/[+8]/[+0xC]` 等偏移一律判**成员/次级表**。
2. **槽 0 值**：每行所取主表的 `vt[0]` 实测**都是 `00410260`**（18/18）。被我判为成员表的那些（如行 1 的 `007EF874` vt0=`004105E0`、行 5 的 `007F6524` vt0=`00410580`、行 18 的 `007E4638` vt0=`00466080` 且为 `VectorClass<TPoint3D<int>>`）槽 0 **都不是** `00410260`。
3. **RTTI 名**：所取主表的 TD 名串必须等于该类（如 `.?AVParasiteClass@@`），且与被调对象语义一致。

**特别提示的两个高危行（双 offset0 写表）**：
- `006C2990`（`VBuildingTypeClass`）：构造器 `0045DD90` 同时写 `0045E2AB c7 86 84 17 00 00 38 46 7e 00 mov [esi+0x1784], 0x7E4638`（=`VectorClass<TPoint3D<int>>`，**正是上一批踩雷的那种内嵌成员表**，槽 0 = `00466080` 非 QI）与 `0045E2CD c7 06 70 45 7e 00 mov [esi], 0x7E4570`。实测 `007E4570` 的 `vt0=00410260`、名 `.?AVBuildingTypeClass@@` ⇒ 执行器取的是**主表**，没有踩雷。
- `006C1610`（`VoxelAnimTypeClass`）：构造器区还相邻出现 `CCFileClass`/`CDFileClass` 的表（`007E16B0`/`007E1668`），这是构造器边界外溢，非本对象成员；本行主表为 `007F6548`（`vt0=00410260`）。

## 6. 一条需账（不构成 FAIL）

18 行 `slot3` 的末条都是 `ret 0x10`（4 个栈 dword）。本镜像的 COM 方法用 **`__stdcall` + 显式 `this` 作第一个栈参**（不是 thiscall），同一张工厂表里可自证：
- 槽 0 `006C0F50`（QueryInterface）末条 `c2 0c 00` = 3 dword = `(this, riid, ppv)`；
- 槽 4 `006C1090` 末条 `c2 08 00` = 2 dword = `(this, BOOL)`；
- 槽 3 本行 = 4 dword = `(this, pUnkOuter, riid, ppv)` ⇒ 与 `IClassFactory::CreateInstance` 的语义参数完全对上（且 `pUnkOuter` 非空返 `0x80040110`、`ppv` 空返 `0x80070057`）。

同表槽 0 的 IID 比对表也自证接口身份：`007F7C90` = `{00000000-0000-0000-C000-000000000046}` = IID_IUnknown，`007F7CA0` = `{00000001-0000-0000-C000-000000000046}` = IID_IClassFactory。⇒ 行文「（IClassFactory::CreateInstance）」的接口归属**成立**，`ret 0x10` 不是异常，`this` 走栈是这套构建的约定。记入备注供后续批次复用，避免下一批把它当「3 参 ret 0xC」而误判。
"""

io.open(os.path.join(OUT, 'VERDICT.md'), 'w', encoding='utf-8').write(HEAD + rows_md + TAIL)
print('written', os.path.join(OUT, 'VERDICT.md'))
