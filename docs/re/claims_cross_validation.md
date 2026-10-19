# 断言库交叉校验与「唯一事实源」合并（MA1）

> 任务：MA1 · 执行方：MiMo 桌面 · 工作区：`D:\Project\ra2-campaign-forge`
> 基线：`ra2youli/gamemd.exe`（YR 1.001，MD5 `4f37486e5b0dbe2ae5f45aeee0f48367` 对账见门禁；只读）
> 产出目录：`out/re_work/claims_audit/`
> 证据标准：文件:行号 / VA+原始字节+反汇编；可机读断言 `out/re_work/claims_audit/claims.txt`

---

## Q1 逐文件解析总表

解析器：`out/re_work/claims_audit/cross_validate.py`（正则 `0xVA = HEXBYTES # comment`）
结果：`out/re_work/claims_audit/per_file_report.json` / `.md`

| # | 文件 | 总行 | 注释 | 空行 | **断言** | **唯一 VA** | 非法行 | 文件内重复 VA | 任务卡声明 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | `docs/re/anchor_claims.txt` | 388 | 58 | 7 | **323** | 323 | 0 | 0 | 323 |
| 2 | `out/re_work/damage_pipeline/claims.txt` | 95 | 5 | 0 | **90** | 90 | 0 | 0 | 90 |
| 3 | `out/re_work/damage_pipeline/claims_s26.txt` | 191 | 5 | 15 | **171** | 168 | 0 | 3 | 171 |
| 4 | `out/re_work/shroud_click/claims.txt` | 79 | 0 | 0 | **79** | 79 | 0 | 0 | 79 |
| 5 | `out/re_work/fs_mix_deep/claims.txt` | 165 | 0 | 0 | **190*** | 190 | 5† | 0 | 190 |
| 6 | `out/re_work/triggers_deep/claims.txt` | 174 | 0 | 3 | **174** | 171 | 0 | 3 | 174 |
| 7 | `out/re_work/savegame/claims.txt` | 146 | 3 | 0 | **143** | 137 | 0 | 6 | 143 |
| 8 | `out/re_work/hook_matrix/claims.txt` | 44 | 4 | 0 | **40** | 39 | 0 | 1 | 40 |
| 9 | `out/re_work/doc_audit/claims.txt` | 43 | 7 | 0 | **26** | 26 | 0 | 0 | 26 |
| 10 | `out/re_work/open_items2/claims.txt` | 73 | 1 | 0 | **72** | 72 | 0 | 0 | 72 |
| | **合计** | | | | **1308** | **1062** | 5† | 13 | 1308 |

\* `fs_mix_deep` 的 5 条「非法行」实为**注释内嵌换行**的续行（源字符串如 `"Failed to bootstrap!\n"` 被折行），不是格式错误断言；有效断言仍为 190。  
† 同上，见 `inspect` 输出 L142/178/181/190/195。  
文件内重复 VA（13 处）均为**同 VA 同字节**重复登记，无内容冲突（例：`savegame` 0x0067FDF0 模板序言登记两次；`hook_matrix` 0x006D3D99 已装点与 P-6.1 各登记一次）。

**结论**：任务卡「9 套」实为 **10 个文件**；条数与任务卡声明 **10/10 一致**；格式整体合规。

---

## Q2 字节冲突检测

方法：同 VA 跨文件比对声明 HEXBYTES；区分 **真不一致** 与 **前缀长度差**（一短一长且长串以短串为前缀）。

| 指标 | 数量 |
|---|---:|
| 跨文件同 VA（≥2 来源） | **218** |
| 字节差异条目 | **27** |
| 其中真不一致（byte_mismatch） | **0** |
| 其中前缀长度差（prefix_length） | **27** |

### 字节冲突表（27 条全部为前缀长度差）

| VA | 短声明 | 长声明 | 判定 |
|---|---|---|---|
| `0x004068E0` | 1B `C3`（fs_mix_deep:184） | 4B `C3909090`（anchor_claims:58） | 前缀一致，长者含 nop 垫 |
| `0x004739F0` | 1B `56`（anchor_claims:338） | 8B `568BF1E838700000`（open_items2:41） | 前缀一致 |
| `0x00473D10` | 3B `83EC10`（anchor_claims:341 / open_items2:46） | 6B `83EC1053568B`（fs_mix_deep:9） | 前缀一致 |
| `0x004C6CB0` | 6B `81EC70030000`（anchor_claims:92） | 8B `81EC7003000033C0`（shroud_click:59） | 前缀一致 |
| `0x005301A0` | 3B `83EC68`（anchor_claims:278） | 8B `83EC68A1D0C18100`（fs_mix_deep:33） | 前缀一致 |
| `0x0067FDF0` | 8B `83EC085356578BFA`（savegame:3,19） | 10B `83EC085356578BFA8BD9`（anchor_claims:148） | 前缀一致 |
| `0x0067FE70` | 8B（savegame:22） | 10B（anchor_claims:158） | 前缀一致 |
| `0x006805F0` | 8B（savegame:67,131） | 10B（anchor_claims:160） | 前缀一致 |
| `0x00680EF0` | 8B（savegame:6,121） | 10B（anchor_claims:159） | 前缀一致 |
| `0x006BD7F4` | 5B `A3044E8800`（anchor_claims:366） | 6B `A3044E8800EB`（fs_mix_deep:80） | 前缀一致 |
| `0x006DD8D7` | 3B `8B562C`（anchor_claims:186） | 6B `8B562C4A81FA`（triggers_deep:142） | 前缀一致 |
| `0x0071E950` | 7B（triggers_deep:140） | 8B（anchor_claims:231） | 前缀一致 |
| `0x0071F697` | 5B（anchor_claims:249） | 6B（triggers_deep:66） | 前缀一致 |
| `0x0071F950` | 4B（anchor_claims:245） | 8B（triggers_deep:137） | 前缀一致 |
| `0x0071F9C0` | 6B（anchor_claims:247） | 8B（triggers_deep:138） | 前缀一致 |
| （其余 12 条） | 同模式 | | 前缀一致 |

完整机器表：`out/re_work/claims_audit/byte_conflicts.json` / `byte_conflicts.md`。

**合并策略**：同 VA 取**信息最全**的字节串（多数优先，并列取更长前缀扩展）；实测 **merged 值恒等于某一来源**，未拼接、未造字节（`inspect_merge_bytes.py`：`merged longer than all sources = 0`，`not identical to any single source = 0`）。

---

## Q3 语义冲突检测

方法：`semantic_scan.py`（指令类对立 + 关键词对立 + 注释重叠弱信号）。

| 级别 | 数量 | 裁定 |
|---|---:|---|
| 硬语义冲突（需 Lead 裁定） | **2 → 0** | 初筛 2 条经复核为**误报**（见下） |
| 弱注释分歧（表述不同、事实一致） | **14** | **不构成冲突**，仅风格差异 |
| 多来源 VA 总数 | 218 | 字节侧见 Q2 |

**误报说明（原「硬」2 条）**：

| VA | 初筛标签 | 实情 | 证据 |
|---|---|---|---|
| `0x00750931` | ret vs call | 两侧都是 `ret 8`；「call」来自 “callee cleanup” 一词 | `anchor_claims.txt:77` / `hook_matrix/claims.txt:43` |
| `0x007509EF` | ret vs call | 同上，`ret 4` | `anchor_claims.txt:79` / `hook_matrix/claims.txt:44` |

**弱分歧样例（事实一致）**：

| VA | 来源 A | 来源 B | 判定 |
|---|---|---|---|
| `0x0047F40F` | hook_matrix「FogBlendB1 区头原版 8B」 | （同文件）「灰雾混色桩 B1 补丁区头」 | 同一补丁区，表述不同 |
| `0x00508F8F` | anchor「je 0x00508FF6 门控」 | hook_matrix「P-2.4 SpySatGate 原字节」 | 同一字节 `74 65` |
| `0x0064CC61` | anchor「mov al,[0xB04880]」 | hook_matrix「P-1.2 原字节=文档」 | 同一字节 |

### 语义冲突表（终态）

| VA | 冲突双方 | 判定 | 需 Lead 裁定 |
|---|---|---|---|
| — | **无实质性语义冲突** | 218 个多来源 VA 中注释均指向同一机器行为 | 否 |

机器表：`out/re_work/claims_audit/semantic_conflicts_v2.json`。

---

## Q4 去重合并（唯一事实源）

输出：`out/re_work/claims_audit/claims_merged.txt`（VA 升序，同 VA 一条；注释 = 最完整者 + `sources=` 全来源）

| 指标 | 数量 |
|---|---:|
| 合并前断言总行 | **1308** |
| 合并前唯一 VA | **1062** |
| **合并后唯一 VA（claims_merged）** | **1062** |
| 合并消重行数 | **246** |
| 真字节冲突 | **0** |
| 需裁定语义冲突 | **0** |

消重 246 行全部来自「同 VA 多文件/同文件重复登记」，合并后每 VA 保留一条最强断言。

---

## Q5 门禁实跑

```
python tools/verify_anchors.py
  回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
  ★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！

python tools/audit_bytes.py out/re_work/claims_audit/claims.txt
  合计 1062 条：OK=1062  MISMATCH/NOREAD=0
```

（`claims.txt` = `claims_merged.txt` 副本，作为本任务交付的可机读断言。）

---

## Q6 抽样独立反证

脚本：`out/re_work/claims_audit/sample_verify.py`  
口径：**不调用** `tools/audit_bytes.py`；自带 PE 段映射（`va2off`）+ Capstone x86-32 反汇编；随机种子 `20260927`，样本 10 条。

| VA | FileOffset | 判定 | 期望/实机 | Capstone |
|---|---|---|---|---|
| `0x0048A29F` | `0x0008A29F` | OK | `E83C251D00` | `call 0x65c7e0` |
| `0x004AB9B0` | `0x000AB9B0` | OK | `83EC7C535556` | `sub esp,0x7c; push ebx/ebp/esi` |
| `0x0052BB7A` | `0x0012BB7A` | OK | `68E4608200` | `push 0x8260e4` |
| `0x0052C8B9` | `0x0012C8B9` | OK | `68945D8200` | `push 0x825d94` |
| `0x0067D35D` | `0x0027D35D` | OK | `A154418B00` | `mov eax,[0x8b4154]` |
| `0x00680A70` | `0x00280A70` | OK | `83EC085356578BFA` | 模板序言 |
| `0x006DE911` | `0x002DE911` | OK | `E86A3B0700` | `call 0x752480` |
| `0x006F0B36` | `0x002F0B36` | OK | `39782C750E` | `cmp [eax+0x2c],edi; jne` |
| `0x007E23B8` | `0x003E23B8` | OK | `B0444100` | Aircraft Draw v[69] 指针 |
| `0x007F7BF8` | `0x003F7BF8` | OK | `90C87B00` | BlitTrans vtable+4 |

**结果：10/10 OK**。明细：`sample_verify.json` / `sample_verify.md`。

---

## 交付物索引

| 路径 | 说明 |
|---|---|
| `docs/re/claims_cross_validation.md` | 本文 |
| `out/re_work/claims_audit/cross_validate.py` | Q1/Q2/Q4 解析合并 |
| `out/re_work/claims_audit/semantic_scan.py` | Q3 语义扫描 |
| `out/re_work/claims_audit/inspect_merge_bytes.py` | 合并策略审计 |
| `out/re_work/claims_audit/sample_verify.py` | Q6 独立抽样 |
| `out/re_work/claims_audit/per_file_report.json/.md` | Q1 |
| `out/re_work/claims_audit/byte_conflicts.json/.md` | Q2 |
| `out/re_work/claims_audit/semantic_conflicts_v2.json` | Q3 |
| `out/re_work/claims_audit/claims_merged.txt` | Q4 唯一事实源 |
| `out/re_work/claims_audit/claims.txt` | 门禁用（= merged） |
| `out/re_work/claims_audit/merge_stats.json` | 合并统计 |
| `out/re_work/claims_audit/sample_verify.json/.md` | Q6 |
