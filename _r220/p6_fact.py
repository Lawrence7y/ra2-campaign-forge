# -*- coding: utf-8 -*-
"""R220 p6：FACT_INDEX V601 -> V602，只在 F29.limitations 追加 R220 实测段。"""
import hashlib, os, json
ROOT='/home/t628/projects/ra2-campaign-forge'; TIER=ROOT+'/lead/next_re_20261117_r14'
OLD=TIER+'/R17_R131_FACTINDEX_V601/FACT_INDEX.tsv'
NEWD=TIER+'/R17_R131_FACTINDEX_V602'; NEW=NEWD+'/FACT_INDEX.tsv'
fails=[]
def ck(nm,c,d=''):
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
raw=open(OLD,'rb').read(); h=hashlib.sha256(raw).hexdigest()
ck('W1 旧 V601 284839 B / sha 54ff0419', len(raw)==284839 and h.startswith('54ff0419'), (len(raw),h[:16]))
ck('W2 旧 CR == 0', raw.count(b'\r')==0)
txt=raw.decode('utf-8'); lines=txt.split('\n')
ck('W3 57 行 + 末段空', len(lines)==58 and lines[-1]=='', len(lines))
rows=[l.split('\t') for l in lines[:57]]
ck('W4 每行 5 列', all(len(r)==5 for r in rows))
f29=[r for r in rows if r[0]=='F29'][0]
L0=len(f29[4].encode()); ck('W5 F29 lim > 54000 B', L0>54000, L0)
APP=('**【R220 实测·0x87c484 定性推翻 + 162 表跨度订正 + IMA ADPCM 三表互锁 + .text 段界口径；statement 与 grade 均不改】** '
'R220 用 `_r220/m14_verify.py`（38 断言）… `_r220/m31_rev.py`（正反控全部内建）在现盘 `ra2bench/gamemd.exe`（sha256 `73201cc0…`）上重算：'
'① **`0x87c484` 不是 R219 记的「12 B 步长派发表 5 条」，而是 MSVC CRT locale 类别表的 6 条记录 × 12 B**：'
'rec0..rec5 的 `+8` 依次为字符串 `LC_COLLATE` / `LC_CTYPE` / `LC_MONETARY` / `LC_NUMERIC` / `LC_TIME` / `(null)`，'
'后 5 条 `+0` 全部指向 `0x87c370` 处的字符串 `C`，六条 `+4` 全部落 `.text`（`0x7ce046` 为 `33 c0 c3` = `xor eax,eax/ret` 桩，'
'其余五条 `0x7d6ce7/0x7d6aa2/0x7d6830/0x7d6624/0x7d60b5` 为该类别的设置函数）。'
'条目数由循环上界字节定死：`0x7cdd08 = 81 ff c0 c4 87 00`（`cmp edi,0x87c4c0`）+ `0x7cdd0e = 7e`（`jle`，**含末条**）'
'⇒ `(0x87c4c0−0x87c484)/12 = 5` 余 0，**含末条共 6 条**（跨 `0x87c484..0x87c4d0`）；'
'R219 的「4 项余 8 B」是把 `jle` 误当 `jl` 的差一条。调用点 `0x7cde2b = ff 96 88 c4 87 00`（`call dword ptr [esi+0x87c488]`）'
'的 `esi` 由 `0x7cddac = 8d 34 7f`（`lea esi,[edi+edi*2]`）+ `0x7cddb6 = c1 e6 02`（`shl esi,2`）得 `edi*12` '
'⇒ 实际调用 **`rec[edi].+4`**，并把返回值写回 `rec[edi].+0`（`0x7cddf7 mov [esi+0x87c484],eax`）缓存该类别 charset。'
'**正反控 10/10 PASS**（`_r220/m21_locale_ctl.py`）：K9 反控以 `0x87c488` 为基址时 `+8` 全部退化为字符串 `C`；K10 负控第 7 条 `+8` 非 `LC_*`。'
'② **162 记录常量表的真实跨度是 2592 B（162×16），R219 的 2576 B 是 161 条截断**：`0x876ff4..` 与 `0x87b170..` 两副本各 2592 B '
'**逐字节相同**，sha256 `0cf1a6373d8db08b92b2855486c85fd6298037a755406616c72def249382a7f1`；'
'记录形态为 `[a,a,a,a,a+d,a+d+64,a+d+128,a+d+192]`，`d=96` 占 160 条、前 2 条 `d=64`；`a` = 0 出现 4 次后 32k 各 2 次（k=1..79）；'
'全表 16 位字皆为 32 的倍数、最大值 `2816`（出现在 rec160/rec161）。R219 记的 `f3−f2=0x00800080` 与之相容（按 dword 视之即相邻两字差 0x40/0x80），'
'但「各 2576 B」应订正为「各 2592 B」。引用计数不变：`0x87b170` **24** 条（全部 `[edx+0x87b170]`）、`0x876ff4` **8** 条（`0x7c680f..0x7c6959`），均按**字**取值、无虚表槽消费。'
'③ **IMA ADPCM 三表互锁（本轮最强证据）**：`0x8758e4` 处是 **89 项 16 位 step table**，与标准 IMA ADPCM 表**逐项 89/89 相同**，'
'`.text` 引用 **3** 条（`0x7c63cd`/`0x7c64d1`/`0x7c65f0`，形态皆 `mov ax,word ptr [ecx+0x8758e4]`），'
'并且同函数上界 `cmp word ptr [ebx+0x22],0x58` 的 **0x58 = 88** 恰为该表末项下标；'
'`0x879b30` 处是 **89 块 × 16 dword = 5696 B** 的反量化 diff 表，每块前 8 个 dword 严格递增、后 8 个为前 8 的相反数（89/89 成立），'
'`.text` 引用 **24** 条全部为 `add eax, dword ptr [edx*2+0x879b30]`，块首项单调不降；'
'且 **`0x879b30 + 5696 == 0x87b170`**，与上述 162 记录表起点**零间隙衔接** —— 两条独立测量互锁；'
'`0x87bd90` 处是 **16×16 = 256 B** 常量表，第 r 行 16 个字节全等于 2r，引用 **24** 条全部为 `or dl, byte ptr [ebx+0x87bd90]`。'
'生成律**如实分级**（不做预估）：以 `s = IMA[k]` 与 `floor(s*(2i+1)/8)` 精确生成的块数为 **44/89**；放宽到「任一整数 s + 任一口径」为 **67/89**；'
'逐块反解出的 89 个 s* 中 **78/89 落在 IMA 表内**、且达标块的 `s*−IMA[k]` 恒为 **0**（44/44）'
'⇒ 与 IMA 表的对应关系成立，但**逐块舍入口径未定，余 22 块未解**（列为下轮待办）。card A 的「S3TC/DXT 调色板」推断据此**不采纳**。'
'④ **`.text` 段界口径（新事实，必须写明口径）**：按 `rawsize`（`lo..0x7e1000`）逐字节 resync 得 **1,394,186** 条、末指令 `0x7e0fff`；'
'按 `vsize`（`lo..0x7e038d`）得 **1,392,592** 条、末指令 `0x7e038c`；差 **1594** 恰为尾部 `[0x7e038d,0x7e1000)` 共 **3187 B 全 `0x00`** '
'被解成 `add byte ptr [eax],al`。⇒ R219 的 1,394,186 **可复现但含填充伪指令**，此后引用该数必须注明是 rawsize 口径；'
'严格只数真实代码应为 1,392,592（审计 #576 的 P1 独立发现，主会话复算成立）。'
'⑤ **四 offset 口径复证**：`+0x77c`/`+0x780`/`+0x784` 的指令引用 **9/9/12**（和 **30**），'
'其中「`mov dword ptr [reg+off], imm32` 且 imm32 落 `.text`」= **2/3/7**（和 **12**，与 R219 一致）；'
'加入第 4 个 offset `+0x788`（**30** 条引用）后和 **60**、imm32→`.text` = **21**。'
'负控：`+0x7a4` = **15**（非 0，属真实字段访问，R220 卡面「预期 0」的负控假设**有误**）、`+0x778` = **19**、`+0x78c` = **32**。'
'口径提醒：「imm 落 `.text`」这个限定**只在 `+0x788` 起作用**（`0x6660f3 mov dword ptr [esi+0x788],0x7d0` 的 imm 不落 `.text`），'
'丢掉该限定会把 21 算成 22（审计 #576 的 P3 独立发现）。'
'**边界**：本条不改 F29 的 statement 与 grade；`coverage.tsv` / `function_atlas.tsv` 仍不可读；89 块余 22 块的舍入口径未定。')
ck('W6 无 tab', '\t' not in APP)
ck('W7 无 CR/换行', '\r' not in APP and '\n' not in APP)
ck('W8 无双引号', '"' not in APP)
ck('W9 以句号结尾且 >2000 B', APP.endswith('。') and len(APP.encode())>2000, len(APP.encode()))
newlim=f29[4]+APP
ck('W10 lim 只增不减', len(newlim.encode())>L0, len(newlim.encode()))
f29[4]=newlim
newtxt='\n'.join('\t'.join(r) for r in rows)+'\n'; nb=newtxt.encode('utf-8')
ck('W11 新字节 = 旧 + 追加段', len(nb)==len(raw)+len(APP.encode()), (len(nb),len(raw)+len(APP.encode())))
ck('W12 新 CR == 0', nb.count(b'\r')==0)
ck('W13 除 F29 外 56 行逐字节不变', all(lines[i]=='\t'.join(rows[i]) for i in range(57) if rows[i][0]!='F29'))
if fails: print('[ABORT] %r'%fails); raise SystemExit(1)
os.makedirs(NEWD,exist_ok=True); assert not os.path.exists(NEW)
open(NEW,'wb').write(nb); chk=open(NEW,'rb').read(); assert chk==nb
print('[写入] %s bytes %d -> %d sha %s -> %s'%(NEW,len(raw),len(chk),h[:16],hashlib.sha256(chk).hexdigest()[:16]))
json.dump(dict(old_sha=h,new_sha=hashlib.sha256(chk).hexdigest(),old_bytes=len(raw),new_bytes=len(chk)),
          open(ROOT+'/_r220/p6.json','w'),indent=1)
