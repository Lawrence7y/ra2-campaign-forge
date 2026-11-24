# M71-MERGE — 并表 11 行（S22_B4，已审 PASS 11/0）+ 第三条披露

## 独占写权

本轮**只有你**可以写 `COVERAGE\coverage.tsv` 与 `COVERAGE\PANEL.md`。
不许 git commit；不许碰 `R14_COMMON.md`、`STATUS_BOARD.md`、台账、`NAMED_PUSH_*`、`NAMED_PUSH_AUDIT*`、`INVENTORY`。

改动前记两文件 `mtime`/字节/`sha256`，改后再记，写进 `MERGE_M71\BEFORE_AFTER.txt`。

## 并什么（11 行）

- 审计表：`NAMED_PUSH_AUDIT12\verdict.tsv`（11 行，全部 PASS）
- delta 来源：`NAMED_PUSH_S22_B4\delta.tsv`
- 交集必须正好 **11 行**；不是就**停下报告**

**不进并表**：`NAMED_PUSH_S22_B5\delta.tsv` 为空（9 行 vector 族四环齐全 0，③b 全败于 `{0,1}` AL 布尔）。

## Lead 已核过的前置（不符就停下）

- 现盘上：数据行 **18,498**、全表 `[已证]` **1,591**、atlas 内 **1,585**、atlas 外 **6**、S22（atlas 内 proved）**98**
- 11 行 atlas 内与否自己核（`entry` 小写须归一）

## 改什么

`coverage.tsv` 这 11 行各改 3 列：第 4 列语义 ← delta 原文；第 5 列 → `[已证]`；第 6 列 → `NAMED_PUSH_AUDIT12/VERDICT.md`。
第 1、2、3、7、8 列不动。数据行仍 18,498、8 列、制表符分隔。

## `PANEL.md` 同步

- S22（atlas 内 proved）**98 → 109**（以你实算为准）
- 全表 `[已证]` **1,591 → 1,602**；atlas 内 **1,585 → 1,596**
- 严格双列表按权威口径（`[未证]` 字面）
- 备注列追加：`M71 并表 NAMED_PUSH_AUDIT12 PASS 11 行（S22_B4 工厂族）；S22 named 池至此清空（B1 18 + B2 18 + B3 13 + B4 13 + B5 9 = 71 = 全池），B5 的 9 行 vector 族四环齐全 0（③b 全败于 {0,1} AL 布尔）`
- **达标判定不得改变**；若翻转，**停下报告**

## 必须追加的第三条披露（**原样写入，不许改写**）

接在 M70 披露之后：

```
> ⚠️ **M71 披露：④ 的严格读法会翻转 ≥21 行（未执行，待成文规则）**
> `a-S22B4` 审计指出并请 Lead 裁定：若把 ④ 收紧为「镜像内必须存在对该 vt 槽的**实际派发**」，则本批 11 行全部翻为 FAIL，并会连带推翻 `NAMED_PUSH_AUDIT2` 已判 PASS 的 10 行。
> Lead 处置：**不追溯、先披露**。理由：该收紧属口径变更而非发现事实错误，按 `R14_COMMON` 既有纪律「口径收紧需一次成文裁决 + 一次性整批处置，不得零散改判」。
> 另据同审计独立核验，更正 M70 披露的强度：M70 的「本 entry 返回码无消费方」在**静态意义上准确**（11 个 CLSID 与 21 处 `CoCreateInstance` 的静态集合交集为空、每个 CLSID 全镜像仅 2 处引用），但**不得写成绝对**——镜像内存在 `0x41C250`（13 个调用者）这类按 CLSID 创建路径，运行期仍可能产生消费方。
> 另需账：该族 `AddRef`/`Release` 是 `mov eax,1; ret 4` 桩，**Release 实际不释放**；「失败 Release 新建对象」走的是 vt+0x20（slot8 删除析构器，`push 1`），不是 Release。
```

## 交付

- `MERGE_M71\MERGE_LOG.md`、`BEFORE_AFTER.txt`、`VERIFY.txt`
- `VERIFY.txt` 必须含：并行数、数据行数、全表/atlas 内/atlas 外 `[已证]`、S22 的 proved 与 strict、**有无达标翻转**、**M71 披露段落行号**
