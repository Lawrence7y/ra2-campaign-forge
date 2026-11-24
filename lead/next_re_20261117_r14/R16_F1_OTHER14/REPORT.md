# R16-F1-OTHER14 · 14 行「真·无 ④」补 ④ 使用见证 · 执行报告

> 角色：执行器 `work/cn:hy4flash-free` · 日期 2026-11-21（R16 第 17 轮）· **14 行**
> 写域：`lead\next_re_20261117_r14\R16_F1_OTHER14\`（仅此目录；未写 `COVERAGE\coverage.tsv`）
> 清单来源：`R16_PROBE_F1_PIVOT\other14.tsv`（14 行，逐行复核，未照抄）
> 形态：2 行 `sem_live_table_install` → **direct call 形态**；12 行 `sem_virtual_witness_only` → **槽位见证形态**
> 披露节号：**§12.6**（D-47(A) 让位后重号；每行 ④ 自带 D-47 披露指针，均不含 §12.4）

---

## 0. 一句话结论

**14/14 成功（OK），0 行 SKIP**；**0 行判成 `same_source=yes`**（逐行自证 ④ 独立于 ②，故无因同源而不得补者）。2 行 direct call 全部成立（站点 E8 + `site+5+rel32==entry` + 非自环），12 行槽位 **12/12 解出**（6 项字节复核全过）。改前 14 行第 4 列**均不含 `④`**（`pre_has_ring4=否`，逐行读字节确认）。行行不同自检：完整文本 **14/14**、entry 归一后 **14/14**。

**只补 ④ 成文、未改 grade/判定、未并表。**

---

## 1. 14 行清单与逐行结论

权威输入 `other14.tsv` 的 `f_reason` 决定形态；地址全部回 `gamemd.exe` 只读复核（方法见 §3/§4）。

| # | entry | subsystem | name | 形态 | 关键地址（vt/槽 或 站点） | same_source | 改前含④ | 结论 |
|---:|---|---|---|---|---|---|---|---|
| 1 | 0040BC10 | S13 | DynamicVectorClass&lt;BombClass*&gt;::scalar_deleting_dtor | slot_witness | vt=007E17CC slot0 / 装表 0040B563 | no | 否 | OK |
| 2 | 0040F8F0 | S13 | DynamicVectorClass&lt;WarheadTypeClass*&gt;::scalar_deleting_dtor | slot_witness | vt=007E1E84 slot0 / 装表 0040F4AD | no | 否 | OK |
| 3 | 0040FEC0 | S13 | DynamicVectorClass&lt;WeaponTypeClass*&gt;::scalar_deleting_dtor | slot_witness | vt=007E1ED4 slot0 / 装表 0040FB4D | no | 否 | OK |
| 4 | 00422CA0 | S20 | AnimClass::Draw | slot_witness | vt=007E3354 slot69 / 装表 0042201C | no | 否 | OK |
| 5 | 0046B910 | S13 | DynamicVectorClass&lt;BulletClass*&gt;::scalar_deleting_dtor | slot_witness | vt=007E4678 slot0 / 装表 004662FD | no | 否 | OK |
| 6 | 0048AFD0 | S13 | VectorClass&lt;DamageGroup*&gt;::scalar_deleting_dtor | slot_witness | vt=007E5144 slot0 / 装表 00489B1E | no | 否 | OK |
| 7 | 0048B020 | S13 | DynamicVectorClass&lt;DamageGroup*&gt;::scalar_deleting_dtor | slot_witness | vt=007E5170 slot0 / 装表 004892AA | no | 否 | OK |
| 8 | 004AF540 | S11 | DriveLocomotionClass::DriveLocomotionClass | **direct_call** | 站点 006C404C → 004AF540 | no | 否 | OK |
| 9 | 004B5AB0 | S11 | DropPodLocomotionClass::DropPodLocomotionClass | **direct_call** | 站点 006C494C → 004B5AB0 | no | 否 | OK |
| 10 | 0054EBA0 | S13 | DynamicVectorClass&lt;KamikazeControl*&gt;::scalar_deleting_dtor | slot_witness | vt=007ECE7C slot0 / 装表 0054E298 | no | 否 | OK |
| 11 | 0062B380 | S13 | DynamicVectorClass&lt;ParasiteClass*&gt;::scalar_deleting_dtor | slot_witness | vt=007EF824 slot0 / 装表 006291AD | no | 否 | OK |
| 12 | 0065BED0 | S13 | RadSiteClass::scalar_deleting_dtor | slot_witness | vt=007F0810 slot8 / 装表 0065B228 | no | 否 | OK |
| 13 | 0065C200 | S13 | DynamicVectorClass&lt;RadSiteClass*&gt;::scalar_deleting_dtor | slot_witness | vt=007F07A4 slot0 / 装表 0065B17D | no | 否 | OK |
| 14 | 0075E510 | S13 | WarheadTypeClass::scalar_deleting_dtor | slot_witness | vt=007F6B30 slot8 / 装表 0075D0BA | no | 否 | OK |

**成功：14 行**（全部进 `delta.tsv` / `fields.tsv`）；**SKIP：0 行**，故无 SKIP 原因。关键地址缺失：**0 行**（无「未取得」字段）。

### 1.1 `same_source` 自证（卡面 §3.3，逐行自判，不照抄审计）

14 行原本 `same_source=-`（`scan_F1_audit.tsv` 实测为 `-`，因走 `surface.py` 路由 2、无审计记录），本卡**自己判一次**，全部 **no**：

- **12 行槽位见证**：② = `COL→TD→RTTI 装饰名`（`.rdata/.data` 静态类名链）；④ = **体外装表点**（`.text` 中 `mov [dest],imm32==vt`，非本 entry 体内）。两条字节链不同，④ 独立于 ②。`vt[slot]==entry` 的槽位占用部分**只按 D-47(A)/§12.6 让位口径引用，不作独立证据链**——与 F1 前几批一致，未把同一次槽扫当第四环。
- **2 行 direct call**：② = 类身份证据（构造器装 canonical vt + 工厂上下文，见语义栏）；④ = 工厂 `CreateInstance` 体内 direct call `E8 @site → entry`，`site+5+rel32==entry`、非自环，位于 `.text` 调用站点，独立于 ②。**direct call 本就独立于 ②**（比槽位见证更强）。D-47/§12.6 在本形态仅作披露指针，不依赖槽位让位。

**判成 `same_source=yes` 的行数：0** ⇒ 无「因同源不得补」而 SKIP 者。

### 1.2 改前第 4 列 `④` 实测（卡面 §3.4，供并表算净增）

逐行读 `coverage.tsv` 原始字节的第 4 列：`④` 出现计数 **14/14 = 0**，`pre_has_ring4` 全为 `否`。即本批 **净增 14 行 ④**（不是已有 ④ 的重复措辞）。任一行为前缀断言失败都会报错——`verify_delta.py` 实测 `errors: []`。

---

## 2. 行行不同自检（entry 归一后，卡面 §4.3）

对 14 条实际追加的 ④ 正文取集合（`scan_raw.json` → `verify_summary.json`，并由 `verify_delta.py` 独立再核 `delta.tsv` 第 4 列追加段）：

| 检查 | 结果 |
|---|---|
| 完整 ④ 正文 `set()` | **14/14 不同** |
| 全部 8 位十六进制替换为 `ENTRY` 后 `set()` | **14/14 不同** |

direct call 两行按字节空格分隔写法（`E8 EF B4 DE FF` vs `E8 5F 11 DF FF`）保留操作数字节差异，归一后仍各异；槽位 12 行以 class / vt / slot / 装表点各自独立而不同（9 行 slot0 靠不同 class/vt/RTTI/装表点，2 行 slot8 靠不同类，1 行 slot69）。**无抄袭/复制**。

---

## 3. 六项字节复核（12 行槽位见证，卡面 §4.3）

回 `gamemd.exe` 只读复算（`scan.py` 生成，`verify_delta.py` 独立再算），**12/12 × 6 项全 True**：

| 项 | 判据 | 结果 |
|---|---|---|
| 1 | `u32(vt + slot*4) == entry` | 12/12 True |
| 2 | `u32(vt − 4) == COL` | 12/12 True |
| 3 | `u32(COL + 4) == offset`（全 0） | 12/12 True |
| 4 | `u32(COL + 12) == TD` | 12/12 True |
| 5 | `cstr(TD + 8) == mangled`，且与 `other14.tsv` 的 `slot_rtti` 逐字相等 | 12/12 True |
| 6 | capstone 解码体外装表点 `imm32 == vt`，且不在本 entry 体内 | 12/12 True |

附加：`rtti_tokens_ok` 12/12 True（模板名 `DynamicVectorClass<X*>` ↔ `.?AV?$DynamicVectorClass@PAVX@@@@` 逐 token 对齐）。`probe.col_name_match` 对模板类名返回 `nomatch` 是其机械正则不解析 `<...>` 的已知局限，已用 token 判据替代，不影响 ②。

**槽位分布**（与卡面 §2 线索一致）：9 行 slot0、RadSiteClass/WarheadTypeClass 各 slot8、AnimClass::Draw slot69（vt `007E3354` + 0x114 = 槽址 `007E3468`，与语义 `v[69]` 逐值吻合）。**12/12 解出**。

### 3.1 宿主函数定界的诚实披露

7 行装表点是 `mov [global], vt`（静态初始化函数写全局对象 vptr，如 `0040B563: C705 D8F58700 CC177E00` = `mov [0x87F5D8],0x7E17CC`），这些函数**不在 function_atlas 收录范围**，`which_body` 返回 None。其宿主地址由**nop/int3 填充后的函数起点 + 线性反汇编精确落到站点**确定（`host_src=disasm-padding`），未编造：0040B540 / 0040F490 / 0040FB30 / 004662E0 / 0054E260 / 00629190 / 0065B160。其余 5 行宿主由 atlas 命中（00421EA0 / 00489280 / 00489280 / 0065B1E0 / 0075CEC0）。**装表点本身（地址 + imm32==vt 字节）全部取得，无「未取得」**。

---

## 4. direct call 两行实证（站点指令字节 + 目标 entry，卡面 §4.3）

| entry | 站点 | 指令字节 | capstone 解码 | `site+5+rel32` | 宿主（工厂） | 体外/非自环 | 结论 |
|---|---|---|---|---|---|---|---|
| 004AF540 | 006C404C | `E8 EF B4 DE FF` | `call 0x4af540` | 004AF540 | 006C4010 | 是 | OK |
| 004B5AB0 | 006C494C | `E8 5F 11 DF FF` | `call 0x4b5ab0` | 004B5AB0 | 006C4910 | 是 | OK |

四项判据（`d1` 操作码 E8 / `d2` `site+5+rel32==entry` / `d3` capstone 目标 == entry / `d4` 体外非自环）**2/2 × 4 项全 True**。两站点均落在工厂 `CreateInstance` 函数体内（宿主函数头 `56 57 8B 7C 24 18 85 FF 75 0A…` 正常 prologue，非 self、非 atexit），与探针线索 `006C404C → 004AF540`、`006C494C → 004B5AB0` 逐字节吻合。**形态 1（direct call）成立，未写成槽位见证。**

---

## 5. `coverage.tsv` 与 `gamemd.exe` sha256（证明未改）

| 文件 | 字节数 | SHA-256 | 时点一致性 |
|---|---:|---|---|
| `COVERAGE\coverage.tsv` | 4,083,215 | `2F498B18E64E7EF568A0EB7888CE9F8D710CABC91038E52A8167F8826B53B36E` | scan 前 = gen 前 = gen 后 = verify（全程未变） |
| `ra2youli\gamemd.exe` | 4,825,360 | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` | 与卡面给定值一致，全程只读 |

`coverage.tsv` 全程仅以 `rb` 打开读取；`gamemd.exe` 仅 `pefile.PE(path, fast_load=True)` + 只读字节缓冲 + capstone 解码，sha 未变。**未写 `COVERAGE\coverage.tsv`、PANEL、R14_COMMON、台账、看板、`_drafts\`、`_cards\` 或任何其它卡目录；未改 `ra2youli\` 下任何文件。**

---

## 6. 披露指针纪律

每行 ④ 末尾均自带 D-47 披露指针：

- 槽位行：`（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）`
- direct 行：`（D-47 披露指针：R14_COMMON §12.6 与 PANEL 对应披露）`

`verify_delta.py` 逐行断言追加段含 `§12.6` 且**不含 `§12.4`**，14/14 通过。不表述为「已过 §12.3」（§12.6 引用纪律）。

---

## 7. 边界声明

**只补 ④ 成文**：在 `delta.tsv` 第 4 列原语义后追加 ④ 文本，**原第 4 列为严格前缀**（14/14 断言）；第 1/2/3/5/6/7/8 列与盘上逐字节相同（14/14）；第 5 列 grade 逐字节保持 `[已证]`（14/14）。**未改 grade、未改判定、未并表。**

产物（全部在 `R16_F1_OTHER14\`）：`delta.tsv`（8 列 × 14 行 + 表头）、`fields.tsv`（12 列 × 14 行 + 表头）、`REPORT.md`，另附只读脚本与中间 JSON（`scan.py` / `scan_raw.json` / `gen_products.py` / `verify_summary.json` / `verify_delta.py` / `verify_delta.json`）。

样例 ④ 两条见 `verify_summary.json` 的 `samples` 字段（槽位行 0040BC10、direct 行 004AF540），正文亦见 `delta.tsv` 相应行。
