#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-KA 独立抽取 j_run.json 的进出局/下单/落格判定字段（不 import W177-J 脚本）。"""
import json, hashlib, os
RUN = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-J\EVIDENCE\j_run.json"
CK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-J\work\run_checkpoint.json"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177_KA\EVIDENCE\ka_run_fields.txt"
r = json.load(open(RUN, encoding='utf-8'))
c = json.load(open(CK, encoding='utf-8'))
P = []
def p(s=''):
    P.append(str(s)); print(s)
p('j_run sha256=' + hashlib.sha256(open(RUN,'rb').read()).hexdigest().upper())
p('checkpoint sha256=' + hashlib.sha256(open(CK,'rb').read()).hexdigest().upper())
p('j_run == run_checkpoint ? ' + str(r == c))
p('entry: nav_done=%s ingame_frame=%s player_house=%s' % (r.get('nav_done'), r.get('ingame_frame'), r.get('player_house')))
p('order: click.ok=%s pre_credits=%s post_credits=%s player_napowr_len=%s nap.o1_81=%s nap.o2_74=%s' % (
  r['order_click']['ok'], r['order_click']['pre_credits'], r['order_verify']['post_credits'],
  len(r['order_verify']['player_napowr']), r['order_verify']['player_napowr'][0]['o1_81'],
  r['order_verify']['player_napowr'][0]['o2_74']))
p('credits_built=%s credits_end=%s' % (r.get('credits_built'), r.get('credits_end')))
p('pickup.ok=%s closed_loop.ok=%s iters=%s cur=%s target=%s anchor=%s' % (
  r['pickup_click']['ok'], r['closed_loop']['ok'], r['closed_loop']['iters'], r['closed_loop']['cur'], r['target'], r['anchor']))
p('sampling: n=%s rate_claimed=%s distinct_frames=%s click_frame=%s covers=%s' % (
  r['sampling']['n_samples'], r['sampling']['rate_per_s'], r['sampling']['distinct_frames'],
  r['sampling']['click_frame'], r['sampling']['covers_click_frame']))
l = r['landing']
p('landing: main_ok=%s has_building=%s has_infantry=%s lenA=%s headA=%s rttiA=%s ghost_o1_after=%s frames_elapsed=%s' % (
  l['main_ok'], l['has_building'], l['has_infantry'], l['lenA'], l['headA'], l['rttiA'], l['ghost_o1_after'], l['frames_elapsed']))
p('flags_at_click=%s' % l['flags_at_click'])
gi = r['ghost_arg2_ident']['candidates'][0]
p('arg2: ptr=%s rtti=%s owner=%s owner_rtti=%s flags_arg2=%s flags_owner=%s' % (
  gi['arg2_520'], gi['rtti_520'], gi['owner_21C'], gi['rtti_21C'], gi['flags_arg2'], gi['flags_owner']))
p('JUDGEMENT: entered=%s ordered_deducted=%s picked_ghost=%s map_clicked=%s landed=%s refunded=%s' % (
  bool(r.get('nav_done') and r.get('ingame_frame',0)>0),
  r['order_verify']['post_credits'] < r['order_click']['pre_credits'],
  bool(r.get('pickup_click',{}).get('ok')),
  bool(r['landing'].get('frame_click') and r['closed_loop'].get('ok')),
  bool(l['main_ok']),
  r.get('credits_end',0) > 9400))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT,'w',encoding='utf-8').write('\n'.join(P)+'\n')
print('saved', OUT)
