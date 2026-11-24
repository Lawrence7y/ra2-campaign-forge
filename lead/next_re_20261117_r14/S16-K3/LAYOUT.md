# LAYOUT.md — 4 条 `[已证]` 的正确依据链（T2 重做）

撤销 S16-K2 的全部错误前提；逐条以「槽位 + 函数体 + 类归属」三独立支柱重建。
未截断原字节见 `EVIDENCE/E02_t2_bodies.txt`；槽位见 `EVIDENCE/E01_t1_slots.txt`；
零交叉污染普查见 `EVIDENCE/E03_forwarders.txt`。

## 0. 必须撤销的假前提（a-S16-K2-B ★B 裁决）

| 旧表述（作废） | 实测反证 |
|---|---|
| `0x410320` = `AbstractClass::Save` | `0x410320` 在 `.rdata/.data` 作为 **dword 出现 0 次**、作为 **vtable 槽值出现 0 次**（1214 张表全扫）⇒ 非虚函数、不在任何虚表；`AbstractClass::Save` 真身是 **slot 13 = `0x410410`**（SLOTS.md §3） |
| `0x410320` 是虚函数 / 槽 6 = `0x410320` | `AbstractClass.v[6]=0x4C9150`（`33 C0 C3` 纯虚桩）；SuperClass/SWT v[6]=`0x6CDFD0`/`0x6CE8D0`，都是**调用** `0x410320` 的包装器，不是它本身 |
| 「与基类 Save 槽号一致」可作证据 | 基类槽 6 是空桩 ⇒ 无基类实现可供继承语义，此论证无效，已删 |
| `docs/re/superweapon_re.md:701-721` 把 `0x410320` 标成 `AbstractClass::Save` | 该文档含同一假前提，见 `DISAGREE.md` D2 |

`0x410320` 的真实身份：`E_POINTER` 守卫（空 `pStm` 返 `0x80004003`）+ 经 IStream 写 dword 的**共享 Save 包装器**；
`EVIDENCE/E02` 里 `0x410320` 体：`push esi; mov esi,[esp+0xc]; test esi,esi; ... mov eax,0x80004003; ret 0xc` / `mov eax,[esi]; ... call [eax+0x10]`。
同理 `0x410380` 是共享 **Load** 包装器（`call [eax+0xc]` = IStream::Read 侧）。

## 1. 我的定名判据（先立标准，再套用）

> 纯转发函数 `call X; ret` 的 `[已证]` 判据：
> **(a)** 被调者 X 的语义有**独立于槽位**的字节证据（此处 `0x410320` 的 E_POINTER 守卫 + IStream 调用 =
> IPersistStream 保存包装器签名，见 KB22 §0 槽 0/7 同型）；
> **(b)** 槽位本身有**独立交叉验证**：跨类普查「v[6] 体调 X、v[5] 体调 Y」**零交叉污染**；
> **(c)** 类归属由 RTTI 独立给出；
> **(d)** 函数体**完整打到 ret**（不截断）。
> 四条全满足才给 `[已证]`；若只能靠「它在槽 N」推语义（缺 a 或缺 b）⇒ 降 `[静态推断]`。

跨类普查实测（1214 张 COL 根 vtable）：**v[6] 体调 `0x410320` 者 54 类；v[5] 体调 `0x410380` 者 41 类；
v[6]→`0x410380` = 0、v[5]→`0x410320` = 0（零交叉污染）**。`0x410320` 作为**槽值**出现 0 次（非虚，与 54 条「体调用」不矛盾）。

## 2. 逐条重建

### 2.1 `0x006CDFD0` → `SuperClass::Save` — **[已证]**（4/4 判据全过）
- 类归属：唯一 vtable 命中 `vft=0x7F3FE8, col=0x80B610, TD=0x8423E0, name=.?AVSuperClass@@, off=0`，**slot 6**。
- 完整体（11 条，`[0x6CDFD0,0x6CDFED)`，首 `ret` 于 `0x6CDFEA`，后接 nop 对齐）：
  `8B44240C / 8B4C2408 / 8B542404 / 50 / 51 / 52 / E8(→0x410320) / 85C0 / 7C02 / 33C0 / C20400`。
- 语义：3 栈参 `ret 0xC`（this, pStm, fClearDirty）→ 共享 Save 包装器 `0x410320` → `test eax;jl;xor eax,eax`
  是 HRESULT 归一化（非「纯转发 call;ret」，旧卡漏了这 3 条）。与 KB22 槽 6 = COM Save 同型，54 类零交叉污染。
- 定名理由：槽契约（KB22）、被调者字节签名、RTTI 类、完整体四支柱独立成立 ⇒ `[已证]`。
  **删去**旧证的「`call 0x410320(AbstractClass::Save)`」括注。

### 2.2 `0x006CE220` → `~SuperClass` — **[已证]**（4/4 判据全过）
- 类归属：`vft=0x7F3FE8, col=0x80B610, TD=0x8423E0, .?AVSuperClass@@`，**slot 8**。
- 完整体（8 条，`[0x6CE220,0x6CE23E)`，`ret 4` 于 `0x6CE23B`）：
  `56 / 8BF1 / E8(→0x6CB120) / F644240801 / 7409 / 56 / E8(→0x7C8B3D) / 83C404 / 8BC6 / 5E / C20400`。
- 语义：`0x6CB120`（基类 dtor，写 SuperClass 4 张 RTTI vtable）+ `test byte [esp+8],1` 删除标志 + 条件
  `call 0x7C8B3D`（operator delete）+ `ret 4` = **规范标量删除析构**。此语义**不靠槽位**（体自身自证），
  槽 8 只是旁证 ⇒ 比 2.1 更强。

### 2.3 `0x006CE8D0` → `SuperWeaponTypeClass::Save` — **[已证]**（4/4 判据全过）
- 类归属：`vft=0x7F4090, col=0x80B6C8, TD=0x842600, .?AVSuperWeaponTypeClass@@`，**slot 6**。
- 完整体：与 2.1 **逐字节同构**（`8B44240C/8B4C2408/8B542404/push×3/E8→0x410320/85C0/7C02/33C0/C20400`，
  `[0x6CE8D0,0x6CE8ED)`，`ret 0xC` 于 `0x6CE8EA`）。
- 语义/定名同 2.1；归属由 RTTI 独立锁定（非按与 SuperClass 同构反推）。

### 2.4 `0x006CEFE0` → `~SuperWeaponTypeClass` — **[已证]**（4/4 判据全过；**非「规范型」**）
- 类归属：`vft=0x7F4090, col=0x80B6C8, TD=0x842600, .?AVSuperWeaponTypeClass@@`，**slot 8**。
- 完整体（`[0x6CEFE0,0x6CF066)`，`ret 4` 于 `0x6CF063`，逐条见 E02）：
  `51 / 56 / 8BF1 / 8D442404 / B9 A8E330 / C706 90407F00 / C74604 74407F00 / C74608 6C407F00 /
   C7460C 64407F00 / 8B15[0xA8E330] / 50 / 89742408 / FF5210 / 83F8FF / 742D / ...（注销循环 0x6CF030..046）/
   8BCE / E8(→0x4109C0 =~AbstractTypeClass) / F644240C01 / 7409 / 56 / E8(→0x7C8B3D) / 83C404 /
   8BC6 / 5E / 59 / C20400`。
- 语义：**复杂**标量删除析构：写 SWT 4 张 vtable + 从全局 `0xA8E330` 类型注册表注销 + 调基类析构
  `0x4109C0` + 删除标志条件 `operator delete` + `ret 4`。旧卡称「4 条规范型」**不准确**，此条须按复杂型描述
  （a-S16-K2-B ★B 已指出）；分级仍 `[已证]`（体自身自证 + RTTI + 槽 8）。

## 3. 重做结果汇总

| entry | 定名 | 槽 | 类归属(RTTI) | 完整体 | 跨类锚 | 级 |
|---|---|---:|---|---|---|---|
| `0x6CDFD0` | `SuperClass::Save` | 6 | ✓ | ✓ 11 条到 ret | ✓ | **[已证]** |
| `0x6CE220` | `~SuperClass` | 8 | ✓ | ✓ 11 条到 ret | n/a（体自证） | **[已证]** |
| `0x6CE8D0` | `SuperWeaponTypeClass::Save` | 6 | ✓ | ✓ 11 条到 ret | ✓ | **[已证]** |
| `0x6CEFE0` | `~SuperWeaponTypeClass` | 8 | ✓ | ✓ 49 条到 ret | n/a（体自证） | **[已证]** |

**4 条全部重做后成立（4/4），但依据文字全部改写。** proved 净变化 0（仍为 46/90），
因为错误前提是「依据文字」层而非「地址/语义」层——这与 a-S16-K2-B「4 条独立复现成立、须改依据」一致。

### 3.1 若审计采用更严标准的敏感性（诚实列出）
若审计坚持「纯转发必须由函数**自身**含语义字节、不得借被调者 `0x410320` 的语义与跨类普查」，
则 2.1/2.3 两条将降 `[静态推断]`，成立数 = **2/4**；届时 proved = 42+2 = **44/90 = 48.89% < 50%**，
S16 在 proved 线也不达标。本卡采 §1 判据（a/b/c/d 全过）判 4/4，但**不隐瞒**此敏感性；最终以审计裁定为准。
