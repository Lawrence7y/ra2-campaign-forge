"""Compile a campaign design (design.py) into game-ready files.

Outputs (all inside <out>/<CampaignName>/):
  *.MAP                 mission maps, chained through [Basic] NextScenario
  BATTLEMD98.INI        appended campaign entry picked up by the engine's
                        BATTLEMD*.INI filesystem wildcard (the official
                        BATTLEMD.INI is never written to - see below)
  expandmd98.mix        map archive (maps only; never any INI)
  BUILD_REPORT.txt      build log: chain, artifacts, sha256, self-check results
  story.md              human-readable storyline dump
  INSTALL.txt           manual install / uninstall notes

Packaging contract (FORGE-1 plan B):
- The engine loads the battle lists with FindFirstFileA("BATTLEMD*.INI")
  (VA 0x52CBA0 -> IAT 0x7E1208) and merges what it finds by battle id
  (0x46CE10). That wildcard only ever sees *loose* files in the game
  directory, so a BATTLEMD*.INI packed inside a MIX is dead code - the package
  therefore ships the INI loose and keeps expandmd98.mix free of INI files.
- Because entries merge by id, re-using ALL1/SOV1 would override the official
  campaign entry in a directory-order-dependent way. The generated file
  therefore uses its own id (default "RA2F1", overridable through the optional
  design field campaign.id) and only *appends* a campaign.
- Description is the campaign-level blurb from campaign.description (R3) and
  the mission that ends the campaign is written EndOfGame=yes (R5).
- Install/uninstall live in ra2forge.install (per-file backups + manifest +
  exact restore).

Usage:
  python -m ra2forge build --design X --out out [--install <game dir>]
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from . import csf as csf_mod
from . import design as design_mod
from . import mapselmd as mapselmd_mod
from .install import (
    PACKAGE_MANIFEST_NAME, MANIFEST_NAME, SEAL_NAME, BACKUP_SUFFIX,
    STAGE_INFIX,
)
from .maplib import MissionMap, STANDARD_HOUSES, read_basic_section
from . import triggers as tg
from .mixlib import MixFile, crc_hash, write_mix

HOUSE_INDEX = design_mod.HOUSE_INDEX
SIDES = design_mod.SIDES

BATTLE_FILE_NAME = "BATTLEMD98.INI"   # loose file matching BATTLEMD*.INI on the FS
MIX_FILE_NAME = "expandmd98.mix"
# the official battlemd.ini numbers its [Battles] list 1..14 (RA2 ships the
# ALL02..SOV07 debug placeholders); a fresh index keeps the two lists apart.
# R1 keeps FORGE-1's "never occupy an official index" strategy: we append at 15
# with our own entry id (default RA2F1) instead of rewriting an official entry.
BATTLE_INDEX = 15


class BuildError(RuntimeError):
    """Raised when a build self-check fails (e.g. the NextScenario chain)."""


def build(design: dict, out_dir: str | Path, *,
          csf_out: str | Path | None = None,
          csf_base: str | Path | None = None,
          mapselmd: bool = False,
          mapselmd_base: str | Path | None = None,
          install_game_dir: str | Path | None = None,
          allow_csf_out_in_game: bool = False,
          feature_set=None, sandbox_state=None,
          guard_state: str | None = None,
          plan_report=None, resolve_plan_out=None) -> Path:
    """Compile design into <out_dir>/<CampaignName>/ and return the MIX path.

    W46/S4: with the OPT-IN ``feature_set`` switch, resolve() runs BEFORE the
    first output byte; the plan drives the optional game-dir artifacts and a
    per-file plan-vs-actual reconciliation is emitted. With feature_set=None
    every branch below is byte-for-byte v13's.

    Self-checks (hard failures, not warnings):
      1. every written .MAP is read back from disk and its [Basic] NextScenario
         must match the design's mission order;
      2. the written MIX must contain exactly the map files and no INI.

    When csf_out is provided (CLI --csf-out PATH) and campaign.description is
    non-empty, BATTLEMD98.INI Description= is written as a stable CSF label
    (RA2F:<hash>) instead of raw text, the CSF file at csf_out is created or
    updated (optionally cloned from csf_base first), a ready-to-use ra2md.csf
    plus csf_patch.json are emitted in the package directory, and BUILD_REPORT
    records the exact CSF target/label/text mapping. When csf_out is None
    (default), behavior is byte-for-byte identical to v0.9.
    W34: when mapselmd=True (CLI --mapselmd) a COMPLETE clone of the official
    MAPSELMD.INI plus our appended stages is emitted as a loose file; with
    mapselmd=False (default) NOTHING about the build changes - the output is
    byte-for-byte identical to v10. A minimal (our-stages-only) MAPSELMD.INI
    is a hard error, never generated.
    """
    warnings = design_mod.validate(design)
    camp = design["campaign"]
    missions = design["missions"]
    raw_desc = design_mod.description_for(camp)
    out = Path(out_dir) / _fs_safe(camp["name"])

    # ---- W46/S4: resolve() BEFORE the first output byte (opt-in only) -----
    # With feature_set=None, eff_csf_out/eff_mapselmd are EXACTLY the caller's
    # switches, so the default build is byte-for-byte v13.
    feature_plan = None
    eff_csf_out = csf_out
    eff_mapselmd = mapselmd
    build_gate = None
    if feature_set is not None:
        from . import resolve_integration as RI
        feature_plan = RI.build_resolve(
            feature_set, sandbox_state, guard_state=guard_state,
            resolve_plan_out=resolve_plan_out)
        design_map_names = [f"{m['name'].upper()}.MAP" for m in missions]
        build_gate = RI.build_effective_switches(
            feature_plan, design_map_names=design_map_names,
            csf_out=csf_out, csf_base=csf_base, mapselmd=mapselmd,
            mapselmd_base=mapselmd_base, raw_desc=raw_desc, out=out)
        eff_csf_out = build_gate["csf_out"]
        eff_mapselmd = build_gate["mapselmd"]

    inplace = (feature_plan is not None
               and "BATTLEMD.INI" in feature_plan.get("shipped", [])
               and "BATTLEMD98.INI" not in feature_plan.get("shipped", []))
    # W41 (W38 CRITICAL): the --csf-out ownership guard runs BEFORE the first
    # byte of the build is written. A --csf-out landing inside a game directory
    # is an install-level write entry and is REFUSED by default, so a refused
    # build leaves ZERO output (not even a partial package dir).
    check_lines: list[str] = []
    csf_guard: dict | None = None
    if eff_csf_out is not None and raw_desc:
        csf_guard = _csf_out_ownership_guard(
            Path(eff_csf_out),
            install_game_dir=(Path(install_game_dir)
                              if install_game_dir is not None else None),
            allow_csf_out_in_game=allow_csf_out_in_game,
            check_lines=check_lines)

    out.mkdir(parents=True, exist_ok=True)

    story: list[str] = [f"# {camp['name']}", ""]
    if camp.get("description"):
        story += [camp["description"], ""]

    # --- 1. compile every mission, chaining NextScenario in design order ---
    chain = mission_chain(missions)
    compiled: list[tuple[str, MissionMap]] = []
    for i, m in enumerate(missions):
        mmap, mission_warnings = _build_mission(m, i, design)
        mmap.next_scenario = chain[i]
        # R5: the mission that ends the campaign carries EndOfGame=yes (same
        # convention as the official final missions)
        mmap.end_of_game = not chain[i]
        compiled.append((f"{m['name'].upper()}.MAP", mmap))
        story.append(f"## Mission {i + 1}: {m.get('title', m['name'])}")
        story.append("")
        if m.get("briefing"):
            story.append(m["briefing"])
            story.append("")
        for w in mission_warnings:
            warnings.append(f"{m['name']}: {w}")

    map_texts: dict[str, str] = {}
    for map_name, mmap in compiled:
        text = mmap.to_ini_text()
        map_texts[map_name] = text
        _write_map_file(out / map_name, text)

    # --- 2. P0 self-check: read the maps back from disk, verify the chain ---
    check_lines.extend(_verify_next_scenario_chain(out, compiled, chain))

    # --- 3. campaign registry: a loose, additive BATTLEMD98.INI -----------
    battle_id = battle_id_for(camp)
    desc_override: str | None = None
    csf_label: str | None = None
    if eff_csf_out is not None and raw_desc:
        csf_label = csf_label_for(design, battle_id)
        desc_override = csf_label

    if inplace:
        # W60 (a): emit the OFFICIAL loose BATTLEMD.INI, byte-exactly rewritten
        # in its [SOV1] section.  NO BATTLEMD98.INI is produced (that is route
        # (b), rejected by LEAD_VERIFY_W37 2.3 for duplicate IDs).
        from . import battlemd_inplace as BI
        from . import resolve_integration as RI
        fs_obj = RI.load_json_obj(feature_set, "feature-set")
        bm = fs_obj.get("features", {}).get("battlemd", {})
        scen = bm.get("scenario") or (chain[0] + ".MAP" if chain else "ECH01.MAP")
        rewritten, rep = BI.rewrite_sov1(
            BI.official_bytes(), scen, cd=bm.get("cd"),
            final_movie=bm.get("final_movie"),
            description=bm.get("description"))
        (out / BI.OFFICIAL_NAME).write_bytes(rewritten)
        check_lines.append(
            f"  [PASS] W60 inplace SOV1 rewrite: {rep['before_bytes']} B -> "
            f"{rep['after_bytes']} B, scenario={scen}, "
            f"keys_added={rep['keys_added']}, eol={rep['line_ending']}, "
            f"diff_lines={len(rep['diff'])}")
    else:
        _write_map_file(
            out / BATTLE_FILE_NAME,
            _battle_ini(camp, missions, battle_id, desc_override=desc_override),
        )
        check_lines.extend(
            _verify_battle_file(out, camp, missions, battle_id,
                                desc_override=desc_override)
        )

    # --- 4. MIX carries maps only (no INI may ever end up in it) ----------
    mix_files = {name: text.encode("gbk", errors="replace")
                 for name, text in map_texts.items()}
    mix_path = write_mix(out / MIX_FILE_NAME, mix_files, include_database=False)
    check_lines.append(_verify_mix_contents(mix_path, sorted(mix_files)))

    (out / "story.md").write_text("\n".join(story) + "\n", encoding="utf-8")
    pkg_id_str = _write_package_identity(out, design)

    # --- W34: full-clone MAPSELMD.INI registration (opt-in only) ----------
    mapsel_info: dict | None = None
    if eff_mapselmd:
        mapsel_info = _emit_mapselmd(out, design, missions, chain,
                                     mapselmd_base, check_lines)

    csf_info: dict | None = None
    if eff_csf_out is not None:
        if raw_desc and csf_label is not None:
            csf_info = _emit_csf_artifacts(
                out=out,
                csf_out=Path(eff_csf_out),
                csf_base=Path(csf_base) if csf_base is not None else None,
                csf_label=csf_label,
                csf_text=raw_desc,
                battle_id=battle_id,
                pkg_id=pkg_id_str,
                check_lines=check_lines,
                guard_report=csf_guard,
                install_game_dir=(Path(install_game_dir)
                                  if install_game_dir is not None else None),
                allow_csf_out_in_game=allow_csf_out_in_game,
            )
        else:
            csf_info = {
                "enabled": True,
                "skipped": "campaign.description is empty; no CSF label emitted",
                "csf_out": str(eff_csf_out),
            }

    if feature_plan is not None:
        check_lines.append(
            f"  [PASS] W46/S4 plan-driven build: feature_set_id="
            f"{feature_plan['feature_set_id']} shipped="
            f"{sorted(feature_plan['shipped'])} plan_driven="
            f"{build_gate['plan_driven']}")

    _write_build_report(out, camp, compiled, chain, battle_id, check_lines,
                        pkg_id_str, csf_info=csf_info,
                        mapsel_info=mapsel_info)
    _write_install_readme(out, len(missions), mapsel_enabled=bool(eff_mapselmd))
    if feature_plan is not None:
        # Post-emission reconciliation: every game-dir file the package holds
        # must be exactly plan.shipped(); LEAVE rows must be absent. The
        # pre-write subset gate already refuses known mismatches with ZERO
        # output; this is the second, byte-level check on the real artifacts.
        from . import resolve_integration as RI
        RI.build_reconcile(feature_plan, out, plan_report=plan_report)
    return mix_path


# ---------------------------------------------------------------------------
# package identity (PKG-IDENT01)
# ---------------------------------------------------------------------------

def _write_package_identity(out: Path, design: dict) -> str:
    """Stamp <out>/ra2forge_package.json when the design declares an optional
    top-level "package" object: {"id": ..., "version": ...}.

    The id is the STABLE PACKAGE IDENTITY the installer (install.py
    PKG-IDENT01) judges upgrades and coexistence by - deliberately a different
    namespace from the campaign's battle id (campaign.id / BATTLEMD*.INI):
    the battle id decides how the ENGINE merges campaign entries and must
    stay stable across versions of the same package; the package_id decides
    whether the INSTALLER treats a directory as this package's own and must
    differ between different packages. Neither derives from the other, and
    neither derives from the build path. A design without the "package"
    object builds an UNDECLARED package (no ra2forge_package.json): installs
    from it work, but re-installing over such a record requires the explicit
    --adopt-legacy assertion. Returns the stamped id ("<undeclared>" when
    absent) for the build report.
    """
    pkg = design.get("package")
    if pkg is None:
        return "<undeclared>"
    if not isinstance(pkg, dict):
        raise BuildError('the optional "package" design field must be an '
                         f'object with "id" (and optionally "version"), got '
                         f"{type(pkg).__name__}")
    pid = str(pkg.get("id") or "").strip()
    if not pid:
        raise BuildError('the optional "package" design field declares no '
                         'usable "id" (non-empty string required)')
    ver = str(pkg.get("version") or "").strip() or "unknown"
    payload = {"tool": "ra2forge", "package_id": pid, "package_version": ver}
    (out / PACKAGE_MANIFEST_NAME).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return pid


# ---------------------------------------------------------------------------
# campaign chain
# ---------------------------------------------------------------------------

def mission_chain(missions: list[dict]) -> list[str]:
    """Map file each mission must point at through [Basic] NextScenario.

    Default: the next mission in the design order; the last mission ends the
    campaign (empty value). A mission may override the default with an explicit
    "next": "<mission name>" entry (or "next": "" to stop the chain there).
    """
    names = [f"{m['name'].upper()}.MAP" for m in missions]
    by_lower = {str(m["name"]).lower(): f"{m['name'].upper()}.MAP" for m in missions}
    chain: list[str] = []
    for i, m in enumerate(missions):
        if "next" in m:
            raw = str(m.get("next") or "").strip()
            chain.append(by_lower[raw.lower()] if raw else "")
        elif i + 1 < len(names):
            chain.append(names[i + 1])
        else:
            chain.append("")
    return chain


def _verify_next_scenario_chain(out: Path, compiled, chain) -> list[str]:
    """Read every written .MAP back and assert its [Basic] NextScenario.

    An empty NextScenario on a non-final mission is the FORGE-1 P0 breakage
    (all three demo missions were written without a link), so this is a hard
    failure - never a warning.
    """
    lines: list[str] = []
    map_names = {name.upper() for name, _ in compiled}
    for (map_name, _mmap), expected in zip(compiled, chain):
        path = out / map_name
        if not path.is_file():
            raise BuildError(f"{map_name}: map file missing at {path}")
        text = path.read_bytes().decode("gbk", errors="replace")
        basic = read_basic_section(text)
        if "NextScenario" not in basic:
            raise BuildError(f"{map_name}: [Basic] has no NextScenario key")
        got = basic["NextScenario"].strip()
        if got.upper() != expected.upper():
            raise BuildError(
                f"{map_name}: [Basic] NextScenario={got!r} but the design order "
                f"requires {expected!r} (chain self-check failed)")
        # R5: the campaign-ending mission must carry EndOfGame=yes, every other
        # mission EndOfGame=no (official convention: the last mission of a
        # campaign sets it, e.g. extracted/yr_maps/map_133A0CB2.map:267)
        want_eog = "no" if expected else "yes"
        eog = basic.get("EndOfGame", "").strip().lower()
        if eog != want_eog:
            raise BuildError(
                f"{map_name}: [Basic] EndOfGame={eog!r} but "
                f"EndOfGame={want_eog} is required (R5 self-check failed)")
        if expected:
            if got.upper() not in map_names:
                raise BuildError(
                    f"{map_name}: NextScenario={got!r} is not a map of this "
                    f"campaign {sorted(map_names)}")
            lines.append(f"  [PASS] {map_name}: [Basic] NextScenario={got} -> "
                         f"chained, EndOfGame={eog}")
        else:
            lines.append(f"  [PASS] {map_name}: [Basic] NextScenario= (empty) -> "
                         f"campaign ends here, EndOfGame={eog}")
    return lines


def _verify_battle_file(out: Path, camp: dict, missions: list[dict],
                        battle_id: str,
                        desc_override: str | None = None) -> list[str]:
    """Read the written BATTLEMD98.INI back and assert the appended entry (R1/R3).

    Checks on the bytes that actually landed on disk: the [Battles] index maps to
    our own battle id, that id's section starts the campaign at the first map and
    carries the campaign-level description from the design file (or the CSF label
    when --csf-out is enabled), and no official entry name is present anywhere in
    the file.
    """
    path = out / BATTLE_FILE_NAME
    if not path.is_file():
        raise BuildError(f"{BATTLE_FILE_NAME}: file missing at {path}")
    text = path.read_bytes().decode("gbk", errors="replace")
    sections = _parse_ini(text)
    battles = sections.get("Battles", {})
    entry = sections.get(battle_id, {})
    if battles.get(str(BATTLE_INDEX)) != battle_id:
        raise BuildError(
            f"{BATTLE_FILE_NAME}: [Battles] {BATTLE_INDEX}="
            f"{battles.get(str(BATTLE_INDEX))!r}, expected {battle_id!r}")
    if not entry:
        raise BuildError(f"{BATTLE_FILE_NAME}: section [{battle_id}] is missing")
    first_map = f"{missions[0]['name'].upper()}.MAP"
    if entry.get("Scenario", "").upper() != first_map:
        raise BuildError(
            f"{BATTLE_FILE_NAME}: [{battle_id}] Scenario={entry.get('Scenario')!r}, "
            f"expected {first_map!r}")
    want_desc = (desc_override if desc_override is not None
                 else (design_mod.description_for(camp) or str(camp["name"]).strip()))
    if entry.get("Description", "") != want_desc:
        raise BuildError(
            f"{BATTLE_FILE_NAME}: [{battle_id}] Description="
            f"{entry.get('Description')!r}, expected the design's campaign "
            f"description {want_desc!r}")
    overrides = sorted(s for s in sections
                       if design_mod.OFFICIAL_BATTLE_ID_RE.match(s))
    if overrides:
        raise BuildError(
            f"{BATTLE_FILE_NAME}: official entry name(s) {overrides} must never "
            f"appear - the file may only append our own campaign")
    return [
        f"  [PASS] {BATTLE_FILE_NAME}: [Battles] {BATTLE_INDEX}={battle_id} -> "
        f"{first_map} (append; official BATTLEMD.INI untouched)",
        f"  [PASS] {BATTLE_FILE_NAME}: [{battle_id}] read back from disk "
        f"(Scenario={entry['Scenario']}, Description={entry['Description'][:40]!r}"
        f"{'...' if len(entry['Description']) > 40 else ''})",
        f"  [PASS] {BATTLE_FILE_NAME}: no official entry name "
        f"(no [ALL1]/[SOV1]/[ALL02]..[SOV07])",
    ]


def _parse_ini(text: str) -> dict[str, dict[str, str]]:
    """Minimal INI reader (sections -> key/value), used by the self-check."""
    sections: dict[str, dict[str, str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            sections.setdefault(current, {})
            continue
        if current is not None and "=" in line:
            key, _, value = line.partition("=")
            sections[current][key.strip()] = value.strip()
    return sections


def _verify_mix_contents(mix_path: Path, expected_names: list[str]) -> str:
    """Re-open the written MIX and assert it holds exactly the map files."""
    if any(n.upper().endswith(".INI") for n in expected_names):
        raise BuildError(
            f"refusing to pack INI files into {mix_path.name}: {expected_names}")
    want = {crc_hash(n) for n in expected_names}
    with MixFile(mix_path) as mix:
        got = {e.id for e in mix.all_entries()}
    if got != want:
        raise BuildError(
            f"{mix_path.name} entries {sorted(f'{i:08X}' for i in got)} != expected "
            f"{sorted(f'{i:08X}' for i in want)}")
    return (f"  [PASS] {mix_path.name}: {len(got)} entries, 0 INI "
            f"({', '.join(expected_names)})")


# ---------------------------------------------------------------------------
# battle registry
# ---------------------------------------------------------------------------

def battle_id_for(campaign) -> str:
    """Battle id for the appended campaign entry (R1).

    Accepts the campaign dict and delegates to design.campaign_battle_id: the
    optional `campaign.id` field wins, otherwise the stable default RA2F1.
    (A bare name string is tolerated and yields the default: since FORGE-2 the id
    no longer derives from the campaign name - a name hash made every campaign
    register under a different id, which the user ruling replaced with the fixed
    RA2F1 entry.)
    """
    if isinstance(campaign, str):
        return design_mod.DEFAULT_BATTLE_ID
    return design_mod.campaign_battle_id(campaign)


def csf_label_for(design: dict, battle_id: str | None = None) -> str:
    """Stable CSF label name for campaign.description when CSF mode is enabled.

    Uses design.package.id when declared, otherwise falls back deterministically
    to battle_id + campaign.name. Format: RA2F:<8-hex-sha256-prefix>.
    """
    pkg = design.get("package")
    pid = str(pkg.get("id") or "").strip() if isinstance(pkg, dict) else ""
    if pid:
        seed = f"pkg:{pid}"
    else:
        camp = design.get("campaign") or {}
        bid = battle_id or battle_id_for(camp)
        seed = f"battle:{bid}:{str(camp.get('name') or '').strip()}"
    short_hash = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8].upper()
    return f"RA2F:{short_hash}"


def _csf_out_ownership_guard(csf_out: Path, *, install_game_dir: Path | None,
                             allow_csf_out_in_game: bool,
                             check_lines: list[str]) -> dict:
    """W41 (closes W38 CRITICAL): --csf-out landing INSIDE a game directory is
    an install-level write entry - it must never be written silently.

    W38 WRITE_ENTRY_AUDIT flagged builder.py:434-437 / cli.py:140-146 as a
    direct write to an arbitrary user path with ZERO identity/target checks.
    A game directory is detected the same way install.preinstall_plan() does:
    a directory containing gamemd.exe. Both an explicit --install game dir and
    any gamemd.exe-bearing ancestor of csf_out are considered.

    Default (allow_csf_out_in_game=False): REFUSE with BuildError before the
    first byte is written. The correct channel is the `install` command, which
    routes ra2md.csf through preflight / backup / manifest / uninstall.

    With the explicit, dangerous --allow-csf-out-in-game flag the write is
    permitted ONLY after target-identity checks (plain file name, no reserved
    slot, no symlink/alias) and is loudly logged in the build report.
    """
    resolved = csf_out.resolve()
    game_dirs: list[Path] = []
    if install_game_dir is not None:
        gd = Path(install_game_dir).resolve()
        if (gd / "gamemd.exe").is_file():
            game_dirs.append(gd)
    # any ancestor that looks like a game directory (W29 disk-first override)
    for parent in resolved.parents:
        if (parent / "gamemd.exe").is_file() and parent not in game_dirs:
            game_dirs.append(parent)
    if not game_dirs:
        return {"in_game_dir": False, "game_dirs": [], "confirmed": False}

    if not allow_csf_out_in_game:
        gd = game_dirs[0]
        raise BuildError(
            f"--csf-out {csf_out} resolves inside the game directory {gd} "
            "(gamemd.exe present). Writing a loose ra2md.csf there is an "
            "install-level write entry and is REFUSED by default: a partial "
            "CSF would make the official UI text render as MISSING:'...' "
            "(W40 A/E; NOT a startup-failure rule - W40 A booted a legal "
            "minimal CSF), and a silent overwrite would bypass install "
            "preflight/backup/manifest. Use the guarded "
            "channel instead: 'python -m ra2forge build ... --install "
            f"\"{gd}\"' (or 'python -m ra2forge install --package <pkg> "
            f"--game \"{gd}\"'), which routes ra2md.csf through the full "
            "preflight/backup/uninstall chain. If you deliberately want this "
            "build to write into the game directory anyway, re-run with the "
            "explicit --allow-csf-out-in-game flag (dangerous; still refuses "
            "aliases and reserved slots). NO file has been written.")

    # explicit confirmation path: install-grade target identity checks
    name = resolved.name
    if (not name or name in (".", "..") or Path(name).name != name
            or "/" in name or "\\" in name):
        raise BuildError(f"--csf-out target name {name!r} is not a plain "
                         "file name - refusing the in-game-dir write")
    reserved = (MANIFEST_NAME, SEAL_NAME)
    if name in reserved or STAGE_INFIX in name or name.endswith(BACKUP_SUFFIX):
        raise BuildError(
            f"--csf-out target {name!r} collides with an install-reserved slot "
            "(manifest / seal / backup / staging) - refusing the in-game-dir "
            "write")
    if csf_out.is_symlink():
        raise BuildError(
            f"--csf-out {csf_out} is a symbolic link - refusing to write a "
            "loose ra2md.csf through an alias")
    check_lines.append(
        f"  [WARN] --csf-out {csf_out} is INSIDE a game directory "
        f"{game_dirs[0]} and --allow-csf-out-in-game was given explicitly: "
        "treated as an install-level write entry (target identity checked, "
        "no reserved slot, no alias). This BYPASSES install preflight/backup/"
        "manifest, so the written ra2md.csf is UNTRACKED: a later "
        "'uninstall' will NOT remove it (W21 orphan risk). The safe channel "
        "is the install command, which records it in ra2forge_install.json.")
    return {"in_game_dir": True,
            "game_dirs": [str(g) for g in game_dirs],
            "confirmed": True}


def _emit_csf_artifacts(
    *,
    out: Path,
    csf_out: Path,
    csf_base: Path | None,
    csf_label: str,
    csf_text: str,
    battle_id: str,
    pkg_id: str,
    check_lines: list[str],
    guard_report: dict | None = None,
    install_game_dir: Path | None = None,
    allow_csf_out_in_game: bool = False,
) -> dict:
    """W41: write a COMPLETE official-base ra2md.csf clone + our label.

    Closes the W30 UNCOVERED §2 gap's build side and the W29 "minimal CSF is
    dangerous" hazard. The ONLY allowed production path is "clone a complete
    official CSF base, then append/set our label":

      * --csf-base B          : B must be a complete official clone; it is
                                cloned to csf_out (overwriting it).
      * no --csf-base, csf_out already exists : it must ALREADY be a complete
                                official clone (update-in-place); a corrupt or
                                minimal/partial file is REFUSED untouched.
      * no --csf-base, csf_out missing : clone the BUNDLED byte-exact official
                                ra2md.csf (extracted read-only from
                                ra2bench\\langmd.mix in W41/EVIDENCE/step1).

    A from-scratch / create_if_missing minimal CSF is NO LONGER possible -
    every write goes through csf.assert_complete_csf() (magic ' FSC', version 3,
    header/label/value count consistency, and the full 5,211-label official
    baseline set). The path-ownership guard runs first (W38 CRITICAL).
    """
    # (0) W38 CRITICAL: install-level ownership guard. Normally pre-computed
    # at the very top of build() (before ANY write); the defensive fallback
    # keeps this function self-contained for direct callers.
    guard = guard_report if guard_report is not None else \
        _csf_out_ownership_guard(
            csf_out, install_game_dir=install_game_dir,
            allow_csf_out_in_game=allow_csf_out_in_game,
            check_lines=check_lines)

    try:
        # (1) obtain / write the COMPLETE base clone at csf_out.
        if csf_base is not None:
            base_csf = csf_mod.read_csf(csf_base, strict=True)
            csf_mod.assert_complete_csf(base_csf)
            if csf_out.resolve() != csf_base.resolve():
                csf_mod.write_csf(csf_out, base_csf, require_complete=True)
        elif csf_out.is_file():
            # "update in place": the existing file must already be complete.
            existing = csf_mod.read_csf(csf_out, strict=True)
            csf_mod.assert_complete_csf(existing)
        else:
            # no base + no target: clone the bundled byte-exact official CSF.
            base_csf = csf_mod.load_official_csf()
            csf_mod.write_csf(csf_out, base_csf, require_complete=True)

        # (2) append/set our label; require_complete guards the final write.
        res = csf_mod.append_or_set_label(
            csf_out, csf_label, csf_text,
            create_if_missing=False, verify=True, require_complete=True,
        )
        # (3) final re-read + mandatory completeness check of the artifact.
        final_csf = csf_mod.read_csf(csf_out, strict=True)
        complete = csf_mod.assert_complete_csf(final_csf)
    except (OSError, csf_mod.CsfError) as exc:
        raise BuildError(f"CSF emission failed for {csf_out}: {exc}") from exc

    # (4) package copy - also routed through the completeness-guarded writer.
    pkg_csf = out / "ra2md.csf"
    if csf_out.resolve() != pkg_csf.resolve():
        csf_mod.write_csf(pkg_csf, final_csf, require_complete=True)

    patch_payload = {
        "target_csf": "ra2md.csf",
        "label": csf_label,
        "text": csf_text,
        "battle_id": battle_id,
        "package_id": pkg_id,
        "csf_out": str(csf_out),
        "action": res["action"],
        "num_labels": res["num_labels"],
        "complete_baseline_labels": complete["baseline_labels"],
        "csf_out_in_game_dir": guard["in_game_dir"],
    }
    (out / "csf_patch.json").write_text(
        json.dumps(patch_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    check_lines.append(
        f"  [PASS] ra2md.csf: label {csf_label} -> {res['action']} "
        f"(num_labels={res['num_labels']}, complete official clone of "
        f"{complete['baseline_labels']} baseline labels, readback verified)"
    )
    return {
        "enabled": True,
        "target_csf": "ra2md.csf",
        "label": csf_label,
        "text": csf_text,
        "csf_out": str(csf_out),
        "pkg_csf": pkg_csf.name,
        "patch_file": "csf_patch.json",
        "action": res["action"],
        "num_labels": res["num_labels"],
    }


def _emit_mapselmd(out: Path, design: dict, missions: list[dict],
                   chain: list[str], mapselmd_base, check_lines: list[str]) -> dict:
    """W34: clone the COMPLETE official MAPSELMD.INI and append our stages.

    A minimal file (only our stages) is a hard error inside
    mapselmd.validate_official_base(): the engine treats MAPSELMD.INI as a
    whole-file override, so dropping official stages would break every
    official campaign. The bytes are written verbatim (CRLF preserved) and
    read back from disk before the self-check lines are appended.
    """
    base_bytes: bytes | None = None
    if mapselmd_base is not None:
        try:
            base_bytes = Path(mapselmd_base).read_bytes()
        except OSError as exc:
            raise BuildError(f"--mapselmd-base {mapselmd_base}: {exc}") from exc
    try:
        data, report = mapselmd_mod.build_mapselmd(
            design, missions, chain, base_bytes=base_bytes)
        mapselmd_mod.write_mapselmd(out / mapselmd_mod.MAPSEL_FILE_NAME, data)
    except mapselmd_mod.MapselmdError as exc:
        raise BuildError(f"MAPSELMD.INI generation failed: {exc}") from exc

    path = out / mapselmd_mod.MAPSEL_FILE_NAME
    if path.read_bytes() != data:
        raise BuildError("MAPSELMD.INI: readback mismatch after write")
    check_lines.append(
        f"  [PASS] {mapselmd_mod.MAPSEL_FILE_NAME}: full official clone "
        f"(base {report['base_size']} B sha256={report['base_sha256'][:12]}...) "
        f"+ {report['appended_stages']} appended stage(s) -> "
        f"[{report['faction']}] {', '.join(report['appended_keys'])}")
    check_lines.append(
        f"  [PASS] {mapselmd_mod.MAPSEL_FILE_NAME}: all 14 official stages and "
        "both faction sequences survive verbatim (no minimal file)")
    check_lines.append(
        f"  [PASS] {mapselmd_mod.MAPSEL_FILE_NAME}: last stage has NO child "
        "link (EndOfGame=yes side terminates the campaign); CRLF="
        f"{report['crlf']}")
    return report


def _battle_ini(camp: dict, missions: list[dict], battle_id: str,
                desc_override: str | None = None) -> str:
    # R3: the Description shown in the campaign list is the campaign-level blurb
    # from the design file (campaign.description) - never a hard coded string and
    # never a "DESC:xxx" CSF label unless CSF mode is explicitly enabled via
    # --csf-out. Falls back to campaign.name when the design omits the field.
    desc = (desc_override if desc_override is not None
            else (design_mod.description_for(camp) or str(camp["name"]).strip()))
    lines = [
        "; Generated by RA2 Campaign Forge - APPENDED campaign entry.",
        "; The game scans the GAME DIRECTORY for BATTLEMD*.INI and merges the",
        "; entries by battle id, so this file only ADDS a campaign; the official",
        "; BATTLEMD.INI is left untouched. Delete this file to unregister.",
        "[Battles]",
        f"{BATTLE_INDEX}={battle_id}",
        "",
        f"[{battle_id}]",
        "CD=2",
        f"Scenario={missions[0]['name'].upper()}.MAP",
        "FinalMovie=",
        f"Description={desc}",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# mission compilation
# ---------------------------------------------------------------------------

def _build_mission(m: dict, index: int, design: dict) -> tuple[MissionMap, list[str]]:
    warnings: list[str] = []
    size = m.get("size", [90, 90])
    theater = str(m.get("theater", "TEMPERATE")).upper()
    mmap = MissionMap(m["name"], width=size[0], height=size[1], theater=theater)

    side = str(design["campaign"].get("side", "soviet")).lower()
    player_house = str((m.get("player") or {}).get("house") or SIDES[side])
    mmap.player_house = player_house
    mmap.basic["briefing"] = _sanitize_briefing(m.get("briefing", ""))
    mmap.name = str(m.get("title") or m["name"])

    # per-house configuration - the game picks the player by PlayerControl=yes
    # (mirror of official campaign maps like SOV01UMD.MAP)
    enemies = list(dict.fromkeys(
        [str(o["enemy"]) for o in m.get("objectives", [])
         if o.get("type") in ("destroy_all_forces", "destroy_all_buildings")]
        + [str(o["house"]) for o in m.get("objectives", [])
           if o.get("type") == "hunt_wave"]
        + [str(o.get("team", {}).get("house")) for o in m.get("objectives", [])
           if o.get("type") == "reinforce" and o.get("team", {}).get("house")
           and o["team"]["house"] != player_house]))
    player_color = {"soviet": "DarkRed", "allied": "DarkBlue", "yuri": "Gold"}.get(
        side, "DarkRed")
    enemy_colors = ["DarkBlue", "DarkRed", "Gold", "Green", "Orange", "Purple"]
    house_configs = [{
        "name": player_house,
        "player": True,
        "credits": int((m.get("player") or {}).get("credits", 0)),
        "color": player_color,
        "edge": "South",
        "allies": player_house,
        "iq": 0,
    }]
    for j, enemy in enumerate(enemies):
        color = enemy_colors[j % len(enemy_colors)]
        if color == player_color:
            color = enemy_colors[(j + 1) % len(enemy_colors)]
        house_configs.append({
            "name": enemy,
            "player": False,
            "credits": int((m.get("player") or {}).get("enemy_credits", 0)),
            "color": color,
            "edge": "North",
            "allies": ", ".join(enemies),
            "iq": 2,
        })
    mmap.house_configs = house_configs

    tid_gen = _hex_id_gen(0x0B000000 + index * 0x10000)
    tag_gen = _hex_id_gen(0x0C000000 + index * 0x10000)

    # waypoints
    for wp_id, pos in (m.get("waypoints") or {}).items():
        mmap.add_waypoint(int(wp_id), int(pos[0]), int(pos[1]))

    # water
    for wrect in m.get("water", []):
        mmap.add_water_rect(int(wrect["row0"]), int(wrect["col0"]),
                            int(wrect["row1"]), int(wrect["col1"]))

    # scenery: forests, civilian structures, neutral cars, battle smudges
    scenery = m.get("scenery") or {}
    for trect in scenery.get("tree_rects", []):
        mmap.scatter_trees(int(trect["row0"]), int(trect["col0"]),
                           int(trect["row1"]), int(trect["col1"]),
                           density=float(trect.get("density", 0.08)),
                           seed=int(trect.get("seed", 0)))
    for civ in scenery.get("civilians", []):
        mmap.add_structure(str(civ.get("owner", "Neutral")), str(civ["type"]).upper(),
                           int(civ["row"]), int(civ["col"]),
                           health=int(civ.get("health", 256)),
                           sellable=0, rebuildable=0, repairable=0, nominal=0)
    for car in scenery.get("cars", []):
        mmap.add_unit(str(car.get("owner", "Neutral")), str(car["type"]).upper(),
                      int(car["row"]), int(car["col"]), mission="Sleep")
    for sm in scenery.get("smudges", []):
        mmap.add_smudge(int(sm["row"]), int(sm["col"]), str(sm["type"]).upper())

    # objects
    design_tag_to_tagid: dict[str, str] = {}
    for s in m.get("structures", []):
        if s.get("tag"):
            design_tag_to_tagid[str(s["tag"])] = None
    for design_tag in design_tag_to_tagid:
        design_tag_to_tagid[design_tag] = next(tag_gen)
    for s in m.get("structures", []):
        mmap.add_structure(str(s["owner"]), str(s["type"]).upper(),
                           int(s["row"]), int(s["col"]),
                           health=int(s.get("health", 256)),
                           tag=design_tag_to_tagid.get(str(s.get("tag", "")), "None"))
    for u in m.get("units", []):
        mmap.add_unit(str(u["owner"]), str(u["type"]).upper(),
                      int(u["row"]), int(u["col"]),
                      health=int(u.get("health", 256)),
                      mission=str(u.get("mission", "Guard")))
    for inf in m.get("infantry", []):
        mmap.add_infantry(str(inf["owner"]), str(inf["type"]).upper(),
                          int(inf["row"]), int(inf["col"]),
                          health=int(inf.get("health", 256)),
                          mission=str(inf.get("mission", "Guard")))

    # --- triggers ---------------------------------------------------------
    player_idx = HOUSE_INDEX[player_house]
    mission_triggers: list[dict] = []

    # lose trigger: player loses everything
    mission_triggers.append(tg.make_trigger(
        next(tid_gen), next(tag_gen), player_house, "Defeat",
        [tg.ev_all_destroyed(player_idx)],
        [tg.act_loser(player_idx)],
        tag_name="Defeat"))

    # objectives: win-type objectives chain; event-only objectives are freestanding
    win_objs = [o for o in m.get("objectives", [])
                if o["type"] in ("destroy_all_forces", "destroy_all_buildings",
                                 "destroy_building", "survive")]
    event_objs = [o for o in m.get("objectives", [])
                  if o["type"] in design_mod.EVENT_ONLY_OBJECTIVES]

    win_triggers: list[dict] = []
    for o in win_objs:
        otype = o["type"]
        if otype == "destroy_all_forces":
            enemy = str(o["enemy"])
            win_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house,
                f"Objective: destroy {enemy}",
                [tg.ev_all_destroyed(HOUSE_INDEX[enemy])], [],
                tag_name=f"Destroy {enemy}"))
        elif otype == "destroy_all_buildings":
            enemy = str(o["enemy"])
            win_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house,
                f"Objective: raze {enemy}",
                [tg.ev_all_buildings_destroyed(HOUSE_INDEX[enemy])], [],
                tag_name=f"Raze {enemy}"))
        elif otype == "destroy_building":
            tag_id = design_tag_to_tagid[str(o["structure_tag"])]
            win_triggers.append(tg.make_trigger(
                next(tid_gen), tag_id, player_house,
                "Objective: destroy target",
                [tg.ev_destroyed_by_any()], [],
                tag_name=f"Destroy target {o['structure_tag']}"))
        elif otype == "survive":
            win_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house,
                f"Objective: survive {o['seconds']}s",
                [tg.ev_elapsed_time(int(o["seconds"]))], [],
                tag_name=f"Survive {o['seconds']}"))

    # chain win objectives: each enables the next, last declares victory
    if win_triggers:
        for j, trig in enumerate(win_triggers):
            if j + 1 < len(win_triggers):
                trig["disabled"] = 1 if j > 0 else 0
                trig["actions"] = [tg.act_enable_trigger(win_triggers[j + 1]["id"])]
            else:
                trig["actions"] = [tg.act_winner(player_idx)]
        mission_triggers.extend(win_triggers)
    else:
        warnings.append("no win objective - mission can only be lost; "
                        "add destroy_all_forces/survive/destroy_building")

    if len(m.get("objectives", [])) != len(win_objs) + len(event_objs):
        warnings.append("some objectives were not compiled - check objective types")

    # event-only objectives (reinforce/text/speech/timer/reveal/hunt)
    for o in event_objs:
        at = int(o.get("at_second", 0))
        events = [tg.ev_elapsed_time(at)] if at > 0 else [(0, (0, 0))]
        otype = o["type"]
        if otype == "text":
            mission_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house, "Message",
                events, [tg.act_text(str(o["text"]))], tag_name="Message"))
        elif otype == "speech":
            mission_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house, "EVA",
                events, [tg.act_speech(str(o["eva"]))], tag_name="EVA"))
        elif otype == "timer":
            mission_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house, "Timer",
                events, [tg.act_timer_set(int(o["seconds"])), tg.act_timer_start()],
                tag_name="Timer"))
        elif otype == "reveal_map":
            mission_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house, "Reveal",
                events, [tg.act_reveal_all()], tag_name="Reveal"))
        elif otype == "reveal_waypoint":
            wp_id = int(o["waypoint"])
            mission_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house, "Recon",
                events, [tg.act_reveal_waypoint(wp_id)], tag_name="Recon"))
        elif otype == "hunt_wave":
            enemy = str(o["house"])
            mission_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house,
                f"Enemy assault ({enemy})",
                events, [tg.act_all_to_hunt(HOUSE_INDEX[enemy])],
                tag_name=f"Hunt {enemy}"))
        elif otype == "reinforce":
            team = o["team"]
            team_id = str(team["id"]).upper()
            house = str(team.get("house", player_house))
            entries = [(int(e["count"]), str(e["type"]).upper())
                       for e in team.get("units", [])]
            wp_letter = str(o.get("at_waypoint", "")).upper()
            if wp_letter and len(wp_letter) == 1 and wp_letter.isalpha():
                wp_id = ord(wp_letter) - ord("A")
                if wp_id not in mmap.waypoints:
                    mmap.add_waypoint(wp_id, int(team.get("row", size[1] // 2)),
                                      int(team.get("col", size[0] // 2)))
                mmap.add_reinforcement_team(team_id, house, entries,
                                            waypoint_letter=wp_letter)
                action = tg.act_reinforce_at_waypoint(team_id, wp_letter)
            else:
                mmap.add_reinforcement_team(team_id, house, entries)
                action = tg.act_reinforce(team_id)
            mission_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house, "Reinforcement",
                events, [action], tag_name="Reinforcement"))

    for t in mission_triggers:
        mmap.add_trigger(t)
    return mmap, warnings


def _hex_id_gen(start: int):
    val = start
    while True:
        yield f"{val:08X}"
        val += 0x1C


def _sanitize_briefing(text: str) -> str:
    # briefings are single-line INI values; use '@' as paragraph separator
    return re.sub(r"[\r\n]+", "@@", str(text)).strip()


def _fs_safe(name: str) -> str:
    # NTFS handles CJK fine; only strip characters Windows forbids in filenames
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()[:80] or "campaign"


def _write_map_file(path: Path, text: str):
    # the game reads INI-style files as ANSI in the system code page;
    # Chinese installs expect GBK (cp936), a strict superset of ASCII
    data = text.encode("gbk", errors="replace")
    with open(path, "wb") as f:
        f.write(data)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_line(path: Path) -> str:
    return (f"  {path.name}  {path.stat().st_size} bytes  "
            f"sha256={_sha256(path)[:16]}")


def _write_build_report(out: Path, camp: dict, compiled, chain, battle_id: str,
                        check_lines: list[str],
                        package_id: str = "<undeclared>",
                        csf_info: dict | None = None,
                        mapsel_info: dict | None = None) -> Path:
    lines = [
        "RA2 Campaign Forge - build report",
        f"campaign={camp['name']}",
        f"side={str(camp.get('side', 'soviet')).lower()}",
        f"battle_file={BATTLE_FILE_NAME} (loose, appended entry)",
        f"battle_id={battle_id}",
        f"battle_id_source={'campaign.id' if camp.get('id') else 'default RA2F1'}",
        f"battle_index={BATTLE_INDEX}",
        f"package_id={package_id}",
        f"package_id_source={'design.package.id' if package_id != '<undeclared>' else 'undeclared (no ra2forge_package.json written)'}",
        f"description={design_mod.description_for(camp) or camp['name']}",
        f"first_scenario={compiled[0][0]}",
        f"mix={MIX_FILE_NAME} (maps only)",
    ]
    if csf_info is not None:
        if csf_info.get("skipped"):
            lines.extend([
                f"csf_mode=enabled (skipped: {csf_info['skipped']})",
                f"csf_out={csf_info['csf_out']}",
            ])
        else:
            lines.extend([
                "csf_mode=enabled",
                f"csf_target={csf_info['target_csf']}",
                f"csf_label={csf_info['label']}",
                f"csf_text={csf_info['text']}",
                f"csf_out={csf_info['csf_out']}",
                f"csf_instruction=write label {csf_info['label']!r} into {csf_info['target_csf']} "
                f"(package {csf_info['pkg_csf']} + {csf_info['patch_file']} generated)",
            ])
    if mapsel_info is not None:
        lines.extend([
            "mapselmd_mode=enabled",
            f"mapselmd_target={mapselmd_mod.MAPSEL_FILE_NAME} (loose, full clone + append)",
            f"mapselmd_faction={mapsel_info['faction']}",
            f"mapselmd_base_sha256={mapsel_info['base_sha256']}",
            f"mapselmd_base_size={mapsel_info['base_size']}",
            f"mapselmd_out_sha256={mapsel_info['out_sha256']}",
            f"mapselmd_official_stages_kept={mapsel_info['official_stages_kept']}",
            f"mapselmd_appended_stages={mapsel_info['appended_stages']}",
            f"mapselmd_appended_keys={','.join(mapsel_info['appended_keys'])}",
            f"mapselmd_last_stage_terminates={mapsel_info['last_stage_terminates']}",
            "mapselmd_instruction=install the loose file into the game directory; "
            "uninstall restores the pre-install original from its backup",
        ])
    lines.extend([
        "",
        "NextScenario chain:",
    ])
    for (map_name, mmap), nxt in zip(compiled, chain):
        lines.append(f"  {map_name}  title={mmap.name}  "
                     f"next={nxt or '<campaign end>'}  "
                     f"end_of_game={'yes' if mmap.end_of_game else 'no'}")
    lines += ["", "self-checks:", *check_lines, "", "artifacts:"]
    for map_name, _ in compiled:
        lines.append(_artifact_line(out / map_name))
    # W60: an inplace package ships BATTLEMD.INI, not BATTLEMD98.INI.
    # Report whichever battle-list member actually exists; the default path
    # (BATTLEMD98.INI present) is byte-for-byte unchanged.
    battle_artifact = out / BATTLE_FILE_NAME
    if not battle_artifact.is_file():
        battle_artifact = out / "BATTLEMD.INI"
    lines.append(_artifact_line(battle_artifact))
    lines.append(_artifact_line(out / MIX_FILE_NAME))
    lines.append(_artifact_line(out / "story.md"))
    if (out / PACKAGE_MANIFEST_NAME).is_file():
        lines.append(_artifact_line(out / PACKAGE_MANIFEST_NAME))
    if csf_info is not None and not csf_info.get("skipped"):
        if (out / "ra2md.csf").is_file():
            lines.append(_artifact_line(out / "ra2md.csf"))
        if (out / "csf_patch.json").is_file():
            lines.append(_artifact_line(out / "csf_patch.json"))
    if mapsel_info is not None:
        lines.append(_artifact_line(out / mapselmd_mod.MAPSEL_FILE_NAME))
    lines.append("")
    report = out / "BUILD_REPORT.txt"
    report.write_text("\n".join(lines), encoding="utf-8")
    return report


def _write_install_readme(out: Path, mission_count: int,
                          mapsel_enabled: bool = False):
    text = (
        "RA2 Campaign Forge - install instructions\r\n"
        "=========================================\r\n\r\n"
        f"This package contains {mission_count} chained mission(s).\r\n\r\n"
        "Automatic install (recommended - backs up and can restore):\r\n"
        "  python -m ra2forge build --design <design.json> --out out "
        "--install \"<game dir>\"\r\n"
        "  python -m ra2forge uninstall --game \"<game dir>\"\r\n\r\n"
        "Manual install:\r\n"
        "  1. Copy BATTLEMD98.INI, expandmd98.mix and every *.MAP into your\r\n"
        "     Red Alert 2 Yuri's Revenge directory (the folder with gamemd.exe).\r\n"
        "  2. Start the game -> New Campaign -> the campaign list gains one extra\r\n"
        "     entry (its Description is the campaign.description of the design\r\n"
        "     file); the official campaigns stay exactly as they were.\r\n"
        "  3. The last mission of the chain carries EndOfGame=yes; delete that line\r\n"
        "     if a real playthrough shows the campaign ending early.\r\n\r\n"
        "Why BATTLEMD98.INI must stay a loose file:\r\n"
        "  the engine enumerates the battle lists with "
        "FindFirstFileA(\"BATTLEMD*.INI\")\r\n"
        "  in the GAME DIRECTORY and merges them by battle id. A file inside a MIX\r\n"
        "  is never seen by that wildcard, so the registration cannot live in the\r\n"
        "  archive (and nothing else may be packed there either - maps only).\r\n\r\n"
        "Files:\r\n"
        "  *.MAP             mission maps (YR .map format, playable standalone too)\r\n"
        "  BATTLEMD98.INI    appended campaign entry (delete it to unregister)\r\n"
        "  expandmd98.mix    map archive (maps only - no INI inside)\r\n"
        "  story.md          the storyline briefing for every mission\r\n"
        "  BUILD_REPORT.txt  build log: chain + artifact hashes + self-checks\r\n")
    if mapsel_enabled:
        text += (
            "\r\n"
            "MAPSELMD.INI (W34 campaign-progression registration):\r\n"
            "  This package also ships a COMPLETE clone of the official\r\n"
            "  MAPSELMD.INI with the appended campaign stages. It is a WHOLE-FILE\r\n"
            "  override, so never replace it with a minimal file containing only\r\n"
            "  this campaign - that would break every official campaign.\r\n"
            "  The installer backs up any existing MAPSELMD.INI and restores it\r\n"
            "  on uninstall. A pre-existing MAPSELMD.INI that is not recorded as\r\n"
            "  ours is a definite preflight conflict and the install is refused.\r\n"
            "  1. Copy MAPSELMD.INI into the game directory (same folder as\r\n"
            "     gamemd.exe) together with the other loose files.\r\n"
            "  2. Manual copy: back up the existing MAPSELMD.INI first; never\r\n"
            "     silently overwrite a foreign one.\r\n")
    (out / "INSTALL.txt").write_text(text, encoding="ascii")
