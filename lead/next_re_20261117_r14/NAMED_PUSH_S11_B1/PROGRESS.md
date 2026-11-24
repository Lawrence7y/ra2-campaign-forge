# PROGRESS — NAMED_PUSH_S11_B1

- [start] 读卡完毕；建目录 `NAMED_PUSH_S11_B1/{EVIDENCE,work}`；REPORT 骨架已落盘。
- [setup] SHA-256 实测 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` = 卡面期望。`core.py` 自检：`.text=[00401000,007E038D)`、insns=1,394,186、immkeys=107,892；阳性对照槽 `007E3ED0`→vt `007E3EBC`/slot5/`BuildingClass`，安装点 `0043B71F`(ctor)/`0043B9FA`/`0043BCFD`(dtor) 全复现审计已公布事实。
- [filter] S11 命中 31 → `p3b2_named=True` 29 → `fn_/sub_` 伪名 **0** → 取前 18（清单见 REPORT）。
- [trap③] 18/18 的 entry 全镜像只有 1 处 4B 引用、全在 `.rdata` 虚表槽（`.text` 内 0 处 ⇒ 无 direct caller、无立即数引用）。按类枚举全部 vtable 后确认每个 Locomotion 类有 **3 张表**：`COL.offset=0`(10/12 槽，装 [this+0]) / `COL.offset=4`(48 槽，装 [this+4]) / `COL.offset=0x18`(8 槽，装 [this+0x18])；后两张的 slot0 都是 `83 6C 24 04|18 E9 ...`（`sub [esp+4],N; jmp` 的 this 调整 thunk）。对照卡面给的副表 slot0（`004105E0`=`sub [esp+4],4; jmp 0x410260`、`00410580`=`xor al,al; ret 8`、`00410590`=`ret 4`）确认同型 ⇒ **只有 COL.offset==0 那 4 行落在对象主虚表**（004AF720 / 004B62C0 / 004B6470 / 0054DC60），其余 14 行只在副表 ⇒ ② 不成立。
- [row 1-4] 004AF610(②FAIL 副表0x18) / 004AF720(**②PASS 主表**，③PASS QI 多值，④PASS ctor 004AF540 @004AF5C2) / 004B5B70(②FAIL 副表4) / 004B6040(②FAIL 副表4) — 逐行 EVIDENCE 已落盘 004AF720。
- [row 5-8] 004B62C0(**四环齐**：②主表 slot6 @007E835C，③`call 0x55AA60`→`test`→`jl` E_POINTER+负HRESULT，④ctor 004B5AB0 @004B5ADD) / 004B6470(**四环齐**：②主表 slot0，③QI 多值，④同 ctor) / 004B64E0(②FAIL 副表0x18) / 004CCB40(②FAIL 副表4)。
- [row 9-12] 004CCC80 / 004CCFD0 / 004CF610（②FAIL 副表4，Fly 三行同表 007E89F4）/ 00514310(②FAIL 副表4)。
- [row 13-16] 00516CA0 / 00516E10（②FAIL 副表4，Hover 同表 007EACFC）/ 0054B1C0(②FAIL 副表4) / 0054DB50(②FAIL 副表0x18)。
- [row 17-18] 0054DC60(**四环齐**：②主表 slot0 @007ECE34，③`call 0x55A9B0`→`cmp eax,0x80004002`→`jne`，④ctor 0054AC40 @0054ACC3，㉓ 排除 dtor 0054DFA0) / 006622C0(②FAIL 副表4；③ 无站点)。
- [㉓] 每类都找到删除式析构器（`test byte [esp+8],1; call 0x7C8B3D`）：Drive `004B4D00`、DropPod `004B66F0`、Fly `004D03A0`、Hover `005172C0`、Jumpjet `0054DFA0`、Rocket `006635C0`。④ 一律锚构造器（`call 0x55A6C0` 基类 ctor，尾 `mov eax,esi; ret`），**未**用任何析构器内重装点。
- [④ 补强] 三个构造器各只有 1 个直接调用者，且都是 `push <size>; call 0x7C8E17(operator new); mov ecx,eax; call <ctor>` 的堆实例化点 ⇒ 活对象真实创建；4 个 entry 的 direct caller 均为 0 ⇒ 只能经活虚表派发。
- [产出] `delta.tsv` 4 行 [已证]；`EVIDENCE/ROW_*.txt` × 4（逐行地址+字节）；`base_rate.tsv`：18 / ②4 / ③b4 / ④18 / all_four 4 / rate 0.2222。
