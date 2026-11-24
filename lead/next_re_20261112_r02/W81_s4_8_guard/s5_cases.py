"""W60 / S5 -- six NEW offline regression cases for battlemd.mode=inplace.

Bound into regress_dlc_v15.py via bind_s5(globals()); every case uses the
EXACT SAME Case harness as the 90 inherited cases.  Pure offline: no game
launched, no attach, only this card's sandbox/ and out/ are written.

  INPLACE1 install -> .bak + SOV1 rewrite + manifest original SHA-256
  INPLACE2 uninstall -> byte-exact restore (measured SHA equality)
  INPLACE3 hand-edit after install -> verify reports drift, non-zero exit
  INPLACE4 pre-existing .bak -> explicit REFUSAL (INPLACE_BACKUP_ORPHAN)
  INPLACE5 battlemd.mode=off + csf on -> K2 still HARD REFUSES (not weakened)
  INPLACE6 BATTLEMD98.INI append route (b) is NOT mistaken for inplace
"""
from __future__ import annotations

import json


class _NS:
    pass


G = _NS()


def bind_s5(g: dict) -> None:
    for k, v in g.items():
        if not k.startswith("__"):
            setattr(G, k, v)
    G.V15_ROOT = G.V12_ROOT
    G.CARD = G.W43_ROOT


def _w(path, obj) -> None:
    G.w(path, json.dumps(obj, indent=2, ensure_ascii=False))


def _fsfile(c, name: str, obj: dict):
    p = c.dir / name
    _w(p, obj)
    return p


def _design(tag: str, package_id: str = "org.ra2forge.w60") -> dict:
    d = G._ms_design(tag, ["CP1", "CP2"], package_id=package_id)
    d["campaign"]["description"] = "W60 inplace regression campaign."
    return d


def _official_bytes() -> bytes:
    return (G.V15_ROOT / "ra2forge" / "data" /
            "BATTLEMD.OFFICIAL.INI").read_bytes()


def _inplace_fs(fsid: str, scenario: str = "ECH01.MAP") -> dict:
    return {
        "schema_version": "w42-s2-1", "kind": "feature_set",
        "feature_set_id": fsid,
        "features": {
            "maps": {"mode": "sideload",
                     "map_files": ["CP1.MAP", "CP2.MAP"],
                     "chain": ["CP1", "CP2"]},
            "battlemd": {"mode": "inplace", "scenario": scenario,
                         "description_ref": "raw"},
            "mix": {"mode": "repack",
                    "source_map_set": ["CP1.MAP", "CP2.MAP"],
                    "target_name": "expandmd98.mix"},
            "csf": {"mode": "off"},
            "mapselmd": {"mode": "off"},
        },
    }


def _full_csf() -> dict:
    return {"mode": "clone_append", "base": "official_full_clone",
            "official_label_count": 5211, "labels": ["RA2F:00000001"],
            "target_name": "ra2md.csf", "official_full_min": 5211}


def _s0() -> dict:
    return {
        "schema_version": "w42-s2-1", "kind": "sandbox_initial_state",
        "sandbox_id": "S0", "game_dir": "<fixture>",
        "present_files": [{"name": "BATTLEMD.INI", "size_bytes": 2733,
                           "kind": "official_loose"}],
        "absent_files": ["BATTLEMD98.INI", "CP1.MAP", "CP2.MAP",
                         "expandmd98.mix", "ra2md.csf", "MAPSELMD.INI"],
        "guard_state": "KNOWN_GOOD", "baseline_adjudicated": True,
        "game_process_count": 0,
    }


def _build(c, design: dict, tag: str, extra=()) -> tuple:
    dp = c.dir / f"design_{tag}.json"
    _w(dp, design)
    out_dir = c.dir / f"out_{tag}"
    rc, out, err = c.run_module(
        G.V15_ROOT, ["build", "--design", str(dp), "--out", str(out_dir),
                     *extra], f"v15-build-{tag}")
    return rc, out, err, out_dir / design["campaign"]["name"]


def _golden_official(c, sub: str = ""):
    """Inert golden game dir whose BATTLEMD.INI is the REAL official 2733 B
    baseline (make_golden's own BATTLEMD.INI is only a tiny inert fixture)."""
    game = c.dir / ("game" + sub)
    G.make_golden(game)
    (game / "BATTLEMD.INI").write_bytes(_official_bytes())
    return game


def _install(c, pkg, game, fpath, extra=()) -> tuple:
    return c.run_module(
        G.V15_ROOT,
        ["install", "--package", str(pkg), "--game", str(game),
         "--feature-set", str(fpath), *extra], "v15-install")


def _manifest(game) -> dict:
    return json.loads((game / G.MANIFEST).read_text(encoding="utf-8"))


def _sha(data: bytes) -> str:
    return G.hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# INPLACE1 -- install creates .bak, rewrites [SOV1], records original SHA-256
# ---------------------------------------------------------------------------

def case_INPLACE1(fx) -> object:
    c = G.Case("INPLACE1")
    fs = _fsfile(c, "fs_inplace1.json", _inplace_fs("W60-INPLACE1"))
    d = _design("W60IP1")
    rc_b, o_b, e_b, pkg = _build(c, d, "ip1", ["--feature-set", str(fs)])
    c.check("INPLACE1a: inplace build exits 0 and ships BATTLEMD.INI "
            "(NOT BATTLEMD98.INI)",
            rc_b == 0 and (pkg / "BATTLEMD.INI").is_file()
            and not (pkg / "BATTLEMD98.INI").exists(), o_b + e_b)
    official = _official_bytes()
    orig_sha = _sha(official)
    c.check("INPLACE1b: package BATTLEMD.INI = 2730 B, only [SOV1] Scenario "
            "changed, CRLF preserved",
            (pkg / "BATTLEMD.INI").stat().st_size == 2730
            and b"Scenario=ECH01.MAP" in (pkg / "BATTLEMD.INI").read_bytes()
            and b"\r\n" in (pkg / "BATTLEMD.INI").read_bytes()
            and b"Scenario=SOV01umd.MAP" not in
            (pkg / "BATTLEMD.INI").read_bytes(),
            o_b + e_b)

    g = _golden_official(c)
    before = (g / "BATTLEMD.INI").read_bytes()
    rc_i, o_i, e_i = _install(c, pkg, g, fs)
    c.check("INPLACE1c: inplace install exits 0", rc_i == 0, o_i + e_i)
    bak = g / "BATTLEMD.INI.ra2forge.bak"
    c.check("INPLACE1d: BATTLEMD.INI.ra2forge.bak created, BYTE-IDENTICAL to "
            "the official original",
            bak.is_file() and bak.read_bytes() == before == official,
            o_i + e_i)
    after = (g / "BATTLEMD.INI").read_bytes()
    c.check("INPLACE1e: game-dir BATTLEMD.INI is rewritten IN PLACE (2730 B, "
            "SOV1 Scenario=ECH01.MAP), no extra BATTLEMD*.INI file",
            len(after) == 2730 and b"Scenario=ECH01.MAP" in after
            and b"Scenario=SOV01umd.MAP" not in after
            and not (g / "BATTLEMD98.INI").exists(), o_i + e_i)
    m = _manifest(g)
    e = [x for x in m["files"] if x["name"] == "BATTLEMD.INI"]
    c.check("INPLACE1f: manifest records original_sha256 (== official), "
            "original_size_bytes=2733, post_install_sha256 and backup slot",
            len(e) == 1
            and e[0].get("original_sha256") == orig_sha
            and e[0].get("original_size_bytes") == 2733
            and e[0].get("post_install_sha256") == e[0].get("sha256")
            and e[0].get("backup") == "BATTLEMD.INI.ra2forge.bak",
            str(e))
    c.check("INPLACE1g: manifest embeds the inplace_rewrite preflight report",
            m.get("inplace_rewrite", {}).get("applicable") is True
            and m["inplace_rewrite"].get("official_baseline_matched") is True,
            str(m.get("inplace_rewrite")))
    return c


# ---------------------------------------------------------------------------
# INPLACE2 -- uninstall restores the original BYTE-FOR-BYTE (measured SHA)
# ---------------------------------------------------------------------------

def case_INPLACE2(fx) -> object:
    c = G.Case("INPLACE2")
    fs = _fsfile(c, "fs_inplace2.json", _inplace_fs("W60-INPLACE2"))
    rc_b, o_b, e_b, pkg = _build(
        c, _design("W60IP2"), "ip2", ["--feature-set", str(fs)])
    c.check("INPLACE2a: inplace build exits 0", rc_b == 0 and pkg.is_dir(),
            o_b + e_b)
    g = _golden_official(c)
    original = (g / "BATTLEMD.INI").read_bytes()
    orig_sha = _sha(original)
    rc_i, o_i, e_i = _install(c, pkg, g, fs)
    c.check("INPLACE2b: inplace install exits 0", rc_i == 0, o_i + e_i)
    m = _manifest(g)
    recorded = [x for x in m["files"] if x["name"] == "BATTLEMD.INI"][0]
    c.check("INPLACE2c: recorded original_sha256 equals the real original",
            recorded["original_sha256"] == orig_sha, str(recorded))
    rc_u, o_u, e_u = c.uninstall()
    c.check("INPLACE2d: uninstall exits 0 and reports the restore",
            rc_u == 0
            and "restored   BATTLEMD.INI.ra2forge.bak -> BATTLEMD.INI" in o_u,
            o_u + e_u)
    back = (g / "BATTLEMD.INI").read_bytes()
    c.check("INPLACE2e: restored BATTLEMD.INI is BYTE-IDENTICAL to the official "
            "original (measured SHA-256 equality)",
            back == original and _sha(back) == orig_sha
            == recorded["original_sha256"], f"{len(back)} B " + o_u + e_u)
    c.check("INPLACE2f: backup slot consumed; no manifest/seal residue",
            not (g / "BATTLEMD.INI.ra2forge.bak").exists()
            and not (g / G.MANIFEST).exists(), o_u + e_u)
    return c


# ---------------------------------------------------------------------------
# INPLACE3 -- hand-edit after install => verify detects drift, non-zero exit
# ---------------------------------------------------------------------------

def case_INPLACE3(fx) -> object:
    c = G.Case("INPLACE3")
    fs = _fsfile(c, "fs_inplace3.json", _inplace_fs("W60-INPLACE3"))
    rc_b, o_b, e_b, pkg = _build(
        c, _design("W60IP3"), "ip3", ["--feature-set", str(fs)])
    g = _golden_official(c)
    rc_i, o_i, e_i = _install(c, pkg, g, fs)
    c.check("INPLACE3a: install exits 0", rc_i == 0, o_i + e_i)
    rc_v0, o_v0, e_v0 = c.verify()
    c.check("INPLACE3b: verify BEFORE hand edit is clean (exit 0)",
            rc_v0 == 0, o_v0 + e_v0)
    p = g / "BATTLEMD.INI"
    drifted = p.read_bytes().replace(b"Scenario=ECH01.MAP",
                                     b"Scenario=HANDEDIT.MAP")
    c.check("INPLACE3c: hand edit actually changed the bytes",
            drifted != p.read_bytes())
    p.write_bytes(drifted)
    rc_v, o_v, e_v = c.verify()
    c.check("INPLACE3d: verify AFTER hand edit exits NON-ZERO (drift detected)",
            rc_v != 0, f"rc={rc_v} " + o_v + e_v)
    c.check("INPLACE3e: verify names BATTLEMD.INI as changed / sha mismatch",
            "BATTLEMD.INI" in (o_v + e_v)
            and ("changed" in (o_v + e_v).lower()
                 or "mismatch" in (o_v + e_v).lower()
                 or "drift" in (o_v + e_v).lower()),
            o_v + e_v)
    return c


# ---------------------------------------------------------------------------
# INPLACE4 -- pre-existing .bak => explicit refusal, zero writes
# ---------------------------------------------------------------------------

def case_INPLACE4(fx) -> object:
    c = G.Case("INPLACE4")
    fs = _fsfile(c, "fs_inplace4.json", _inplace_fs("W60-INPLACE4"))
    rc_b, o_b, e_b, pkg = _build(
        c, _design("W60IP4"), "ip4", ["--feature-set", str(fs)])
    c.check("INPLACE4a: inplace build exits 0", rc_b == 0, o_b + e_b)
    g = _golden_official(c)
    orphan = b"UNRECORDED USER BACKUP - MUST NEVER BE OVERWRITTEN\n"
    (g / "BATTLEMD.INI.ra2forge.bak").write_bytes(orphan)
    before = G.sha_tree(g)
    rc_i, o_i, e_i = _install(c, pkg, g, fs)
    c.check("INPLACE4b: install REFUSED with INPLACE_BACKUP_ORPHAN (exit 34); "
            "explicit, not silent",
            rc_i == 34 and "INPLACE_BACKUP_ORPHAN" in (o_i + e_i),
            f"rc={rc_i} " + o_i + e_i)
    c.check("INPLACE4c: ZERO writes, orphan .bak untouched, no manifest",
            G.sha_tree(g) == before
            and (g / "BATTLEMD.INI.ra2forge.bak").read_bytes() == orphan
            and not (g / G.MANIFEST).exists(), o_i + e_i)
    return c


# ---------------------------------------------------------------------------
# INPLACE5 -- battlemd.mode=off + csf on => K2 STILL hard refuses
# ---------------------------------------------------------------------------

def case_INPLACE5(fx) -> object:
    c = G.Case("INPLACE5")
    f = _inplace_fs("W60-INPLACE5")
    f["features"]["battlemd"] = {"mode": "off"}
    f["features"]["csf"] = _full_csf()
    fs = _fsfile(c, "fs_off_csf.json", f)
    sb = _fsfile(c, "s0.json", _s0())
    rc_r, o_r, e_r = c.run_module(
        G.V15_ROOT, ["resolve", "--feature-set", str(fs),
                     "--sandbox", str(sb)], "v15-resolve-k2")
    c.check("INPLACE5a: resolve reports K2 CSF_WITHOUT_BATTLEMD and "
            "coupling_passed=false (K2 NOT weakened by W60)",
            "CSF_WITHOUT_BATTLEMD" in o_r
            and '"coupling_passed": false' in o_r, o_r + e_r)
    # a DEFAULT (no --feature-set) package for the install path
    rc_b, o_b, e_b, pkg = _build(c, _design("W60IP5"), "ip5")
    c.check("INPLACE5b: default build exits 0", rc_b == 0, o_b + e_b)
    g = _golden_official(c)
    before = G.sha_tree(g)
    rc_i, o_i, e_i = _install(c, pkg, g, fs)
    c.check("INPLACE5c: install REFUSED (exit 26 RESOLVE_COUPLING_REFUSED), "
            "ZERO writes",
            rc_i == 26 and "RESOLVE_COUPLING_REFUSED" in (o_i + e_i),
            f"rc={rc_i} " + o_i + e_i)
    c.check("INPLACE5d: no BATTLEMD.INI.ra2forge.bak, game dir unchanged",
            G.sha_tree(g) == before
            and not (g / "BATTLEMD.INI.ra2forge.bak").exists(), o_i + e_i)
    return c


# ---------------------------------------------------------------------------
# INPLACE6 -- append route (b) is NOT mistaken for inplace (mode isolation)
# ---------------------------------------------------------------------------

def case_INPLACE6(fx) -> object:
    c = G.Case("INPLACE6")
    f = _inplace_fs("W60-INPLACE6")
    f["features"]["battlemd"] = {"mode": "append", "ids": ["BATTLE01"],
                                 "description_ref": "raw"}
    fs = _fsfile(c, "fs_append.json", f)
    code = f"""
import sys, json
sys.path.insert(0, {str(G.V15_ROOT)!r})
from ra2forge import feature_subset as FS
p = FS.resolve(FS.load_json({str(fs)!r}), FS.load_json({str(_fsfile(c, 's0b.json', _s0()))!r}))
print(json.dumps({{"shipped": p["shipped"],
                   "bm_row": [r["action"] for r in p["files"]
                              if r["name"] == "BATTLEMD.INI"][0]}}))
"""
    rc_p, o_p, e_p = c.run_python(G.V15_ROOT, code, "v15-append-plan")
    try: pl = json.loads(o_p.strip().splitlines()[-1])
    except (ValueError, IndexError): pl = {}
    c.check("INPLACE6a: append plan ships BATTLEMD98.INI (NOT BATTLEMD.INI) "
            "and marks the official file LEAVE",
            "BATTLEMD98.INI" in pl.get("shipped", [])
            and "BATTLEMD.INI" not in pl.get("shipped", [])
            and pl.get("bm_row") == "LEAVE", str(pl))
    rc_b, o_b, e_b, pkg = _build(
        c, _design("W60IP6"), "ip6", ["--feature-set", str(fs)])
    c.check("INPLACE6b: append build emits BATTLEMD98.INI, NOT BATTLEMD.INI",
            rc_b == 0 and (pkg / "BATTLEMD98.INI").is_file()
            and not (pkg / "BATTLEMD.INI").exists(), o_b + e_b)
    g = _golden_official(c)
    official = (g / "BATTLEMD.INI").read_bytes()
    rc_i, o_i, e_i = _install(c, pkg, g, fs)
    c.check("INPLACE6c: append install exits 0", rc_i == 0, o_i + e_i)
    c.check("INPLACE6d: official BATTLEMD.INI is BYTE-IDENTICAL after append "
            "install; NO inplace backup slot",
            (g / "BATTLEMD.INI").read_bytes() == official
            and not (g / "BATTLEMD.INI.ra2forge.bak").exists(), o_i + e_i)
    m = _manifest(g)
    c.check("INPLACE6e: manifest has NO inplace_rewrite block (route (b) was "
            "never treated as inplace)",
            "inplace_rewrite" not in m
            and all(x.get("name") != "BATTLEMD.INI" for x in m["files"]),
            str(list(m.keys())))
    return c


S5_CASES = {
    "INPLACE1": case_INPLACE1, "INPLACE2": case_INPLACE2,
    "INPLACE3": case_INPLACE3, "INPLACE4": case_INPLACE4,
    "INPLACE5": case_INPLACE5, "INPLACE6": case_INPLACE6,
}