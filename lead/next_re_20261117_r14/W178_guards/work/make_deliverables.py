"""Generate W178 coverage_delta.tsv and a compact numeric evidence file."""
import json
import os
import re

ROOT = r"D:\Project\ra2-campaign-forge"
CARD = os.path.join(ROOT, "lead", "next_re_20261117_r14", "W178_guards")
EVID = os.path.join(CARD, "EVIDENCE")
CORE = os.path.join(EVID, "w178_core.json")
COVERAGE = os.path.join(CARD, "coverage_delta.tsv")
FINAL = os.path.join(EVID, "FINAL_COUNTS.txt")
EVID_REL = r"lead/next_re_20261117_r14/W178_guards/EVIDENCE/w178_core.json"


def main():
    with open(CORE, "r", encoding="utf-8") as f:
        d = json.load(f)

    rows = []
    for r in d["sites"]:
        site = r["site_hex"].lower()
        fn = r["fn_hex"].lower()
        m = re.search(r"@ (0x[0-9a-f]+)", r["ecx_source"])
        load_site = m.group(1) if m else "unknown"
        if r["host_reachability_grade"] == "zero-static-ref":
            grade = "[未证]"
            reach = "host has 0 direct calls/0 dword refs/0 imm refs; runtime reachability unproven"
        else:
            grade = "[静态推断]"
            reach = f"host has {r['direct_caller_count']} direct caller(s); CFG reaches call"
        sem = (
            f"E8 direct call to FUN_00724730; this=ecx last written at {load_site} from [0x887368]; "
            f"0 ecx zero-tests after last write; {reach}; predicted AV EIP=0x724737 fault=0x250."
        )
        rows.append([
            site,
            "S02",
            f"guard_site_{site}_to_FUN_00724730",
            sem,
            grade,
            EVID_REL,
        ])

    six = d["site_6cd8cd"]
    callers = ",".join(f"{x:#x}" for x in six["direct_callers_of_fn"])
    rows.append([
        "006cd8cd",
        "S16",
        "sw_singleton_6cd8cd_unguarded_d250",
        (
            "FUN_006CC390 superweapon path; eax=[0x8871E0] @0x6CD8C2 then [eax+0x250] @0x6CD8CD "
            f"with no NULL test; jump-table case 9 reaches site; host callers {callers}; "
            "predicted AV EIP=0x6CD8CD fault=0x250."
        ),
        "[静态推断]",
        EVID_REL,
    ])

    with open(COVERAGE, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            assert all("\t" not in x for x in row)
            f.write("\t".join(row) + "\n")

    zero_static = [r for r in d["sites"] if r["host_reachability_grade"] == "zero-static-ref"]
    proven = [r for r in d["sites"] if r["host_reachability_grade"] == "static-ref"]
    lines = [
        "W178 final counts (all static; no game files written, no injection)",
        "",
        f"SHA256_OK={d['sha256_ok']}",
        f"full_text_skipdata_instructions={d['sweep']['insn_count']}",
        f"skipdata_bytes={d['sweep']['skipdata_bytes']}",
        f"direct_E8_calls_to_FUN_00724730={d['sweep']['calls_to_724730_count']}",
        f"verified_instruction_boundaries={sum(1 for r in d['sites'] if r.get('site_boundary'))}",
        f"ecx_last_write_from_[0x887368]={sum(1 for r in d['sites'] if '0x887368' in r.get('ecx_source',''))}",
        f"ecx_zero_tests_after_last_write_sites={sum(1 for r in d['sites'] if r.get('zero_guard',{}).get('ecx_zero_tests'))}",
        f"all_sites_CFG_reachable_from_host_entry={sum(1 for r in d['sites'] if r.get('reachable_from_fn_entry'))}",
        f"zero_static_ref_host_sites={len(zero_static)} " + " ".join(f"{r['site_hex']}@{r['fn_hex']}" for r in zero_static),
        f"proven_reachable_null_sites={len(proven)}",
        f"site_6CD8CD_reachable_with_12entry_jumptable={d['site_6cd8cd']['reachable_from_fn_entry']}",
        f"site_6CD8CD_direct_callers={','.join(f'{x:#x}' for x in d['site_6cd8cd']['direct_callers_of_fn'])}",
        "",
        "Recompute:",
        r"  python -X utf8 D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W178_guards\work\analyze.py",
        r"  python -X utf8 D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W178_guards\work\make_deliverables.py",
        "Channels: full .text capstone skipdata=True sweep (no atlas) + atlas interval containment;",
        "two atlas-hole functions were bounded independently by ret/nop padding.",
    ]
    with open(FINAL, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {len(rows)} coverage rows; proven={len(proven)} zero_static={len(zero_static)}")


if __name__ == "__main__":
    main()
