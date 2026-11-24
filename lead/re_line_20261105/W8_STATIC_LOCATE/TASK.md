# W8 任务书 · 三个「未定位」字段的静态定位（F6 视口坐标 / F7 索敌限频 / F8 可见对象数）

> **为什么是这一题**：D-17 静态补证第一层（`D17_STATIC_FIELDS.md`）只能定 F1–F5，
> **F6 真实视口坐标 / F7 索敌执行计数 / F8 可见对象数 全部「未定位」**。
> D-20 判 B 后已证「可见单位数不存在现成计数 VA」（`D20_B_VISIBILITY_GAP.md`）。
> W3 收官把 5.7 倍帧时差收敛到 C1 寻路 / C2 渲染裁剪 / C3 微观索敌 / C4 战斗物理，
> **其中 C2/C3 都要靠 F6/F7/F8 才能定谳**。
> ⇒ 这三项是目标① 当前**唯一还能纯静态推进**的硬骨头。
>
> **本任务纯静态：零真机、零采样代码、零活进程读取。** 只允许 `ra2tool.Engine` 反汇编 + 磁盘文件读。

## 0. 目标镜像（必须先自证）

| 项 | 值 |
|---|---|
| 路径 | `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe` |
| SHA256 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` |
| 字节数 | `4,825,360` |
| ImageBase | `0x400000` |

读法：`sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104')` → `from ra2tool import Engine`。
可用的 Engine 方法（我已实测）：`sha` / `IB` / `coverage` / `raw(va,n)` / `disasm(va,n)` / `stream` /
`disp_hits(va)` / `disp_hits_field(off)` / `func_rets(va)` / `loop_backedges(a,b)` / `reach_without(...)` / `rd(va)` / `u32(va)` / `fo(va)`。

## 1. 先读（按序，只读不改）

1. `lead/re_line_20261105/D17_STATIC_FIELDS.md` —— F1–F8 现状表，F6/F7/F8 标「未定位」
2. `lead/re_line_20261105/D20_B_VISIBILITY_GAP.md` —— 「可见单位数」为何不是现成 VA（**F8 必须接住这份**）
3. `lead/re_line_20261105/W3_COSTBOUND/sections/Q1_C2_RENDER.md` —— C2 渲染裁剪的静态边界
4. `lead/re_line_20261105/W3_COSTBOUND/sections/Q1_C3C4_PHYS_TARGET.md` —— C3/C4，含「`0x6FB010` 是 UpdateReload 不是索敌」的结论
5. `lead/re_line_20261105/W4_FIELD_SPEC/sections/card_00A8EC34.md` —— 已知的「索敌入口累计」是**另一个**字段，别和 F7 混

## 2. 三项任务（各自独立出回件，互不代判）

### F6 · 真实视口坐标 / 当前可见世界矩形

已知线索（**不是我给的结论，是待验线索**）：
- `0x00432A35` 读 `[0x887308]` → `0x00432A3A mov eax,[eax+0x1C]`。
- `0x432A29..0x432A32` 在写 **8 个 dword 的矩形结构**到 `esi+0x10`。
- ★ 已定谳：**`0x887308/0x88730C` 是 `DSurface` 指针槽**（vtable `0x007E85D4`、RTTI `.?AVDSurface@@`），**不是视口坐标**（台账 §563）。

必须回答：
1. `0x432A35` 所在函数的**完整边界**（起止 VA）与它在绘制链里的位置；
2. 它读到的 `DSurface+0x1C` 到底是**什么类型的值**（指针？矩形？尺寸？）—— 给字节依据；
3. **当前可见世界矩形**由谁计算、写到哪里（给 VA + 偏移 + 类型 + 生命周期）；
4. 若确实找不到「世界坐标矩形」，就明确写 **`未定位`** 并给出「已排除的路径清单」（查了哪些、排除了什么）。
   **不要把「查不到」当成「不存在」**（A3 曾两次犯此错）。

### F7 · 索敌执行计数 / 限频计时器

必须回答：
1. `0x6FB010` 已被判为 `UpdateReload`（`Ammo==-1` 时 `0x6FB025 je` 直接返回）—— **请独立复核这条**，别照抄；
2. **真正的索敌入口在哪**：`0x6F8DF0`（Greatest_Threat）的**全部直接调用者**（`Engine.stream` 扫 E8 rel32），逐个给 VA；
3. 这些调用者里，是否存在**帧限频**（如 `% 8`、`& 7`、计数器比较）—— 给字节；若某处是 `(frame & 7)` 之类的节奏门，把计数器的 VA/偏移写出来；
4. 「索敌执行计数」是否存在**现成的全局累加器**（`inc [全局]`）—— 有则给 VA，没有则写 `未定位` + 排除清单。
   ★ `docs/re/targeting_spatial.md` 把 `0x6FB010` 当索敌入口是**误标**，该判断已在台账 §566 记载，请独立复核后说明。

### F8 · 可见对象数 / 裁剪通过数

前置：`D20_B_VISIBILITY_GAP.md` 已证 ——
`call 0x5F4B10` 全镜像仅 3 处（全是透传包装）；`0x6D8DB0..0x6DA1FB` 内零处调用、零处写全局 dword；
`call 0x6D2140`(IsVisible) 139 处均只 `test al,al` 不计数。

必须回答：
1. **独立复核**上面三条数字（自己扫，不照抄）；
2. `DrawIfVisible 0x5F4B10` 的**全部直接调用者**与它们各自所在函数 —— 有没有任何一个在循环里累加计数；
3. 若结论仍是「无现成计数 VA」，请给出 **最小可行推导规格**（要读哪些字段、按什么顺序、代价多少条指令、误差来源），
   但**不写实现代码**（本任务只要规格）；
4. 明确写 `未定位` 或给 VA，二选一，不许模糊。

## 3. 每份回件强制头部（缺则整份作废）

```
被核对象 = gamemd.exe（+ 本节引用的前置文件）
gamemd.exe SHA256 = <自己实算的 64 位>，字节数 = <自己实算的>
Engine 自证 = COVERAGE <coverage> / IMAGEBASE 0x400000
回件时刻 = <实际时刻>
```

## 4. 判定档（每项三选一，不许模糊）

- **LOCATED**：给出 VA（或 基址+偏移）+ 类型 + 生命周期 + 访问证据（`文件:行` 或 `反汇编地址 + 原始字节`）+ 计数/读取口径。
- **UNLOCATED**：明确写未定位 + **已排除路径清单**（查了什么、为什么排除）。
- **INFEASIBLE**：证明「外部静态无法复现该判定」，并给出论证（不是「我没找到」）。

## 5. 交付物

写到 `lead/re_line_20261105/W8_STATIC_LOCATE/`：
- `F6_VIEWPORT.md` / `F7_TARGETING.md` / `F8_VISIBILITY.md` —— 三份正文
- `reviews/F6_review.md` / `F7_review.md` / `F8_review.md` —— 三份独立复核
- `W8_STATIC_LOCATE.md` —— 汇总（七节：`## 0 总判` / `## 1 SHA256 绑定` / `## 2 F6` / `## 3 F7` / `## 4 F8` / `## 5 对 D-17 的增量` / `## 6 必须改项` / `## 7 诚实账`）
- `_w8_*.py` + `_w8_*_out.txt` —— 只读探针

## 6. 铁律（违反即作废）

- **零真机**：不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，**不读活进程内存**。
- **零采样代码**：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入。
- **只读**：`ra2youli\`、`out\re_work\...`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md`、
  `W1_*`…`W7_*` 既有件、`D*_RULING\`、`A1_*`、`A2_*`、`A3_*`、`_leader\*` —— **一律不得修改**。
  **唯一写域 = `W8_STATIC_LOCATE/`**。
- Python 一律 `python -I -X utf8`，绝对路径。
- **不 commit、不 push**。
- 每个数字追到「实跑命令 + 输出」或「文件:行」；**拿不到就写「未验」，不许补造**。
- ★ **不要把「查不到」当成「不存在」**。
- ★ **并行度**：本任务最多同时 2 个子代理（用户 2026-11-06 令：并行开太多会卡顿）。
