# W134 — 真机核对：一条命令验证 §859 的数组表

**状态**：探针已就绪并自检通过（15/15）；**尚未运行**。本文件是操作说明 + 判读表。

---

## 1. 这一步要回答什么

§859 用二进制自带的 RTTI 证明了 49 个实例数组的**身份**（哪个全局是哪个类别的清单）。
但**数值**（某局里 `[0x8B4118]` 是否等于图上实际载具数）从未与真机核对过。
另外 §859-7-1 明确登记了一个未证项：

> `AbstractClass::Array`（`0xB0F720`，Count `0xB0F730`）是否是**完整**的全局对象注册表。

这一步一次跑完就能判定，而且**不需要改任何代码、不注入、不写内存**——纯 `PROCESS_VM_READ`。

## 2. 前置条件

游戏必须**已进入一局遭遇战**（主菜单下所有数组都是空的，读数没有意义）。
进局只能走 GUI（`gamemd.exe` 只有 `-MPDEBUG` / `-DESTNET` / `-CD` 三个命令行开关，
**没有**加载地图或存档的开关，这一点本轮已用字符串扫描确认）。

进局后，`[0x00A80228]`（`HouseClass::Array.Count`）会从 0 变成正数，
这就是探针 `--wait` 用的判定信号。

## 3. 怎么跑

```powershell
# 1) 找到进程号
Get-Process gamemd | Select-Object Id

# 2) 先只看数组头（快，不遍历元素）
python -X utf8 lead\next_re_20261112_r10\W134_live\w134_live_arrays.py --pid <PID> --wait 180

# 3) 完整版：遍历每个数组的每个元素，把元素的 vptr 反查成类名
python -X utf8 lead\next_re_20261112_r10\W134_live\w134_live_arrays.py --pid <PID> --wait 180 --walk --out w134_live.txt
```

`--wait 180` 最多等 3 分钟直到 `HouseClass::Array` 非空；超时会打 WARNING 但继续读
（这时读到的多半是空数组，说明还没进局）。

自检（不需要游戏）：

```powershell
python -X utf8 lead\next_re_20261112_r10\W134_live\w134_live_arrays.py --selftest
```

## 4. 判读表

### 4.1 W134-1 数组形状

每个数组应满足（全部来自 `0x004E6B60` 静态构造器）：

| 检查 | 期望 |
|---|---|
| `CapacityIncrement` | **恒为 10** |
| `Count` | `0 ≤ Count ≤ Capacity` |
| `Items` | `Count > 0` 时非 0 |
| `IsInitialized` | 1 |

**判读**：
- 若 `CapacityIncrement` 不是 10 ⇒ **§859-2 的布局结论错了**，整张表都要重审。
- 若出现 `Count > Capacity` ⇒ 该数组正被并发修改（读数撕裂），重跑；持续出现则布局错。
- 若某些数组 `Count==0 ∧ Items==0` ⇒ 正常（该局没有这类对象），不是错误。

### 4.2 W134-2 计数一览

一次拿到全部关键计数。**这是项目一直缺的"真实 N"**。

### 4.3 W134-3 元素类名（需要 `--walk`）

对 `DynamicVectorClass<BuildingClass*>` 这类数组，每个元素的 vptr 应反查成
**声明的类或它的派生类**。

**这是身份结论的独立验证**：如果 `0x8B4108` 真是 `UnitClass::Array`，
里面的元素就应该是 `UnitClass`（或派生）；如果里面有 `InfantryClass`，那我的结论就错了。

**判读**：
- 元素类全部落在声明类或其派生 ⇒ **§859 身份成立**。
- 出现明显不相干的类（例如在 `BuildingClass::Array` 里读到 `BulletClass`）⇒ **§859 错了**，立即回报。
- vptr 反查不到（`unresolved`）⇒ 该元素是引擎里没有 RTTI 的类型，或指针已失效；不算反证。

### 4.4 W134-4 `AbstractClass::Array` 完整性

这是唯一一项**纯静态无法判定**的。

**关键**：不要拿 `AbstractClass.Count` 跟"各类型计数之和"直接比——
一个对象同时出现在多个数组里（一个 `UnitClass` 同时在 `UnitClass::Array`、
`FootClass::Array`、`TechnoClass::Array`、`AbstractClass::Array` 里），直接求和会重复计数。

正确的比法是**逐桶比**：

| `AbstractClass::Array` 里某类的桶 | 应等于 |
|---|---|
| `BuildingClass` 桶的大小 | `[0x00A8EB50]` |
| `UnitClass` 桶的大小 | `[0x008B4118]` |
| `InfantryClass` 桶的大小 | `[0x00A83DF8]` |
| `AircraftClass` 桶的大小 | `[0x00A8E3A0]` |

**判读**：
- 四个桶全部与对应计数相等 ⇒ `AbstractClass::Array` **是**完整注册表，`0xB0F730` 可作"对象总数"。
- 某类桶 < 对应计数 ⇒ 该类**有对象没登记**，注册表**不完整**；把差值和类名记下来。
- 某类桶 > 对应计数 ⇒ 计数或身份有一处错了，先怀疑我的表。

## 5. 安全声明

- 只开 `PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION`，**不开写权限**。
- 不注入、不建远程线程、不改内存、不改文件。
- 只读，所以最坏情况是探针自己报错退出，游戏不受影响。
- 逐元素遍历有上限（`walk_elements` 内 `cap=200000`），不会因为 `Count` 被读成垃圾值而爆炸。

## 6. 已知限制

1. **需要人先进局**。GUI 自动化在仓库里有（`goal1_harness8_20261031\qc151_trip.harness8_v4.py`
   的 `wait_screen` / `_red_button_centers` / `_burst_battle`），但那是 8,800 行的 QС 门禁脚本，
   复用成本高；本轮没有驱动它。
2. 元素 vptr 反查依赖 `vtables_canonical.json`（1,214 条）。没有 RTTI 的对象会显示 `unresolved`。
3. 一次读数只是一个时刻的快照。要下"某数组会泄漏/不会泄漏"这类结论，需要**跨时刻多次采样**
   （例如建一栋建筑前后各读一次）。
