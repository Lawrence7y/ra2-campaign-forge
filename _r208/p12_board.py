# -*- coding: utf-8 -*-
"""R208 p12：STATUS_BOARD 收口。开局 262 行 >= 260 ⇒ 先归档最早 2 段到 BOARD_ARCHIVE（归档 CR 保持 2952），
再给第 208 轮追加本轮收口段（CR 保持 0、总行 <= 300）。
"""
import os,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=ROOT+'/lead'; TIER=LEAD+'/next_re_20261117_r14'; BASE=LEAD+'/R17_LEAD_BASELINE'
BOARD=TIER+'/STATUS_BOARD.md'; ARCH=TIER+'/BOARD_ARCHIVE.md'
def backup(path,tag):
    b=open(path,'rb').read()
    bak=BASE+'/'+os.path.basename(path)+'.before_r208_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    return b
def commit(path,nb,exp_cr,tag):
    assert nb.count(b'\r\n')==exp_cr,(tag,nb.count(b'\r\n'))
    tmp=path+'.r208tmp'; open(tmp,'wb').write(nb); os.replace(tmp,path)
    assert open(path,'rb').read()==nb
    d=open(path,'rb').read()
    print('OK %-26s %d B  CR %d  lines %d'%(os.path.basename(path),len(d),d.count(b'\r\n'),d.count(b'\n')))

# ---- 归档最早 2 段 ----
b=backup(BOARD,'boardc'); a=backup(ARCH,'archc')
assert b.count(b'\r\n')==0 and a.count(b'\r\n')==2952
lines=b.decode('utf-8').split('\n')
starts=[i for i,l in enumerate(lines) if l.startswith('## ')]
assert len(starts)>=3, starts
cut=starts[2]
moved='\n'.join(lines[:cut])+'\n'
rest='\n'.join(lines[cut:])
nb_arch=a+b'\n'+moved.encode('utf-8')
assert nb_arch.count(b'\r\n')==2952
commit(ARCH,nb_arch,2952,'arch')
nb_board=rest.encode('utf-8')
assert nb_board.count(b'\r\n')==0
commit(BOARD,nb_board,0,'board-trim')
print('归档段首行: %s'%lines[0][:60])
print('归档字节 %d'%len(moved.encode()))

# ---- 追加本轮收口段 ----
ADD = '''
**R208 收口段（T 形态双编码订正 · AircraftClass −8 收官 · V590）.**

**订正（推翻本轮上文第 2 条的措辞，不动数字）.** T 形态 **101** 条不是一种编码：**100 条** `83 6C 24 04 <imm8> E9`（mdisp ∈ {4,24,36,40,44}）+ **1 条** `81 6C 24 04 <imm32> E9`（COL `0x7fb310` / `.?AVAircraftClass@@` / mdisp **1728** / vftable `0x7e2250` / slot0 `0x41c670` / `81 6C 24 04 C0 06 00 00 E9 13 7C FF FF` / jmp `0x414290`）。imm8 有符号上限 127 < 1728 ⇒ 编译器用 imm32，是编码选择的后果。**立即数 == mdisp 仍 101/101、E9 目标 == 本类主视图 slot0 仍 101/101**。

**新证 1（thunk 级常量性）.** 100 条 A83 只落 **21** 个 thunk 地址（`0x4105e0` 一址供 **75** 个 COL），每址立即数唯一 21/21、组内 mdisp 唯一（0 冲突）⇒ 等式是 thunk 级常量的推论，不是逐 COL 独立性质。

**新证 2（分母口径警告）.** `.text` 锚点 `83 6C 24 04`=**67**、`81 6C 24 04`=**3**（0x41c670/680/690，imm 全 1728），与 slot0 口径 100/1 **不可混用**：三处里只有 0x41c670 是某个 COL 的 slot0，另两处是同一 vftable `0x7e2250` 的 slot1/slot2（前三槽即三连 81 thunk，第四槽 0x41b6a0）。主视图 954 条 **0 条** thunk；2 条 `8B 44 24 04` 开头（`CD` 0x4790e0 / `ProgressScreenClass` 0x643e80）经体首指令判为真函数体。

**取得（QM9 ⑥ 收官）.** AircraftClass m=8 视图体内 −8 调整 = **`add esi, -8` @0x41bc8f**（入口 0x41bc30 +0x5F，401 B/135 条），**不是 lea**；InfantryClass `lea esi,[edi - 8]` @0x522a8e、UnitClass @0x74612e（各入口 +0x2E，112 B/39 条）。Infantry↔Unit 体差 **10** 处 = 栈帧 2 / 参数 1 / 字段 1 / 内部跳转 6，无一处落 this 调整位。反控：Aircraft +0x400 窗口 −8 命中 **0**。

**跨家族（§2.12 规则 D 全复算）.** #531（hy4，1 回合 / **7.47' vs 预算 5.0 ⇒ OVERTIME 如实记**）自报 15/15 PASS 并落 `_r208/x1_tform.json`（101 条 A/B 明细、3 条 I 形态、mismatch/jmp_fail 皆空）；其自述曾用旧引用判据起过后台探测得 `vftable=None`，已声明作废。#532（deepseek，26 回合 / 3.57' / 无 OVERTIME）9 断言 **1 FAIL** = 「统一 83」表述（订正句全采纳），另两条加强（thunk 级常量、锚点口径）实测成立。主会话 **55 断言 0 FAIL**（v1 13 / v2 11 / v3 12 / v4 7 / v5 12）。

**自错 5 组（0 条进结论）.** TD 名串多判 NUL／thunk 判据把 slot0 地址当函数地址读／`.data` 引用榜未排 0／只搜 lea 漏 `add esi,-8`（恰是本轮要收的项）／81 编码 E9 基址取 `va+9` 应 `va+13`（错算落点 0x41428c 全是 `90` 填充）。

**落盘.** R14_COMMON **§2.216** CR 保持 **1081**；GOAL **§1266** CR 保持 **337**；LEAD_LOCK **QN** CR 保持 **137**；本看板 CR 保持 **0**（开局 **262 行 >= 260** ⇒ 先归档最早 2 段至 BOARD_ARCHIVE，归档 CR 保持 **2952**）。C16_FLOORS 纳入 §2.216（unpinned 0 / hollow 0 / missing 0）。**FACT_INDEX V589→V590**：写入 F29（stmt 3435→5343 B，其余 55 行逐字节不变），sha `89bb71ba`→**`e49a3edd`**、240722→**242630** B、57 行不变；指针 + facts_floors（D0/D8/D9/D10，MASTER `96f504e7`→`940c94c0`）+ gate_runner LEDGER 同步重钉。三门 exit 0：`check_disc`（C15 末节 216、C16 208 节全钉、C19 ok(e49a3edd/242630/V590)、C20 ok）、`facts_floors`（D8 242630）、`gate_runner`（G1=G2=G3=ok）。

**未取得.** ① `attributes` 位义（动态）；② `attributes 5 vs 1`；③ 13 个 onlysec pTD 成因；④ 34 个无类 TD 派生链；⑤ 5 个 pTD 多记录成因；⑥ R206 遗留 6 项；⑦ F23/F35 grade（两 tsv 不可读，禁预估回填）；⑧ C7 三死分支、C11 十二 ID。
'''
cur=open(BOARD,'rb').read()
nb=cur+ADD.encode('utf-8')
assert nb.count(b'\r\n')==0
n_lines=nb.count(b'\n')
assert n_lines<=300, n_lines
commit(BOARD,nb,0,'board-add')
print('final board lines',n_lines)
json.dump({'board_lines':n_lines,'arch_cr':2952},open(ROOT+'/_r208/p12_board.json','w'))
