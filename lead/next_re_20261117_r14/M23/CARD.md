# M23 · 合并员（COVERAGE\ 唯一写者）—— 三张已审计卡的 delta

写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + 本卡目录 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M23\`。**其他位置一律只读**。
⚠️ **严禁创建 venv、严禁 pip install**（系统 python 3.12 够用）。
⚠️ **coverage.tsv 的格式陷阱（必须先验证再动手）**：**表头行用逗号、数据行用 TAB**，8 列
`entry,subsystem,name,one_line_semantics,grade,evidence_path,n_sources,conflict`。
按逗号切会毁表。**改动前先备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M23.bak`。

## 输入（三张都已异族审计 PARTIAL，白名单如下，**严格照白名单，一条不多一条不少**）

### ① `S16_N1`（审计 `a-S16-N1`；执行 `hy4flash-free` / 审计 `deepseek-v4.1-flash`）
白名单 **8 行**，全部 `[静态推断]`：
`00539EB0` `0053AE00` `0053B410` `0053AE50` `006CE2C0` `006CE270` `006CE280`（7 行照 delta）
+ **`0053A0E0` 改名为 `LightningStorm::HasDeferment`**（delta 里写的是 `Ion::HasDeferment`，**审计已否证**；YRpp `SuperClass.h:166` 宿主是 `class LightningStorm`，`class Ion` 是空类）。
- 其中 **5 行 grade 由 `[未证]` 升 `[静态推断]`**（`0053A0E0` `0053AE50` `006CE2C0` `006CE270` `006CE280`）—— 审计已核准，照升。
- `006CE280` 的 grade 保持 `[静态推断]`，语义栏须保留 `contract_unique` 特征（审计称其通道 B 不绑定地址，是弱环但**不得剔除**）。

### ② `S13_K9`（审计 `a-S13-K9`）
白名单 **11 行，全部升 `[已证]`**（盘上现为 `[静态推断]`）：
`0040B880` `0040B930` `0040F7C0` `0040FD90` `0040FE40` `0046B7E0` `0046B890` `0062B250` `0062B300` `0065C0D0` `0065C180`
- **黑名单 3 行（不得改 grade）**：`0048AD60` `0054E8E0` `0048AD70` —— 审计裁定「3 行降级不成立，`[静态推断]` 由环② 支撑」⇒ **保持盘上 `[静态推断]`**；但它们的**名字与语义照收**（`GetItem` / `operator==`），只**不动 grade**。
- 审计要求：`evidence_path` **补 `#entry` 锚点**（形如 `…\EVIDENCE\VERDICT_EVIDENCE.md#0040B880`），否则逐行不可核查。
- 审计建议（可采纳）：slot6 前缀统一 —— `0048AD60` 写成 `VectorClass<DamageGroup*>::GetItem`、`0054E8E0` 同为 slot6 却写成 `DynamicVectorClass<…>`，**统一为 `VectorClass<T>::GetItem`**（YRpp 中 GetItem 为 final、不覆盖）。

### ③ `S13_K8`（审计 `a-S13-K8`，白名单 **149 行**，黑名单 1 行）
- **黑名单 `00773030`：整行不得改动**。盘上现为 `[已证] WeaponTypeClass::FindIndex`，delta 要降成 `[未证] sub_00773030` —— 审计已裁定**拒绝**（证据站得住；它是 ABSTRACTTYPE_ARRAY 的类静态成员，「非虚表槽」是应有形态不是反证；降级会同时丢 1 proved + 1 named ⇒ S13 named 216→215 = 89.58% 跌破 90.00%）。
- **18 行 `[已证]`：⚠️ 本卡暂缓升格，按 `[静态推断]` 并入**（Lead 已立 D-39 口径待裁；见下）。
  即：名字、语义、证据路径**照收**，**grade 保持盘上现值 `[静态推断]` 不变**。
  18 个 entry：`0075E510` `0065BED0` `0040BBC0` `0040BC10` `0040F8A0` `0040F8F0` `0040FE70` `0040FEC0` `0046B8C0` `0046B910` `0048AFD0` `0048B020` `0054EB50` `0054EBA0` `0062B330` `0062B380` `0065C1B0` `0065C200`
  **必须改写语义栏的 ③ 表述**（审计判执行员原话对其中 9 行失实、触 ⑮）：正确表述 =
  「**`test byte[esp+8],1` 门控的 `call 0x7C8B3D`(operator delete) + `ret 4`（vptr 写可有可无，基类 dtor 承担）**」。
  **禁止**再写「体内 `mov [this],VT`（vptr 重写）」——实测 9/18 体内不写自身 VT。
  **禁止**在语义栏写「[已证]」或任何升格字样。
- **9 行 `[静态推断]`→`[未证]`：照降**（审计已核准）：`0041C230` `0041C350` `0041C380` `0041C3C0` `0041C430` `0041D7E0` `004251F0` `00452820` `00708080`。
- **其余 106 行 `[静态推断]` + 16 行 `[未证]`**：名字/语义/证据路径照收，grade 不变。

## 列映射（三张 delta 都是 8 列，但第 7/8 列语义不同）
- delta 第 7 列 = `name_kind` / `reused_audited` ⇒ **不进 coverage**（可写进 MERGE_LOG）。
- delta 第 8 列 = `缺环说明` ⇒ **不进 coverage**。
- coverage `n_sources` = `evidence_path` 里 **`;` 分隔的路径条数**；`conflict` = **0**（除非同 entry 同名异源 ⇒ 1 并记 CONFLICTS.tsv）。

## 硬要求
1. **不得新增/删除 entry**：合并后数据行必须仍为 **18,431**（改动前先实测确认此数；不符即**停下报告**，不要凑）。
2. **不改 `subsystem`**（D-37 未裁）：三张卡的所有行 subsystem 保持盘上现值。
3. 幂等：同 entry 多次出现只落一次；**同 grade 不同名一律保留旧值并标 `conflict=1`**，不自行裁决。
4. 记 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M23\MERGE_LOG.tsv`：逐行 `card entry action(old_grade→new_grade) name_from name_to`；另有 rejected 段列 `00773030` 与 K9 的 3 行（附理由）。
5. 改完更新 `COVERAGE\PANEL.md`（每子系统 n / named_L / named_S / proved）。
6. 交付 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M23\PROGRESS.md`：**改动前后 grade 直方图**（`[已证]`/`[静态推断]`/`[未证]` 各多少）、每卡 applied/held/rejected 计数、coverage.tsv 改动前后 **SHA-256 与行数**、PANEL 更新确认。
7. **预期（改完后自行核对，不符先停）**：`[已证]` 1,376 → **1,387**（+11，仅 K9）；`[静态推断]` 6,028 → 6,028+5(K16 升) +0 −9(K8 降) = **6,024**；`[未证]` 11,027 → 11,027−5+9 = **11,031**；和仍 = 18,431。
   S13：proved 75 → **86**、named 216 不变。S16：named 73 → **81**（90.00%）、proved 46 不变。

## 上下文（供你判断，不是可选项）
Lead 已立 **D-39**（待用户裁）：虚函数的环③与环④物理同源 ⇒ 有效环数最多 3，那 18 行能否 `[已证]` 未定。
**裁决前按本线默认「先按 `[静态推断]` 并入」，所以本卡不得升那 18 行。** 若你发现任何行与上述白名单冲突（例如某行盘上已是 `[已证]` 但要求降级），**停下报告，不要自行决定**。
