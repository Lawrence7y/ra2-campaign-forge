# LEAD_VERIFY_W80 · `survive` 斜率**不由三个配置旋钮决定**（7 趟否证；卡死前数据完整，我据原始产物签发）

> 记录人：Lead｜时间：2026-11-14 09:58｜卡：W80（Hy4，真机 7 趟；**卡在写报告前失败**）
> 说明：`agent-1 failed`（其最后一句是 `Clean. Running E3 s20.`）。但它把 7 趟的 `TRIP_RESULT.json` + 每趟 `CONFIG_PRE.json`（含行级 before/after）全部落盘，**我据原始产物签发，不依赖它的报告**。真目录我先核查过未被污染（见 §5）。

## 1 · 7 趟数据（我逐趟读 `TRIP_RESULT.json`）

| 趟 | condition | 改动 | 图 | 判胜 frame | game_seconds |
|---|---|---|---|---:|---:|
| `trip_base_s8` | `base` | **无** | `survive(8)` | **210** | 6.72 |
| `trip_base_s20` | `base` | **无** | `survive(20)` | **390** | 12.48 |
| `trip_e1_30_s8` | `e1_30` | `ddraw.ini [ddraw] maxgameticks 0→30` | `survive(8)` | **210** | 6.72 |
| `trip_e1_30_s20` | `e1_30` | 同上 | `survive(20)` | **390** | 12.48 |
| `trip_e2_gs2_s20` | `e2_gs2` | `RA2MD.INI [Options] GameSpeed 1→2` | `survive(20)` | **390** | 12.48 |
| `trip_e2b_all_s20` | `e2_gs2_all` | `RA2MD.INI` **三行** GameSpeed 1→2（行 39/58/75） | `survive(20)` | **390** | 12.48 |
| `trip_e3_unlock_s20` | `e3_unlock` | `ra2render.ini [Speed] UnlockGameSpeed 0→1` | `survive(20)` | **390** | 12.48 |

**结论：四个旋钮改动后判胜帧与基线完全相同（210 / 390），零影响。**

## 2 · 单变量纪律（我核了每趟 `CONFIG_PRE.json` 的 `edit` 与 `config_diff_vs_pristine`）

| 趟 | `diff_vs_pristine` | 行级 before → after | 文件 sha256 before |
|---|---|---|---|
| `base_s8` / `base_s20` | **`[]`**（无改动） | — | — |
| `e1_30_*` | `["ddraw.ini"]` | `maxgameticks=0` → `=30`（line_index 88，CRLF） | `c983abad…` |
| `e2_gs2_s20` | `["RA2MD.INI"]` | `GameSpeed=1` → `=2`（line 75，CRLF） | `c91c6a47…` |
| `e2b_all_s20` | `["RA2MD.INI"]` | **`*all*`：3 行**（39/58/75）`1`→`2` | `c91c6a47…` |
| `e3_unlock_s20` | `["ra2render.ini"]` | `UnlockGameSpeed=0` → `=1`（line 53，**LF**） | `27c9a60c…` |

`[签发]` **每趟只改一个文件**，`diff_vs_pristine` 恰好列那一个；且有行级 before/after + 前后 sha256。**单变量纪律成立。**
`[它额外做对的一步]` `e2b_all` 把 `RA2MD.INI` 里**三处** `GameSpeed` 一起改（行 39/58/75）—— 回应了我提的"哪一段生效"问题：**三段一起改也没有影响**，所以不是"改错了段"。

## 3 · 判定

`[签发]`
- **H-A（`maxgameticks` 决定斜率）否证** —— 两点（s8 与 s20）均不变。
- **H-B（`GameSpeed` 决定斜率）否证** —— 单段与三段一起改，均不变。
- **H-C/E3 变体（`UnlockGameSpeed` 放开游戏速度控制）否证** —— 不变。

`[结论]` **`survive` 的 `15` 斜率不由这三个配置旋钮决定。** `frame = 15N + 90` 仍然成立且仍然**未被解释**。
`[对照我提的 H-E（`[静态推断]`，未证）]` 「引擎把 **15 帧**当 1 秒、实际渲染 31.25/s ⇒ 时间流速 2.08×」能同时解释三件事（斜率恰为 15、E1/E2/E3 全无效、引擎自报时间 ≈ frame/31.25 取整）。**但这只是解释性假说，无直接观测**（要证实需在 `gamemd.exe` 里找到"秒定义 = 15 帧"的常量）。**本卡未做该静态检索**，我也不据此签字。

## 4 · 基线复现（第三次）

`base_s8 = 210`、`base_s20 = 390` —— 与 W79 的 `210 / 390 / 915` 三点**完全一致**。⇒ `frame = 15N + 90` 的**可复现性现在是 3 批独立真机（W79 三点 + W76 十点 + W80 两点）共 15 个点**。

## 5 · 真目录与锁（W80 死在中途，我核查了）

`[我亲自核]` 真目录 5 个锚点全部与期望一致：`gamemd.exe = 73201cc021497c95…`（**未打补丁**）、`ddraw.dll = 85e0f7d5…`、`RA2MD.INI = c91c6a47…`、`BATTLEMD.INI = 7e40691a…`、`ra2md.mix = 69d886de…`。
⇒ **它死在中途但没有污染真目录**（改配置只发生在 `sandbox_game\`，每趟 `knob_restore` 都记了 `byte_identical: true`）。
锁 `owner=lead`、`gamemd` 残留 0。

## 6 · 一条操作层面的教训

`[本次实测]` W80 在"跑完 E3、准备写报告"时死掉，**7 趟数据全部保留**、但**没有一个字的报告**。
⇒ 这印证了本项目反复出现的模式：**卡的价值在产物，不在自述**。我这次能完整签发，是因为它每趟都小步落盘（`TRIP_RESULT` + `CONFIG_PRE` 逐趟写），而不是最后一次性写。
`[反过来看]` 若它把 7 趟结果攒在内存里最后一起写，这次就全丢了。**"每趟落盘"这条要求是有效的。**

## 7 · 未闭合

- `15` 的**机制**仍未定谳（三个配置旋钮已排除）。
- 剩下的可查方向：① 在 `gamemd.exe` 里静态检索"秒定义 = 15 帧"的常量（`[静态推断]` H-E 的证实路径）② 若有 `ddraw`/`render` 日志记录 tick 率，直接读 ③ 换一台机/换一个镜像看斜率是否随环境变（若不变，说明是引擎内建常数）。
