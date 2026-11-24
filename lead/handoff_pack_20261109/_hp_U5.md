# U5 —— B2B_DESIGN.md:148 镜像同步（JSON:2 的设计镜像，每条一页）

## 目标
- 文件：`lead/b2b_design_20261106/B2B_DESIGN.md`（SHA256 = 565771d8b31c516dc7a1e0100ea047484406a203390492df9f57170a6532feaf，66,735 字节，693 行——本轮实算）
- 行：**第 148 行**（§2 状态矩阵表数据行 1，第 3 列 condition；镜像 `STATE_MATRIX.json:2`）

## 原文整行逐字（本轮 Read 实读 :148）
```
| `unknown` | `unknown` | `pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后任意 | `unknown` | `none` | `None` | `false` |
```

## 改后整行逐字（改文正本：`_m5_cells.json` U5.new_condition_cell 起草、`U5U6_MIRROR_TEXTS.md` §3.1 成文交付；改文只动第 3 列 condition，不含管道符，不破坏 7 列表格与 14 行结构）
```
| `unknown` | `unknown` | `pre=None` / `{}` / 缺 `state` / 脏值（未采集或采集未完成），跑后读取正常（`post.read_error` 为空）；`post.read_error` 非空时先落 `post_read_error`（码序 `read_error` 出口先于 `unknown` 出口，见 :5 行） | `unknown` | `none` | `None` | `false` |
```

## 改文正本的时间线（如实登记，不取舍）
- `_uf_UNIFIED_FIX_LIST_20261109.md`（04:38）与 `UNIFIED_TEXT_FIX.md`（05:04）两份汇总件均**如实标注 U5/U6「两源均未给出逐字改文……不代拟」**（:92、:21）。
- 镜像逐字改文正本由 `lead/u5u6_mirror_20261109/` 写域**后补起草**（`_m5_cells.json` 05:15，`U5U6_MIRROR_TEXTS.md` 05:40 交付轮，复核 verdict=confirmed），待乙设计责任人批准。时间线自洽，无矛盾；本条改文唯一正本 = `_m5_cells.json` U5。

## JSON 侧 ↔ B2B 侧对照（U5U6_MIRROR_TEXTS §3.1 表转录）
| 段 | JSON 侧（pf2:193 逐字） | B2B 侧改文（去反引号） | 差异性质 |
|:--|:--|:--|:--|
| 谓词① | 跑后读取正常（post.read_error 为空） | 同文 | 仅反引号 |
| 谓词② | post.read_error 非空时先落 post_read_error | 同文 | 仅反引号 |
| 谓词③ | 码序 read_error 出口先于 unknown 出口，候选 :4643 先于 :4648，见 :5 行 | 码序 read_error 出口先于 unknown 出口，见 :5 行 | 白名单差＝「候选 :4643 先于 :4648，」（本表未改行省略行号指针的既有惯例） |
| 既有缩写 | 跑前快照未采集或采集未完成 | 未采集或采集未完成 | 白名单差＝「跑前快照」（原 :148 即为缩写，非新差） |

## 出处
- 镜像义务：B2B_DESIGN.md:144「下表与之逐行一致」（本轮实读 ✓）；滞留风险 pf2 §4.7-2:205；镜像必改 row5 §4.3-B:133、§4.5-1:153（只改 JSON 不同步 :148 = 双源不一致，且 T2/T5/重签件:154 条件 2 均抓不到）。
- 事实底座（pf2 §4.7-3 本轮 grep，转引）：「任意文件状态」B2B 0 命中、「跑后任意」仅 :148 一处、JSON 仅 :2 一处。

## 需谁批准
**乙设计责任人**（row5 §5.4-2:185；pf2 §4.7-2 同主体）。改后乙设计指纹变 → V2:45 + 重签件 §2 第 4 行（:33）+ :153 生效条件 1。

## 依赖关系
- **与 U2 成对、六处同批**（P3）：单侧落盘即破 :144「逐行一致」硬声明。
- 「见 :5 行」坐标歧义（P2）适用于本行。
