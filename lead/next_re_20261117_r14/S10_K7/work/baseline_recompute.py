from __future__ import annotations
import datetime, json, os
from common import GAME, COVER, EV, BASE, sha256

def main():
    st=os.stat(COVER); gs=os.stat(GAME)
    now=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    lines=COVER.read_text(encoding="utf-8-sig",errors="replace").splitlines()
    hdr=lines[0].split("\t")
    rows=[]
    for ln in lines[1:]:
        if not ln.strip(): continue
        c=ln.split("\t")
        rows.append(c)
    s10=[c for c in rows if len(c)>=5 and c[1].strip().upper()=="S10"]
    proved=[c for c in s10 if c[4].strip()=="[已证]"]
    namedS=[c for c in s10 if c[2].strip() and not c[2].strip().startswith("sub_") and not c[2].strip().startswith("Class::sub_")]
    targets={}
    for e in ("006B7010","004E0E80"):
        targets[e]=[c for c in rows if c[0].strip().upper()==e]
    atlas=BASE.parent.parent.parent/"next_re_20261116_r12"/"W130_atlas"/"function_atlas.tsv"
    # fallback discover atlas if layout differs
    if not atlas.exists():
        hits=list(BASE.parent.parent.glob("*/W130_atlas/function_atlas.tsv"))
        atlas=hits[0] if hits else atlas
    atlas_entries=set()
    if atlas.exists():
        for ln in atlas.read_text(encoding="utf-8-sig",errors="replace").splitlines()[1:]:
            c=ln.split("\t")
            if c: atlas_entries.add(c[0].strip().upper())
    s10e={c[0].strip().upper() for c in s10}
    out={
      "sample_time_cst":now.isoformat(),
      "coverage_path":str(COVER),"coverage_size":st.st_size,
      "coverage_mtime_local":datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
      "coverage_sha256":sha256(COVER),
      "game_path":str(GAME),"game_size":gs.st_size,
      "game_mtime_local":datetime.datetime.fromtimestamp(gs.st_mtime,datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
      "game_sha256":sha256(GAME),
      "header_col5":hdr[4] if len(hdr)>4 else None,
      "coverage_data_rows":len(rows),"s10_rows":len(s10),"s10_proved_col5_all":len(proved),"s10_proved_pct_all":round(100*len(proved)/len(s10),6),
      "s10_atlas_proved_col5":sum(1 for c in s10 if c[0].strip().upper() in atlas_entries and c[4].strip()=="[已证]"),"s10_atlas_proved_pct":round(100*sum(1 for c in s10 if c[0].strip().upper() in atlas_entries and c[4].strip()=="[已证]")/len(s10e&atlas_entries),6),
      "s10_grade_col5_counts":{g:sum(1 for c in s10 if c[4].strip()==g) for g in ("[已证]","[静态推断]","[未证]")},
      "s10_named_S":len(namedS),"s10_atlas_entries":len(s10e&atlas_entries),"s10_outside_atlas":sorted(s10e-atlas_entries),
      "s10_outside_atlas_rows":[[c[0],c[4]] for c in s10 if c[0].strip().upper() in (s10e-atlas_entries)],
      "s10_atlas_path":str(atlas),"s10_atlas_exists":atlas.exists(),
      "target_rows":targets
    }
    (EV/"baseline_recompute.json").write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
