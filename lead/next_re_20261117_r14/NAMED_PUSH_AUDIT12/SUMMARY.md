# NAMED_PUSH S22_B4 11 行 — 异族审计 SUMMARY

状态：**已完成**（11 行全审，逐行落盘）
审计员：异族独立审计员（非 Hy4、非 DeepSeek）；全部结论由本人反汇编得出，未引用执行器的 `ROW_*.txt` / `REPORT.md` 作为证据
二进制：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
SHA-256 实测：`73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（与卡面期望**一致**）
工具：Python 3.12.10 + capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26；自写 `work\aud.py`（PE 映射）、`work\rt.py`（RTTI）、`work\bodies.py`、`work\check11.py`、`work\derive.py` / `work\derive2.py`（要素全派生）、`work\com2.py` / `work\clsid.py`（COM 注册与 CoCreateInstance）

## 总账

| | 行数 | entry |
|---|---:|---|
| **PASS** | **11** | `006C5210` `006C5390` `006C5510` `006C5690` `006C5810` `006C5990` `006C5B10` `006C5C90` `006C5E10` `006C5F90` `006C6110` |
| **FAIL** | **0** | — |

11/11 判 PASS。**但这不等于无保留放行**——三类需账必须写进台账（见 §「需账 3 类」），另有一处口径问题须由 Lead 裁定（见 §「判读提请」第 1 条）。

## 11 个 entry 的取法（卡面要求先写）

任务范围以本次指令为准：**`NAMED_PUSH_S22_B4\delta.tsv` 的全部 11 个数据行**。取法：按表头 `entry`\t`subsystem`\t`name`\t`one_line_semantics`\t`grade`\t`evidence_path` 解析，该文件为 1 行表头 + 11 行数据，`subsystem` 全为 `S22`、`grade` 全为 `[已证]`，逐行 `entry` 即上表 11 个地址。

> 口径差异说明（不加掩饰）：卡片 `_cards\a-NAMED-PUSH-2.md` 的「待审 11 行」表写的是 **S14_B2(6)+S05_B1(3)+S05_B2(2)**，那是**上一批**、已由 `NAMED_PUSH_AUDIT2` 出过报告（PASS 10 / FAIL 1 = `006A48A0`）。本次指令明确改为 `NAMED_PUSH_S22_B4`，而该目录的 `delta.tsv` 恰为 11 行，故按本次指令执行；卡片其余条款（五项验法、输出格式、纪律）全部照用。卡片 §「本批要特别回答的一件事」（S14 的 4 行标量析构）在 S22_B4 **不适用**——S22_B4 无析构行，11 行全是 `TClassFactory<V>::CreateInstance`；该问题已由 `NAMED_PUSH_AUDIT2` §「对 S14 那 4 行析构的专门结论」回答，本报告不重复、也不借机追溯裁改。

交叉自洽（只作行数校验，不作证据）：`base_rate.tsv` = `S22_B4 13 11 12 13 11 0.8462`；`PROGRESS.md` 记 13 行核完、11 成立、2 FAIL（`006C3E90`、`006C4190`）。`delta.tsv` 的 11 行正是这 11 个「成立」行 ⇒ 本批是**执行器自认全过**的批次，这正是最需要异族复核的形态。

## FAIL 逐条原因

**无 FAIL。**

## 需账 3 类（不构成 FAIL，但必须进台账）

### 需账 1 ·「失败 Release 新建对象」措辞不准（11 行共性）

第 4 列语义栏统一写「失败 Release 新建对象」。实测失败路是 `call dword ptr [edx + 0x20]`（如 `006C5278` `ff5220`）并前置 `push 1`，即 **vt+0x20 = slot8 = 该类的删除析构器**（如 FactoryClass 的 `004CA770`：装 4 表 → `call 0x7258D0` 解单例 → 从 `0xA83E30` 注册表摘除 → 按 delete 标志释放）。

真正的 COM `Release` 是 slot2，而 slot2 在本族是 **`00410310` = `mov eax,1; ret 4` 桩**（slot1 `00410300` 同为 `mov eax,1; ret 4`，即 AddRef 桩）——**Release 根本不释放**。

- 性质：与本批上一轮 `00414290` 同类「措辞错」，**不是方向性实质错**（失败侧确实销毁新对象，方向对）；按 `NAMED_PUSH_AUDIT2` 先例记需账不改判。
- 建议台账备注：「失败侧走 deleting-destructor slot8（带 flag=1），非 slot2 Release；本族 AddRef/Release 均为 `return 1` 桩」。

### 需账 2 · ② 主虚表的「主/小表」判定依据（B1 翻车点，本批**未踩**）

B1 批的翻车形态是「把小成员表当主虚表」。本批 11 行**逐行单独核过主/副表**，结论是**执行器引的都是主表**。

补充一个反直觉的实测：**这 11 个产品类没有一个是单表**，全部是「1 张主表（offset 0）+ 3 张副表（+4/+8/+0xC）」的四表对象，副表 slot0 分别固定为 `004105E0` / `00410580` / `00410590`（三个不同的 adjustor thunk）。因此主表判据可以完全机械化：**offset 0 且 slot0 = `00410260`**。

| entry | 产品类 | 主表（offset 0） | 主表 slot0 | 副表 +4 / +8 / +0xC（slot0） | 成员表 |
|---|---|---|---|---|---|
| 006C5210 | FactoryClass | `007E88D0`@`004C991A` | `00410260` | `007E88B4`@`004C9920` / `007E88AC`@`004C9926` / `007E88A4`@`004C992D`（`4105E0`/`410580`/`410590`） | `007E8934`@`004C98E6` DynamicVectorClass<TechnoTypeClass*> |
| 006C5390 | WarheadTypeClass | `007F6B30`@`0075D0BA` | `00410260` | `007F6B14`@`0075D0C1` / `007F6B0C`@`0075D0C7` / `007F6B04`@`0075D0CE` | TypeList×3 |
| 006C5510 | WeaponTypeClass | `007F73B8`@`00771E77` | `00410260` | `007F739C`@`00771E7D` / `007F7394`@`00771E83` / `007F738C`@`00771E8A` | TypeList×3 |
| 006C5690 | ParticleClass | `007EF954`@`0062BC4A` | `00410260` | `007EF938`@`0062BC50` / `007EF930`@`0062BC57` / `007EF928`@`0062BC5E` | — |
| 006C5810 | ParticleTypeClass | `007F0188`@`00644CF4` | `00410260` | `007F016C`@`00644CFA` / `007F0164`@`00644D01` / `007F015C`@`00644D08` | `007E4E58`@`00644C46` TypeList<RGBClass> |
| 006C5990 | ParticleSystemClass | `007EFB9C`@`0062DFA6` | `00410260` | `007EFB80`@`0062DFAC` / `007EFB78`@`0062DFB3` / `007EFB70`@`0062DFBA` | `007E9D64`@`0062DF4A` DynamicVectorClass<ParticleClass*> |
| 006C5B10 | ParticleSystemTypeClass | `007F00A8`@`0064419C` | `00410260` | `007F008C`@`006441A2` / `007F0084`@`006441A8` / `007F007C`@`006441AF` | — |
| 006C5C90 | AITriggerTypeClass | `007E2A50`@`0041E401` | `00410260` | `007E2A34`@`0041E407` / `007E2A2C`@`0041E40E` / `007E2A24`@`0041E415` | — |
| 006C5E10 | NeuronClass | `007E3DF0`@`0043A375` | `00410260` | `007E3DD4`@`0043A37B` / `007E3DCC`@`0043A382` / `007E3DC4`@`0043A389` | — |
| 006C5F90 | FoggedObjectClass | `007E8B38`@`004D0909` | `00410260` | `007E8B1C`@`004D090F` / `007E8B14`@`004D0916` / `007E8B0C`@`004D091D` | `007E8BA0`@`004D08F5` DynamicVectorClass<DrawRecord> |
| 006C6110 | AlphaShapeClass | `007E32A4`@`00420B10`（`[edi]`，`mov edi,ecx`@`00420AF2`） | `00410260` | `007E3288`@`00420B16` / `007E3280`@`00420B1D` / `007E3278`@`00420B24` | — |

11 行主表 **slot0 全部 = `00410260`**，且 `00410260` 是真正的 QueryInterface（`00410269` `b803400080`=E_POINTER、`004102E6` `b802400080`=E_NOINTERFACE、`004102F8` 成功返 0，逐 IID 比较 `007F7C90`/`007F7C80`/`007F7C70`/`007E9AE0` 后 `call [eax+4]`=AddRef）。副表 slot0 = `004105E0`（调节 thunk 版 QI）——执行器**没有**拿它冒充主表。**B1 的翻车形态在本批不成立。**

### 需账 3 · ④ 的强度：是「活表安装 + COM 注册」，不是本镜像内的派发点

11 行的 ④ 都落在「工厂构造器写活表 → 该对象作为 pUnk 交给 `CoRegisterClassObject`」：

- 工厂构造器（如 `006C5140`）只有 4 条：`8bc1` / `c74004 00000000` / `c700 983d7f00` / `c3`，把 `{vt}` 写进 `operator new(8)` 出的活堆对象；
- 该 vt 指令字面量**全镜像只出现 1 次**（如 `006C514B`），即**不存在第二个写点** ⇒ **㉓ 成对陷阱在本批 11 行全部不成立**（没有「析构器也装同一张表」）；
- 注册调用点（如 `006BD43C` `call esi`，`esi = [0x7E15D8]` 于 `006BC43F`）属宿主 `006BB9A0`——从 `006BB9A0` 线性反汇编 6400 条指令**零 `.byte` 跳过**直通该块，未跨函数；宿主非 atexit、非析构。

**但**：这 11 个 entry 的 `slot3` 在本镜像内**没有任何一处派发调用**（见下节 direct=0 与 CLSID 无使用方）。所以 ④ 的实质是「活虚表**安装**到已注册的 COM 类对象」，派发发生在 ole32 侧、不在镜像字节里。按 `NAMED_PUSH_AUDIT2` 已确立并被执行的口径（④ = 行外的真构造器写点），这成立；按更严的「必须存在对本 vt 槽的镜像内派发」口径，11 行会全部翻 FAIL。**这属政策口径差，不是字节差**，见 §判读提请。

## 独立核验（指令另点）：direct caller 与 CoCreateInstance

### 1 · 11 行的 direct caller 是否真为 0 —— **属实**

两种互相独立的方法，结论一致：

- **调用指令扫描**：对每个 entry 扫全 `.text`（`0x401000`–`0x7E038D`）的 `E8/E9 rel32`，命中 **0**。该扫描只可能产生假阳性（错位字节被当成 call），不可能漏掉真实 call ⇒ 0 命中即 0 真调用者。
- **数据引用扫描**：全镜像找 4 字节等于 entry 的位置，除各自 vtable 槽（`007F3DA4`/`007F3DBC`/`007F3DD4`/`007F3DEC`/`007F3E04`/`007F3E1C`/`007F3E34`/`007F3E4C`/`007F3E64`/`007F3E7C`/`007F3E94`）外 **0 处**（无函数指针表、无跳转桩）。

⇒ 第 4 列「direct 调用者=0」准确。

### 2 · 镜像内是否真有 CoCreateInstance 使用这些 CLSID —— **没有；但镜像确实在用这套机制**

- `ole32.dll` 同时导入 `CoRegisterClassObject`（IAT `007E15D8`）与 `CoCreateInstance`（IAT `007E15FC`）。
- 全 `.text` 有 **21 处** `call dword ptr [0x7E15FC]`：**15 处 rclsid 为静态立即数**，**6 处 rclsid 由寄存器/对象字段给出**（动态）。
- 15 处静态 rclsid 的取值集合：`{0E272DC9-…}`×6、`{1440AD10-…}`、`{B48FA168-…}`×2、`{E6F33E57-…}`×3、`{4DD3BAF5-…}`、`{B832B0AB-…}`、`{BF6EA206-…}`。
- 本批 11 行各自注册的 CLSID 与该集合**交集为空**：

| entry | 注册 CLSID | 静态 CoCreateInstance 使用 |
|---|---|---|
| 006C5210 | `{34ECD9A8-0AB0-11D2-ACA7-006008055BB5}` | 无 |
| 006C5390 | `{A8C54DA4-0F7B-11D2-8172-006008055BB5}` | 无 |
| 006C5510 | `{9FD219CA-0F7B-11D2-8172-006008055BB5}` | 无 |
| 006C5690 | `{0E272DCC-9C0F-11D1-B709-00A024DDAFD1}` | 无 |
| 006C5810 | `{703E044B-0FB1-11D2-8172-006008055BB5}` | 无 |
| 006C5990 | `{0E272DC8-9C0F-11D1-B709-00A024DDAFD1}` | 无 |
| 006C5B10 | `{703E044A-0FB1-11D2-8172-006008055BB5}` | 无 |
| 006C5C90 | `{BA093524-4CF4-11D2-BC26-00104B8FB04D}` | 无 |
| 006C5E10 | `{241AB316-4CF5-11D2-BC26-00104B8FB04D}` | 无 |
| 006C5F90 | `{1C470B0E-69D7-11D2-B8F2-006008C809ED}` | 无 |
| 006C6110 | `{623C7584-74E7-11D2-B8F5-006008C809ED}` | 无 |

- **每个 CLSID 在全镜像只有 2 处 32 位引用**：① 注册块（`0x6BD4xx` 一带 `push imm`）② 本类的 `GetClassID`（如 `004CA230` `mov eax,[esp+8]; test; jne; mov eax,0x80004003; ret 8; …` 把 GUID 拷进 `ppClsid`）。**没有第三处**。
- 反证机制是活的：注册块里**紧邻的兄弟工厂** `TClassFactory<BulletClass>`（ctor `006C4FC0`、vt `007F3D80`、CLSID `{0E272DC9-…}`）在镜像内被 `CoCreateInstance` 使用 **6 处**（`00469F4B` `0046A123` `0046A564` `0046A9E2` `0046B072` `0046B3D8`，另 `0046B570` 是该类的 `GetClassID` 返回同一 GUID）。且其消费方真的按 HRESULT 分支——如 `0041C283` `85c0` `test eax,eax` / `0041C285` `7c4c` `jl`。

### 3 · 对 M70「本 entry 返回码无消费方」的准确性判定

- **静态意义上成立**：这 11 个 entry 无 direct caller；其 CLSID 无静态 CoCreateInstance 使用方。M70 若指的是这个，准确。
- **但不能写成「绝对无消费方」**，两点要限定：
  1. **entry 体内确有消费点**：对本函数 `call [主表slot0]`（`00410260` QI）返回码的 `test edi,edi` + `jge` 就是 ③b② 的证据。M70 说的是**对外返回码**，与体内消费点**不是一回事**，两者不要互相顶掉。
  2. **镜像存在 6 处「动态 rclsid」的 CoCreateInstance，以及 `0x41C250` 这类「按调用方给的 CLSID 创建」的加载器（13 个调用者；其对 CoCreateInstance 返回码 `test eax,eax` / `jl` 分支，见 `0041C283`/`0041C285`）；调用方（如 `00416BAB` `call [edx+0x84]` → `00416BB1` `add eax,0x34c`）取的正是对象内的 CLSID 字段。** ⇒ 若运行期数据（存档/类型描述）出现上述 11 个 CLSID，即会出现真实消费方。

**建议 M70 措辞改为**：「本批 11 个 CLSID 在镜像内无**静态**点名使用方；镜像另有泛用的按-CLSID 创建路径（动态 rclsid 6 处 + `0x41C250`），故不能排除运行期消费；且 entry 体内的返回码消费点（对 QI 的 `test/jge`）不因对外无消费方而消失。」

## 逐行落盘记录

| # | entry | 产品类 | ② 槽 | ③b | ④ 写点 / 注册点 | direct | 判 |
|---:|---|---|---|---|---|---:|---|
| 1 | `006C5210` | FactoryClass | `007F3DA4` | 3b2 | `006C5149` / `006BD43C` | 0 | PASS |
| 2 | `006C5390` | WarheadTypeClass | `007F3DBC` | 3b2 | `006C52C9` / `006BD479` | 0 | PASS |
| 3 | `006C5510` | WeaponTypeClass | `007F3DD4` | 3b2 | `006C5449` / `006BD4B6` | 0 | PASS |
| 4 | `006C5690` | ParticleClass | `007F3DEC` | 3b2 | `006C55C9` / `006BD4F3` | 0 | PASS |
| 5 | `006C5810` | ParticleTypeClass | `007F3E04` | 3b2 | `006C5749` / `006BD530` | 0 | PASS |
| 6 | `006C5990` | ParticleSystemClass | `007F3E1C` | 3b2 | `006C58C9` / `006BD56D` | 0 | PASS |
| 7 | `006C5B10` | ParticleSystemTypeClass | `007F3E34` | 3b2 | `006C5A49` / `006BD5AA` | 0 | PASS |
| 8 | `006C5C90` | AITriggerTypeClass | `007F3E4C` | 3b2 | `006C5BC9` / `006BD5E7` | 0 | PASS |
| 9 | `006C5E10` | NeuronClass | `007F3E64` | 3b2 | `006C5D49` / `006BD624` | 0 | PASS |
| 10 | `006C5F90` | FoggedObjectClass | `007F3E7C` | 3b2 | `006C5EC9` / `006BD661` | 0 | PASS |
| 11 | `006C6110` | AlphaShapeClass | `007F3E94` | 3b2 | `006C6049` / `006BD69E` | 0 | PASS |

## 判读提请（供 Lead 决定，不改本报告结论）

1. **④ 口径要不要收紧成「镜像内必须存在对该 vt 槽的派发」？**
   若收紧：本批 **11 行全翻 FAIL**（direct=0、CLSID 静态无使用方），且会连带影响既往以「构造器写点」为 ④ 的全部行（含 `NAMED_PUSH_AUDIT2` 判 PASS 的 10 行）。建议**先成文再执行**，并同时给出「COM 类工厂族」的**专门口径**：这类对象的正常使用方式就是经 `CoRegisterClassObject` 注册、由 ole32 派发，要求镜像内自派发等于要求在单进程游戏里自调用 COM——本身不合理。
2. **本批的正确观察是「模板族同质」**：11 行是同一个 `TClassFactory<V>::CreateInstance` 模板的 11 个实例，函数体 114–119 字节、48–49 条指令、结构完全同形。**同质性既是执行器全过的原因，也是异族审计最容易失效的地方**——逐行复核的价值在于确认「同形」而非「同一个错被抄 11 遍」，本报告为此对每行的 ② 槽/主副表/③b 站点/④ 写点/CLSID 分别取证（地址各不相同，见上表与 `VERDICT.md`）。
3. **可机械化的两条**（建议写进下一版卡）：
   - 「失败侧 `call [reg+0x20]` + `push 1`」在本族 = 删除析构器，**不要写成 Release**；本族 AddRef/Release（slot1/slot2）= `mov eax,1; ret 4` 桩，可机械识别。
   - 主表判定可机械化：**offset 0 的 vt 且其 slot0 = `00410260`** = 主表；`+4/+8/+0xC` 三处副表 slot0 固定为 `004105E0` / `00410580` / `00410590`（调节 thunk），一律不是主表。B1 的翻车点用这一条即可拦住，无需逐个人工判断。

## 证据文件索引（可复核）

全部为本次审计自建，位于 `NAMED_PUSH_AUDIT12\work\`：

| 文件 | 内容 |
|---|---|
| `aud.py` / `rt.py` | PE 映射（ImageBase 0x400000）与 RTTI 读取（本镜像 RTTI 指针为**绝对 VA**，非 RVA——坑点已记） |
| `body_<entry>.txt` × 11 / `all_bodies.txt` | 11 个 entry 的完整反汇编（函数边界按「ret 后紧跟 nop 填充」判定，长度 114–119B / 48–49 条） |
| `check11.py` / `check11.txt` | 逐行 ②槽 / direct-caller / 数据引用扫描 |
| `derive2.py` / `derive11b.txt` | ② 槽与 RTTI、产品主表与副表、工厂构造器唯一写点、③b 站点（全部从字节派生，不硬编码） |
| `ctors.txt` | 11 个工厂构造器原文（各 4 条指令） |
| `clsid.py` / `clsid_map.txt` | 注册块 CLSID ↔ 工厂 一一映射，与 21 处 CoCreateInstance 实参求交集 |
| `com2.py` / `com2_run.txt` | 21 处 `call [0x7E15FC]` 及其前置 push（rclsid 解析） |
| `prod11.txt` / `ctor_75CEC0.txt` | 产品构造器写表细节、`[ebp]`/`[edi]` 基址确认 |
