# -*- coding: utf-8 -*-
"""R220 p2：GOAL §1278 追加。"""
import os, hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'; BASE=ROOT+'/R17_LEAD_BASELINE'
P=ROOT+'/lead/GOAL_THREE_TARGETS_20261018.md'
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
b0=bak(P,'GOAL'); assert b0.count(b'\r')==337 and b0.endswith(b'\n')
SEC="""
## §1278 · R220（2026-11-28）· 0x87c484 = CRT locale 类别表 6 条；162 记录表真实跨度 2592 B；IMA ADPCM 三表互锁；.text 段界口径订正

- **0x87c484 定性推翻 R219**：不是「12 B 派发表 5 条」，是 **MSVC CRT locale 类别表 6 条 × 12 B**（rec0..rec5 的 +8 依次为
  LC_COLLATE / LC_CTYPE / LC_MONETARY / LC_NUMERIC / LC_TIME / (null)，后 5 条 +0 全为 0x87c370 的字符串 C）。
  上界 cmp edi,0x87c4c0 + jle（含末条）⇒ 6 条而非 5 条；调用点 0x7cde2b 的 [esi+0x87c488] 因 esi=edi*12 实为 **rec[edi].+4**。
  正反控 10/10 PASS（_r220/m21_locale_ctl.py）。
- **162 记录表跨度订正**：0x876ff4 与 0x87b170 两副本各 **2592 B（162×16）**，R219 的 2576 B 是 161 条截断；
  两副本 2592 B 逐字节相同、sha256 0cf1a637…；记录形态 [a,a,a,a,a+d,a+d+64,a+d+128,a+d+192]（d=96 占 160 条），
  a=0 四次后 32k 各 2 条，全表字皆 32 的倍数，max 2816（_r220/m23_extent2.py、m24_span.py）。
- **IMA ADPCM 三表互锁（本轮最强证据）**：①0x8758e4 = 89 项 16 位 step table，与标准 IMA 表 **89/89 逐项相同**，
  .text 引用 3 条（0x7c63cd/0x7c64d1/0x7c65f0，皆 mov ax,word[ecx+0x8758e4]），上界 0x58=88 恰为末项下标；
  ②0x879b30 = **89 块 × 16 dword = 5696 B**，每块前 8 严格递增、后 8 为前 8 相反数（89/89），引用 24 条全为
  add eax,dword[edx*2+0x879b30]，且 **0x879b30+5696 == 0x87b170 零间隙**；③0x87bd90 = 16×16 = 256 B（第 r 行全 2r），
  引用 24 条全为 or dl,byte[ebx+0x87bd90]。生成律如实分级：floor(s*(2i+1)/8) 且 s=IMA[k] 命中 44/89，
  放宽口径 67/89，反解 s* 78/89 落 IMA 表内、s*−IMA[k] 恒 0（44/44）⇒ 关系成立、**舍入口径未定（余 22 块）**。
- **.text 段界口径（新事实）**：rawsize 口径 **1,394,186** 条（末 0x7e0fff），vsize 口径 **1,392,592** 条（末 0x7e038c），
  差 **1594** = 尾部 [0x7e038d,0x7e1000) 共 **3187 B 全 0x00**。R219 的 1,394,186 有效但含填充伪指令，今后必须写明口径。
- **四 offset 口径复证**：+0x77c/+0x780/+0x784 = 9/9/12（和 30），imm32→.text = 2/3/7（和 **12**，与 R219 一致）；
  加入 +0x788（30 条引用）后和 **60**、imm32→.text = **21**。负控 +0x7a4=15、+0x778=19、+0x78c=32。
  「imm 落 .text」限定只在 +0x788 起作用（0x6660f3 的 imm 0x7d0 不落 .text），丢掉会算成 22。
- **门禁现态**：check_disc.py **exit 0，31 项全 PASS / 0 FAIL / 0 SKIP**（R137「5 FAIL」已失效，id 3/4/22/27/28 现全 PASS）；
  恒 PASS 根因是 C11_LANDABLE(12 个 id) 第 7 列声明「无」走 claims-none 通道（:405，挡板 :415/:432，:441 计 unver 后 continue），
  不是判据写错；C20 比较 os.path.normpath 字符串（:1336/:1344），非 realpath/inode/sha256。
  正控把指针 V601→V999 后新增 2 FAIL（C19+C20），反控无改动 31 PASS 一致。
- **跨家族**：card A(#573 hy4 exec 22 回合 12.47′ vs 12，OVERTIME)、card B(#574 hy4 exec 22 回合 12.47′ vs 12，OVERTIME)、
  card C(#575 hy4 exec 14 回合 2.55′ vs 12)、审计 #576（deepseek 18 回合 succeeded）。10/10 数值主会话独立复算一致；
  审计独立发现 3 条口径问题（P1 段界 1594 条伪指令、P2 2576→2592、P3 imm-in-text 仅 +0x788）**全部成立并已采纳**。
- **自错 5 条 0 进结论**：E1 m2 硬编码序列误得 161 条；E2 m25 结构体格式串非法；E3 m16 SKIPDATA 下读 operands 抛异常；
  E4 卡面 imm32 预期未区分第四 offset（子代理报 21 属正确）；E5 卡面负控 0x7a4 预期 0 为错（实测 15）。
- **落盘**：R14_COMMON §2.228 CR=1081（1943574→1949638 B）；本段 §1278 CR=337；LEAD_LOCK QN CR=137；STATUS_BOARD 第 220 轮 CR=0。
"""
new=b0+SEC.encode('utf-8'); assert new.count(b'\r')==337
open(P,'wb').write(new); chk=open(P,'rb').read()
assert chk.startswith(b0) and chk.count(b'\r')==337 and chk==new
print('[OK] GOAL %d -> %d B CR=%d sha %s'%(len(b0),len(chk),chk.count(b'\r'),hashlib.sha256(chk).hexdigest()[:16]))
