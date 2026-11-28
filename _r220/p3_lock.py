# -*- coding: utf-8 -*-
"""R220 p3：LEAD_LOCK 新增 QN 段。"""
import os, hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'; BASE=ROOT+'/R17_LEAD_BASELINE'
P=ROOT+'/lead/LEAD_LOCK'
def bak(path,tag):
    b=open(path,'rb').read()
    base='%s/%s.before_r220_%s'%(BASE,os.path.basename(path),tag)
    for i in range(10):
        dst=base+(('_%d'%i) if i else '')+'_20261128.bak'
        if os.path.exists(dst):
            if open(dst,'rb').read()==b: return b
            continue
        fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as f: f.write(b)
        return b
    raise SystemExit('bak exhausted')
b0=bak(P,'LOCK'); assert b0.count(b'\r')==137
assert b'**QM7' in b0
SEC="""
**QN. 🔴 ` 0x87c484 ` 不是「12 B 派发表」，是 MSVC CRT locale 类别表 6 条 × 12 B.** rec0..rec5 的 +8 依次为
LC_COLLATE / LC_CTYPE / LC_MONETARY / LC_NUMERIC / LC_TIME / (null)，后 5 条 +0 全指向 ` 0x87c370 ` 的字符串 C。
上界 ` 0x7cdd08 = 81 ff c0 c4 87 00 `（cmp edi,0x87c4c0）+` 0x7cdd0e = 7e `（jle 含末条）
⇒ ` (0x87c4c0−0x87c484)/12 = 5 ` 余 0，含末条共 **6** 条；R219 的「4 项余 8 B」**订正**。
调用点 ` 0x7cde2b = ff 96 88 c4 87 00 `（call [esi+0x87c488]）的 ` esi = edi*12 `
（` 0x7cddac = 8d 34 7f ` / ` 0x7cddb6 = c1 e6 02 `）⇒ 实际调 **rec[edi].+4**，写回 rec[edi].+0 缓存 charset。
正反控 **10/10 PASS**（` _r220/m21_locale_ctl.py `）：K9 反控以 ` 0x87c488 ` 为基址则 +8 全变 C；K10 负控第 7 条 +8 非 LC_*。

**QN2. 🔴 162 记录常量表真实跨度 = 2592 B（162×16），R219 的 2576 B 是 161 条截断.** 两副本 2592 B **逐字节相同**，
sha256 ` 0cf1a637… `；记录形态 ` [a,a,a,a,a+d,a+d+64,a+d+128,a+d+192] `，` d=96 ` 占 160 条、
前 2 条 ` d=64 `；` a ` = 0 四次后 32k 各 2 条（k=1..79）；全表字皆 32 的倍数，max **2816**。
引用：` 0x87b170 ` **24** 条、` 0x876ff4 ` **8** 条，均按字取值。

**QN3. 🔴 IMA ADPCM 三表互锁（本轮最强证据）.** ①` 0x8758e4 ` = **89 项 16 位 step table**，与标准 IMA 表
**89/89 逐项相同**，.text 引用 **3** 条（` 0x7c63cd/0x7c64d1/0x7c65f0 `，皆 ` mov ax,word[ecx+0x8758e4] `），
上界 ` cmp word [ebx+0x22],0x58 ` 的 **0x58 = 88** 恰为末项下标；②` 0x879b30 ` = **89 块 × 16 dword = 5696 B**，
每块前 8 严格递增、后 8 为前 8 相反数（89/89），引用 **24** 条全为 ` add eax,dword[edx*2+0x879b30] `，
且 **` 0x879b30+5696 == 0x87b170 ` 零间隙**；③` 0x87bd90 ` = 16×16 = **256 B**（第 r 行全 2r），
引用 **24** 条全为 ` or dl,byte[ebx+0x87bd90] `。生成律如实分级：` floor(s*(2i+1)/8) ` 且 ` s=IMA[k] `
命中 **44/89**，放宽口径 **67/89**，反解 s* **78/89** 落 IMA 表内且 ` s*−IMA[k] ` 恒 **0**（44/44）
⇒ 关系成立、**舍入口径未定（余 22 块）**。

**QN4. 🟡 .text 段界口径订正（新事实）.** rawsize 口径 **1,394,186** 条（末 ` 0x7e0fff `），
vsize 口径 **1,392,592** 条（末 ` 0x7e038c `），差 **1594** = 尾部 ` [0x7e038d,0x7e1000) ` 共 **3187 B 全 0x00**。
R219 的 1,394,186 有效但**含填充伪指令**，今后引用必须写明口径。审计 #576 的 P1 独立发现，成立。

**QN5. 🟡 四 offset 口径复证.** ` +0x77c/+0x780/+0x784 ` = **9/9/12**（和 30），imm32→.text = **2/3/7**（和 **12**，与 R219 一致）；
加入 ` +0x788 `（30 条引用）后和 **60**、imm32→.text = **21**。负控 ` +0x7a4 ` = **15**（非 0）、` +0x778 ` = **19**、` +0x78c ` = **32**。
「imm 落 .text」限定**只在 +0x788 起作用**（` 0x6660f3 mov [esi+0x788],0x7d0 ` 的 imm 不落 .text），丢掉该限定会把 21 算成 22。

**QN6. 🟡 门禁现态.** ` check_disc.py ` **exit 0，31 项全 PASS / 0 FAIL / 0 SKIP**；R137 的「5 FAIL」已在现态失效
（` id 3/4/22/27/28 ` 现全 PASS）。恒 PASS 根因是 ` :357 C11_LANDABLE ` 的 12 个 id 第 7 列声明「无」
⇒ 走 ` :405 ` claims-none 通道，挡板在 ` :415 `（R128）与 ` :432 `（R129），此后 ` :441-442 c11_unver += 1 ` 并 continue
⇒ **不是判据写错，是声明不补跑**。C20 比较 ` os.path.normpath ` 字符串（` :1336 `、` :1344 `），非 realpath/inode/sha256。
正控把指针 V601→V999 后新增 **2 FAIL**（C19+C20），反控无改动 31 PASS 一致。

**QN7. 🟡 跨家族 / 自错.** card A(#573 hy4 exec 22 回合 12.47′ vs 12，**[OVERTIME]**)、card B(#574 hy4 exec 22 回合 12.47′ vs 12，**[OVERTIME]**)、
card C(#575 hy4 exec 14 回合 2.55′ vs 12，无超时)、审计 #576（deepseek audit 18 回合，succeeded）。10/10 数值主会话独立复算一致。
审计独立发现 3 条主会话口径问题 **全部成立并已采纳**：P1 段界 1594 条伪指令、P2 2576→2592、P3 imm-in-text 仅 +0x788。
card A 的「DXT/调色板」语义推断**不采纳**（QN3 已由 IMA 三表互锁定性为 ADPCM 音频路径）。
自错 5 条 **0 条进结论**：E1 ` m2 ` 硬编码序列误得 161 条；E2 ` m25 ` 结构体格式串非法；E3 ` m16 ` SKIPDATA 下读 operands 抛异常；
E4 卡面 imm32 预期未区分第四 offset（子代理报 21 属正确）；E5 卡面负控 ` 0x7a4 ` 预期 0 为错（实测 15）。

**QN8. 🟡 收口.** R14_COMMON **§2.228** CR 保持 **1081**（1943574→1949638 B）；GOAL **§1278** CR 保持 **337**；
本段 **QN** CR 保持 **137**；STATUS_BOARD 第 220 轮 CR 保持 **0**（232 行 < 260，不触发归档）。

**QN9. ⚪ 未取得.** ①89 块中余 **22** 块（k=0/4/10/12/15/21/28/31/38/39 等）的舍入口径；
②162 表在 ` 0x7c742f ` 处 ` mov dx,word[edx+0x87b170] ` 的 ` edx ` 索引界与语义；
③` 0x7c7371 ` 的完整参数字义（` [ebp+0x10] ∈ {8,0x10} `、` [ebp+0x14] ∈ {1,2} `、` [ebp+0x1c] ` 指向何物）；
④F23/F35 grade 裁定；⑤C7 三死分支的自然真实行、C11 十二 ID 真判据接入方案。
"""
SEC=SEC.replace('\\u002b','+').replace('\\u2208','∈').replace('\\u0060','`').replace('\\u0060','`')
SEC=SEC.replace('`','`')
# unicode_escape 手工替换后清理残留
import re
SEC=SEC.replace('\\u0060','`')
new=b0+SEC.encode('utf-8'); assert new.count(b'\r')==137, new.count(b'\r')
open(P,'wb').write(new); chk=open(P,'rb').read()
assert chk.startswith(b0) and chk.count(b'\r')==137
print('[OK] LEAD_LOCK %d -> %d B CR=%d sha %s'%(len(b0),len(chk),chk.count(b'\r'),hashlib.sha256(chk).hexdigest()[:16]))
