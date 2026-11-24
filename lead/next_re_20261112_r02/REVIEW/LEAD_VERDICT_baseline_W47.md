# LEAD_VERDICT · BASELINE 裁决实测（W47 中途通报，我采纳的部分）

> 记录人：Lead（本会话）｜ 时间：2026-11-13 21:50
> 来源：W47（Hy4）中途通报；其最终报告 `BASELINE_ADJUDICATION_RESULT.md` 尚未交付，本节只记**已被它实算并给出脚本/stdout 的部分**。

---

## 1. 两条会改变我既有口径的发现

### 1.1 我们手上的 `73201cc0…` 是 **ra2opt 改过的状态**，不是原始态

`[转引·W47 实算]` 本机 1703 份 `gamemd*.exe`，其中 **114 份是真实 PE32**（4,825,360 B），产生 21 个不同整文件 SHA；按 (C01,C02,C04,C08) 精确分组 = **6 组**，主态两支：

| 整文件 SHA | 份数 | 定性 |
|---|---|---|
| `73201cc0…`（我一直当基线用的那个） | **95** | **ra2opt perf 留痕态**（含 `ra2bench/`、`ra2youli/`） |
| `db264305…` | **15** | **原始态**（含 `ra2youli\.ra2opt\orig\`、`D:\Red2\ra2youli\`） |

`[转引]` 两主态**仅差 2 字节**：
```
0xAE: 0x00 → 0x20      (DllCharacteristics)
0xB2: 0x10 → 0x40      (SizeOfStackReserve 1 MB → 4 MB)
```
`.text` 的 raw SHA **同为 `c0368a17…`**。

`[我的判断]` 这两处改动正是 **PE 优化器**的典型动作（栈保留放大 + DllCharacteristics 标志位），与 `ra2opt`（性能优化工具）的性质吻合。
⇒ **`73201cc0…` 不是"原始镜像"，是"被 ra2opt 优化过的镜像"。** 原始态是 `db264305…`。

### 1.1b Lead 逐字节复算（22:00，`[本次实测]`）

我直接对比 `ra2bench\gamemd.exe`（A 线测量的靶）与 `ra2youli\.ra2opt\orig\gamemd.exe`：

```
sizes          4,825,360 / 4,825,360
差异字节数     2
  0x00AE       0x20 (改后) vs 0x00 (原始)      ← DllCharacteristics
  0x00B2       0x40 (改后) vs 0x10 (原始)      ← SizeOfStackReserve 4MB vs 1MB
.text raw SHA  两者同为 c0368a179f6e1a0f85bf94ebeb3a3e62…
.text identical: True
原始态文件     ra2youli\.ra2opt\orig\gamemd.exe = DB264305C8A6963D17F5D189A5A9720D…（实存）
```

⇒ **W47 的报告准确，我独立复算命中。**
⇒ `[签发]` **A 线全部性能数据测在「`.text` 与原始态完全相同、仅 2 个 PE 头字节不同」的镜像上。**
这削弱了「性能结论不可外推」的严重性（**代码路径一致**），但**不能据此说等价**：栈保留 1→4 MB 可能改变映像内存布局与缓存行为，**未做实验**。

`[对 A 线的后果 —— 必须加注]` 本会话 A 线所有性能数据（单 tick CPU 1.336–1.767 ms、600 s 漂移、战斗 +0.8% 等）**都测在这个 ra2opt 优化态上**。
`[口径更正]` 以后引用 A 线数字必须写：**「在 `73201cc0…`（ra2opt 优化态；`.text` 与原始态逐字节相同、仅 DllCharacteristics 与 SizeOfStackReserve 不同）上测得」**。
`[未定谳]` 那 2 字节差异**是否影响性能**，未做对照实验。**这是 A 线一个新增的未闭合项。**

### 1.2 测试环境**不是干净零售安装**（G3 / G5 = FAIL）

`[转引·W47 实算]` 六门不再是全 UNKNOWN：

| 门 | 结论 | 依据 |
|---|---|---|
| **G3** | **FAIL** | 真实游戏目录 `game.components()` 含 `cnc_ddraw` / `ddraw_ini` / `ipxwrapper` / `xwis`（`ares`/`phobos`/`syringe` 为 false） |
| **G5** | **FAIL** | `C07 = 85e0f7d5…` 经字节 + 版本资源定性为 **cnc-ddraw 7.1.0.0**：含字面串 `cnc-ddraw`/`CnCNet`/`cnc_ddraw`/`ddraw.ini`，`FileDescription "DirectDraw replacement"`，`FileVersion "7.1.0.0 (git~541b5de, master)"` |
| G1/G2/G4/G6 | 仍 UNKNOWN | 无外部零售介质、无独立权威登记、无第二独立介质；repo 内 **0** 个 `iso/cue/mdf/nrg/img/vhd/cab/7z/rar` |

`[签发]` **W43/W46 里「六门全 UNKNOWN」应更新为「2 FAIL + 4 UNKNOWN」**，overall 仍 `UNDETERMINED`、`retail_oracle_eligible = false`。

`[对 A 线的后果 —— 更重的一条]` `ddraw.dll` 是 **cnc-ddraw 7.1.0.0**（社区 DirectDraw 替代实现），**不是原版渲染器**。
⇒ 本会话反复说的「渲染侧不可测」，现在有了具体原因：**渲染路径根本不在原版 ddraw 上**。A 线的渲染侧结论在任何情况下都不能外推到原版环境。

---

## 2. 已闭合的一条旧悬案

`[转引·W47]` `db264305…` **本机确实存在（15 份）**，且 `D:\Red2\ra2youli\gamemd.exe` 由它独立复算命中；`ra2opt\cli.py:307-312` 把该值作为 `seed --verify` 的 expected。
⇒ `FINAL_RULING.md §5.1 L115` 标注的「Lead 未复算/未验」**现已闭合**。

---

## 3. `.detour` 独立复核（与我此前的裁决一致）

`[转引]` W47 用与 ra2opt 无关的 struct 解析器复核 **114/114**：`Characteristics = 0xC0000040` = `CNT_INITIALIZED_DATA|MEM_READ|MEM_WRITE`，**无 `MEM_EXECUTE`**；首 32 字节 `40 00 00 00 44 74 72 00 …` 与 `baseline_integrity_note.md:127-131` **逐字节一致**。
⇒ 支持裁决 D2（`detour_classification = westwood_native`）。但 D3（零售介质对照，决定性那一项）离线仍 `undetermined`。

---

## 4. 推荐值（我采纳，但不等于签发）

`[转引]` W47 推荐 `TARGET_BASELINE = ra2youli\gamemd.exe`（`73201cc0…`），理由：写靶的绝对路径 + `RE-N00/BASELINE.json` 与 `W7_load_baseline` 都登记此值 + 95 份互证。
`[我采纳为"工程口径"]` 因为它就是所有卡实际写入与测量的那一份。
`[但必须连写]` **它不是「干净零售金标准」**：`is_clean_retail_gold` 保持 **false**（裁决 D4），且 G3/G5 已 FAIL。**推荐 ≠ 证明。**

---

## 5. 我未核实 / 未签发

- 以上全部为 `[转引]` W47 的中途通报；**其最终报告尚未交付**，我未逐条复算它的 1703 份哈希与 6 组分组
- `D:\Red2\ra2youli\` 是**项目工作区之外**的路径，我未独立确认其存在与内容
- 那 2 字节差异对性能的影响：**未做任何实验**
- `BASELINE_CANDIDATES.json` 我未校验
