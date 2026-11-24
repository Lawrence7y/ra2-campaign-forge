# S22_B4 11 行 异族逐行裁定

二进制 SHA-256 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（与卡面一致）。地址均为 VA（ImageBase `0x400000`），字节为镜像内实测。每行五项：② 类身份 / ② 主虚表 / ③b 形态 / ④ 使用见证 / ④②是否同源 / ⑤ 语义。

## A · `006C5210` — S22 `TClassFactory<VFactoryClass>`  →  **PASS**

| 项 | 结论 | 地址 / 字节 |
|---|---|---|
| ② 类身份 | 成立 | 槽 `007F3DA4` = `006C5210`（= 本 entry）；vt `007F3D98` +0x0C = slot#3；COL `0080B108` → TD `00841CB8` → `.?AV?$TClassFactory@VFactoryClass@@@@`；CHD `0080B0F8` numBase=3 |
| ② 主虚表 | 成立 | 体内 new(0x74) → ctor `004C98B0`，在 `004C991A` 写主表 `007E88D0`（`.?AVFactoryClass@@`，slot0=`00410260`、slot1=`00410300`、slot8 删除析构=`004CA770`） |
| ③b 形态 | **3b2** | 站点 `006C526A` `ff10` `call dword ptr [eax]`（callee = 主表 slot0 `00410260` QI）→ `006C526E` `85ff` `test edi, edi` → `006C5270` `7d09` `jge 0x6c527b`，目标 `006C527B`；失败路 `006C5278` `ff5220` `call dword ptr [edx + 0x20]`（前置 `push 1`）；入口三类错误码 `80070057`@`006C521B`、`80040110`@`006C5233`、`8007000E`@`006C5258` |
| ② 主/副表对照 | 主表唯一位于 offset 0 | 主表 `007E88D0`（slot0=`00410260`）；副表 +4 `007E88B4`@`004C9920` slot0=`004105E0`；+8 `007E88AC`@`004C9926` slot0=`00410580`；+0xC `007E88A4`@`004C992D` slot0=`00410590` ⇒ **主表判据 = offset 0 且 slot0=`00410260`**；第 4 列引的是主表 |
| ④ 使用见证 | 成立（活表安装 + COM 注册） | 工厂构造器 `006C5140`（`8bc1` / `c7 40 04 0` / `c7 00 983d7f00` / `c3`）在 `006C5149` 写活表；该表**全镜像唯一写点**；宿主 `006BB9A0` 在 `006BD43C` `call esi`（`esi`=`[0x7E15D8]`=CoRegisterClassObject @`006BC43F`）注册 `{34ECD9A8-0AB0-11D2-ACA7-006008055BB5}`，pUnk=该对象 |
| ④/② 不同源 | **no（不同源）** | ② 用 `.rdata` 槽值 `007F3DA4`；④ 用 `.text` 指令字面量写点 `006C5149` + 注册调用 `006BD43C` |
| ⑤ 语义 | 相符（1 处措辞需账） | 第 4 列所写守卫/站点/分支/返回码逐条对上；「失败 Release 新建对象」实为 vt+0x20（slot8 删除析构器，`push 1`），非 slot2 Release（`00410310`=`mov eax,1; ret 4` 桩） |

**② 细节**：`007F3D98` 只有 5 个槽（槽4 `006C5290` = LockServer），紧随其后的 `0080B158` 是**下一张表的 COL**、不是本表槽；slot0 `006C5150` 为 QI 形态（`006C5150`：先 `test` ppvOut→`0x80004003`，再逐 IID 比较）⇒ 按 IClassFactory 布局 slot3 = CreateInstance，与 entry 语义自洽。

**③b② 检查点与消费点真实性**：callee `00410260` 的返回约定可逐字节伪证——`00410269` `b803400080` = `E_POINTER 0x80004003`（`ret 0xc` 于 `0041026F`）、`004102E6` `b802400080` = `E_NOINTERFACE 0x80004002`（`ret 0xc` 于 `004102EC`）、成功路 `004102F5` `33c0` 后 `ret 0xc` 于 `004102F8`；三常量三 `ret`，与第 4 列自述一致。消费点在本函数自身：`006C526A` 返回后 `006C526C` `8bf8`(`mov edi,eax`)、`006C526E` `85ff`(`test edi,edi`)、`006C5270` `7d09`(`jge`)，test 与 jcc **零间隔、中间无 eax 覆写**；两路动作真不同：`<0` 走 `006C5278` `call [edx+0x20]`（`push 1`）销毁新对象后返回负码；`>=0` 跳至 `006C527B` 直接 `mov eax,edi` 返回 `0`。本体内 `call [eax]` 仅 1 处 ⇒ 不是「多路同一 call」伪装。

**④ 取证链（与 ② 不共用同一槽）**：`00` 唯一写点 `006C5149` 把 `007F3D98` 装进 `operator new(8)` 出的活堆对象（`006C523E` 之后），该对象在 `006BD43C` 作为 `pUnk` 交给 `CoRegisterClassObject(CLSID={34ECD9A8-0AB0-11D2-ACA7-006008055BB5}, pUnk, CLSCTX=1, REGCLS=1, &cookie)`；注册调用点 `006BD43C` 属宿主 `006BB9A0`（从 `006BB9A0` 线性反汇编 6400 条零 `.byte` 直通本块，未跨函数）。**㉓ 检查**：`007F3D98` 的字面量在全镜像只出现 1 次（`006C5149`），不存在第二个写点 ⇒ 不存在「析构器也装同一张表」的成对陷阱。

**⑤ 需账**：删除析构器 `004CA770` 自身还调 `0x7258D0` 解单例并从 `0xA83E30` 注册表摘除，第 4 列未写。

## B · `006C5390` — S22 `TClassFactory<VWarheadTypeClass>`  →  **PASS**

| 项 | 结论 | 地址 / 字节 |
|---|---|---|
| ② 类身份 | 成立 | 槽 `007F3DBC` = `006C5390`（= 本 entry）；vt `007F3DB0` +0x0C = slot#3；COL `0080B158` → TD `00841CE8` → `.?AV?$TClassFactory@VWarheadTypeClass@@@@`；CHD `0080B148` numBase=3 |
| ② 主虚表 | 成立 | 体内 new(0x1d0) → ctor `0075CEC0`，在 `0075D0BA` 写主表 `007F6B30`（`.?AVWarheadTypeClass@@`，slot0=`00410260`、slot1=`00410300`、slot8 删除析构=`0075E510`） |
| ③b 形态 | **3b2** | 站点 `006C53EF` `ff10` `call dword ptr [eax]`（callee = 主表 slot0 `00410260` QI）→ `006C53F3` `85ff` `test edi, edi` → `006C53F5` `7d09` `jge 0x6c5400`，目标 `006C5400`；失败路 `006C53FD` `ff5220` `call dword ptr [edx + 0x20]`（前置 `push 1`）；入口三类错误码 `80070057`@`006C539B`、`80040110`@`006C53B3`、`8007000E`@`006C53DD` |
| ② 主/副表对照 | 主表唯一位于 offset 0 | 主表 `007F6B30`（slot0=`00410260`）；副表 +4 `007F6B14`@`0075D0C1` slot0=`004105E0`；+8 `007F6B0C`@`0075D0C7` slot0=`00410580`；+0xC `007F6B04`@`0075D0CE` slot0=`00410590` ⇒ **主表判据 = offset 0 且 slot0=`00410260`**；第 4 列引的是主表 |
| ④ 使用见证 | 成立（活表安装 + COM 注册） | 工厂构造器 `006C52C0`（`8bc1` / `c7 40 04 0` / `c7 00 b03d7f00` / `c3`）在 `006C52C9` 写活表；该表**全镜像唯一写点**；宿主 `006BB9A0` 在 `006BD479` `call esi`（`esi`=`[0x7E15D8]`=CoRegisterClassObject @`006BC43F`）注册 `{A8C54DA4-0F7B-11D2-8172-006008055BB5}`，pUnk=该对象 |
| ④/② 不同源 | **no（不同源）** | ② 用 `.rdata` 槽值 `007F3DBC`；④ 用 `.text` 指令字面量写点 `006C52C9` + 注册调用 `006BD479` |
| ⑤ 语义 | 相符（1 处措辞需账） | 第 4 列所写守卫/站点/分支/返回码逐条对上；「失败 Release 新建对象」实为 vt+0x20（slot8 删除析构器，`push 1`），非 slot2 Release（`00410310`=`mov eax,1; ret 4` 桩） |

**② 细节**：`007F3DB0` 只有 5 个槽（槽4 `006C5410` = LockServer），紧随其后的 `0080B1A8` 是**下一张表的 COL**、不是本表槽；slot0 `006C52D0` 为 QI 形态（`006C52D0`：先 `test` ppvOut→`0x80004003`，再逐 IID 比较）⇒ 按 IClassFactory 布局 slot3 = CreateInstance，与 entry 语义自洽。

**③b② 检查点与消费点真实性**：callee `00410260` 的返回约定可逐字节伪证——`00410269` `b803400080` = `E_POINTER 0x80004003`（`ret 0xc` 于 `0041026F`）、`004102E6` `b802400080` = `E_NOINTERFACE 0x80004002`（`ret 0xc` 于 `004102EC`）、成功路 `004102F5` `33c0` 后 `ret 0xc` 于 `004102F8`；三常量三 `ret`，与第 4 列自述一致。消费点在本函数自身：`006C53EF` 返回后 `006C53F1` `8bf8`(`mov edi,eax`)、`006C53F3` `85ff`(`test edi,edi`)、`006C53F5` `7d09`(`jge`)，test 与 jcc **零间隔、中间无 eax 覆写**；两路动作真不同：`<0` 走 `006C53FD` `call [edx+0x20]`（`push 1`）销毁新对象后返回负码；`>=0` 跳至 `006C5400` 直接 `mov eax,edi` 返回 `0`。本体内 `call [eax]` 仅 1 处 ⇒ 不是「多路同一 call」伪装。

**④ 取证链（与 ② 不共用同一槽）**：`00` 唯一写点 `006C52C9` 把 `007F3DB0` 装进 `operator new(8)` 出的活堆对象（`006C53C1` 之后），该对象在 `006BD479` 作为 `pUnk` 交给 `CoRegisterClassObject(CLSID={A8C54DA4-0F7B-11D2-8172-006008055BB5}, pUnk, CLSCTX=1, REGCLS=1, &cookie)`；注册调用点 `006BD479` 属宿主 `006BB9A0`（从 `006BB9A0` 线性反汇编 6400 条零 `.byte` 直通本块，未跨函数）。**㉓ 检查**：`007F3DB0` 的字面量在全镜像只出现 1 次（`006C52C9`），不存在第二个写点 ⇒ 不存在「析构器也装同一张表」的成对陷阱。

**⑤ 需账**：`007F6B30` 是主表、`007F6B14` 才在 +4（slot0=`004105E0` 调节 thunk），第 4 列引的是主表，未踩 B1 的「小成员表当主表」。

## C · `006C5510` — S22 `TClassFactory<VWeaponTypeClass>`  →  **PASS**

| 项 | 结论 | 地址 / 字节 |
|---|---|---|
| ② 类身份 | 成立 | 槽 `007F3DD4` = `006C5510`（= 本 entry）；vt `007F3DC8` +0x0C = slot#3；COL `0080B1A8` → TD `00841D20` → `.?AV?$TClassFactory@VWeaponTypeClass@@@@`；CHD `0080B198` numBase=3 |
| ② 主虚表 | 成立 | 体内 new(0x160) → ctor `00771C70`，在 `00771E77` 写主表 `007F73B8`（`.?AVWeaponTypeClass@@`，slot0=`00410260`、slot1=`00410300`、slot8 删除析构=`007730F0`） |
| ③b 形态 | **3b2** | 站点 `006C556F` `ff10` `call dword ptr [eax]`（callee = 主表 slot0 `00410260` QI）→ `006C5573` `85ff` `test edi, edi` → `006C5575` `7d09` `jge 0x6c5580`，目标 `006C5580`；失败路 `006C557D` `ff5220` `call dword ptr [edx + 0x20]`（前置 `push 1`）；入口三类错误码 `80070057`@`006C551B`、`80040110`@`006C5533`、`8007000E`@`006C555D` |
| ② 主/副表对照 | 主表唯一位于 offset 0 | 主表 `007F73B8`（slot0=`00410260`）；副表 +4 `007F739C`@`00771E7D` slot0=`004105E0`；+8 `007F7394`@`00771E83` slot0=`00410580`；+0xC `007F738C`@`00771E8A` slot0=`00410590` ⇒ **主表判据 = offset 0 且 slot0=`00410260`**；第 4 列引的是主表 |
| ④ 使用见证 | 成立（活表安装 + COM 注册） | 工厂构造器 `006C5440`（`8bc1` / `c7 40 04 0` / `c7 00 c83d7f00` / `c3`）在 `006C5449` 写活表；该表**全镜像唯一写点**；宿主 `006BB9A0` 在 `006BD4B6` `call esi`（`esi`=`[0x7E15D8]`=CoRegisterClassObject @`006BC43F`）注册 `{9FD219CA-0F7B-11D2-8172-006008055BB5}`，pUnk=该对象 |
| ④/② 不同源 | **no（不同源）** | ② 用 `.rdata` 槽值 `007F3DD4`；④ 用 `.text` 指令字面量写点 `006C5449` + 注册调用 `006BD4B6` |
| ⑤ 语义 | 相符（1 处措辞需账） | 第 4 列所写守卫/站点/分支/返回码逐条对上；「失败 Release 新建对象」实为 vt+0x20（slot8 删除析构器，`push 1`），非 slot2 Release（`00410310`=`mov eax,1; ret 4` 桩） |

**② 细节**：`007F3DC8` 只有 5 个槽（槽4 `006C5590` = LockServer），紧随其后的 `0080B1F8` 是**下一张表的 COL**、不是本表槽；slot0 `006C5450` 为 QI 形态（`006C5450`：先 `test` ppvOut→`0x80004003`，再逐 IID 比较）⇒ 按 IClassFactory 布局 slot3 = CreateInstance，与 entry 语义自洽。

**③b② 检查点与消费点真实性**：callee `00410260` 的返回约定可逐字节伪证——`00410269` `b803400080` = `E_POINTER 0x80004003`（`ret 0xc` 于 `0041026F`）、`004102E6` `b802400080` = `E_NOINTERFACE 0x80004002`（`ret 0xc` 于 `004102EC`）、成功路 `004102F5` `33c0` 后 `ret 0xc` 于 `004102F8`；三常量三 `ret`，与第 4 列自述一致。消费点在本函数自身：`006C556F` 返回后 `006C5571` `8bf8`(`mov edi,eax`)、`006C5573` `85ff`(`test edi,edi`)、`006C5575` `7d09`(`jge`)，test 与 jcc **零间隔、中间无 eax 覆写**；两路动作真不同：`<0` 走 `006C557D` `call [edx+0x20]`（`push 1`）销毁新对象后返回负码；`>=0` 跳至 `006C5580` 直接 `mov eax,edi` 返回 `0`。本体内 `call [eax]` 仅 1 处 ⇒ 不是「多路同一 call」伪装。

**④ 取证链（与 ② 不共用同一槽）**：`00` 唯一写点 `006C5449` 把 `007F3DC8` 装进 `operator new(8)` 出的活堆对象（`006C5541` 之后），该对象在 `006BD4B6` 作为 `pUnk` 交给 `CoRegisterClassObject(CLSID={9FD219CA-0F7B-11D2-8172-006008055BB5}, pUnk, CLSCTX=1, REGCLS=1, &cookie)`；注册调用点 `006BD4B6` 属宿主 `006BB9A0`（从 `006BB9A0` 线性反汇编 6400 条零 `.byte` 直通本块，未跨函数）。**㉓ 检查**：`007F3DC8` 的字面量在全镜像只出现 1 次（`006C5449`），不存在第二个写点 ⇒ 不存在「析构器也装同一张表」的成对陷阱。

**⑤ 需账**：同类为 4 表对象（+0/+4/+8/+0xC），第 4 列「主虚表 slot0=00410260(=00410260」是自比较冗余写法，取值无误。

## D · `006C5690` — S22 `TClassFactory<VParticleClass>`  →  **PASS**

| 项 | 结论 | 地址 / 字节 |
|---|---|---|
| ② 类身份 | 成立 | 槽 `007F3DEC` = `006C5690`（= 本 entry）；vt `007F3DE0` +0x0C = slot#3；COL `0080B1F8` → TD `00841D58` → `.?AV?$TClassFactory@VParticleClass@@@@`；CHD `0080B1E8` numBase=3 |
| ② 主虚表 | 成立 | 体内 new(0x138) → ctor `0062BB20`，在 `0062BC4A` 写主表 `007EF954`（`.?AVParticleClass@@`，slot0=`00410260`、slot1=`00410300`、slot8 删除析构=`0062D9A0`） |
| ③b 形态 | **3b2** | 站点 `006C56ED` `ff10` `call dword ptr [eax]`（callee = 主表 slot0 `00410260` QI）→ `006C56F1` `85ff` `test edi, edi` → `006C56F3` `7d09` `jge 0x6c56fe`，目标 `006C56FE`；失败路 `006C56FB` `ff5220` `call dword ptr [edx + 0x20]`（前置 `push 1`）；入口三类错误码 `80070057`@`006C569B`、`80040110`@`006C56B3`、`8007000E`@`006C56DB` |
| ② 主/副表对照 | 主表唯一位于 offset 0 | 主表 `007EF954`（slot0=`00410260`）；副表 +4 `007EF938`@`0062BC50` slot0=`004105E0`；+8 `007EF930`@`0062BC57` slot0=`00410580`；+0xC `007EF928`@`0062BC5E` slot0=`00410590` ⇒ **主表判据 = offset 0 且 slot0=`00410260`**；第 4 列引的是主表 |
| ④ 使用见证 | 成立（活表安装 + COM 注册） | 工厂构造器 `006C55C0`（`8bc1` / `c7 40 04 0` / `c7 00 e03d7f00` / `c3`）在 `006C55C9` 写活表；该表**全镜像唯一写点**；宿主 `006BB9A0` 在 `006BD4F3` `call esi`（`esi`=`[0x7E15D8]`=CoRegisterClassObject @`006BC43F`）注册 `{0E272DCC-9C0F-11D1-B709-00A024DDAFD1}`，pUnk=该对象 |
| ④/② 不同源 | **no（不同源）** | ② 用 `.rdata` 槽值 `007F3DEC`；④ 用 `.text` 指令字面量写点 `006C55C9` + 注册调用 `006BD4F3` |
| ⑤ 语义 | 相符（1 处措辞需账） | 第 4 列所写守卫/站点/分支/返回码逐条对上；「失败 Release 新建对象」实为 vt+0x20（slot8 删除析构器，`push 1`），非 slot2 Release（`00410310`=`mov eax,1; ret 4` 桩） |

**② 细节**：`007F3DE0` 只有 5 个槽（槽4 `006C5710` = LockServer），紧随其后的 `0080B248` 是**下一张表的 COL**、不是本表槽；slot0 `006C55D0` 为 QI 形态（`006C55D0`：先 `test` ppvOut→`0x80004003`，再逐 IID 比较）⇒ 按 IClassFactory 布局 slot3 = CreateInstance，与 entry 语义自洽。

**③b② 检查点与消费点真实性**：callee `00410260` 的返回约定可逐字节伪证——`00410269` `b803400080` = `E_POINTER 0x80004003`（`ret 0xc` 于 `0041026F`）、`004102E6` `b802400080` = `E_NOINTERFACE 0x80004002`（`ret 0xc` 于 `004102EC`）、成功路 `004102F5` `33c0` 后 `ret 0xc` 于 `004102F8`；三常量三 `ret`，与第 4 列自述一致。消费点在本函数自身：`006C56ED` 返回后 `006C56EF` `8bf8`(`mov edi,eax`)、`006C56F1` `85ff`(`test edi,edi`)、`006C56F3` `7d09`(`jge`)，test 与 jcc **零间隔、中间无 eax 覆写**；两路动作真不同：`<0` 走 `006C56FB` `call [edx+0x20]`（`push 1`）销毁新对象后返回负码；`>=0` 跳至 `006C56FE` 直接 `mov eax,edi` 返回 `0`。本体内 `call [eax]` 仅 1 处 ⇒ 不是「多路同一 call」伪装。

**④ 取证链（与 ② 不共用同一槽）**：`00` 唯一写点 `006C55C9` 把 `007F3DE0` 装进 `operator new(8)` 出的活堆对象（`006C56C1` 之后），该对象在 `006BD4F3` 作为 `pUnk` 交给 `CoRegisterClassObject(CLSID={0E272DCC-9C0F-11D1-B709-00A024DDAFD1}, pUnk, CLSCTX=1, REGCLS=1, &cookie)`；注册调用点 `006BD4F3` 属宿主 `006BB9A0`（从 `006BB9A0` 线性反汇编 6400 条零 `.byte` 直通本块，未跨函数）。**㉓ 检查**：`007F3DE0` 的字面量在全镜像只出现 1 次（`006C55C9`），不存在第二个写点 ⇒ 不存在「析构器也装同一张表」的成对陷阱。

**⑤ 需账**：同类 4 表（+0/+4/+8/+0xC），主表写点 `0062BC4A`；第 4 列只写主表，未混入副表。

## E · `006C5810` — S22 `TClassFactory<VParticleTypeClass>`  →  **PASS**

| 项 | 结论 | 地址 / 字节 |
|---|---|---|
| ② 类身份 | 成立 | 槽 `007F3E04` = `006C5810`（= 本 entry）；vt `007F3DF8` +0x0C = slot#3；COL `0080B248` → TD `00841D88` → `.?AV?$TClassFactory@VParticleTypeClass@@@@`；CHD `0080B238` numBase=3 |
| ② 主虚表 | 成立 | 体内 new(0x318) → ctor `00644BE0`，在 `00644CF4` 写主表 `007F0188`（`.?AVParticleTypeClass@@`，slot0=`00410260`、slot1=`00410300`、slot8 删除析构=`00645950`） |
| ③b 形态 | **3b2** | 站点 `006C586F` `ff10` `call dword ptr [eax]`（callee = 主表 slot0 `00410260` QI）→ `006C5873` `85ff` `test edi, edi` → `006C5875` `7d09` `jge 0x6c5880`，目标 `006C5880`；失败路 `006C587D` `ff5220` `call dword ptr [edx + 0x20]`（前置 `push 1`）；入口三类错误码 `80070057`@`006C581B`、`80040110`@`006C5833`、`8007000E`@`006C585D` |
| ② 主/副表对照 | 主表唯一位于 offset 0 | 主表 `007F0188`（slot0=`00410260`）；副表 +4 `007F016C`@`00644CFA` slot0=`004105E0`；+8 `007F0164`@`00644D01` slot0=`00410580`；+0xC `007F015C`@`00644D08` slot0=`00410590` ⇒ **主表判据 = offset 0 且 slot0=`00410260`**；第 4 列引的是主表 |
| ④ 使用见证 | 成立（活表安装 + COM 注册） | 工厂构造器 `006C5740`（`8bc1` / `c7 40 04 0` / `c7 00 f83d7f00` / `c3`）在 `006C5749` 写活表；该表**全镜像唯一写点**；宿主 `006BB9A0` 在 `006BD530` `call esi`（`esi`=`[0x7E15D8]`=CoRegisterClassObject @`006BC43F`）注册 `{703E044B-0FB1-11D2-8172-006008055BB5}`，pUnk=该对象 |
| ④/② 不同源 | **no（不同源）** | ② 用 `.rdata` 槽值 `007F3E04`；④ 用 `.text` 指令字面量写点 `006C5749` + 注册调用 `006BD530` |
| ⑤ 语义 | 相符（1 处措辞需账） | 第 4 列所写守卫/站点/分支/返回码逐条对上；「失败 Release 新建对象」实为 vt+0x20（slot8 删除析构器，`push 1`），非 slot2 Release（`00410310`=`mov eax,1; ret 4` 桩） |

**② 细节**：`007F3DF8` 只有 5 个槽（槽4 `006C5890` = LockServer），紧随其后的 `0080B298` 是**下一张表的 COL**、不是本表槽；slot0 `006C5750` 为 QI 形态（`006C5750`：先 `test` ppvOut→`0x80004003`，再逐 IID 比较）⇒ 按 IClassFactory 布局 slot3 = CreateInstance，与 entry 语义自洽。

**③b② 检查点与消费点真实性**：callee `00410260` 的返回约定可逐字节伪证——`00410269` `b803400080` = `E_POINTER 0x80004003`（`ret 0xc` 于 `0041026F`）、`004102E6` `b802400080` = `E_NOINTERFACE 0x80004002`（`ret 0xc` 于 `004102EC`）、成功路 `004102F5` `33c0` 后 `ret 0xc` 于 `004102F8`；三常量三 `ret`，与第 4 列自述一致。消费点在本函数自身：`006C586F` 返回后 `006C5871` `8bf8`(`mov edi,eax`)、`006C5873` `85ff`(`test edi,edi`)、`006C5875` `7d09`(`jge`)，test 与 jcc **零间隔、中间无 eax 覆写**；两路动作真不同：`<0` 走 `006C587D` `call [edx+0x20]`（`push 1`）销毁新对象后返回负码；`>=0` 跳至 `006C5880` 直接 `mov eax,edi` 返回 `0`。本体内 `call [eax]` 仅 1 处 ⇒ 不是「多路同一 call」伪装。

**④ 取证链（与 ② 不共用同一槽）**：`00` 唯一写点 `006C5749` 把 `007F3DF8` 装进 `operator new(8)` 出的活堆对象（`006C5841` 之后），该对象在 `006BD530` 作为 `pUnk` 交给 `CoRegisterClassObject(CLSID={703E044B-0FB1-11D2-8172-006008055BB5}, pUnk, CLSCTX=1, REGCLS=1, &cookie)`；注册调用点 `006BD530` 属宿主 `006BB9A0`（从 `006BB9A0` 线性反汇编 6400 条零 `.byte` 直通本块，未跨函数）。**㉓ 检查**：`007F3DF8` 的字面量在全镜像只出现 1 次（`006C5749`），不存在第二个写点 ⇒ 不存在「析构器也装同一张表」的成对陷阱。

**⑤ 需账**：ctor `00644BE0` 先构造成员 `TypeList<RGBClass>`（`00644C46` 写 `007E4E58`）再写主表，第 4 列「分配构造一个对象」略去成员构造。

## F · `006C5990` — S22 `TClassFactory<VParticleSystemClass>`  →  **PASS**

| 项 | 结论 | 地址 / 字节 |
|---|---|---|
| ② 类身份 | 成立 | 槽 `007F3E1C` = `006C5990`（= 本 entry）；vt `007F3E10` +0x0C = slot#3；COL `0080B298` → TD `00841DC0` → `.?AV?$TClassFactory@VParticleSystemClass@@@@`；CHD `0080B288` numBase=3 |
| ② 主虚表 | 成立 | 体内 new(0x100) → ctor `0062DF20`，在 `0062DFA6` 写主表 `007EFB9C`（`.?AVParticleSystemClass@@`，slot0=`00410260`、slot1=`00410300`、slot8 删除析构=`00630230`） |
| ③b 形态 | **3b2** | 站点 `006C59ED` `ff10` `call dword ptr [eax]`（callee = 主表 slot0 `00410260` QI）→ `006C59F1` `85ff` `test edi, edi` → `006C59F3` `7d09` `jge 0x6c59fe`，目标 `006C59FE`；失败路 `006C59FB` `ff5220` `call dword ptr [edx + 0x20]`（前置 `push 1`）；入口三类错误码 `80070057`@`006C599B`、`80040110`@`006C59B3`、`8007000E`@`006C59DB` |
| ② 主/副表对照 | 主表唯一位于 offset 0 | 主表 `007EFB9C`（slot0=`00410260`）；副表 +4 `007EFB80`@`0062DFAC` slot0=`004105E0`；+8 `007EFB78`@`0062DFB3` slot0=`00410580`；+0xC `007EFB70`@`0062DFBA` slot0=`00410590` ⇒ **主表判据 = offset 0 且 slot0=`00410260`**；第 4 列引的是主表 |
| ④ 使用见证 | 成立（活表安装 + COM 注册） | 工厂构造器 `006C58C0`（`8bc1` / `c7 40 04 0` / `c7 00 103e7f00` / `c3`）在 `006C58C9` 写活表；该表**全镜像唯一写点**；宿主 `006BB9A0` 在 `006BD56D` `call esi`（`esi`=`[0x7E15D8]`=CoRegisterClassObject @`006BC43F`）注册 `{0E272DC8-9C0F-11D1-B709-00A024DDAFD1}`，pUnk=该对象 |
| ④/② 不同源 | **no（不同源）** | ② 用 `.rdata` 槽值 `007F3E1C`；④ 用 `.text` 指令字面量写点 `006C58C9` + 注册调用 `006BD56D` |
| ⑤ 语义 | 相符（1 处措辞需账） | 第 4 列所写守卫/站点/分支/返回码逐条对上；「失败 Release 新建对象」实为 vt+0x20（slot8 删除析构器，`push 1`），非 slot2 Release（`00410310`=`mov eax,1; ret 4` 桩） |

**② 细节**：`007F3E10` 只有 5 个槽（槽4 `006C5A10` = LockServer），紧随其后的 `0080B2E8` 是**下一张表的 COL**、不是本表槽；slot0 `006C58D0` 为 QI 形态（`006C58D0`：先 `test` ppvOut→`0x80004003`，再逐 IID 比较）⇒ 按 IClassFactory 布局 slot3 = CreateInstance，与 entry 语义自洽。

**③b② 检查点与消费点真实性**：callee `00410260` 的返回约定可逐字节伪证——`00410269` `b803400080` = `E_POINTER 0x80004003`（`ret 0xc` 于 `0041026F`）、`004102E6` `b802400080` = `E_NOINTERFACE 0x80004002`（`ret 0xc` 于 `004102EC`）、成功路 `004102F5` `33c0` 后 `ret 0xc` 于 `004102F8`；三常量三 `ret`，与第 4 列自述一致。消费点在本函数自身：`006C59ED` 返回后 `006C59EF` `8bf8`(`mov edi,eax`)、`006C59F1` `85ff`(`test edi,edi`)、`006C59F3` `7d09`(`jge`)，test 与 jcc **零间隔、中间无 eax 覆写**；两路动作真不同：`<0` 走 `006C59FB` `call [edx+0x20]`（`push 1`）销毁新对象后返回负码；`>=0` 跳至 `006C59FE` 直接 `mov eax,edi` 返回 `0`。本体内 `call [eax]` 仅 1 处 ⇒ 不是「多路同一 call」伪装。

**④ 取证链（与 ② 不共用同一槽）**：`00` 唯一写点 `006C58C9` 把 `007F3E10` 装进 `operator new(8)` 出的活堆对象（`006C59C1` 之后），该对象在 `006BD56D` 作为 `pUnk` 交给 `CoRegisterClassObject(CLSID={0E272DC8-9C0F-11D1-B709-00A024DDAFD1}, pUnk, CLSCTX=1, REGCLS=1, &cookie)`；注册调用点 `006BD56D` 属宿主 `006BB9A0`（从 `006BB9A0` 线性反汇编 6400 条零 `.byte` 直通本块，未跨函数）。**㉓ 检查**：`007F3E10` 的字面量在全镜像只出现 1 次（`006C58C9`），不存在第二个写点 ⇒ 不存在「析构器也装同一张表」的成对陷阱。

**⑤ 需账**：ctor `0062DF20` 内含 `DynamicVectorClass<ParticleClass*>` 成员（`0062DF4A` 写 `007E9D64`），主表 `007EFB9C` 后写，顺序正常。

## G · `006C5B10` — S22 `TClassFactory<VParticleSystemTypeClass>`  →  **PASS**

| 项 | 结论 | 地址 / 字节 |
|---|---|---|
| ② 类身份 | 成立 | 槽 `007F3E34` = `006C5B10`（= 本 entry）；vt `007F3E28` +0x0C = slot#3；COL `0080B2E8` → TD `00841DF8` → `.?AV?$TClassFactory@VParticleSystemTypeClass@@@@`；CHD `0080B2D8` numBase=3 |
| ② 主虚表 | 成立 | 体内 new(0x310) → ctor `006440A0`，在 `0064419C` 写主表 `007F00A8`（`.?AVParticleSystemTypeClass@@`，slot0=`00410260`、slot1=`00410300`、slot8 删除析构=`00644960`） |
| ③b 形态 | **3b2** | 站点 `006C5B6F` `ff10` `call dword ptr [eax]`（callee = 主表 slot0 `00410260` QI）→ `006C5B73` `85ff` `test edi, edi` → `006C5B75` `7d09` `jge 0x6c5b80`，目标 `006C5B80`；失败路 `006C5B7D` `ff5220` `call dword ptr [edx + 0x20]`（前置 `push 1`）；入口三类错误码 `80070057`@`006C5B1B`、`80040110`@`006C5B33`、`8007000E`@`006C5B5D` |
| ② 主/副表对照 | 主表唯一位于 offset 0 | 主表 `007F00A8`（slot0=`00410260`）；副表 +4 `007F008C`@`006441A2` slot0=`004105E0`；+8 `007F0084`@`006441A8` slot0=`00410580`；+0xC `007F007C`@`006441AF` slot0=`00410590` ⇒ **主表判据 = offset 0 且 slot0=`00410260`**；第 4 列引的是主表 |
| ④ 使用见证 | 成立（活表安装 + COM 注册） | 工厂构造器 `006C5A40`（`8bc1` / `c7 40 04 0` / `c7 00 283e7f00` / `c3`）在 `006C5A49` 写活表；该表**全镜像唯一写点**；宿主 `006BB9A0` 在 `006BD5AA` `call esi`（`esi`=`[0x7E15D8]`=CoRegisterClassObject @`006BC43F`）注册 `{703E044A-0FB1-11D2-8172-006008055BB5}`，pUnk=该对象 |
| ④/② 不同源 | **no（不同源）** | ② 用 `.rdata` 槽值 `007F3E34`；④ 用 `.text` 指令字面量写点 `006C5A49` + 注册调用 `006BD5AA` |
| ⑤ 语义 | 相符（1 处措辞需账） | 第 4 列所写守卫/站点/分支/返回码逐条对上；「失败 Release 新建对象」实为 vt+0x20（slot8 删除析构器，`push 1`），非 slot2 Release（`00410310`=`mov eax,1; ret 4` 桩） |

**② 细节**：`007F3E28` 只有 5 个槽（槽4 `006C5B90` = LockServer），紧随其后的 `0080B338` 是**下一张表的 COL**、不是本表槽；slot0 `006C5A50` 为 QI 形态（`006C5A50`：先 `test` ppvOut→`0x80004003`，再逐 IID 比较）⇒ 按 IClassFactory 布局 slot3 = CreateInstance，与 entry 语义自洽。

**③b② 检查点与消费点真实性**：callee `00410260` 的返回约定可逐字节伪证——`00410269` `b803400080` = `E_POINTER 0x80004003`（`ret 0xc` 于 `0041026F`）、`004102E6` `b802400080` = `E_NOINTERFACE 0x80004002`（`ret 0xc` 于 `004102EC`）、成功路 `004102F5` `33c0` 后 `ret 0xc` 于 `004102F8`；三常量三 `ret`，与第 4 列自述一致。消费点在本函数自身：`006C5B6F` 返回后 `006C5B71` `8bf8`(`mov edi,eax`)、`006C5B73` `85ff`(`test edi,edi`)、`006C5B75` `7d09`(`jge`)，test 与 jcc **零间隔、中间无 eax 覆写**；两路动作真不同：`<0` 走 `006C5B7D` `call [edx+0x20]`（`push 1`）销毁新对象后返回负码；`>=0` 跳至 `006C5B80` 直接 `mov eax,edi` 返回 `0`。本体内 `call [eax]` 仅 1 处 ⇒ 不是「多路同一 call」伪装。

**④ 取证链（与 ② 不共用同一槽）**：`00` 唯一写点 `006C5A49` 把 `007F3E28` 装进 `operator new(8)` 出的活堆对象（`006C5B41` 之后），该对象在 `006BD5AA` 作为 `pUnk` 交给 `CoRegisterClassObject(CLSID={703E044A-0FB1-11D2-8172-006008055BB5}, pUnk, CLSCTX=1, REGCLS=1, &cookie)`；注册调用点 `006BD5AA` 属宿主 `006BB9A0`（从 `006BB9A0` 线性反汇编 6400 条零 `.byte` 直通本块，未跨函数）。**㉓ 检查**：`007F3E28` 的字面量在全镜像只出现 1 次（`006C5A49`），不存在第二个写点 ⇒ 不存在「析构器也装同一张表」的成对陷阱。

**⑤ 需账**：与 006C5690 同为 0E272D 段，但注册 CLSID 不同（{703E044A} vs {0E272DCC}），第 4 列未混淆。

## H · `006C5C90` — S22 `TClassFactory<VAITriggerTypeClass>`  →  **PASS**

| 项 | 结论 | 地址 / 字节 |
|---|---|---|
| ② 类身份 | 成立 | 槽 `007F3E4C` = `006C5C90`（= 本 entry）；vt `007F3E40` +0x0C = slot#3；COL `0080B338` → TD `00841E38` → `.?AV?$TClassFactory@VAITriggerTypeClass@@@@`；CHD `0080B328` numBase=3 |
| ② 主虚表 | 成立 | 体内 new(0x110) → ctor `0041E350`，在 `0041E401` 写主表 `007E2A50`（`.?AVAITriggerTypeClass@@`，slot0=`00410260`、slot1=`00410300`、slot8 删除析构=`0041FFF0`） |
| ③b 形态 | **3b2** | 站点 `006C5CEF` `ff10` `call dword ptr [eax]`（callee = 主表 slot0 `00410260` QI）→ `006C5CF3` `85ff` `test edi, edi` → `006C5CF5` `7d09` `jge 0x6c5d00`，目标 `006C5D00`；失败路 `006C5CFD` `ff5220` `call dword ptr [edx + 0x20]`（前置 `push 1`）；入口三类错误码 `80070057`@`006C5C9B`、`80040110`@`006C5CB3`、`8007000E`@`006C5CDD` |
| ② 主/副表对照 | 主表唯一位于 offset 0 | 主表 `007E2A50`（slot0=`00410260`）；副表 +4 `007E2A34`@`0041E407` slot0=`004105E0`；+8 `007E2A2C`@`0041E40E` slot0=`00410580`；+0xC `007E2A24`@`0041E415` slot0=`00410590` ⇒ **主表判据 = offset 0 且 slot0=`00410260`**；第 4 列引的是主表 |
| ④ 使用见证 | 成立（活表安装 + COM 注册） | 工厂构造器 `006C5BC0`（`8bc1` / `c7 40 04 0` / `c7 00 403e7f00` / `c3`）在 `006C5BC9` 写活表；该表**全镜像唯一写点**；宿主 `006BB9A0` 在 `006BD5E7` `call esi`（`esi`=`[0x7E15D8]`=CoRegisterClassObject @`006BC43F`）注册 `{BA093524-4CF4-11D2-BC26-00104B8FB04D}`，pUnk=该对象 |
| ④/② 不同源 | **no（不同源）** | ② 用 `.rdata` 槽值 `007F3E4C`；④ 用 `.text` 指令字面量写点 `006C5BC9` + 注册调用 `006BD5E7` |
| ⑤ 语义 | 相符（1 处措辞需账） | 第 4 列所写守卫/站点/分支/返回码逐条对上；「失败 Release 新建对象」实为 vt+0x20（slot8 删除析构器，`push 1`），非 slot2 Release（`00410310`=`mov eax,1; ret 4` 桩） |

**② 细节**：`007F3E40` 只有 5 个槽（槽4 `006C5D10` = LockServer），紧随其后的 `0080B388` 是**下一张表的 COL**、不是本表槽；slot0 `006C5BD0` 为 QI 形态（`006C5BD0`：先 `test` ppvOut→`0x80004003`，再逐 IID 比较）⇒ 按 IClassFactory 布局 slot3 = CreateInstance，与 entry 语义自洽。

**③b② 检查点与消费点真实性**：callee `00410260` 的返回约定可逐字节伪证——`00410269` `b803400080` = `E_POINTER 0x80004003`（`ret 0xc` 于 `0041026F`）、`004102E6` `b802400080` = `E_NOINTERFACE 0x80004002`（`ret 0xc` 于 `004102EC`）、成功路 `004102F5` `33c0` 后 `ret 0xc` 于 `004102F8`；三常量三 `ret`，与第 4 列自述一致。消费点在本函数自身：`006C5CEF` 返回后 `006C5CF1` `8bf8`(`mov edi,eax`)、`006C5CF3` `85ff`(`test edi,edi`)、`006C5CF5` `7d09`(`jge`)，test 与 jcc **零间隔、中间无 eax 覆写**；两路动作真不同：`<0` 走 `006C5CFD` `call [edx+0x20]`（`push 1`）销毁新对象后返回负码；`>=0` 跳至 `006C5D00` 直接 `mov eax,edi` 返回 `0`。本体内 `call [eax]` 仅 1 处 ⇒ 不是「多路同一 call」伪装。

**④ 取证链（与 ② 不共用同一槽）**：`00` 唯一写点 `006C5BC9` 把 `007F3E40` 装进 `operator new(8)` 出的活堆对象（`006C5CC1` 之后），该对象在 `006BD5E7` 作为 `pUnk` 交给 `CoRegisterClassObject(CLSID={BA093524-4CF4-11D2-BC26-00104B8FB04D}, pUnk, CLSCTX=1, REGCLS=1, &cookie)`；注册调用点 `006BD5E7` 属宿主 `006BB9A0`（从 `006BB9A0` 线性反汇编 6400 条零 `.byte` 直通本块，未跨函数）。**㉓ 检查**：`007F3E40` 的字面量在全镜像只出现 1 次（`006C5BC9`），不存在第二个写点 ⇒ 不存在「析构器也装同一张表」的成对陷阱。

**⑤ 需账**：工厂表 slot4=`006C5D10`（LockServer）与 slot3 相邻，第 4 列未把 slot4 当 CreateInstance。

## I · `006C5E10` — S22 `TClassFactory<VNeuronClass>`  →  **PASS**

| 项 | 结论 | 地址 / 字节 |
|---|---|---|
| ② 类身份 | 成立 | 槽 `007F3E64` = `006C5E10`（= 本 entry）；vt `007F3E58` +0x0C = slot#3；COL `0080B388` → TD `00841E70` → `.?AV?$TClassFactory@VNeuronClass@@@@`；CHD `0080B378` numBase=3 |
| ② 主虚表 | 成立 | 体内 new(0x38) → ctor `0043A350`，在 `0043A375` 写主表 `007E3DF0`（`.?AVNeuronClass@@`，slot0=`00410260`、slot1=`00410300`、slot8 删除析构=`0043A9C0`） |
| ③b 形态 | **3b2** | 站点 `006C5E6A` `ff10` `call dword ptr [eax]`（callee = 主表 slot0 `00410260` QI）→ `006C5E6E` `85ff` `test edi, edi` → `006C5E70` `7d09` `jge 0x6c5e7b`，目标 `006C5E7B`；失败路 `006C5E78` `ff5220` `call dword ptr [edx + 0x20]`（前置 `push 1`）；入口三类错误码 `80070057`@`006C5E1B`、`80040110`@`006C5E33`、`8007000E`@`006C5E58` |
| ② 主/副表对照 | 主表唯一位于 offset 0 | 主表 `007E3DF0`（slot0=`00410260`）；副表 +4 `007E3DD4`@`0043A37B` slot0=`004105E0`；+8 `007E3DCC`@`0043A382` slot0=`00410580`；+0xC `007E3DC4`@`0043A389` slot0=`00410590` ⇒ **主表判据 = offset 0 且 slot0=`00410260`**；第 4 列引的是主表 |
| ④ 使用见证 | 成立（活表安装 + COM 注册） | 工厂构造器 `006C5D40`（`8bc1` / `c7 40 04 0` / `c7 00 583e7f00` / `c3`）在 `006C5D49` 写活表；该表**全镜像唯一写点**；宿主 `006BB9A0` 在 `006BD624` `call esi`（`esi`=`[0x7E15D8]`=CoRegisterClassObject @`006BC43F`）注册 `{241AB316-4CF5-11D2-BC26-00104B8FB04D}`，pUnk=该对象 |
| ④/② 不同源 | **no（不同源）** | ② 用 `.rdata` 槽值 `007F3E64`；④ 用 `.text` 指令字面量写点 `006C5D49` + 注册调用 `006BD624` |
| ⑤ 语义 | 相符（1 处措辞需账） | 第 4 列所写守卫/站点/分支/返回码逐条对上；「失败 Release 新建对象」实为 vt+0x20（slot8 删除析构器，`push 1`），非 slot2 Release（`00410310`=`mov eax,1; ret 4` 桩） |

**② 细节**：`007F3E58` 只有 5 个槽（槽4 `006C5E90` = LockServer），紧随其后的 `0080B3D8` 是**下一张表的 COL**、不是本表槽；slot0 `006C5D50` 为 QI 形态（`006C5D50`：先 `test` ppvOut→`0x80004003`，再逐 IID 比较）⇒ 按 IClassFactory 布局 slot3 = CreateInstance，与 entry 语义自洽。

**③b② 检查点与消费点真实性**：callee `00410260` 的返回约定可逐字节伪证——`00410269` `b803400080` = `E_POINTER 0x80004003`（`ret 0xc` 于 `0041026F`）、`004102E6` `b802400080` = `E_NOINTERFACE 0x80004002`（`ret 0xc` 于 `004102EC`）、成功路 `004102F5` `33c0` 后 `ret 0xc` 于 `004102F8`；三常量三 `ret`，与第 4 列自述一致。消费点在本函数自身：`006C5E6A` 返回后 `006C5E6C` `8bf8`(`mov edi,eax`)、`006C5E6E` `85ff`(`test edi,edi`)、`006C5E70` `7d09`(`jge`)，test 与 jcc **零间隔、中间无 eax 覆写**；两路动作真不同：`<0` 走 `006C5E78` `call [edx+0x20]`（`push 1`）销毁新对象后返回负码；`>=0` 跳至 `006C5E7B` 直接 `mov eax,edi` 返回 `0`。本体内 `call [eax]` 仅 1 处 ⇒ 不是「多路同一 call」伪装。

**④ 取证链（与 ② 不共用同一槽）**：`00` 唯一写点 `006C5D49` 把 `007F3E58` 装进 `operator new(8)` 出的活堆对象（`006C5E3E` 之后），该对象在 `006BD624` 作为 `pUnk` 交给 `CoRegisterClassObject(CLSID={241AB316-4CF5-11D2-BC26-00104B8FB04D}, pUnk, CLSCTX=1, REGCLS=1, &cookie)`；注册调用点 `006BD624` 属宿主 `006BB9A0`（从 `006BB9A0` 线性反汇编 6400 条零 `.byte` 直通本块，未跨函数）。**㉓ 检查**：`007F3E58` 的字面量在全镜像只出现 1 次（`006C5D49`），不存在第二个写点 ⇒ 不存在「析构器也装同一张表」的成对陷阱。

**⑤ 需账**：NeuronClass 实为 4 表对象（写点 `0043A375`–`0043A389`），非「单表小类」；第 4 列只引主表，无冲突。

## J · `006C5F90` — S22 `TClassFactory<VFoggedObjectClass>`  →  **PASS**

| 项 | 结论 | 地址 / 字节 |
|---|---|---|
| ② 类身份 | 成立 | 槽 `007F3E7C` = `006C5F90`（= 本 entry）；vt `007F3E70` +0x0C = slot#3；COL `0080B3D8` → TD `00841EA0` → `.?AV?$TClassFactory@VFoggedObjectClass@@@@`；CHD `0080B3C8` numBase=3 |
| ② 主虚表 | 成立 | 体内 new(0x78) → ctor `004D08B0`，在 `004D0909` 写主表 `007E8B38`（`.?AVFoggedObjectClass@@`，slot0=`00410260`、slot1=`00410300`、slot8 删除析构=`004D2910`） |
| ③b 形态 | **3b2** | 站点 `006C5FEA` `ff10` `call dword ptr [eax]`（callee = 主表 slot0 `00410260` QI）→ `006C5FEE` `85ff` `test edi, edi` → `006C5FF0` `7d09` `jge 0x6c5ffb`，目标 `006C5FFB`；失败路 `006C5FF8` `ff5220` `call dword ptr [edx + 0x20]`（前置 `push 1`）；入口三类错误码 `80070057`@`006C5F9B`、`80040110`@`006C5FB3`、`8007000E`@`006C5FD8` |
| ② 主/副表对照 | 主表唯一位于 offset 0 | 主表 `007E8B38`（slot0=`00410260`）；副表 +4 `007E8B1C`@`004D090F` slot0=`004105E0`；+8 `007E8B14`@`004D0916` slot0=`00410580`；+0xC `007E8B0C`@`004D091D` slot0=`00410590` ⇒ **主表判据 = offset 0 且 slot0=`00410260`**；第 4 列引的是主表 |
| ④ 使用见证 | 成立（活表安装 + COM 注册） | 工厂构造器 `006C5EC0`（`8bc1` / `c7 40 04 0` / `c7 00 703e7f00` / `c3`）在 `006C5EC9` 写活表；该表**全镜像唯一写点**；宿主 `006BB9A0` 在 `006BD661` `call esi`（`esi`=`[0x7E15D8]`=CoRegisterClassObject @`006BC43F`）注册 `{1C470B0E-69D7-11D2-B8F2-006008C809ED}`，pUnk=该对象 |
| ④/② 不同源 | **no（不同源）** | ② 用 `.rdata` 槽值 `007F3E7C`；④ 用 `.text` 指令字面量写点 `006C5EC9` + 注册调用 `006BD661` |
| ⑤ 语义 | 相符（1 处措辞需账） | 第 4 列所写守卫/站点/分支/返回码逐条对上；「失败 Release 新建对象」实为 vt+0x20（slot8 删除析构器，`push 1`），非 slot2 Release（`00410310`=`mov eax,1; ret 4` 桩） |

**② 细节**：`007F3E70` 只有 5 个槽（槽4 `006C6010` = LockServer），紧随其后的 `0080B428` 是**下一张表的 COL**、不是本表槽；slot0 `006C5ED0` 为 QI 形态（`006C5ED0`：先 `test` ppvOut→`0x80004003`，再逐 IID 比较）⇒ 按 IClassFactory 布局 slot3 = CreateInstance，与 entry 语义自洽。

**③b② 检查点与消费点真实性**：callee `00410260` 的返回约定可逐字节伪证——`00410269` `b803400080` = `E_POINTER 0x80004003`（`ret 0xc` 于 `0041026F`）、`004102E6` `b802400080` = `E_NOINTERFACE 0x80004002`（`ret 0xc` 于 `004102EC`）、成功路 `004102F5` `33c0` 后 `ret 0xc` 于 `004102F8`；三常量三 `ret`，与第 4 列自述一致。消费点在本函数自身：`006C5FEA` 返回后 `006C5FEC` `8bf8`(`mov edi,eax`)、`006C5FEE` `85ff`(`test edi,edi`)、`006C5FF0` `7d09`(`jge`)，test 与 jcc **零间隔、中间无 eax 覆写**；两路动作真不同：`<0` 走 `006C5FF8` `call [edx+0x20]`（`push 1`）销毁新对象后返回负码；`>=0` 跳至 `006C5FFB` 直接 `mov eax,edi` 返回 `0`。本体内 `call [eax]` 仅 1 处 ⇒ 不是「多路同一 call」伪装。

**④ 取证链（与 ② 不共用同一槽）**：`00` 唯一写点 `006C5EC9` 把 `007F3E70` 装进 `operator new(8)` 出的活堆对象（`006C5FBE` 之后），该对象在 `006BD661` 作为 `pUnk` 交给 `CoRegisterClassObject(CLSID={1C470B0E-69D7-11D2-B8F2-006008C809ED}, pUnk, CLSCTX=1, REGCLS=1, &cookie)`；注册调用点 `006BD661` 属宿主 `006BB9A0`（从 `006BB9A0` 线性反汇编 6400 条零 `.byte` 直通本块，未跨函数）。**㉓ 检查**：`007F3E70` 的字面量在全镜像只出现 1 次（`006C5EC9`），不存在第二个写点 ⇒ 不存在「析构器也装同一张表」的成对陷阱。

**⑤ 需账**：工厂 CLSID {1C470B0E} 与 AlphaShape {623C7584} 在全镜像各仅 2 处引用（注册块 + 本类 GetClassID）。

## K · `006C6110` — S22 `TClassFactory<VAlphaShapeClass>`  →  **PASS**

| 项 | 结论 | 地址 / 字节 |
|---|---|---|
| ② 类身份 | 成立 | 槽 `007F3E94` = `006C6110`（= 本 entry）；vt `007F3E88` +0x0C = slot#3；COL `0080B428` → TD `00841ED8` → `.?AV?$TClassFactory@VAlphaShapeClass@@@@`；CHD `0080B418` numBase=3 |
| ② 主虚表 | 成立 | 体内 new(0x40) → ctor `00420AF0`，在 `00420B10` 写主表 `007E32A4`（`.?AVAlphaShapeClass@@`，slot0=`00410260`、slot1=`00410300`、slot8 删除析构=`00421730`） |
| ③b 形态 | **3b2** | 站点 `006C616A` `ff10` `call dword ptr [eax]`（callee = 主表 slot0 `00410260` QI）→ `006C616E` `85ff` `test edi, edi` → `006C6170` `7d09` `jge 0x6c617b`，目标 `006C617B`；失败路 `006C6178` `ff5220` `call dword ptr [edx + 0x20]`（前置 `push 1`）；入口三类错误码 `80070057`@`006C611B`、`80040110`@`006C6133`、`8007000E`@`006C6158` |
| ② 主/副表对照 | 主表唯一位于 offset 0 | 主表 `007E32A4`（slot0=`00410260`）；副表 +4 `007E3288`@`00420B16` slot0=`004105E0`；+8 `007E3280`@`00420B1D` slot0=`00410580`；+0xC `007E3278`@`00420B24` slot0=`00410590` ⇒ **主表判据 = offset 0 且 slot0=`00410260`**；第 4 列引的是主表 |
| ④ 使用见证 | 成立（活表安装 + COM 注册） | 工厂构造器 `006C6040`（`8bc1` / `c7 40 04 0` / `c7 00 883e7f00` / `c3`）在 `006C6049` 写活表；该表**全镜像唯一写点**；宿主 `006BB9A0` 在 `006BD69E` `call esi`（`esi`=`[0x7E15D8]`=CoRegisterClassObject @`006BC43F`）注册 `{623C7584-74E7-11D2-B8F5-006008C809ED}`，pUnk=该对象 |
| ④/② 不同源 | **no（不同源）** | ② 用 `.rdata` 槽值 `007F3E94`；④ 用 `.text` 指令字面量写点 `006C6049` + 注册调用 `006BD69E` |
| ⑤ 语义 | 相符（1 处措辞需账） | 第 4 列所写守卫/站点/分支/返回码逐条对上；「失败 Release 新建对象」实为 vt+0x20（slot8 删除析构器，`push 1`），非 slot2 Release（`00410310`=`mov eax,1; ret 4` 桩） |

**② 细节**：`007F3E88` 只有 5 个槽（槽4 `006C6190` = LockServer），紧随其后的 `0080B478` 是**下一张表的 COL**、不是本表槽；slot0 `006C6050` 为 QI 形态（`006C6050`：先 `test` ppvOut→`0x80004003`，再逐 IID 比较）⇒ 按 IClassFactory 布局 slot3 = CreateInstance，与 entry 语义自洽。

**③b② 检查点与消费点真实性**：callee `00410260` 的返回约定可逐字节伪证——`00410269` `b803400080` = `E_POINTER 0x80004003`（`ret 0xc` 于 `0041026F`）、`004102E6` `b802400080` = `E_NOINTERFACE 0x80004002`（`ret 0xc` 于 `004102EC`）、成功路 `004102F5` `33c0` 后 `ret 0xc` 于 `004102F8`；三常量三 `ret`，与第 4 列自述一致。消费点在本函数自身：`006C616A` 返回后 `006C616C` `8bf8`(`mov edi,eax`)、`006C616E` `85ff`(`test edi,edi`)、`006C6170` `7d09`(`jge`)，test 与 jcc **零间隔、中间无 eax 覆写**；两路动作真不同：`<0` 走 `006C6178` `call [edx+0x20]`（`push 1`）销毁新对象后返回负码；`>=0` 跳至 `006C617B` 直接 `mov eax,edi` 返回 `0`。本体内 `call [eax]` 仅 1 处 ⇒ 不是「多路同一 call」伪装。

**④ 取证链（与 ② 不共用同一槽）**：`00` 唯一写点 `006C6049` 把 `007F3E88` 装进 `operator new(8)` 出的活堆对象（`006C613E` 之后），该对象在 `006BD69E` 作为 `pUnk` 交给 `CoRegisterClassObject(CLSID={623C7584-74E7-11D2-B8F5-006008C809ED}, pUnk, CLSCTX=1, REGCLS=1, &cookie)`；注册调用点 `006BD69E` 属宿主 `006BB9A0`（从 `006BB9A0` 线性反汇编 6400 条零 `.byte` 直通本块，未跨函数）。**㉓ 检查**：`007F3E88` 的字面量在全镜像只出现 1 次（`006C6049`），不存在第二个写点 ⇒ 不存在「析构器也装同一张表」的成对陷阱。

**⑤ 需账**：主表写在 `[edi]`（`mov edi,ecx`@`00420AF2`），非 `[esi]`，第 4 列未点名寄存器故无冲突。

