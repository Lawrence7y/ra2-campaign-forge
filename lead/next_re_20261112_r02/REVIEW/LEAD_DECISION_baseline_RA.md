# LEAD_DECISION · R-A 基线语义与 W47 待办收口

> 裁决人：Lead（本会话）｜ 时间：2026-11-13 22:10
> 触发：W47（`W47_baseline_adjudication\BASELINE_ADJUDICATION_RESULT.md` 37,511 B + `BASELINE_CANDIDATES.json` 1.33 MB）提出 5 项需 Lead 动作

---

## ① R-A 基线语义 —— **裁定：`73201cc0…`（写靶现状），但守卫必须同时认 `db264305…`**

### 裁决
| 轨 | 值 | 语义 |
|---|---|---|
| **R-A `TARGET_BASELINE`** | `ra2youli\gamemd.exe` = **`73201cc0…`** | **写靶绝对路径上的现状字节**（W38-S1 §5 R7 的定义） |
| **R-B `RETAIL_ORACLE`** | **UNDETERMINED** | G1/G2/G4/G6 UNKNOWN、G3/G5 FAIL ⇒ 不设 |
| 参考态 | `ra2youli\.ra2opt\orig\gamemd.exe` = **`db264305…`** | **`pre_ra2opt_reference`**，不是基线 |

理由：R-A 的定义是「我们往哪儿写、写完对着谁比」，那就是写靶路径上的现状。`db264305…` 是 ra2opt 的**备份快照**，不在写靶路径上，`FINAL_RULING §5.1:113` 也已裁它不能当零售 oracle。

### 但必须连写的一条（否则守卫会误报）
`[本次实测]` 两态**仅差 2 字节**（`0xAE` DllCharacteristics、`0xB2` SizeOfStackReserve），**`.text` raw SHA 完全相同**（`c0368a17…`）。
`[后果]` 若用户跑过一次 `ra2opt restore`，写靶字节会变成 `db264305…` ⇒ 版本守卫会判 **MISMATCH** 并拒绝写入 —— **这是假阳性**（用户的游戏其实是好的，只是被还原过）。

⇒ **裁决：版本守卫必须把两个态都认作 KNOWN，并在报告里标明当前是哪一态**：
```
ACCEPT: 73201cc0…  -> state=TARGET_CURRENT      (ra2opt applied)
ACCEPT: db264305…  -> state=TARGET_RESTORED     (ra2opt reverted, same .text)
REJECT: 其他        -> MISMATCH
```
并额外要求：判据应包含 **`.text` raw SHA 相等**这一条，这样即使将来出现第三个变体（只改头不改代码）也能被正确归类为「同代码不同头」，而不是直接 MISMATCH。

`[责任归属]` 这条属于 S4/S5 的守卫实现，不在 W47 范围；登记为 **G-17（新增）**。

---

## ② `--target-dir` / `--baseline-id` —— 给出，但**签发 BASELINE.json 还需一次重跑**

```
--target-dir  D:\Project\ra2-campaign-forge\ra2youli
--baseline-id RA2YR-CN-73201cc0-L1
```
`[未签发的理由]` W47 自己指出：**P0/P1 是时点快照，签发前须在无并发真机卡时重跑**。当时 W45 正在跑。
`[现在状态]` `[本次实测]` 22:10 锁为 `owner=lead`、`gamemd` 残留 0 ⇒ **已静默，可以重跑**。
`[但我暂不派卡]` 按用户指示「不用全都排满」，且这一轮已有 3 张卡失败。**这一步留给下一轮**，届时只需重跑 P0/P1 两步（v2 脚本 3.0 s），不需要重做全量。

---

## ③ 引用六门时必须改口 —— 已采纳

`[签发]` 以后凡引用 W43/W46 的「G1–G6 全 UNKNOWN」，一律写成：
> **G1/G2/G4/G6 = UNKNOWN，G3/G5 = FAIL（由 W47 实算），overall = UNDETERMINED、`retail_oracle_eligible = false`**

`G3 = FAIL`：真实游戏目录含 `cnc_ddraw` / `ddraw_ini` / `ipxwrapper` / `xwis`（`ares`/`phobos`/`syringe` 为 false）。
`G5 = FAIL`：`ddraw.dll` = **cnc-ddraw 7.1.0.0**（`FileDescription "DirectDraw replacement"`、`FileVersion "7.1.0.0 (git~541b5de, master)"`），**不是原版渲染器**。
`[注意]` W47 说明：61 个「干净」目录只是仅含 `gamemd.exe` 的夹具目录，**没有被拿来凑 PASS** —— 这个自律要保留。

---

## ④ 外部零售介质 —— 接受为长期未闭合项

`[转引]` 仓库 582,702 个文件中 **0 个** `iso/cue/mdf/nrg/img/vhd/vhdx/cab/7z/rar`。
`[裁决]` 在这一前提下 **D3（零售介质对照，决定性判据）永久 undetermined** ⇒ `detour_classification = westwood_native` 依据的是 D2（结构性判据：C02 114/114、EP 在 `.text` 114/114、IAT 目录[12] 指向 `.rdata` 不在 `.detour`），**不是 D3**。这条区分要写清。

---

## ⑤ 「第三方 Detours」旧口径文档债 —— 登记，不由 W47 修

`[转引]` W47 登记 4 处未更正的旧口径（它纪律禁止改 `ra2opt/` 与 `W21`–`W46`）。
`[我的裁决]` 与 D2 一致：**`westwood_native`**。这 4 处属**文档债**，不是事实争议 —— 事实已由 D2 判据确定为原生。
`[处置]` 不派人追修（成本 > 收益）；在 `REVIEW\LEAD_DECISIONS_W42.md` D2 里已记明「`ra2opt\__init__.py:25`、W38 `D-W38-11`、`FINAL_RULING.md §5.1` 的『第三方』措辞属未更正的旧口径」，以后引用一律以 D2 为准。

---

## ⑥ 对 A 线的最终注记（我此前已记，这里定稿）

`[签发]` A 线全部性能数据的环境事实，引用时必须连写三条：
1. 镜像 = **`73201cc0…`（ra2opt 已施态：`.text` 与原始态逐字节相同，仅 DllCharacteristics 与 SizeOfStackReserve 两字节不同）**
2. 渲染 = **`ddraw.dll` 是 cnc-ddraw 7.1.0.0 替代实现，不是原版**
3. 安装目录 = **非干净零售**（含 `ipxwrapper`/`xwis`/`ddraw_ini`）

⇒ A 线的任何结论**都不能外推到原版零售环境**。这不是免责声明，是环境事实。

`[新增未闭合项]` 那 2 字节（尤其栈保留 1→4 MB）对性能的影响**未做对照实验** ⇒ 登记 **G-18**。
