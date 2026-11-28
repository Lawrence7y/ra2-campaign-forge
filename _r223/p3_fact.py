# -*- coding: utf-8 -*-
"""R223 p3：FACT_INDEX V604 -> V605，只在 F29.limitations 追加 R223 实测段。"""
import hashlib, os, json
ROOT='/home/t628/projects/ra2-campaign-forge'; TIER=ROOT+'/lead/next_re_20261117_r14'
OLD=TIER+'/R17_R131_FACTINDEX_V604/FACT_INDEX.tsv'
NEWD=TIER+'/R17_R131_FACTINDEX_V605'; NEW=NEWD+'/FACT_INDEX.tsv'
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
raw=open(OLD,'rb').read(); h=hashlib.sha256(raw).hexdigest()
ck('W1 旧 V604 303399 B / sha 22cfe5c4',len(raw)==303399 and h.startswith('22cfe5c4'),(len(raw),h[:16]))
ck('W2 旧 CR == 0',raw.count(b'\r')==0)
txt=raw.decode('utf-8'); lines=txt.split('\n')
ck('W3 57 行 + 末段空',len(lines)==58 and lines[-1]=='',len(lines))
rows=[l.split('\t') for l in lines[:57]]
ck('W4 每行 5 列',all(len(r)==5 for r in rows))
f29=[r for r in rows if r[0]=='F29'][0]
L0=len(f29[4].encode())
ck('W5 F29 lim > 70000 B',L0>70000,L0)
APP=('**【R223 实测·0x7c6620 定性为网格 3x3 邻域冲突检查器（死代码）＋ 状态块 12 B 四偏移 ＋ 四张 4 项对齐表与 8 项 nibble 表成对同构；statement 与 grade 均不改】** '
'R223 用 `_r223/` 13 个脚本、**124 断言 / 0 FAIL**（`m7_final` 32、`m9_tables_final` 16、`m19_facts` 13、`m13_reach2` 12、`m20_audit_recheck` 10、`m17_proof` 8、`m12_indirect` 7、`m10_grid` 6、`m11_live` 6、`m14_tbl874` 4、`m2_window` 3、`m16_grid2` 2、`m18_grid3` 2），'
'在现盘 `ra2bench/gamemd.exe`（sha256 `73201cc0…f3fcf67476`）上重算：'
'① **`0x7c6620` 是网格记录 3x3 邻域冲突检查器，不是 ACM 帧更新器**（R222 待办① 关闭）：函数体 `[0x7c6620,0x7c672a)` 0x10a B；'
'记录寻址 `rec = dword[0xb0b6ec] + (arg1 + arg2*dword[0x8759a4])*8`（`0x7c662a mov eax,[ebp+0xc]` / `0x7c6633 imul eax,dword[0x8759a4]` / '
'`0x7c663a add eax,[ebp+8]` / `0x7c663d lea esi,[esi+eax*8]`，`esi` 由 `0x7c662d mov esi,[0xb0b6ec]` 装入），**步长取内存全局不是立即数**；'
'8 B 记录只碰 `[rec+0]`（dword 值）与 `[rec+4]`（dword 标志：`test ...,1`@`0x7c667d`，`or ...,2`@`0x7c66c7`/`0x7c66dc`），全函数**无** `[rec+5..7]` 访问，'
'与分配器 `0x6b2756..0x6b2764` 只清零 `[rec+0]`(dword)+`[rec+4]`(byte)+`[rec+5]`(byte) 完全一致；'
'9 组邻域由 `edi`/`ecx` 初值 `0xffffffff` + 回边 `cmp reg,2`/`jl`（`0x7c670b/0x7c670c/0x7c670f` 内层、`0x7c6715/0x7c6716/0x7c6719` 外层）给出，'
'`(0,0)` 那组由 `0x7c664f mov eax,edi` / `0x7c6651 or eax,ecx` / `0x7c6653 test eax,eax` / `0x7c6655 je` 跳过；'
'阈值 `0xc`（`cdq`+`xor eax,edx`+`sub eax,edx` 取绝对值各 2 处，`cmp eax,0xc` 在 `0x7c6696`/`0x7c66ad`）；'
'bit0 置位且 `arg3 != 0`（`0x7c6686 cmp dword[ebp+0x14],0` / `0x7c668a jne`）⇒ **直接返回 0 不修**；bit0 清零 ⇒ 按 `arg2 == 1`（`0x7c66b2 cmp dword[ebp+0x10],1`）'
'把邻居改成 `本值 − 0xc`（`0x7c66bf..0x7c66c5`）或 `本值 + 0xc`（`0x7c66d4..0x7c66da`）并 `or dword[rec+4],2` 标记已修，随后**自递归**处理被拖动的邻居'
'（`0x7c66ee call 0x7c6620`，4 实参 + `0x7c66f3 lea esp,[esp+0x10]`）；3 个 `ret`（`0x7c66a2`/`0x7c670a` 前 `xor eax,eax`，`0x7c6729` 前 `mov eax,1`）⇒ 返回值只有 0/1。'
'② **`0x7c6620` 在文件里无任何外部引用 ⇒ 死代码**：全 `.text` `e8/e9` rel32 指向它**仅 1 条 = 0x7c66ee 自递归**；全文件 dword 字面量 `0x7c6620` **0 次**、'
'`68 20 66 7c 00`（push imm32）**0 次**；审计员另测 0f8x rel32 / eb·7x rel8 / `ff 15`·`ff 25` 各 **0**，`.rdata`/`.data`/`.detour` 内 rel32 各 **0**，'
'RVA `0x3c6620` 与段相对 `0x3c5620` 各 **0**，无导出、relocs stripped。⇒ 与 `0x7c62ac`（解包器）、`0x7c6270`（reset8）、`0x7c6730`（reset4）、`0x7c6752` 整族（块1）同属死区；'
'文件里活跃的音频路径只有块2 族（`0x7c7371` / 3 份解码展开）+ 状态清零器 `0x7c7350`。'
'③ **`0x7c7371` 的状态块 `&[ebx+0x7d0]` 只 4 个偏移共 12 B**（R222 待办② 关闭）：`+0`（dword 值，4 位点 `0x7c73c7`/`0x7c778c` 读、`0x7c798b`/`0x7c75c3` 写）、'
'`+4`（word，4 位点 `0x7c73c9`/`0x7c778e` 读、`0x7c798d`/`0x7c75c5` 写）、`+6`（dword，2 位点 `0x7c7b61` 读 / `0x7c7d5b` 写）、`+0xa`（word，2 位点 `0x7c7b64` 读 / `0x7c7d5e` 写）；'
'映射回对象 `obj+0x7d0`/`obj+0x7d4`/`obj+0x7d6`/`obj+0x7da`，与清零器 `0x7c7350` 写的四槽 `[eax]`(dword)/`[eax+4]`(word)/`[eax+6]`(dword)/`[eax+0xa]`(word) **一一对应** ⇒ 两声道各 6 B（int32 预测器 + uint16 step），与 R222 自洽。'
'`0x7c7350` 唯一调用点 `0x7c2a74`；`0x7c7371` 恰 2 个调用点 `0x7c24a2`/`0x7c2557`。窗口扫描另见 `[ebx+0x7fc]` 两条（`0x73c51c`/`0x73c5b2`）**属另一对象**，不并入本块。'
'④ **四张 4 项对齐表同构，且与各自 8 项 nibble 表成对**（R222 待办③ 关闭）：每族 `4t − 8t` 恒 **0x20**（块1 `0x7c6b58`/`0x7c6b38`、块2A `0x7c7778`/`0x7c7758`、'
'块2B `0x7c7b3c`/`0x7c7b1c`、块2C `0x7c7f10`/`0x7c7ef0`），8 项表与 4 项表相对块1 的位移**完全相同**（`0xc20`/`0xfe4`/`0x13b8`）。'
'逐 stub 屏蔽（imm32 + disp32 置 0）后**跨表同索引 4/4 全等**：k=0 组 13 B `55c1ed0433db0bede9…`，k=1/2/3 组各 15 B `83ed0c/08/04 55c1ed04 33db 45 e9…`；'
'把 imm8 也屏蔽后全库只剩 **2 个图案**（13 B 组 4 个成员 + 15 B 组 12 个成员）⇒ 四张表是同一模板的四份独立展开。'
'唯一结构差异是 stub0 之后的**对齐填充**：块1 `90`（1 B）、块2A `8bff`（2 B）、块2B/2C `8d4900`（3 B）。'
'4 项表各有 **1 条** `jmp dword ptr [ebx*4 + 表址]` 引用（指令起始 `0x7c67d0`/`0x7c73ef`/`0x7c77b6`/`0x7c7b86`，表址 disp32 起点 = 指令起始 +3，ModRM `9d`），表址字面量全文件各 **1** 次；'
'三个非零项的跳转目标全部落在本族 8 项表内：`stub1 → idx6` / `stub2 → idx4` / `stub3 → idx2`（四族 **12/12** 一致，`8-2k` 律），`stub3` 结束地址 +1 恰为本族解码器入口（**4/4**）。'
'⑤ **`.data` 的 320 dword 单调串 `[0x874700,0x874c00)` 不是指针表**（反控）：320 个值全落 `.text`、单调、步长 `0x204..0x20a`、首 `0x7b15ec` 末 `0x7d9d27`；'
'但 ① 对 `[0x874700,0x874c00)` **逐值**搜 disp32 命中 **0**；② `%4==0` 仅 **91/320**；③ 前驱字节为 int3/ret 的 **0/320** ⇒ 数据巧合，不是跳转表也不是函数指针数组。'
'审计中出现的 `0x7c6789`/`0x7c6990`/`0x7c637a`/`0x7c6581` 等「指向音频簇的 dword」全部落在这一串里，4 个只有 1 个是真实指令起点，**不可当函数指针证据**。'
'⑥ **网格描述符四全局与消费者隔离**：`0x8759a0 ← dword[0x87f918]+1`（行，`0x6b2784`）、`0x8759a4 ← dword[0x87f914]+1`（列/步长，`0x6b27ec` 与 `0x6b2b3b`）、'
'`0x8759a8 ← dword[0x87f90c]`（`0x6b27fe`）、`0x8759ac ← dword[0x87f910]`（`0x6b2790`）；分配字节 = `(d[0x87f918]+1) * (d[0x87f914]+1) * 8`'
'（`0x6b2731 lea esi,[eax+1]` / `0x6b2730 inc ecx` / `0x6b2734 imul esi,ecx` / `0x6b2737 lea edx,[esi*8]`），清零循环跑 `esi−1` 次（`0x6b274b lea edx,[esi-1]`），基址 `0xb0b6ec`（BSS，文件内无字节）。'
'引用计数 `0x8759a0` **4** / `0x8759a4` **18**（16 读 2 写）/ `0x8759a8` **10** / `0x8759ac` **10** / `0xb0b6ec` **32**；**活跃块2 族（`0x7c7371..0x7c7f20`）对这四个全局与网格基址引用数均为 0** ⇒ 网格记录与 ADPCM 解码是两条独立数据流，`0x7c6620` 是唯一同时读 `0xb0b6ec` 与 `0x8759a4` 的消费者。'
'⑦ **反控 5 条**：eax 基址同窗口扫描（vs ebx 5 位点）；把 imm8 一并屏蔽后图案数 **4→2**；320 dword 串三条独立否证（无 disp32 / 非 4 对齐 / 非函数入口）；'
'`0x7c7371` 内部 `[ebx+X]` 全枚举得 5 个 distinct（`0x0`/`0xa`/`0x7c80f6`/`0x87bc90`/`0x87bd90`），只有前两个 <0x20 属结构字段，其余三个是 `.text` 段内常量地址（不是结构偏移）。'
'⑧ **跨家族 / 自错**：exec `#584`（hy4，**39 回合 / 20.37′**，`[OVERTIME: 20.37\' vs 2.0\']`）26 断言 26/0 全 PASS，其「`[ebx+0x7fc]` 属另一对象」判断由主会话复算采纳；'
'审计 `#585`（hy4 audit，**18 回合 / 18.43′**，`[OVERTIME]`）A1–A8 全 PASS、B4 **口径有误但数字对**（表址 disp32 起始 ≠ `jmp` 指令起始，差 3；ModRM 应为 `9d` 非 `8d`）、B5 独立判同构、C1–C3 全 PASS；'
'跨家族审计 `#587`（deepseek audit，**24 回合 / 8.05′**）三争议点全部独立复现，并**订正主会话措辞**：不是「16 个 stub 全部字节相同」，而是「跨表同索引相同（4 组 × 4）」——主会话以 `m20_audit_recheck.py` 复算**成立并采纳**；'
'其独立发现「表址位移与 handler 位移不等差（+0xc1f vs +0xc20）」亦复算成立。`#586`（deepseek 首发）状态 `cancelled`（0 回合 / 15.9′），如实记录、不计入结论。'
'自错 2 条 **0 条进结论**：E1 `p1_four.py` 的 W2 断言「R14 原文无 CRLF」与 CR=1081 口径矛盾（同 R222 E2，不影响写入）；'
'E2 `m9_tables_final.py` 首版把 stub0 之后的间接 `jmp` 计入 stub 体，导致 `padding` 判据错位（已改为「stub0 体后紧跟 `ff 24 9d` 指令，其后再量 pad」）。'
'**边界**：本条不改 F29 的 statement 与 grade；`coverage.tsv` / `function_atlas.tsv` 仍不可读；'
'`0x7c6620` 的记录值量纲与 `arg3`/`arg4` 真实语义、`[rec+4]` bit2..bit31 的其它使用方、`dword[0x87f90c]`/`dword[0x87f910]` 语义仍未取得。')
ck('W6 无 tab','\t' not in APP)
ck('W7 无 CR/换行','\r' not in APP and '\n' not in APP)
ck('W8 无双引号','"' not in APP)
ck('W9 以句号结尾且 >7000 B',APP.endswith('。') and len(APP.encode())>7000,len(APP.encode()))
newlim=f29[4]+APP
ck('W10 lim 只增不减',len(newlim.encode())>L0,len(newlim.encode()))
f29[4]=newlim
newtxt='\n'.join('\t'.join(r) for r in rows)+'\n'
nb=newtxt.encode('utf-8')
ck('W11 新字节 = 旧 + 追加段',len(nb)==len(raw)+len(APP.encode()),(len(nb),len(raw)+len(APP.encode())))
ck('W12 新 CR == 0',nb.count(b'\r')==0)
ck('W13 除 F29 外 56 行逐字节不变',all(lines[i]=='\t'.join(rows[i]) for i in range(57) if rows[i][0]!='F29'))
if fails:
    print('[ABORT]',fails); raise SystemExit(1)
os.makedirs(NEWD,exist_ok=True)
assert not os.path.exists(NEW)
open(NEW,'wb').write(nb)
chk=open(NEW,'rb').read()
ck('W14 回读一致',chk==nb)
print('[写入] %s bytes %d -> %d sha %s -> %s'%(NEW,len(raw),len(chk),h[:16],hashlib.sha256(chk).hexdigest()[:16]))
json.dump(dict(old_sha=h,new_sha=hashlib.sha256(chk).hexdigest(),old_bytes=len(raw),new_bytes=len(chk)),open(ROOT+'/_r223/p3.json','w'),indent=1)
