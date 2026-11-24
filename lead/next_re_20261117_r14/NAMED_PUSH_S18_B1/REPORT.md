# NAMED-PUSH — S18 B1 批次（有名字的 ③b② 候选，攻 proved 增量）

> 状态：**完成**。执行纪律已遵：先建目录、先写骨架、逐行核完即落盘 EVIDENCE；每 5 行追加 PROGRESS。
> 卡片：`lead\next_re_20261117_r14\_cards\NAMED-PUSH.md`（全文 73 行读完）
> 本批：**B1** = `SURVEY_3B2\hits_detail.tsv` 中 `subsystem==S18` AND `p3b2_named==True` 的行按 entry 升序取**前 18 行**。
> 输出目录：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_S18_B1\`（卡片中 `<你的子系统>`=S18、`<你的目录>`=本目录）。

## 材料自校验
- 目标：`ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`；现场 `Get-FileHash` 复算一致。
- ImageBase `0x400000`；`.text=[0x401000,0x7E038D)`（VirtualSize）。
- Python 3.12.10 / capstone 5.0.7（**skipdata=True**）/ pefile 2024.8.26；无 venv、未 pip install、未用 Ghidra。
- 只读输入：`SURVEY_3B2\hits_detail.tsv`（仅当线索）。未改 coverage.tsv / PANEL.md / R14_COMMON.md / 台账 / SURVEY_3B2 下任何产物。写域仅本目录。

## 筛选命令（得到本批 18 个 entry）

PowerShell（在 R14 目录下执行）：

```powershell
$p = "SURVEY_3B2\hits_detail.tsv"
$rows = Import-Csv $p -Delimiter "`t"
$b1 = $rows | Where-Object { $_.subsystem -eq 'S18' -and $_.p3b2_named -eq 'True' } |
      Sort-Object { [Convert]::ToInt32($_.entry,16) } | Select-Object -First 18
$b1 | Format-Table entry,subsystem,name,grade,size,n_call,n_site,n_valid,p3b2_named -AutoSize
```

结果：S18 named=True 共 **82** 行；B1 = 前 18 行（entry 升序）。等价 Python 落盘于 `work/filter_b1.py`（`sorted([r for r in rows if r['subsystem']=='S18' and r['p3b2_named']=='True'], key=lambda x:int(x['entry'],16))[:18]`）。

## 判定口径（严格 D-40，宁严不宽）
1. **①入口**：entry 在 `.text` 内、函数边界自洽（atlas size + 反汇编连贯，skipdata=0）。
2. **②类身份**：必须独立取证——RTTI 描述符链 `[vt-4]=COL→[COL+0xC]=TD→TD+8 名串` 且 `vt[slot]==entry`。`Class::slotN` 的 `Class` 仅作线索，仍须 RTTI/虚表钉死；钉不死判 FAIL。
3. **③整体合同**：只认 ③b。本批实际命中全为 ③b②（call→test/cmp→jcc）；按 S15S16 已过审判据逐行核：被调返回须可伪证（imm 哨兵/错误码，**bool 0/1 不算** D-46(A)）、零间隔无 eax 覆写、两路动作真不同（非纯转发壳/getter，非 malloc+对象初始化模板假句，非多路同一 call 仅差参数）。
4. **④使用见证**：真实调用者或活虚表派发，direct-only 不足，且与 ② 不同源。本批 ② 走 `.data/.rdata` 的 RTTI 数据链，④ 走 `.text` 中构造器装活表 + `[reg+off]` 派发链，两链独立（与已过审 S15S16 7 行同构；区别于 S13-PUSH 6 行「④仅复述同一静态槽」的 FAIL 形态）。
5. **三陷阱**：eax 覆写、多路同一 call、模板假句——逐行排查。

## 基础率（诚实报数）

分母 = 本批 18 行（S18 named=True 的 ③b② 候选中 entry 最小的 18 个）。

| 档 | 行数 | 口径 |
|---|---:|---|
| 本批行数 | 18 | S18 named=True 候选 asc 前 18 |
| ①入口 PASS | 18 | 全部在 .text、反汇编连贯（skipdata=0） |
| ②类身份取得（RTTI 独立钉死） | **18** | 每行均有 RTTI 名串与线索类名一致，且 slot offset/4 == 线索槽号 |
| ③③b 成立（③b②） | **1** | 仅 005414C0；余为 bool/未知返回/getter/模板假句 |
| ④独立使用见证（活虚表派发） | **18** | 每行均有非 atexit 构造安装点 + [reg+off] 派发链 |
| **四环齐全（严格 D-40）** | **1** | 005414C0 |

## 本批 18 行总表（entry / ②③④ / 是否产出）

| # | entry | name(原样) | ①入口 | ②类身份 | ③③b | ④使用见证 | ②④独立 | 裁定 | 产出 |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | 0048BF40 | ConnectionClass::slot2 | PASS | PASS(.?AVConnectionClass@@) | FAIL(bool 0/1+纯转发壳) | PASS(活vt+direct) | 是 | 不成立 | 否 |
| 2 | 0048C040 | ConnectionClass::slot3 | PASS | PASS(.?AVConnectionClass@@) | FAIL(被调 bool/unknown) | PASS(活vt+direct) | 是 | 不成立 | 否 |
| 3 | 0048C320 | ConnectionClass::slot4 | PASS | PASS(.?AVConnectionClass@@) | FAIL(返回源 unknown) | PASS(活vt+direct) | 是 | 不成立 | 否 |
| 4 | 0048C3B0 | ConnectionClass::slot5 | PASS | PASS(.?AVConnectionClass@@) | FAIL(纯转发 ret0/1) | PASS(活vt) | 是 | 不成立 | 否 |
| 5 | 004A0630 | ConnectionPointClass::slot5 | PASS | PASS(.?AVConnectionPointClass@@) | FAIL(p3=0) | PASS(活vt) | 是 | 不成立 | 否 |
| 6 | 0053FCB0 | IPXGlobalConnClass::slot12 | PASS | PASS(.?AVIPXGlobalConnClass@@) | FAIL(p3=0) | PASS(活vt) | 是 | 不成立 | 否 |
| 7 | 0053FF10 | IPXGlobalConnClass::slot13 | PASS | PASS(.?AVIPXGlobalConnClass@@) | FAIL(被调 unknown) | PASS(活vt) | 是 | 不成立 | 否 |
| 8 | 0053FFA0 | IPXGlobalConnClass::slot14 | PASS | PASS(.?AVIPXGlobalConnClass@@) | FAIL(被调 unknown) | PASS(活vt) | 是 | 不成立 | 否 |
| 9 | 00540050 | IPXGlobalConnClass::slot9 | PASS | PASS(.?AVIPXGlobalConnClass@@) | FAIL(bool 0/1) | PASS(活vt) | 是 | 不成立 | 否 |
| 10 | 005414C0 | IPXManagerClass::slot2 | PASS | PASS(.?AVIPXManagerClass@@) | **PASS(③b② -1 哨兵)** | PASS(活vt) | 是 | **成立** | **是** |
| 11 | 00541820 | IPXManagerClass::slot1 | PASS | PASS(.?AVIPXManagerClass@@) | FAIL(null/bool 探测无错误码) | PASS(活vt+direct37) | 是 | 不成立 | 否 |
| 12 | 00542350 | IPXManagerClass::slot9 | PASS | PASS(.?AVIPXManagerClass@@) | FAIL(getter ③a) | PASS(活vt) | 是 | 不成立 | 否 |
| 13 | 005423C0 | IPXManagerClass::slot10 | PASS | PASS(.?AVIPXManagerClass@@) | FAIL(getter ③a) | PASS(活vt) | 是 | 不成立 | 否 |
| 14 | 005C18A0 | MPCooperative::slot4 | PASS | PASS(.?AVMPCooperative@@) | FAIL(malloc 模板假句) | PASS(活vt) | 是 | 不成立 | 否 |
| 15 | 005C1A10 | MPCooperative::slot8 | PASS | PASS(.?AVMPCooperative@@) | FAIL(bool/unknown) | PASS(活vt) | 是 | 不成立 | 否 |
| 16 | 005C1DC0 | MPCooperative::slot6 | PASS | PASS(.?AVMPCooperative@@) | FAIL(malloc 模板假句) | PASS(活vt) | 是 | 不成立 | 否 |
| 17 | 005C2100 | MPCooperative::slot23 | PASS | PASS(.?AVMPCooperative@@) | FAIL(返回源 unknown) | PASS(活vt) | 是 | 不成立 | 否 |
| 18 | 005C2680 | MPCooperative::slot24 | PASS | PASS(.?AVMPCooperative@@) | FAIL(多路同一 call+unknown) | PASS(活vt) | 是 | 不成立 | 否 |

## 逐行裁定依据（每行自身地址锚，见 `EVIDENCE/ROW_<entry>.txt`）

- **② 全数钉住（18/18）**：每行 entry 作为 4B VA 在 `.rdata` 命中虚表槽，回扫 `[vt-4]=COL(sig=0)→[COL+0xC]=TD→TD+8` 得到 RTTI 名串，与 name 线索类名逐字一致；且 `slot offset / 4 == 线索槽号`（如 005414C0 offset+8→slot2、0053FCB0 offset+48→slot12、005C2680 offset+96→slot24），证明名字不是凭 slotN 猜的，而是被虚表+RTTI 独立钉死。这是与 S04 的决定性差异。
- **③ 唯一成立 = 005414C0**：`call [edx+0x18]@0x0054159B` 调到 0x00541040，后者 `mov eax,0xffffffff;ret@0x00541066` 失败返回 -1；本体零间隔 `cmp eax,-1@0x0054159E; je@0x005415A1`。失败路 `inc dword [esi+0xA0]@0x005415D6`（非栈写）后 `xor eax,eax;ret 0x10`；成功路查表 `[esi+eax*4+0x28]` 并 `call [eax+8]@0x005415C7` 实发送后 `mov eax,1;ret 0x10`。两路动作真不同、无 eax 覆写、非 bool、非纯转发、非模板假句。与 S15S16 过审的 `006E4660`（call [reg]→cmp eax,-1→je→两路动作真不同）同构。
- **③ 其余 17 行 FAIL 分类**（每行详见自身 EVIDENCE，理由逐行独立）：
  - bool 主输出 / 纯转发壳：0048BF40、0048C3B0、00540050（D-46(A) bool 不算 ③b②；两路汇同一 ret 仅 eax 常量不同）。
  - 被调返回源 unknown / 单 ret 无 imm 哨兵：0048C040、0048C320、0053FF10、0053FFA0、0053FFA0、00541820、005C1A10、005C2100、005C2680。
  - p3=0（无可伪证站点）：004A0630、0053FCB0。
  - ③a getter 纯转发：00542350、005423C0。
  - malloc 空判断 + 对象初始化模板假句：005C18A0、005C1DC0。
  - 多路同一 call（细则#1）：005C2680。
- **④ 全数成立但不足以单独升级**：18 行均有非 atexit 构造安装点（如 005414C0 的 005408F7 `mov [esi],0x7EC16C` 已字节复核）+ `[reg+off]` 派发链；0048BF40/0048C040/0048C320 有 direct caller（00540624/0054063A/0054065A），00541820 有 37 个 direct caller，但按「direct-only 不足」不作为独立升级依据。②④ 来源不同（②=.data RTTI 链；④=.text 构造安装/派发链）。

## 与 S04 的败因对比（本批有多少行 ② 真的钉住）

- S04 的 73 个命中 `p3b2_named=0`（全无名字）：entry 作为 4B VA 全镜像 0 命中、无虚表槽、无可安装 RTTI 链 ⇒ **② 物理不可得**，36 行实测全败、B1/B2 共 36 行四环 0。
- 本批 S18 named=True：名字来自既有 coverage 的 `Class::slotN`（线索），但**按 D-40 须独立取证**——本批 **18/18 行的 ② 都被 RTTI 描述符链独立钉死**（虚表槽驻留 + RTTI 名串 + slot 号自洽），这是 S04 完全不具备的条件。
- 结论：② 从 S04 的 0/18 变为本批的 **18/18**；但 proved 增量最终受 ③ 限制——只有 1 行（005414C0）的 ③b② 满足「非 bool 可伪证哨兵 + 两路动作真不同」。本批 ② 真钉住 18 行，四环齐全 1 行。

## 汇总
- rows_checked：**18**
- ② 钉住行数：**18**
- all_four_rings（严格 D-40）：**1**
- delta 产出：**1 行**（005414C0）
- 结论：本批 18 行 ② 全数钉住（S04 败因在此批不复现），③ 成为决定性瓶颈；按「宁严不宽、虚报不可接受」如实交 1 行。

## 输出清单
- `REPORT.md`（本文件）、`PROGRESS.md`、`base_rate.tsv`、`delta.tsv`
- `EVIDENCE/ROW_<entry>.txt` × 18（每行自身地址与字节）
- `work/`（取证脚本 filter/analyze/summary/dump_sites/verify_strong/gen_evidence/verify_dtor 与中间 JSON，全部只读目标、可复算）
