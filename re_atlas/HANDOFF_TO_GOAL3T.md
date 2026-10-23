# 交接件 · RE-ATLAS → GOAL-3T

> 只投递，不催促，不替 GOAL-3T 做决定。是否采纳由 GOAL-3T 自行判断。
> 每条含：日期 / 发现 / 证据 / 可能影响哪个目标 / 置信度。
> 本线不改 `lead/`、`docs/re/`、`ra2render/`、`tools/` 下任何文件。

---

## H-001 · 2026-10-21 · `TeamTypeClass` / `AITriggerTypeClass` 实例尺寸与 ATLAS 冲突

**发现**：ATLAS §11.2 的这两行实例尺寸与其自带的"取证指令"都不成立。
字节复算得 `TeamTypeClass` = **248 (`0xF8`)**、`AITriggerTypeClass` = **272 (`0x110`)**；
ATLAS 分别记 288 (`0x120`) 与 256 (`0x100`)。

**证据**
| 类 | `vtable[12]` | 字节 | 解出尺寸 |
|:---|:---|:---|:---|
| `TeamTypeClass` | `0x006F20B0` | `B8 F8 00 00 00 C3` | 248 |
| `AITriggerTypeClass` | `0x0041FFE0` | `B8 10 01 00 00 C3` | 272 |

ATLAS 对 `TeamTypeClass` 给的取证 VA `0x6F29C0` 实测是
`1C 24 E8 19 84 DD FF DD 1D 68 EA B0 00 83 C4 08 C3`（浮点函数中部），
不含 `mov eax,0x120`，也不在 27 个虚表槽里。
ATLAS 对 `AITriggerTypeClass` 给的 `0x420990` 实测是
`C7 46 0C 78 32 7E 00` = `mov [esi+0xC],0x7E3278`（vtable 字面量写）。

复跑：`python re_atlas/tools/xcheck_sizes.py`（`evidence/size_xcheck.txt`）。

**可能影响的目标**
- ① 卡顿 / ② 主崩溃 / ③ 安全改动能力：**当前均无直接影响**。
  本线核对 `ra2render/` 源码，无任何位置引用这两个类或这两个尺寸。
- 但若 GOAL-3T 后续要动 AI 小队/AI 触发器路径（例如为定位崩溃而推算
  `TeamClass`/`AITriggerTypeClass` 数组步长），错误的尺寸会导致越界读。
  尤其 `AITriggerTypeClass::Array`（`0x00A8B200`）的**下标步长**若按 256 算，
  每项会少走 16 字节。

**建议动作**（不做也行）：若 GOAL-3T 的 ATLAS 副本参与任何门禁或断言，
留意 `0x120`/`0x100` 这两个字面量是否被引用。

**置信度**：**字节实证**。
`AITriggerTypeClass` 另有语料内既有的 `E-AIT-1`（`docs/re/trigger_tag_abi_deep_dive.md:21,191,211`）
独立佐证同一数值；`TeamTypeClass` 为本线首报，语料内无第二来源。

**核验状态**：✅ **已核验（异族双通道，2026-10-21 20:2x）**。
`dwfrun-7cee3752`：GLM 5.3 与 DeepSeek v4.1-flash 各自独立复算，两路均 `CONFIRMED`，
均得出 248 / 272。GLM 附注"按段表 VA 换算，两 GetSize 均为 `B8 imm32+C3`"；
DeepSeek 附注"两处 GetSize 均为 NOP 填充后的函数头"。
（前两轮 `dwfrun-4cc83e74` / `dwfrun-c318607d` 因限流零落盘；第三轮改用纯文本四行协议，
因为两模型都不会主动调 typed `ask` 要求的 `submit_result`。）

---

## H-002 · 2026-10-21 · `vtable[12] == GetSize` 不是普适前提

**发现**：ATLAS §11.2 的尺寸推导前提是"`vtable[12]` 就是 `AbstractClass::GetSize`"。
实测至少两个类在该槽放的是**访问器**，不是尺寸函数：

| 类 | `vtable[12]` 体首 | 实际语义 |
|:---|:---|:---|
| `RadarClass` | `mov eax,[ecx]` | 返回对象首字段（多为 vptr） |
| `WWMouseClass` | `mov eax,[ecx+0x20]` | 返回某成员 |

**证据**：`evidence/size_xcheck.txt` 的 `NO-IMM` 分支；`tools/disas.py <VA>` 可逐条复核。

**可能影响的目标**
- ③ 安全改动能力：若将来用"类尺寸"做缓冲区边界校验或 hook 前的栈帧检查，
  **照 ATLAS §11.2 直接取数会在 `RadarClass`/`WWMouseClass` 上拿到垃圾值**
  （`RadarClass` 记 4864，实际槽返回的是指针）。
  这类错误在校验器里表现为"偶发、与具体类相关"，很难归因。
- ①② 无直接影响。

**置信度**：**实证**（字节 + 槽位比对）。

**建议动作**：凡引用 §11.2 尺寸前，先验 `vtable[12]` 体首是否 `mov eax,imm`。
本线已把它写成门禁，可复用：

```python
# 返回 (尺寸, 取证指令)；体首不是 mov eax,imm 时 size=None
from re_atlas.tools.xcheck_sizes import size_from_getsize  # 见该文件
```

**核验状态**：✅ 字节直证，无需异族（属"读一个立即数"级别的机械事实）。

---

## H-003 · 2026-10-21 · 二进制快照身份：生产件 vs `.ra2opt/orig` 仅差 PE CheckSum

**发现**：`ra2youli/gamemd.exe` 与 `ra2youli/.ra2opt/orig/gamemd.exe` **只差 2 字节**，
都在可选头 `CheckSum` 字段（`0xB0..0xB3`）：
live = `00 00 40 00` ⇒ `0x00400000`（4,194,304）；
orig = `00 00 10 00` ⇒ `0x00100000`（1,048,576）。
`TimeDateStamp`（`0xA8..0xAB`）两份都是 `00 00 00 00`，**未改**。
`.text` 逐字节相同。

**证据**：`re_atlas/evidence/binary_identity.txt`（逐字节 diff + 三份哈希）。

**可能影响的目标**
- ③ 安全改动能力：**按 sha256 做"母本未改动"门禁时会误判**。
  两份代码段完全相同却哈希不同，若门禁只比 sha256 而不比 `.text` 段哈希，
  会把"`ra2opt` 重算过校验和"误报成"母本被改"。
- ① ② 无直接影响（但测量若跨件混用会破坏可比性）。

**置信度**：**实证**（逐字节 diff）。

**建议动作**：母本门禁建议以 **`.text` 段 sha256**（本件 `c0368a17…`）为主键，
或以"生产件哈希 + orig 哈希"双白名单。现有记录里 `ra2opt` 那侧已写明
"LAA 在 COFF Characteristics 非 DllChar"，校验和差异应是其副产物。

**核验状态**：✅ 字节直证。

---

## H-004 · 2026-10-21 · 方法提示：线性 capstone 扫描在本件覆盖 11.1%

**发现**：对本件 `.text` 做一次线性 `disasm`，只解出 155,215 条指令，
止于 `0x0046F5A0`（段尾 `0x007E1000`），覆盖 **11.1%**。原因是在段内嵌数据处失步。
改用递归遍历（入口 + rel32 + 虚表槽为根）可解出 1,447,234 条、发现 15,224 个函数入口。

**证据**：`evidence/fn_census.txt`（线性，11.1%）vs `evidence/fn_walk.txt`（递归，完整）。

**可能影响的目标**
- ①②③：任何"全 .text 扫描 X 命中/0 命中"的断言，若基于线性 capstone，
  **只看了 11%**，结论不可信。项目已有"grep 0 命中须带样本"的机检规则
  （EVIDENCE_STANDARD 追加三条），但该规则只覆盖 grep，不覆盖 capstone 扫描。
- 本线对 GOAL-3T 已知有若干"全镜像仅 N 处"的结论（例如 ATLAS §16 的
  `call 0x0041FD60` 全镜像仅 `0x006E8E2A`）。**这些看起来是字节级 E8 扫描**
  （用 `tools/xref_abs.py` 一类），那是对的；但若某处用了 disasm 迭代，需复查。

**置信度**：**实证**（两个脚本的输出都在 `out/`）。

**建议动作**：涉及"全段扫描"的断言，建议在证据里注明是
"字节扫描"还是"反汇编迭代"。前者可信，后者需先验覆盖率。

**核验状态**：✅ 自证（两次不同方法的输出对比）。

---

## H-005 · 2026-10-21 · `AbstractClass` 是多继承（4 个 vptr），且 `GetSize` 返回 0 是抽象桩

**发现**
1. `AbstractClass`（所有游戏对象的根类）在 `+0x00/+0x04/+0x08/+0x0C` 有**四个 vtable 指针**，
   对应主类 + 三个接口子对象，`CompleteObjectLocator.offset` 依次为 **0 / 4 / 8 / 12**。
   这是多继承布局，不是单继承。
2. `AbstractClass::GetSize`（`vtable[12]`，`0x004C9150`）字节是 `33 C0 C3`
   = `xor eax,eax; ret`，即**返回 0 的抽象桩**。`AbstractTypeClass` 同槽同址同体。

**证据**
- 删除析构 `0x004105A0` 连写四次 vptr：
  `mov [esi],0x7E1F50` / `[esi+4],0x7E1F34` / `[esi+8],0x7E1F2C` / `[esi+0xC],0x7E1F24`
- 每个 `vtable-4` 的 COL.offset 实测 0/4/8/12
- 接口槽是 `sub [esp+4],4; jmp <主类实现>` 的 this 调整跳板
- 复跑：`python re_atlas/tools/dump_class_layouts.py`

**可能影响的目标**
- ③ 安全改动能力：**最相关**。若任何 hook 或校验逻辑假设
  "对象首 dword 是唯一 vptr"或"用基类 GetSize 算尺寸"，会在本族上出错：
  - 写 hook 时若只保存/恢复 `[obj]`，会漏掉 `+4/+8/+0xC` 三个接口 vptr；
  - 若用 `AbstractClass::GetSize()` 做缓冲区大小，会拿到 **0**，进而把
    "分配 0 字节"或"零长度拷贝"当作合法，实际对象有 48~564 字节。
- ② 主崩溃：中相关。任何"按 vptr 判断对象类型"的代码只认 `[obj]`，
  遇到接口 this 指针（`obj+4`）会把同一对象判成不同类。
- ① 卡顿：无直接影响。

**置信度**：**实证**（析构反汇编 + COL 偏移 + 跳板三重证据，机器可复跑）。

**核验状态**：✅ 字节直证（多继承结构属"读常量"级机械事实，不需异族）。

---

## H-006 · 2026-10-21 · `TaskForceClass` 成员数组 = 8 字节 `{id,value}` 对

**发现**：`TaskForceClass`（212 字节）的成员容器布局已完全确定：

| 项 | 值 |
|:---|:---|
| 计数 | `obj + 0x9C`（u32），同时用作下一个写入下标 |
| 数组基址 | `obj + 0xA4` |
| **元素 stride** | **8 字节** |
| 元素结构 | `{ dword @+0, dword @+4 }` |

`+0xA8` **不是独立字段**，它是 `array[i]` 的第二半（地址 `0xA4 + 8i + 4`）。

**证据**（`0x006E8496..0x006E84B5`）：

```
mov  ecx, [esi+0x9C]                 ; 下标 = 当前计数
mov  edx, [eax]                      ; 解析结果第 1 个 dword
mov  [esi + ecx*8 + 0xA4], edx       ; ★ stride = ecx*8
mov  eax, [eax+4]                    ; 第 2 个 dword
mov  [esi + ecx*8 + 0xA8], eax       ; ★ 同一元素的 +4
mov  eax, [esi+0x9C]
mov  ecx, [esi + eax*8 + 0xA8]       ; 读回
```

配合 §H-006 早前观察到的循环（`lea ebx,[edi+0xA4]` + `cmp esi,[edi+0x9C]`），
读写两侧一致。

**可能影响的目标**
- ③ 安全改动能力：若做"遍历/裁剪 TaskForce 成员"的补丁，确切公式为
  `count = *(u32*)(tf+0x9C)`、`item(i) = tf + 0xA4 + 8*i`。
  按 4 字节步长遍历会读到错位数据；按标准 `DynamicVectorClass`
  （`+4=Items, +0x10=Count`）更会完全错位。
- ①② 无直接影响。

**置信度**：**实证**（写路径 + 读回 + aid helper `0x4C4EF0` 三重）。

**核验状态**：✅ 字节直证。

**⚠ 不要套用到 `ScriptTypeClass`**：后者计数在 `+0xA0`，解析走 `+0x24` 子对象，
`+0xA4` 在其方法里根本没出现。本线曾因"两类同一偏移"误推统一模型并已撤回。

---

## H-007 · 2026-10-21 · `0xB0C110` 是 `SwizzleManagerClass::Instance`：登记过的指针字段会被**清零**

**发现**：`0xB0C110` 在 `.text` 里有 **489** 处字面量引用，
其中 **485 处是真的 swizzle 调用**（473 → `0x6CF240`、5 → `0x6CF2C0`、
4 → `0x6CF230`、1 → `0x6CF430`、2 处有 1–2 条指令插队但最终同样到 `0x6CF240`），
另有 4 处是假命中（3 处在静态初始化器自身编码里，1 处是索引计算）。
本线前轮把它误判为"字段注册表根"。**实测它是一个对象**：

- 静态初始化器 `0x006CF0C8: C7 05 10 C1 B0 00 08 41 7F 00` 直接写入虚表 `0x7F4108`；
- `0x7F4108` 经 RTTI 反查 = **`SwizzleManagerClass`**（基类 `ISwizzle`/`IUnknown`）；
- `0x6CF240` 是该虚表的**槽 4**（YRpp 命名为 `Here_I_Am`）。

**关键行为**（这条才是要投递的）：

```text
0x006CF2A8  mov dword ptr [edi], 0    ; ★ 登记之后把原字段清零
```

`0x6CF240` 把 `{原指针值, 字段地址}` 追加进 swizzle 表，**然后 `*ppField = 0`**。
之后该字段读出来是 **0**，真实值只能通过 swizzle 表查回。
`Save` 里就是靠这个机制做存档指针重定位。

**可能影响的目标**
- **③ 安全改动能力（直接相关）**：若任何补丁/守卫把"可能被 swizzle 登记过"的字段
  当指针读，读到 0 会走进空指针分支，或把 0 当成合法句柄。
  典型受害者是各类 `Save`/`Load` 周边字段。写这类补丁前先确认该字段是否被
  `0x6CF240` 登记过（判据：`lea reg,[obj+off]` 后紧跟 `push reg; push 0xB0C110`）。
- ② 主崩溃：**间接**。若崩溃点在 `Save`/`Load` 路径、且崩在 `mov [reg], …` 而
  `reg` 源自被清零字段，这条可以解释"为什么指针是 0"。**仅登记的线索，
  不主动引导**，是否相关由 GOAL-3T 判断。
- ① 卡顿：无关。

**复核**：`kb/21_swizzle_and_object_fields.md` §0。

**置信度**：**实证**（静态初始化器 + 虚表 + 槽 4 函数体三处字节）。
社区源 `YRpp/SwizzleManagerClass.h:26` 独立佐证
`static constexpr reference<SwizzleManagerClass, 0xB0C110u> const Instance{};`

**核验状态**：✅ 字节直证 + 社区源独立佐证。

---

## H-008 · 2026-10-21 · 类型识别与尺寸的正确取法（`vtable[11]`/`vtable[12]` 成对）

**发现**：`vtable[11]` = `WhatAmI()`，返回 `AbstractType` 类型 ID；
`vtable[12]` = `GetSize()`。**两者成对**，59 个类逐一命中，ID 冲突 **0**。
类型 ID 全表可由引擎自己的名字表 `0x816EE0`（74 项）直接读出。

这修正了 H-002 的表述。H-002 只说了"槽 12 不一定是 GetSize"，但没给替代判据。
本条给出：

```text
type_id = vtable[11](obj)    # 落在 0x00..0x49 且能对到名字表 ⇒ 这是主虚表
size    = vtable[12](obj)    # 只有上一步成立，才认它是 GetSize
```

**可能影响的目标**
- **③ 安全改动能力**：任何"按类型分派"的补丁（例如只对 `UnitClass` 生效）
  用 `vtable[11]` 判型，比 `dynamic_cast` 或字符串比较更稳，也**不依赖 RTTI 数据完整**。
- ①② 无直接影响。

**证据**：`kb/20_vtable_contract.md`、`evidence/class_ids.txt`（`tools/dump_class_ids.py`）。
三方一致：`vtable[11]` 字节 ↔ 名字表 `0x816EE0` ↔ 社区源 `YRpp/GeneralDefinitions.h:19`。

**置信度**：**实证**（69 类字节 + 74 项名字表直读）。
**核验状态**：✅ 字节直证 + 社区源独立佐证。

---

## H-009 · 2026-10-21 · `AbstractClass` 24 槽逐槽定名（含三个易错位置）

**发现**：`AbstractClass` 主虚表 `0x007E1F50` 的 24 个槽已逐一定名，
槽 0–7 是 COM 八槽，顺序与 YRpp 一致：

```text
[0] QueryInterface  [1] AddRef   [2] Release  [3] GetClassID
[4] IsDirty         [5] Load     [6] Save     [7] GetSizeMax
[8] ~AbstractClass  [9] Init     [10] PointerExpired
[11] WhatAmI        [12] Size    [13] AbstractClass::Save（基类序列化块）
```

**三个易错位置（对 ③ 有实际影响）**

1. **槽 4 是 `IsDirty`，不是 `Load`。** 全函数体 6 条：
   `mov ecx,[esp+4]; xor eax,eax; mov dl,[ecx+0x20]; test dl,dl; sete al; ret 4`
   —— **返回 `!Dirty`**。按"槽 4 = Load"去挂钩或读参数会拿错语义。
   真正的 `Load` 在**槽 5**（体首 `call 0x410380`，那才是有流参数的包装）。
2. **槽 13 不是 COM `Save`**，是"基类字段的序列化块"，只写 `+0x10`（`UniqueID`）
   与 `+0x20`（`Dirty`，bool）。COM `Save` 在槽 6（体首 `call 0x410320`）。
   两者撞名，引用时写全称。
3. **槽 24 不是虚函数**，是下一张表的 COL 指针（值在 `.rdata`）。
   扫虚表遇到 `.rdata` 值就该停 —— 表示"换表了"。
   附带段边界：`.rdata` 是 `0x7E1000..0x811074`（**不是** `..0x812000`），
   而 COL 指向的 TypeDescriptor 在 `.data`，查名字两段都要接受。

**可能影响的目标**
- **③ 安全改动能力**：任何"遍历虚表 / 克隆 / 存档"类补丁都会碰 0–7，
  槽号错一位就是语义完全不同的函数，上面三处是最容易错的。
- ② 主崩溃：若崩溃桩在 `Save`/`Load` 路径，`IsDirty` 与 `Load` 混淆会导致
  "以为在存档、实际在查脏标志"的误判。**仅登记，不主动引导。**
- ① 无关。

**证据**：`kb/22_abstractclass_vtable_slots.md`、`evidence/vtable_slots.txt`
（工具 `tools/dump_vtable_slots.py`，两次运行逐字节相同）。

**置信度**：**实证**（逐槽字节 + YRpp 声明顺序）。
**核验状态**：✅ 槽 0–7 双通道；槽 4 为单通道字节，但函数体仅 6 条、判据唯一。

---

## 未投递项

以下**不投**，因为与本线禁区或 GOAL-3T 在飞内容重合，投递只会制造噪声：

- 帧循环 / `CurrentFrame` 相关：GOAL-3T 禁区且已有多轮结论。
- SBH 分配器：同上。
- `HouseClass` 单位实例化与判负：同上。
- `0x0050B6F0`（`IsPlayerControl`）：虽本线做了全函数反汇编，但它是
  HouseClass 归属闸、与 ② 主崩溃的 `HouseClass` 线相邻。**本线只记录在
  `CONFLICTS.md` R-2，不主动投递**，避免引导 GOAL-3T 改向。
- 触发器派发表的逐槽明细：与三目标无交集，留在本线 KB。

---

## H-010 · 2026-10-21 · INI 查找是 CRC32 + 大小写敏感，且未命中返回**哨兵而非 NULL**

**发现**（`kb/30_ini_subsystem.md` §3，工具 `tools/dump_ini_nodes.py`）

1. **节名/键名是大小写敏感的。** `INIClass::GetSection`（`0x526810`）把节名算 CRC32
   （`0x4A1DE0` / `0x4A1FB0`，表 `0x0081F7B4` 与 `0xEDB88320` 标准表**256 项全等**），
   然后在一个**按哈希排序的 8 字节元素数组**（`{u32 hash, INISection*}`）上二分
   （`0x52B750`）。比较器 `0x52B720` **只比首 dword（哈希）**，命中后也不做字符串复核。
   ⇒ `[InfantryTypes]` 与 `[infantrytypes]` 是**两个不同的节**。

2. **"没找到"返回 `0xB7882C`，不是 NULL。** 这是 BSS 里一个共享空对象
   （`0x0052690C` / `0x00526A01` / `0x00528B60` / `0x0052B4A8` 四处都 `mov esi,0xB7882C`，
   共 19 处 `.text` 引用）。所有"读 INI 键"的路径在 miss 时都退到它。

3. **CRC32 碰撞即误命中**：因为不做名字复核，两张不同名的节若哈希相同，
   后者内容会被当作前者返回。

**可能影响的目标**

- **③ 安全改动能力**（主要）：如果任何补丁/注入通过"查 INI 键"来决定行为：
  - 用**大小写不规范的键名**会静默读不到值（拿到默认值），表现为"补丁没生效"而非报错；
  - **用 `if (!section)` / `if (!value)` 判"不存在"是错的** —— 必须先比 `0xB7882C`。
    这是本子系统最容易写出的假阴性。
  - 若在运行时**新增节**，新节必须进入 `+0x28` 的排序数组（否则 `+0x34` dirty 未被置位时
    二分查不到），单纯往链表插节点是不够的。
- ①② 无直接关系。

**证据**：`kb/30_ini_subsystem.md` §3（含逐指令片段）、`evidence/ini_nodes.txt`。
`dump_ini_nodes.py` 先用 `AbstractClass`（已知 vtable `0x007E1F50` → `.?AVAbstractClass@@`）
做 COL 解码正对照，再对 CRC 表做**全 256 项**比对，两次运行字节相同。

**置信度**：**实证**（字节逐指令 + 256 项表全等）。
**核验状态**：✅ **已异族复核**（R-020，3 通道确认 / 0 推翻；边界见 `kb/30` §7.2）。

**冲突待核**：无。与 GOAL-3T 现有结论无交集。

---

## H-011 · 2026-10-21 · `ReadBool` 只认首字符、`ReadInteger` 尾 `h` 走十六进制（写 INI 必踩）

**发现**（`kb/30_ini_subsystem.md` §10）

1. **`ReadBool`（`0x5295F0`）只看值的第一个字节**：`toupper` 后减去 `'0'` 做下标，
   查 `0x5297B4` 的 42 项字节表 → 3 元分派（`0x5297A8`）。
   只有 6 个字符被区分：`0`/`F`/`N` → false，`1`/`T`/`Y` → true。
   **其余 36 个字符（含 `2`、`-1`、`enabled`、空串）→ 返回调用方给的默认值**，
   既不报错也不当 false。

2. **`ReadInteger`（`0x5276D0`）看值的最后一个字节**：`tolower` 后与本 `'h'` 比较，
   相等则 `sscanf(value, "%xh")`（格式串 `0x825BB4`），否则 `strtol`。
   ⇒ `Key=100h` 是 **0x100**，`Key=100` 是 100。

3. `WriteBool` 写的是 `"yes"` / `"no"` 字面量，**与被读取的词汇表不一致**。

**可能影响的目标**

- **③ 安全改动能力**（主要）：任何通过"写 INI 键改行为"的补丁/配置注入——
  - 把布尔键写成 `2`、`true`（首字符小写 t 会被 toupper 成 T，**这个其实可以**）、
    `enabled`、空值，都会**静默取默认值**，表现为"配置没生效"而非错误；
  - 布尔键可以缩写（只读首字母），所以 `N`/`No`/`Nope` 等价 —— 反过来，
    **想让某键为 false 时别写 `Off`**（`O` 不在表内 ⇒ 取默认值，可能恰是 true）；
  - 整数字段的十六进制后缀只认 `h`，`0x` 前缀虽能被 `%xh` 吃下，但
    **dec 字面量加 `h` 会静默变成十六进制**，例如 `Key=90h` 是 144 不是 90。
- ①② 无直接关系。

**证据**：`kb/30_ini_subsystem.md` §10（逐指令片段 + 42 项表全表）；
`tools/dump_ini_readers.py`（`evidence/ini_readers.txt`，含 `ReadString`
头字节 `83 EC 0C` 正对照，两次运行字节相同）。

**置信度**：**实证**（分派表、类表逐项、格式串直读）。
**核验状态**：⏳ 未核验（R-017 结论，本轮复核只覆盖 R-016 八条；需补派）。

**冲突待核**：无。

> **✔ 2026-10-22 已核验（R-030）**：千问 qfmodel 异族盲验（先独立推导、后读断言集）
> **18 CONFIRMED / 0 REFUTED / 1 UNVERIFIABLE**；本线另补机器门禁
> `tools/verify_r017_claims.py`（sha 钉版 + 53 断言 + 四组负控，EXIT=0），
> 证据 `evidence/r017_crosscheck_qwen.md` / `evidence/r017_verify.txt`。
> **⚠ 对本条的两处更正（引用本条时以更正版为准）**：
> 1. 「`0x` 前缀能被 `%xh` 吃下」**错** —— `Key=0x100` 末字节是 `'0'`，
>    走不进 h 分支；回退是**单参 atoi**（非 strtol，无 base/无 `0x` 处理）
>    ⇒ **`Key=0x100` 实际解析成 0**。
> 2. 新证：**首字符 `$` 才是另一条十六进制路**（`0x527851`，`"$%x"`）
>    ⇒ `Key=$100` 与 `Key=100h` 都是 256。
> 对 ③ 的净影响：想写十六进制只用 `100h`（或 `$100`）；**写 `0x100` 会静默变 0**，
> 这比原表述更危险（原表述反而暗示 `0x` 可用）。其余条目（ReadBool 首字符表、
> 大小写、yes/no 词汇不对称）全部双证成立。详见 kb/30 §10.3 更正表与 G-36。

---

## H-012 · 2026-10-21 · `AbstractTypeClass+0x24` 既是 `ID` 又是**节名**（编译器硬约束）

**发现**（`kb/30_ini_subsystem.md` §11）

`AbstractTypeClass::LoadFromINI`（`0x00410A60`）把 `this+0x24` 直接当节名传给 `GetSection`：

```text
0x00410A79  lea ebp,[ebx+0x24]    ; ID
0x00410A7E  push ebp
0x00410A7F  call 0x526810         ; GetSection(this->ID)
```

`+0x24` 是 `char ID[0x18]`。⇒ **节头字符串 = 对象 ID**。显示名在 `+0x60`（`wchar_t*`），
由 `UIName` 键经 CSF 解析填入；`Name` 键落到 `+0x64`（上限 `0x31`）。

另：按 YRpp 声明顺序朴素相加会把 `Name` 算到 `+0x61`，**字节实测 `+0x64`** ——
差的 3 字节是 `wchar_t*` 的 4 字节对齐填充（`+0x5D`→`+0x60`）。
本类实际尾部到 **`+0x95`**。

**可能影响的目标**

- **③ 安全改动能力**：任何"按结构体偏移读写 `AbstractTypeClass` 派生对象字段"的补丁——
  - 若按朴素声明顺序算偏移，**所有派生类字段整体偏 3 字节**，
    表现为"读到相邻字段"而不是崩溃，属静默错误；
  - 若补丁需要在运行时改某类型的显示名，**改 `Name`/`UIName` 不会改节名**，
    节名要改 `+0x24` 的 `char[0x18]`（且改了会破坏与 INI 节头的对应关系）。
- ①② 无直接关系。

**证据**：`kb/30_ini_subsystem.md` §11（逐指令）；`tools/dump_ini_keymap.py`
（`evidence/ini_keymap.txt`，双正对照 + 算式/字节对齐自检，两次运行字节相同）。

**置信度**：**实证**。
**核验状态**：⏳ 未核验（R-018/R-019 结论，需补派）。

**冲突待核**：无。

---

## H-013 · 2026-10-21 · 全引擎 INI 键索引：478 个读取点、427 个键，含运行期拼出的键

**发现**（`kb/30_ini_subsystem.md` §12，工具 `tools/dump_ini_keyindex.py`）

扫 `.text` 全段得到 **478 个** INI 读取调用点，恢复 **473 个**键字面量、
**427 个**不同键。三条对"改配置改行为"的补丁有直接影响的结论：

1. **`ReadUnicodeString`（`0x528F00`）零调用点。** 引擎从不调用它
   ⇒ 用 `\uXXXX` 转义写的值不会生效。

2. **键名可以运行期拼。** `"PowerUp%01dYSort"`（`0x008194D4`）被 6 个读取点共用，
   全在 ~`0x0045FE50`；实际键是 `PowerUp0YSort` … `PowerUp9YSort`。
   按字面量写这个键无效。

3. **10 个键被多处读取**：`Description` / `DoubleThick` / `Elasticity` / `Flat` /
   `Image` / `PowerUp%01dYSort` / `Shadow` / `SpawnDelay` / `ToTile` / `Trailer`
   ⇒ 这些键在 artmd/rulesmd 里同名、由不同 loader 各读一遍，**改一处不影响另一处**。

**可能影响的目标**

- **③ 安全改动能力**：任何"通过改 INI 键让引擎换行为"的方案——
  - 以为改了一个键就够、实际有第二个 loader 也读同名键（上面的 10 个），
    表现为"改了一半生效"；
  - 对格式化键按字面量写入，永远不会被读到；
  - 依赖 `ReadUnicodeString` 的转义格式，永远不生效。
- ①② 无直接关系。

**证据**：`kb/30` §12；`evidence/ini_keyindex.txt`（1419 行，两次运行字节相同）。
正对照三重：`Name`/`UIName` 各恰好 1 处且落在 `0x00410A60`，加字面量
`0x00817854 == "Name"`。

**置信度**：**实证**（线性全扫 + 三重正对照）。
**核验状态**：✅ **已核验（R-031 定稿，2026-10-22）** — 异族 GLM 5.3 盲验
（`evidence/r018_r019_crosscheck_glm.md`）+ 本线机器门禁双算。

> **★ R-031 定稿追记（2026-10-22）——上面三个数字已换口径，请按新版引用**
>
> 本条正文的 478 / 473 / 427 是**两代之前**的数（工具静默截断所致），
> 早已由 R-023 重算为 **2,426 / 2,305 / 1,893**；R-031 再把后两个换成
> **ABI 键槽口径的 2,209 站点 / 2,023 键**。
>
> **核验结论（逐项）**：
> 1. ✅ **调用点数 2,426 成立**，两条独立路径确认：`E8` 纯字节扫描 ==
>    指令扫描，逐址相等零差异；异族盲验独立也得 2,426。
> 2. ✅ **`ReadUnicodeString` 不是零调用点** —— 正文那条**已被推翻**
>    （R-023 已改）：实际 **5 处**（`0x597B0C` / `0x597E51` / `0x5FABC1` /
>    `0x686DE7` / `0x6982C9`）。异族盲验独立复现同 5 址。
>    ⇒ **不能再以"`ReadUnicodeString` 零调用"为由排除 `\uXXXX`**，
>    目标 ③ 的这一条风险判断请撤回。
> 3. ✅ **键名可运行期拼成立**，且范围比本条更大：按键槽口径，
>    **2,023 个字面量键里含 `%` 的有 0 个** —— 所有 `%` 串都是模板。
>    `PowerUp%01dYSort` 的十个真键结论不变。
> 4. ⚠️ **「10 个键被多处读取」已作废**：键槽口径是 **137 个**键被多处读取，
>    且头部高频不是本条列的那十个；多读的本质是"多个不同 loader 共用键名"。
>
> **对目标 ③ 的净影响（修订后）**：
> - 「同名键改一处不保证全局生效」**仍然成立**，但机制要写对：不是"10 个
>   特殊键"，而是任一键都可能被多个 loader 各自读（137 个实证）。
> - **新增一条**：任何含 `%` 的串都不能当键写 —— 它们是模板，不是键。
> - **撤回一条**：不能再以 `ReadUnicodeString` 零调用点为由排除 `\uXXXX`。
>
> 证据：`evidence/r031_section12_restatement.md`（全文）；
> `kb/30_ini_subsystem.md` §12.7（定稿数字）；
> 复跑 `tools/r031_authoritative_numbers.py`（17/17 PASS, EXIT=0）+ 5 个诊断工具。
> 置信度：**实证**。核验者：R-031 本地门禁（规则 B/C 双算）+ GLM 盲验（异族）。

**冲突待核**：无（`ReadUnicodeString` 那条已在 R-023 就地更正，此处仅追记）。

---

## H-014 · 2026-10-21 · `rulesmd.ini` 的节由谁读、按什么顺序读

**发现**（`kb/30_ini_subsystem.md` §13，工具 `tools/dump_rules_sections.py`）

节名指针表在 `0x007F0C78`（31 项 `const char*`）。38 个 `RulesClass::Read_*`
里 **36 个**的节名已从代码读出（不是按函数名猜），载入顺序取自
`RulesClass::Init`（`0x6686C0`）的 32 个内部调用。

三条容易踩的：

1. **`Read_AdvancedCommandBar` 读的是 `AdvancedCommandBar`，不是同表里紧邻的
   `MultiplayerAdvancedCommandBar`。** 函数名不能用来推节名。
2. **`Read_File` 先跑三次**，负责建立 `[VehicleTypes]` 等列表节；它体内第一个节名引用
   是 `ColorAdd`，但它**不只**读那一节。
3. **同一套节会被解析三遍**：`Init` 对三份 INI（第一份 / gamemode / map）各调一次
   `Read_File`，而 28 个 loaders 在 `Read_File` 里 ⇒ **后一遍覆盖前一遍**。
   想覆盖某值就放到后面的 INI 里。`Read_General` 在 `Read_Difficulty`（调三次）之前。

**可能影响的目标**

- **③ 安全改动能力**：任何"改 rulesmd 某节生效"的补丁——
  - 若把 `[MultiplayerAdvancedCommandBar]` 当成单机也读的节，改了不生效；
  - 若依赖"先读的值会保留到后面"，会被后读的节覆盖；
  - 若想只改某一档难度，必须改对应那一次 `Read_Difficulty` 的键
    （`Easy`/`Normal`/`Hard`），不是改节名。
- ①② 无直接关系。

**证据**：`kb/30` §13；`evidence/rules_sections.txt`（两次运行字节相同）。
四项正对照：`Read_Colors→Colors`、`Read_General→General`、
`Init` 头 `81 EC D0 00 00 00`、指针表非空项 ≥28。

**置信度**：**实证**（字节 + 四条正对照）。
**核验状态**：✅ **已核验（R-021 机器门禁，2026-10-22）** ——
`tools/verify_r021_claims.py` **30/30 PASS，EXIT=0**。主体成立（指针表 31 项、
28 调用序列逐位、`Init` 只调 `Read_File`×3、`Read_General` 在三个
`Read_Difficulty` 之前、`Read_File` 首动作是 `call Read_Colors`）。
**但本条正文有三处必须按下面追记读，否则会写错 INI。**

> **★ R-021 核验追记（2026-10-22）—— 本条的 3 处错误**
>
> **错误 1（会写错键）**：正文写 `Read_Difficulties` 用
> `Easy` / `Normal` / **`Hard`** 三个键名。**字节事实：第三个是 `Difficult`。**
> ```text
> 0x818134 'Easy'   0x81BB60 'Normal'   0x83A0C4 'Difficult'
> ```
> ⇒ 写 `Hard=` 写进一个**没有任何读取点**的键，静默无效。KB §13.4 原本是对的，
> 是本条抄错了。
>
> **错误 2（已撤回的旧结论仍在正文）**：正文说「载入顺序取自 `RulesClass::Init`
> （`0x6686C0`）的 **32 个内部调用**」。这是 R-021 **已撤回**的第一版结论
> （0x1600 窗口越界读进了紧邻的 `Read_File`）。事实：`Init` 只调
> **`Read_File` ×3**，自己**不直接调任何按节的 loader**。KB §13.5 已改，
> 本条未同步。
>
> **错误 3（范围与调用数）**：正文「28 个 loaders 在 `Read_File` 里」需改为
> **29 次调用 / 28 个不同 loader**：`Read_File` 有**分离冷块**
> （`0x668F71`/`0x668F76` 两条 `je` 跳到 `0x668F90`），真范围是
> `0x668BF0–0x668FA3`，冷块里还有第 29 次调用
> `0x00668F96 Read_AdvancedCommandBar(参数 0)`。
>
> **★ 对目标 ③ 的实质影响（比上面三条更重要）**：
> `Read_AdvancedCommandBar` 用**布尔参数**在两个节之间选：
> 参数 `1` → `MultiplayerAdvancedCommandBar`（`0x668F81`），
> 参数 `0` → `AdvancedCommandBar`（`0x668F96`）；而分支条件
> （`0x668F6A`）是 `[0xA8B238]` = `SessionClass::Instance.GameMode`。
> 把两段串起来（**这一步别省**）：
>
> | GameMode | 含义 | 参数 | 读的节 |
> |--:|:--|--:|:--|
> | 0 | Campaign | 0 | **`AdvancedCommandBar`** |
> | 3 / 4 | LAN / Internet | 1 | `MultiplayerAdvancedCommandBar` |
> | 5 | Skirmish | 0 | **`AdvancedCommandBar`** |
>
> ⇒ **单机（战役 / 遭遇战）读 `AdvancedCommandBar`；联机才读 MP 节。**
> 即「MP 节是联机专用」的经验直觉**成立** —— 但依据是这两段字节，
> 不是节名。⇒ **单机改 `[MultiplayerAdvancedCommandBar]` 不生效；
> 要改单机命令栏请改 `[AdvancedCommandBar]`。** 这也意味着 §13.3 原文
> 「MP 节没人用」不成立（它被读，只是不在单机路径），但推翻它**并不**
> 带来"单机读 MP 节"的反向结论。
> （边界：只证"读了"，未证读入值是否在单机被应用。）
>
> **本追记自身的更正**：第一版追记把方向写反了（写成"单机读 MP 节"）。
> 原因：只看到两条 `je` 跳向同一处就下结论，**没把目标处的参数
> （`xor eax,eax`→`push 0`）与 F3 的判据（非 0 才用 MP 节）串起来**。
> 由异族盲验（`evidence/r021_crosscheck_blind.md`）抓出；本地门禁当时
> 只断言"存在门控"，太弱。现已按 GameMode 逐个断言。
>
> 证据：`evidence/r021_section13_verification.md`、`evidence/r021_crosscheck_blind.md`；
> KB §13.3 / §13.5 核验框 / §13.7。
> 核验者：R-021 机器门禁 34/34 + 异族盲验（独立复现 C3/C4/C5/C6 四条推翻）。

**冲突待核**：无。与 GOAL-3T 现有结论无交集。

---

## H-015 · 2026-10-21 · `ShortGame` 的读取点已定位；多数字典节是"键名即数据"

**发现**（`kb/30_ini_subsystem.md` §14，工具 `tools/dump_rules_keys.py`）

1. **`ShortGame` 由 `Read_MultiplayerDialogSettings`（`0x00671EA0`）读取**，
   与它同节（`[MultiplayerDialogSettings]`）的共 27 个键，含
   `MinUnitCount` / `UnitCount` / `MaxUnitCount` / `MultiEngineer` / `MCVRedeploys` /
   `FogOfWar` / `BuildOffAlly` / `SuperWeaponsAllowed` 等。
2. **`[VehicleTypes]` / `[BuildingTypes]` / `[Sides]` 这类节的"键"就是数据本身**：
   20 个 loader 走 `GetKeyCount` → `GetKeyName`，把键名当类型名/阵营名使用。
   ⇒ 往这些节里加条目**不需要配字段**，键名必须是合法标识；加了不认识的名字会被静默忽略。
3. 只有 5 个 loader 读固定键（27/19/14/12/11 个），其余节要么枚举键名，要么按键名注册。

**可能影响的目标**

- **①② 与 ① 的 `ShortGame` 实验**：`ShortGame` 的生效路径是
  `[MultiplayerDialogSettings]` → `Read_MultiplayerDialogSettings`（`0x671EA0`）。
  该函数**在 `rulesmd.ini` 解析期**执行（由 `Read_File` 调，见 H-014），
  不是每帧读 ⇒ 运行期改这个键不会立即影响已开始的局。
- **③ 安全改动能力**：往 `[VehicleTypes]` 等列表节追加条目不配字段即可；
  但键名必须是合法类型标识，否则静默无效（不报错）。

**证据**：`kb/30` §14；`evidence/rules_keys.txt`。

> **⚠ 2026-10-21 更正（见 H-017）**：本条引用的「306 键」**已作废**，正确值 **651**。
> 本节的核心判断（字典节的键名即数据、20 个 loader 枚举键名）不受影响，
> 但键总数与"读固定键的 loader 数量"全部变化。以 H-017 为准。
三项正对照：`Read_AI` 含 `BuildConst` / `Read_Sides` 判为枚举形态 / 总键数 ≥100。

**置信度**：**实证**（字面量直读）。
**核验状态**：✅ **已核验**（R-032 核验，2026-10-23）—— 见下方「核验回填（H-015）」。

**冲突待核**：无。

### 核验回填（H-015）· 2026-10-23

**门禁**：`tools/verify_r032_claims.py` → **13/13 PASS，EXIT=0**（`evidence/r032_verify.txt`，
两次复跑逐字相同；工具 sha16 `84b3f0b8ded6391f`）。
**证据件**：`evidence/r032_h015_dictionary_sections_verification.md`。

**判定**：机制判断 **半数推翻**（「键名即数据」只对 3/20 成立，17/20 注册的是**值**）；
计数判断 **FALSIFIED**（5 个 loader → 15 个）。

#### 1. 第 3 条被推翻：不是「5 个 loader 读固定键」

「只有 5 个 loader 读固定键（27/19/14/12/11 个）」是 R-022「306 键」时代的旧值。
实测：**15 个** loader 压入字面量键，**660 个读取站点**，去重后 **651 键**
（与 §14.2 逐项相等）。上面那条「⚠ 以 H-017 为准」的批注只改了总数，
没改这行 —— 本轮把整条判死。

**三个数各有量纲，不可混用**：

| 数 | 数的是什么 |
|--:|:--|
| 660 | 读取**站点**（同键读两次算两个）|
| 651 | **loader 内**去重（§14.2 交付口径）|
| 650 | **跨 loader** 去重（`ContentScan` 在 Difficulty/IQ 各读一次）|

9 个重复全在三个 loader：`Read_General` 1（`EngineerCaptureLevel` 写 `+0x17F8`/`+0x17FC`）、
`Read_AudioVisual` 1（`Smoke` 写 `+0x0BAC`/`+0x0BB0`）、`Read_LandCharacteristics` 7
（`Hover`/`Foot`/`Track`/`Wheel`/`Float`/`Amphibious`/`FloatBeach` 各读两次）。

#### 2. ★ 核心判断被推翻一半：「键名即数据」只对 3/20 成立

**(a) 族 A（17/20）注册的是「值」，不是「键名」。** 指令形状：

```text
call 0x526960                  ; n = CountKeys(section)  ← 上界来自 INI
call 0x526CC0                  ; key = GetKeyName(section, i) -> eax
push eax / push section
call 0x528A10                  ; ReadString(section, key, "", &buf, size)
test eax,eax / je skip         ; 值取不到 → 不注册
lea ecx,[esp+0xc] / call 0x7480D0   ; ← Registrar(buf)：注册的是**值**
```

⇒ **键名是查表的键，值是数据。** 我在第一版门禁里断言"键槽里是 `GetKeyName`
的返回值 `eax`"就当成"键名即数据"的证据 —— 那只证明键名**从哪来**，
没证明键名**被当成什么用**。是异族盲验抓出的（见 `CONFLICTS.md` **G-53**）。

**编译器必须写对的一处**：

```ini
[VehicleTypes]
0=HTNK        ; ✅ 键随意，值 = 类型名
1=SMCV
```

```ini
[VehicleTypes]
HTNK=1        ; ❌ HTNK 被当"键"去查值，查到的 "1" 被当类型名注册
```

反写**不报错**，而是静默产生一个叫 `1` 的类型条目。

**(b) 族 B（3/20）才是「键名即数据」**：`Read_Sides` 把键名交给 `0x6A46D0`
（按名字线性查 Side 表，比 `[obj+0x24]`），未命中则 `0x6A4550` 构造并追加
⇒ **键名 = 类型名，不存在则新建**；`Read_Colors` 把键名交给 `0x626AB0` 作条目索引；
`Read_ColorAdd` 用键名查三元组。

**(c) 值取不到就不注册**（17/17）：族 A 全部 `test eax,eax / je 跳过注册`。
⇒ **`Key=`（空值）与「不写这个键」完全等价**。原文"值的内容大多被忽略"不够准。

**(d) `<none>` / `none` 是保留字**：`0x7480D0` 先比 `0x00817474 "<none>"`、
再比 `0x00817694 "none"`，两个 `je` 都跳 `0x74814E`（`xor eax,eax` 零返回）⇒ 不建条目。

**(e) 未知名字会新建、不报错**：名字不在已知集合 → `new 0xE78` → `0x7470D0` 构造
并写入 `[0xA83CE4+ecx*4]` / `inc [0xA83CF0]`，全程无任何报错调用。

#### 3. 顺带更正一张表：参数个数以 `ret imm16` 为准

`dump_rules_keys.py:48` / `verify_r024_claims.py:73` 的 `READER_KEYS` 把
`0x528A10` 记作 4、`0x528F00` 记作 4、`0x529160` 记作 3；
实测 `ret 0x14`/`ret 0x14`/`ret 0x10` ⇒ **5 / 5 / 4**。

**但 R-024 的键清单不受影响**：`want` 在那两个工具里只作"向后走几步的上限"，
键永远是倒数第二个 push。R-032 用独立路径重算，**逐 loader 与交付表相等**。
⇒ 结论成立，错的是注释。机制见 `CONFLICTS.md` **G-52**。

#### 4. 对目标 ③ 的净影响

- **★ 最重要**：列表节的写法被**改正**了 —— 类型名写在**值**侧（`0=HTNK`），
  不是键侧（`HTNK=1`）。写反不报错，只静默生成垃圾条目。
  这直接决定编译器生成的 `rulesmd.ini` 是否正确。
- **加强**：族 A 必须给**非空值**（空值 = 不注册）。
- **新增**：`<none>` / `none` 是两个保留字，不能当类型名。
- **缩小**：「键名即数据」只对族 B（3 个：Colors/ColorAdd/Sides）成立，
  原文推广到 20 个是错的。
- **不变**：`ShortGame` 那条（第 1 点）由 R-023 门禁独立覆盖，本轮未动。

#### 5. 诚实边界

- 族 A 那 17 个 loader **静态无法列出它们认哪些键**（键名运行期由 INI 提供）。
  能静态回答的只有「读哪个节」和「遍历该节全部键」。这是原理限制不是工具缺陷。
- `GetKeyCount`/`GetKeyName` 的"第 i 个键名"语义是推断，未跑游戏确认。
- `0x529160` 只测了 arity（4 参 / `ret 0x10`），**未定**它是哪个读族。
- 「未知名字会新建」追到 `0x7470D0` 写 `[0xA83CE4+ecx*4]` / `inc [0xA83CF0]`，
  但**未验证运行期这些全局初值确实为 0**（BSS 未初始化是盘上推断，非观测）。

---

## H-016 · 2026-10-21 · `ShortGame` 等 18 个设置键**载入后被镜像到独立全局**，游戏读的是全局

**发现**（`kb/30_ini_subsystem.md` §15.3，工具 `tools/dump_rules_consumers.py`）

1. `Read_MultiplayerDialogSettings`（`0x00671EA0`）返回后，调用方
   （`0x0052CD70` 开头那个规则装载函数）立刻把 **18 个字段拷贝到独立全局变量**。
   **游戏其余部分大多读全局，不读 `RulesClass` 字段。**
2. 与你相关的三条：

   | 键 | `RulesClass` 偏移 | 镜像全局 | 取值引用数 |
   |:---|:---|:---|---:|
   | **`ShortGame`** | `+0x14B6` | **`0x00A8B262`** | **50** |
   | `FogOfWar` | `+0x14B7` | `0x00A8B31F` | 22 |
   | `MCVRedeploys` | `+0x14B8` | `0x00A8B320` | 44 |

3. **9 个字段不镜像**，只留在 `RulesClass` 里（读点直接走 `[RulesClass+off]`）：
   `MinMoney` `+0x1480`、`MaxMoney` `+0x1488`、`MoneyIncrement` `+0x148C`、
   `MinUnitCount` `+0x1490`、`MaxUnitCount` `+0x1498`、`ShadowGrow` `+0x14AD`、
   `Shroud` `+0x14AE`、`TiberiumGrows` `+0x14B0`、`AllyChangeAllowed` `+0x14BB`。
4. **`ShadowGrow` 是 27 个键里唯一读点为 0 的**（纯字节扫描复核：`+0x14AD` 的
   disp32 在 `.text` 里只出现 3 次，全是构造器写 + 读取器读+写）。
   写这个键对引擎行为无影响。

**可能影响的目标**

- **② 主崩溃 / ① `ShortGame` 实验**：如果你的实验改的是 `rulesmd.ini` 里的
  `ShortGame=`，生效路径是
  `Read_MultiplayerDialogSettings` → `[RulesClass+0x14B6]` → **拷贝到 `0x00A8B262`**
  → 全局被 50 处读。**若用运行期写内存的方式改，必须改 `0x00A8B262` 这个全局，
  改 `[RulesClass+0x14B6]` 不会影响已经镜像完的值。** 反之若要改 `Shroud`，
  必须改 `[RulesClass+0x14AE]`（没有全局）。
- **③ 安全改动能力**：给出"改哪个地址才真正生效"的判据。选错侧（字段 vs 全局）
  会呈现为"改了但没效果"，很容易被误判成机制不生效。

**⚠ 同时报告一个我方错误，供你评估我方数据可靠性**

`kb/30` §12（R-019 的全引擎键索引）旧数字 **478 调用点 / 473 恢复键** 是**错的**，
已在 §12.0 全面重算为 **2,426 / 2,305**。根因：capstone 的
`md.disasm(.text 全段)` **在 `0x46F5A0` 静默停止**（那里是一张跳转表），
一次调用只覆盖 `.text` 的前 9%，却返回成功。
**若你方任何工具用单次 `md.disasm` 扫 `.text` 求"全部"引用，那组数字必须重算。**
新工具 `tools/text_sweep.py` 做带审计重同步的全段扫描，并用纯 `E8` 字节扫描
（不解码）做逐址对账（当前 2426 == 2426 零差异）。

**证据**：`kb/30` §15；`evidence/rules_consumers.txt`；
`evidence/rules_fields.txt`（27 键 × 默认值 × 消费点）。

**置信度**：**实证**（字节级：18 条 `mov [全局], reg` 拷贝指令逐条列出；
每个全局的字节扫描出现次数 == 指令扫描 (取值 + 取址) 次数，18/18 相等）。

**核验状态**：✅ **已核验（R-023 核验，2026-10-22）** —— 门禁 `tools/verify_r023_claims.py`
**22/22 PASS，EXIT=0** + 异族盲验（`evidence/r023_crosscheck_blind.md`，独立复现 R1/R2，
并**纠正了我方 R3 的函数起点**）。
**维持**：27 键表、18/9 划分、三条具体映射（`ShortGame`/`FogOfWar`/`MCVRedeploys`）、
`ShadowGrow` 零消费、镜像块 18 条。**推翻/修正 3 条**（见下方追记）。

**冲突待核**：无。

---

## H-016 核验回填 · 2026-10-22 · **三条推翻（两条 ★ 影响编译器建议）**

记录件：`evidence/r023_rulesclass_mirror_verification.md`（门禁输出 `evidence/r023_verify.txt`）。

### 1. ★ 载入函数边界短了 292 字节

原记「函数 `0x52CD70` 到 `0x52D30C`，最后 `ret` 在 `0x52D30B`」**错**：

```
0x0052D274  83f801            cmp  eax, 1
0x0052D277  0f8e8f000000      jle  0x52d30c     <-- 从函数内部跳过尾部冷块
...
0x0052D30B  c3                ret
0x0052D30C  8b0de0718800      mov  ecx, [0x8871e0]   <-- 冷块，仍在读 RulesClass*
...
0x0052D42F  c3                ret                    <-- 真尾
```

真边界 **`0x52CD70..0x52D430`**。判据必须是从入口做**跳转闭包**，
「函数在自己的最后一条 `ret` 结束」是结论不是探测器。
（R-021 在 `Read_File` 上踩过同一形态：分离冷块到 `0x668FA3`。这是第二次。）

### 2. ★★ 「载入后只写一次、之后游戏读全局」不成立

这条直接改你方"改哪个地址才生效"的用法：

| 口径 | 数字 |
|:---|:---|
| 载入块内写入 | 每全局 1 条（共 18） |
| ModemGst 第二块 | 每全局 1 条（17/18） |
| **其余处写入** | **每全局最少 2 处，合计 208 处** |

这些全局是**可被运行期覆写的工作变量**，不是冻结镜像。形态是"读一处设置、按位拆开、
逐位写回同一组全局"。**所属函数身份已逐个确认**（靠函数内调试字符串）：
`ModemHst.cpp`(`0x5B796E`/`0x5B8CDA`/`0x5B9648`)、`netdlg2.cpp`(`0x5DDBC4`)、
`WDTSel.cpp`/`WDTTerr.cpp`(`0x76ED0E`)、`wonline.cpp`(`0x78F719`/`0x78F7E8`/`0x7970CE`)、
`Skirmish.cpp`(`0x6ACEDE`) —— **全部是大厅/联机/地图选择 UI**。

⇒ **要稳定改，必须改源头**（INI，或那份设置结构）。只改全局会在下一次 UI/会话刷新时被写回。
「读点在全局上」这一点没错（P11 对账 18/18 成立），错的是「改一次就够」。

### 3. ★ 存在第二个成批写入点（原文完全没提）

**函数 `0x5B67F0..0x5B6CC6`**（不是 `0x5B6011`，见 §3b）内，`0x5B69E4` 一带写同一组全局中的
**17 个**（缺 `CaptureTheFlag` `0xA8B31E`），源结构在 `[ebx+0x7E]..[ebx+0xA3]`，
紧邻调试字符串 `Decoding game options\n`（`0x82C7A4`）与 `Scenario has changed\n`（`0x82C78C`）；
同函数字符串族全指向 `D:\ra2mdpost\ModemGst.cpp`。
⇒ 这是**会话/网络房间设置包**的解码路径，与 `RulesClass` 无关。
（定位靠**字符串族**，不是靠地址邻接猜。）

盲验独立复核：该函数内**没有**任何更宽存储覆盖 `0xA8B31E`，而前面的比对块确实**读**它
⇒ 缺写是真没回写，不是漏扫。

### 3b. ★ 我方 R3 的函数起点报错了（异族盲验纠正）

原报 `0x5B6011`，**错**。真起点 **`0x5B67F0`**。
错因：我用「`ret` 之后必须是填充」回退找函数头，而 `0x5B69E1` 是**提前退出**的 `ret 4`，
**后面紧跟代码**（`0x5B69E4 push`），于是回退跨过它、退到前一函数的 `int3` 填充。
从 `0x5B67F0` 做跳转闭包：可达 `0x5B69E4`/`0x5B6B3B`，恰两条出口
（`0x5B69E1` 提前退出、`0x5B6CC0` 正常退出），止于 `0x5B6CC6` 后接 `0x90` 填充。门禁 **P13b** 钉住。

> 这与第 1 条是**同一类错误的两个方向**：第 1 条"切太短"（遇 `ret` 就停，丢冷块），
> 本条的"退太远"（要求 `ret` 后有填充，跨过提前退出）。
> **两者都源于把"边界长什么样"当判据，而不是从分支图推。**

### 4. 另纠一处归类（防撞库误归因）

`0x463Axx` 家族的 `mov [ebp+0x1488], eax` **不是** `RulesClass.MaxMoney`：
该区引 `0x887180`（`INI_Art`）、不引 `0x8871E0`，是 **artmd 侧 TypeClass** 字段。
按 disp 撞库统计 `RulesClass` 字段读点会把它算进来 —— 这正是 §15.4 只能给区间的原因。

### 5. 门禁本轮三次假色（都是自己的缺陷，记下防回潮）

- **只读 `operand[0]`**（假**红**）：`mov cl,[esi+0x14AD]` 的内存操作数在 operand[1]，
  于是所有内存**读**被漏计 —— `ShadowGrow` 显示 2 处（应 3），18 个全局引用数普遍减半。
  「只数写」不是保守，是错的，因为待验命题正是"零消费"。
- **P3 复述了交付件的边界**（假**绿**）：第一版断言"最后一条 `ret` 后是 padding"，
  等于假设了要证的东西。改成跳转闭包后立刻红，红得对。
- **R3 函数起点**（错，非门禁项）：见 §3b，盲验抓出。

### 6. 异族盲验对账（`evidence/r023_crosscheck_blind.md`）

盲验走收窄版 3 问、先独立推导、明确未读本线既有件。**6 项中 5 项独立一致，1 项纠正我方**：

| 项 | 我方 | 盲验 | 判定 |
|:---|:---|:---|:---|
| 载入函数真尾 | `0x52D42F` | `0x52D42F` | 一致（盲验另加"序言/尾栈对称 + `0x52D430` 无 jmp/call 直指"两条佐证） |
| `0x52D30C` 同函数 | 是 | 是（并指出 `0x52D245 jne 0x52D325` 跨过该段到汇合点） | 一致 |
| 18 个全局仍被别处写 | 是，全部 | 是，18 个全部 | 一致 |
| 计数 | 208（排除两块） | 全 `.text` 243 = 18+17+**208** | 一致（口径不同同值） |
| 第二写点缺项 | `0xA8B31E` | `0xA8B31E` | 一致 |
| **第二写点函数起点** | 原报 `0x5B6011` | **`0x5B67F0`** | **盲验对，我方错** |

盲验另给两处我方未做的佐证：`0x6AD75A: mov [0xa8b25c], eax`（`call esi` 返回值直接写，
独立第三类写者）；`0x79727E..0x7972FD` 连续 19 条几乎刷全部 18 个全局（形态像初始化/复位）。
盲验自陈边界（我采信）：208 是「绝对地址直写」的**下界**，基址+偏移聚合写与整块 `memcpy` 扫不到。

---

## H-017 · 2026-10-21 · `[General]` 是 rulesmd.ini 最大的节（279 键），`[AudioVisual]` 次之（152）

**发现**（`kb/30_ini_subsystem.md` §14.2，工具 `tools/dump_rules_keys.py`）

R-022 公布的「306 个字面量键」**作废**，正确值是 **651**。两处系统性低估：

1. **窗口 `0x1000` 太窄**：`Read_AudioVisual`（`0x6691E0`）的函数体到首个 `ret`
   是 **0x2710 = 10 KB**，`Read_AI`/`Read_CombatDamage`/`Read_General` 也都 4–5 KB。
   工具"解到 `ret` 就停"，窗口用完照常返回 ⇒ 这 4 个 loader 的键清单被腰斩。
2. **键提取口径错**：收集函数体内所有字面量 `push`，把默认值、节名、以及容器
   转发给委托的节名都算成了键。

修正后的分布（15 个 loader 读固定键，合计 651）：

| loader | 键数 | | loader | 键数 |
|:---|---:|:-:|:---|---:|
| **`Read_General`** | **279** | | `Read_CrateRules` | 10 |
| **`Read_AudioVisual`** | **152** | | `Read_Radiation` | 9 |
| `Read_CombatDamage` | 71 | | `Read_LandCharacteristics` | 8 |
| `Read_AI` | 52 | | `Read_SpecialWeapons` | 7 |
| `Read_MultiplayerDialogSettings` | 27 | | `Read_JumpjetControls` | 7 |
| `Read_Difficulty` | 12 | | `Read_ElevationModel` | 3 |
| `Read_IQ` | 11 | | `Read_WallModel` | 2 |
| | | | `Read_Maximums` | 1 |

**`[General]` 与 `[AudioVisual]` 两节占 431/651（66%）。**

**可能影响的目标**

- **③ 安全改动能力 / ra2forge 战役编译器**：如果生成 rulesmd.ini 时只覆盖
  `Read_MultiplayerDialogSettings` 那类"小节"，**66% 的可调参数没被覆盖**。
  优先覆盖 `[General]` 与 `[AudioVisual]`。
- **①②**：R-022 曾说"只有 5 个 loader 读固定键"，据此判断某个键"不被读取"会误判。
  例如 `[AudioVisual]` 有 152 个键，远不是小配置面。

**⚠ 与 H-016 同源的两个工具陷阱（供你方工具自查）**

- `md.disasm(.text 全段)` 在 `0x46F5A0` **静默停止**（只覆盖 9%），见 H-016。
- 窗口式取函数体**必须**断言"走到了该函数自己的 `ret`"，否则长函数被腰斩而
  输出看起来正常。这是"窗口太小"；反过来"窗口太大"会把相邻函数读进来
  （我已有一条独立纪律记录在案）。

**证据**：`kb/30` §14.0–§14.2；`evidence/rules_keys.txt`。
四项正对照：`Read_AI` 含 `BuildConst` / `Read_Sides` 判为枚举形态 /
总键数 ≥100 / **全部 38 个 loader 都走到自己的 `ret`** /
**`Read_MultiplayerDialogSettings` 的 27 键与 §15 结构体字段表逐名相等**。

**置信度**：**实证**（字面量直读 + 逐调用参数定位）。
**核验状态**：✅ **已核验（R-024 核验，2026-10-23）** —— 门禁 `tools/verify_r024_claims.py`
**15/15 PASS，EXIT=0** + 异族盲验（**279 / 152 独立一致**，12 个列表型键独立逐条确认）。
**651 总计、15 个 loader 的逐项分布、431/651 占比、20 个枚举 loader 全部 HOLDS，零推翻。**
**新增两条边界**（交付件未写死）：
1. **38 个 loader 里 18 个**在首个 `ret` 之后仍有可达代码（17 个失败尾声 + 1 个 `Read_File` 清理路径），
   但**冷块内零键字面量** ⇒ 键清单未被截断。**这不使 `first ret` 成为正确判据**。
2. **`279/152` 是「函数体内直接调用」口径**。若展开包装函数（`0x475D70`/`0x67BB10`/`0x67BAC0`/
   `0x474620`），`[General]` 是 **365**、`[AudioVisual]` 是 **160**（盲验给出）。
   `0x474620` 是 `ReadDouble` 薄包装（默认 `-1.0`）。做全量键普查时必须展开。
详见 `evidence/r024_rules_keys_fields_verification.md` §二 / §六。

**冲突待核**：无。

---

## H-018 · 2026-10-22 · `[General]` 268 个字段已定位；12 个键是列表型不是单值

**发现**（`kb/30_ini_subsystem.md` §17，工具 `tools/dump_rules_fields.py`）

`[General]` 是 rulesmd.ini **最大的节（279 键，占全部字面量键 43%）**，
读取器 `0x0066D530`，函数体 `[0x0066D530, 0x00671E8E)`。

1. **268 个标量字段的偏移已解出**，双向一致（默认载入 == 存回），
   **零"凭空多出的字段"**（全部 267 个键名都在声明键集合内）。
2. **12 个键是列表型**，不是标量：`BarrelDebris` `BaseUnit` `BridgeExplosions`
   `DamageFireTypes` `DeadBodies` `DropPod` `ExplosiveVoxelDebris`
   `MetallicDebris` `RepairBay` `Shipyard` `WeatherConBolts` `WeatherConClouds`。
   形态是 `ReadString` → `push 0; push 0`（空分隔符=默认）→ 切分 → 追加容器。
   ⇒ **这些键可以写多个逗号分隔的名字**，写单个值不会报错但只生效第一个。
3. **`[AudioVisual]` 同轮补到 151/152**（其中 `OnFire` 也是列表型）。

**可能影响的目标**

- **③ 安全改动能力 / ra2forge 战役编译器**：`[General]` 有 268 个可写字段，
  是目前已定位的最大配置面。若生成 rulesmd.ini 时只覆盖小节，
  **43% 的可调项被漏掉**。
- **①②**：如果实验里改 `[General]` 的某个键而无效，先确认它是不是
  上面那 12 个列表型之一 —— 列表型需要 `push 0; push 0` 的解析路径，
  单值语义与标量键不同。

**⚠ 一个必须提醒你的工具陷阱（我这轮又踩了）**

`Read_General` 的真实首个 `ret` 在 **`0x00671E8B`**，距入口 **18,782 字节**。
我用**手估**的 `0x0066E52F`（函数体中部）当边界，只解出 **33** 个键；
换成工具算出的边界后是 **268**。

若你方任何分析用"入口 + 固定偏移"或手估地址当函数边界，长函数会被腰斩
且**输出看起来完全正常**。判据：**解开的结果里若有任何键名不在该 loader
的声明键集合内，说明边界跨进了别的函数**；若明显少于声明键数，
说明边界太短。

**证据**：`kb/30` §17；`evidence/rules_fields_general.txt`（554 行，268 字段 + 消费点区间）；
`evidence/rules_fields_av.txt`（151 字段）。

**置信度**：**实证**（字节级：每种存回形态逐指令核；268/268 双向一致；
零凭空多出字段）。

**核验状态**：✅ **已核验（R-024 核验，2026-10-23）** —— 门禁 `tools/verify_r024_claims.py`
**14/14 PASS，EXIT=0**。**268 字段（按存回偏移去重）、12 个列表型键、
`[AudioVisual]` 151 字段/152 键、268 个偏移全部 < `0x18C0` 全部 HOLDS，零推翻。**

**★ 两条口径提醒（核验时踩到，已固化进门禁）**：

1. **必须按「存回偏移」去重，不能按字段名去重。** 按名字会得到 267/150，
   看起来像"少一个字段"——那是测量假象。合法多条目：
   `EngineerCaptureLevel` `+0x17F8`/`+0x17FC`、`Smoke` `+0x0BAC`/`+0x0BB0`。
2. **有 2 行不是标准的六列形态**，属你已标注的已知形态（不是缺陷）：
   `HarvesterUnit  -  +0x0BE4 …（默认载入=None）`、
   `CMislAcceleration  +0x04FC +0x0530 …（跨字段默认）`。
   用"恰好六列"过滤会报 266 并误判为缺 2 个字段。

**冲突待核**：`[General]` 有 7 行"默认载入偏移 ≠ 存回偏移"
（`PrismSupportModifier` `+0x0498→+0x049C` 等），成因是 `ReadDouble` 的
8 字节默认值跨字段。**以「存回」列为准**，「默认载入」列不要用来推字段边界。
（R-024 核验：268 个存回偏移互不重复、全部在界内，与此判据一致。）

---

## H-019 · 2026-10-22 · 单位/建筑的 INI 键分在 **两个文件**里，写错不报错

**日期**：2026-10-22（R-028）
**影响目标**：②（主崩溃：出图/载入期读到的类型定义）
**置信度**：**实证**（字节级；vtable COL 解出类名；613 键逐行标注文件归属）

### 发现

`InfantryTypeClass` / `UnitTypeClass` / `AircraftTypeClass` /
`BuildingTypeClass` 的 `LoadFromINI` **同时读两个 INIClass**：

| INIClass | 地址 | 来源 |
|:---|:---|:---|
| `rulesmd.ini` | — | 调用方压栈的参数（`mov ebx,[esp+0x148]` 等） |
| `artmd.ini` | **`0x00887180`** | 全局 `CCINIClass` 实例 `INI_Art` |

后者的 vtable `0x7E1AF4` 的 COL 解出的类名就是 `.?AVCCINIClass@@`。

**归属比例**（613 键全解）：

| 类 | 总键 | 写 rulesmd | 写 artmd |
|:---|---:|---:|---:|
| `BuildingTypeClass` | 270 | 119 | **151** |
| `InfantryTypeClass` | 33 | 28 | 5 |
| `UnitTypeClass` | 27 | 15 | 12 |
| `AircraftTypeClass` | 10 | 6 | 4 |
| `TechnoTypeClass` | 252 | 230 | 22 |
| `ObjectTypeClass` | 20 | 15 | 5 |

### 为什么这条对 ② 可能有意义

写错文件时**引擎不报错、不崩溃**，只是那个键永远读到默认值。
所以"我明明配了 `TurretAnimX` 却没生效"这类现象不需要崩溃也能发生，
而**反向**——把一个本该在 artmd 的键塞进 rulesmd——会留下一个
引擎从来不去读的节，同时字段保持默认。

若 `units0` / 出图期读到的某些属性与配置不符，先查**键是不是写错了文件**，
再怀疑二进制。归属表逐行可查（`evidence/typeclass_fields.txt` 的 `INI` 列）。

### 另一条可能相关的

`WaterBound` 与 `SpeedType` **共用同一个偏移 `+0x67C`**：
建筑不移动，于是 `TechnoTypeClass::SpeedType` 那个槽在
`BuildingTypeClass` 里被复用为 `WaterBound`（`cmp eax,5 / sete / and 6 / dec`：
`yes` → 存 5，`no` → 存 -1）。**同名偏移、不同语义**，
跨类按偏移做批量改写会打穿这一格。

### 证据

- `kb/30` §19（含继承链、两文件分栏、构造器链交叉核对）与 §19.11（核验）
- `evidence/typeclass_fields.txt`（**旧版，已被 v2 取代**）
- `evidence/typeclass_fields_v2.txt`（**现行**，644 行，逐行标 INI）
- `tools/dump_typeclass_fields.py`（EXIT=0，可复跑）
- `tools/verify_r028_claims.py`（独立门禁，49/49，EXIT=0）

---

## H-019 核验回填 · 2026-10-22 · **三条推翻（两条 ★ 写 INI 必读）+ 一条新增事实**

**核验方式**：另写独立解析器（锚定读者调用点，不复用原工具的 `pending`
状态机）逐行对账 → 49/49 门禁 → 异族盲验独立复核（盲验对 Q4 四个键的
偏移与"存储指令是 `fstp` 不是 `mov`"与本线完全一致）。

### ★ 数字全面更正（**引用请改用这一组**）

| 类 | 旧 | **真** |
|:---|---:|---:|
| `TechnoTypeClass` | 252 | **276** |
| `BuildingTypeClass` | 270 | **277** |
| **七层合计** | 613（rules 414 / art 199） | **644（rules 446 / art 198）** |

**根因**：工具把 `fstp [ebp+off]` 当作"栈暂存默认值"跳过，而
`TechnoTypeClass`（`mov ebp,ecx` @`0x712180`）与 `BuildingTypeClass`
（@`0x45FE5F`）的 `this` **恰好就是 EBP** ⇒ 这两个类全部 `ReadDouble`
字段被静默丢弃（24 + 7 = **31**）。

三条独立证据：① 两实现 `missing=0 / extra=31`，且 **31/31 全是 ReadDouble**；
② 这 31 个偏移**每一个**都被本类构造器在同一偏移写过默认值（24/24、7/7）；
③ 模拟"跳过 `fstp [ebp+off]`"后计数**精确落回 252 / 270**。

**31 个新增键对 ③ 直接可用**（完整见 v2 的 `ReadDouble` 行）：
`Weight +0x370`、`PhysicalSize +0x378`、`Size +0x380`、`SizeLimit +0x388`、
`DeployTime +0x3C8`、`PitchAngle +0x3B0`、`RollAngle +0x3A0`、
`InfantryCostBonus +0x16D0` … `DefensesCostBonus +0x16E0`（五个连续 dword）、
`ChargedAnimTime +0x16E8`、`GateCloseDelay +0xE28`。

### ★ 推翻 2：`MovementZone` 属 **rulesmd**，不是 artmd

`+0x05B4`，唯一调用点 `0x716079`。它的 `ecx` 来自 `[esp+0x388]`，
该栈槽与序言 `mov esi,[esp+0x37C]`（唯一 INIClass 形参）**是同一槽**
（两者在不同 esp 基线下都指向 `entry+4`）⇒ 调用方传入的 `rulesmd`。
旧表误标 artmd 源于 `cur_ini` 只写不复位，继承了 12 条指令前
`0x716044 mov ecx,0x887180` 的状态。
⇒ **写在 artmd 里的 `MovementZone=` 引擎不读，写了也不报错。**

### ★ 推翻 3：`0x887180` 的"直读 vptr"证据不成立（结论不变）

它在 **BSS**（`.data` raw 只到 VA `0x87E000`），静态读 4 字节得空。
成立的证据是**唯一写入点** `0x40E031: mov dword ptr [0x887180], 0x7E1AF4`，
及 `0x7E1AF4` 的 COL 类名 `.?AVCCINIClass@@`。`INI_Art` 结论保留、依据改写。

### ★★ 新增事实（★ 写 INI 必读）：`ReadDouble` 静默吃掉 `%`

`ReadDouble`（`0x5283D0`）读完值后：`push 0x2525`（`"%%"`）→
`call 0x7CAF30`（strstr）→ 命中则 `fmul qword ptr [0x7E3808]`。
`0x7E3808` 实测 8 字节 `7b14ae47e17a843f` = **0.01**（已解出）。

⇒ **走 `ReadDouble` 的键写成 `50%` 会被静默读成 `0.5`，不报错、不留痕。**
已知走 `ReadDouble` 的键 **35 个**（31 新增 + `LightIntensity` /
`LightRedTint` / `LightGreenTint` / `LightBlueTint`）。
战役编译器若沿用人写的百分比写法，**一整类数值键会悄悄差 100 倍**。
建议进 `INI_WRITE_RULES`。

### 影响目标

- **③（安全改动能力 / 战役编译器）**：31 个新增可用字段 + `MovementZone`
  归属纠正 + `%` 语义警告 —— 本条最直接的价值。
- **②**：`Weight` / `Size` / `SizeLimit` / `DeployTime` 等此前不在旧表里的键，
  若你方曾按旧表判定"这个键引擎不读"，需按 v2 重判。

### 诚实边界（**请看**）

- **644 不是键总数，是"标量字段"数**。另有 **153 个**键读进**内联
  `char[]` 缓冲区**（`read → lea reg,[this+off] → rep movsd`），如
  `TurretAnim` / `TurretAnimDamaged` / `TurretAnimGarrisoned`
  落在 `+0x11B0..+0x11DF`。两张表都未列它们。
- `+0x1F8` 单向不变量：**238 个字面量站点 0 违反**；另 **1 个**站点
  （`TurretAnimGarrisoned` `0x464553`）INIClass 来自栈参数、静态不可判，
  已如实标 unresolved，不计入断言。
- `SuperWeapon +0x16F0` 的"默认缺失"是工具取默认值的口径所致，非新事实。
- 异族盲验覆盖：继承链 / `INI_Art` / 对象寄存器 / 4+3 个键的偏移 /
  构造器对比；**未**逐条复核全部 644 行。

### 核验状态

**已核验**（本线独立解析器 49/49、EXIT=0、两次运行逐字节相同；
异族盲验关键点独立一致）。
件 sha256 前 16：`verify_r028_claims.py` `5fd1d9e1d0d9c377` /
`dump_typeclass_fields.py` `03135c34a02d40af` /
`typeclass_fields_v2.txt` `065ef20c1f458a79`。

### 未核验

`%` 语义：本线已独立实测常量与指令序列，但**未纳入机器门禁**
（门禁不覆盖运行期语义），异族也未专门复核这一条。

---

## H-020 · 2026-10-22 · 收尾扫描告警转发：`boot_session_fingerprint.py:1568`「路径穿越」——本线复核判**过报**（附判据，处置归你方）

**背景**：R-029 收尾时 Mimosa L2 对你方文件
`lead/goal1_boot_fingerprint_20261022/boot_session_fingerprint.py:1568` 报
🔴 路径穿越（完整扫描 `scan-2026-10-22T03-43-55.987Z-febb480a6b88`，23 条，本线目录 0 条）。
该文件在我方 §8.4 禁写区，只转发不改动。

**本线只读复核 → 判过报**：

- `:1537` `fingerprint_id = _sha256_hex(...)[:16]` ⇒ 仅十六进制字符，**不可能含 `../`**；
- `:1565` `name = "boot_fingerprint_%s_%s.json" % (stamp, fingerprint_id)`
  ⇒ `stamp` 为 `strftime`，`name` 全程受约束，`:1566` 的 join 不引入穿越面；
- `:1818` `out_dir = args.out_dir or os.getcwd()` ⇒ 唯一可变分量是操作者自定的报告输出目录，
  属 CLI 工具的常规目标选择，**无不可信输入源**。

判据：`--out-dir` 由跑工具的操作者自己给，这是设计行为不是漏洞面；扫描器只按
`os.path.join(out_dir, …)` + `open(w)` 模式匹配，未做数据流判定。

**若你方仍想消警**：`:1566` 处可加一行
`os.path.abspath(out_dir)` 前置规范化 + `os.path.commonpath` 校验，或按本仓既有
误报标注流程处置。**核验状态**：本线判过报（字节/数据流只读复核），你方工具是否接受此判归你方。

---

## H-021 · 2026-10-22 · 修完 G-41 后的爆炸半径普查：**RulesClass 那棵树安全，③ 无第二个同类漏收**

**日期**：2026-10-22（R-028 核验同轮追加）
**影响目标**：②③（**以"排除风险"为主**，不是新增可用面）
**置信度**：**实证**（字节级普查 + 逐项定性 + 正反双向对照）
**核验状态**：本线机器门禁 6/6 + 分类器正反对照通过；**未送异族**

### 为什么这条值得单独写

H-019 核验修掉了 `fstp [ebp+off]` 被误当"栈暂存"而跳过的缺陷，收回 31 个
`ReadDouble` 字段。但你方真正需要知道的是**"我还能不能信其它已交付的表"**。
一个只修两个类的补丁回答不了这个问题，所以做了全段普查。

### 结论一：RulesClass 那棵树**不在**爆炸半径内

`Read_General`（`0x66D530`）与 `Read_AudioVisual`（`0x6691E0`）的
`this` 都是 **ESI**（`0x66D547 mov esi,ecx` / `0x6691F6 mov esi,ecx`）。
EBP 排除规则在这棵树上**没有把字段当栈扔掉的机会**。

⇒ **H-016 / H-017 / H-018 的 `[General]` 268 字段 / 279 键 /
`[AudioVisual]` 151/152，不受 G-41 影响。** 这是我实测的
（普查对这两个入口判 `this=esi`，且 P3 反面对照 PASS），不是推断。

⇒ 同一轮里 `Read_MultiplayerDialogSettings`（`0x671EA0`）的
**27 个键全部自洽**（默认载入 == 存回），H-015 的数字也站得住。

### 结论二：③ 的受影响面**到此为止**

全 `.text` 里 `this`=EBP 且调用 `Read*` 的函数共 **13** 个
（根 15,751 → 去重 span 13,193 → 解析出 `this` 的 4,339 个）。
其中已被修复后工具覆盖 2 个（就是那两个类），未覆盖 **11** 个。

11 个**逐个定性**后，只有 **2 个**是 `KEY_FIELD` 形态（有"字面量键 →
`[this+disp]` 存储"，即唯一可能被同类漏收的形状）：

| 入口 | 定性 | 对 ③ 的意义 |
|:---|:---|:---|
| `0x6686C0` | `RulesClass::Init`（R-021 的 31 节载入顺序），1 键 `Players`→`+0x14D0` | **派发层，不是字段表** |
| `0x6980C0` | **联机会话/序列号 loader**（15 键，`RA2MD.INI` 的 `[MultiPlayer]`/`[SerialDefaults]`）；调用方 `0x52E119 mov ecx,0xA8B238`（`GameMode` 全局） | **R2-9 联机（只读），不进战役配置面** |

⇒ **除已修的 31 条，没有第二个同类漏收。** 你方按 v2 表生成的
rulesmd 不需要因为这条普查再改任何东西。

### 顺带：一个新发现的 loader（记录但不建议现在用）

`0x6980C0` 此前不在任何表里，本次普查发现它有 15 个「键 → 字段」：
`PortBase` / `PortPool` / `SendDelay` / `PortNumberOverride` / `PhoneIndex` /
`CheckHeap` / `WOLLimitResolution` / `LastNickSlot` / `Color` / `ColorEx` /
`Side` / `SideEx` / `WOLTaunts` / `LANTaunts` / `WOLScrollText` /
`LANScrollText`。

对 ② 可能有一条间接线索：`RA2MD.INI` 的 `[MultiPlayer]` 里
**`PortBase` / `PortPool` / `SendDelay`** 是联机端口与发送延迟。
若你方在排查"进图慢/卡"且涉及联机初始化路径，这几个键是候选观测点。
**但这属于 R2-9 只读范围，本线不做分析，也不建议在没有目标时去动它们。**

### 诚实边界

- 普查根集合 = `.text` 内 rel32 `E8/E9` 目标 + `.rdata` 中成组的 `.text`
  指针。**不是**完整 CFG：只经 `call [reg+disp]` 且该槽不在 `.rdata` 的入口
  可能不在根里。已知虚表槽覆盖了这类的主干，但**不能宣称"穷尽"**。
- `0x6980C0` 的类名是**本线命名**（`SessionSettings::LoadFromINI`），
  **置信度中**：依据是它读的节名与键名、以及调用方传入 `GameMode` 全局；
  未从 RTTI 或 vtable 确认类身份。
- 11 个未覆盖项的定性依据是"字面量键紧邻 reader + 随后 `[this+disp]` 存储"
  这一形态判据；形态判据不是语义判据，个别项可能被归类误差影响。
- 未送异族复核。

### 证据

- `tools/census_ebp_this_loaders.py`（EXIT=0，6/6）→ `evidence/ebp_this_census.txt`
- `tools/classify_ebp_this_candidates.py`（EXIT=0，正反对照通过）
  → `evidence/ebp_this_classify.txt`
- `kb/30` §19.11(g)

---

## H-022 · 2026-10-23 · 覆盖率口径状态：**双报、暂定**（Lead 裁决 D-02 → A）

**发现**：函数命名覆盖率的口径已由 R-035 重定为**双报**：

| 口径 | 分母 | 已命名 | 覆盖率 |
|:--|--:|--:|--:|
| LOWER | 13,352 | 547 | **4.10%** |
| UPPER | 14,242 | 557 | **3.91%** |
| ~~公布~~ | ~~15,224~~ | ~~551~~ | ~~3.62%~~ |

**永不单报**：任一端单独出现都会被误读成精确值。

**状态：暂定 → 待 D-06→A（口径已变更，见下）。** 按 Lead 裁决（D-02 → A，2026-10-23），在 C 会话异族盲验通过之前，这组数字**不得作为对外引用基线**，本条**不得标「已交付」**。盲验**已完成**（V-001）但其结果**推翻了下界定性**：上表 13,352 / 14,242 两行的「LOWER」是**字节扫描口径，只能当上界**。

**★ 2026-10-23 R-038 追加（口径更新，引用前必读）**：异族盲验发现本线
`fn_walk.raw_rel32_targets()` 对 E8 也用无形状校验的字节扫描 —— 7,279 个「E8 目标」
里 **563 个 `0xE8` 字节是别的指令的操作数**（563/563 逐址复核，零例外），其中 560 个
目标**只被幻影字节指向**。本线独立复现并修好门禁。改对齐解码后：

| 口径族 | LOWER | UPPER | 覆盖率 |
|:--|--:|--:|--:|
| 上界族（字节扫描，~~原 D-02 双报~~） | 13,352 | 14,242 | 4.10% … 3.91% |
| **对齐族（真 call 起点，推荐引用）** | **12,792** | **13,682** | **4.28% … 4.07%** |

**永不单报**不变；但三档双报需 **Lead 裁 D-06→A** 才定稿（D-06 / D-02 均待裁决）。
另：UPPER 对序言判据的敏感度实测 **≈2.0×**（基准 890，收紧判据得 450），
**UPPER 不可单值冻结**，引用须带敏感度注记。
**方向结论不受影响**：两种口径的覆盖率都**高于**公布的 3.62%。

**对你的影响**：若 `ra2render/` 或任何门禁/断言引用过 3.62% 或 15,224，改双报时
**优先用对齐族 4.28%…4.07%**；在 D-06→A 裁决前不要写进对外文档。

**复算入口**（可自行跑，只读）：`re_atlas/tools/verify_r035_claims.py`
（R-038 修复版：**17/17 PASS**，其中 P1 恒真项单列不计 PASS；含 P2b/P2c/P3b/P5b/P7b）；
变异 `tools/mutate_r035_gate.py`（**12/12 killed**，含区分性变异）；
独立复现工具 `tools/r038_e8_phantom.py`。


**置信度**：门禁可复算；**未盲验**。

---

## H-023 · 2026-10-23 · R1-3 剩余部分交付：17 个函数名 / 69 个源文件 / 2,589 站点

**发现**：R1-3 原目标（用调试字符串显著提升覆盖率）已证伪，天花板 **17 个函数
（0.12%）**。Lead 裁决（D-03 → A）收下剩余部分，本轮已交付成可复核清单：

| 项 | 值 | 口径 |
|:--|--:|:--|
| 可命名的函数 | **17** | 35 个 `push 'Class::Method'` 站点去嵌套归属 |
| 源文件（可归属） | **69** | `__FILE__` 去重 **74** 个 basename，其中 5 个零归属 |
| debug 字符串站点 | **2,589**（字节扫描）/ **2,588**（对齐） | path 1,299 + format 351 + text 939/938；四类合计 6,277/6,276（R-039：text 类有 1 个字节扫描幻影，见下） |

**⚠ 引用陷阱（★ 会咬人）**：
1. 「69 个源文件」**不是**「镜像里有 69 个 .cpp」。文件总数是 **74**，
   69 是「至少有一个站点能归属到函数」的文件数。拿 69 当分母算覆盖率会少 5 个；
   拿它当「这个构建包含哪些 .cpp」会漏 5 个（`CD.CPP` / `Event.CPP` /
   `GameDlg.CPP` / `Score.CPP` / `stlscore.cpp`）。
2. 「17 个函数名」只说明**该函数 push 了这个字符串**，不证明它就是那个方法。
   自洽的只有 `0x652CF3 push 'RadarClass::One_Time()'`（在 `0x652CF0` 体内）。
3. 交付清单里的地址是「最早入口优先」规则下的**入口**。`RadarClass::One_Time`
   给的是 `0x63F7B0`（`jmp 0x652CF0` 的尾调用 thunk），本体在 `0x652CF0`。
   要本体地址须再跟一次 `jmp`。
4. **R-039 补**：站点普查 2,589/6,277 基于 `re.finditer(b"\x68")` 字节扫描；
   对齐解码复核发现 **1 个幻影**（`0x5BA0CE` 是 `cmp eax,0x68` 的 imm8 字节，
   后 4 字节拼出合法字符串指针）落在 text 类。该幻影**不归属任何函数**，
   故 17/69 两个交付数字不变；只有站点普查数 −1（2,588/6,276）。


**R1-3 状态**：**已完成，目标下调**。不再投入算力。

**复算入口**（只读）：`re_atlas/tools/r036_r13_deliverable.py`
（门禁 **8/8 PASS**，含 R-039 P3b 对齐复核）→ `evidence/r036_r13_deliverable.md` /
`.txt`（含逐站点明细）；`evidence/r039_push_aligned.txt`（幻影逐址）。

**置信度**：字节实证 + 变异 **7/7**（精确集合判定，含杀幻影的区分性一例）。**未盲验**。

**对你的影响**：这三个数**不改变任何可执行建议**，属于「知道即可」。
若你方在做调试字符串/断言字符串相关改动，注意 `__FILE__` 那条路给的是**源文件名**，
`call 0x734E60` 是**字符串驻留表查找**（`ret 8`），不是 assert。

---

## H-024 · 2026-10-23 · 自查欠账：R-035 的两个数字本轮复现不出来

**发现**：本轮复算 R-035 §六 的归属表。闭包类口径下**只有 `path=425` 可复现**，
其余三列各差 1–3、合计差 3；另 §2 的重叠统计也对不上。
**R-036b 追加**：补测地址类规则后，**合计 761 精确命中且稳定**，但四列仍不符。

| R-035 报 | 本轮实测 | 状态 |
|:--|:--|:--|
| path 425 / format 147 / text 289 / ident 277 | 425 / 146 / 288 / 274（闭包类最优） | 仅 path 可复现 |
| debug 合计 **761** | **758**（闭包类 12 种落在 730…838） | 闭包类不可复现 |
| debug 合计 **761**（地址类） | **761** ✅ 但四列 **418/149/290/289** | **合计可复现、分列不可复现** |
| 重叠 **426,741 / 40%** | **523,181 / 48.7%** | **不可复现** |

**地址类命中的细节**：入口集 `roots_call|T2` = 13,352 + 886 = **14,238**
（两条独立构造收敛到该值），规则 = 「地址上最近的前驱入口，且其闭包包含该站点」。
该命中**不是刀锋**：随机删 T2 候选 1/2/5 个仍 761，删 100 个仍 752–756。
21 种组合里仅此 1 种命中合计。

**为什么不采信**：四列同时不符时，合计相等只说明两类误差抵消（ident −12 / path +7，
方向相反），不能说明规则正确。拿它改写 R-035 §六，是把四个**可核对**的分项
换成四个错的 —— 净损失。R-035 也没把归属代码落盘（`verify_r035_claims.py` 只验了
站点计数，没验函数归属），**没有独立证据**能判定当初用的哪个口径。

**影响范围**：**不影响** R-035 主结论（分母 13,352/14,242、覆盖率 4.10%/3.91%），
那些由另外的门禁断言。**只影响**引用 §六 那张表的人。

**处置**：登记为欠账，不随 R-036 交付；待 C 会话独立复算，若同样复现不出分列则按
G-57 口径作废并改写 R-035 §六。

**对你的影响**：**无**。若你方引用过 761 或 426,741，请改引用本条的实测值或等结论。

**置信度**：实测（12 种口径矩阵）。**未盲验**。

---

## H-025 · 2026-10-23 · ★ 虚表契约作用域修正：`vtable[11]` 不是「任何类」都能读

**发现**：`kb/20` 的载荷句是「**任何** `AbstractClass*` 都能用 `vtable[11]` 识别真实类型」。
实测这句话**范围过宽**。若你方照它去写「按类型分派」的代码，有 9 个类会拿到 0。

**漏斗（全部实测，字节级）**：

| 层 | 类数 | 说明 |
|:--|--:|:--|
| RTTI 总类数 | 988 | |
| 带虚表 | 954 | |
| 虚表槽数 ≤12 | **804** | **槽 11/12 根本不存在** |
| `AbstractClass` 后代 | **78** | 契约真正的作用域 |
| 其中符合 | **69** | 槽 11/12 = `mov eax,imm; ret` |
| 其中不符合 | **9** | 全是抽象中间基类 |

**9 个不符合的类**（槽 11/12 都指向 `0x004C9150`，字节 `33 C0 C3` = `xor eax,eax; ret`，
**返回 0 而不是 ID**）：

`AbstractClass` / `AbstractTypeClass` / `ObjectClass` / `ObjectTypeClass` /
`MissionClass` / `RadioClass` / `TechnoClass` / `TechnoTypeClass` / `FootClass`

**★ 但对你的实际用法仍然安全**，理由是一个关键区分：
- 69 个符合的类里，**被别的类继承的 = 0**（全是叶子/最派生类）。
- 真实对象的虚表**永远是**最派生类的那张。
- ⇒ 对真实实例读 `vtable[11]` 拿到 ID，契约成立。
- ⇒ 只有当你**故意**拿一个中间基类的虚表去读，才会拿到 0。那 9 个从不被实例化。

**正确的用法表述**（替换「任何 `AbstractClass*`」）：

> 对具体的（最派生的）`AbstractClass` 实例，`vtable[11]` 是类型 ID、
> `vtable[12]` 是实例尺寸。69 个叶子类型类全部成立。
> 不要把这套读法用在中间基类的虚表上。

**分母也要说清**：69 的正确读法是「**78 个后代中 69 个符合**」，
不是「954 个类中 69 个通过」，也不是「69/69 = 100%」。

**复跑入口**（只读）：`re_atlas/tools/verify_r037_scope.py`（8/8 PASS，EXIT=0）
→ `evidence/r037_vtable_scope.txt`（含 69 个类的 ID/尺寸全表）。

**置信度**：字节实证 + 变异 3/3（精确集合判定）。**未盲验**。

**对三个目标的影响**：**均无直接影响**。本线核对 `ra2render/` 未引用这两个槽做类型分派。
若你方后续要写按类型分派的补丁，用上表的作用域表述。

---

## H-026 · 2026-10-23 · 自查：R-037 的门禁第一版抓不住变异，已修

**发现**：R-037 的 P6 断言初版是「9 个不符合类的槽 11/12 指针都等于 `0x4C9150`」。
变异测试把 `0x4C9150` 的首字节改成 `0x90`（桩不再是 `xor eax,eax`），
**P6 不变红** —— 因为指针值没变，改的是**指针指向的内容**。

**我原先证明的**是「9 个类指向同一地址」；**我想证明的**是「那个地址是抽象桩」。
两者不是一回事。补上 `read_va(0x4C9150,3) == 33 C0 C3` 后才可杀（3/3 killed）。

**对你的意义**：这条不是给你用的结论，是提醒 —— 若你方也写了「某个槽指向某函数」
类的断言，它同样抓不到「那个函数被改坏」。**断言要落在被测物上**。

**置信度**：实测（变异前后对比）。

---

## H-027 · 2026-10-23 · P1 共享库已沉淀：`class_contract.json`（机器可读的类型 ID/尺寸契约）

**发现**：契约此前只活在散文（kb/20）与文本表里；本轮压成一份 json，
**全部数值生成时从字节重读**，可逐行复算：

- **路径**：`re_atlas/evidence/class_contract.json`（schema `ra2-atlas/class-contract/v1`）
- **内容**：69 个最派生 `AbstractClass` 叶子类的 `{class, vtable, id, size,
  engine_name, id_fn, size_fn}`；9 个抽象中间基类名单（对它们读法**不成立**）；
  名字表/桩地址与桩字节；population 漏斗 988/954/804/78。
- **用法声明（在 json 的 `scope` 字段里）**：对**具体（最派生）实例**，
  `vtable[11]` callee 返类型 ID、`vtable[12]` callee 返实例尺寸。
  中间基类的槽 11/12 指向抽象桩 `0x004C9150`（`xor eax,eax;ret`），返回 0。

**★ 一处勘误（若你方引用过 kb/20 需要知道）**：引擎名字表（`0x816EE0`，74 项）
的存储顺序**不是严格递增**——条目 69=`Temporal(0x46)`、条目 70=`RadSite(0x45)`。
「值集合 = {0x00..0x49}、无空洞」仍成立；**若你方有校验按「递增」判这张表，
会在索引 70 误报**。正确判据是集合相等。kb/20 §1 已加勘误横幅。

**复算入口**（只读）：`re_atlas/tools/r040_shared_contract.py`（6/6 PASS；
其中 C3/C4/C5/C7 为字节可钉，C2/C6 为结构性普查）；
`tools/mutate_r040_gate.py`（4/4 killed，精确集合判定）。

**置信度**：字节直读 + 4 正对照（TEventClass/HouseClass/UnitClass/TeamTypeClass，
其中 TeamTypeClass=248 与 H-001 的翻案值交叉吻合）。**未盲验**。

**对三个目标的影响**：若你方写「按类型分派」的守卫/补丁，现在可以直接吃这份
json，不必再解析散文；引用尺寸时用 `size` 字段（单位字节，实例尺寸）。

---

## H-028 · 2026-10-23 · 流程自纠：本线的散文措辞已被门禁证伪过一次，别再搬进断言

**发现**：R-040 的门禁 C4 照抄了本线 kb/20 散文「`value` 严格递增」——首跑变红，
证伪的是**我们自己**的措辞。若当时「改断言迁就散文」，勘误就留在知识库里了。

**对你的意义**：这是「门禁要断言取值、不要断言散文/存在」的同型提醒——
**形状词（递增/单调/成对）不可从散文搬进校验，要独立判字节**。
你方门禁若引用过本线文档里的形状措辞，值得照此复查一遍。

**置信度**：实测（门禁首跑 FAIL → 逐址查明 1 处非递增 → 判据改集合相等）。
