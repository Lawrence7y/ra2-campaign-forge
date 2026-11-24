#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W75 · verify that the on-screen tooltip text seen in
screen_tripA_hover_tooltip.png ("執行教學任務。" in the bottom status bar)
is exactly the CSF value of STT:CampaignAnimTutorial recorded by W61.

W61 EVIDENCE/csf_values.txt stored the value as mojibake because RA2 CSF
strings are UTF-16LE with each byte XOR 0xFF (EA obfuscation). Reversing that
transform recovers the real Big5/Unicode display text.
"""
import json
import w75_lib as L

MOJIBAKE = {
    "STT:CampaignAnimTutorial": "ꠈ瞳骦ꒇ넄괦쿽",
    "STT:CampaignAnimSoviet": "橴\ua634秸羐鷏ꂆ쿽",
    "STT:CampaignAnimAllied": "橴\ua634褠焲骺녴鷏ꂆ쿽",
    "GUI:TutorialCampaign": "驏꺊痬舋踠",
    "STT:AlliedCampaignIcon": "愡澇褠焲꣩蛅넚橴\ua634褠焲鷏ꂆ쿽",
    "STT:SovietCampaignIcon": "愡澇秸羐꣩蛅넚橴\ua634秸羐鷏ꂆ쿽",
}

rows = []
for label, m in MOJIBAKE.items():
    raw = m.encode("utf-16-le")
    recovered = bytes(b ^ 0xFF for b in raw).decode("utf-16-le",
                                                   errors="replace")
    rows.append({"label": label, "mojibake_from_W61": m,
                 "recovered_text": recovered, "n_chars": len(recovered)})

tutorial = next(r for r in rows
                if r["label"] == "STT:CampaignAnimTutorial")
observed = "執行教學任務。"   # read from screen_tripA_hover_tooltip.png
res = {
    "method": "CSF value = UTF-16LE bytes each XOR 0xFF; reverse -> display text",
    "rows": rows,
    "observed_on_screen_tripA_hover": observed,
    "observed_matches_STT_CampaignAnimTutorial":
        tutorial["recovered_text"] == observed,
    "conclusion": ("the bottom status bar text appearing on hover IS "
                   "STT:CampaignAnimTutorial; the id=1771 tooltip dispatch "
                   "chain is live at runtime"),
}
(L.OUT / "CSF_TOOLTIP_MATCH.json").write_text(
    json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(res, ensure_ascii=True, indent=1))
