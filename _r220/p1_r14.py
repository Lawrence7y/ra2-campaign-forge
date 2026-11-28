# -*- coding: utf-8 -*-
"""R220 p1：R14_COMMON §2.228 追加（wx 备份 -> 断言旧 CR/sha -> 一次性写 -> 回读校验）。"""
import os, hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
T=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/R17_LEAD_BASELINE'
P=T+'/R14_COMMON.md'
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
b0=bak(P,'R14')
assert b0.count(b'\r')==1081, b0.count(b'\r')
assert b0.endswith(b'\n')
oldsha=hashlib.sha256(b0).hexdigest()
SEC = """
## 2.228 R220（2026-11-28）· 0x87c484 = CRT locale 类别表（6 × 12 B）+ 162 记录表真实跨度 2592 B + IMA ADPCM 三表互锁 + .text 段界口径订正

### 一 · 🔴 0x87c484 不是「12 B 派发表 5 条」，是 MSVC CRT locale 类别表 6 条 × 12 B

| 记录 | 基址 | +0 | +4 | +8 |
|---|---|---|---|---|
| rec0 | 0x87c484 | 0x00000000 | 0x007ce046（33 c0 c3） | LC_COLLATE |
| rec1 | 0x87c490 | 0x0087c370（C） | 0x007d6ce7 | LC_CTYPE |
| rec2 | 0x87c49c | 0x0087c370 | 0x007d6aa2 | LC_MONETARY |
| rec3 | 0x87c4a8 | 0x0087c370 | 0x007d6830 | LC_NUMERIC |
| rec4 | 0x87c4b4 | 0x0087c370 | 0x007d6624 | LC_TIME |
| rec5 | 0x87c4c0 | 0x0087c370 | 0x007d60b5 | (null) |

- 上界字节 0x7cdd08 = 81 ff c0 c4 87 00（cmp edi,0x87c4c0）+ 0x7cdd0e = 7e（jle，含末条）
  ⇒ (0x87c4c0−0x87c484)/12 = 5 余 0，含末条共 6 条。R219 的「4 项余 8 B」订正。
- 调用点 0x7cde2b = ff 96 88 c4 87 00（call dword ptr [esi+0x87c488]）；
  0x7cddac = 8d 34 7f（lea esi,[edi+edi*2]）+ 0x7cddb6 = c1 e6 02（shl esi,2）⇒ esi = edi*12
  ⇒ 实际调 rec[edi].+4；写回 rec[edi].+0（0x7cddf7 mov [esi+0x87c484],eax）缓存 charset。
- 正反控 10/10 PASS（_r220/m21_locale_ctl.py）：K9 反控以 0x87c488 为基址则 +8 全变 C；K10 负控第 7 条 +8 非 LC_*。

### 二 · 162 记录常量表真实跨度 = 2592 B（162 × 16），R219 的 2576 B 是 161 条截断

- 0x876ff4.. 与 0x87b170.. 共 2592 B 逐字节相同，sha256 0cf1a6373d8db08b92b2855486c85fd6298037a755406616c72def249382a7f1。
- 记录形态 [a,a,a,a, a+d, a+d+64, a+d+128, a+d+192]，d=96（160 条）/ d=64（前 2 条）；
  a = 0 四次后 32k 各 2 条（k=1..79）；全表 16 位字皆为 32 的倍数，max = 2816。
- 引用：0x87b170 共 24 条（全部 [edx+0x87b170]）；0x876ff4 共 8 条（0x7c680f..0x7c6959）；均按字取值，无虚表槽消费。
- 正控（_r220/m23_extent2.py / m24_span.py）：X1 两份副本有效记录各 162；X3/X4 2592 B sha 相同且逐字节相同；
  X7 a 取值集合 = {0} ∪ {32k, k=1..79}；X8b 全 162 记录 max 16 位字 = 2816。

### 三 · 🔴 IMA ADPCM 三表互锁（本轮最强证据）

1. 0x8758e4 = 89 项 16 位 step table，与标准 IMA ADPCM 表逐项 89/89 相同；
   .text 引用 3 条（0x7c63cd / 0x7c64d1 / 0x7c65f0，皆 mov ax,word ptr [ecx+0x8758e4]），
   且上界 cmp word ptr [ebx+0x22], 0x58 的 0x58 = 88 恰为末项下标。
2. 0x879b30 = 89 块 × 16 dword = 5696 B；每块前 8 严格递增、后 8 = 前 8 的相反数（89/89）；
   引用 24 条全部 add eax, dword ptr [edx*2+0x879b30]；块首项单调不降。
   0x879b30 + 5696 == 0x87b170 ⇒ 与上述表起点零间隙，两条独立测量互锁。
3. 0x87bd90 = 16×16 = 256 B，第 r 行 16 字节全为 2r；引用 24 条全部 or dl, byte ptr [ebx+0x87bd90]。
4. 生成律（如实分级，不做预估）：以 s = IMA[k] 与 floor(s*(2i+1)/8) 精确生成 44/89 块；
   放宽到「任一整数 s + 任一口径」则 67/89；逐块反解出的 89 个 s* 中 78/89 落在 IMA 表内，
   达标块的 s*−IMA[k] 恒为 0（44/44）⇒ 与 IMA 对应关系成立，但逐块舍入口径未定（余 22 块）。
- 判据脚本 _r220/m25_law.py / m26_blocklaw.py / m27_final.py（Y11/Y12/Y13/Y14）/ m28_imalaw.py / m31_rev.py，全部 0 FAIL。

### 四 · 🟡 .text 段界口径订正（新事实）

| 口径 | 指令数 | 末指令 |
|---|---|---|
| rawsize（lo..0x7e1000，R219 采用） | 1394186 | 0x7e0fff |
| vsize（lo..0x7e038d） | 1392592 | 0x7e038c |

差 1594 = 尾部 [0x7e038d,0x7e1000) 共 3187 B 全 0x00（实测 1594 条 add byte ptr [eax],al）。
R219 的 1394186 有效但含填充伪指令；今后引用必须写明口径。

### 五 · 四 offset 口径复证（与 R219 一致并补足第 4 个字段）

| offset | 指令引用 | imm32 写 .text |
|---|---|---|
| +0x77c | 9 | 2 |
| +0x780 | 9 | 3 |
| +0x784 | 12 | 7 |
| 三者和 | 30 | 12 |
| +0x788 | 30 | 9 |
| 四者和 | 60 | 21 |

负控：+0x7a4 = 15（非 0，真实字段）、+0x778 = 19、+0x78c = 32。
口径提醒：「imm 落 .text」限定只在 +0x788 起作用（0x6660f3 mov [esi+0x788],0x7d0 的 imm 不落 .text），
丢掉该限定会把 21 算成 22。

### 六 · 门禁现态实测（次优先项）

- check_disc.py → exit 0，31 项全 PASS / 0 FAIL / 0 SKIP；R137 的「5 FAIL」已在现态失效（id 3/4/22/27/28 现全 PASS）。
- 「永不 FAIL」机制：:357 C11_LANDABLE = {3,4,11,12,13,14,15,17,22,26,27,28} 的第 7 列以「无」开头
  ⇒ 走 :405 的 claims-none 通道，两道现有挡板在 :415（R128 自述行残留）与 :432（R129 校验式真跑），
  其后 :441-442 c11_unver += 1 并 continue ⇒ 恒 PASS 根因是「声明不补跑」，不是判据写错。
- C20 比较 os.path.normpath 字符串（非 realpath / inode / sha256）：:1336、:1344。
- C7 三处 if-return 在 :152 / :172（return False，可 FAIL）与 :203（return None，计 SKIP）；
  真正死的是 exists / bytes= / none 三种形态在数据表覆盖 0 行，已由 C7b 钉住。
- 正控：指针 V601→V999 后新增 2 FAIL（C19 + C20），证明指针联动判据是活的；反控无改动 31 PASS 一致。

### 七 · 跨家族与自错

- card A(#573 hy4 exec 22 回合 12.47′ vs 12，OVERTIME)、card B(#574 hy4 exec 22 回合 12.47′ vs 12，OVERTIME)、
  card C(#575 hy4 exec 14 回合 2.55′ vs 12，无超时)、审计 #576（deepseek audit 18 回合，succeeded）。10/10 数值主会话独立复算一致。
- 审计独立发现 3 条主会话口径问题，全部成立并已采纳：P1 段界口径 1594 条伪指令（入 §4）；P2 2576→2592（入 §2）；
  P3 imm-in-text 只在 +0x788 起作用（入 §5）。
- 自错 5 条 0 条进结论：E1 m2 硬编码序列误得 161 条；E2 m25 结构体格式串非法；E3 m16 在 SKIPDATA 下读 operands 抛异常；
  E4 卡面 imm32 预期未区分第四 offset（子代理报 21 属正确）；E5 卡面负控 0x7a4 预期 0 为错（实测 15）。
"""
assert '`' not in SEC
new=b0+SEC.encode('utf-8')
assert new.count(b'\r')==1081, new.count(b'\r')
open(P,'wb').write(new)
chk=open(P,'rb').read()
assert chk.startswith(b0) and chk.count(b'\r')==1081 and chk==new
print('[OK] R14_COMMON %d -> %d B, CR=%d, sha %s -> %s'%(len(b0),len(chk),chk.count(b'\r'),oldsha[:16],hashlib.sha256(chk).hexdigest()[:16]))
