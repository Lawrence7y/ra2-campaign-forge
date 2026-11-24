# VERDICT — NAMED_PUSH_AUDIT17（异族独立审计，agent-233）

## 0 · 审计身份与口径

- 身份：**异族独立审计员**。被审批次由执行器 **Hy4** 产出（S18_B5 9 行 + S17_B1 3 行，共 **12 行**）；本审计员不是 Hy4。
- 二进制：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`
  实测 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ✅（与卡面期望一致）
- 工具：Python 3.12.10（无 venv、未 pip install）、capstone **5.0.7**（`skipdata=True`）、pefile **2024.8.26**
- 扫描规模：`.text = [0x401000, 0x7E038D)`；线性反汇编 **1,392,592** 条指令，**覆盖率 100.00%**（㉖ 口径自洽）
- 只采信自写脚本从字节读出的结果；**未**引用执行器任何 `EVIDENCE/ROW_*.txt` 作证据；未修改 `coverage.tsv` / `PANEL.md` / `R14_COMMON.md` / 台账 / `NAMED_PUSH_*` 下任何文件。
- 技术前提（已在实现中落实）：`pTD` / `pCHD` 存**绝对 VA**（非 RVA）；装饰名在 **TD+8 内联**（不是指针）。

### 取数方法（12 行如何来）

两个 `delta.tsv` 的第 1 列 `entry` + 第 2 列 `subsystem` 全量读出，行数自核：
`NAMED_PUSH_S18_B5` = 9 行（007B13D0 / 007B1BC0 / 007B2630 / 007B26D0 / 007B30B0 / 007B31E0 / 007B3450 / 007B3890 / 007B3AA0，全 S18）、
`NAMED_PUSH_S17_B1` = 3 行（004A2CD0 / 006BEF10 / 006BF690，全 S17），合计 **12**，未增删。

### 本批三道陷阱的处置

| 陷阱 | 处置 | 结果 |
|---|---|---|
| 读写方向写反 | 把执行器点名的每个 API 调用经 **IAT 独立解析**成真实导入名（WSOCK32），再核该函数的参数方向 | 12/12 无反向（见 §3 API 汇总） |
| ④ 锚点落在析构器（㉓） | 对**每张持有虚表**枚举**全部** 写点，逐个判构造器/析构器/**标量删除析构器**，并扫 atexit 注册集合 | 12/12 锚在构造器；析构写点全部排除（见 §4） |
| 小成员表 vtable 不是主虚表 | 按 TD 归组枚举**每个 TD 的全部 COL→虚表**，并核对 slot0 是否为 QueryInterface | 无一行拿小表顶主表（CStreamClass 的两张表已分辨，见 §4） |


## 1 · 逐行裁决（12 行）

| entry | subsystem | name | verdict | ③b 形态 | same_source |
|---|---|---|---|---|---|
| `004A2CD0` | S17 | `CStreamClass::slot4` | **PASS** | 3b2 | no |
| `006BEF10` | S17 | `TClassFactory<VCStreamClass>::slot3` | **PASS** | 3b2 | no |
| `006BF690` | S17 | `TClassFactory<SuperClass>::slot3` | **PASS** | 3b2 | no |
| `007B13D0` | S18 | `IPXInterfaceClass::slot16` | **PASS** | 3b2 | no |
| `007B1BC0` | S18 | `IPXInterfaceClass::slot7` | **PASS** | 3b2 | no |
| `007B2630` | S18 | `IPXInterfaceClass::slot10` | **PASS** | 3b2 | no |
| `007B26D0` | S18 | `IPXInterfaceClass::slot17` | **PASS** | 3b2 | no |
| `007B30B0` | S18 | `UDPInterfaceClass::slot23` | **PASS** | 3b2 | no |
| `007B31E0` | S18 | `UDPInterfaceClass::slot26` | **PASS** | 3b2 | no |
| `007B3450` | S18 | `UDPInterfaceClass::slot15` | **PASS** | 3b2 | no |
| `007B3890` | S18 | `UDPInterfaceClass::slot7` | **PASS** | 3b2 | no |
| `007B3AA0` | S18 | `UDPInterfaceClass::slot16` | **PASS** | 3b2 | no |

## 2 · 逐行一节（五项结论 + 地址字节）

### 2.1 `004A2CD0` — CStreamClass::slot4（S17）→ **PASS**

**① ② 类身份（全表枚举；独立成立）**

```
  vt=007E5DAC slot4 (+0x10) @007E5DBC ; COL=007FF9B8 TD=0081FC30 .?AVCStreamClass@@
```
entry 在整镜像中作为 dword 只出现 1 次：007E5DBC (.rdata) ⇒ 唯一持有表 base=007E5DAC
      主/次表核：同 TD 0081FC30 有 **2 张**表 —— 007E5DAC(15 槽，slot0=004A2990=QueryInterface) 与
      007E5D94(5 槽：0:004A3220 1:004A3230 2:004A3240 3:004A2A20 4:004A2AB0)。本 entry **只在 007E5DAC**，
      不在那张 5 槽小表里 ⇒ 「小成员表顶替主表」不成立。
      004A2990 实测即 QI：004A2999 b8 03400080(E_POINTER) / 004A2A02 b8 02400080(E_NOINTERFACE) /
      004A2A11 33c0(S_OK)，其间以 f3a7(repe cmpsd,ecx=4) 比 16 字节 IID(0x7F7C90/0x7F7CF0)。

**② ③b 具体形态：3b2（可伪证返回约定）**

```
③b② 多值状态码 HRESULT（非 bool）
      被调 004A3020（直接调用，目标钉死）：
        004A2D8D  e8 8e020000   call 0x4A3020
        004A2DB1  e8 6a020000   call 0x4A3020
      调用方真分支：
        004A2D92  85 c0         test eax,eax
        004A2D94  7c 61         jl   0x4A2DF7
        004A2DB6  85 c0         test eax,eax
        004A2DB8  7c 3d         jl   0x4A2DF7
      被调返回域：004A3089 b8 05400080 (E_FAIL) / 004A30CD 25 05400080 (neg+sbb 后 E_FAIL 或 0) /
        004A307F 7c51 与 004A30BB jl 0x4A30D2 把内层 IStream::Read 的负 HRESULT 原样透传 / 004A30D5 c20800 ret 8 不清 eax
      ⇒ 返回值域 {0(S_OK), 0x80004005(E_FAIL), 任意负 HRESULT} —— **多值状态码**
      两路动作不同：失败 jl→004A2DF7 收尾、eax 保持负码原样返回；成功 004A2D96 清 [esi+0x14] 续填，
        块末 004A2DF5 33c0 xor eax,eax → 返回 0
      无 eax 覆写：004A2D8D→004A2D92、004A2DB1→004A2DB6 之间均无写 eax 指令
```

**③ ④ 使用见证（独立成立；direct-only 不足）**

```
  ctor 004A2820 @004A285E mov [esi],0x7e5dac
```
④ 活虚表安装点（direct-only 不足 ⇒ 本行直调 0 条，全 .text E8/E9 目标扫 0 命中）
      枚举 vt 007E5DAC 全部写点（整镜像 dword 出现 3 次，全 .text）：
        004A285E  c706 ac5d7e00  mov dword ptr [esi],0x7e5dac   ← 采用
        004A2889  c706 ac5d7e00  mov dword ptr [esi],0x7e5dac
        004A3119  c706 ac5d7e00  mov dword ptr [esi],0x7e5dac
      ㉓ 构造/析构逐个判定：
        004A285E 所在 004A2820：push esi; mov esi,ecx; 初化 +8/+0xC/+0x10/+0x11/+0x14；
          三次 push 0x10000 + call 0x7C8E17(operator new) 填 +0x18/+0x1C/+0x20；再装 vt；mov eax,esi; ret
          ⇒ **构造器**（体内 free 0 次）。直接调用者 006BEF4C call 0x4A2820（TClassFactory<VCStreamClass> 构造点）
        004A2889 所在 004A2880：装 vt 后经 0x4A3020 收尾并释放缓冲 ⇒ **析构器**（排除）
        004A3119 所在 004A3110：本表 **slot14 == 004A3110** ⇒ **删除析构器**（排除）
      atexit 排除：全 .text `push imm32; call 0x7C978A` 注册点 152 个，
        004A2820 / 004A2880 / 004A3110 三者均不在注册集合；CStreamClass 非全局静态对象

**④ ④ 与 ② 不同源 → `same_source = no`**


**⑤ 语义与实测一致**

```
逐项核执行器所报数值，全中：004A2D8D ✓ 004A2DB1 ✓ 004A2D92 ✓ 004A2D94 ✓ 004A2DB6 ✓ 004A2DB8 ✓
      004A3089 ✓ 004A30CD ✓ 004A2DF5 ✓ COL 007FF9B8 ✓ TD 0081FC30 ✓ 安装点 004A285E ✓ 排除 004A2880 ✓ 004A3110 ✓
      第 4 列未主张读/写方向，无可反之处。
      附加实测（不入结论）：004A2D61/004A2DDC call 0x7CA090 以 dst=[esi+0x18]+[esi+0x14]、src=ebp 做 memcpy
      ⇒ 数据流「调用方 → 本对象缓冲」，随后 0x4A3020 经 call [edx+0x10] 写出，方向为「写」，与 slot4 名不冲突。
```

---

### 2.2 `006BEF10` — TClassFactory<VCStreamClass>::slot3（S17）→ **PASS**

**① ② 类身份（全表枚举；独立成立）**

```
  vt=007F3768 slot3 (+0xC) @007F3774 ; COL=00809C68 TD=00840F68 .?AV?$TClassFactory@VCStreamClass@@@@
```
entry 作为 dword 只出现 1 次：007F3774 (.rdata) ⇒ 唯一持有表 base=007F3768
      表 5 槽：0:006BEE50 1:006BEEC0 2:006BEEE0 3:006BEF10 4:006BEF90
      按 TD 归组：TD 00840F68 只对应 **1 个 COL**(00809C68) ⇒ 该类仅此一张表，5 槽即全部虚函数
        ⇒ 「小成员表顶替主表」不成立
      slot0=006BEE50 实测为 QI：006BEE55 test eax,eax / 006BEE59 b8 03400080(E_POINTER)

**② ③b 具体形态：3b2（可伪证返回约定）**

```
③b② 多值状态码 HRESULT（非 bool）
      被调钉死链：006BEF3C push 0x2c; 006BEF3E call 0x7C8E17(operator new); 006BEF4A mov ecx,eax;
        006BEF4C e8 cf38deff call 0x4A2820（CStreamClass 构造器，见 ROW_004A2CD0，其 004A285E 装活表 007E5DAC）
        ⇒ [esi]=007E5DAC ⇒ 006BEF6A ff10 call dword ptr [eax] = 007E5DAC **slot0 = 004A2990 (QueryInterface)**
      调用方真分支：
        006BEF6C 8bf8  mov edi,eax
        006BEF6E 85ff  test edi,edi
        006BEF70 7d09  jge 0x6bef7b
        006BEF72 8b16  mov edx,[esi]
        006BEF78 ff5238 call dword ptr [edx+0x38]   ← CStreamClass slot14=004A3110（0x38/4=14 ✓ 与表实测自洽）
        006BEF7B 8bc7  mov eax,edi  → ret 0x10
      被调 004A2990 返回域：004A2999 b8 03400080(E_POINTER) / 004A2A02 b8 02400080(E_NOINTERFACE) / 004A2A11 33c0(S_OK)
      ⇒ {0x80004003, 0x80004002, 0} 多值状态码，非 {0,1} 布尔
      两路动作不同：成功保留对象直接返回；失败先 Release 释放再返回负码
      无 eax 覆写（结果经 edi 保存，006BEF7B mov eax,edi 还原）
      入口 operator new 空判断（006BEF46 test eax,eax + 006BEF48 je → 0x8007000E）属 ③a，不计入
```

**③ ④ 使用见证（独立成立；direct-only 不足）**

```
  ctor 006BEE40 @006BEE49 mov [eax],0x7f3768
```
④ 活虚表安装点（全 .text 扫 E8/E9 目标 == 006BEF10：0 条直调）
      枚举 vt 007F3768 全部写点：整镜像 dword 出现 **1 次**
        006BEE49  c700 68377f00  mov dword ptr [eax],0x7f3768   ← 采用
      所在函数 006BEE40 全 body：8bc1 mov eax,ecx / c74004 00000000 mov [eax+4],0 /
        c700 68377f00 装 vt / c3 ret  ⇒ **构造器**，无 free、无 push dtor
      实调用上下文（证非死表）：唯一调用者 006BC468 call 0x6bee40，其前序
        006BC458 push 8 / 006BC45A call 0x7C8E17(operator new) / 006BC462 test eax,eax / 006BC466 mov ecx,eax
        ⇒ 堆分配后立刻构造，随后 006BC477.. 把该对象作参数压栈（CoCreate 风格注册）
      atexit 排除：006BEE40 / 006BEE50 均不在 152 个注册集合；vt 007F3768 在 .data 出现 0 次
        ⇒ 无全局静态实例

**④ ④ 与 ② 不同源 → `same_source = no`**


**⑤ 语义与实测一致**

```
逐项核数值，全中：vt 007F3768 ✓ slot+0xC ✓ 槽 007F3774 ✓ COL 00809C68 ✓ TD 00840F68 ✓
      内联名 .?AV?$TClassFactory@VCStreamClass@@@@ ✓（与执行器逐字相同）
      006BEF6A ✓ 006BEF6C ✓ 006BEF6E ✓ 006BEF70 ✓ 006BEF72 ✓ [edx+0x38] ✓
      004A2999 E_POINTER ✓ 004A2A02 E_NOINTERFACE ✓ 004A2A11 xor eax,eax ✓ 006BEF4C call 0x4A2820 ✓
      ④ 006BEE49 ✓。第 4 列未主张读/写方向，无可反之处。
```

---

### 2.3 `006BF690` — TClassFactory<SuperClass>::slot3（S17）→ **PASS**

**① ② 类身份（全表枚举；独立成立）**

```
  vt=007F37E0 slot3 (+0xC) @007F37EC ; COL=00809DF8 TD=00841068 .?AV?$TClassFactory@VSuperClass@@@@
```
entry 作为 dword 只出现 1 次：007F37EC (.rdata) ⇒ 唯一持有表 base=007F37E0
      表 5 槽：0:006BF5D0 1:006BF640 2:006BF660 3:006BF690 4:006BF710
      TD 00841068 只对应 1 个 COL(00809DF8) ⇒ 仅此一张表，5 槽即全部虚函数
      slot0=006BF5D0 实测为 QI：006BF5D5 test eax,eax / 006BF5D9 b8 03400080(E_POINTER)

**② ③b 具体形态：3b2（可伪证返回约定）**

```
③b② 多值状态码 HRESULT（非 bool）
      被调钉死链：006BF6BC push 0x80; call 0x7C8E17(operator new); 006BF6CD mov ecx,eax;
        006BF6CF e8 ecb70000 call 0x6CAEC0（SuperClass 构造器，其 006CAF12 装 SuperClass 主表 007F3FE8）
        ⇒ [esi]=007F3FE8（COL=0080B610 → TD=008423E0 内联 .?AVSuperClass@@，slot0=00410260）
        ⇒ 006BF6ED ff10 call dword ptr [eax] = **00410260 = QueryInterface**
      调用方真分支：
        006BF6EF 8bf8 mov edi,eax / 006BF6F1 85ff test edi,edi / 006BF6F3 7d09 jge 0x6bf6fe
        006BF6FB ff5220 call dword ptr [edx+0x20]   ← SuperClass slot8=006CE220（0x20/4=8 ✓）
        006BF6FE 8bc7 mov eax,edi → ret 0x10
      被调 00410260 返回域：00410269 b8 03400080(E_POINTER) / 004102E6 b8 02400080(E_NOINTERFACE) / 004102F5 33c0(S_OK)
        并依次比 0x7F7C90 / 0x7F7C80 / 0x7F7C70 / 0x7E9AE0 四个 16 字节 IID（f3a7,ecx=4），004102E1 cmp [eax],0 + jne 判命中
      ⇒ {0x80004003, 0x80004002, 0} 多值状态码，非 {0,1} 布尔
      两路动作不同：成功保留对象返回 0；失败 call [edx+0x20] 释放后返回负码
        006CE220 实测 `push esi; mov esi,ecx; call 0x6CB120; test byte [esp+8],1; je; push esi; call 0x7C8B3D(free)`
        ⇒ 确为释放语义 ✓
      无 eax 覆写；入口 operator new 空判断（006BF6C9 test eax,eax → 0x8007000E）属 ③a 不计入
```

**③ ④ 使用见证（独立成立；direct-only 不足）**

```
  ctor 006BF5C0 @006BF5C9 mov [eax],0x7f37e0
```
④ 活虚表安装点（全 .text 扫 E8/E9 目标 == 006BF690：0 条直调）
      枚举 vt 007F37E0 全部写点：整镜像 dword 出现 **1 次**
        006BF5C9  c700 e0377f00  mov dword ptr [eax],0x7f37e0   ← 采用
      所在函数 006BF5C0：8bc1 mov eax,ecx / mov [eax+4],0 / 装 vt / c3 ret ⇒ **构造器**
      实调用上下文：唯一调用者 006BC599 call 0x6bf5c0，前序 006BC589 push 8 / call 0x7C8E17 /
        006BC593 test eax,eax / 006BC597 mov ecx,eax ⇒ 堆分配后立刻构造并被使用
      atexit 排除：006BF5C0 / 006BF5D0 不在 152 个注册集合；vt 007F37E0 在 .data 出现 0 次
      附（表 007F3FE8 的写点，仅用于 ③ 的被调钉死，不作本行 ④ 锚）：006CAF12（构造器 006CAEC0 内）、
        006CB129（析构器 006CB120 内，即 Release 006CE220 所 call 者）、006CAFF9、006CDF15

**④ ④ 与 ② 不同源 → `same_source = no`**


**⑤ 语义与实测一致**

```
逐项核数值，全中：vt 007F37E0 ✓ slot+0xC ✓ 槽 007F37EC ✓ COL 00809DF8 ✓ TD 00841068 ✓
      内联名 .?AV?$TClassFactory@VSuperClass@@@@ ✓
      006BF6ED ✓ 006BF6EF ✓ 006BF6F1 ✓ 006BF6F3 ✓ 006BF6F5 ✓ [edx+0x20] ✓
      00410269 E_POINTER ✓ 004102E6 E_NOINTERFACE ✓ 004102F5 xor eax,eax ✓
      006BF6CF call 0x6CAEC0 ✓ 007F3FE8 slot0=00410260 ✓（执行器「符合主表 slot0 常见 00410260」实测成立）
      ④ 006BF5C9 ✓。第 4 列未主张读/写方向，无可反之处。
```

---

### 2.4 `007B13D0` — IPXInterfaceClass::slot16（S18）→ **PASS**

**① ② 类身份（全表枚举；独立成立）**

```
  vt=007F794C slot16 (+0x40) @007F798C ; COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@
```
entry 作为 dword 只出现 1 次：007F798C (.rdata) ⇒ 唯一持有表 base=007F794C
      IPX 表 23 槽，slot16 == 007B13D0 ✓；IPX TD 只有 1 个 COL ⇒ 该表即 IPX 主虚表
      三张相关虚表（同一族，实测）：
        IPX      vt=007F794C 23 槽 COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@      chd base[1]=WinsockInterfaceClass
        Winsock  vt=007F79BC 23 槽 COL=0080EAF8 TD=0084D8D0 .?AVWinsockInterfaceClass@@  chd numBase=1(根)
        UDP      vt=007F7A6C 31 槽 COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@      chd base[1]=WinsockInterfaceClass
      即 IPX、UDP 均派生自 Winsock；每个 TD 只有 1 个 COL ⇒ 每类各 1 张虚表，无「小成员表 vs 主表」歧义。

**② ③b 具体形态：3b2（可伪证返回约定）**

```
③b② 多值状态码（WSOCK32 SOCKET_ERROR 哨兵 + WSA 错误码二级判别）
      本体 007B13D0..007B1720（290 条指令 / 848 字节），首 cmp eax,0x473 为消息号分派。
      sendto 路：
        007B14C6  e8 e5740100   call 0x7C89B0  → IAT [0x7E1558] = **WSOCK32!sendto**
        007B14CB  83f8ff        cmp eax,-1
        007B14CE  7510          jne 0x7B14E0
        007B14D0  call 0x7C897A → WSAGetLastError
        007B14D5  3d 33270000   cmp eax,0x2733   (WSAEWOULDBLOCK=10035)
        007B14DA  0f8531ffffff  jne 0x7B1411   ⇒ 真错误：007B141D call [eax+0x24] 关闭，返回 0
        等 0x2733 时落到 007B14E0 继续（视为可重试，摘队/释放缓冲/回边 007B143C）
      recvfrom 路：
        007B1586  e8 1f740100   call 0x7C89AA  → IAT [0x7E154C] = **WSOCK32!recvfrom**
        007B158B  83f8ff        cmp eax,-1
        007B158E  89442410      mov [esp+0x10],eax   （存值，不覆写 eax）
        007B1592  752b          jne 0x7B15BF
        失败：call 0x7C897A(WSAGetLastError) / 007B1599 cmp eax,0x2733 / 007B159E je 0x7B1714
      ⇒ 返回值域至少 {-1 且错误码 0x2733, -1 且其它错误, ≥0 字节数} 三态，**多值状态码，非 {0,1} 布尔**
      两路动作真不同（重试续跑 vs 关socket/中止）；无 eax 覆写（call→cmp 紧邻）
```

**③ ④ 使用见证（独立成立；direct-only 不足）**

```
  ctor 007B0D90 @007B0DA4 mov [esi],0x7f794c + 派发点 007775FF call [eax+0x40]
```
④ 使用见证
      (a) 直调：全 .text E8/E9 目标 == 007B13D0 的站点 **0 条**
      (b) 活虚表安装点：007B0DA4（见下 ㉓）
      (c) 真实派发点：007775C1 mov eax,[0x887628] → 007775FF ff5040 call dword ptr [eax+0x40]
          （0x887628 即构造后存放网络接口对象的全局；slot16 派发；IPX/UDP 两类的 slot16 分别是本行与 007B3AA0）
      ㉓ 构造/析构逐个判定（枚举全部写点，非析构锚）：
        IPX  ctor 007B0D90 @007B0DA4（先 call 0x7B19C0 = Winsock 基类构造，再装 vt，尾 mov eax,esi/ret）
             直接调用者 **5** 个：0052E3F1 00540926 00560533 00685B21 00686189
        Winsock ctor 007B19C0 @007B1A20（大体量字段初化 + 0x80 次字节表清零 + 尾 mov eax,esi/ret）
             直接调用者 2 个：007B0D93（IPX ctor 内）、007B2DB3（UDP ctor 内）
        Winsock 析构 007B1AB0 @007B1ABC、Winsock slot0=007B2780 @007B278C（删除析构器）—— **排除**
        UDP  ctor 007B2DB0 @007B2E2D（call 0x7B19C0 后初化 + 尾 mov eax,esi/ret）
             直接调用者 1 个：0052F456
        UDP  析构 007B2E50 @007B2E56（call 0x7C8B3D 释放）、UDP slot0=007B4170 @007B4176（删除析构器）—— **排除**
      atexit 排除：全 .text `push imm32; call 0x7C978A` 注册点 152 个；
        007B0D90 / 007B19C0 / 007B2DB0 / 007B1AB0 / 007B2780 / 007B2E50 / 007B4170 **均不在**注册集合
      静态实例排除：007F794C / 007F79BC / 007F7A6C 作为 dword 在 .data 中出现 **0 次**
        ⇒ 无全局静态对象，活表全部来自堆分配路径
      对象落点：构造后存入全局 **0x887628**（0052E3FD / 00685B26 / 0068618E 存 IPX；0052F461 存 UDP）

**④ ④ 与 ② 不同源 → `same_source = no`**


**⑤ 语义与实测一致**

```
逐项核数值，全中：007B14C6 ✓ 007B1586 ✓ cmp eax,-1 ✓ jne 分支 ✓ ② vt 007F794C slot+0x40 槽 007F798C ✓
      COL 0080EA60 ✓ TD 0084D8F8 ✓ ④ 007B0DA4 ✓ in_func 007B0D90 ✓ direct5 ✓ 非析构 ✓
      API 身份独立复核（IAT）：sendto=0x7E1558 ✓ recvfrom=0x7E154C ✓ WSAGetLastError=0x7E1574 ✓
      「失败返 -1、成功返字节数/继续」与实测一致；「无 eax 覆写」实测成立；第 4 列未反写读/写方向。
```

---

### 2.5 `007B1BC0` — IPXInterfaceClass::slot7（S18）→ **PASS**

**① ② 类身份（全表枚举；独立成立）**

```
  vt=007F794C slot7 (+0x1C) @007F7968 ; COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@（另有 Winsock@007F79D8 同址实现）
```
entry 作为 dword 出现 2 次（**两个持有表**，全部枚举）：
        007F7968  IPX     vt=007F794C slot7 (+0x1C)  COL=0080EA60 TD=0084D8F8
        007F79D8  Winsock vt=007F79BC slot7 (+0x1C)  COL=0080EAF8 TD=0084D8D0
      执行器 ② 只引 IPX 表。按 §8.7 判据1 全枚举后：IPX 与 Winsock **两张表的 slot7 指向同一 entry**，
      且 chd 显示 IPX 派生自 Winsock（base[1]=WinsockInterfaceClass）⇒ 该实现由**基类 Winsock 定义**、
      IPX 未覆写。两种表述都字节为真：「IPX 虚表 slot7 == 本 entry」成立（本行按此命名），
      但若按「实现所属类」讲，归属类应为 WinsockInterfaceClass —— 记此注，不改变 ② 的可核性。
      三张相关虚表（同一族，实测）：
        IPX      vt=007F794C 23 槽 COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@      chd base[1]=WinsockInterfaceClass
        Winsock  vt=007F79BC 23 槽 COL=0080EAF8 TD=0084D8D0 .?AVWinsockInterfaceClass@@  chd numBase=1(根)
        UDP      vt=007F7A6C 31 槽 COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@      chd base[1]=WinsockInterfaceClass
      即 IPX、UDP 均派生自 Winsock；每个 TD 只有 1 个 COL ⇒ 每类各 1 张虚表，无「小成员表 vs 主表」歧义。

**② ③b 具体形态：3b2（可伪证返回约定）**

```
③b② 多值状态码（WSAAsyncSelect = SOCKET_ERROR 哨兵）
      007B1BDB  e8 dc6d0100   call 0x7C89BC  → IAT [0x7E156C] = **WSOCK32!WSAAsyncSelect**
      007B1BE0  83f8ff        cmp eax,-1
      007B1BE3  7517          jne 0x7B1BFC
        失败：007B1BE5 call 0x7C897A(WSAGetLastError) / 007B1BEB push 0x84DEA4(日志串) / 007B1BF8 32c0 xor al,al / ret
      007B1C1F  e8 986d0100   call 0x7C89BC  → WSAAsyncSelect（第二次）
      007B1C24  83f8ff        cmp eax,-1
      007B1C27  7517          jne 0x7B1C40
        失败：007B1C29 call 0x7C897A / 007B1C2F push 0x84DE68 / 007B1C3C xor al,al / ret
      007B1C40  b001          mov al,1 / ret    ← 成功
      ⇒ 判据是 WSOCK32 的 SOCKET_ERROR(-1) 哨兵，`cmp eax,-1` 后真分支；返回值域 {-1, 0} 且 -1 是错误域专用值
        （不是 {0,1} 布尔：分支比较对象是 -1，不是 0/1）。两路动作不同（记日志+失败 vs 继续+成功）。
      无 eax 覆写：007B1BDB→007B1BE0、007B1C1F→007B1C24 之间无写 eax 指令。
```

**③ ④ 使用见证（独立成立；direct-only 不足）**

```
  ctor 007B0D90 @007B0DA4 + 真实调用者 007B3895 call 0x7b1bc0
```
④ 使用见证（两种都成立，且与 ② 不同源）
      (a) **真实调用者**：007B3890 体内 007B3895 `e8 26e3ffff call 0x7B1BC0`（UDP slot7 直接调用本 entry，
          紧随 007B389A `84c0 test al,al` + 007B389C `je` 消费其布尔返回）
      (b) 活虚表安装点 007B0DA4（IPX ctor）/ 007B1A20（Winsock ctor）—— 见下 ㉓
      ㉓ 构造/析构逐个判定（枚举全部写点，非析构锚）：
        IPX  ctor 007B0D90 @007B0DA4（先 call 0x7B19C0 = Winsock 基类构造，再装 vt，尾 mov eax,esi/ret）
             直接调用者 **5** 个：0052E3F1 00540926 00560533 00685B21 00686189
        Winsock ctor 007B19C0 @007B1A20（大体量字段初化 + 0x80 次字节表清零 + 尾 mov eax,esi/ret）
             直接调用者 2 个：007B0D93（IPX ctor 内）、007B2DB3（UDP ctor 内）
        Winsock 析构 007B1AB0 @007B1ABC、Winsock slot0=007B2780 @007B278C（删除析构器）—— **排除**
        UDP  ctor 007B2DB0 @007B2E2D（call 0x7B19C0 后初化 + 尾 mov eax,esi/ret）
             直接调用者 1 个：0052F456
        UDP  析构 007B2E50 @007B2E56（call 0x7C8B3D 释放）、UDP slot0=007B4170 @007B4176（删除析构器）—— **排除**
      atexit 排除：全 .text `push imm32; call 0x7C978A` 注册点 152 个；
        007B0D90 / 007B19C0 / 007B2DB0 / 007B1AB0 / 007B2780 / 007B2E50 / 007B4170 **均不在**注册集合
      静态实例排除：007F794C / 007F79BC / 007F7A6C 作为 dword 在 .data 中出现 **0 次**
        ⇒ 无全局静态对象，活表全部来自堆分配路径
      对象落点：构造后存入全局 **0x887628**（0052E3FD / 00685B26 / 0068618E 存 IPX；0052F461 存 UDP）

**④ ④ 与 ② 不同源 → `same_source = no`**


**⑤ 语义与实测一致**

```
逐项核数值，全中：007B1BDB ✓ 007B1C1F ✓ cmp eax,-1 ✓ jne ✓ ② vt 007F794C slot+0x1C 槽 007F7968 ✓
      COL 0080EA60 ✓ TD 0084D8F8 ✓ ④ 007B0DA4 / 007B0D90 / direct5 / 非析构 ✓ 直调者 007B3895 ✓
      API 身份独立复核：WSAAsyncSelect=0x7E156C ✓ WSAGetLastError=0x7E1574 ✓
      ⚠ 唯一偏差（不改变 ③b 成立）：执行器 ② 称「.?AVIPXInterfaceClass@@」而**未提 Winsock 表同址**；
        按判据1 已补全枚举，归属说明见 ② 注。
```

---

### 2.6 `007B2630` — IPXInterfaceClass::slot10（S18）→ **PASS**

**① ② 类身份（全表枚举；独立成立）**

```
  vt=007F794C slot10 (+0x28) @007F7974 ; COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@（另 Winsock@007F79E4 / UDP@007F7A94 同址）
```
entry 作为 dword 出现 **3 次（三个持有表，全部枚举）**：
        007F7974  IPX     slot10 (+0x28)  COL=0080EA60 TD=0084D8F8
        007F79E4  Winsock slot10 (+0x28)  COL=0080EAF8 TD=0084D8D0
        007F7A94  UDP     slot10 (+0x28)  COL=0080EBE0 TD=0084E1C0
      三个表的 slot10 指向同一 entry ⇒ 实现由基类 Winsock 定义，IPX 与 UDP 均未覆写。
      执行器只引 IPX 表（字节为真），按 §8.7 判据1 在此补全枚举。
      三张相关虚表（同一族，实测）：
        IPX      vt=007F794C 23 槽 COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@      chd base[1]=WinsockInterfaceClass
        Winsock  vt=007F79BC 23 槽 COL=0080EAF8 TD=0084D8D0 .?AVWinsockInterfaceClass@@  chd numBase=1(根)
        UDP      vt=007F7A6C 31 槽 COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@      chd base[1]=WinsockInterfaceClass
      即 IPX、UDP 均派生自 Winsock；每个 TD 只有 1 个 COL ⇒ 每类各 1 张虚表，无「小成员表 vs 主表」歧义。

**② ③b 具体形态：3b2（可伪证返回约定）**

```
③b② 多值状态码（setsockopt = SOCKET_ERROR 哨兵；两次调用四种日志落点）
      007B2652  e8 4d630100   call 0x7C89A4  → IAT [0x7E1554] = **WSOCK32!setsockopt**（SO_REUSEADDR 路）
      007B2657  83f8ff        cmp eax,-1
      007B265A  7515          jne 0x7B2671
        失败 007B265C call 0x7C897A(WSAGetLastError) / 007B2662 push 0x84E0D8 / jmp 007B267E
        成功 007B2671 push 0x84E0B8
      007B2690  e8 0f630100   call 0x7C89A4  → setsockopt（第二路，0x1001）
      007B2695  83f8ff        cmp eax,-1
      007B2699  7518          jne 0x7B26B3
        失败 007B269B call 0x7C897A / 007B26A1 push 0x84E080 / 007B26AE mov al,1
        成功 007B26B3 push 0x84E060 / 007B26C0 mov al,1
      ⇒ 判据是 SOCKET_ERROR(-1) 哨兵 + 二次 `cmp eax,-1` 真分支，两路日志串实测不同（0x84E0D8/0x84E0B8、0x84E080/0x84E060）
        ⇒ 可伪证错误域；非 {0,1} 布尔判据（比较对象 -1）。
      无 eax 覆写：两处 call→cmp 紧邻。
```

**③ ④ 使用见证（独立成立；direct-only 不足）**

```
  ctor 007B0D90 @007B0DA4 + 4 个真实调用者 (007B13AB/007B31BC/007B32EA/007B36A1)
```
④ 使用见证（两路都成立，且与 ② 不同源）
      (a) **真实调用者 4 条**（全 .text E8/E9 目标 == 007B2630）：
          007B13AB (IPX slot16 体内) / 007B31BC (UDP slot23 体内) / 007B32EA (UDP slot26 体内) / 007B36A1 (UDP slot15 体内)
      (b) 活虚表安装点 007B0DA4 / 007B1A20 / 007B2E2D（三张表各自的构造器）—— 见下 ㉓
      ㉓ 构造/析构逐个判定（枚举全部写点，非析构锚）：
        IPX  ctor 007B0D90 @007B0DA4（先 call 0x7B19C0 = Winsock 基类构造，再装 vt，尾 mov eax,esi/ret）
             直接调用者 **5** 个：0052E3F1 00540926 00560533 00685B21 00686189
        Winsock ctor 007B19C0 @007B1A20（大体量字段初化 + 0x80 次字节表清零 + 尾 mov eax,esi/ret）
             直接调用者 2 个：007B0D93（IPX ctor 内）、007B2DB3（UDP ctor 内）
        Winsock 析构 007B1AB0 @007B1ABC、Winsock slot0=007B2780 @007B278C（删除析构器）—— **排除**
        UDP  ctor 007B2DB0 @007B2E2D（call 0x7B19C0 后初化 + 尾 mov eax,esi/ret）
             直接调用者 1 个：0052F456
        UDP  析构 007B2E50 @007B2E56（call 0x7C8B3D 释放）、UDP slot0=007B4170 @007B4176（删除析构器）—— **排除**
      atexit 排除：全 .text `push imm32; call 0x7C978A` 注册点 152 个；
        007B0D90 / 007B19C0 / 007B2DB0 / 007B1AB0 / 007B2780 / 007B2E50 / 007B4170 **均不在**注册集合
      静态实例排除：007F794C / 007F79BC / 007F7A6C 作为 dword 在 .data 中出现 **0 次**
        ⇒ 无全局静态对象，活表全部来自堆分配路径
      对象落点：构造后存入全局 **0x887628**（0052E3FD / 00685B26 / 0068618E 存 IPX；0052F461 存 UDP）

**④ ④ 与 ② 不同源 → `same_source = no`**


**⑤ 语义与实测一致**

```
逐项核数值，全中：007B2652 ✓ 007B2690 ✓ cmp eax,-1 ✓ 日志串 0x84E0D8/0x84E0B8 ✓ 0x84E080/0x84E060 ✓
      ② vt 007F794C slot+0x28 槽 007F7974 ✓ COL 0080EA60 ✓ TD 0084D8F8 ✓ ④ 007B0DA4 ✓ direct callers=4 ✓ 非析构 ✓
      API 身份独立复核：setsockopt=0x7E1554 ✓ setsockopt 参数 (0x1002/0x1001, 4, 串) 与 SO_REUSEADDR/SO_DONTLINGER 形态相符
      ⚠ 唯一偏差：② 未提 Winsock/UDP 两表同址（已补全枚举，归属注同上行）。
```

---

### 2.7 `007B26D0` — IPXInterfaceClass::slot17（S18）→ **PASS**

**① ② 类身份（全表枚举；独立成立）**

```
  vt=007F794C slot17 (+0x44) @007F7990 ; COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@（另 Winsock@007F7A00 / UDP@007F7AB0 同址）
```
entry 作为 dword 出现 **3 次（三个持有表）**：
        007F7990  IPX slot17(+0x44) / 007F7A00  Winsock slot17 / 007F7AB0  UDP slot17
      三表同址 ⇒ 实现由基类 Winsock 定义，IPX/UDP 未覆写。执行器只引 IPX 表（字节为真），此补全枚举。
      三张相关虚表（同一族，实测）：
        IPX      vt=007F794C 23 槽 COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@      chd base[1]=WinsockInterfaceClass
        Winsock  vt=007F79BC 23 槽 COL=0080EAF8 TD=0084D8D0 .?AVWinsockInterfaceClass@@  chd numBase=1(根)
        UDP      vt=007F7A6C 31 槽 COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@      chd base[1]=WinsockInterfaceClass
      即 IPX、UDP 均派生自 Winsock；每个 TD 只有 1 个 COL ⇒ 每类各 1 张虚表，无「小成员表 vs 主表」歧义。

**② ③b 具体形态：3b2（可伪证返回约定）**

```
③b② 多值状态码（gethostname = SOCKET_ERROR 哨兵）
      007B26DB  e8 ee620100   call 0x7C89CE  → IAT [0x7E1560] = **WSOCK32!gethostname**
      007B26E0  83f8ff        cmp eax,-1
      007B26E3  7519          jne 0x7B26FE
        失败 007B26E5 call 0x7C897A(WSAGetLastError) / 007B26EB push 0x84E134 / 007B26F8 32c0 xor al,al / 007B26FB c20800 ret 8
        成功 007B26FE push 0x84E110 / 007B2709 add esp,8 / 007B270C b001 mov al,1 / 007B270F ret 8
      ⇒ `cmp eax,-1` 后真分支；判据对象是 gethostname 的 SOCKET_ERROR 哨兵，属 API 错误域
        （不是 {0,1} 布尔：分支比较 -1，且两路落不同日志串 0x84E134 / 0x84E110）。
      无 eax 覆写：007B26DB→007B26E0 紧邻。
```

**③ ④ 使用见证（独立成立；direct-only 不足）**

```
  ctor 007B0D90 @007B0DA4（无直调，无槽位派发点可锚）
```
④ 使用见证 —— **本行是 12 行里 ④ 最弱的一行，照实记**
      (a) 直调：全 .text E8/E9 目标 == 007B26D0 的站点 **0 条**
      (b) 槽位派发点：扫「从全局 0x887628 取对象后 call [reg+0x44]」**0 命中**；
          全 .text `call [reg+0x44]` 共 131 处，泛化过高（0x44 在多族类里都是某槽），
          无法把任何一处钉到本类实例 ⇒ **不主张有派发点**
      (c) 活虚表安装点：007B0DA4（IPX ctor）/ 007B1A20（Winsock ctor）/ 007B2E2D（UDP ctor）——
          即 ④ 只由「该槽所在的活虚表确实被构造器装入活对象」这一条支撑
      ㉓ 构造/析构逐个判定（枚举全部写点，非析构锚）：
        IPX  ctor 007B0D90 @007B0DA4（先 call 0x7B19C0 = Winsock 基类构造，再装 vt，尾 mov eax,esi/ret）
             直接调用者 **5** 个：0052E3F1 00540926 00560533 00685B21 00686189
        Winsock ctor 007B19C0 @007B1A20（大体量字段初化 + 0x80 次字节表清零 + 尾 mov eax,esi/ret）
             直接调用者 2 个：007B0D93（IPX ctor 内）、007B2DB3（UDP ctor 内）
        Winsock 析构 007B1AB0 @007B1ABC、Winsock slot0=007B2780 @007B278C（删除析构器）—— **排除**
        UDP  ctor 007B2DB0 @007B2E2D（call 0x7B19C0 后初化 + 尾 mov eax,esi/ret）
             直接调用者 1 个：0052F456
        UDP  析构 007B2E50 @007B2E56（call 0x7C8B3D 释放）、UDP slot0=007B4170 @007B4176（删除析构器）—— **排除**
      atexit 排除：全 .text `push imm32; call 0x7C978A` 注册点 152 个；
        007B0D90 / 007B19C0 / 007B2DB0 / 007B1AB0 / 007B2780 / 007B2E50 / 007B4170 **均不在**注册集合
      静态实例排除：007F794C / 007F79BC / 007F7A6C 作为 dword 在 .data 中出现 **0 次**
        ⇒ 无全局静态对象，活表全部来自堆分配路径
      对象落点：构造后存入全局 **0x887628**（0052E3FD / 00685B26 / 0068618E 存 IPX；0052F461 存 UDP）

**④ ④ 与 ② 不同源 → `same_source = no`**


**⑤ 语义与实测一致**

```
逐项核数值，全中：007B26DB ✓ cmp eax,-1 ✓ jne(gap=0) ✓ 失败 xor al,al / 成功 mov al,1 ✓
      ② vt 007F794C slot+0x44 槽 007F7990 ✓ COL 0080EA60 ✓ TD 0084D8F8 ✓ ④ 007B0DA4 / 007B0D90 / direct5 / 非析构 ✓
      API 身份独立复核：gethostname=0x7E1560 ✓
      「读写方向写反」不适用（无缓冲区方向主张，仅查返回哨兵）。
      ⚠ 保留意见：执行器 ④ 写「装活 vt + 派发」，其中「派发」在本行**我复现不出来**（见 ④(b)）。
```

---

### 2.8 `007B30B0` — UDPInterfaceClass::slot23（S18）→ **PASS**

**① ② 类身份（全表枚举；独立成立）**

```
  vt=007F7A6C slot23 (+0x5C) @007F7AC8 ; COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@
```
entry 作为 dword 只出现 1 次：007F7AC8 (.rdata) ⇒ 唯一持有表 base=007F7A6C
      UDP 表 31 槽（0:007B4170 … 23:007B30B0 … 30:007B3920），slot23 == 本 entry ✓
      UDP TD 只有 1 个 COL ⇒ 该 31 槽表即 UDP 主虚表（非「小成员表」）
      三张相关虚表（同一族，实测）：
        IPX      vt=007F794C 23 槽 COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@      chd base[1]=WinsockInterfaceClass
        Winsock  vt=007F79BC 23 槽 COL=0080EAF8 TD=0084D8D0 .?AVWinsockInterfaceClass@@  chd numBase=1(根)
        UDP      vt=007F7A6C 31 槽 COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@      chd base[1]=WinsockInterfaceClass
      即 IPX、UDP 均派生自 Winsock；每个 TD 只有 1 个 COL ⇒ 每类各 1 张虚表，无「小成员表 vs 主表」歧义。

**② ③b 具体形态：3b2（可伪证返回约定）**

```
③b② 多值状态码（socket / bind = SOCKET_ERROR 哨兵）
      007B30E4  e8 b5580100   call 0x7C899E  → IAT [0x7E157C] = **WSOCK32!socket**
      007B30E9  83f8ff        cmp eax,-1
      007B30EC  89866cf00300  mov dword ptr [esi+0x3f06c],eax   （存 socket 句柄，不覆写 eax）
      007B30F2  7509          jne 0x7B30FD
        失败 007B30F4 32c0 xor al,al / 007B30FA c20400 ret 4
      007B315F  e8 34580100   call 0x7C8998  → IAT [0x7E1580] = **WSOCK32!bind**
      007B3164  83f8ff        cmp eax,-1
      007B3168  7523          jne 0x7B318D
        失败 007B316A call 0x7C897A(WSAGetLastError) / 007B3170 push 0x84E204 / 007B317C..007B3181 call [eax+4]（关 socket）
             / 007B3184 xor al,al / ret 4
        成功 007B318D.. 组包 + 007B31B3 call 0x7C89A4(setsockopt) + 007B31BC call 0x7B2630 + 007B31CE mov al,1
      ⇒ 判据是 SOCKET_ERROR(-1) 哨兵（socket 与 bind 各一次），两路动作真不同（关 socket / 继续组包入列）
      无 eax 覆写：两处 call→cmp 紧邻（007B30EC 是存值不是覆写比较对象）
```

**③ ④ 使用见证（独立成立；direct-only 不足）**

```
  ctor 007B2DB0 @007B2E2D mov [esi],0x7f7a6c + 派发点 0069C457 call [edx+0x5c]
```
④ 使用见证
      (a) 直调 0 条
      (b) 活虚表安装点 007B2E2D（UDP ctor）
      (c) 真实派发点：0069C436 mov ecx,[0x887628] → 0069C457 ff525c call dword ptr [edx+0x5c]（slot23）
      ㉓ 构造/析构逐个判定（枚举全部写点，非析构锚）：
        IPX  ctor 007B0D90 @007B0DA4（先 call 0x7B19C0 = Winsock 基类构造，再装 vt，尾 mov eax,esi/ret）
             直接调用者 **5** 个：0052E3F1 00540926 00560533 00685B21 00686189
        Winsock ctor 007B19C0 @007B1A20（大体量字段初化 + 0x80 次字节表清零 + 尾 mov eax,esi/ret）
             直接调用者 2 个：007B0D93（IPX ctor 内）、007B2DB3（UDP ctor 内）
        Winsock 析构 007B1AB0 @007B1ABC、Winsock slot0=007B2780 @007B278C（删除析构器）—— **排除**
        UDP  ctor 007B2DB0 @007B2E2D（call 0x7B19C0 后初化 + 尾 mov eax,esi/ret）
             直接调用者 1 个：0052F456
        UDP  析构 007B2E50 @007B2E56（call 0x7C8B3D 释放）、UDP slot0=007B4170 @007B4176（删除析构器）—— **排除**
      atexit 排除：全 .text `push imm32; call 0x7C978A` 注册点 152 个；
        007B0D90 / 007B19C0 / 007B2DB0 / 007B1AB0 / 007B2780 / 007B2E50 / 007B4170 **均不在**注册集合
      静态实例排除：007F794C / 007F79BC / 007F7A6C 作为 dword 在 .data 中出现 **0 次**
        ⇒ 无全局静态对象，活表全部来自堆分配路径
      对象落点：构造后存入全局 **0x887628**（0052E3FD / 00685B26 / 0068618E 存 IPX；0052F461 存 UDP）

**④ ④ 与 ② 不同源 → `same_source = no`**


**⑤ 语义与实测一致**

```
逐项核数值，全中：007B30E4(socket) ✓ 007B315F(bind) ✓ cmp eax,-1 ✓ jne ✓
      ② vt 007F7A6C slot+0x5C 槽 007F7AC8 ✓ COL 0080EBE0 ✓ TD 0084E1C0 ✓（主虚表）✓
      ④ 007B2E2D ✓ in_func 007B2DB0 ✓ direct1 ✓ 非析构 ✓；排除 007B2E56(析构 007B2E50) ✓
        007B4176(删除析构 007B4170 = **本表 slot0**，实测装 vt 后 call 0x7C8B3D 释放) ✓
      API 身份独立复核：socket=0x7E157C ✓ bind=0x7E1580 ✓ closesocket=0x7E1584 ✓ setsockopt=0x7E1554 ✓
```

---

### 2.9 `007B31E0` — UDPInterfaceClass::slot26（S18）→ **PASS**

**① ② 类身份（全表枚举；独立成立）**

```
  vt=007F7A6C slot26 (+0x68) @007F7AD4 ; COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@
```
entry 作为 dword 只出现 1 次：007F7AD4 (.rdata) ⇒ 唯一持有表 base=007F7A6C
      UDP 表 slot26 == 007B31E0 ✓；UDP TD 只有 1 个 COL ⇒ 主虚表
      三张相关虚表（同一族，实测）：
        IPX      vt=007F794C 23 槽 COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@      chd base[1]=WinsockInterfaceClass
        Winsock  vt=007F79BC 23 槽 COL=0080EAF8 TD=0084D8D0 .?AVWinsockInterfaceClass@@  chd numBase=1(根)
        UDP      vt=007F7A6C 31 槽 COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@      chd base[1]=WinsockInterfaceClass
      即 IPX、UDP 均派生自 Winsock；每个 TD 只有 1 个 COL ⇒ 每类各 1 张虚表，无「小成员表 vs 主表」歧义。

**② ③b 具体形态：3b2（可伪证返回约定）**

```
③b② 多值状态码（bind = SOCKET_ERROR 哨兵；另 socket 一处同形）
      007B3234  e8 65570100   call 0x7C899E  → **WSOCK32!socket**；007B323B 83feff cmp esi,-1；007B323E 750c jne
        失败 007B3240.. 32c0 xor al,al / ret 4
      007B3295  e8 fe560100   call 0x7C8998  → **WSOCK32!bind**
      007B329A  83f8ff        cmp eax,-1
      007B329D  7520          jne 0x7B32BF
        失败 007B329F 56 push esi / 007B32A0 call 0x7C8992(**closesocket**) / 007B32A6 push 0x84E294 / 007B32B6 xor al,al / ret 4
        成功 007B32BF..: 007B32C6 写组播地址表 [ebx+ecx*2+0x3f320]=bp、007B32D6 写 [ebx+edx*4+0x3f300]=esi、
             007B32E4 计数 +1、007B32EA call 0x7B2630(setsockopt 路)、007B32F4 push 0x84E274、007B32FC mov al,1
      ⇒ SOCKET_ERROR(-1) 哨兵 cmp+jne 真分支；两路动作真不同（closesocket 放弃 vs 写表+调 007B2630+成功）
      无 eax 覆写：两处 call→cmp 紧邻
```

**③ ④ 使用见证（独立成立；direct-only 不足）**

```
  ctor 007B2DB0 @007B2E2D + 派发点 005D90A9 call [eax+0x68]
```
④ 使用见证
      (a) 直调 0 条
      (b) 活虚表安装点 007B2E2D（UDP ctor）
      (c) 真实派发点：005D9093 mov eax,[0x887628] → 005D90A9 ff5068 call dword ptr [eax+0x68]（slot26）
          同类另有 005D96B5/005D96DA/005D9876/005D98A8/005D9ABA 等 20 处同槽派发（均自 0x887628）
      ㉓ 构造/析构逐个判定（枚举全部写点，非析构锚）：
        IPX  ctor 007B0D90 @007B0DA4（先 call 0x7B19C0 = Winsock 基类构造，再装 vt，尾 mov eax,esi/ret）
             直接调用者 **5** 个：0052E3F1 00540926 00560533 00685B21 00686189
        Winsock ctor 007B19C0 @007B1A20（大体量字段初化 + 0x80 次字节表清零 + 尾 mov eax,esi/ret）
             直接调用者 2 个：007B0D93（IPX ctor 内）、007B2DB3（UDP ctor 内）
        Winsock 析构 007B1AB0 @007B1ABC、Winsock slot0=007B2780 @007B278C（删除析构器）—— **排除**
        UDP  ctor 007B2DB0 @007B2E2D（call 0x7B19C0 后初化 + 尾 mov eax,esi/ret）
             直接调用者 1 个：0052F456
        UDP  析构 007B2E50 @007B2E56（call 0x7C8B3D 释放）、UDP slot0=007B4170 @007B4176（删除析构器）—— **排除**
      atexit 排除：全 .text `push imm32; call 0x7C978A` 注册点 152 个；
        007B0D90 / 007B19C0 / 007B2DB0 / 007B1AB0 / 007B2780 / 007B2E50 / 007B4170 **均不在**注册集合
      静态实例排除：007F794C / 007F79BC / 007F7A6C 作为 dword 在 .data 中出现 **0 次**
        ⇒ 无全局静态对象，活表全部来自堆分配路径
      对象落点：构造后存入全局 **0x887628**（0052E3FD / 00685B26 / 0068618E 存 IPX；0052F461 存 UDP）

**④ ④ 与 ② 不同源 → `same_source = no`**


**⑤ 语义与实测一致**

```
逐项核数值，全中：007B3295 ✓ cmp eax,-1 ✓ jne(gap=0) ✓ 失败 closesocket+日志+xor al,al ✓
      成功「写组播地址表 + call 007B2630 + mov al,1」✓（007B32C6/007B32D6/007B32EA/007B32FC）
      ② vt 007F7A6C slot+0x68 槽 007F7AD4 ✓ COL 0080EBE0 ✓ TD 0084E1C0 ✓
      ④ 007B2E2D ✓ 007B2DB0 ✓ 排除两处析构写点 007B2E56 / 007B4176 ✓
      API 身份独立复核：bind=0x7E1580 ✓ socket=0x7E157C ✓ closesocket=0x7E1584 ✓
```

---

### 2.10 `007B3450` — UDPInterfaceClass::slot15（S18）→ **PASS**

**① ② 类身份（全表枚举；独立成立）**

```
  vt=007F7A6C slot15 (+0x3C) @007F7AA8 ; COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@
```
entry 作为 dword 只出现 1 次：007F7AA8 (.rdata) ⇒ 唯一持有表 base=007F7A6C
      UDP 表 slot15 == 007B3450 ✓；UDP TD 只有 1 个 COL ⇒ 主虚表
      三张相关虚表（同一族，实测）：
        IPX      vt=007F794C 23 槽 COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@      chd base[1]=WinsockInterfaceClass
        Winsock  vt=007F79BC 23 槽 COL=0080EAF8 TD=0084D8D0 .?AVWinsockInterfaceClass@@  chd numBase=1(根)
        UDP      vt=007F7A6C 31 槽 COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@      chd base[1]=WinsockInterfaceClass
      即 IPX、UDP 均派生自 Winsock；每个 TD 只有 1 个 COL ⇒ 每类各 1 张虚表，无「小成员表 vs 主表」歧义。

**② ③b 具体形态：3b2（可伪证返回约定）**

```
③b② 多值状态码（socket / bind = SOCKET_ERROR 哨兵）
      007B35F8  e8 a1530100   call 0x7C899E  → **WSOCK32!socket**
      007B35FD  83f8ff        cmp eax,-1
      007B3600  898770f00300  mov dword ptr [edi+0x3f070],eax  （存句柄）
      007B3606  750d          jne 0x7B3615
        失败 007B3608 5f / 007B3609 32c0 xor al,al / ret 4
      007B3653  e8 40530100   call 0x7C8998  → **WSOCK32!bind**
      007B3658  83f8ff        cmp eax,-1
      007B365B  7514          jne 0x7B3671
        失败 007B365D 8b17 mov edx,[edi] / 007B3661 ff5204 call dword ptr [edx+4]（关 socket）/ 007B3665 xor al,al / ret 4
        成功 007B3671.. 组包 + 后续 gethostname/setsockopt
      ⇒ SOCKET_ERROR(-1) 哨兵 cmp+jne 真分支，两路动作真不同
      另：入口 007B3464 ff5064 call [eax+0x64]（slot25）后 007B3469 84c0 test al,al + 007B346B jne 是**布尔返回检查**
        ⇒ 按 ③a 处理，本审计**不计入** ③b（与执行器自述一致）
      无 eax 覆写：007B35FD→007B3606（中间 007B3600 是存值，不动 eax）、007B3658→007B365B
```

**③ ④ 使用见证（独立成立；direct-only 不足）**

```
  ctor 007B2DB0 @007B2E2D + 派发点 0052F474 call [edx+0x3c]
```
④ 使用见证（本行 ④ 最硬：派发点与构造点同处一个函数）
      0052F439 mov ecx,[0x887628] / 0052F43F cmp ecx,ebx / 0052F441 jne → 若为空则 0052F456 call 0x7B2DB0 新建 UDP 对象
      0052F461 mov [0x887628],ecx
      0052F471 8b11 mov edx,[ecx]
      0052F474 ff523c **call dword ptr [edx+0x3c]**  ← slot15 = 本 entry 007B3450
      ⇒ 该派发点的对象正是 0x7B2DB0 构造的 UDP 实例，槽号 +0x3C/4=15 与 ② 完全一致
      (a) 直调 0 条
      (b) 活虚表安装点 007B2E2D（UDP ctor）
      ㉓ 构造/析构逐个判定（枚举全部写点，非析构锚）：
        IPX  ctor 007B0D90 @007B0DA4（先 call 0x7B19C0 = Winsock 基类构造，再装 vt，尾 mov eax,esi/ret）
             直接调用者 **5** 个：0052E3F1 00540926 00560533 00685B21 00686189
        Winsock ctor 007B19C0 @007B1A20（大体量字段初化 + 0x80 次字节表清零 + 尾 mov eax,esi/ret）
             直接调用者 2 个：007B0D93（IPX ctor 内）、007B2DB3（UDP ctor 内）
        Winsock 析构 007B1AB0 @007B1ABC、Winsock slot0=007B2780 @007B278C（删除析构器）—— **排除**
        UDP  ctor 007B2DB0 @007B2E2D（call 0x7B19C0 后初化 + 尾 mov eax,esi/ret）
             直接调用者 1 个：0052F456
        UDP  析构 007B2E50 @007B2E56（call 0x7C8B3D 释放）、UDP slot0=007B4170 @007B4176（删除析构器）—— **排除**
      atexit 排除：全 .text `push imm32; call 0x7C978A` 注册点 152 个；
        007B0D90 / 007B19C0 / 007B2DB0 / 007B1AB0 / 007B2780 / 007B2E50 / 007B4170 **均不在**注册集合
      静态实例排除：007F794C / 007F79BC / 007F7A6C 作为 dword 在 .data 中出现 **0 次**
        ⇒ 无全局静态对象，活表全部来自堆分配路径
      对象落点：构造后存入全局 **0x887628**（0052E3FD / 00685B26 / 0068618E 存 IPX；0052F461 存 UDP）

**④ ④ 与 ② 不同源 → `same_source = no`**


**⑤ 语义与实测一致**

```
逐项核数值，全中：007B35F8(socket) ✓ 007B3653(bind) ✓ cmp eax,-1 ✓ jne ✓ 两路动作不同 ✓
      ② vt 007F7A6C slot+0x3C 槽 007F7AA8 ✓ COL 0080EBE0 ✓ TD 0084E1C0 ✓
      ④ 007B2E2D ✓ 007B2DB0 ✓ direct1 ✓ 排除析构写点 ✓
      「call 0x4068E0 空 stub→test→je 属布尔不计」：0x4068E0 实测**单字节 c3 ret**（确为空 stub ✓）
      API 身份独立复核：socket=0x7E157C ✓ bind=0x7E1580 ✓ closesocket=0x7E1584 ✓ gethostname=0x7E1560 ✓
```

---

### 2.11 `007B3890` — UDPInterfaceClass::slot7（S18）→ **PASS**

**① ② 类身份（全表枚举；独立成立）**

```
  vt=007F7A6C slot7 (+0x1C) @007F7A88 ; COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@
```
entry 作为 dword 只出现 1 次：007F7A88 (.rdata) ⇒ 唯一持有表 base=007F7A6C
      UDP 表 slot7 == 007B3890 ✓（注意：基类 Winsock 的 slot7 是 007B1BC0，UDP 在此**确实覆写**，
      因此本行与 007B1BC0 是两条不同实现，非同一 entry 的两个名字）
      UDP TD 只有 1 个 COL ⇒ 主虚表
      三张相关虚表（同一族，实测）：
        IPX      vt=007F794C 23 槽 COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@      chd base[1]=WinsockInterfaceClass
        Winsock  vt=007F79BC 23 槽 COL=0080EAF8 TD=0084D8D0 .?AVWinsockInterfaceClass@@  chd numBase=1(根)
        UDP      vt=007F7A6C 31 槽 COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@      chd base[1]=WinsockInterfaceClass
      即 IPX、UDP 均派生自 Winsock；每个 TD 只有 1 个 COL ⇒ 每类各 1 张虚表，无「小成员表 vs 主表」歧义。

**② ③b 具体形态：3b2（可伪证返回约定）**

```
③b② 多值状态码（WSAAsyncSelect = SOCKET_ERROR 哨兵）
      007B38C6  e8 f1500100   call 0x7C89BC  → IAT [0x7E156C] = **WSOCK32!WSAAsyncSelect**
      007B38CB  83f8ff        cmp eax,-1
      007B38CE  7419          je 0x7B38E9
        失败 007B38E9 push 0x84E3D0 / call 0x4068E0 / 007B38F6 32c0 xor al,al / ret
        成功 007B38D0 8b8630f30300 mov eax,[esi+0x3f330] / inc ebx / add edi,4 / cmp / 007B38DC jl 回边（遍历地址表）
             → 007B38DE e86d14e2ff call 0x5D4D50 / 007B38E5 b001 mov al,1 / ret
      ⇒ SOCKET_ERROR(-1) 哨兵 cmp+je 真分支；两路动作真不同（记日志失败 vs 遍历地址表后 call 0x5D4D50 成功）
      入口 007B3895 e8 26e3ffff call 0x7B1BC0（**直调** 另一行 entry）+ 007B389A test al,al + 007B389C je
        是布尔检查 ⇒ 属 ③a，不计入 ③b
      无 eax 覆写：007B38C6→007B38CB 紧邻
```

**③ ④ 使用见证（独立成立；direct-only 不足）**

```
  ctor 007B2DB0 @007B2E2D + 派发点 0052F4AC call [eax+0x1c]
```
④ 使用见证
      0052F4A0 8b0d28768800  mov ecx,[0x887628]
      0052F4AA 8b01          mov eax,[ecx]
      0052F4AC ff501c        **call dword ptr [eax+0x1c]**   ← slot7 = 本 entry 007B3890
      ⇒ 与 007B3450 同一函数 0052F4xx，对象同为 0x887628（UDP 实例），槽号 +0x1C/4=7 与 ② 一致
      (a) 直调 0 条（本 entry 无直接调用者）
      (b) 活虚表安装点 007B2E2D（UDP ctor）
      ㉓ 构造/析构逐个判定（枚举全部写点，非析构锚）：
        IPX  ctor 007B0D90 @007B0DA4（先 call 0x7B19C0 = Winsock 基类构造，再装 vt，尾 mov eax,esi/ret）
             直接调用者 **5** 个：0052E3F1 00540926 00560533 00685B21 00686189
        Winsock ctor 007B19C0 @007B1A20（大体量字段初化 + 0x80 次字节表清零 + 尾 mov eax,esi/ret）
             直接调用者 2 个：007B0D93（IPX ctor 内）、007B2DB3（UDP ctor 内）
        Winsock 析构 007B1AB0 @007B1ABC、Winsock slot0=007B2780 @007B278C（删除析构器）—— **排除**
        UDP  ctor 007B2DB0 @007B2E2D（call 0x7B19C0 后初化 + 尾 mov eax,esi/ret）
             直接调用者 1 个：0052F456
        UDP  析构 007B2E50 @007B2E56（call 0x7C8B3D 释放）、UDP slot0=007B4170 @007B4176（删除析构器）—— **排除**
      atexit 排除：全 .text `push imm32; call 0x7C978A` 注册点 152 个；
        007B0D90 / 007B19C0 / 007B2DB0 / 007B1AB0 / 007B2780 / 007B2E50 / 007B4170 **均不在**注册集合
      静态实例排除：007F794C / 007F79BC / 007F7A6C 作为 dword 在 .data 中出现 **0 次**
        ⇒ 无全局静态对象，活表全部来自堆分配路径
      对象落点：构造后存入全局 **0x887628**（0052E3FD / 00685B26 / 0068618E 存 IPX；0052F461 存 UDP）

**④ ④ 与 ② 不同源 → `same_source = no`**


**⑤ 语义与实测一致**

```
逐项核数值，全中：007B38C6 ✓ cmp eax,-1 ✓ je(gap=0) ✓ 失败日志+xor al,al ✓
      成功「遍历地址表 + call 0x5D4D50 + mov al,1」✓（007B38DC 回边、007B38DE call 0x5D4D50、007B38E5 mov al,1）
      ② vt 007F7A6C slot+0x1C 槽 007F7A88 ✓ COL 0080EBE0 ✓ TD 0084E1C0 ✓
      ④ 007B2E2D ✓ 007B2DB0 ✓ 排除析构写点 ✓
      API 身份独立复核：WSAAsyncSelect=0x7E156C ✓
```

---

### 2.12 `007B3AA0` — UDPInterfaceClass::slot16（S18）→ **PASS**

**① ② 类身份（全表枚举；独立成立）**

```
  vt=007F7A6C slot16 (+0x40) @007F7AAC ; COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@
```
entry 作为 dword 只出现 1 次：007F7AAC (.rdata) ⇒ 唯一持有表 base=007F7A6C
      UDP 表 slot16 == 007B3AA0 ✓（IPX 的 slot16 是 007B13D0，两者是不同实现）
      UDP TD 只有 1 个 COL ⇒ 主虚表
      三张相关虚表（同一族，实测）：
        IPX      vt=007F794C 23 槽 COL=0080EA60 TD=0084D8F8 .?AVIPXInterfaceClass@@      chd base[1]=WinsockInterfaceClass
        Winsock  vt=007F79BC 23 槽 COL=0080EAF8 TD=0084D8D0 .?AVWinsockInterfaceClass@@  chd numBase=1(根)
        UDP      vt=007F7A6C 31 槽 COL=0080EBE0 TD=0084E1C0 .?AVUDPInterfaceClass@@      chd base[1]=WinsockInterfaceClass
      即 IPX、UDP 均派生自 Winsock；每个 TD 只有 1 个 COL ⇒ 每类各 1 张虚表，无「小成员表 vs 主表」歧义。

**② ③b 具体形态：3b2（可伪证返回约定）**

```
③b② 多值状态码（sendto = SOCKET_ERROR 哨兵 + WSA 错误码二级判别）
      007B3D75  e8 364c0100   call 0x7C89B0  → IAT [0x7E1558] = **WSOCK32!sendto**
      007B3D7A  83f8ff        cmp eax,-1
      007B3D7D  757c          jne 0x7B3DFB          ← 成功：继续缓冲摘除
      007B3D7F  e8 f64b0100   call 0x7C897A (WSAGetLastError)
      007B3D84  3d 33270000   cmp eax,0x2733         (WSAEWOULDBLOCK)
      007B3D89  7470          je 0x7B3DFB           ← 可重试：与成功同落点
      007B3D8B  call 0x7C897A / 007B3D91 push 0x84E4B4(日志) / 007B3DA4 ff5224 call [edx+0x24] / 007B3DAA xor eax,eax / ret
      ⇒ 返回域三态 {-1∧0x2733, -1∧其它错误, ≥0 字节数}，真错误与可重试分离 ⇒ **多值状态码，非 {0,1} 布尔**
      无 eax 覆写：007B3D75→007B3D7A 紧邻
```

**③ ④ 使用见证（独立成立；direct-only 不足）**

```
  ctor 007B2DB0 @007B2E2D + 派发点 007775FF call [eax+0x40]
```
④ 使用见证
      (a) 直调 0 条
      (b) 活虚表安装点 007B2E2D（UDP ctor）
      (c) 真实派发点：007775C1 mov eax,[0x887628] → 007775FF ff5040 call dword ptr [eax+0x40]（slot16）
          注：0x887628 在 IPX 模式下装 IPX 实例（其 slot16=007B13D0）、UDP 模式下装 UDP 实例（slot16=本行），
          故该派发点覆盖 slot16 这一槽的两个实现，本行是其 UDP 侧
      ㉓ 构造/析构逐个判定（枚举全部写点，非析构锚）：
        IPX  ctor 007B0D90 @007B0DA4（先 call 0x7B19C0 = Winsock 基类构造，再装 vt，尾 mov eax,esi/ret）
             直接调用者 **5** 个：0052E3F1 00540926 00560533 00685B21 00686189
        Winsock ctor 007B19C0 @007B1A20（大体量字段初化 + 0x80 次字节表清零 + 尾 mov eax,esi/ret）
             直接调用者 2 个：007B0D93（IPX ctor 内）、007B2DB3（UDP ctor 内）
        Winsock 析构 007B1AB0 @007B1ABC、Winsock slot0=007B2780 @007B278C（删除析构器）—— **排除**
        UDP  ctor 007B2DB0 @007B2E2D（call 0x7B19C0 后初化 + 尾 mov eax,esi/ret）
             直接调用者 1 个：0052F456
        UDP  析构 007B2E50 @007B2E56（call 0x7C8B3D 释放）、UDP slot0=007B4170 @007B4176（删除析构器）—— **排除**
      atexit 排除：全 .text `push imm32; call 0x7C978A` 注册点 152 个；
        007B0D90 / 007B19C0 / 007B2DB0 / 007B1AB0 / 007B2780 / 007B2E50 / 007B4170 **均不在**注册集合
      静态实例排除：007F794C / 007F79BC / 007F7A6C 作为 dword 在 .data 中出现 **0 次**
        ⇒ 无全局静态对象，活表全部来自堆分配路径
      对象落点：构造后存入全局 **0x887628**（0052E3FD / 00685B26 / 0068618E 存 IPX；0052F461 存 UDP）

**④ ④ 与 ② 不同源 → `same_source = no`**


**⑤ 语义与实测一致**

```
逐项核数值，全中：007B3D75 ✓ cmp eax,-1 ✓ jne(gap=0) ✓ 失败 WSAGetLastError+cmp 0x2733+日志+ret ✓
      成功「继续缓冲摘除」✓；② vt 007F7A6C slot+0x40 槽 007F7AAC ✓ COL 0080EBE0 ✓ TD 0084E1C0 ✓
      ④ 007B2E2D ✓ 007B2DB0 ✓ 排除析构写点 ✓
      API 身份独立复核：sendto=0x7E1558 ✓ WSAGetLastError=0x7E1574 ✓
```

---


---

## 3 · API 身份独立复核（IAT 实测，用于「读写方向 / 形态」判据）

执行器点名的每个被调 API，本审计经 `DIRECTORY_ENTRY_IMPORT` 把 `.text` 里的 thunk 解到真实导入名：

| thunk | IAT 槽 | 真实导入 | 被本批哪行使用 |
|---|---|---|---|
| 0x7C89B0 | 0x7E1558 | **WSOCK32!sendto** | 007B13D0（007B14C6）、007B3AA0（007B3D75） |
| 0x7C89AA | 0x7E154C | **WSOCK32!recvfrom** | 007B13D0（007B1586） |
| 0x7C89BC | 0x7E156C | **WSOCK32!WSAAsyncSelect** | 007B1BC0（007B1BDB/007B1C1F）、007B3890（007B38C6） |
| 0x7C89A4 | 0x7E1554 | **WSOCK32!setsockopt** | 007B2630（007B2652/007B2690）、007B30B0（007B31B3） |
| 0x7C89CE | 0x7E1560 | **WSOCK32!gethostname** | 007B26D0（007B26DB）、007B3450（007B349D） |
| 0x7C899E | 0x7E157C | **WSOCK32!socket** | 007B30B0（007B30E4）、007B31E0（007B3234）、007B3450（007B35F8） |
| 0x7C8998 | 0x7E1580 | **WSOCK32!bind** | 007B30B0（007B315F）、007B31E0（007B3295）、007B3450（007B3653） |
| 0x7C8992 | 0x7E1584 | **WSOCK32!closesocket** | 007B31E0（007B32A0）、007B30B0（经 call [eax+4]）、007B1B80 |
| 0x7C897A | 0x7E1574 | **WSOCK32!WSAGetLastError** | 多行 |
| 0x4068E0 | — | 进程内**单字节 `c3 ret`**（日志被编译为空 stub） | 多行（执行器称「空 stub」，实测正确） |

⇒ 执行器所报 API 身份**无一错认**，故「把 send 写成 recv / 把 bind 写成 socket」这类方向性错误在本批**不存在**。

---

## 4 · ㉓ 析构器锚点审计：三张虚表的**全部**写点与判定

三张相关虚表（族结构实测）：

```
IPX      vt=007F794C  23 槽  COL=0080EA60  TD=0084D8F8  .?AVIPXInterfaceClass@@      chd base[1]=WinsockInterfaceClass
Winsock  vt=007F79BC  23 槽  COL=0080EAF8  TD=0084D8D0  .?AVWinsockInterfaceClass@@  chd numBase=1（根）
UDP      vt=007F7A6C  31 槽  COL=0080EBE0  TD=0084E1C0  .?AVUDPInterfaceClass@@      chd base[1]=WinsockInterfaceClass
```

每个 TD **只有 1 个 COL** ⇒ 每类各 1 张虚表 ⇒「小成员表顶替主虚表」在本族不成立。

全部写点（整镜像 dword 出现，逐个判定）：

| 虚表 | 写点(指令) | 所在函数 | 判定 | 依据 |
|---|---|---|---|---|
| 007F794C | 007B0DA4 | 007B0D90 | **构造器** | 先 `call 0x7B19C0`(Winsock 基类构造) 再装 vt，尾 `mov eax,esi; ret`；5 个直调者 |
| 007F79BC | 007B1A20 | 007B19C0 | **构造器** | 大体量字段初化 + 0x80 次表清零，尾 `mov eax,esi; ret`；2 个直调者(007B0D93/007B2DB3) |
| 007F79BC | 007B1ABC | 007B1AB0 | 析构器（排除） | 装 vt 后拆 3 个成员子对象 vt(0x7F7A3C) + 4 次 `call 0x7C8B3D` 释放 |
| 007F79BC | 007B278C | 007B2780 | **标量删除析构**（排除） | 同上，且尾 `test al,1; je; push esi; call 0x7C8B3D`（条件释放 this） |
| 007F7A6C | 007B2E2D | 007B2DB0 | **构造器** | `call 0x7B19C0` 后初化，尾 `mov eax,esi; ret`；1 个直调者(0052F456) |
| 007F7A6C | 007B2E56 | 007B2E50 | 析构器（排除） | 装 vt 后 `call 0x7C8B3D` 释放 |
| 007F7A6C | 007B4176 | 007B4170 | **标量删除析构**（排除） | 该函数即 UDP 虚表 **slot0**；装 vt 后 `call 0x7C8B3D` |

**atexit 排除**：全 `.text` 扫 `push imm32 ; call 0x7C978A` 得注册点 **152** 个；
`007B0D90 / 007B19C0 / 007B2DB0 / 007B1AB0 / 007B2780 / 007B2E50 / 007B4170` **均不在**该集合。
**静态实例排除**：三张表的 VA 作为 dword 在 `.data` 中出现 **0 次** ⇒ 无全局静态对象（不存在 ㉓ 的「atexit 全局析构器写的死表」形态）。

⇒ 12 行里 **没有一行**把 ④ 锚在析构器上。执行器自报的排除名单（CStreamClass 的 007B2E56/007B4176、007B2880/007B3110、007B1ABC/007B278C 等）与本审计逐个复核一致。

### 4.1 S17 的另一组 ㉓ 复核（CStreamClass / TClassFactory）

CStreamClass 有两个虚表（同 TD 0081FC30）：`007E5DAC`（15 槽，slot0=004A2990=**QueryInterface**，主表）与 `007E5D94`（5 槽次基表）。
本批 entry `004A2CD0` **只在主表** ⇒ 不存在「拿 5 槽小表顶主表」。
`007E5DAC` 三个写点：`004A285E`(构造器 004A2820) / `004A2889`(析构器 004A2880) / `004A3119`(删除析构 = 本表 **slot14** = 004A3110)。
三者均不在 152 个 atexit 注册集合。TClassFactory<VCStreamClass>/<SuperClass> 各只有 1 个 COL，写点各 1 处，均为构造器。

---

## 5 · ③b② 判定标准（本批实际用法，供复核）

本批 12 行的 ③b 全部落在 **③b② 可伪证返回约定**，判据统一为：

1. **被调函数的返回值域必须是多值状态码**，不是 `{0,1}` 布尔：
   S18 九行全部以 **WSOCK32 的 `SOCKET_ERROR = -1`** 为哨兵，`cmp eax,-1` + `jcc` 真分支；
   其中 `007B13D0`（sendto/recvfrom）、`007B3AA0`（sendto）还进一步 `cmp eax,0x2733`（WSAEWOULDBLOCK）做**三级判别**
   ⇒ 返回域至少三态，明确不是布尔。
2. **调用方真的拿它分支**，且两路动作不同（关 socket / 记日志失败 vs 继续组包·遍历·返回成功）。
3. **无 eax 覆写**：`call` 与 `cmp` 之间无写 `eax` 的指令（逐行核）。
4. 凡「布尔主输出 / 空指针判断」一律按 **③a** 排除，不计入 ③b：
   例如 `007B3450` 的 `call [eax+0x64]` 后 `test al,al/jne`、`007B3890` 的 `007B3895 call 0x7B1BC0` 后 `test al,al/je`、
   各构造函数入口的 `operator new` 空判断。

**与 D-46「bool 主输出不算」的关系**：D-46 排除的是「函数自身返回 bool 且无错误码契约」那一形态（`0045A640`）。
本批九行的 ③b② 证据不是函数自身的布尔返回，而是**被调 WSOCK32 API 的可伪证错误约定**驱动了真分支；
函数自身的布尔返回只是另加事实。故不适用 D-46 的排除，也不因此放宽。

---

## 6 · 对 ④ 的强弱分级（照实记，供 Lead 二次裁量）

| 强度 | 行 | ④ 依据 |
|---|---|---|
| 最强（派发点与构造点同函数） | **007B3450** | `0052F474 call [edx+0x3c]`（slot15）；同一函数 0052F456 处正构造 UDP 对象并存入 0x887628 |
| 强（真实派发点，槽号与 ② 一致） | **007B3890**(0052F4AC `call [eax+0x1c]` slot7)、**007B30B0**(0069C457 `[edx+0x5c]` slot23)、**007B31E0**(005D90A9 `[eax+0x68]` slot26)、**007B3AA0**(007775FF `[eax+0x40]` slot16)、**007B13D0**(同上 007775FF；该槽 IPX/UDP 两侧分别正是 007B13D0/007B3AA0) | 对象取自全局 **0x887628**（构造后落点） |
| 强（真实调用者） | **007B1BC0**(007B3895 `call 0x7b1bc0`)、**007B2630**(4 条：007B13AB/007B31BC/007B32EA/007B36A1) | 直调目标钉死 |
| 中（仅活虚表安装点） | **007B26D0** | 直调 0 条；`call [reg+0x44]`（slot17）全镜像 131 处、无一可钉到本类实例 ⇒ **本行 ④ 最弱**，执行器所写「+ 派发」我复现不出来 |
| 中（仅活虚表安装点） | **004A2CD0**、**006BEF10**、**006BF690**（S17 三行） | 直调 0 条；无该槽派发点，④ = 构造器装活表 |

⇒ 若 Lead 采「④ 必须有派发点或调用者」的严格读法，**只有 `007B26D0` 与 S17 三行**会掉；其余 8 行不受影响。
本审计的 PASS 沿用已入账 16 批的先例（ctor 安装点 = 活虚表见证），并把强弱显式列出以便一次性重裁。

