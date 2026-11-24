# W175 · 0x8871E0 全局对象溯源 / 字段写点 / 两个绕过开关

卡号 W175｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`｜ImageBase 0x400000
纪律依据 R13_COMMON §6（19 条）；R14_COMMON.md 不存在。
工具：Python 3.12.10 + capstone 5.0.7（`skipdata=True`，1,394,120 条指令）+ pefile + audit_lib。

## 结论表

| # | 结论 | 分级 | 证据 |
|---|---|---|---|
| 1 | `[0x8871E0]` 的对象来自 `new(0x18c0)` + thiscall `call 0x665650`（ecx=this，eax=this 返回）；3 写点＝成功/失败NULL/销毁NULL | [已证] | `EVIDENCE/t1_callsite_52BA60.txt`、`t1_ctor_665650_head.txt`、`t1_cleanup_6BE1C0.txt` |
| 2 | 构造器 `0x665650` = **RulesClass::RulesClass**（9175 B / 1621 指令，唯一调用者 `0x52BAD1`）；析构 `0x667A30` 被**直接调用**（非虚） | [已证] | `EVIDENCE/t1_ctor_665650_extent.txt`、`t1_compare_ctor.txt`、`t1_step8.py` |
| 3 | **无 vftable、无 RTTI**：构造器对 `[obj+0]` 只写 `mov [esi],0xf`（数据值，非代码指针）；析构器不写 `[esi+0]`；全节 `.?AVRulesClass@@`（及任何含 Rule 的 `.?AV*`）0 命中；§909-1 真机 `[P]=0x0F`。⇒ 卡片「vftable→RTTI」前提对**此对象被否证** | [已证] | `EVIDENCE/t1_esi0_rtti_link.txt`、`t1_rtti_allsecs.txt`、`t1_vft_rtti_raw.txt` |
| 4 | `+0x1808` 写点 = **2**：`0x6677B3`（构造默认，`89 9E 08 18 00 00`＝`mov [esi+0x1808],ebx`）与 `0x66CFDC`（INI，`mov [esi+0x1808],eax`） | [已证] | `EVIDENCE/t2_disp_1808_172c.txt`、`t2_doublechannel.txt` |
| 5 | `+0x1808` INI 键 = **`RadApplicationDelay`**（字符串 `0x83B31C`），段 `[Radiation]`（`0x7F0C88`→`0x839E80`），函数 `0x66CF70`=RulesClass::Read_Radiation（thiscall `mov esi,ecx`） | [已证] | `EVIDENCE/t2_ini_readers.txt`、`t3_iat.txt` |
| 6 | `+0x172C` 写点 = **2**：`0x6675B0`（构造默认 `mov [esi+0x172c],0x280`＝640）与 `0x66BAA3`（INI，`mov [esi+0x172c],eax`） | [已证] | 同 #4、`t2_ini_readers.txt:109-117` |
| 7 | `+0x172C` INI 键 = **`CrateRadius`**（`0x83AC5C`），段 `[CrateRules]`（`0x7F0C80`→`0x839E9C`），函数 `0x66B900` | [已证] | `EVIDENCE/t3_global_writes.txt:109-117`、`t3_iat.txt` |
| 8 | `[0xA8ED6B]`(byte) 写点 = **3**：`0x52F63E`=0、`0x5A922F`=1（暂置）、`0x5A95A1`=恢复保存的旧值（A2 moffs） | [已证] | `EVIDENCE/t3_bytechannel_full.txt`、`t3_final_verify.txt:16-75` |
| 9 | `[0xB73550]`(dword) 写点 = **3**：`0x77780E`=0(ebx, 关停)、`0x777CD6`=CreateWindowExA 返回值(HWND)、`0x777D7E`=CreateWindowExA 返回值(HWND, "Yuri's Revenge") | [已证] | `EVIDENCE/t3_bytechannel_full.txt`、`t3_final_verify.txt:76-113` |
| 10 | 开关语义候选：`A8ED6B`=「强制绘制/绕过状态剔除」位（save-set-restore 惯用法）；`B73550`=主窗口 HWND，0=无窗口⇒绕过剔除 | [静态推断] | 写值轨迹 + 台账 §924-3/§924-4 门控语义 |

## 核心数字（给审计）

1. **RTTI 字符串地址 = 不存在（RulesClass 非多态）**；复算：`grep -a '\.?AVRulesClass@@' gamemd.exe` = 0；`t1_esi0_rtti_link.txt` 构造器 `[esi+0]` 仅 1 处写入且值 0xF；§909-1 真机 `[P]=0x0F`。
2. **`+0x1808` 写点 2 / `+0x172C` 写点 2**；复算：`t2_doublechannel.txt` 字节通道 `89 86/9E … 08 18 00 00` 与 `89 … 2C 17 00 00` / `C7 86 2C 17 00 00`。
3. **`[A8ED6B]` 写点 3 / `[B73550]` 写点 3**；复算：`t3_bytechannel_full.txt` 6 个模式命中（88 1D / C6 05 / A2 / 89 1D / A3×2），与双通道反汇编对账。

## 复算命令

```
python work\t2_step1.py        # 全 .text skipdata=True 扫 disp 0x1808/0x172C
python work\t2_doublechannel.py# 字节通道独立扫写点
python work\t3_bytefull.py     # 两个全局的穷举写模式（含 A2/A3 moffs）
```
