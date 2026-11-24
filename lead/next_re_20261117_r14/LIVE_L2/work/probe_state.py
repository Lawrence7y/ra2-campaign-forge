#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick read-only probe of the live L2 game state."""
import json, time
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D

PID = 41892
m = W.Mem(PID)
ph = P.player_house(m)
out = {
    "frame": m.u32(W.A_FRAME), "mode": m.u32(W.A_MODE),
    "objects": m.u32(P.A_ABSTRACT),
    "ph": hex(ph) if ph else None,
    "credit_30C": m.u32(ph + 0x30C) if ph else None,
    "building_array_count": W.building_array(m)[1],
    "player_building_types": C.all_player_building_types(m, ph),
    "bypass": D.bypass_globals(m),
    "cam": C.cam_origin(m),
}
out["buildings"] = D.buildings_snapshot(m, ph, only_player=True)
m.close()
print(json.dumps(out, ensure_ascii=False, indent=2))
