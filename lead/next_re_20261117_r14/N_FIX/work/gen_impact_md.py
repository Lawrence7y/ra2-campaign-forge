#!/usr/bin/env python3
"""Assemble IMPACT_BY_CARD.md from evidence (UTF-8 direct)."""
import os
from collections import defaultdict
ROOT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
N=os.path.join(ROOT,'N_FIX')
rows=defaultdict(list)
for line in open(os.path.join(N,'NOINIT_CENSUS.tsv'),encoding='utf-8'):
    p=line.rstrip('\n').split('\t')
    if p[0]=='addr': continue
    rows[p[1].split('/')[0]].append(p)

# booked high (primary; strict in parens), this-round increment, status
booked={'C01':'96','C02':'840','C03':'428','C04':'776','C05':'565',
        'C06':'382（严格 274）','C07':'559（严格 359）','C08':'417（严格 416）',
        'C09':'438','C10':'254'}
inc={'C01':0,'C02':0,'C03':0,'C04':7,'C05':6,'C06':8,'C07':13,'C08':0,'C09':0,'C10':0}
# mis-rejection count per card (unique addresses qualified by criterion)
mis={'C01':0,'C02':9,'C03':6,'C04':7,'C05':6,'C06':8,'C07':13,'C08':9,'C09':15,'C10':0}
status={
 'C01':'已正确处理：15 个具名地址本就写作 `Xxx::Xxx` [已证]，无 noinit_t 降级。0x40E320/0x52ACE0 等重复地址属同码折叠，不影响。',
 'C02':'9 行叫 `Xxx::noinit_t`，但 trace `conf=high / source=self_known`，**已计入 840**，high 增量 0；属错名（应改具名构造器名），非降级。',
 'C03':'6 行叫 `Xxx::noinit_t`，但 trace `conf=high / source=self_strong`，**已计入 428**，high 增量 0；同 C02 属错名。',
 'C04':'7 个唯一地址（9 行含 0x52ACE0/0x5447C0 各 2 实例）全为 `sub_XXXXXX` [未证] / conf=low，真实具名构造器被降级 → **本轮 +7**。C04 VERDICT §反向问题已报 10 个 noinit_t 落名，其中 3 个 Sxx 归属错另计（见 UNKNOWNS），high 口径本卡此前未补。',
 'C05':'6 地址全为 `sub_XXXXXX`：3 个 conf=low [未证]、3 个 conf=med [静态推断]（MPObserverTeam / MPSiegeDefenderTeam / MPSiegeAttackerTeam），均未进 565 → **本轮 +6**。',
 'C06':'9 地址：8 个 `sub_` [未证]/conf=low 被降级 → **本轮 +8**；另 `0x5D8170` conf=high 但名为 vtable 槽 `T_Initializer_VMultiplayerBattle___MultiplayerGameMode::slot1` [静态推断]，已进 382，不属「noinit_t 形态 / low/[未证]」，按纪律 §954 不计入误剔，仅记为命名异常。',
 'C07':'13 地址全为 `sub_XXXXXX` [未证] / conf=low，真实构造器被降级 → **本轮 +13**。',
 'C08':'9 地址全为 `sub_` [未证]/conf=low；**§960 已修正 +9（408→417，严格 416）**，本轮不重复计入。',
 'C09':'15 唯一地址（16 行含 0x71E6A0 双实例）全为 `sub_` [未证]/conf=low；**§942 已修正 +15（423→438）**，本轮不重复计入。',
 'C10':'本片 atlas 区间内无 noinit_t 真构造器地址（0 行），无影响。',
}

out=[]
out.append("# IMPACT_BY_CARD.md — 逐片 noinit_t 误剔影响")
out.append("")
out.append("目标 `ra2youli\\gamemd.exe` SHA-256 `73201CC0…F67476`｜判据见 `BASELINE.md`（已收窄：上一行确为 `: Xxx(noinit_t())` **且** 下一行有 `JMP_THIS(0x…)`）。")
out.append("分级仅用 [已证] / [静态推断] / [未证]。high 口径 = self_known([已证]) + vtable-core，与 cards 的 `classification_trace.tsv` / `_audit\\VERDICT.md` 一致。")
out.append("")
out.append("## 汇总（本轮新增 vs 已入账修正）")
out.append("")
out.append("| 卡 | 入账 high | 误剔地址数 | 本轮 high 增量 | 修正后 high | 修正归属 |")
out.append("|---|---|---:|---:|---|---|")
def corrected_val(c):
    b=booked[c]; i=inc[c]
    if i==0: return b
    if '（' in b:
        primary,rest=b.split('（',1)
        rest_n=rest.replace('严格 ','').replace('）','')
        return f"{int(primary)+i}（严格 {int(rest_n)+i}）"
    return str(int(b)+i)

for c in ['C01','C02','C03','C04','C05','C06','C07','C08','C09','C10']:
    corr = '已入账（§960）' if c=='C08' else ('已入账（§942）' if c=='C09' else ('本轮新增' if inc[c]>0 else '无需修正'))
    out.append(f"| {c} | {booked[c]} | {mis[c]} | {'+'+str(inc[c]) if inc[c] else '0'} | {corrected_val(c)} | {corr} |")
out.append("")
out.append("**本轮新增 high 增量合计 = +34**（C04 +7 / C05 +6 / C06 +8 / C07 +13）。C08 +9、C09 +15 已在 417/438 中，**不重复计入**。")
out.append("C02/C03 的 15 个 `::noinit_t` 名字本身错，但已 high，故 high 增量 0 —— 属命名问题，不是误剔降级。")
out.append("")
out.append("**停机核验**：本卡按 lead 给的入账值求和 = 96+840+428+776+565+382+559+417+438+254 = **4755**，与 P0-CLOSE 的 **4752** 差 +3；已定位为 C01(96 vs 102 = −6) 与 C08(417 vs 408 = +9) 两处口径差，非本卡凑数（详见 `SUMMARY.md`）。")
out.append("")
out.append("## 逐片明细（addr / 现名 / 应为）")
out.append("> 每片列出该片 atlas 区间内、收窄判据命中的全部实例。重复地址（同码折叠）逐条列出，high 增量按唯一地址计。")
for c in ['C01','C02','C03','C04','C05','C06','C07','C08','C09','C10']:
    out.append("")
    corrected = corrected_val(c)
    out.append(f"### {c} — 误剔 {mis[c]} / 本轮增量 {'+'+str(inc[c]) if inc[c] else '0'} / 修正后 high {corrected}")
    out.append("")
    out.append(status[c])
    out.append("")
    if rows[c]:
        for p in rows[c]:
            addr,_,name,grade,should,sgrade,ev=p
            out.append(f"- `{addr}` 现=`{name}` [{grade}] → 应为=`{should}` [{sgrade}]（{ev}）")
    else:
        out.append("- （无命中）")
out.append("")
with open(os.path.join(N,'IMPACT_BY_CARD.md'),'w',encoding='utf-8') as f:
    f.write("\n".join(out)+"\n")
print("wrote IMPACT_BY_CARD.md lines", len(out))
