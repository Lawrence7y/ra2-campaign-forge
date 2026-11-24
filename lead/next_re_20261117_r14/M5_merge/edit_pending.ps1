$ErrorActionPreference = 'Stop'
$base = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
$pend = Join-Path $base 'COVERAGE\PENDING_CORRECTIONS.tsv'
$V = 'PARTIAL (M4_merge/_audit/VERDICT.md L25/29 ★E 必改(2))'
$S = 'a-M4 VERDICT ★E/必改(2)'

$rows = @()

# ---- Task 2: W177-C 11 under-evidenced [已证] registrations ----
$rows += "W177-C`t0087F7E8`tgrade`t[已证] (M4: [已证·复用]->[已证]; m13_ingame.json)`t[静态推断]`t$S`t$V; runtime JSON observation, not byte-level nor independent recompute; 该批登记不得用作[已证]依据; M5 已降 probe grade"
$rows += "W177-C`t000001AC`tgrade`t[已证] (M4: [已证·观测]->[已证]; B02_reject_conyard.json)`t[静态推断]`t$S`t$V; 卡面自述u32=0而证据canplace_1AC_u32=512, 自相矛盾; M5 已降 probe grade"
$rows += "W177-C`t00000030`tgrade`t[已证] (M4: [已证·复用]->[已证]; work/wb_probe.py)`t[未证] (disk already [未证])`t$S`t$V; 仅探针脚本且盘上probe实为[未证], M4'14/14'偏宽; M5 未改盘(已[未证]), 仅登记更正"
$rows += "W177-C`t00886FA0`tgrade`t[已证] (M4: [已证读数]->[已证]; B02_reject_conyard.json)`t[未证]`t$S`t$V; 恒0读数零区分力且疑非本build有效地址, 未证0x886FA0=相机原点; M5 已降 probe grade"
$rows += "W177-C`t00886FA4`tgrade`t[已证] (M4: [已证读数]->[已证]; B02_reject_conyard.json)`t[未证]`t$S`t$V; 恒0读数零区分力且疑非本build有效地址, 未证0x886FA4=相机原点; M5 已降 probe grade"
$rows += "W177-C`t0000009C`tgrade`t[已证] (M4: [已证·复用]->[已证]; work/wb_probe.py)`t[静态推断]`t$S`t$V; 仅探针脚本(方法≠证据, §966复用不算); M5 已降 probe grade"
$rows += "W177-C`t000000A0`tgrade`t[已证] (M4: [已证·复用]->[已证]; work/wb_probe.py)`t[静态推断]`t$S`t$V; 仅探针脚本(方法≠证据, §966复用不算); M5 已降 probe grade"
$rows += "W177-C`t00000520`tgrade`t[已证] (M4: [已证·复用]->[已证]; m13_ingame.json)`t[静态推断]`t$S`t$V; runtime JSON observation 勉强够但非字节级/独立复算, 按保守不入[已证]; M5 已降 probe grade"
$rows += "W177-C`tA8EB50`tgrade`t[已证] (M4: [已证·复用]->[已证]; work/w177_core.py)`t[静态推断]`t$S`t$V; 仅探针脚本(方法≠证据, §966复用不算); M5 已降 probe grade"
$rows += "W177-C`tB0F724`tgrade`t[已证] (M4: [已证·复用]->[已证]; work/wb_probe.py)`t[静态推断]`t$S`t$V; 仅探针脚本(方法≠证据, §966复用不算); M5 已降 probe grade"
$rows += "W177-C`tB0F730`tgrade`t[已证] (M4: [已证·复用]->[已证]; work/wb_probe.py)`t[静态推断]`t$S`t$V; 仅探针脚本(方法≠证据, §966复用不算); M5 已降 probe grade"

# ---- Task 3: probe 15 non-standard bare '已证' tokens normalized ----
$S3 = 'a-M4 VERDICT L25 ★E 末句/必改(3)'
$V3 = 'PARTIAL (M4_merge/_audit/VERDICT.md): 非标token bare 已证 归一为[已证]; evidence 字节级读/写指令+imm32+指令边界可独立复算, 保留[已证]; M5 已改 probe token'
$t3map = [ordered]@{
 '00482943'='EVIDENCE/t2_disp_1808_172c.txt'; '004DA560'='EVIDENCE/t2_disp_1808_172c.txt'
 '0052BAD8'='EVIDENCE/t1_callsite_52BA60.txt'; '0052BAFA'='EVIDENCE/t1_callsite_52BA60.txt'
 '006BEABD'='EVIDENCE/t1_cleanup_6BE1C0.txt'; '0052F63E'='EVIDENCE/t3_final_verify.txt'
 '005A922F'='EVIDENCE/t3_final_verify.txt'; '005A95A1'='EVIDENCE/t3_final_verify.txt'
 '0077780E'='EVIDENCE/t3_final_verify.txt'; '00777CD6'='EVIDENCE/t3_final_verify.txt'
 '00777D7E'='EVIDENCE/t3_bytechannel_full.txt'; '006675B0'='EVIDENCE/t2_doublechannel.txt'
 '006677B3'='EVIDENCE/t2_doublechannel.txt'; '0066BAA3'='EVIDENCE/t3_global_writes.txt'
 '0066CFDC'='EVIDENCE/t2_ini_readers.txt'
}
foreach ($a in $t3map.Keys) {
 $rows += "W175_global8871`t$a`tgrade`t已证 (非标token, 无方括号)`t[已证]`t$S3`t$V3; evidence=$($t3map[$a])"
}

# ---- Task 4: a-M3 '69 个 entry' should be 46 ----
$rows += "M3_merge/PANEL`tPANEL.md:74; M3_merge/REPORT.md:23`tentry_count`t69 个 entry`t46 个 entry`ta-M4 VERDICT L29 裁决第4项`tPARTIAL (M4_merge/_audit/VERDICT.md): CONFLICTS.tsv 末93行 distinct entry=46, conflict=1 181=146+46-11自洽; PANEL.md:74 已在M5写域内改69->46; M3_merge/REPORT.md:23 写域外未改, 待后续卡更正"

$raw = [System.IO.File]::ReadAllText($pend)
$lf = ([regex]::Matches($raw,"`n")).Count
if (-not $raw.EndsWith("`n")) { $raw += "`n" }
$raw += ([string]::Join("`n",$rows)) + "`n"
[System.IO.File]::WriteAllText($pend, $raw, (New-Object System.Text.UTF8Encoding($false)))
$bytes = [System.IO.File]::ReadAllBytes($pend)
$n=0;$crlf=0
for($i=0;$i -lt $bytes.Length;$i++){if($bytes[$i] -eq 10){$n++;if($i -gt 0 -and $bytes[$i-1] -eq 13){$crlf++}}}
"PENDING LF before=$lf after=$n CRLF=$crlf added=$($rows.Count) bytes=$($bytes.Length)"
