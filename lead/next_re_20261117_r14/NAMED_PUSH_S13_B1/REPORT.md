# REPORT — NAMED-PUSH S13 B1

## 身份 / 目标

- 批次：`S13_B1`（子系统 S13，第 1 批；候选全部 10 行，不足 18 按实际数量）
- 目标二进制：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
- 期望 SHA-256：`73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（现场复算一致）
- ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`
- 工具：Python 3.12.10 + capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26
- 判定口径：D-40 四环（① 入口 / ② 类身份独立 / ③b 整体合同 / ④ 使用见证且与 ② 不同源），外加三陷阱与 ㉓（④ 锚点落析构器判 FAIL）、小成员表 vtable 不是主虚表。
- ③b② 可伪证性口径：多值状态码（如 E_POINTER 0x80004003）/ `Find` 返 `-1` 下标约定算；分配 NULL 返回约定算（失败返 0/成功返指针，非布尔状态位）；`{0,1}` 布尔 / 零值单常量不算。

## 筛选命令（卡面要求写进报告）

```powershell
# hits_detail.tsv: subsystem == S13 且 p3b2_named == True，排除地址式伪名 fn_/sub_，entry 升序取全部
python _work/filter_b1.py
```

`_work/filter_b1.py` 的筛选表达式：

```python
s13_all = [r for r in rows if r["subsystem"] == "S13"]
named   = [r for r in s13_all if r["p3b2_named"] == "True"]
PSEUDO  = re.compile(r"^(fn_|sub_)[0-9A-Fa-f]{8}$")      # 地址式伪名
sel     = [r for r in named if not PSEUDO.match(r["name"])]
sel.sort(key=lambda r: int(r["entry"], 16))              # entry 升序
```

结果：`S13 total=13`，`p3b2_named==True` 共 **10** 行，其中 `fn_`/`sub_` 伪名 **0** 行（S13 无地址式伪名），入选 **10** 行（全部，不足 18 按实际数量）。

## 候选表（按 entry 升序）

| # | entry | name | hits grade | size | ② | ③b | ④ | 产出 |
|---:|---|---|---|---:|:-:|:-:|:-:|:-:|
| 1 | 004684E0 | BulletClass::slot10 | [静态推断] | 392 | OK | OK（Find -1） | OK | **[已证]** |
| 2 | 00468670 | BulletClass::slot124 | [静态推断] | 1304 | OK | FAIL | OK | — |
| 3 | 0046C6A0 | BulletTypeClass::slot5 | [静态推断] | 134 | OK | FAIL | OK | — |
| 4 | 0046C730 | BulletTypeClass::slot6 | [静态推断] | 29 | OK | FAIL（③a 纯转发） | OK | — |
| 5 | 00629FD0 | ParasiteClass::slot23 | [静态推断] | 645 | OK | OK（分配 NULL） | OK | **[已证]** |
| 6 | 00708080 | death_handler | [未证] | 1846 | FAIL | FAIL（{0,1} 布尔） | FAIL | — |
| 7 | 0075E0C0 | WarheadTypeClass::slot5 | [静态推断] | 501 | OK | OK（E_POINTER） | OK | **[已证]** |
| 8 | 0075E2C0 | WarheadTypeClass::slot6 | [静态推断] | 225 | OK | OK（E_POINTER） | OK | **[已证]** |
| 9 | 00772CD0 | WeaponTypeClass::slot5 | [静态推断] | 476 | OK | OK（E_POINTER） | OK | **[已证]** |
| 10 | 00772EB0 | WeaponTypeClass::slot6 | [静态推断] | 225 | OK | OK（E_POINTER） | OK | **[已证]** |

## 四环判定口径（本批执行细则）

- **① 入口**：地址在 `.text` 内、atlas 函数边界自洽（取该 entry 的 atlas size 反汇编）。
- **② 类身份**：`vt[slot]==entry` + `vt-4 → COL(sig=0) → TD → name(.?AV...@@)` 链；`slotN` 里的类名只作线索，须由 RTTI/虚表钉死；核对槽号与 slotN 一致；排除"小成员表 vtable"（只证了内嵌子对象而非主类表）。
- **③b**：只认 ③b①/②/③/④；③b② 要可伪证（多值错误码 / `Find` -1 约定 / 分配 NULL 约定）且调用方拿返回值真分支、两路动作不同；禁 ③a（纯转发 / 零+默认 / 单调用+单写）；禁"被调用者内部的写"当循环内非栈写。
- **④ 使用见证**：构造器装活表的 `.text` 写点（`mov [reg],vt`，宿主函数有基类构造调用、非 atexit、非析构器、写点在行外）或真实 direct call；direct-only 不足；**与 ② 不同源**（② 用 `.rdata` 槽/RTTI 链，④ 用 `.text` 构造写点 ⇒ 不同源；若 ④ 仍是同一 `vt[slot]` 引用 ⇒ FAIL）。
- **㉓**：④ 锚点若落 `push <dtor>; call 0x7C978A` 注册的析构器、或宿主函数有 `call 0x7258D0` / `call 0x7C8B3D` + `cmp eax,-1` 摘链（析构特征）⇒ FAIL。
- **三陷阱**：`eax` 覆写（test 后分支前 `mov eax,[...]`）、多路同一 call、模板假句（对象初始化/清零式）。

## 逐行结论摘要（每行独立地址，无整批共用 reason）

| entry | ② 锚点 | ③b 形态与锚 | ④ 锚点（构造器 + 写点） | 裁定 |
|---|---|---|---|---|
| 004684E0 | slot@007E470C, vt=007E46E4 #10, COL=007FC7B0→.?AVBulletClass@@ | ③b② `call [eax+0x10]@46862A → cmp eax,-1@46862D → je@468630 → 46865F` | ctor 00466380（00466384 call 005F3900）→ `@00466425` | 四环齐 |
| 00468670 | slot@007E48D4, vt=007E46E4 #124, .?AVBulletClass@@ | 4 站点全无多值约定（al 布尔 / 返常量 0 / 间接 call / 无失败常量） | 同 vt 构造器存在 | ③ FAIL |
| 0046C6A0 | slot@007E495C, vt=007E4948 #5, .?AVBulletTypeClass@@ | 005F9720 返仅 0 + 主体模板假句（4 表 + 3×006CF240） | ctor 0046BBC0 → @0046BCE6（行内/析构锚已排除） | ③ FAIL |
| 0046C730 | slot@007E4960, vt=007E4948 #6, .?AVBulletTypeClass@@ | ③a 纯转发：005F9950 已归一化，本行再幂等归一 | ctor 0046BBC0 → @0046BCE6 | ③ FAIL |
| 00629FD0 | slot@007EF8EC, vt=007EF890 #23, .?AVParasiteClass@@ | ③b② `call new@62A0D8 → test@62A0E0 → je@62A0E2 → 62A108`（NULL 约定） | ctor 00629210（00629213 call 00410170）→ `@00629231` | 四环齐 |
| 00708080 | 无 vtable slot / 无 RTTI（仅 3 direct caller） | `cmp eax,1@708141 → jne@708144`（{0,1} 不算） | 仅 direct（不足） | ②③④ FAIL |
| 0075E0C0 | slot@007F6B44, vt=007F6B30 #5, .?AVWarheadTypeClass@@ | ③b② `call 00410380@75E0F0 → test@75E0F5 → jl@75E0F7 → 75E2AE`（E_POINTER） | ctor 0075CEC0（0075CECB call 00410800）→ `@0075D0BA` | 四环齐 |
| 0075E2C0 | slot@007F6B48, vt=007F6B30 #6, .?AVWarheadTypeClass@@ | ③b② `call 00410320@75E2D1 → test@75E2D6 → jl@75E2D8 → 75E39C`（E_POINTER，写方向） | ctor 0075CEC0 → `@0075D0BA` | 四环齐 |
| 00772CD0 | slot@007F73CC, vt=007F73B8 #5, .?AVWeaponTypeClass@@ | ③b② `call 00410380@772CFD → test@772D02 → jl@772D04 → 772EA6`（E_POINTER，读方向） | ctor 00771C70（00771C7A call 00410800）→ `@00771E77` | 四环齐 |
| 00772EB0 | slot@007F73D0, vt=007F73B8 #6, .?AVWeaponTypeClass@@ | ③b② `call 00410320@772EC1 → test@772EC6 → jl@772EC8 → 772F8C`（E_POINTER，写方向） | ctor 00771C70 → `@00771E77` | 四环齐 |

## 与 S04 的败因对比

卡面背景：S04 的 73 个 ③b② 命中全部无名字（named=0），36 行实测全败的根因是 **② 类身份取不到**。

本批 S13 的对比读数：

- **② 真正钉住：9 / 10 行**（仅 `00708080 death_handler` 无 vtable slot / 无 RTTI）。其中 8 行是 `Class::slotN`（类名由 `vt-4 → COL → TD → .?AV<Class>@@` 数据链独立钉死，槽号与 slotN 自洽），1 行 `0046C730` 同理。**② 的取法与 S04 完全相反**：S13 named 候选几乎全部能从 RTTI 数据链取得类身份，② 不是本批瓶颈。
- 本批的实际瓶颈是 **③b**：4 / 10 行在 ③b 失败（00468670 无可伪证多值约定、0046C6A0 模板假句 + 零值布尔、0046C730 ③a 纯转发、00708080 {0,1} 布尔）。
- ④：9 / 10 行具备行外构造器安装点（唯一例外 `00708080` 仅 direct call）。**㉓ 主动排查命中**：多个 vtable 的 install 集合里确有析构器写点（`0046C896`/`0062AF70`/`0075E516`/`007730F7` 均含 `call 007258D0` 或 `call 007C8B3D` + `cmp eax,-1` 摘链），本批 ④ 一律避开这些、只点真构造器写点；`004684E0`/`0075E0C0` 还出现"行内写点"（@0046C6C4/@0075E13E），已按"写点在行外"排除。
- 小成员表陷阱：所有 9 行 ② 的 RTTI 名串即候选名里的 `Class`，且 install 点是写 `[esi]`/`[ebp]` 主 vptr（`vt` 基址），未发现"仅小成员表"情形。

**结论**：S04 是"② 物理不可得导致全败"；S13 是"② 易得、③b 是主要淘汰环节、④ 需绕过 ㉓/行内写点"。两者败因不同，S13 不是 S04 同型。

## ⚠ 与 R14_COMMON §12.3 的口径张力（必须披露，供 Lead 裁定）

`R14_COMMON.md` §12.3（COMMON-REFRESH-2）记载：S13_PUSH 的 6 行（004684E0 / 00629FD0 / 0075E0C0 / 0075E2C0 / 00772CD0 / 00772EB0）④ 与 ② "共用同一虚表槽"，Lead 裁定不予并表；§12.4 据此给出"S13 严格口径可并 0"的负结果。

本批对这同样的 6 行给出不同裁定，理由是**证据结构不同**，须由 Lead 复核：

- S13_PUSH 的 ④ 原文自标「⚠ 环②与环④共用同一 vtable 槽」，其 ④ 直接说"槽 +20 驻本 entry"——即把同一条 `.rdata` 槽引用既当 ② 又当 ④，这是 §12.3 禁止的同源。
- 本批 6 行的 ④ 全部改为 **`.text` 构造期写点**：`mov [reg],vt` 指令，宿主函数有基类构造调用、非 atexit、非析构、写点在行外；② 仍用 `.rdata` 槽 + RTTI 数据链。两条证据来自不同段（`.rdata` 数据 vs `.text` 指令）、不同 artifact。
- 这一"② 用 RTTI 数据链 / ④ 用 `.text` 构造写点 ⇒ same_source=no"的判法，与本批同族的 `NAMED_PUSH_AUDIT2\verdict.tsv`（S14_B2/S05 共 11 行异族审计）判例一致——该审计对 ②=虚表槽+RTTI、④=ctor `mov [esi],vt` 的 10 行全部裁 `same_source=no` 且 PASS。
- 若 Lead 坚持 §12.3 的更严读法（"只要 ④ 与 ② 涉及同一张 vt 即算同源"），则本批 6 行应整体翻为 ④ FAIL，delta 变 0、base_rate 变 `10 9 6 9 0 0.0000`，且与同族 S14_B2/S05 的审计判例冲突。此点未擅自并入 `coverage.tsv`，只在报告披露。

## 产出清单

- `delta.tsv`：6 行（四环齐全，grade `[已证]`；entry 大写无 `0x`；evidence_path 指向各自 EVIDENCE）
- `base_rate.tsv`：`S13_B1  10  9  6  9  6  0.6000`
- `EVIDENCE/ROW_<entry>.txt` × 10（含未入选 4 行的否决理由，每行自身地址）
- `PROGRESS.md`、`REPORT.md`（本文件）
- `_work/`（筛选/反汇编/取证脚本与中间 JSON/TXT）

未触碰 `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账、`SURVEY_3B2`、`S04_PUSH_*`；只写本批目录。
