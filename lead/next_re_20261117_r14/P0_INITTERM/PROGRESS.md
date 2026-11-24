# P0-INITTERM · PROGRESS

卡号 **P0-INITTERM**｜执行员 p0initterm｜2026-11-17｜目标 `gamemd.exe` SHA-256 `73201CC0…F67476`（现场校验 ✓）｜写域仅本卡目录

## 一句话结论
`.data+0x4` 起的 `_initterm` 静态初始化表 = **3,944 项真函数入口**（槽值即函数），coverage 仅收 22、atlas 仅收 2 ⇒ **3,922 项未收编**；含 thunk 口径分母 **18,417**，不含口径分母 **14,473**（均由当前 coverage 14,495 截面推导；详见 CALIBER.md）。

## 结论表（与派卡/审计对照）
| 项 | 我的实测 | 派卡/审计值 | 一致? |
|---|---:|---:|---|
| 主表消费点 | `0x7CBDD3` call `0x7CBED3`；push end=`0x815da4` / begin=`0x812000`（立即数，非加载） | 同 | ✓ |
| 槽位数 `(end-begin)/4` | 3,945 | — | — |
| slot[0] @ `0x812000` | `0x00000000`（NULL，`_initterm` 的 `test eax,eax/je` 跳过） | 「.data+0x4 起」 | ✓ |
| **表项数（非空槽）** | **3,944** | 3,944 | ✓ |
| 所在段/字节范围 | `.data` `0x812000..0x815da4`（VA 等于节首），项宽 4B | `.data+0x4` | ✓ |
| FUNC / NOT_FUNC / UNDECIDABLE | **3,944 / 0 / 0** | 全 FUNC | ✓ |
| 16B 对齐 | 3,944/3,944 | 3,944/3,944 | ✓ |
| in coverage | **22** | 22 | ✓ |
| in atlas | **2**（`00412870` / `006A4DC0`） | 2 | ✓ |
| **未收编（FUNC ∧ ¬coverage）** | **3,922** | 3,922 | ✓ |
| coverage_delta 行数 | 3,922 | — | 新产出 |
| FPU 形态首字节 DD/DB | 1,767+252=**2,019** | 2,019/2,026（审计 §2） | ✓ |
| 分母含 thunk | **18,417** = 14,495+3,922 | 审计 18,431（多 +14 非表项） | 见 DISAGREE |
| 分母不含 thunk | **14,473** = 14,495−22 | 审计 14,715（全镜像估计） | 见 CALIBER |

## T1 `_initterm` 调用点穷举（**4 处，不是 1 处**）
| 调用点 | begin | end | 槽位 | 非空 FUNC | 范围 |
|---|---|---|---:|---:|---|
| `0x7CBDD3` | `0x812000` | `0x815da4` | 3,945 | **3,944** | 本卡目标 |
| `0x7CBDC4` | `0x815da8` | `0x815dbc` | 5 | 4 | 表外，未并入 |
| `0x7CBE8B` | `0x815dc0` | `0x815dd0` | 4 | 3 | 表外，未并入 |
| `0x7CBE9C` | `0x815dd4` | `0x815ddc` | 2 | 1 | 表外，未并入 |

穷举法：`.text` 全字节扫 E8/E9/EB rel32→`0x7CBED3`（4 命中，纪律 E）；全段扫 dword==`0x7CBED3`（0）；`_initterm` 函数体字节模式全镜像仅 1 份 ⇒ 无其它入口形式（call [reg] 派发已由该 dword 扫描排除）。边界是 `push imm32` 立即数，非内存加载。

## 给审计员的 4 个核心数字 + 独立复算
1. **3,944 项**：`python work/t1_tables.py` → `EVIDENCE/t1_tables.txt`：`slot[0]=0`、`(0x815da4-0x812000)/4-1=3944`；或数 `INITTERM_TABLE.tsv` 数据行（3,944）。
2. **FUNC 3,944 / 未收编 3,922**：`python work/analyze.py` → `EVIDENCE/stats.json`；或 `Import-Csv INITTERM_TABLE.tsv | ? in_coverage -eq N` = 3,922。
3. **atlas 仅 2 的可验证依据**：`EVIDENCE/t5_atlas.tsv`；**0/3,944** 是 `.text` 内 E8/E9 直接目标（唯一调用是 `0x7CBEE4 call eax` 寄存器间接）；`W130_atlas/FuncAtlas.java:104` 用 `fm.getFunctions(true)`、`:112-115` 只数直接 call/jmp 引用、`:31-45` 的 fnptr **不建函数只标记**。
4. **两口径分母 18,417 / 14,473**：当前 `coverage.tsv` 14,495 数据行；14,495+3,922=18,417；14,495−22=14,473。

## 语义桶（T3，详见 SEMANTICS.md）
`B_CALL_THUNK` 1,962（22 在 coverage）/ `C_FP_INIT` 1,148（0）/ `D_PLAIN_STORE` 818（0）/ `E_OTHER` 16（0）。**未见直接 C7 写 .rdata vptr** ⇒ 本表主体是全局初始化器（含调用 `_ftol`/数学辅助），不是写 vptr 的 C++ 对象构造器（见 SEMANTICS.md / DISAGREE.md）。

## 交付 / 纪律
`INITTERM_TABLE.tsv`(3,944) · `coverage_delta.tsv`(3,922) · `SEMANTICS.md` · `CALIBER.md` · `UNKNOWNS.md` · `DISAGREE.md` · `EVIDENCE\`(不截断) · `work\`(可复跑)。
只读 gamemd.exe（SHA ✓）/ COVERAGE / 台账；未改游戏文件、未 git commit；capstone 全程 `skipdata=True`。
