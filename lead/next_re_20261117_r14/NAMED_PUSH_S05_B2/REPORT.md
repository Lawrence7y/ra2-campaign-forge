# NAMED-PUSH — S05 B2 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录、先写骨架、逐行核完即落盘 EVIDENCE；每 5 行追加 PROGRESS。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 80 行读完）。
> 本批：**B2** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S05` AND `p3b2_named==True`，**再排除地址式伪名 `fn_XXXXXXXX` / `sub_XXXXXXXX`**，按 entry 升序取**第 19 到第 36 个**（共 18 行）。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S05_B2\`（卡片 `<你的子系统>`=S05、`<你的目录>`=本目录）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`；`work/filter_b2.py` 现场复算一致。
- ImageBase `0x400000`；`.text=[0x401000,0x7E038D)`（VirtualSize）。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）。未改 coverage.tsv / PANEL.md / R14_COMMON.md / 台账 / SURVEY_3B2 下任何产物。写域仅本目录。

## 筛选命令（得到本批 18 个 entry）

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
batch = rows[18:36]               # 第 19 到第 36 个（1-indexed）
```

落盘于 `work/filter_b2.py`。结果：S05 named=True 共 39 行，排除 `fn_`/`sub_` 伪名后 **37** 行；B2 = 第 19–36 行。18 个 entry：

| # | entry | name(原样) | ②线索槽号 | ②RTTI钉住 | ③③b | ④ | 产出 |
|---:|---|---|---:|---|---|---|---|
| 19 | 00459900 | BuildingClass::slot282 | 282 | PASS | FAIL(malloc模板) | PASS | 否 |
| 20 | 00459C20 | BuildingClass::slot219 | 219 | PASS | FAIL(无站点) | PASS | 否 |
| 21 | 00523B10 | InfantryTypeClass::slot35 | 35 | PASS | FAIL(malloc模板) | PASS | 否 |
| 22 | 00523B40 | InfantryTypeClass::slot32 | 32 | PASS | FAIL(malloc模板) | PASS | 否 |
| 23 | 005240A0 | InfantryTypeClass::slot25 | 25 | PASS | FAIL({0}布尔探测) | PASS | 否 |
| 24 | 00524D70 | InfantryTypeClass::slot8 | 8 | PASS | **PASS(③b② -1哨兵+数组前移非栈写循环)** | PASS | **是** |
| 25 | 005F7900 | AircraftTypeClass::slot37 | 37 | PASS | FAIL(bool{0,1}) | PASS | 否 |
| 26 | 005F9950 | ObjectTypeClass::slot6 | 6 | PASS | **PASS(③b② E_POINTER HRESULT 负→原值/非负→0)** | PASS | **是** |
| 27 | 006F3F40 | FootClass::slot9 | 9 | PASS | FAIL(malloc模板/unknown) | PASS | 否 |
| 28 | 00703860 | TechnoClass::slot26 | 26 | PASS | FAIL(imm=6/100 非falsifiable) | PASS | 否 |
| 29 | 00704350 | TechnoClass::slot187 | 187 | PASS | FAIL(imm=1 bool/汇合) | PASS | 否 |
| 30 | 00712040 | AircraftTypeClass::slot38 | 38 | PASS | FAIL(无站点) | PASS | 否 |
| 31 | 007120D0 | AircraftTypeClass::slot44 | 44 | PASS | FAIL(imm=1 bool getter) | PASS | 否 |
| 32 | 007170A0 | AircraftTypeClass::slot7 | 7 | PASS | FAIL(无站点) | PASS | 否 |
| 33 | 007474B0 | UnitTypeClass::slot32 | 32 | PASS | FAIL(malloc模板) | PASS | 否 |
| 34 | 00747560 | UnitTypeClass::slot35 | 35 | PASS | FAIL(malloc模板) | PASS | 否 |
| 35 | 00748010 | UnitTypeClass::slot5 | 5 | PASS | FAIL({0}布尔探测) | PASS | 否 |
| 36 | 007480B0 | UnitTypeClass::slot6 | 6 | PASS | FAIL(无站点) | PASS | 否 |

## 判定口径（严格 D-40，宁严不宽）
1. **①入口**：18 行 entry 全部在 `.text` 内、atlas 边界自洽、skipdata=0。
2. **②类身份**：`[vt-4]=COL(sig=0)→[COL+0xC]=TD→TD+8 名串` 且 `vt[slot]==entry`、`slot offset/4 == 名字线索槽号`、RTTI 类名字串与 `Class::slotN` 的类名逐字一致。用 `work/resolve_rtti_b2.py`（kmax=600）钉死（高槽号 282/219/187 需扩展回扫；共享虚表的行按类名选对 vtable，如 005F7900 选 007E2868 AircraftTypeClass 而非同槽号的 VoxelAnimTypeClass）。`slotN` 里的类名仅作线索、已被 RTTI 独立钉死。② 走 .rdata RTTI 数据链。
3. **③整体合同**：只认 ③b。bool 0/1 不算（D-46(A)）；imm=6/100 等常量非 falsifiable 不算；禁 malloc 空判断模板假句、禁纯转发/getter、禁被调用者内部写充循环非栈写；须两路动作签名真不同、无 eax 覆写、非多路同一 call。
4. **④使用见证**：非 atexit 构造安装点写 vt 入活对象 + `[reg+off]` 派发链（.text），direct-only 不足，且与 ② 不同源（.rdata RTTI 链 vs .text 构造/派发链）。

## 基础率（诚实报数）
分母 = 本批 18 行。

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | 18 | S05 named=True 排除伪名后第 19–36 行 |
| ①入口 PASS | 18 | 全部在 .text、skipdata=0 |
| ②类身份取得（RTTI 独立钉死） | **18** | 18 行虚表槽驻留+RTTI 名串+slot 号自洽（含 3 个高槽号扩展回扫） |
| ③③b 成立 | **2** | 00524D70、005F9950（均 ③b②） |
| ④独立使用见证（活虚表派发） | **18** | 18 行均有非 atexit 构造安装点 + [reg+off] 派发链，与 ② 不同源 |
| **四环齐全（严格 D-40）** | **2** | 00524D70、005F9950 |

## 逐行裁定依据（每行自身地址锚，见 `EVIDENCE/ROW_<entry>.txt`）
- **② 钉住 18/18**：每行 entry 作为 4B VA 在非 .text 段命中虚表槽，回扫 `[vt-4]=COL(sig=0)→[COL+0xC]=TD→TD+8` 得 RTTI 名串，与名字线索类名逐字一致，`slot offset/4 == 线索槽号`。高槽号 282/219/187 由 kmax=600 扩展回扫钉死；共享虚表行（005F7900/006F3F40/00712040/007120D0/007170A0）按类名选对 vtable。
- **③ 成立仅 2 行**（各自地址详见自身 EVIDENCE）：
  - **00524D70**：`call [edx+0x10]@0x00524DAA (edx=[0xA8E348] 全局列表) → cmp eax,-1@0x00524DAD → je@0x00524DB0`。-1 未找到哨兵 falsifiable；je 路逐字段释放、不成立路边界检查 + `mov [0xA8E358],ecx` 非栈写 + 数组前移循环 `mov [ecx+eax*4-4],edx`（循环体非栈写 + jl 回边）。两路真不同、0 eax 覆写。与 B1 00410C30/0041CFE0 同构。
  - **005F9950**：`call 0x00410320@0x005F995F → test eax,eax@0x005F9964 → jl@0x005F9966`。被调 0x410320 NULL 入参返回 `0x80004003`(E_POINTER) 可伪证 HRESULT；jl 路原样保留负错误码 ret 0xc、不成立路 xor eax,eax 归一为 0。负→原值/非负→0 可逐条证伪、0 eax 覆写。
- **③ 其余 16 行 FAIL 分类**（每行详见自身 EVIDENCE，理由逐行独立）：
  - malloc 空判断模板假句：00459900、00523B10、00523B40、006F3F40(部分)、007474B0、00747560。
  - bool/NULL 探测（被调常量集仅 {0} 或空 / {0,1}）：00459C20(无站点)、005240A0、005F7900、00704350、00748010。
  - 非 falsifiable 常量：00703860(imm=6/100)、007120D0(imm=1 bool getter)。
  - 无 call->test->jcc 站点：00459C20、00712040、007170A0、007480B0。
- **④ 18 行全成立**：每行均有非 atexit 构造安装点（如 005237E8/005239A8、005F73D9/005F740B 等实测非 atexit 注册）+ `[reg+off]` 派发链（.text），与 ② 的 .rdata RTTI 链不同源。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住）
- S04 的 73 个命中全 `p3b2_named=0`（无名字）：entry 作为 4B VA 全镜像 0 命中、无虚表槽、无可安装 RTTI 链 ⇒ **② 物理不可得**，36 行实测全败。
- 本批 S05 named=True（已排除伪名）：名字来自 coverage 的 `Class::slotN`（线索），按 D-40 独立取证——**18/18 行的 ② 被 RTTI 描述符链独立钉死**（含 3 个高槽号扩展回扫、5 个共享虚表按类名选对），这是 S04 完全不具备的条件。S04 的系统性败因（② 取不到 + ④ direct-only）在本批不复现：② 18/18、④ 18/18。
- 结论：② 从 S04 的 0/18 变为本批的 **18/18**；proved 增量最终受 ③ 限制——只有 2 行的 ③b② 满足「可伪证错误码/哨兵 + 两路动作真不同 + 无 eax 覆写」。本批四环齐全 **2 行**。

## 汇总
- rows_checked：**18**
- ② 钉住行数：**18**
- ③b 成立行数：**2**
- ④ 成立行数：**18**
- all_four_rings（严格 D-40）：**2**
- delta 产出：**2 行**（00524D70、005F9950）
- 结论：② 在本批 18/18 全钉住（S04 败因不复现），③ 成为决定性瓶颈；按「宁严不宽、虚报不可接受」如实交 2 行。

## 输出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`
- `EVIDENCE/ROW_<entry>.txt` × 18（每行自身地址与字节）
- `work/`（filter_b2 / recore / witness_core / resolve_rtti_b2 / analyze / site_paths / summary3b / dump_focus / witness_check / witness_pass / gen_evidence 等脚本与中间 JSON/probe，全部只读目标、可复算）
