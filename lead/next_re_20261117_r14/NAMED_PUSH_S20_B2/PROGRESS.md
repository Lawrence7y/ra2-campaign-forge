# PROGRESS — S20 B2（升序第 19..36 行，每 5 行推进）

- 起工：读卡（80 行全文）→ 建目录 `NAMED_PUSH_S20_B2\{EVIDENCE,_work}` → 先写 REPORT 骨架落盘 → 逐行核完立即落 `EVIDENCE/`。
- 筛选：S20 `p3b2_named=True` 38 行，`fn_`/`sub_` 伪名 **0** 行（S20 的 named 全是 `Class::slotN`/`vslotN` 与真名，无地址式伪名），B2 = 升序第 19..36（`_work/filter_b2.py` → `b2_rows.json`）。
- 底座：复用 S20_B1 的 `_work/core.py`（PE 段表 / RTTI COL→TD→名串 / **整表枚举 1212 张虚表** / 立即数安装点 + atexit ㉓ / ③b② 机械站点 / 容器 Find 解析）。
- 三已知陷阱逐行排查：① 流方向按 `0x410320=写出(+0x10)` / `0x410380=读入(+0xC)` 复算（本批 00630090/006457A0 均为**写出**）；② ④ 锚点全部落在构造器安装点、非析构器、非 atexit；③ 主虚表 slot0=00410260，本批 vt 均为主表非小成员表（唯一 5 槽的 007F3780=ClassFactory 真接口，其 slot0=006BEFD0，未误当成员表）。

## 第 19-23 行

- `0062D830` ParticleClass::slot122：② vt=`007EF954` slot#122（123 槽表，大槽号靠整表枚举钉住）；④ `0062B767` in ctor `0062B5E0`。③ FAIL：分支全是对 `0x75F230` 返回的方向枚举（0..7，`cmp eax,2/6/4/3/7`）做 switch，无错误码/失败常量；`0x6D2140` 的 `al` 在下一 call 前未测且其 eax 被 `0x75F230` 覆写（eax 覆写陷阱）。
- `0062D9A0` ParticleClass::slot8：② slot#8；④ `0062B767`（行内 `0062D9A4` 排除）。③ **③b② PASS**：`0062D9EB call [0xA83DC8+0x10]`→`0062D9EE cmp eax,-1`/`0062D9F1 je`（零间隔）；命中路 `0062DA12 mov [ecx+eax*4-4],edx` 压缩 + `0062DA1E jl`；`or eax,-1` @004E9F2C；收尾 `call 0x5F3B80` 基类析构 + delete 标志释放。
- `0062E070` ParticleSystemClass::Update_B：② **FAIL**（真名但整表枚举 0 命中：无虚表槽指向本 entry，是 direct-only 方法，direct=00630233）⇒ 不出 delta。
- `0062FE90` ParticleSystemClass::slot10：② vt=`007EFB9C` slot#10；④ `0062DD16` in ctor `0062DC50`。③ **③b② PASS**：成员容器 `[this+0xBC]`（vtable `007E9D84` 于 0062E244 装入）`0062FEBB call [edx+0x10]`→`0062FEBE cmp eax,-1`/`0062FEC1 je`（零间隔）+ 压缩写 `0062FED9` + `0062FEE2 jl`。
- `00630090` ParticleSystemClass::slot6：② slot#6；④ 同 `0062DD16`。③ **③b② PASS（流写出）**：`006300A2 call 0x410320`（内部 ff5010=Write，空参 0041032B 返 E_POINTER 0x80004003）→`006300A7 test`/`006300A9 jl`（零间隔）；成功路按计数逐元素 `call [ecx+0x10]` 写出 + 回边；失败路带错误码收尾。

## 第 24-28 行

- `006447E0` ParticleSystemTypeClass::slot5：② slot#5；④ `0064419C` in ctor `006440A0`。③ FAIL：站点 `006447EB call 0x5F9720`，被调**全函数 1 个 ret、ret 前 005F993C xor eax,eax ⇒ 恒返 0**，`006447F2 jl` 失败路静态不可达，返回约定不可伪证（同 S20_B1 的 00428800 负结果）。
- `00644960` ParticleSystemTypeClass::slot8：② vt=`007F00A8` slot#8；④ `0064419C`（行内 `00644966` 排除）。③ **③b② PASS**：容器 0xA83D68 `0064499A call [edx+0x10]`→`0064499D cmp eax,-1`/`006449A0 je`（零间隔）+ 压缩 `006449C1` + `jl`；`or eax,-1`@004EF00F；`call 0x5F7400` 基类析构 + delete 释放。
- `00644F50` ParticleTypeClass::slot25：② vt=`007F0188` slot#25；④ `00644CF4` in ctor `00644BE0`。③ FAIL：巨型配置装载函数，6 站点全是 `0x528A10`（容器查）/ `0x7C8D20`（free）/ `0x7C8E17`（new）的指针 NULL 判；3 个循环体 0 非栈写；主输出 `al` bool（00645405/00645417）⇒ D-46(A) 不算。
- `006457A0` ParticleTypeClass::slot6：② slot#6；④ `00644CF4`。③ **③b② PASS（流写出）**：`006457B3 call 0x5F9950`（→0x410320 Write，空参 E_POINTER）→`006457B8 test`/`006457BA jl`（零间隔）；成功路按 [ebx+0x2C8] 一次写出 + [ebx+0x2BC] 每 3 字节逐条 `call [ecx+0x10]`（`add edi,3`/`jl` 回边）。
- `00645950` ParticleTypeClass::slot8：② slot#8；④ `00644CF4`（行内 `00645956` 排除）。③ **③b② PASS**：两个注册表 0xB0F670 / 0xA83D98 各一个 Find -1 站点（`0064598D`/`006459D6` 零间隔 cmp eax,-1+je）+ 压缩写 + `jl` 回边；`or eax,-1`@004E056F/004EEDAF；基类析构 + delete 释放。

## 第 29-33 行

- `006BF090` T_TClassFactory_VWaveClass__::slot3：② vt=`007F3780` slot#3（COM 工厂 5 槽真接口，slot0=006BEFD0 非 `00410260`，已核非小成员表）；④ `006BEFC9` in ctor `006BEFC0`。③ FAIL：主体是 COM CreateInstance——NULL 出参 `0x80070057` / 已初始化 `0x80040110` / `0x7C8E17` new 的 **operator new 分配 NULL 判**（B1 明示不作合同）；唯一 `test edi,edi/jge` 是 `call [eax]`（接口方法）的 HRESULT 判但不是可伪证常量路径。状态/分配检查，非 ③b。
- `00749F30` VoxelAnimClass::slot23：② vt=`007F6318` slot#23；④ `00749434` in ctor `007493B0`（首条 007493BE call 0x5F3900）。③ **③b④ PASS**：8 邻域扫描——读 `0074A385 call 0x5657A0` 取格内对象→判 `0074A395 test al`（0x4838E0）→**循环体内非栈写** `0074A48F c6861e01000000 mov byte [esi+0x11E],0`（堆对象，非栈槽、非被调内写）→推进 `0074A56A inc edi`/`0074A56B cmp edi,8`/`0074A572 jl 0x74A329` 带边界检查。
- `0074B050` VoxelAnimTypeClass::slot25：② vt=`007F6548` slot#25；④ `0074AE6B` in ctor `0074AD80`。③ FAIL：配置装载，11 站点全是 `0x528A10`/`0x514D0`/`0x7C8E17` 的指针 NULL/分配判；0 回边。
- `0074B810` VoxelAnimTypeClass::slot5：② slot#5；④ `0074AE6B`。③ FAIL：`call 0x5F9720` 恒返 0，`0074B822 jl` 失败路不可达（同 006447E0）。
- `0074B8D0` VoxelAnimTypeClass::slot6：② slot#6；④ `0074AE6B`。③ FAIL（从严）：29B 纯转发壳 `call 0x5F9950`→`test/jl`→`xor eax,eax`/`ret`，除返回归一化外无自身动作 ⇒ 卡面禁 ③a 纯转发（同 S20_B1 的 00428970 等待裁行）。

## 第 34-36 行

- `0074BA30` VoxelAnimTypeClass::slot8：② slot#8；④ `0074AE6B`（行内 `0074BA36` 排除）。③ **③b② PASS**：两个注册表 0xB0F670 / 0xA8EB28 各一个 Find -1 站点（`0074BA6D`/`0074BAB6` 零间隔）+ 压缩写 + `jl` 回边；基类析构 `call 0x5F7400` + delete 释放。
- `0074CE50` VeinholeMonsterClass::slot23：② vt=`007F66A8` slot#23；④ `0074C443` in ctor `0074C420`。③ FAIL：状态机——1 个 4 路跳转表（`jmp [eax*4+0x74D414]`）但各例是状态转移（写 [esi+0xCC]/[esi+0xE8] 等），不满足「每路可单独验证」的可伪证合同；唯一站点 `call 0x426630` 返回剩余计数（非失败常量），`test eax/jne` 是数量判；2 个循环为 jmp 驱动，无「读→判→非栈写→推进」齐备 ⇒ ③b 四形态皆不达。
- `0075F7D0` WaveClass::slot6：② vt=`007F6BF4` slot#6；④ `0075EA3F` in ctor `0075E950`。③ FAIL：`0075F7E2 call 0x410320`（写出）**返回值未测**——紧接 `mov ecx,[edi+0x200]` 后进入 `call [edx+0x10]`，机械筛把后续虚拟写的 `test eax/jl` 误当站点；首写出调用无零间隔判据；循环体写由被调完成（0 非栈写）。本行从严不计。

## 收口

- rows_checked=18；①18/18；②17/18（第 21 行 Update_B 无虚表槽）；③b 成立 **8**；④17/18（随 ②）；四环齐全 **8**（行 20/22/23/25/27/28/30/34），rate 8/18=0.4444。
- 与 S20_B1 对比：B1 ②18/18、③b7、四环 7；B2 多一行无虚表槽（Update_B），③b 由 7 升至 8。
- selfcheck：delta 格式/地址引用/reason 去重/四环标题/base_rate 自洽 **全通过，FAIL=0**。
