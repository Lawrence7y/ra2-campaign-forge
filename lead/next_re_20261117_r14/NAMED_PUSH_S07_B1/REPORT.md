# NAMED-PUSH S07 B1 — REPORT（最终）

## 批次口径

- 目标二进制：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
  - SHA-256 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，与期望**逐字相符**（见 `work/sha_check.txt` 口径，实测见执行日志）
  - ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`（pefile VirtualSize=0x3DF38D 实测一致）
- 子系统：`S07`；批次：`B1`；候选 18 行
- 工具：Python 3.12.10 / capstone 5.0.7（`skipdata=True`）/ pefile 2024.8.26，无 venv、无 pip install
- 四环：D-40 ①入口 / ②类身份(独立取证) / ③整体合同(只认③b) / ④使用见证(与②不同源)
- 三陷阱主动排查：
  - ① **读写方向不写反**：`call 0x410380` 经 `[eax+0xC]`=IStream::Read=流读入；`call 0x410320` 经 `[eax+0x10]`=IStream::Write=流写出（本批字节逐行核定，见 `work/IO` 证据）
  - ② **④锚点落析构器判 FAIL(㉓)**：④ 锚点一律取行外构造器写活表点；体内析构器自装表（如 0042173D/004370C4/00491214/00555156）按 ㉓ 排除
  - ③ **小成员表 vtable 非对象主虚表**：主表 vt[0] 常见 00410260；ConvertClass 紧邻的 007E5318(`DynamicVectorClass<ConvertClass*>`)/007E5338(`VectorClass`) 为容器成员表，明确排除，② 只用对象主表 007E5358(`.?AVConvertClass@@`)
- ③可伪证性：多值状态码 / Find 返 -1 下标约定算；{0,1} 布尔不算（本批 Find 失败码由被调体 `83 C8 FF`=`or eax,-1` 字节伪证）

## 筛选命令（可复算）

见 `work/filter_b1.py`。核心口径：

```python
named = [r for r in csv.DictReader(open(HITS, encoding='utf-8'), delimiter='\t')
         if r['subsystem'] == 'S07' and r['p3b2_named'] == 'True']
def is_pseudo(n): return bool(re.match(r'^(fn_|sub_)[0-9A-Fa-f]{8}$', n))
real = [r for r in named if not is_pseudo(r['name'])]
b1 = sorted(real, key=lambda x: int(x['entry'], 16))[:18]
```

`S07 named=True` 共 **22** 行；排除 `fn_`/`sub_` 伪名后仍 **22** 行（本批 22 行均非地址式伪名，全部是 `Class::slotN`/`Class::vslotN` 真名）；按 entry 升序取前 **18**。被截在批次外的 4 行：006DBE00(Tactical::slot6)、007BA8C0/007BBB90/007BBCF0(BSurface)。

## 逐行总表（18 行）

| # | entry | name | ①入口 | ②类身份 | ③b | ④使用见证 | 四环齐全 | 产出 | 一句话理由 |
|---|-------|------|-------|---------|-----|-----------|---------|------|-----------|
| 1 | 00421730 | AlphaShapeClass::vslot8 | PASS | PASS | **PASS** | PASS | **是** | 是 | 析构体内容器 Find -1 哨兵+压缩摘链非栈写循环，RTTI 钉死，行外 ctor 装表 |
| 2 | 00435BE0 | BuildingLightClass::vslot69 | PASS | PASS | FAIL | PASS | 否 | 否 | 唯一站点 malloc 零判断=分配包装模板假句，无 ③b |
| 3 | 004361D0 | BuildingLightClass::vslot23 | PASS | PASS | FAIL | PASS | 否 | 否 | 浮点光照计算，站点为类型/布尔探测(imm=1)，无可伪证错误码 |
| 4 | 004370C0 | BuildingLightClass::vslot8 | PASS | PASS | **PASS** | PASS | **是** | 是 | 同 slot8 析构摘链 Find -1+压缩循环，RTTI+行外 ctor |
| 5 | 00491210 | ConvertClass::slot0 | PASS | PASS | **PASS** | PASS | **是** | 是 | 析构摘链 Find -1+压缩循环；主表 007E5358，成员容器表已排除 |
| 6 | 004BAD80 | DSurface::slot23 | PASS | PASS | FAIL | PASS | 否 | 否 | chA p3=0，无 falsifiable 返值/跳表/循环非栈写 |
| 7 | 004BB0D0 | DSurface::slot3 | PASS | PASS | FAIL | PASS | 否 | 否 | 单一 magic 常量 0x887601c2 比较，非多值状态码/非 Find -1 |
| 8 | 004BB620 | DSurface::slot4 | PASS | PASS | FAIL | PASS | 否 | 否 | 同 magic 常量 0x887601c2 比较，不构成可伪证返回约定 |
| 9 | 004BB830 | DSurface::slot7 | PASS | PASS | FAIL | PASS | 否 | 否 | chA p3=0，call→test 两路动作签名相同 |
| 10 | 004BF750 | DSurface::slot36 | PASS | PASS | FAIL | PASS | 否 | 否 | chA p3=0，被调无可伪证返值常量 |
| 11 | 004C0750 | DSurface::slot19 | PASS | PASS | FAIL | PASS | 否 | 否 | 间接 call→TEST_EAX→je 空/布尔探测，非多值错误码 |
| 12 | 004C0E30 | DSurface::slot20 | PASS | PASS | FAIL | PASS | 否 | 否 | 同 TEST_EAX je 布尔探测，无 ③b 整体合同 |
| 13 | 005550C0 | LightSourceClass::slot5 | PASS | PASS | **PASS** | PASS | **是** | 是 | 流读入 0x410380([eax+0xc])，E_POINTER 负值/成功 0 分支，方向未写反 |
| 14 | 00555110 | LightSourceClass::slot6 | PASS | PASS | **PASS** | PASS | **是** | 是 | 流写出 0x410320([eax+0x10])，E_POINTER 负值/成功 0 分支，方向未写反 |
| 15 | 00555150 | LightSourceClass::slot8 | PASS | PASS | **PASS** | PASS | **是** | 是 | 析构摘链 Find -1+压缩循环，RTTI+行外 ctor |
| 16 | 00565C10 | DisplayClass::slot28 | PASS | PASS | FAIL | PASS | 否 | 否 | malloc 零判断+多间接 test→je 模板假句，无 falsifiable 返值 |
| 17 | 00567230 | DisplayClass::slot29 | PASS | PASS | FAIL | PASS | 否 | 否 | chA p3=0，call→test 动作签名相同 |
| 18 | 006DBD20 | Tactical::slot5 | PASS | PASS | **PASS** | PASS | **是** | 是 | 流读入 0x410380([eax+0xc])，E_POINTER 负值/成功 0 分支，方向未写反 |

## 三陷阱核查小结

- **①读写方向**：2 条流读入（005550C0 slot5、006DBD20 slot5，callee 0x410380 正路 `call [eax+0xc]`=Read）、1 条流写出（00555110 slot6，callee 0x410320 正路 `call [eax+0x10]`=Write）。逐字节核定，one_line_semantics 与实际方向一致，未写反。其余 15 行无流操作，方向 N/A。
- **② ④锚点落析构器(㉓)**：18 行 ④ 全部取得**行外构造器**装活表点（如 00420960/00435820/0048E740/004BA5A0/004A8730/00554760/006D1C20，均 `call 基类构造` 开头+字段初始化，atexit=False、无 free）；7 条 PASS 行本体内若出现析构器自装表（0042173D/004370C4/00491214/00555156）均按 ㉓ 排除、未作锚。**无一行 ④ 锚落在析构器**。
- **③小成员表 vtable**：18 行 RTTI 名串均与名字栏类名一致、slot offset/4==线索槽号、vt[slot]==entry；VT[0] 判读——9 行主表标志 00410260（AlphaShape/BuildingLight/LightSource/Tactical），ConvertClass/DSurface/DisplayClass 的 vt[0] 为本非 COM 根类的首方法（007E5358/007E85D4/007E6114，由行外 ctor 写对象 offset0=主表）。**ConvertClass 的 007E5318/007E5338 容器成员表明确排除**。无一行误把小成员表当主表。
- **③可伪证性**：4 条析构摘链行(00421730/004370C0/00491210/00555150)的 Find 失败码 -1 由被调体 `83 C8 FF`(or eax,-1) 字节伪证（Find 函数分别 00421A90/004E9DB0/0049B0B0/005554F0）；3 条流 I/O 行的失败码 0x80004003(E_POINTER) 由 0x410380/0x410320 空参分支字节伪证。均为多值/哨兵，非 {0,1} 布尔。

## 与 S04 败因对比

S04 的 73 个命中全部 `named=0`，②类身份物理不可得，36 行实测全败（② 取不到）。本批 18 行均有真名（`Class::slotN`/`Class::vslotN`），**② 真钉住 18/18**（主虚表/RTTI 名串/槽号三者自洽，且逐行排除小成员表陷阱）——可见"有名字"确实解除了 S04 的 ② 硬约束。但 ② 非充分：③ 成为独立门槛，本批 11 行栽在 ③（malloc 零判断/布尔 magic 比较/间接虚调用不可伪证/chA p3=0），与 S05/S06/S14 历批的 ③ 固有败因同型。最终 7 行四环齐全。

## 汇总（base_rate.tsv 权威口径）

- rows_checked：**18**
- ② 类身份钉住：**18**
- ③b 整体合同成立：**7**
- ④ 使用见证成立：**18**（④ 全取行外构造器装活表点，非析构器、非 direct-only、与 ② 不同源）
- 四环齐全：**7 / 18 = 0.3889**
- delta 产出 7 行 `[已证]`，evidence_path 各指本目录 `EVIDENCE/ROW_<entry>.txt`

## 产出四环齐全行（7）

00421730 / 004370C0 / 00491210 / 00555150（析构体内容器 Find -1 + 压缩摘链非栈写循环，4 行同族但各行容器全局/Find 函数/槽地址独立）；
005550C0 / 00555110 / 006DBD20（流 I/O E_POINTER 负值/成功 0 可伪证返回约定，3 行分别 slot5 读入 / slot6 写出 / slot5 读入）。

## 三陷阱与同族低信息量披露

- 4 条析构摘链行属「模板级低信息量 ③b②」（与 S05 00410C30/0041CFE0、S14 00691EE0、S20 00763200 同型），严格符合卡面「Find 返 -1 下标约定算」的字面要求；各行容器全局(88A0F0/B0F720/8B4190/89ECF8/ABCA10)、Find 函数(00421A90/004E0550/004E9DB0/0049B0B0/005554F0)、槽地址、RTTI 链均各自独立，非同一段 reason 复用。
- 3 条流 I/O 行方向已逐字节核定，未把读入写成写出（S14 006A48A0「方向写反」覆辙未犯）。

## work/ 清单

- `filter_b1.py`（筛选，可复算）→ `b1_rows.json`
- `recore.py` / `witness_core.py`（PE/capstone/RTTI/虚表底座，复制自 NAMED_PUSH_S05_B1）
- `analyze.py`（四环初筛+三陷阱标注）→ `analysis.json`
- `dump.py` / `dumpdis.py` / `sigdump.py` / `site_detail.py`（证据抽取与站点签名）
- `find_verify.py` / `find_verify2.py` / `find_verify3.py` + `*.txt`（容器活表→Find→`or eax,-1` 字节伪证）
- `ctor_check.txt` / `find_dump.txt` / `magic_check.txt`（构造器锚与主表/magic 常量核对）
- `finalize.py`（逐行裁定+产物生成）→ `verdicts.json`
- 全部脚本只读 gamemd.exe，写域仅本批次目录，可复算。
