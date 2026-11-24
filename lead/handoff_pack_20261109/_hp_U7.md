# U7 —— B2B_DESIGN.md:150 镜像加句（JSON:4 的设计镜像，每条一页）

## 目标
- 文件：`lead/b2b_design_20261106/B2B_DESIGN.md`（同 U5 件）
- 行：**第 150 行**（§2 状态矩阵表数据行 3，第 3 列 condition；镜像 `STATE_MATRIX.json:4`）

## 原文整行逐字（本轮 Read 实读 :150）
```
| `error` | `error` | 跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口 | `error_pre_snapshot` | `none` | `None` | `false` |
```

## 改后整行逐字（加句 = 源定同句 row5:135 / 统一清单:83、:111 逐字「（post.read_error 非空时仍先落 post_read_error，见 :5 行）」，cell 端拼接；无反引号 =「同句」字面要求——U5U6_MIRROR_TEXTS §3.3）
```
| `error` | `error` | 跑前采集抛异常（`snap.error` 非空）⇒ 独立 error 出口（post.read_error 非空时仍先落 post_read_error，见 :5 行） | `error_pre_snapshot` | `none` | `None` | `false` |
```

## JSON 侧对照
- 加句与 JSON:4 为**同句逐字（零字面差）**。JSON:4 既有尾句「，不降级、不静默、不给 high」为白名单差（原 :150 即无此尾句，非新差）。
- JSON:4 推荐拼后全文（拼接点系 `_m5_cells.json` 推荐＝「独立 error 出口」之后，源件未逐字指明——P6，最终由批准人定）：
```
跑前采集抛异常（snap.error 非空）⇒ 独立 error 出口（post.read_error 非空时仍先落 post_read_error，见 :5 行），不降级、不静默、不给 high
```

## 出处
- 源② row5 §4.3-B:135「B2B_DESIGN.md:150 镜像同句」；镜像义务 B2B_DESIGN.md:144（本轮实读 ✓）。
- 事实底座：W2 本体 = 源③ W2_SAME_CAUSE.md §4.2:100（同 U4）。

## 需谁批准
**乙设计责任人**（同 U5）；可推迟性同 U4（row5:135「不加则须在登记中如实保留 W2」）。级联同 U5。

## 依赖关系
- **与 U4 成对、六处同批**（P3）；受范围准冲突①（P1）辖。
- 「见 :5 行」坐标歧义（P2）适用于本行。
