#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Append §867: 143 arrays, not 49; there are 12 AbstractClass* vectors, not one."""
import io

LED = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"

SEC = """
## §867 · **实例数组总数是 143 不是 49；且 `AbstractClass*` 有 12 个不同的数组 —— `0xB0F720` 不是"唯一的主注册表"**（2026-11-15 15:20）

> 来源：DeepSeek 子代理 `ds-t1-arrays` 的全量枚举，**关键基址由我逐条复验**。
> 性质：**补全 §859-7-4 那条我自己登记的限制**，同时削弱 §859 对 `0xB0F720` 的定性。

- **§867-1 [已证·数量]** 全镜像机械枚举（`.text` 里 `C7 05 <base> <vftable>` + RTTI 链）得到
  **142–143 个 `DynamicVectorClass<T*>` 全局**（`vector_globals.tsv` 143 行含表头，实测 142 个基址）。
  **我 §859 只找到 49 个 —— 漏了 93 个。**
  - 与我那 49 个的关系：**49 个全部包含在内，我方无独有项**（差集为 0）。
  - 那 49 处表面"类型分歧"**不是真分歧**：T1 只报元素类型（`UnitClass*`），我报完整实例化（`DynamicVectorClass<UnitClass*>`），两者一致。

- **§867-2 [已证·`AbstractClass*` 有 12 个数组，不是一个]**
  下列 12 个基址全部是 `DynamicVectorClass<AbstractClass*>`（同一虚表 `0x007E91EC`）：
  | # | 基址 | Items | Count | 初始化器 |
  |---|---|---|---|---|
  | 1 | `0x00B0F5B8` | `0x00B0F5BC` | `0x00B0F5C8` | `0x7254ED` |
  | 2 | `0x00B0F5D8` | `0x00B0F5DC` | `0x00B0F5E8` | `0x7256ED` |
  | 3 | `0x00B0F5F0` | `0x00B0F5F4` | `0x00B0F600` | — |
  | 4 | `0x00B0F618` | | `0x00B0F628` | — |
  | 5 | `0x00B0F640` | | `0x00B0F650` | — |
  | 6 | `0x00B0F658` | | `0x00B0F668` | — |
  | 7 | `0x00B0F670` | | `0x00B0F680` | — |
  | 8 | `0x00B0F698` | | `0x00B0F6A8` | — |
  | 9 | `0x00B0F6C8` | | `0x00B0F6D8` | — |
  | 10 | `0x00B0F6F0` | | `0x00B0F700` | — |
  | 11 | `0x00B0F708` | | `0x00B0F718` | — |
  | 12 | **`0x00B0F720`** | `0x00B0F724` | `0x00B0F730` | `0x7252ED` |
  - 我亲自复验了 1/2/12 三个：`C7 05 <base> <0x007E91EC>` 全部命中，RTTI 均为
    `.?AV?$DynamicVectorClass@PAVAbstractClass@@@@`；三者的初始化器地址相邻（`0x7252ED / 0x7254ED / 0x7256ED`），
    说明是**同一族的静态初始化器**。

- **§867-3 [已证·对 §859 的定性修正]**
  §859 把 `0xB0F720` 描述为"全部游戏对象的注册表"，并据此讨论"完整性"。
  - ⇒ **它只是 12 个 `AbstractClass*` 数组中的一个**。"唯一主注册表"这个定性**不成立**。
  - ⇒ 与 **§862**（根类构造器不登记）和 **§863→T3 的 `INCOMPLETE` 判定**完全自洽：
    引擎并不维护"一个总表"，而是按用途维护**一族** `AbstractClass` 向量。
  - ⇒ **口径定稿**：**不要再用 `[0xB0F730]` 当"对象总数"**。若要总数，应使用
    `FootClass` + `BuildingClass` + 其它已知叶子类型计数之和，并说明这是估算。
  - ⇒ 反过来，**`UnitClass::Array` / `BuildingClass::Array` / `InfantryClass::Array` /
    `AircraftClass::Array` 这四个"按类型的实例表"仍然是可靠的**——它们是 §859 里被真机历史
    反复使用的口径，且本轮没被任何证据削弱。

- **§867-4 [已证·顺带发现的新数组（部分，说明我漏得多离谱）]**
  除 `AbstractClass*` 外，我完全漏掉的重要数组包括：
  | 类别 | 基址 |
  |---|---|
  | `ObjectClass*`（**3 个**） | `0x0087F778` / `0x00A8E360` / `0x00A8ECB8` |
  | `BulletClass*`（**2 个**） | `0x0089DE18`（`ScalableBullets`）+ 已知的 `0x00A8ED40` |
  | `BombClass*`（2 个） | `0x0087F5D8` / `0x0089C668` |
  | `TechnoClass*`（**4 个**） | 已知 `0x00A8EC78` + `0x0087F5F0` / `0x00889E08` / `0x00AC4C40` |
  | `BuildingClass*`（2 个） | 已知 `0x00A8EB40` + `0x008B41E0` |
  | 类型表（`*TypeClass`） | `BuildingTypeClass 0x00A83C68`、`UnitTypeClass 0x00A83CE0`、`InfantryTypeClass 0x00A8E348`、`AircraftTypeClass 0x00A8B218`、`WeaponTypeClass 0x00887568`、`WarheadTypeClass 0x008874C0`、`BulletTypeClass 0x00A83C80`、`HouseTypeClass 0x00A83C98` 等 |
  | `MixFileClass*`（**4 个**） | `0x00884D90 / 0x00884DA8 / 0x00884DC0 / 0x00884DE0` |
  - ⇒ 尤其注意：**`BuildingTypeClass` 在 `0x00A83C68`**，这正好解释了台账 §397/§（LESSONS）里那条
    "`B_type`(`0x00A83C78`) vs `B_inst`(`0x00A8EB50`) 同标签两对象"的历史事故 ——
    **`0xA83C78` 是"建筑**类型**表"的 Count，`0xA8EB50` 是"建筑**实例**表"的 Count**，两者本来就不是一个东西。

- **§867-5 [未证·如实登记]**
  1. 143 这个数字**可能仍不是全部**：`unresolved_candidates.tsv` 为空，但这只说明"没有留下无法解释的候选"，
     不代表"没有漏掉没有 `C7 05` 存储的向量"（例如通过 `operator new` + 赋值构造的）。
  2. 我只复验了 3 个新基址（`0xB0F5B8`/`0xB0F5D8`/`0xB0F720`），**其余 90 个未逐条复验**。
  3. 这 12 个 `AbstractClass*` 数组各自的**用途**完全未知（哪个存子弹、哪个存待删、哪个存建筑……）。
  4. 数组清单**尚未合并进 `instance_arrays.tsv`**，也**未更新任何下游统计**。

- **§867-6 [已证·产物]** `lead\\next_re_20261112_r10\\W135_ds\\T1_all_vector_globals\\`
  | 文件 | 内容 |
  |---|---|
  | **`vector_globals.tsv`** | 142 行 × 11 列（element/base/items/count/vftable/col/td/mangled/has_dynamic_store/has_base_store/n_stores） |
  | `unresolved_candidates.tsv` | 空（表头只有） |
  | `t1_enumerate.py` | 枚举器 |
"""

P = LED
s = io.open(P, encoding="utf-8", newline="").read()
if "## §867 ·" in s:
    raise SystemExit("REFUSE: §867 already present")
s = s.rstrip("\n") + "\n" + SEC
io.open(P, "w", encoding="utf-8", newline="\n").write(s)
bad = [(i, hex(ord(c))) for i, c in enumerate(s) if ord(c) < 32 and c not in "\n\t"]
print("appended §867; size=%d; control chars=%d" % (len(s.encode("utf-8")), len(bad)))
