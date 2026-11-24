# -*- coding: utf-8 -*-
"""生成 delta.tsv / base_rate.tsv（只放四环齐全的 8 行；语义从 EVIDENCE 的一句话语义逐字读取，保证引用与证据同数）。"""
import os

WORK = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.dirname(WORK)
EVDIR = os.path.join(OUTDIR, "EVIDENCE")

# 8 行四环齐全（entry 升序；name/subsystem 原样取自筛选产物）
PASS = ["0062D9A0", "0062FE90", "00630090", "00644960",
        "006457A0", "00645950", "00749F30", "0074BA30"]
NAME = {
 "0062D9A0":"ParticleClass::slot8",
 "0062FE90":"ParticleSystemClass::slot10",
 "00630090":"ParticleSystemClass::slot6",
 "00644960":"ParticleSystemTypeClass::slot8",
 "006457A0":"ParticleTypeClass::slot6",
 "00645950":"ParticleTypeClass::slot8",
 "00749F30":"VoxelAnimClass::slot23",
 "0074BA30":"VoxelAnimTypeClass::slot8",
}
EV = "D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/NAMED_PUSH_S20_B2/EVIDENCE/ROW_%s.txt"


def sem_of(entry):
    txt = open(os.path.join(EVDIR, "ROW_%s.txt" % entry), encoding="utf-8").read()
    marker = "## 一句话语义\n   "
    i = txt.index(marker) + len(marker)
    j = txt.index("\n", i)
    return txt[i:j].strip()


hdr = "entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path"
lines = [hdr]
for e in PASS:
    assert e == e.upper() and not e.startswith("0x") and len(e) == 8, e
    sem = sem_of(e)
    assert sem, e
    lines.append("%s\tS20\t%s\t%s\t[已证]\t%s" % (e, NAME[e], sem, EV % e))
open(os.path.join(OUTDIR, "delta.tsv"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

# base_rate: rows_checked=18, ring2=17 (row21 Update_B 无虚表槽), ring3b=8, ring4=17, all_four=8
rows_checked, ring2_ok, ring3b_ok, ring4_ok, all_four = 18, 17, 8, 17, len(PASS)
with open(os.path.join(OUTDIR, "base_rate.tsv"), "w", encoding="utf-8") as f:
    f.write("batch\trows_checked\tring2_ok\tring3b_ok\tring4_ok\tall_four\trate\n")
    f.write("S20_B2\t%d\t%d\t%d\t%d\t%d\t%.4f\n" % (
        rows_checked, ring2_ok, ring3b_ok, ring4_ok, all_four, all_four / rows_checked))
print("delta rows =", len(PASS))
print("base_rate: S20_B2 %d %d %d %d %d %.4f" % (
    rows_checked, ring2_ok, ring3b_ok, ring4_ok, all_four, all_four / rows_checked))
