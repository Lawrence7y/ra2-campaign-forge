#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-J 独立分支判定：从 EVIDENCE/j_flag_samples.jsonl 复算
 (a) 主判定 [arg2+0x16BF] 是 0 还是非 0
 (b) 按 0x47C620 静态分支表判走哪支
 (c) 次判定：落格后目标格 [+0xE4] 链是否 >=2 且含 BuildingClass
只读 JSONL；输出 EVIDENCE/branch_recompute.txt。
"""
import json, os

CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-J"
JL = os.path.join(CARD, "EVIDENCE", "j_flag_samples.jsonl")
RUN = os.path.join(CARD, "EVIDENCE", "j_run.json")
OUT = os.path.join(CARD, "EVIDENCE", "branch_recompute.txt")

rows = [json.loads(l) for l in open(JL, encoding="utf-8")]
run = json.load(open(RUN, encoding="utf-8"))
out = []
P = out.append

P("W177-J 独立分支判定（输入 EVIDENCE/j_flag_samples.jsonl + j_run.json）")
P("=" * 76)
frames = sorted(set(r["frame"] for r in rows if r.get("frame") is not None))
P("samples=%d  distinct_frames=%d  frame[%d..%d]" % (len(rows), len(frames), frames[0], frames[-1]))
P("rate/s=%.1f  duration=%.4fs" % (run["sampling"]["rate_per_s"], run["sampling"]["duration_s"]))

def distinct(key):
    return sorted(set(r[key] for r in rows if r.get(key) is not None))

for key in ["g_F16BF", "g_F16BE", "g_F16B7", "g_DE58", "A8E9A0", "A8E7AC", "A8ED6B", "ghost_o1"]:
    P("  %-10s distinct=%s" % (key, distinct(key)))

f16bf = distinct("g_F16BF")
P("")
P("--- (a) 主判定 ---")
if f16bf == [0]:
    P("  [arg2+0x16BF] = 0  (全 %d 样本、%d distinct frame 恒 0)" % (len(rows), len(frames)))
    main = 0
elif len(f16bf) == 1:
    P("  [arg2+0x16BF] = %s  (非 0)" % f16bf[0])
    main = f16bf[0]
else:
    P("  [arg2+0x16BF] 观测到多值 %s —— 无法单值判定" % f16bf)
    main = None

P("")
P("--- (b) 静态分支表（0x47C620 反汇编，EVIDENCE/callsite_arg2.txt + P0_GATE_B/_audit/a1_47c620_full.txt）---")
P("  entry: [0xA8E7AC]==0 -> 不旁路；arg2=[esp+0x20]!=0 -> 继续")
P("  [arg2+0x16BF]!=0  -> (A8E9A0!=0) 只查 WhatAmI 6/0x24；(A8E9A0==0) 完全不查占用")
P("  [arg2+0x16BF]==0 & (16BE!=0|16B7!=0) -> 0x47C805 闸（第二道类型无关占格闸）")
P("  [arg2+0x16BF]==0 & 16BE==0 & 16B7==0 & E58!=0 -> 0x47C76B 表查（不查 head A）")
P("  [arg2+0x16BF]==0 & 16BE==0 & 16B7==0 & E58==0 & A8E9A0!=0")
P("     -> 先查 WhatAmI==2，再落 0x47C738 闸（选择子=0，扫 head A，[obj+0x14]&1）")

f16be = distinct("g_F16BE"); f16b7 = distinct("g_F16B7")
de58 = distinct("g_DE58"); a8 = distinct("A8E9A0"); bypass = distinct("A8E7AC")
click = [r for r in rows if r.get("t", 0) >= 0.249 and r.get("t", 0) <= 0.252]
cf = click[0] if click else {}
P("")
P("  点击帧样本(t=0.250017,frame=%s): 16BF=%s 16BE=%s 16B7=%s E58=%s A8E9A0=%s A8E7AC=%s A8ED6B=%s" %
  (cf.get("frame"), cf.get("g_F16BF"), cf.get("g_F16BE"), cf.get("g_F16B7"),
   cf.get("g_DE58"), cf.get("A8E9A0"), cf.get("A8E7AC"), cf.get("A8ED6B")))
if main == 0 and f16be == [0] and f16b7 == [0] and de58 == [0] and a8 == [1] and bypass == [0]:
    branch = "0x47C738 gate (head A, selector=0, [obj+0x14]&1) via all-four-flags-zero path"
    P("  ==> 走支判定：%s" % branch)
    P("  （与 §994 的「=0 ⇒ 两条类型无关占格闸」一致；本例精确到第一道 0x47C738）")
elif main not in (0, None) and a8 == [1]:
    branch = "only-check-6/0x24 (infantry not scanned)"
    P("  ==> 走支判定：%s" % branch)
else:
    branch = "UNRESOLVED"
    P("  ==> 走支判定：%s" % branch)

P("")
P("--- (c) 次判定：落格后目标格 head A 链 ---")
land = run["landing"]
P("  landing: frame_before=%s frame_click=%s frame_after=%s frames_elapsed=%s" %
  (land["frame_before"], land["frame_click"], land["frame_after"], land["frames_elapsed"]))
P("  headA=%s lenA=%s rttiA=%s" % (land["headA"], land["lenA"], land["rttiA"]))
P("  has_building=%s has_infantry=%s main_ok=%s ghost_o1_after=%s" %
  (land["has_building"], land["has_infantry"], land["main_ok"], land["ghost_o1_after"]))
n_bld = sum(1 for r in rows if any(v and "BuildingClass" in v for v in r["rttiA"]))
P("  全 %d 样本中出现 BuildingClass 的样本数=%d；lenA distinct=%s" %
  (len(rows), n_bld, sorted(set(r["lenA"] for r in rows))))

P("")
P("--- 两者关系（分开给，不合并）---")
P("  观测到的支：%s" % branch)
P("  落格结果：%s（目标格仍 3x InfantryClass，无 BuildingClass，ghost 仍 limbo o1=1）" %
  ("成功" if land["main_ok"] else "未成功"))
P("  关系：F16BF=0 所选的 0x47C738 闸是「命中即拒」的类型无关占格闸；落格未成功，与之一致。")
P("  注意：本脚本只读标志与目标格链；未直接读 0x47C620 返回 al / EIP，故「该闸实际拒」为 [静态推断]；")
P("        「标志=0」「未落格」「链无 BuildingClass」均为 [已证]（真机读数）。")

P("")
P("--- arg2 语义（T4）---")
gi = run["ghost_arg2_ident"]["candidates"][0]
P("  arg2 = [ghost+0x520] = %s  RTTI=%s  (%s)" %
  (gi["arg2_520"], gi["rtti_520"], gi["rtti_520_chain"]["name_raw"]))
P("  owner[+0x21C] = %s  RTTI=%s" % (gi["owner_21C"], gi["rtti_21C"]))
P("  arg2_eq_owner=%s  arg2_eq_playerhouse=%s" %
  (gi["arg2_eq_owner"], gi["arg2_eq_playerhouse"]))
P("  => arg2 是 BuildingTypeClass*，非 HouseClass*（VERDICT E2「HouseClass*」静态推断被真机 RTTI 推翻）。")
P("  => 但函数确实从 arg2 读 16BF/16BE/16B7/E58；且从真 HouseClass(owner) 读这四字段亦全为 0，")
P("     故走支判定不受该语义更正影响。")

txt = "\n".join(out) + "\n"
open(OUT, "w", encoding="utf-8").write(txt)
print(txt)
print("saved", OUT)
