# BASELINE.md — 判据的特异性测试（§952）

目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`｜ImageBase 0x400000｜只读。
扫描域：项目根 `YRpp\` 全部 238 个 `.h/.hpp/.cpp/.inl`（排除 `.git`/`.mimosa`）。
复跑脚本：`work\analyze_yrpp.py`；原始输出：`EVIDENCE\scan_noinit_raw.txt`、`EVIDENCE\census_detailed.json`。

## 1. 问题

拟用判据 =「`noinit_t` 相关行的**下一行**有 `JMP_THIS(0x…)`」。
在采用之前必须先测：这个「下一行出现 `JMP_THIS`」的形态，是不是 `noinit_t` 特有的？
若普通构造器也普遍如此，则该形态不特异，必须收窄判据，否则「N 个误剔」无意义（§952）。

## 2. 方法（对全镜像所有 JMP_THIS 行取前一行）

对 YRpp 238 文件里**全部** `JMP_THIS(0x…)` 行取紧邻前一行，按前一行形态分桶。
不只看 `noinit_t` 样本，而是以 JMP_THIS 为总体做基线。

## 3. 结果

| 前一行形态 | JMP_THIS 行数 | 占比 |
|---|---:|---:|
| 普通函数/构造器签名行（`…(…) [noexcept] [:]`，非 noinit_t） | **686** | 84.1% |
| `noinit_t` 委托初始化行（`: Xxx(noinit_t())`） | **99** | 12.1% |
| 其他（`{`、`{ JMP_THIS…` 同体、注释、空行等） | 30 | 3.7% |
| 普通初始化列表行（非 noinit_t） | 1 | 0.1% |
| **合计 JMP_THIS 行** | **816** | 100% |

`noinit_t` 行总数 300（其中 99 行下一行有 JMP_THIS；106 行为纯空桩定义；余 95 行为空桩体内的 `: Base(noinit_t())` 委托行）。

### 判据判定：**「下一行有 JMP_THIS」不特异，必须收窄。

理由：816 个 JMP_THIS 中 686 个（84.1%）的上一行是**普通签名行**，并非 noinit_t。
「JMP_THIS 写在签名/委托行的下一行」只是 YRpp 内联函数的统一排版风格（形如
`Ctor(args) noexcept\n\t: Ctor(noinit_t())\n\t{ JMP_THIS(0x…); }`），
对 noinit_t 与普通函数一视同仁。单凭「相邻 JMP_THIS」会把 686 个正常函数也判成受害。

## 4. 收窄后的判据（本卡采用）

同时满足两条才算「真误剔」：

1. **上一行确为委托初始化行**：正则 `:\s*([A-Za-z_][A-Za-z0-9_:]*)\s*\(\s*noinit_t\s*(\(\s*\))?\s*\)`；
   且该行不是 `explicit __forceinline Xxx(noinit_t)` 空桩定义本身。
2. **下一行（紧邻）有 `JMP_THIS(0x…)`**，给出真实函数地址。

不满足 (2) 的 noinit_t 行一律归「纯空桩」，不提升（见 `SUMMARY.md` 纯空桩清单）。
收窄后命中 **99 实例 / 95 唯一地址**；C08 已知 9 个、C09 已知 15 个地址全部在命中集内
（双向核对：`work\inspect_census.py`），证明收窄判据与已证缺陷同源。

## 5. 分级

- 基线统计 `[已证]`：238 文件逐行扫描，非抽样；脚本可复跑。
- C08/C09 回收核对 `[已证]`：与 `_audit\VERDICT.md` 清单逐地址一致。
- 判据特异性结论 `[静态推断]`（由 686/816 的比例直接推出）。
