# -*- coding: utf-8 -*-
import os
CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_S10"
COV  = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"

# 25 new one_line_semantics. Each: [functional sentence] + [D-42 ③b condition + verified offsets].
SEM = {
"0045A560":"动态数组 SetCapacity：为新容量分配后备缓冲、逐元素拷贝旧数组、按需释放旧缓冲并改挂 Items/Count，成功返回 true。合同闭合 ③b④ 完整循环 I/O：0x45A5AE 处 mov edx,[esi+4]/inc eax/mov [edi+eax*4-4],edx/jl 回边读-写-推进齐备；0x7C8E17 分配、0x7C8B3D 释放，ret8。",
"0045A610":"动态数组 FindItemIndex：按指针线性扫描 Items 至 Count，命中返回下标、未命中返回 -1（ret4）。合同闭合 ③b② 可证伪返回约定：0x45A623 处 cmp [ecx],esi/inc eax/add ecx,4/jl 回边比对，未命中走 0x45A62F 的 or eax,-1；Count 取 +0x10。",
"004D4200":"任务计时/就绪判定入口：按多道闸决定是否触发默认动作并返回 1 或随机化帧间隔。合同闭合 ③b① 多闸互斥：+0x5A4 计时路径、+0x674 空即 0x4D4217 处 push 0x80004003(E_POINTER)、vt[+0x10] 谓词、+0xB4==-1 则 vt[+0x484] 并 ret1，否则 0x65C7E0 随机段（0x4D424F 起）。",
"004D4280":"按任务阶段号四路跳转的调度器：阶段取自 +0xBC，经边界检查后索引跳表执行各阶段动作。合同闭合 ③b① 跳表可核：0x4D42B4 处 cmp eax,3 上界守卫、0x4D42BD 处 jmp [eax*4+0x4D4B04]；四目标全在 .text，阶段返回 0x3C(0x4D451B)/0x2D(0x4D477A) 等互斥出口。",
"004D4B20":"飞行器任务守卫链：先按类型(WhatAmI)与关联对象多级条件过滤，再择一执行动作并随机化收尾。合同闭合 ③b① 多路互斥：0x4D4B33 取 vt[+0x2C]、0x4D4B38 处 sub edi,0xF 比类型 15、+0x2B4 的 vt[+0x2C]==6、0x70D0D0(0xE) 资格判定，四结局互斥，尾 0x65C7E0 随机。",
"004D4CB0":"飞行器守卫链的近亲分派（90 条指令）：同型类型/资格过滤后落到三个互斥动作出口。合同闭合 ③b① 多路可核：0x4D4CC8 处 sub edi,0xF 比类型 15、+0x2B4 的 vt[+0x2C]==6、0x70D0D0(0xE)；三出口 0x4D4D39/0x4D4D26/0x4D4D86 互斥，尾 0x65C7E0 随机。",
"004D4DC0":"单位格相关任务判定：读地图类型字节、经虚调用与取格链定位目标格、再按状态字节二次分流。合同闭合 ③b① 多路守卫：byte[+0x390] 起 → vt[+0x1C8] → 0x703590 → 0x5657A0(GetCellAt) → vt[+0x480] 链，随后 byte[+0x68E] 分流；全函数 170 指令 13 处 jcc。",
"004D5070":"单位对邻格/目标的循环搜索：按 8 路 for 循环逐项取 CellStruct、取格、比对状态位，命中即触发动作。合同闭合 ③b④ 完整循环 I/O：0x4D5118 循环头、0x4D519C 处 jl 回边，读 +0x158 状态位、0x89F688 坐标表、0x5657A0 取格、0x47C520 校验，inc/cmp 推进边界。",
"004D5350":"单位复杂任务决策（186 指令/18 jcc）：多层门控串联后落到互斥的动作链。合同闭合 ③b① 多路可核：byte[+0x6D4] 闸、vt[+0x39C] 谓词、vt[+0x2C] 类型选择(=15)、0x70D0D0(0xE) 资格、byte[+0xEC3] 状态位；各路 vt[+0x480]/vt[+0x1E8]/vt[+0x200]/vt[+0x1EC] 结局互斥。",
"004D6AA0":"单位邻格扩展搜索（555 指令/30 调用）：对 8 邻格逐格取坐标、取格并校验，命中则执行动作并返回计数。合同闭合 ③b④ 完整循环 I/O：0x4D6F7A 循环头、0x4D6FF9 处 jl 回边，读 +0x158、0x89F688 坐标表、0x5657A0 取格、0x47C520 校验，inc/cmp 推进；尾 0x65C7E0 随机。",
"004D9290":"单位目标表遍历与重定位：先做资格/接口检查(0x80004002、0x7DC720)，再遍历候选表逐项推进并回写计数。合同闭合 ③b④ 完整循环 I/O：0x4D93B9 循环头，从 +0x58C 表按 +0x598 计数逐项 inc/cmp/jl 推进；动作走 vt[+0x480]，越界失败有可证伪返回。",
"004DA2C0":"按内部状态字显式分派：状态 0/1 各带独立动作链并回写状态位。合同闭合 ③b① 多路可核：0x4DA2CC 处 sub eax,0/je 判态 0、0x4DA2D1 处 dec eax/jne 判其它；态 0 在 0x4DA2FF 写 +0xBC=1、态 1 在 0x4DA2E6 写 +0xBC=0，各态动作链经 +0x5A4/+0x5D4 门控而不同。",
"004DA530":"FootClass 每帧 AI 主入口（722 指令/98 jcc/31 调用）：以本类虚派发 +0x5C 为钩子，串联多道守卫与动作链。合同闭合 ③b① 多路守卫可核：call [vt+0x5C]、+0x5A4 计时路径、+0x674 归属指针(空则 E_POINTER 0x7DC720)、byte[+0x390] 地图类型闸、0xA8ED84 当前帧参与周期计算，分支动作互斥。",
"004DDF90":"飞行器按状态字分派的收尾：状态 0/1 各调用不同虚方法族并清理队列。合同闭合 ③b① 多路可核：+0xBC 取自 0x4DDF97，sub 0/je 0x4DDFDB(态0)调 vt[+0x53C]，dec/jne 0x4DDFA9(态1)调 vt[+0x1E8]/vt[+0x1EC]；+0x2B4 目标存在为另一道闸，两路动作互斥。",
"0051F3E0":"单位任务的五道互斥闸：归属状态、资格函数、类型与两个标志字节全过关才执行动作并转后处理。合同闭合 ③b① 多路可核：+0x6C0 的 byte[+0xEC2]、0x70D0D0(0xE)、+0x2B4 的 vt[+0x2C]==6、+0x520 的 byte[+0x1577] 与 byte[+0x1701]；通过后 vt[+0x480]/vt[+0x1E8] 动作。",
"005B2FD0":"任务状态转移：当前态 0x1C 且入参 5 时保持不变，否则一次性重写任务字段组。合同闭合 ③b①+③b③：0x5B2FD9 处 cmp eax,0x1C + 0x5B2FE2 处 cmp eax,5 双条件短路；0x5B2FE9 起写 +0xAC=arg、+0xB4=-1、+0xB8=0、+0xBC=0、+0xC0/+0xC4 帧戳，0x5B3021/0x5B302A 处自 +0xC8 写帧戳/参数/清零；时间戳取 0xA8ED84，字段组固定即内存形状断言。",
"005B3060":"任务主分派器：按当前任务号经跳表调用对应处理虚方法并刷新帧时间戳。合同闭合 ③b① 跳表可核：0x5B30B8 处 cmp eax,0x1F 上界守卫、0x5B30C1 处 jmp [eax*4+0x5B34E8]；表 0x5B34E8 共 32 槽、目标全在 .text，各 case 调 vt[+0x204] 等虚方法，时戳统一取 0xA8ED84。",
"005B3570":"排队任务出列转当前任务：把 +0xB4 排队任务搬到 +0xAC，清排队位并刷新时间戳；无排队则可证伪返回。合同闭合 ③b① 状态转移+返回：0x5B3579 处 cmp eax,-1 / je 0x5B35CC 为可证伪空返回；非空分支写 +0xAC、+0xB4=-1、+0xB8、+0xBC、+0xC0/+0xC4，并自 +0xC8 写帧戳三字段(取 0xA8ED84)。",
"005B35E0":"任务排队的多路过滤：态 0x1C+参数 5、态 0x13、参数 -1 三种情况直接跳过，否则写排队槽后按参数字节虚调用分派。合同闭合 ③b① 多路可核：0x5B35ED 处 cmp ecx,0x1C + cmp eax,5、0x5B35F7 处 cmp ecx,0x13、0x5B35FC 处 cmp eax,-1；通过则写 +0xB4/+0xB8，再按 arg 调 vt[+0x200]/vt[+0x1EC]。",
"005B3650":"任务队列三路互斥搬运：态 0x1C+参数 5 或态 0x13 跳过；否则按排队槽是否非空决定 0xB4→0xB0 覆盖当前，或双向交换 0xB0←0xAC/0xAC←arg。合同闭合 ③b① 多路可核：0x5B365B 处 cmp eax,0x1C + cmp esi,5、0x5B3665 处 cmp eax,0x13、0x5B366A 处 cmp edx,-1；三路 ret 0xC 出口互斥。",
"005B36B0":"排队任务落地为当前任务的转移：+0xB0 有效则搬到 +0xAC、清空 +0xB0/+0xB8 并 ret al=1，否则 ret al=0。合同闭合 ③b② 可证伪返回约定：0x5B36B6 处 cmp eax,-1 / je 0x5B36D7 为失败出口；成功路径 0x5B36BB/0x5B36C1/0x5B36CB 写 +0xAC、+0xB0=-1、+0xB8=0，al 真值可证伪。",
"006B1850":"SlaveManager 指针动态数组 SetCapacity：分配后备缓冲、逐元素拷贝旧数组、按需释放旧缓冲并改挂 Items/Count。合同闭合 ③b④ 完整循环 I/O：0x6B189E 处 mov edx,[esi+4]/inc eax/mov [edi+eax*4-4],edx/jl 回边读-写-推进齐备；0x7C8E17 分配、0x7C8B3D 释放，ret8。",
"006B1900":"SlaveManager 指针动态数组 FindItemIndex：按指针线性扫描至 Count，命中返回下标、未命中 -1(ret4)。合同闭合 ③b② 可证伪返回约定：0x6B1900 起取 +0x10=Count、+4=Items，0x6B1913 处 cmp [ecx],esi/inc/add ecx,4/jl 回边，未命中 0x6B191F 处 or eax,-1。",
"006B8660":"SpawnManager 指针动态数组 SetCapacity：分配/复用后备缓冲、逐元素拷贝、按需释放旧缓冲并改挂 Items/Count。合同闭合 ③b④ 完整循环 I/O：0x6B86AE 处 mov edx,[esi+4]/inc eax/mov [edi+eax*4-4],edx/jl 回边读-写-推进齐备；0x7C8E17 分配、0x7C8B3D 释放，ret8。",
"006B8710":"SpawnManager 指针动态数组 FindItemIndex：按指针扫描至 Count，命中返回下标、未命中 -1(ret4)。合同闭合 ③b② 可证伪返回约定：0x6B8723 处 cmp [ecx],esi/inc eax/add ecx,4/jl 回边，未命中 0x6B872F 处 or eax,-1；Count 取 +0x10。",
}

# read on-disk coverage rows (exact name/grade/subsystem/evidence_path)
lines=open(COV,encoding='utf-8').read().split('\n')
rows={}
for ln in lines[1:]:
    if not ln.strip(): continue
    c=ln.split('\t')
    if len(c)>=6: rows[c[0]]=c

BAN=['槽语义未证','弱信号','线索','未定']
out=[]
out.append('entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path\tname_kind\t旧grade→新grade')
stats={'n':0,'minlen':9999,'maxlen':0,'badgrade':0,'badban':0,'namechanged':0}
ev=[]
for e,sem in SEM.items():
    c=rows[e]
    entry,subsys,name,oldsem,grade,evp = c[0],c[1],c[2],c[3],c[4],c[5]
    # self-checks
    if grade!='[已证]': stats['badgrade']+=1
    if any(b in sem for b in BAN): stats['badban']+=1; ev.append('BAN '+e)
    L=len(sem); stats['minlen']=min(stats['minlen'],L); stats['maxlen']=max(stats['maxlen'],L)
    if L<80: ev.append('SHORT '+e+' '+str(L))
    # name_kind: slotN vs semantic name
    nk = 'slotN' if ('slot' in name and name.split('::')[-1].startswith('slot')) else 'semantic_name'
    out.append('\t'.join([entry,subsys,name,sem,grade,evp,nk,grade+'→'+grade]))
    stats['n']+=1
    ev.append('OK %s len=%d grade=%s name=%s nk=%s'%(e,L,grade,name,nk))

with open(os.path.join(CARD,'coverage_delta.tsv'),'w',encoding='utf-8') as f:
    f.write('\n'.join(out)+'\n')
with open(os.path.join(CARD,'EVIDENCE','SEMANTICS_CHECK.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(ev)+'\n')
print('STATS',stats)
print('rows written',stats['n'])
