# PROGRESS — S20 B1（每 5 行推进）

- 起工：读卡（80 行全文）→ 建目录 `NAMED_PUSH_S20_B1\{EVIDENCE,_work}` → REPORT 骨架落盘。
- 筛选：S20 `p3b2_named=True` 38 行，`fn_`/`sub_` 伪名 **0** 行，B1 = 升序前 18（`_work/filter_b1.py`）。
- 底座：`_work/core.py`（PE 段表 / RTTI COL→TD→名串 / **整表枚举 1212 张虚表** / 立即数安装点 + atexit ⑳㉓ / ③b② 机械站点 / 容器 Find 解析）。
- 方法要点：② 用虚表枚举（不靠回扫 maxk，避免 slot84/75/91 被截断）；④ 只取 **构造器**安装点且 **行外**；③ 逐行读体。

## 第 1-5 行

- `00423AC0` AnimClass::vslot23：② vt=`007E3354` slot#23（COL=`007FBA60` TD=`008182C8` `.?AVAnimClass@@`）；④ `0042201C` in ctor `00421EA0`（首条 `00421EAE call 0x5F3900` 基类构造，atexit=False，行外）。③ 体 4234 B：半径双层循环 head `0042400C`/`0042402A`，latch `00424269`/`0042424C`，边界 `cmp eax,[esi+0xC8]+0x33C` → `jg` 跳过，循环体内 **非栈写** `00424155 mov [edi+0x11E],al` ⇒ ③b④ 成立。
- `00427B50` AnimTypeClass::vslot40：② vt=`007E3608` slot#40；④ `00427731` in ctor `00427530`。③ FAIL：分支只为 `test eax,eax`（指针 NULL）与 `cmp eax,6`（状态枚举），无错误码约定。
- `00427D00` AnimTypeClass::vslot25：② slot#25；④ 同。③ FAIL：26 个站点全为 `00528A10`/`007C8D20`（new/free）的指针 NULL 判定 + 3 个仅栈写的 14 条循环。
- `00428800` AnimTypeClass::vslot5：② slot#5；④ `00427731`+`00427847`…（行内 `00428831` 已排除）。③ **FAIL（重要）**：站点 `00428814 call 0x5F9720` 的被调 **全函数只有 1 个 `ret`，且 ret 前 `005F993C xor eax,eax`** ⇒ 恒返 0、永不返负 ⇒ `0042881B jl` 失败分支**静态不可达**，返回约定不可伪证。
- `00428970` AnimTypeClass::vslot6：② slot#6；④ `00427731`。③ 待裁：29 B = 3 参数转发 + `test/jl/xor eax,eax/ret 0xc`，仅返回归一化（无额外动作）⇒ 按卡面「禁纯转发」判不成立。

## 第 6-10 行

- `00428C30` AnimTypeClass::vslot39：② slot#39；④ 同。③ FAIL：`004A3890` 返 0/指针（`n_rets=1, rets eax=edi`），分支是指针 NULL；两处 `cmp` 汇入同一 call 仅参数不同（细则#1 不达）。
- `00428EA0` AnimTypeClass::vslot8：② slot#8；④ `00427731`（行内 `00428EAD` 排除）。③ **③b② PASS**：`00428ED6 cmp eax,-1`→`00428ED9 je`（容器 0xB0F670，活表 `007E91EC`，`vt[#4]=004E0550` 于 `004E056F 83C8FF or eax,-1` + `004E0573 ret 4`）；命中路压缩写 `00428EFA mov [ecx+eax*4-4],edx` + 计数 `00428EE8`；第二处 `00428F1F/00428F22`（容器 0x8B4150，活表 `007EA2E4`，`vt[#4]=004EE1B0` 于 `004EE1CF`）。
- `004A7340` DiskLaserClass::slot23：② vt=`007E5FB8` slot#23；④ `004A7A3A` in ctor `004A7A30`。③ FAIL：倒计时 + 几何 + 状态枚举，无返回码约定；无回边（无循环）。
- `004A7C90` DiskLaserClass::slot8：② slot#8；④ `004A7A3A`（行内 `004A7C9D` 排除）。③ **③b② PASS**：`004A7CC6 cmp eax,-1`→`004A7CC9 je`（容器 0x8A0208，活表 `007E5EDC`，`vt[#4]=004A7FB0` 于 `004A7FCF 83C8FF` + `004A7FD3 ret 4`）；命中路压缩写 `004A7CEA`；随后基类析构 `004A7CFA call 0x4101F0`、按 delete 标志 `004A7CFF test byte [esp+0xC],1` + `004A7D07 call 0x7C8B3D`。
- `004C5A30` EMPulseClass::slot5：② vt=`007E87A8` slot#5；④ `004C537D` in ctor `004C5370`（行内 `004C5A54` 排除）。③ **③b② PASS**：`004C5A3B call 0x410380`（**读**封装，内部 `0041039E FF 50 0C`）→ `004C5A40 test`→`004C5A42 jl`；被调空参返 `00410389 b8 03400080`＝**E_POINTER 0x80004003**；成功路 `004C5A4F call 0x4101C0` 基类子对象构造 + 4 表安装 → 返 0。

## 第 11-15 行

- `004C5A80` EMPulseClass::slot6：② slot#6；④ `004C537D`。③ 待裁：29 B 转发 `0x410320`（**写**封装）+ 返回归一化，无额外动作 ⇒ 按「禁纯转发」不成立。
- `004C5AC0` EMPulseClass::slot8：② slot#8；④ `004C537D`（行内 `004C5AC4` 排除）。③ **③b② PASS**：`004C5B0D cmp eax,-1`→`004C5B10 je`（容器 0x8A3870，`vt[#4]` 于 `or eax,-1`）；命中路压缩 `004C5B31`；`004C5B41 call 0x4101F0` 基类析构；`004C5B46 test byte [esp+0xC],1` + `004C5B4E call 0x7C8B3D`。
- `005F44A0` AnimClass::slot84：② vt=`007E3354` slot#84（21 张表含该 entry，AnimClass 那张 slot#84）；④ `0042201C` in ctor `00421EA0`。③ **③b② PASS**：`005F44C5 cmp eax,-1`→`005F44C8 je`（容器 0xA8ECB8，**活表 `007E4F64`**（init `004E7D40` 写 `004E7D5D` 后才 `004E7D76 call 0x7C978A` 注册死表 `004E7D80`/`007E192C` —— ㉓ 成对已辨），`vt[#4]=0040CF00` 于 `0040CF1F 83C8FF` + `0040CF23 ret 4`）；命中路压缩 `005F44E9`；随后 `005F4503 call 0x4AEB10`（读管理器当前对象）+ `cmp eax,esi` + `005F4513 call 0x4AEB30`（清当前对象）。
- `005F4870` AnimClass::slot75：② slot#75；④ `0042201C`。③ FAIL：取包围盒（`call [edx+0xAC]`/`0x6D2140`/`call [edx+0x9C]`），`test esi,esi` 与 `cmp eax,6` 皆为 NULL/枚举判定，无返回码约定。
- `005F5390` AnimClass::slot91：② slot#91；④ `0042201C`。③ FAIL：返回 `[esp+0x10]` 状态枚举 0..4 / 5；多路分支全部汇入同一 `0x6E53A0` 仅事件号不同（细则#1 不达）。

## 第 16-18 行

- `005F5940` AnimClass::slot58：② slot#58（20 张表含该 entry）；④ `0042201C`。③ FAIL：主输出是 `al`（bool，1/0），D-46(A) 明示 bool 主输出不算。
- `005F9970` AnimTypeClass::slot7：② slot#7（10 张表）；④ `00427731`。③ 待裁：24 B 转发 `0x4103E0` + 返回归一化 ⇒ 按「禁纯转发」不成立。
- `0062D7A0` ParticleClass::slot5：② vt=`007EF954` slot#5；④ `0062B767` in ctor `0062B5E0`（行内 `0062D7C4` 排除）。③ **③b② PASS**：`0062D7AB call 0x5F5E80`（→ 内部 `005F5E8B call 0x410380` 读封装；空参 E_POINTER）→ `0062D7B0 test`→`0062D7B2 jl`；成功路 `0062D7BF call 0x5F3B50` 基类构造 + 4 表 + 2 个成员构造 → 返 0。

## 收口

- rows_checked=18；①18/18；②18/18（全为真虚表槽）；③b 成立 **7**；④18/18；四环齐全 **7**（1/7/9/10/12/13/18），rate 7/18=0.3889。
- ③ 待裁 3 行（5/11/17，纯转发+返回归一化）。
