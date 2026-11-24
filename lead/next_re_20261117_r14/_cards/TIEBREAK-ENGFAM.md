# TIEBREAK-ENGFAM — 对 S17 英文族 34 行 PASS 结论的异族反审

## 你为什么要审这一份

已有审计员（异族 A，模型 Zhipu）对 S17 英文措辞族 34 行给出 **34/34 全 PASS**，主张：

- 35 个槽（`Save_VectorBlock_01..35`，缺 #17）是**逐字节同模板**；
- 模板 = `Write(&Count,4,NULL)` @`+0x1D` → 有界循环 → `QI(IID_IPersistStream @0x7F7C80)` @`+0x49` → `ole32!OleSaveToStream` 经 IAT `0x7E15F4` @`+0x55` → `Release`；
- HRESULT 可证伪；
- 「class name unproven」是"当时没查"而非"查不到"，35 个元素类已用构造写入 + RTTI 定死；
- 结论：S17 实质存活 = 21 + 34 = 55，达标。

**这份结论有两个可质疑处，你必须正面处理：**

1. 它的 `verdict.tsv` 里 **34 行 reason 文字完全相同**（模板复制），且 `entry` 列写成 `0x0067FDF0` 而 `coverage.tsv` 是 `0067FDF0`。高度一致的逐行结论 + 复制式理由，正是容易被"同族所以都成立"一句话带过的形态。
2. 它把「循环体内的非栈写」作为 ③b④ 的依据，但那个写发生在**被调用的 `IStream::Write` 里**，不是循环体内的写指令。这正是 `0045A640` 被推翻时用过的那条界线。

你是**异族 B（模型 DeepSeek）**。不要替它辩护，也不要为了"抓错"而硬判 FAIL。只认字节。

## 目标与材料

- `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（先自校验）
- ImageBase `0x400000`，`.text = [0x401000, 0x7E038D)`
- capstone 5.0.7（**必须 `skipdata=True`**）+ pefile 2024.8.26，Python 3.12.10，无 venv、不许 pip install
- 待核清单：`S17_ENGFAM\verdict.tsv`（34 行）、`S17_ENGFAM\VERDICT.md`、`S17_ENGFAM\SUMMARY.md`、`S17_ENGFAM\EVIDENCE\`、`S17_ENGFAM\work\`（**都只当线索**）
- 34 行在 `coverage.tsv` 里：语义匹配 `(?i)unproven|unverified|not proven`，全部 S17、全部 `[已证]`

## 必须做的三件事

### 一、抽 6 行独立复核（不许复用被审方的结论）

抽样规则：取该族地址**最小的一行**、**最大的一行**，再在中间均匀取 **4 行**，共 6 行。把抽样命令与 6 个 entry 写进报告。

对每一行，自己反汇编，逐项给地址与字节：

1. 循环是否真实存在？回边指令地址、目标地址、循环上界从哪个字段读。
2. 循环体内**是否有真正的非栈写指令**（`mov [reg+disp],…` 且 `reg` 不指向栈）？有就给地址与字节；没有就明确写"循环体内无非栈写指令"。
3. `IStream::Write` / `QI` / `OleSaveToStream` / `Release` 这几处调用是否真实存在？给出调用点地址、目标（IAT 槽或直接地址）、以及 `QI` 用的 IID 常量地址。
4. **HRESULT 是否被调用方检查**？即：失败返回值有没有进入一个分支。给出 `test eax,eax` / `cmp` 与随之的 `jl/jne` 地址。这一条决定 ③b② 能不能成立。
5. ② 类身份：元素类的 RTTI 名能否真取到？给出 RTTI 描述符地址与名字字符串地址。

### 二、裁定 ③b 的子形态（这是本卡的核心）

对每个抽样行，分别给出两个独立判定：

- **③b② 判定**：HRESULT 或返回约定是否**可伪证**（存在检查分支）。`yes` / `no` + 依据地址。
- **③b④ 判定**：循环体内**是否存在非栈写指令**（注意：写发生在被调用者内部**不算**本函数的循环内写）。`yes` / `no` + 依据。

然后明确回答：

> 这 6 行里，靠 ③b② 成立的有几行？靠 ③b④ 成立的有几行？两者都不成立的有几行？

**这一问的答案决定整族怎么记。** 若主要靠 ③b② 成立，那么被审方"③b④ 有界循环带非栈写"的描述属于**措辞用错但结论仍成立**；若两者都不成立，则 34 行必须全部退回。

### 三、能否外推到 34 行

- 6 行是否是同一模板？给"是/否"与证据（指令序列同一性、偏移同一性）。
- 若同模板：外推的条件是什么？（例如"模板同一性 + 每行的 Save_Core 向量不同但结构相同"）并说明外推的**残余风险**是什么。
- 若不同模板：指出哪几行不同、不同在哪。
- 顺带核一件事：被审方说缺号的 #17 是 `0x6805F0`。而 `coverage.tsv` 里 `006805F0` 是 **S05**、名字 `Unsorted::Save_Sides`、`[已证]`。请判断：`0x6805F0` 到底是不是该族第 17 个成员？给字节依据。若它不是同模板成员，那"35 个槽"的说法要改成多少？

## 输出

- `TIEBREAK_ENGFAM\VERDICT.md`：三节对应上面三件事，抽样行逐行给地址与字节
- `TIEBREAK_ENGFAM\sample.tsv`：表头 `entry	ring3b2	ring3b4	hr_checked_at	loop_write_at	verdict	reason`，6 行数据
- `TIEBREAK_ENGFAM\FAMILY.md`：整族裁定 + 外推条件 + 残余风险 + `0x6805F0` 归属判定

## 纪律

- 结论要么 PASS 要么 FAIL，不许"基本成立"。
- 每个 PASS 必须有你自己反汇编出的地址；引用被审方的数字要标明"引自被审方，未独立复核"。
- **不许修改** `coverage.tsv`、`PANEL.md`、`R14_COMMON.md`、台账；只写 `TIEBREAK_ENGFAM\`。
