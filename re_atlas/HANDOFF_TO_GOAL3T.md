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
**核验状态**：⏳ 单通道字节，异族核验待派（本轮渠道被 GOAL-3T 占用）。

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
**核验状态**：⏳ 待六模型复核结果回填（`dwfrun-b287db93` 复核的是 R-016 八条，
本节的布尔/整数规则**需下一轮补派**）。

**冲突待核**：无。

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
**核验状态**：⏳ 单通道字节，待异族核验。

**冲突待核**：无。
