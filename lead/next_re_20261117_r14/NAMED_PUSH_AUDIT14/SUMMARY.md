# NAMED_PUSH_AUDIT14 — 异族独立审计 SUMMARY

## 范围
- 来源：`NAMED_PUSH_S11_B1/delta.tsv` 全部 4 行（004AF720 / 004B62C0 / 004B6470 / 0054DC60）。取法：从第 2 行起取全部 4 个 entry（6 列 `entry subsystem name one_line_semantics grade evidence_path`），表头不计。
- 目标镜像：`D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe`，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（本地核对一致）；ImageBase 0x400000，`.text=[0x401000,0x7E038D)`。
- 工具：Python 3.12.10 + capstone 5.0.7（`skipdata=True`）+ pefile 2024.8.26。delta.tsv / REPORT.md / EVIDENCE/ROW_*.txt 只当地址线索；结论全部来自本审计员对 gamemd.exe 字节的独立反汇编（`work/auditlib.py`、`work/probe_*.py`）。

## 判定
- **报告行数 4 / PASS 4 / FAIL 0**

## FAIL 逐条原因
- 无（本批无 FAIL）。

## 专门结论：4 行是否真落在主表 + ④ 锚点是否在删除式析构器

### 主表归属（执行器自报「18 行仅 4 行槽落在主表」）—— 独立确认成立
本批 S11 Locomotion 为多继承族：每类 1 张主表（COL.offset=0，装到 `[this+0]`）+ 2 张子对象接口副表（COL.offset=4 / 0x18，slot0 为 `sub [esp+4],imm; jmp` this 调整 thunk）。三类的表结构与 4 行槽位独立复核如下：

| 类 | 主表 | COL / offset / TD 类名 | 主表 slot0 首字节 | 副表(offset=4 / 0x18) |
|---|---|---|---|---|
| DriveLocomotion | 0x7E7F7C | 0x7FFEB0 / 0 / 0x820248 `.?AVDriveLocomotionClass@@` | 538b5c240855（真函数） | 0x7E7EB0 / 0x7E7E8C |
| DropPodLocomotion | 0x7E8344 | 0x8000A8 / 0 / 0x8202F8 `.?AVDropPodLocomotionClass@@` | 538b5c240855（真函数） | 0x7E8278 / 0x7E8254 |
| JumpjetLocomotion | 0x7ECE34 | 0x804CF0 / 0 / 0x829648 `.?AVJumpjetLocomotionClass@@` | 538b5c240855（真函数） | 0x7ECD68 / 0x7ECD44 |

- 004AF720 = 主表 0x7E7F7C 的 slot0；004B6470 = 主表 0x7E8344 的 slot0；004B62C0 = 主表 0x7E8344 的 slot6（0x7E835C=表基+0x18，实测整表 dump slot6 值即本 entry）；0054DC60 = 主表 0x7ECE34 的 slot0。
- 三张表的 COL 全部 `sig=0, offset=0`，且由构造器安装在 `[this+0]`；主表 slot0 首字节 `53 8b 5c 24 08 55` 是真函数 prologue，而副表 slot0 是 `83 6c 24 04 04 / 18 + e9 jmp` 的 this 调整 thunk（例：0x4B4D90 `sub [esp+4],4; jmp 0x4AF720`）。四行槽均在主表，**无一落在副表**。主表判定成立。

### ④ 锚点是否在删除式析构器里 —— 独立确认：不在
- 四行的 ④ 使用见证均为「构造器安装主虚表 + operator new 实例化」：004AF720→ctor 0x4AF540 安装点 0x4AF5C2 / new 0x6C403E；004B62C0 与 004B6470→ctor 0x4B5AB0 安装点 0x4B5ADD / new 0x6C493E（slot0 行 ctor 尾 0x6C494C）；0054DC60→ctor 0x54AC40 安装点 0x54ACC3 / new 0x6C41C1。
- 三类确有 deleting destructor（DriveLocomotion 0x4B4D00 / DropPod 0x4B66F0 / Jumpjet 0x54DFA0，均含 `test byte [esp+8],1` + `call 0x7C8B3D` operator delete），且它们在 0x4B4D03 / 0x4B66F3 / 0x54DFA3 重装主虚表。但本审计员独立确认：这些析构器重装点**没有被用作任何一行的 ④ 锚点**；且对三个 entry 的全镜像直接调用扫描仅命中副表 jmp thunk（非 call 调用点），④ 来源只能是构造器活虚表派发。㉓ 成对陷阱不成立。
- 结论：④ 与 ② 不同源（② 用虚表槽+COL/TD，④ 用构造器安装点+new 链），四项判定均 PASS。

## 交付物
- `VERDICT.md`：逐行五项结论 + 地址字节
- `verdict.tsv`：4 行，表头 `entry subsystem verdict ring2_at ring3b_form ring4_at same_source reason`
- `SUMMARY.md`：本文件
