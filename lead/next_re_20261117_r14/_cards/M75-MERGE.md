# M75-MERGE — 并表 22 行（S18 九 + S15 十 + S17 三，均已审 PASS）

## 独占写权

本轮**只有你**可以写 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md`。
不许 git commit；不许碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`BOARD_ARCHIVE.md`、任何 `NAMED_PUSH_*` 与 `AUDIT*`、`INVENTORY`。

改动前记两文件 `mtime`/字节/`sha256`，改后再记，写进 `MERGE_M75\BEFORE_AFTER.txt`。

## 并什么（22 行）

| 组 | 审计表 | delta 来源 | 应并行数 |
|---|---|---|---:|
| A | `NAMED_PUSH_AUDIT17\verdict.tsv` | `NAMED_PUSH_S18_B5\delta.tsv`（9）+ `NAMED_PUSH_S17_B1\delta.tsv`（3） | **12** |
| B | `NAMED_PUSH_AUDIT18\verdict.tsv` | `NAMED_PUSH_S15_B1\delta.tsv` | **10** |

交集必须正好 12 + 10；不是就**停下报告**。

## Lead 已核过的前置（不符就停下）

- 22 行 delta 全部 6 列、`entry` 为 8 位大写十六进制无 `0x`、`grade = [已证]`、22 个 entry 互不相同（Lead 已核）
- 现盘上：数据行 **18,498**、全表 `[已证]` **1,621**、atlas 内 **1,615**、atlas 外 **6**
- 当前 atlas 内 proved：S18 **57**、S15 **106**、S17 **56**
- 22 行 atlas 内与否自己核（`entry` 小写须归一）

## 改什么

`coverage.tsv` 这 22 行各改 3 列：第 4 列语义 ← delta 原文；第 5 列 → `[已证]`；第 6 列 → A 组 `NAMED_PUSH_AUDIT17/VERDICT.md`、B 组 `NAMED_PUSH_AUDIT18/VERDICT.md`。
第 1、2、3、7、8 列不动。数据行仍 18,498、8 列、制表符分隔。

## `PANEL.md` 同步

- S18 **57 → 66**、S15 **106 → 116**、S17 **56 → 59**（以你实算为准）
- 全表 `[已证]` **1,621 → 1,643**；atlas 内 **1,615 → 1,637**
- 严格双列表按权威口径（`[未证]` 字面）
- 备注列追加：`M75 并表 NAMED_PUSH_AUDIT17 PASS 12 行（S18_B5 9 + S17_B1 3）+ NAMED_PUSH_AUDIT18 PASS 10 行（S15_B1），evidence_path 分别改指两审计 VERDICT；006E3E30/006E57A0 两行早先 a-S15S16-3B2 判 FAIL，本批换 ③ 依据后过审`
- **达标判定不得改变**；若翻转，**停下报告**

## 必须追加的第五条披露（**原样写入，不许改写**）

接在 M74 披露之后：

```
> ⚠️ **M75 披露：④ 的「仅安装点」形态与最弱行**
> `a-S18S17` 审计指出：`007B26D0` 的 ④ 是全批最弱——执行器写「装活 vt **+ 派发**」，但实测该行直调 0 条、`call [reg+0x44]` 从 `0x887628` 取对象 **0 命中**，全镜像 131 处该偏移无一能钉到本类实例。审计按已入账先例判 PASS，但明确：**若不接受「仅构造器安装点、无可证派发」这一形态，翻转的是 `007B26D0` 加 S17 的 3 行（`004A2CD0`/`006BEF10`/`006BF690`），其余 8 行不受影响。**
> 另：`007B1BC0`/`007B2630`/`007B26D0` 三行各被 2–3 张虚表同时持有（IPX 与 UDP 的 chd base[1] 都是 Winsock，实现由基类 Winsock 定义），执行器只引 IPX 表——字节为真但不完整，审计已补全枚举。
> 另：`006E3E30` / `006E57A0` 两行在早先 `a-S15S16-3B2` 审计中**被判 FAIL**（理由：模板假句／对象初始化）；本批换了 ③ 依据重新主张，`a-S15B1` 认同新依据并确认旧的「对象初始化」假句已删除，故判 PASS。**引用这两行时须同时引用本披露。**
```

## 交付

- `MERGE_M75\MERGE_LOG.md`、`BEFORE_AFTER.txt`、`VERIFY.txt`
- `VERIFY.txt` 必须含：两组并行数（12+10）、数据行数、全表/atlas 内/atlas 外 `[已证]`、S18/S15/S17 的 proved 与 strict、**有无达标翻转**、**M75 披露段落行号**
