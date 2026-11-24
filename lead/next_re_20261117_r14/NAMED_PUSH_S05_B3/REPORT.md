# NAMED-PUSH — S05 B3 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录、先写骨架、逐行核完即落盘 EVIDENCE；本批仅 1 行（不足 5 行，"每 5 行追加 PROGRESS"节奏不适用，核完即落盘）。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 80 行读完）。
> 本批：**B3** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S05` AND `p3b2_named==True`，**再排除地址式伪名 `fn_XXXXXXXX` / `sub_XXXXXXXX`**，按 entry 升序取**第 37 到第 54 个**（1-indexed）。**S05 named-real 共 37 行，故 B3 只落第 37 行 1 行**（第 38–54 个不存在）。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S05_B3\`（卡片 `<你的子系统>`=S05、`<你的目录>`=本目录）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`；`work/filter_b3.py` 现场复算一致。
- ImageBase `0x400000`；`.text=[0x401000,0x7E038D)`（VirtualSize，实测 size=0x3DF38D）。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）、B2 批 `work/recore.py`+`witness_core.py`（只读复用核心库，未改 B2 任何产物）。未改 coverage.tsv / PANEL.md / R14_COMMON.md / 台账 / SURVEY_3B2 下任何产物。写域仅本目录。

## 筛选命令（得到本批 1 个 entry）

```python
import csv
p = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_3B2\hits_detail.tsv"
rows = []
with open(p, encoding="utf-8") as f:
    for row in csv.DictReader(f, delimiter="\t"):
        if row["subsystem"] == "S05" and row["p3b2_named"] == "True":
            n = row["name"]
            if n.startswith("fn_") or n.startswith("sub_"):
                continue          # 排除地址式伪名（② 物理不可得）
            rows.append(row)
rows.sort(key=lambda x: int(x["entry"], 16))
batch = rows[36:54]               # 第 37 到第 54 个（1-indexed）
# 结果 S05 named=True 共 39 行，排除 fn_/sub_ 伪名后仅 37 行（fn_ 伪名 2 个：00450630/004509D0）
# => rows[36:54] 只有 rows[36]，即 entry=00748190 UnitTypeClass::slot8
```

落盘于 `work/filter_b3.py`（含 SHA256 自校验）。筛选结果：S05 named=True 共 39 行，排除 2 个 `fn_` 伪名（00450630、004509D0；与 B1 曾误收的 00450630 同类）后 **37 行**；第 37–54 个只有第 37 行：

| # | entry | name(原样) | ②线索槽号 | ②RTTI钉住 | ③③b | ④ | 产出 |
|---:|---|---|---:|---|---|---|---|
| 37 | 00748190 | UnitTypeClass::slot8 | 8 | PASS | **PASS(③b② -1哨兵+数组前移非栈写循环)** | PASS | **是** |

## 判定口径（严格 D-40，宁严不宽）
1. **①入口**：entry 在 `.text` 内、atlas 边界自洽、skipdata=0；末条 ret 落在函数体内。本行 141B/42 指令、skipdata=0、body_end_in_text=True。
2. **②类身份**：`[vt-4]=COL(sig=0)→[COL+0xC]=TD→TD+8 名串` 且 `vt[slot]==entry`、`slot offset/4 == 名字线索槽号`、RTTI 类名与 `Class::slotN` 类名逐字一致。用 `work/resolve_rtti_b3.py`（kmax=600）独立钉死；`slotN` 类名仅作线索，已被 RTTI 独立证明。② 走 .rdata RTTI 数据链。
3. **③整体合同**：只认 ③b。可伪证错误码/返回约定（失败返回什么、成功返回什么、调用方真拿它分支）；两路动作真不同；循环内非栈写指令须在本函数体内（禁把被调用者内部写当循环非栈写）；禁 ③a（malloc 空判断/对象初始化/清零/纯转发/getter/无分支直线）；三陷阱（eax 覆写、多路同一 call、模板假句）全排查。
4. **④使用见证**：非 atexit 构造安装点写 vt 入活对象 + `[reg+off]` 派发链（.text），direct-only 不足，且与 ② 不同源（.rdata RTTI 数据链 vs .text 构造/派发链）。

## 基础率（诚实报数）
分母 = 本批 1 行。

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | 1 | S05 named=True 排除伪名后第 37–54 行（实际仅第 37 行） |
| ①入口 PASS | 1 | 在 .text、skipdata=0、边界自洽 |
| ②类身份取得（RTTI 独立钉死） | **1** | 槽 007F6238 驻留 entry，COL 0080CD28→TD 00845980→`.?AVUnitTypeClass@@`，slot#8 与线索一致 |
| ③③b 成立 | **1** | 00748190（③b② -1 哨兵+数组前移非栈写循环） |
| ④独立使用见证（活虚表派发） | **1** | 3 处非 atexit 构造安装点 + 358 处 [reg+0x20] 派发，与 ② 不同源 |
| **四环齐全（严格 D-40）** | **1** | 00748190 |

## 逐行裁定依据（地址自证，见 `EVIDENCE/ROW_00748190.txt`）
- **00748190 UnitTypeClass::slot8** —— 四环齐全：
  - ① entry=00748190 在 .text，141B/42 指令，skipdata=0，末条 `ret 4`@0x74821A 在 [0x748190,0x74821D) 内。
  - ② `.rdata` 槽 007F6238 实测 =00748190；回扫 COL 0080CD28(sig=0)→TD 00845980→name `.?AVUnitTypeClass@@`；slot offset +0x20/4=8=线索槽号，类名逐字一致。
  - ③ 站点 `call [edx+0x10]`@0x7481CA (FF 52 10) → `cmp eax,-1`@0x7481CD (83 F8 FF) → `je`@0x7481D0 (74 2D)，零间隔无 eax 覆写。-1（未找到哨兵）为 falsifiable 返回约定；je 成立路跳过摘链仅收尾释放，不成立路做边界检查 + `mov [0xA83CF0],ecx` 非栈写 + 数组前移循环 `mov [ecx+eax*4-4],edx`(89 54 81 FC)（循环体非栈写+jl 回边）。两路真不同、非 bool/模板/纯转发/多路同一 call。站点字节与 B2 已收 00524D70 逐字相同（同型 InfantryTypeClass::slot8 析构摘链逻辑）。
  - ④ vt 007F6218 由构造安装点 007471BF/0074803D/00748196（均非 atexit 注册）写入活对象；[reg+0x20] 派发链 358 处在 .text（抽样 00402A43 等均 ff5220）；direct callers=0（走活虚表派发）。② 与 ④ 不同源。
  - **裁定：①=②=③=④=PASS，四环齐全 -> [已证]，产出 delta 行。**

## 与 S04 的败因对比（本批有多少行 ② 真的钉住）
- S04 的 73 个命中全 `p3b2_named=0`（无名字）：entry 作为 4B VA 全镜像 0 命中、无虚表槽、无可安装 RTTI 链 ⇒ **② 物理不可得**，36 行实测全败。
- 本批 S05 named=True（已排除伪名）：名字来自 coverage 的 `Class::slotN`（线索），按 D-40 独立取证——**1/1 行的 ② 被 RTTI 描述符链独立钉死**（槽 007F6238 + COL 0080CD28 + TD 00845980 + 名串 `.?AVUnitTypeClass@@` + slot#8 自洽）。这是 S04 完全不具备的条件。S04 的系统性败因（② 取不到 + ④ direct-only）在本批不复现：② 1/1、④ 1/1。
- 结论：② 从 S04 的 0/36 变为本批的 **1/1**；本批 ③b② 亦成立（唯一行 00748190），故四环齐全 **1 行**，delta 产出 1 行。

## 汇总
- rows_checked：**1**
- ② 钉住行数：**1**
- ③b 成立行数：**1**
- ④ 成立行数：**1**
- all_four_rings（严格 D-40）：**1**
- delta 产出：**1 行**（00748190）
- 结论：本批 1 行四环全齐，按事实底座如实收 1 行 [已证]。未虚报。

## 输出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`
- `EVIDENCE/ROW_00748190.txt`（本行四环地址与字节）
- `work/`（filter_b3 / recore / witness_core / analyze / resolve_rtti_b3 / deep_probe / verify_witness 脚本与 b3_rows.json / analysis.json / rtti_map.json / resolve_out.txt，全部只读目标、可复算）
