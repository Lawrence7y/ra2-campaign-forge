#!/usr/bin/env python3
"""W131k: find and identify an ENTRY POINT for every subsystem that still lacks one.

Milestone (4) requires "at least 6 subsystems' entry points AND key structures".
Structures exist for 23 subsystems, but dedicated entry evidence existed only for
~7. This closes that: for each subsystem, rank its members by how many DISTINCT
OUTSIDE callers they have (that is what makes something an entry), then label the
top candidates with their own strings / first import.

Deliberately NOT used: "largest function" (that identifies hot code, not entries)
and address order.
"""
import collections
import io
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.join(os.path.dirname(HERE), "W130_atlas")

TARGETS = ["Graphics_Blit_Shape", "Render_DDraw_Display", "Video_Bink",
           "Audio_Sound_Music", "SaveLoad", "AI_Team_Script", "File_Mix_FS",
           "Movement_Locomotion", "Ini_Rules_DB", "Sidebar_Radar_HUD",
           "Tactical_MapView", "Campaign_Meta", "WDT_WorldDom",
           "Input_Commands_Mouse", "MP_Lobby_Session", "WOL_Online",
           "Superweapon_Special", "Config_Registry", "File_Stream_Crypto",
           "Menus_Main_Intro", "Misc_Util_Mem", "Main_Init_Flow"]


def main():
    fns = {}
    with io.open(os.path.join(ATLAS, "function_atlas.tsv"), encoding="utf-8") as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            p = line.rstrip("\n").split("\t")
            d = dict(zip(hdr, p))
            fns[int(d["entry"], 16)] = d

    label = {}
    with io.open(os.path.join(HERE, "fn_subsystem_canonical.tsv"), encoding="utf-8") as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            label[int(p[0], 16)] = p[2]

    callees = collections.defaultdict(set)
    callers = collections.defaultdict(set)
    with io.open(os.path.join(HERE, "calledges.raw.log"), encoding="utf-8",
                 errors="replace") as f:
        for ln in f:
            m = re.search(r"CallEdges\.java> ([0-9a-f]{8})\t([0-9a-f]{8})\t", ln)
            if not m:
                continue
            a, b = int(m.group(1), 16), int(m.group(2), 16)
            callees[a].add(b)
            callers[b].add(a)

    members = collections.defaultdict(set)
    for e, s in label.items():
        if s != "UNASSIGNED":
            members[s].add(e)

    report = {}
    print("=== entry candidates per subsystem "
          "(ranked by #distinct OUTSIDE callers) ===")
    for sub in TARGETS:
        ms = members.get(sub, set())
        if not ms:
            continue
        cand = []
        for e in ms:
            outside = [c for c in callers.get(e, ()) if label.get(c) != sub]
            if outside:
                cand.append((len(outside), len(callees.get(e, set())), e, outside))
        cand.sort(reverse=True)
        top = cand[:3]
        report[sub] = []
        print("\n--- %s  (%d members, %d with outside callers)" % (sub, len(ms), len(cand)))
        for nout, ncal, e, outside in top:
            d = fns.get(e, {})
            imp = d.get("first_import", "") or ""
            st = (d.get("strings", "") or "")[:90]
            who = ", ".join("%s[%s]" % ("0x%08X" % c, label.get(c, "?"))
                            for c in outside[:3])
            print("   0x%08X  outside=%-3d callees=%-4d size=%-6s imp=%-16s"
                  % (e, nout, ncal, d.get("size", "?"), imp[:16]))
            print("        callers: %s" % who)
            print("        strings: %s" % (st or "(none)"))
            report[sub].append({"entry": "0x%08X" % e, "outside_callers": nout,
                                "callees": ncal, "size": int(d.get("size", 0)),
                                "import": imp, "strings": st,
                                "callers": ["0x%08X" % c for c in outside[:6]]})

    json.dump(report, open(os.path.join(HERE, "subsystem_entries.json"), "w"), indent=1)
    with io.open(os.path.join(HERE, "subsystem_entries.tsv"), "w", encoding="utf-8") as f:
        f.write("subsystem\tentry\toutside_callers\tn_callees\tsize\tfirst_import\tstrings\n")
        for sub, lst in report.items():
            if not lst:
                continue
            t = lst[0]
            f.write("%s\t%s\t%d\t%d\t%d\t%s\t%s\n"
                    % (sub, t["entry"], t["outside_callers"], t["callees"], t["size"],
                       t["import"], t["strings"].replace("\t", " ")))
    print("\nwrote subsystem_entries.json / subsystem_entries.tsv")


if __name__ == "__main__":
    main()
