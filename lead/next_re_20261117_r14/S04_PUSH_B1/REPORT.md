# S04-PUSH — B1 批次（攻 S04 的 proved 增量，候选第 1–18 行）

> 状态：**完成**。执行纪律已遵：先建目录、先写骨架、逐行核完即落盘 EVIDENCE；每 5 行追加 PROGRESS。
> 卡片：`lead\next_re_20261117_r14\_cards\S04-PUSH.md`（全文 76 行读完）
> 本批：**B1** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S04` 的 73 行按 entry 升序取**前 18 行**（1-based 第 1–18，0-based `[0,18)`）。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S04_PUSH_B1\`（卡片中的 `S04_PUSH_B1` 一律指本目录）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`；现场 `Get-FileHash` 复算一致（size=4,825,360 B）。
- ImageBase `0x400000`；`.text=[0x401000,0x7E038D)`（VirtualSize）。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install、未用 Ghidra。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）。未改 coverage.tsv / PANEL.md / R14_COMMON.md / 台账 / SURVEY_3B2 下任何产物。写域仅本目录。

## 筛选命令（得到本批 18 个 entry）

PowerShell（在 R14 目录下执行）：

```powershell
$p = "SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$s04 = $rows | Where-Object { $_.subsystem -eq 'S04' }
$b1  = $s04 | Sort-Object { [Convert]::ToInt32($_.entry,16) } | Select-Object -First 18
$b1 | Format-Table entry,subsystem,name,grade,size -AutoSize
```

结果：S04 共 **73** 行；B1 = 前 18 行（entry 升序）。等价 Python 落盘于 `work/filter_b1.py`（逻辑：`sorted([r for r in rows if r['subsystem']=='S04'], key=lambda x:int(x['entry'],16))[:18]`）。

## 判定口径（严格，宁严不宽；S04 余量仅 6 行）
1. **①入口**：entry 在 `.text` 内、函数边界自洽（atlas size + 反汇编连贯）。
2. **②类身份**：RTTI 名 / 虚表归属 / 构造链；**取不到写 `未取得` 并判该行不成立**。
3. **③整体合同**：只认 ③b（③b② 可伪证错误码/返回约定且调用方真分支；③b① 跳转表；③b③ 内存形状；③b④ 完整循环 I/O 带边界检查且循环体内有非栈写）。禁 ③a；禁「被调用者内部的写」当循环内非栈写；禁模板假句。
4. **④使用见证**：真实调用者或活虚表派发；**direct-only 不足**。
5. **D-40 新禁则**：② 与 ④ 必须来自两条**独立**证据链；同一虚表槽不能既证明类身份又证明被使用。
6. 三陷阱主动排查：`eax` 覆写；多路同一 call（仅参数不同）；模板假句。
7. 每行必须有自身地址锚，禁止整批共用 reason；类名取不到写 `未取得`，不许编。

## 基础率（诚实报数）

分母 = 本批 18 行（S04 ③b② 机械候选中 entry 最小的 18 个）。

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | 18 | S04 候选 asc 前 18 |
| ①入口 PASS | 18 | 全部在 .text、解码连贯（skipdata=0） |
| ③b② 可伪证形态成立（无 eax 陷阱） | 17 | 00407550 无 falsifiable 站点；其余 17 行 p3≥1、eax 覆写未触发 |
| ②类身份取得（RTTI/vt/构造链） | **0** | 18 行 entry 作为 4B VA 全镜像 0 命中；无 mov[this],vt；无独立构造链 |
| ④独立使用见证（非 direct-only） | **0** | 全部仅 direct E8 caller；无虚表派发（因 entry 不在任何虚表槽） |
| **四环齐全（严格 D-40）** | **0** | ②、④ 均缺 |

> 说明：④ 的 direct caller 全部为 capstone 指令边界核实的真实 E8（`raw==boundary`，逐行相等），但按卡片「direct-only 不足」与 D-40「不得据 direct call 单独升 [已证]」，不构成独立第 4 环。② 三通道全灭是决定性拦截。

## 本批 18 行总表（entry / ① / ② / ③ / ④ / 独立 / 裁定 / 是否产出）

| # | entry | name(原样) | ①入口 | ②类身份 | ③③b | ④使用见证 | ②④独立 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | 00407550 | sub_00407550 | PASS | 未取得 | 不成立(无 falsifiable 站点) | direct-only(1) | n/a | **不成立** | 否 |
| 2 | 00412610 | sub_00412610 | PASS | 未取得 | ③b②成立 | direct-only(2) | n/a | **不成立** | 否 |
| 3 | 0045DD50 | sub_0045DD50 | PASS | 未取得 | ③b②成立 | direct-only(1) | n/a | **不成立** | 否 |
| 4 | 00473980 | sub_00473980 | PASS | 未取得 | ③b②成立 | direct-only(1) | n/a | **不成立** | 否 |
| 5 | 00474810 | sub_00474810 | PASS | 未取得 | ③b②成立 | direct-only(2) | n/a | **不成立** | 否 |
| 6 | 00475D70 | sub_00475D70 | PASS | 未取得 | ③b②成立 | direct-only(60) | n/a | **不成立** | 否 |
| 7 | 00476340 | sub_00476340 | PASS | 未取得 | ③b②成立 | direct-only(1) | n/a | **不成立** | 否 |
| 8 | 00476420 | sub_00476420 | PASS | 未取得 | ③b②成立 | direct-only(8) | n/a | **不成立** | 否 |
| 9 | 004764F0 | sub_004764F0 | PASS | 未取得 | ③b②成立 | direct-only(1) | n/a | **不成立** | 否 |
| 10 | 004767C0 | sub_004767C0 | PASS | 未取得 | ③b②成立(2 站点) | direct-only(1) | n/a | **不成立** | 否 |
| 11 | 00476B20 | sub_00476B20 | PASS | 未取得 | ③b②成立 | direct-only(1) | n/a | **不成立** | 否 |
| 12 | 00477440 | sub_00477440 | PASS | 未取得 | ③b②成立(3 站点) | direct-only(1) | n/a | **不成立** | 否 |
| 13 | 0048DE70 | sub_0048DE70 | PASS | 未取得 | ③b②成立 | direct-only(1) | n/a | **不成立** | 否 |
| 14 | 0048DF30 | sub_0048DF30 | PASS | 未取得 | ③b②成立 | direct-only(3) | n/a | **不成立** | 否 |
| 15 | 0048DF80 | sub_0048DF80 | PASS | 未取得 | ③b②成立 | direct-only(1) | n/a | **不成立** | 否 |
| 16 | 004F1CA0 | sub_004F1CA0 | PASS | 未取得 | ③b②成立(3 站点) | direct-only(1) | n/a | **不成立** | 否 |
| 17 | 0051FB00 | sub_0051FB00 | PASS | 未取得 | ③b②成立(11 站点) | direct-only(1) | n/a | **不成立** | 否 |
| 18 | 0051FEF0 | sub_0051FEF0 | PASS | 未取得 | ③b②成立 | direct-only(1) | n/a | **不成立** | 否 |

## 逐行裁定依据（每行自身地址锚，见 `EVIDENCE/ROW_<entry>.txt`）

- **② 全灭（决定性）**：18 行 entry 作为 4 字节 VA 在**全镜像 8 个 section 逐字节扫描**（`work/verify2.py`，含非对齐）命中均为 **0** —— 没有一行是任何虚表的槽值，故 RTTI 链 `[vt-4]=COL→TD→名` 与「虚表归属」通道物理不可用。逐行 `mov [this],vt` 构造写=0（`work/verify5.py`），无一行是本类构造器。局部/服务对象 vtable 立即数（如 00475D70 的 `TypeList<int>`/`VectorClass<int>`、004F1CA0 的 `GraphicMenu`/`CCFileClass`）均为函数体内局部对象的构造写，不是本函数所属类的身份证据；按卡「类名取不到写未取得，不许编」。
- **构造链咽喉复核（S17_ENGFAM 法）**：`work/verify6.py` 全 `.text` 扫 `C7 05 <global>,<vt>` 只发现 0051FB00 引用全局 `0x87F7E8`；但 (a) 该全局为多态别名（S06-K1：最终动态对象 PowerClass，另有 MouseClass/DisplayClass/MapClass 写入），(b) 仅 3 处 `mov ecx,0x87f7e8` 单点引用，不满足 §8.8 条2「≥2 项字节吻合」与 D-42 细则3「禁单点推断」→ 不立类身份。
- **调用方交付 this 复核**：`work/verify5.py` 的窗口候选（00475D70 4 处、00476B20 1 处）经 `work/verify8.py` 手工反汇编证伪 —— `mov ecx,reg` 均属 call 本行之前另一条 call 的实参设置，到 call 本行时 ecx 已改写，且这些行序言用 ecx=False，局部 vtable 对象从未作为 this 交付。
- **③ 形态**：17 行有可伪证 ③b② 站点（call→test/or/cmp eax→jcc，动作签名不同，哨兵 0 / -1，eax 覆写陷阱未触发，见各行 EVIDENCE 环③）；00407550 的机械站点 P3=0（无可伪证返回约定）→ ③ 不成立。通道 B（跳转表）本批 0 行。
- **④ 全为 direct-only**：18 行 direct E8 caller 数分别 1/2/1/1/2/60/1/8/1/1/1/1/1/3/1/1/1/1，均经 capstone 指令边界复核（`raw==boundary`，`work/verify7.py`）；但无虚表派发链（entry 不在任何虚表槽），按卡片「direct-only 不足」判 ④ 不成立。

## 汇总
- rows_checked：**18**
- all_four_rings（严格 D-40）：**0**
- delta 产出：**0 行**（`S04_delta.tsv` 仅表头）
- 结论：本批 18 行**无一行四环齐全**；决定性缺环为 ②（类身份全不可得），④ 亦仅 direct-only。按「宁严不宽」不凑数，如实交 0 行。

## 输出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`
- `S04_delta.tsv`（表头 + 0 数据行）
- `EVIDENCE/ROW_<entry>.txt` × 18（每行自身地址与字节，含未入选行否决理由）
- `work/`（取证脚本 analyze/verify2..8/gen_evidence 与中间 JSON，全部只读目标、可复算）
