# W168 DISAGREE（与既有结论/Lead 预期不符之处）

## 1. 派发提示词："两个通配符字符串在 `.data` 里各出现两次"

- **我预期**：按提示词，字面串 `BATTLEMD*.INI` 与 `RULEMD*.INI` 各 2 处。
- **实测**（`EVIDENCE\byte_verify.txt` §2，全文件 ASCII + NUL 终止扫描；`boundary_check.py §B` 大小写不敏感复算）：
  - `BATTLEMD*.INI`：1 次（文件偏移 `0x4261A8`）
  - `RULEMD*.INI`：1 次（`0x42626C`）
  - 子串 `BATTLEMD`：2 次（`0x426198` = `BATTLEMD.INI`，`0x4261A8` = `BATTLEMD*.INI`）
  - 子串 `RULEMD`：1 次（只有 `0x42626C`；`RULESMD.INI` 不含连续 `RULEMD`）
- **因此**：提示词那句按字面不成立；推测其意是"BATTLEMD 家族有 base+wildcard 两个串"。以字节实测为准。这不影响 Q1 的 xref 结论（xref 两通道一致，各 1 处）。

## 2. 台账 §740-4 早期表述："`RULESMD.INI`（MIX 内）先加载 → `RULEMD90.INI`（磁盘）后加载 → 覆盖 `[105mm] ROF`"

- **我预期**（读 §740 时）：覆盖件后加载 ⇒ 覆盖 MIX 内 base 的同名键。
- **实测**（本卡反编译 `FUN_0052CD70`，`EVIDENCE\w168main.clean.txt:456-554` + §751）：RULE 路径里 `stricmp(文件名,"RULESMD.INI")==0` 时把 base **插到数组索引 0**（右移其余），`>1` 个规则文件时弹 dialog 让用户选一个文件整体使用（`DAT_00887048 = local_304[iVar4]`），不是逐键叠加。且 §751/§755 已实测磁盘 `RULEMD*.INI` 覆盖无效。
- **因此**：§740 那句"后加载覆盖"的因果解释不成立/已过时（§751 已改口为"base 插到 0 压过磁盘件"）；本卡独立复核支持 §751 的方向。**但本卡结论针对 BATTLE 路径（逐键并入）——两条路径语义不同，不可把 RULE 的"选择+base 优先"套到 BATTLE。**

## 3. 台账 §910-3："任何'98 一定覆盖官方'或'官方一定覆盖 98'都没有静态依据" — 一致，无分歧

- 本卡独立复核后**加强**这一结论并给出字节依据（`0x46CE10` 按战役名复用对象、`0x46CCD0` 逐键写回、`FUN_0052CB90` 无排序）。无 DISAGREE。

## 4. IAT xref 双通道计数差异（记录，非结论冲突）

- `FindFirstFileA` 直接 `call [IAT]` 站点：字节通道 `FF 15` 扫描 = **14** 处（`EVIDENCE\byte_verify.txt` §7）；Ghidra `getReferencesTo(0x7E1208)` = **13 refs**，其中 12 个是 `CALL`、1 个是 `MOV EBX,[0x7E1208]`（间接调用预备，`0x53000B`），且 Ghidra 漏掉 `0x47AA85`/`0x751EBA` 两处（落在未建函数区）。
- **原因**：Ghidra 对无人引用区不建函数（`R12_FACTS §6.2`）；字节通道不依赖 atlas，是更全的一条。两者对"本卡路径"（`0x52CBA9`/`0x52CDAC`）一致。已按 §6.2 用字节通道做穷举口径。
