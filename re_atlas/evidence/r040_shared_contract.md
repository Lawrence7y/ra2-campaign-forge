# R-040：P1 共享库沉淀 —— 机器可读的 vtable/类型/尺寸契约

**日期**：2026-10-23
**性质**：离线，零真机。只读 `ra2youli/gamemd.exe`（sha256 `73201cc0…f67476`，未改动）。
**门禁**：`tools/r040_shared_contract.py` → **6/6 PASS, EXIT=0**（`evidence/r040_verify.txt`）
**变异**：`tools/mutate_r040_gate.py` → **4/4 killed（精确集合判定）, EXIT=0**（`evidence/r040_mutation.txt`）
**交付物**：`evidence/class_contract.json`（schema `ra2-atlas/class-contract/v1`，16,756 B）

---

## 一、本轮是什么

章程 §3 的 P1：「共享库沉淀（可被 GOAL-3T 复用的虚表/类型/尺寸契约）」。
此前契约存在于散文（kb/20）、文本表（class_ids.txt）与各轮门禁里——消费方要
自己重推或重解析。本轮把它压成**一个 json**，全部数值在生成时从字节重读，
不从旧证据件复制，消费方可逐行复算。

## 二、契约内容（json 的三层）

1. **`classes[69]`**：每个最派生 `AbstractClass` 叶子类的
   `{class, vtable, slots, id, id_hex, size, id_fn, size_fn, engine_name}`。
   用法（写在 `scope` 字段里）：对**具体实例**，`vtable[11]`  callee 返类型 ID、
   `vtable[12]` callee 返实例尺寸。
2. **`abstract_bases[9]`**：9 个中间基类名单——槽 11/12 指向抽象桩，
   **对它们这套读法不成立**（R-037 的作用域修正进数据本身，不再只活在散文里）。
3. **`addresses` + `population`**：名字表 `0x816EE0`（74 项）、桩 `0x4C9150`
   （字节 `33c0c3` 一并登记）、988/954/804/78 的漏斗数。

## 三、门禁 6 条的构成（v5 §7 诚实清点）

| 断言 | 钉什么 | 可杀性 | 杀手 |
|:--|:--|:--|:--|
| C1 | 镜像哈希 | 恒真项 | 单列，不计 PASS 数 |
| C2 | 988/954/804 漏斗 | **结构性普查**（数来自 symbols.json，不随字节变异变红） | 具名标注 |
| C3 | 69 个符合类、id 零冲突、值域 | 字节可钉 | 破坏 `0x71FA60`（TEventClass WhatAmI）⇒ 69→68 红；或名字表 0x46 复制成 0x45 ⇒ 同红 |
| C4 | 名字表 74 项、**值集合 = {0x00..0x49}** | 字节可钉 | 同上 0x46→0x45 复制 ⇒ 集合缺 0x46 红 |
| C5 | 9 具名基类双指桩 + **桩字节 = `33c0c3`** | 字节可钉 | `0x4C9150=0x90` ⇒ 内容合取红（指针合取仍绿，正是要测的分工） |
| C6 | 78 = 69+9 闭合、全叶子、不外溢 | **结构性普查**（划分恒等 + bases 来自 symbols.json） | 具名标注 |
| C7 | 4 个正对照 (id,size) 直读吻合 | 字节可钉 | TEventClass / HouseClass callee 破坏 ⇒ 对应控制红 |

**变异 4/4 killed（精确集合）**，每个字节可钉断言都有专属杀手，红集互不相同。

## 四、本轮抓到的两件事

### 4.1 kb/20 §1 勘误：「严格递增」是错的，「无空穴」对

门禁 C4 初版断言照抄了 kb/20 散文「`value` 严格递增 `0x00..0x49`」——**首跑变红**。
实测：名字表**存储顺序非单调**（条目 69=`Temporal(0x46)`、条目 70=`RadSite(0x45)`，
1 处非递增），但**值集合恰为 {0x00..0x49}、74 个不同值** ⇒「无空穴」成立、
「严格递增」不成立。kb/20 §1 已加勘误横幅。

**方法论意义**：这正是铁律「门禁要断言取值不是存在/散文」的正向演示——
**散文里的形状词（递增/单调）不能直接搬进断言，要从字节重新判。**
若我照抄原断言「修绿」（改成 first=0x00 last=0x49 就放行），勘误会一直留在 kb/20。

### 4.2 我自己的变异目标连错两次（G-55 第四、五次）

初稿 `mutate_r040_gate.py` 的目标从记忆推测：① HouseClass GetSize 写成了
`0x423600`（实测 `0x504730`）；② 预期红集从「应该级联」推出来（实际 C5 因
`len(gap)==EXP_GAP` 合取被 reclassify 耦合，每例都陪红）。
**纠正流程**：先跑基线、再逐变异实测红集、最后才把实测值写成预期——
并把这条流程写进了变异套件 docstring。C5 随之解耦（不再引用派生集 `gap`，
改为逐个具名核对 GAP_NAMES，只测桩本身）。

## 五、诚实边界

1. **`id`/`size` 的正确性继承 kb/20 的全部边界**（含「17 个函数名未逐条验证」类
   的字面量≠语义问题在这里不存在——id/size 是字节直读，但 id→类名映射的
   7 条别名仍见 kb/20 §3.1）。
2. **C2/C6 是结构性普查**，已在输出里具名标注；「6/6 PASS」中真正被字节变异
   钉死的取值断言是 C3/C4/C5/C7 四条。
3. **名字表是 `.data`（可写段）**：补丁若改运行期内存，id↔name 映射可变；
   静态契约不覆盖这种情形（登记，非缺陷）。
4. **未做异族盲验**（新欠账，与 R-036/037/038 同批）。
5. **symbols.json 的 `bases` 若有缺失**，`descends` 闭包会漏类 ⇒ 69/78 可能偏小；
   抽查 House/Techno/Foot 链未见缺失（R-037 §7.3 同款边界）。

## 六、复跑

```bash
python re_atlas/tools/r040_shared_contract.py > re_atlas/evidence/class_contract.json 2> re_atlas/evidence/r040_verify.txt
python re_atlas/tools/mutate_r040_gate.py    > re_atlas/evidence/r040_mutation.txt 2>&1
```
