# SUMMARY — NAMED_PUSH_AUDIT8（异族独立审计）

> 审计对象：`NAMED_PUSH_S12_B1\delta.tsv` 全部 **4 行**（DeepSeek 产）
> 审计身份：异族独立审计员（非 Hy4/S05、非 DeepSeek/S14）；只采信本次自己反汇编的字节
> 目标二进制：`ra2youli\gamemd.exe`，期望 SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，实测逐字一致
> 环境：Python 3.12.10 / capstone 5.0.7（`skipdata=True`）/ pefile 2024.8.26，无 venv、未 pip install
> ImageBase `0x400000`；`.text = [0x401000, 0x7E038D)`
> 判据：卡片五件事 + D-40 四环（①入口 / ②类属 / ③整体合同 / ④使用见证，②④不同源）；③ 只认整体合同真实且可伪证——**多值状态码算，{0,1} 布尔不算**。
> 独立性：自建 `work/audit_lib.py`（自写 PE 加载 + capstone），逐行脚本 `work/v_<entry>.py`；**未引用**执行器 `EVIDENCE/ROW_*.txt` 作证据。

## PASS / FAIL 统计

- **PASS：4 / 4**
- **FAIL：0 / 4**

## FAIL 逐条原因

无（4 行全部通过独立核验，无 FAIL entry）。

## 4 行逐行结论（每验完一行立刻落盘）

| entry | name | ② | ③b 形态 | ④ | ②④同源 | 语义相符 | verdict |
|---|---|---|---|---|---|---|---|
| 00442230 | BuildingClass::vslot91 | PASS (slot 007E4028/007E3EBC#91, RTTI .?AVBuildingClass@@) | 3b2 (Find -1) | PASS (0x43B71F 构造安装, 非atexit) | no | 是 | **PASS** |
| 00447210 | BuildingClass::vslot29 | PASS (slot 007E3F30/007E3EBC#29, RTTI .?AVBuildingClass@@) | 3b2 (mov ebx,eax; 返回集{0,4,5,7,8,0x1A,0x37}多值) | PASS (0x43B71F 构造安装, 非atexit) | no | 是 | **PASS** |
| 00447F10 | BuildingClass::vslot240 | PASS (slot 007E427C/007E3EBC#240, RTTI .?AVBuildingClass@@) | 3b2 (mov ebp,eax; 返回集{0,1,3,5,6,8,9}多值) | PASS (0x43B71F 构造安装, 非atexit) | no | 是 | **PASS** |
| 0044E8F0 | BuildingClass::vslot10 | PASS (slot 007E3EE4/007E3EBC#10, RTTI .?AVBuildingClass@@) | 3b2 (Find -1, 成员向量 DynamicVectorClass<InfantryClass*>) | PASS (0x43B71F 构造安装, 非atexit) | no | 是 | **PASS** |

四行共同结论：
- **②**：4/4 由 `.rdata` RTTI 数据链独立钉住——槽 007E3EBC 主表（槽 0=`0x00410260`），`[-4]=0x7FC360`(COL,sig=0) → TD `0x818D60` → `.?AVBuildingClass@@`；槽号 91/29/240/10 由字节复算，与线索 `vslotN` 逐行相等。
- **④**：4/4 靠活虚表派发（非 direct-only，direct caller 全为 0）——同一构造安装点 `0x43B71F mov [esi],0x7E3EBC`，所在函数 `0x43B680` 收尾 `mov eax,esi; ret 4`（返 this = 构造器），atexit 注册为空 ⇒ ㉓ 成对陷阱排除（④ 锚点不在析构器）。
- **②④ 不同源**：② 锚 `.rdata` RTTI 数据链，④ 锚 `.text` 构造安装指令；两通道独立 ⇒ same_source=no（4/4）。
- **语义方向**：4 行 delta 第 4 列的读写/返回方向均与实测一致，无方向写反、无子型标错。

## 专门结论：`00447210` / `00447F10` 的「返回值先搬进 ebx/ebp 再判」③ 形态

Lead 已裁定 ③ 只认函数整体合同真实。本次独立确认两行的搬移形态**真实且可伪证**：

| 行 | 搬移形态（自反汇编字节） | 被调返回约定（独立枚举全部 ret） | 判定 |
|---|---|---|---|
| 00447210 | `call 6FFEC0`@447267 → `mov ebx,eax`@44726C → `cmp ebx,8`@44726E → `jne`@447271；搬移后比较，ebx 无覆写 | atlas size 1842，12 个 ret，常量集 **{0x0,0x4,0x5,0x7,0x8,0x1A,0x37}**；rc8 上抛@447279、rc4 实质工作@447286、rc5 实质工作@44736B | **多值状态码，非 {0,1} 布尔 ⇒ ③b② 成立** |
| 00447F10 | `call 6FC0B0`@447FD4 → `mov ebp,eax`@447FD9 → `test ebp,ebp`@447FDB → `jne`@447FDD；判 ebp，无覆写 | atlas size 3208，32 个 ret（全 ret 0xC），常量集 **{0x0,0x1,0x3,0x5,0x6,0x8,0x9}**（0=成功@6FCD26）；非零 `mov eax,ebp` 原样上抛@448053，零路继续 slot255/314 | **多值状态码（虽含 1，但另有 3/5/6/8/9 多个失败码），非 {0,1} 布尔 ⇒ ③b② 成立** |

- 「先搬进 ebx/ebp 再判」只是编译器把返回值从 eax 移到 callee-saved 寄存器后比较；**形态真实**：call 紧接 mov reg,eax，再 test/cmp reg，中间无该寄存器覆写，调用方确实拿搬移后的值分支。
- **可伪证性**：两个被调的返回常量集合都由字节独立枚举（分别 12 / 32 个 ret），均为**多值状态码集合**（7 个互异值），满足「多值状态码算」；均**不是 {0,1} 布尔**（脚本 `is {0,1} bool? False`），符合卡片「{0,1} 布尔不算」的排除口径。
- 两路动作真不同（上抛 vs 实质处理 / 原样上抛 vs 后续判定），符合 D-40 ③b②「失败返回什么、成功返回什么、调用方哪条指令拿它分支、两路动作不同」的全部要素。故这两行的 ③ 判定为 PASS。
