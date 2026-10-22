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
**核验状态**：⏳ 未核验（R-018/R-019 结论，需补派）。

**冲突待核**：无。

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
**核验状态**：⏳ 未核验（R-021 结论，需补派）。

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
**核验状态**：⏳ 未核验（R-022 结论，需补派）。

**冲突待核**：无。

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

**核验状态**：⏳ 未核验（需补派异族复核）。

**冲突待核**：无。

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
**核验状态**：⏳ 未核验（需补派异族复核）。

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

**核验状态**：⏳ 未核验（需补派异族复核）。

**冲突待核**：`[General]` 有 7 行"默认载入偏移 ≠ 存回偏移"
（`PrismSupportModifier` `+0x0498→+0x049C` 等），成因是 `ReadDouble` 的
8 字节默认值跨字段。**以「存回」列为准**，「默认载入」列不要用来推字段边界。

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

- `kb/30` §19（含继承链、两文件分栏、构造器链交叉核对）
- `evidence/typeclass_fields.txt`（688 行，613 键，逐行标 INI）
- `tools/dump_typeclass_fields.py`（EXIT=0，可复跑）

### 未核验

本地字节自洽 + 构造器链交叉，**未做异族复核**。

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
