# SUMMARY — NAMED_PUSH_AUDIT9（异族独立审计）

> 审计对象：`NAMED_PUSH_S12_B2\delta.tsv` 全部 **6 行**（DeepSeek 产）
> 审计身份：异族独立审计员（非 Hy4/S05、非 DeepSeek/S14）；只采信本次自己反汇编的字节
> 目标二进制：`ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，实测逐字一致
> 环境：Python 3.12.10 / capstone 5.0.7（`skipdata=True`）/ pefile 2024.8.26，无 venv、未 pip install
> ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`
> 判据：卡片五件事 + D-40 四环（①入口 / ②类属 / ③整体合同 / ④使用见证，②④不同源）；③ 只认整体合同真实且可伪证——**多值状态码算，{0,1} 布尔不算**；㉓ 成对陷阱（④ 锚点落在析构器 ⇒ FAIL）。
> entry 取法：读 `NAMED_PUSH_S12_B2\delta.tsv` 第 1 列（`entry`），数据行第 2–7 行，共 6 行，subsystem 全为 S12。取出的 6 entry：`00453E20 / 00465300 / 004728E0 / 004729C0 / 004CA3C0 / 004CA770`。
> 独立性：自建 `work/audit_lib.py`（自写 PE 加载 + capstone `skipdata=True`），逐行脚本 `work/v_<entry>.py`；**未引用**执行器 `EVIDENCE/ROW_*.txt` 作证据。
> 用户特别要求：独立确认 ② 用的是**主表不是小成员表**（主表 slot0=0x00410260）；④ 锚点**不在析构器里**（㉓）——尤其 004729C0 / 004CA770 两行（entry 自身是删除式析构器，执行器把 ④ 改锚同类构造器 0x471807 / 0x4C991A）。

## PASS / FAIL 统计

- **PASS：6 / 6**
- **FAIL：0 / 6**

## 6 行逐行结论（每验完一行立刻落盘）

| entry | name | ② | ③b 形态 | ④ | ②④同源 | 语义相符 | verdict |
|---|---|---|---|---|---|---|---|
| 00453E20 | BuildingClass::vslot5 | PASS (slot 007E3ED0/007E3EBC#5, COL007FC360/TD818D60 .?AVBuildingClass@@, 主表 slot0=00410260) | 3b2 (call 70BF50 → cmp eax,ebx(=0) → jl；失败负 HRESULT/成功 0) | PASS (0x43B71F 构造安装, ctor 43B680 ret this, 非 atexit; 非 dtor 43BCF0) | no | 是 | **PASS** |
| 00465300 | BuildingTypeClass::slot6 | PASS (slot 007E4588/007E4570#6, COL007FC618/TD8193A8 .?AVBuildingTypeClass@@, 主表 slot0=00410260) | 3b2 (call 716DC0 → test eax → jl；失败负 HRESULT/成功 0) | PASS (0x45E558 构造安装, ctor 45E520 ret this, 非 atexit; 非 dtor 45E580) | no | 是 | **PASS** |
| 004728E0 | CaptureManagerClass::slot6 | PASS (slot 007E4B58/007E4B40#6, COL007FCB60/TD81B6C8 .?AVCaptureManagerClass@@, 主表 slot0=00410260) | 3b2 (call 410320 → mov edi,eax → test → jl；E_POINTER/内层 HRESULT 多值) | PASS (0x471807 构造安装, ctor 4717D0 ret this, 非 atexit; 非 dtor 4729C0) | no | 是 | **PASS** |
| 004729C0 | CaptureManagerClass::slot8（删除析构） | PASS (slot 007E4B60/007E4B40#8, COL007FCB60/TD81B6C8 .?AVCaptureManagerClass@@, 主表 slot0=00410260, 唯一引用) | 3b2 (call [edx+0x10] Find → cmp eax,-1 → je；命中压缩) | PASS (0x471807 同类构造器安装, ctor 4717D0 ret this, 非 atexit; **非 dtor 4729C0**) | no | 是 | **PASS** |
| 004CA3C0 | FactoryClass::slot6 | PASS (slot 007E88E8/007E88D0#6, COL800610/TD822290 .?AVFactoryClass@@, 主表 slot0=00410260) | 3b2 (call 410320 → test eax → jl；E_POINTER/内层 HRESULT 多值) | PASS (0x4C991A 构造安装, ctor 4C98B0 ret this, 非 atexit; 非 dtor 4CA770) | no | 是 | **PASS** |
| 004CA770 | FactoryClass::slot8（删除析构，两容器） | PASS (slot 007E88F0/007E88D0#8, COL800610/TD822290 .?AVFactoryClass@@, 主表 slot0=00410260, 唯一引用) | 3b2 (两站点 Find → cmp eax,-1 → je；两容器命中压缩) | PASS (0x4C991A 同类构造器安装, ctor 4C98B0 ret this, 非 atexit; **非 dtor 4CA770**) | no | 是 | **PASS** |

四行共同结论 + 两行析构器专门结论：
- **② 主表确认（6/6）**：每行都由 `.rdata` RTTI 数据链独立钉住——COL(sig=0) → TD → `.?AV<Class>@@`，槽值 4B = entry，槽号经 `(slot_addr-vtable_base)/4` 复算与线索自洽；**每张主表 slot0 都实测 = `0x00410260`**（用户报告的"4 张主表 slot0 全部=00410260"独立复核成立：BuildingClass 007E3EBC / BuildingTypeClass 007E4570 / CaptureManagerClass 007E4B40 / FactoryClass 007E88D0）。两行删除析构器的 entry 在非 .text 中只有**唯一** dword 引用（0x7E4B60 / 0x7E88F0，正是各自主表的 slot8），未被误挂到小成员表。
- **③b 形态（6/6 = 3b2）**：4 行反序列化载入（0x70BF50 / 0x716DC0 / 0x410320×2）为"失败负 HRESULT、成功 0"的具名多值状态约定；2 行删除析构器为 Find "未命中 -1、命中下标"多值约定。全部有明确 `call → (mov/test/cmp) → jcc`，比较与跳转间无判据寄存器覆写，调用方两路动作不同（上抛/跳过 vs 读回/压缩）；非 {0,1} 布尔、非 ③a、非栈写均来自调用方。
- **④ 使用见证（6/6）**：全部靠活虚表派发链（构造安装点把主表装入活对象 [obj+0]），`direct callers of entry = []`（不靠 direct-only）；所在函数收尾 `mov eax,esi/ret` 返 this = 构造器，atexit 注册为空。**②④ 不同源（6/6）**：② 锚 `.rdata` RTTI 数据链，④ 锚 `.text` 构造安装指令 ⇒ same_source=no。
- **语义方向（6/6）**：delta 第 4 列的读写/返回方向均与实测一致，无方向写反、无子型标错。

## FAIL 逐条原因

无（6 行全部通过独立核验，无 FAIL entry）。

## 两行删除式析构器专门结论（004729C0 / 004CA770）——用户重点

用户明确要求独立确认两点，结论如下：

**① ② 用主表不是小成员表**：
- `004729C0`：slot `0x007E4B60` 属于 vtable `0x007E4B40`（CaptureManagerClass 主表，slot0=`0x00410260`），RTTI `.?AVCaptureManagerClass@@`，slot#8；非 .text 中 entry 的唯一 dword 引用就是 `0x7E4B60`。是主表，非小成员表。
- `004CA770`：slot `0x007E88F0` 属于 vtable `0x007E88D0`（FactoryClass 主表，slot0=`0x00410260`），RTTI `.?AVFactoryClass@@`，slot#8；非 .text 中 entry 的唯一 dword 引用就是 `0x7E88F0`。是主表，非小成员表。

**② ④ 锚点不在析构器里（㉓）**：
- 两行 entry 自身**确为删除式析构器**（④ 若锚在此即 ㉓ FAIL）：
  - `004729C0`：体内 `0x4729CD` 同虚表重装，`0x472A3E/0x472A67/0x472A96 call 0x7C8B3D`(operator delete ×3)、`0x472A5A call 0x4101F0`(基类析构)。
  - `004CA770`：体内 `0x4CA774 mov dl,1`(删除标志)、`0x4CA776` 同虚表重装，`0x4CA84E/0x4CA877/0x4CA8A6 call 0x7C8B3D`(operator delete ×3)、`0x4CA86A call 0x4101F0`(基类析构)。
- 执行器已把 ④ **改锚同类构造器**：`004729C0 → 0x471807`（ctor `0x4717D0`，`mov eax,esi; ret 0xc` 返 this，atexit 空），`004CA770 → 0x4C991A`（ctor `0x4C98B0`，`mov eax,esi; ret` 返 this，atexit 空）。本次逐字节独立确认这两个安装点都**在构造器内、不在析构器内**，㉓ 成对陷阱排除。

**关于"析构语义是否构成 ③b②"的专门判断**（卡片对 S14 4 行析构所问，本批 2 行同类）：
- **哨兵确被检查并分支**：`004729C0` 有 `cmp eax,-1`@`0x4729F6` + `je 0x472A28`@`0x4729F9`；`004CA770` 有 `cmp eax,-1`@`0x4CA7AD`/`0x4CA806` + `je 0x4CA7DF`/`0x4CA838`。两行 cmp→je 间均无 eax 覆写。
- **判断依据**：③b② 要的是"函数整体合同真实且可伪证"，不是"函数必须是正常方法"。这两行的被调是 **Find 的 -1/下标多值返回约定**，两条出口字节（`or eax,-1` 与命中下标）独立可枚举，调用方拿它 `cmp/je` 分支且两路动作实质不同（跳过 vs count--+前移压缩），压缩写是**调用方对全局数组的非栈写**（非被调内部写、非 ③a）。析构函数体内的这次 Remove 恰好是"检查返回码再决定动作"的真实合同，故**构成合法 ③b②**；析构语义本身不构成否证理由。不因执行器已产出而放行——而是独立字节核验后确认其成立。
- 附带确认 `004CA770` 是两个**不同**容器（`DynamicVectorClass<FactoryClass*>`@0xA83E30 与 `DynamicVectorClass<AbstractClass*>`@0xB0F720，两个 Find，调用参数互异），非"多路同一 call"复用。
