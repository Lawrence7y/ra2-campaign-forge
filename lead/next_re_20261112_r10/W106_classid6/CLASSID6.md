# W106 · `WhatAmI()==6` 类归属主报告

**问题**：`0x47C520` 在 `cell+0xE4` 对象链上找的 `WhatAmI()==6` 是哪一类？
**答案**：**类 6 = `BuildingClass`（建筑实例类）**。
**依据等级**：`[已证]`（二进制内 MSVC RTTI 完整对象定位器链 + 构造/析构函数簇双重独立印证；并有"类 15 = InfantryClass"同法对照组）。

---

## 结论一览

| 项 | 值 | 等级 |
|---|---|---|
| `WhatAmI()==6` 的类 | **`BuildingClass`** | `[已证]` |
| 主虚表 | `0x007E3EBC`（与 R09 L2 锚点一致） | `[已证]` |
| 虚表 COL（`vt[-1]`） | `0x007FC360` | `[已证]` |
| COL 指向 TypeDescriptor | `0x00818D60`，名字串在 `+8` = `".?AVBuildingClass@@"` | `[已证]` |
| 继承层级（CHD 0x007FC350） | 15 个基类：BuildingClass→TechnoClass→RadioClass→MissionClass→ObjectClass→AbstractClass→IPersist/IPersistStream/IUnknown/IRTTITypeInfo/…/INoticeSink/INoticeSource/FlasherClass/StageClass | `[已证]`（TD 逐一解出名） |
| 构造函数 | `FUN_0043b740`（0x0043B740，1456 B） | `[已证]` |
| 析构函数 | `FUN_0043bcf0`（0x0043BCF0，__fastcall，986 B） | `[已证]` |
| 辅助构造 | `FUN_0043b680`（192 B） | `[已证]`（归属同簇，`[静态推断]` 为拷贝/变体构造） |
| 对象尺寸 | ≈ `0x720`（1824 B） | `[静态推断]` |
| 对照组 | 虚表 `0x7EB058` 的 `vt[-1]=0x8033B8` → TD `0x825508` = `".?AVInfantryClass@@"` ⇒ **类 15 = InfantryClass** | `[已证]` |

---

## 证据链 A（定谳）：MSVC RTTI COL → TD → 类名 `[已证]`

镜像里**存在** MSVC C++ RTTI 结构（详见 DISAGREE.md）。主虚表的 `[-1]` 槽是 Complete Object Locator：

```
0x7E3EB8:  007FC360        ← vt[-1]（COL 指针）          产出：EVIDENCE\col_tda_proof.txt
COL@0x7FC360 = {sig=0, off=0, cd=0, TD=0x00818D60, CHD=0x007FC350}
TD@0x00818D60：+8 处名字串 = ".?AVBuildingClass@@"       （MSVC mangling：class BuildingClass）
```

- `CHD@0x7FC350 = {sig=0, attr=1, nbases=15, BCA=0x7FC310}`，15 个基类 TD 逐一解名（BuildingClass/TechnoClass/RadioClass/MissionClass/ObjectClass/AbstractClass/IPersist*/IUnknown/IRTTITypeInfo/INoticeSink/INoticeSource/FlasherClass/StageClass），链条自洽（每一环 `BCD[0]→TD` 都解出合法 `.?AV/.?AU` 名）→ 不可能是巧合命中。
- **同一方法对照组**：`0x7EB058[-1]=0x8033B8 → TD 0x825508 = ".?AVInfantryClass@@"`。R09 L2 的"15 = Infantry 候选"由此独立证实，方法有效性有正控。
- 产出命令：`python -I _w106_bytescan.py`、`python -I（COL 解链脚本）`，原始输出 `EVIDENCE\bytescan_out.txt`、`EVIDENCE\rtti_names.txt`、`EVIDENCE\col_tda_proof.txt`。

## 证据链 B：构造/析构函数簇（写 vptr 的唯一 3 处）`[已证]`

全镜像引用主 vptr `0x7E3EBC` 的代码点 = **恰好 3 处**（Ghidra `getReferencesTo`，`EVIDENCE\ghidra_classid6.txt`）：

| 写点 | 含函数 | 语义 |
|---|---|---|
| `0x0043B721` | `FUN_0043b680`（192 B） | 辅助构造：写字段后 `*this=0x7E3EBC; this[1]=0x7E3EA0; this[2]=0x7E3E98; this[3]=0x7E3E90` |
| `0x0043B9FA` | `FUN_0043b740`（1456 B） | **主构造**：写 ~0x71C 字节字段 + 注册进 3 个全局对象向量（`DAT_00a8eb44/00b0f644/00b0f5bc`）+ 以 `{type指针, this}` 注册进全局映射 `DAT_00b0e840` |
| `0x0043BCFD` | `FUN_0043bcf0`（986 B，`__fastcall`） | **析构**：反向摘除出上述列表、释放成员、末尾调基类链 `FUN_006f4500()`；其唯一调用者 = `FUN_00459f20` = 主虚表槽 14（标量删除析构） |

要点：
1. 四重 vptr（`+0/+4/+8/+12`）= 多重继承，与 CHD 里 FlasherClass/StageClass/COM 接口基类吻合（次级子对象虚表 `0x7E3EA0/0x7E3E98/0x7E3E90` 各带自己的定位器 `0x7FC2E0/0x7FC2C8/0x7FC2B0`，`EVIDENCE\whatami_ladder.txt` 原始转储）。
2. 构造函数把 `param_2` 存到 `this+0x148`，随后按 `*(this[0x148]+0x1710)`、`*(this[0x148]+0x1780)` 读类型字段——`+0x148` 处是 **TypeClass 对象**（偏移 0x1710/0x1780 属大号 Type 类 ⇒ 与 BuildingTypeClass 形态一致，`[静态推断]`）。
3. 构造的 13 个调用者中 `FUN_0044f820/0045e880/005a6510/005a82e0/005a91e0/005a95b0/00595400/005904b0`（放置/生产路径簇）与 `FUN_007393c0`（0x73xxxx 存档重载簇）各就各位，符合"建筑由放置与存档重建产生"的语义。`[静态推断]`（函数语义未逐个反编译）

## 证据链 C：对象尺寸指纹 `0x720` `[静态推断]`

- 主构造最末字段写：`param_1[0x1c6] = 0`（dword，覆盖字节 0x718..0x71B）⇒ 对象 ≥ `0x71C`（`EVIDENCE\ghidra_classid6.txt` 反编译）。
- 主虚表槽 12（`0x7E3EEC`）= `0x00459E70: mov eax,1824(0x720); ret`（`EVIDENCE\whatami_ladder.txt`）——若为 Size() 类虚函数则 `sizeof==0x720`。
- 两条独立数字相容（0x71C ≤ 0x720，4 字节对齐余量 4）；删出器 `0x459F20` 无 `push 0x720`（VC6 `operator delete(void*)` 无尺寸），故尺寸保持 `[静态推断]`。
- 对比：`CellClass=0x148`（R10_FACTS §3）；建筑实例 ≈ 0x720 与"建筑是挂在格上的大对象"一致。

## 证据链 D：与崩溃族的语义落点 `[已证]`（事实）/`[静态推断]`（判读）

- `0x0047C520`：守卫 `0x00A8E9A0` → 沿 `cell+0xE4` 链（next=+0x30）找 `WhatAmI()==6` 的第一个对象（R09 L1-2，`[已证]`）。
- ⇒ **这条链上"本来应该有的"是 BuildingClass 实例**；134 个调用者（R09 L4）在问"这个格子上有没有建筑"。
- `[静态推断]`：S1/S2 崩溃 = 链上某个节点已失效（悬垂/被填零），`call [vptr+0x2C]` 读到坏 vptr——坏的是**对象本身或其 vptr 字段**，而不是"6 这个类 ID 不对"。归因仍须走 W99/W100 的状态侧路线（R09 L4-1 结论不变）。

---

## 方法与复现命令

1. 自建 Ghidra 工程（工程锁纪律）：`analyzeHeadless.bat <card>\_ghidra ghidra_<host> -import ra2youli\gamemd.exe`（245 s，8,948 函数）。
2. 字节扫描：`python -I _w106_bytescan.py > EVIDENCE\bytescan_out.txt`（全文 `BC 3E 7E 00`…`D8 3E 7E 00` 命中分类 + vtable 6/15 槽位对照）。
3. RTTI 解链：`EVIDENCE\rtti_names.txt`（.data 0x818C00..0x818F00 的 `.?AV` 名单）、`EVIDENCE\col_tda_proof.txt`（COL/CHD/BCA 全解）。
4. Ghidra 脚本：`analyzeHeadless.bat ... -process gamemd.exe -noanalysis -scriptPath ghidra_scripts -postScript ClassId6.java` → `EVIDENCE\ghidra_classid6.txt`（含 FUN_0043b680/0043b740/0043bcf0 全反编译 + 引用普查）。

## 与已知事实的关系

- R09 L2 锚点 `0x7E3EBC 槽11=0x459EC0=mov eax,6`、`0x7EB058 槽11=0x523340=mov eax,15`：**复核一致**（`EVIDENCE\bytescan_out.txt` 头部直接读文件字节）。
- R09 L2-3 "`[未证]` 类 ID 6 是哪一类"：**本卡闭合**；且给出可复用的"COL→TD→名字"反查法（比虚表游程普查强：不受相邻 vtable 合并游程影响，可对任意 vptr 定名）。
- 类 ID 阶梯（抽样）：6=BuildingClass、15=InfantryClass —— 非 0..7 线性，与 R09 提示一致。
