#!/usr/bin/env python3
"""W41 regression: the W34/v11 suite (51 cases: W26's 39 P/V/C/T/S/F/U/R
series + W30's CSF1..CSF6 + W34's MS1..MS6) copied INTACT and re-pointed at
this card's ra2forge_patched_v13, plus W41's own CSF_INST1..CSF_INST6 cases:

  CSF_INST1 complete clone passes / partial+minimal CSF refused
  CSF_INST2 install -> verify -> uninstall -> byte-exact restore (CREATE/DELETE)
  CSF_INST3 foreign loose ra2md.csf => definite preflight refusal, zero writes
  CSF_INST4 --csf-out inside a game dir => ownership guard triggers, no writes
  CSF_INST5 no-CSF-switch build == v11 byte-for-byte (SHA-256 table)
  CSF_INST6 upgrade / backup / restore path also covers ra2md.csf

Each case is isolated in sandbox/<case>/ with 命令 + 原始输出 + 退出码 logged
to out/<case>.log.

W77: this file is regress_dlc_v15.py copied to the W77_exit33_message_v16
card and minimally re-pointed (card name + ra2forge_patched_v16 package root;
sandbox/ and out/ therefore land in the W77 card only).  All 96 inherited
case bodies are byte-for-byte untouched; exactly ONE new case (W77_1) is
appended, asserting the v16 EXIT 33 refusal message (product language; the
machine-readable parts INPLACE_OFFICIAL_MISMATCH / exit 33 / sha pair /
"Zero bytes written" preserved).  Message-only v15->v16; no verdict/logic
change anywhere.

Usage:
    python -B -X utf8 regress_dlc_v13.py                   # run everything
    python -B -X utf8 regress_dlc_v13.py R2 CSF_INST2      # run a subset

Exit code 0 = all cases passed; 1 = at least one case failed.
NO real game directory is ever touched: the only game dirs used are the
sandbox copies this script creates. The ONLY contact with
D:\\Project\\ra2-campaign-forge\\ra2youli is a READ of its
ra2forge_install.json and langmd.mix (both byte-copied into the sandbox); the
official CSF baseline for the v12 bundle was extracted READ-ONLY from
D:\\Project\\ra2-campaign-forge\\ra2bench\\langmd.mix. All W21-W40 cards are
READ-ONLY references; no file under them is written. No game is launched.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

W43_ROOT = Path(__file__).resolve().parent
REPO_ROOT = W43_ROOT.parents[2]          # ...\ra2-campaign-forge
# W77 re-point: the suite now lives in the W77 card (same tree depth, so
# REPO_ROOT still resolves to the repo root).
W43_ROOT_NAME = "W77_exit33_message_v16"
assert W43_ROOT.name == W43_ROOT_NAME
# W46/S4: every inherited case (W30/W26/W25/W24/W34/W43 call sites) now runs
# against the v14 package.  The historical V12_ROOT alias name is kept so all
# 82 inherited case bodies stay byte-for-byte untouched.
# W77 re-point: the package under test is this card's ra2forge_patched_v16.
V12_ROOT = W43_ROOT / "ra2forge_patched_v16"
# W46/S4: READ-ONLY v13 reference (W43 card) for the v14<->v13 SHA-256 table.
V13_REF_ROOT = (REPO_ROOT / "lead" / "next_re_20261112_r02"
                / "W43_b_line_s3" / "ra2forge_patched_v13")
# Every inherited case (W30/W26/W25/W24/W34 call sites) runs against v12.
V11_ROOT = V12_ROOT  # alias kept for W34-inherited call sites (runs v12)
V10_ROOT = V12_ROOT  # alias kept for W30-inherited call sites (runs v12)
V9_ROOT = V12_ROOT   # alias kept for W26-inherited call sites (runs v12)
V8_ROOT = V12_ROOT   # alias kept for W25-inherited call sites (runs v12)
V7_ROOT = V12_ROOT   # alias kept for W24-inherited call sites (runs v12)
# READ-ONLY v10 reference for MS4 (byte-for-byte backward compatibility).
V10_REF_ROOT = (REPO_ROOT / "lead" / "next_re_20261112_r02"
                / "W30_csf_capability" / "ra2forge_patched_v10")
# READ-ONLY v11 reference for CSF_INST5: v13 no-CSF-switch build == v11.
V11_REF_ROOT = (REPO_ROOT / "lead" / "next_re_20261112_r02"
                / "W34_mapselmd" / "ra2forge_patched_v11")
# W43/S3: READ-ONLY v12 reference for the v13 <-> v12 SHA-256 backward-compat
# table (S3_COMPAT). v13 with NO new switch must be byte-identical to v12.
V12_REF_ROOT = (REPO_ROOT / "lead" / "next_re_20261112_r02"
                / "W41_csf_install" / "ra2forge_patched_v12")
# W43/S3: READ-ONLY W42 S2 contract fixtures (feature sets + sandbox states).
W42_EVIDENCE = (REPO_ROOT / "lead" / "next_re_20261112_r02"
                / "W42_b_line_s2" / "EVIDENCE")
W42_ROOT = (REPO_ROOT / "lead" / "next_re_20261112_r02" / "W42_b_line_s2")
# READ-ONLY official CSF source (byte-identical to ra2youli\langmd.mix).
OFFICIAL_MIX = REPO_ROOT / "ra2bench" / "langmd.mix"
W26_ROOT = (REPO_ROOT / "lead" / "next_re_20261112_r02"
            / "W26_dlc_unseal_fix")      # READ-ONLY reference card
V9_REF_ROOT = W26_ROOT / "ra2forge_patched_v9"  # READ-ONLY v9 reference for C6
W25_ROOT = (REPO_ROOT / "lead" / "next_re_20261112_r02"
            / "W25_dlc_unseal")          # READ-ONLY reference card
W24_ROOT = (REPO_ROOT / "lead" / "next_re_20261112_r02"
            / "W24_dlc_seal_fault")      # READ-ONLY reference card
W23_ROOT = (REPO_ROOT / "lead" / "next_re_20261112_r02"
            / "W23_dlc_verify")          # READ-ONLY reference card
W21_ROOT = (REPO_ROOT / "lead" / "next_re_20261112_r02"
            / "W21_dlc_orphan" / "ra2forge_patched")   # v0.5 reference (READ-ONLY use)
SANDBOX = W43_ROOT / "sandbox"
OUT = W43_ROOT / "out"
REAL_MANIFEST = REPO_ROOT / "ra2youli" / "ra2forge_install.json"
# READ-ONLY reuse of the W24/W25 injection drivers (pointed at v9 below).
SEAL_DRIVER = W24_ROOT / "tools" / "v7i_seal_fault_driver.py"
ROLLBACK_DRIVER = W25_ROOT / "tools" / "v8_rollback_fault_driver.py"
COMPOUND_ROLLBACK_DRIVER = W26_ROOT / "tools" / "v9_compound_rollback_driver.py"

PKG_ID_A = "org.ra2forge.probe-orphan"
PKG_ID_B = "org.ra2forge.other-campaign"

MANIFEST = "ra2forge_install.json"
SEAL = "ra2forge_install.json.seal"

PYTHON = sys.executable

# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

BATTLE_INI_TEXT = {
    "a_v1": "; Generated by RA2 Campaign Forge - APPENDED campaign entry.\n"
            "[Battles]\n15=RA2F1\n\n[RA2F1]\nDescription=ORPHAN PROBE (package A v1)\n",
    "a_v2": "; Generated by RA2 Campaign Forge - APPENDED campaign entry.\n"
            "[Battles]\n15=RA2F1\n\n[RA2F1]\nDescription=ORPHAN PROBE TWO (package A v2)\n",
    # PKG_B: a DIFFERENT package (different package_id) that ships the SAME
    # battle id RA2F1 - the T4 demonstration fixture.
    "b": "; Generated by RA2 Campaign Forge - APPENDED campaign entry.\n"
         "[Battles]\n15=RA2F1\n\n[RA2F1]\nDescription=OTHER CAMPAIGN (package B)\n",
}


def w(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


def make_pkg(root: Path, name: str, *, battle: str, maps: dict, mix: str,
             package_id: str | None, package_version: str | None) -> Path:
    pkg = root / name
    if pkg.exists():
        shutil.rmtree(pkg)
    pkg.mkdir(parents=True)
    w(pkg / "BATTLEMD98.INI", BATTLE_INI_TEXT[battle])
    for map_name, text in maps.items():
        w(pkg / map_name, text)
    w(pkg / "expandmd98.mix", mix)
    if package_id is not None:
        w(pkg / "ra2forge_package.json", json.dumps(
            {"tool": "ra2forge", "package_id": package_id,
             "package_version": package_version or "unknown"}, indent=2) + "\n")
    return pkg


def _rmtree_sandbox(path: Path) -> None:
    """Remove a sandbox subdir even if an earlier test left read-only files."""
    if not path.exists():
        return
    resolved = path.resolve()
    sandbox_resolved = SANDBOX.resolve()
    if sandbox_resolved != resolved and sandbox_resolved not in resolved.parents:
        raise ValueError(f"refusing to delete path outside SANDBOX: {path}")

    def _clear_ro(func, target, _exc):
        os.chmod(target, stat.S_IREAD | stat.S_IWRITE)
        func(target)

    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_clear_ro)
    else:
        shutil.rmtree(path, onerror=_clear_ro)


def build_fixtures() -> dict:
    pkgs = W43_ROOT / "sandbox" / "pkgs"
    _rmtree_sandbox(pkgs)
    fx = {}
    fx["A1"] = make_pkg(pkgs, "pkgA_v1", battle="a_v1",
                        maps={"X.MAP": "map X of package A v1\n",
                              "Y.MAP": "map Y of package A v1\n"},
                        mix="mix of package A v1\n",
                        package_id=PKG_ID_A, package_version="1.0")
    fx["A2"] = make_pkg(pkgs, "pkgA_v2", battle="a_v2",
                        maps={"Y.MAP": "map Y of package A v2 REVISED\n",
                              "Z.MAP": "map Z of package A v2\n"},
                        mix="mix of package A v2\n",
                        package_id=PKG_ID_A, package_version="2.0")
    fx["B"] = make_pkg(pkgs, "pkgB", battle="b",
                       maps={"W.MAP": "map W of package B\n"},
                       mix="mix of package B\n",
                       package_id=PKG_ID_B, package_version="1.0")
    fx["U1"] = make_pkg(pkgs, "pkgU_v1_unstamped", battle="a_v1",
                        maps={"X.MAP": "map X of package A v1\n",
                              "Y.MAP": "map Y of package A v1\n"},
                        mix="mix of package A v1\n",
                        package_id=None, package_version=None)
    fx["U2"] = make_pkg(pkgs, "pkgU_v2_unstamped", battle="a_v2",
                        maps={"Y.MAP": "map Y of package A v2 REVISED\n",
                              "Z.MAP": "map Z of package A v2\n"},
                        mix="mix of package A v2\n",
                        package_id=None, package_version=None)
    return fx


def make_golden(game: Path) -> None:
    """The W21-style inert golden game directory (never executed)."""
    _rmtree_sandbox(game)
    game.mkdir(parents=True)
    w(game / "gamemd.exe", "INERT PLACEHOLDER - NEVER EXECUTED\n")
    w(game / "RA2MD.INI", "[General]\n ; inert fixture\n")
    w(game / "BATTLEMD.INI", "[Battles]\n1=ALL1\n\n[ALL1]\nDescription=official\n")
    w(game / "USERMAP1.MAP", "the user's own map, never recorded\n")


def expected_digest(pkg: Path) -> str:
    """Mirror of install.package_digest_from_steps over package_files().

    W34: MAPSELMD.INI ships only when the package was built with --mapselmd.
    W41: ra2md.csf ships only when the package was built with --csf-out, so
    for all 51 inherited v11-style fixtures the shipped set is unchanged.
    """
    names = ["BATTLEMD98.INI"]
    if (pkg / "MAPSELMD.INI").is_file():
        names.append("MAPSELMD.INI")
    if (pkg / "ra2md.csf").is_file():
        names.append("ra2md.csf")
    names += sorted(p.name for p in pkg.glob("*.MAP"))
    if (pkg / "expandmd98.mix").is_file():
        names.append("expandmd98.mix")
    lines = []
    for name in sorted(names):
        sha = hashlib.sha256((pkg / name).read_bytes()).hexdigest()
        lines.append(f"{name} {sha}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def synthetic_v03_state(game: Path) -> dict:
    """A faithful v0.3-schema install state: manifest in the EXACT layout of
    ra2youli's real manifest, but with fixture bytes whose sha256 match the
    records (so orphans/uninstall judge them 'ours')."""
    make_golden(game)
    ech_originals = {f"ECH0{i}.MAP": f"original ECH0{i} (pre-ra2forge)\n"
                     for i in (1, 2, 3)}
    ech_installed = {name: f"v0.3-era campaign version of {name}\n"
                     for name in ech_originals}
    for name, text in ech_originals.items():
        w(game / (name + ".ra2forge.bak"), text)
    for name, text in ech_installed.items():
        w(game / name, text)
    ini_v03 = "v0.3-era BATTLEMD98.INI\n"
    mix_v03 = "v0.3-era expandmd98.mix\n"
    w(game / "BATTLEMD98.INI", ini_v03)
    w(game / "expandmd98.mix", mix_v03)
    fake_old_pkg = game.parent / "fake_v03_package"
    fake_old_pkg.mkdir(exist_ok=True)

    def entry(name, action, backup, data):
        return {"name": name, "action": action,
                "bytes": len(data.encode("utf-8")),
                "sha256": hashlib.sha256(data.encode("utf-8")).hexdigest(),
                "backup": backup}

    files = [
        entry("BATTLEMD98.INI", "created", None, ini_v03),
        *[entry(n, "replaced", n + ".ra2forge.bak", t)
          for n, t in ech_installed.items()],
        entry("expandmd98.mix", "created", None, mix_v03),
    ]
    manifest = {
        "tool": "ra2forge",
        "version": "0.3",
        "installed_at": "2026-09-27T11:05:23",
        "package": str(fake_old_pkg),
        "game_dir": str(game),
        "files": files,
        "warnings": [
            "BATTLEMD.INI present and left untouched; the campaign is "
            "appended by BATTLEMD98.INI (the engine merges both by battle "
            "id)."],
    }
    w(game / MANIFEST, json.dumps(manifest, indent=2) + "\n")
    return {"ech_originals": ech_originals,
            "ech_installed": ech_installed,
            "ini_v03": ini_v03, "mix_v03": mix_v03}


def real_manifest_state(game: Path) -> None:
    """A copy of the REAL ra2youli manifest (READ from the repo, never
    written back) over fabricated game files. The fabricated bytes cannot
    match the recorded sha256 - exactly the point of the compat test."""
    make_golden(game)
    for i in (1, 2, 3):
        w(game / f"ECH0{i}.MAP", f"fabricated bytes, NOT the recorded sha (ECH0{i})\n")
        w(game / (f"ECH0{i}.MAP" + ".ra2forge.bak"),
          f"fabricated original of ECH0{i}\n")
    w(game / "BATTLEMD98.INI", "fabricated BATTLEMD98.INI\n")
    w(game / "expandmd98.mix", "fabricated expandmd98.mix\n")
    shutil.copyfile(REAL_MANIFEST, game / MANIFEST)


# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------

def sha_tree(root: Path) -> str:
    lines = []
    for p in sorted(root.rglob("*")):
        if p.is_file():
            data = p.read_bytes()
            rel = p.relative_to(root).as_posix()
            lines.append(f"{hashlib.sha256(data).hexdigest()} {len(data):8d} {rel}")
    return "\n".join(lines)


def sha_tree_excluding(root: Path, *names: str) -> str:
    """sha_tree over everything EXCEPT the given (case-insensitive) names -
    used by C2 to account for the one seal file the v0.5 tool leaves behind
    (it predates the seal and does not know the name)."""
    skip = {n.lower() for n in names}
    lines = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name.lower() not in skip:
            data = p.read_bytes()
            rel = p.relative_to(root).as_posix()
            lines.append(f"{hashlib.sha256(data).hexdigest()} {len(data):8d} {rel}")
    return "\n".join(lines)


def tree_lines_without(tree: str, *names: str) -> str:
    """Line-set of an already-rendered sha_tree string, minus the given file
    names (used to compare a tree snapshot against a later tree while preserving
    sha_tree's path sort order)."""
    skip = {n.lower() for n in names}
    kept = []
    for line in tree.splitlines():
        rel = line.split(None, 2)[2].strip().lower()
        if rel not in skip:
            kept.append(line)
    return "\n".join(kept)


# v0.7 prints exactly these seal-related lines that v0.5 cannot print (it
# predates the seal). C1/C2 normalize them out of the byte-identity
# comparison - everything else must match exactly (documented per case and
# in DISAGREE.md).
_SEAL_LINE_MARKERS = ("install seal", SEAL)
# W25 adaptation: v8's uninstall prints an explicit three-state summary line
# ("  status: completed (exit code 0)") that the v0.5 reference cannot print;
# normalized out for the C1/C2 byte-identity comparison like the seal lines.
_STATUS_LINE_MARKER = "  status: "


def _norm_for_compare(text: str, *game_dirs: Path) -> str:
    kept = [ln for ln in text.splitlines()
            if not any(m in ln for m in _SEAL_LINE_MARKERS + (_STATUS_LINE_MARKER,))]
    text = "\n".join(kept)
    for gd in game_dirs:
        text = text.replace(str(gd), "<GAME_DIR>")
    return text


class Case:
    def __init__(self, name: str):
        self.name = name
        self.dir = SANDBOX / name
        _rmtree_sandbox(self.dir)
        self.dir.mkdir(parents=True)
        self.game = self.dir / "game"
        self.log: list[str] = []
        self.checks: list[tuple[str, bool, str]] = []
        self.failed = False

    def check(self, desc: str, cond: bool, detail: str = "") -> None:
        self.checks.append((desc, bool(cond), detail))
        if not cond:
            self.failed = True
        self.log.append(f"[assert] {desc} ... {'PASS' if cond else 'FAIL'}"
                        + (f"\n          {detail}" if detail and not cond else ""))

    def note(self, text: str) -> None:
        self.log.append(f"[note] {text}")

    def run_module(self, root: Path, args: list[str], label: str) -> tuple[int, str, str]:
        """Run python -B -X utf8 -m ra2forge <args> with cwd=<root>."""
        cmd = [PYTHON, "-B", "-X", "utf8", "-m", "ra2forge", *args]
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(cmd, cwd=str(root), env=env,
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=300)
        self.log.append(f"[cmd] {label}: {Path(root).name}$ "
                        + " ".join(["python", "-B", "-X", "utf8", "-m", "ra2forge", *args]))
        self.log.append(f"[exit] {proc.returncode}")
        self.log.append("--- stdout+stderr ---")
        self.log.append((proc.stdout + proc.stderr).rstrip() or "(no output)")
        self.log.append("--- end ---")
        return proc.returncode, proc.stdout, proc.stderr

    def install(self, pkg: Path, extra: list[str] = ()) -> tuple[int, str, str]:
        return self.run_module(V9_ROOT,
                               ["install", "--package", str(pkg),
                                "--game", str(self.game), *extra], "v9")

    def uninstall(self, extra: list[str] = ()) -> tuple[int, str, str]:
        return self.run_module(V9_ROOT,
                               ["uninstall", "--game", str(self.game), *extra],
                               "v9")

    def uninstall_json(self) -> tuple[int, str, str]:
        return self.run_module(V9_ROOT,
                               ["uninstall", "--game", str(self.game), "--json"],
                               "v9")

    def verify(self, extra: list[str] = ()) -> tuple[int, str, str]:
        return self.run_module(V9_ROOT,
                               ["verify", "--game", str(self.game), *extra],
                               "v9")

    def manifest(self) -> dict:
        return json.loads((self.game / MANIFEST).read_text(encoding="utf-8"))

    def finish(self) -> bool:
        verdict = "FAIL" if self.failed else "PASS"
        self.log.append(f"=== case {self.name}: {verdict} ===")
        (OUT / f"{self.name}.log").write_text("\n".join(self.log) + "\n",
                                              encoding="utf-8")
        return not self.failed

    def run_python(self, root: Path, code: str, label: str) -> tuple[int, str, str]:
        """Run python -B -X utf8 -c <code> with cwd=<root> and log cmd+output+exit."""
        cmd = [PYTHON, "-B", "-X", "utf8", "-c", code]
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(cmd, cwd=str(root), env=env,
                              capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=300)
        compact = " ".join(line.strip() for line in code.strip().splitlines())
        self.log.append(f"[cmd] {label}: {Path(root).name}$ python -B -X utf8 -c {compact!r}")
        self.log.append(f"[exit] {proc.returncode}")
        self.log.append("--- stdout+stderr ---")
        self.log.append((proc.stdout + proc.stderr).rstrip() or "(no output)")
        self.log.append("--- end ---")
        return proc.returncode, proc.stdout, proc.stderr


def run_driver(case: Case, pkg: Path, fail_at: str) -> tuple[int, str]:
    """Run W24's tools/v7_fail_driver.py (READ-ONLY reuse) against the v9
    build (real production path with one injected write failure)."""
    cmd = [PYTHON, "-B", "-X", "utf8", str(DRIVER),
           str(pkg), str(case.game), fail_at, str(V9_ROOT)]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(cmd, cwd=str(W43_ROOT), env=env,
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)
    case.log.append(f"[cmd] driver: python -B -X utf8 "
                    f"<W24 read-only tools>/v7_fail_driver.py "
                    f"<{pkg.name}> <game> <{fail_at}> <ra2forge_patched_v9>")
    case.log.append(f"[exit] {proc.returncode}")
    case.log.append("--- stdout+stderr ---")
    case.log.append((proc.stdout + proc.stderr).rstrip() or "(no output)")
    case.log.append("--- end ---")
    return proc.returncode, proc.stdout + proc.stderr


def run_seal_driver(case: Case, pkg: Path, mode: str) -> tuple[int, str]:
    """Run W24's seal-fault driver (READ-ONLY reuse, never modified) against
    the v9 build: the real production path with the seal write made to fail
    (mode = @seal, @seal_open or @seal_half; the injection is the explicit
    command-line mode - the package itself carries no injection code)."""
    cmd = [PYTHON, "-B", "-X", "utf8", str(SEAL_DRIVER),
           str(pkg), str(case.game), mode, str(V9_ROOT)]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(cmd, cwd=str(W43_ROOT), env=env,
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)
    case.log.append(f"[cmd] seal-driver: python -B -X utf8 "
                    f"<W24 read-only tools>/v7i_seal_fault_driver.py "
                    f"<{pkg.name}> <game> <{mode}> <ra2forge_patched_v9>")
    case.log.append(f"[exit] {proc.returncode}")
    case.log.append("--- stdout+stderr ---")
    case.log.append((proc.stdout + proc.stderr).rstrip() or "(no output)")
    case.log.append("--- end ---")
    return proc.returncode, proc.stdout + proc.stderr


def run_rollback_driver(case: Case, pkg: Path, mode: str) -> tuple[int, str]:
    """Run W25's double-fault driver (READ-ONLY reuse) against the v9 build:
    the real production path with the seal write failing on the test's own
    filesystem obstruction AND the record rollback failing on the read-only
    attribute the driver flips in the record->seal window."""
    cmd = [PYTHON, "-B", "-X", "utf8", str(ROLLBACK_DRIVER),
           str(pkg), str(case.game), mode, str(V9_ROOT)]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(cmd, cwd=str(W43_ROOT), env=env,
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)
    case.log.append(f"[cmd] rollback-driver: python -B -X utf8 "
                    f"<W25 read-only tools>/v8_rollback_fault_driver.py "
                    f"<{pkg.name}> <game> <{mode}> <ra2forge_patched_v9>")
    case.log.append(f"[exit] {proc.returncode}")
    case.log.append("--- stdout+stderr ---")
    case.log.append((proc.stdout + proc.stderr).rstrip() or "(no output)")
    case.log.append("--- end ---")
    return proc.returncode, proc.stdout + proc.stderr


def run_compound_rollback_driver(case: Case, pkg: Path, game: Path,
                                 mode: str) -> tuple[int, str]:
    """Run W26's compound rollback driver (tools/v9_compound_rollback_driver.py)
    against the v9 build: flips BOTH manifest and X.MAP read-only in-window."""
    cmd = [PYTHON, "-B", "-X", "utf8", str(COMPOUND_ROLLBACK_DRIVER),
           str(pkg), str(game), mode, str(V9_ROOT)]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(cmd, cwd=str(W43_ROOT), env=env,
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)
    case.log.append(f"[cmd] compound-rollback-driver: python -B -X utf8 "
                    f"tools/v9_compound_rollback_driver.py <{pkg.name}> "
                    f"<{game.name}> <{mode}> <ra2forge_patched_v9>")
    case.log.append(f"[exit] {proc.returncode}")
    case.log.append("--- stdout+stderr ---")
    case.log.append((proc.stdout + proc.stderr).rstrip() or "(no output)")
    case.log.append("--- end ---")
    return proc.returncode, proc.stdout + proc.stderr


# ---------------------------------------------------------------------------
# F/U/R-series helpers (fault injection)
# ---------------------------------------------------------------------------

DRIVER = W24_ROOT / "tools" / "v7_fail_driver.py"

def sha_file(path: Path) -> str | None:
    """SHA-256 of one file, or None when it is absent (recorded as such)."""
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def set_read_only(path: Path) -> None:
    os.chmod(path, stat.S_IREAD)


def clear_read_only(path: Path) -> None:
    os.chmod(path, stat.S_IREAD | stat.S_IWRITE)


def is_read_only(path: Path) -> bool:
    return not (path.stat().st_mode & stat.S_IWRITE)


def stage_residue(game: Path) -> list[str]:
    """Any staging/backup artefact a failed install could have left behind."""
    return sorted(p.name for p in game.iterdir()
                  if ".ra2forge-stage" in p.name or p.name.endswith(".ra2forge.bak"))


def seal_manifest_sha(game: Path) -> str | None:
    """The manifest_sha256 the seal must record for the CURRENT manifest
    bytes (canonical form: UTF-8, BOM tolerated, CRLF/CR -> LF) - a mirror
    of write_install_seal's hashing, used to prove a seal was RE-STAMPED to
    protect the standing record (byte-difference of the seal is NOT a valid
    criterion: sealed_at/installed_at carry seconds precision, so a
    same-second re-install of the same package may legitimately produce
    identical seal bytes)."""
    try:
        data = (game / MANIFEST).read_bytes().decode("utf-8-sig")
    except OSError:
        return None
    data = data.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def seal_covers(game: Path) -> bool:
    """True when the seal on disk parses AND its manifest_sha256 matches the
    CURRENT manifest bytes (i.e. the seal protects THIS record)."""
    try:
        seal = json.loads((game / SEAL).read_text(encoding="utf-8"))
        return (isinstance(seal, dict)
                and seal.get("manifest_sha256") == seal_manifest_sha(game))
    except (OSError, ValueError):
        return False


def build_u1_state(c: Case, pkg: Path) -> tuple[str, str]:
    """The card's U1 scenario, reusable by U3/U4/U5: golden -> install ->
    seal read-only -> uninstall (exit 10). Returns (golden_tree, seal_sha)."""
    make_golden(c.game)
    golden_tree = sha_tree(c.game)
    rc, out, err = c.install(pkg)
    c.check("U1-state: setup install exit 0", rc == 0, err)
    seal_sha = sha_file(c.game / SEAL)
    set_read_only(c.game / SEAL)
    rc, out, err = c.uninstall()
    c.check("U1-state: uninstall on a read-only seal exits 10", rc == 10,
            f"rc={rc} out={out[:200]}")
    return golden_tree, seal_sha


# ---------------------------------------------------------------------------
# cases (P/V/C/T = W22 suite kept intact, re-pointed at v0.8)
# ---------------------------------------------------------------------------

def case_P0(fx) -> Case:
    """P0 builder stamping: design 'package' object -> ra2forge_package.json
    -> fresh install writes the declared identity."""
    c = Case("P0")
    design_path = c.dir / "design_probe.json"
    design = {
        "campaign": {"name": "IDENTITY PROBE",
                     "description": "P0: design-declared package identity",
                     "side": "soviet", "id": "RA2F1"},
        "package": {"id": PKG_ID_A, "version": "0.1"},
        "missions": [{
            "name": "P0", "title": "Probe", 
            "briefing": "Commander! Identity probe (P0).",
            "theater": "TEMPERATE", "size": [90, 90],
            "player": {"house": "Russians"},
            "structures": [
                {"owner": "Russians", "type": "NACNST", "row": 60, "col": 45},
                {"owner": "Americans", "type": "GACNST", "row": 15, "col": 45,
                 "tag": "enemy_hq"}],
            "units": [{"owner": "Russians", "type": "MTNK", "row": 58, "col": 43}],
            "infantry": [{"owner": "Russians", "type": "E1", "row": 59, "col": 44}],
            "objectives": [{"type": "destroy_building", "structure_tag": "enemy_hq"}],
        }],
    }
    w(design_path, json.dumps(design, indent=2))
    rc, out, err = c.run_module(V8_ROOT, ["validate", str(design_path)], "v8")
    c.check("validate design exit 0", rc == 0, err)
    pkg = c.dir / "built" / "IDENTITY PROBE"
    rc, out, err = c.run_module(V8_ROOT, ["build", "--design", str(design_path),
                                          "--out", str(c.dir / "built")], "v8")
    c.check("build exit 0", rc == 0, err)
    stamp = pkg / "ra2forge_package.json"
    c.check("ra2forge_package.json written by build", stamp.is_file())
    if stamp.is_file():
        payload = json.loads(stamp.read_text(encoding="utf-8"))
        c.check("stamped package_id == " + PKG_ID_A,
                payload.get("package_id") == PKG_ID_A, str(payload))
        c.check("stamped package_version == 0.1",
                payload.get("package_version") == "0.1", str(payload))
    report = (pkg / "BUILD_REPORT.txt").read_text(encoding="utf-8")
    c.check("BUILD_REPORT names package_id and battle_id separately",
            "package_id=org.ra2forge.probe-orphan" in report
            and "battle_id=RA2F1" in report, report[:400])
    make_golden(c.game)
    rc, out, err = c.install(pkg)
    c.check("fresh install of stamped build exit 0", rc == 0, err)
    m = c.manifest()
    c.check("manifest package_id declared", m.get("package_id") == PKG_ID_A,
            str(m.get("package_id")))
    c.check("manifest package_version declared", m.get("package_version") == "0.1",
            str(m.get("package_version")))
    dg = expected_digest(pkg)
    c.check("manifest package_digest == recomputed digest of shipped set",
            m.get("package_digest") == dg,
            f"manifest={m.get('package_digest')} expected={dg}")
    c.check("every entry carries source_package_digest == package_digest",
            all(e.get("source_package_digest") == dg for e in m["files"]),
            str([e.get("name") for e in m["files"]
                 if e.get("source_package_digest") != dg]))
    rc, out, err = c.uninstall()
    c.check("uninstall exit 0", rc == 0, err)
    c.check("game dir back to golden (no manifest left)",
            not (c.game / MANIFEST).is_file())
    return c


def case_V1(fx) -> Case:
    """V1 升级（W21 流程 × 身份守门）: unstamped A→A′ at the same path.
    V1a: without --adopt-legacy refused (exit 4, zero writes);
    V1b: with --adopt-legacy the W21 upgrade flow runs (X.MAP orphan exits)."""
    c = Case("V1")
    make_golden(c.game)
    rc, out, err = c.install(fx["U1"])
    c.check("install unstamped U1 over empty dir exit 0", rc == 0, err)
    m1 = c.manifest()
    c.check("U1 manifest records package_id 'unknown' (undeclared)",
            m1.get("package_id") == "unknown", str(m1.get("package_id")))
    before = sha_tree(c.game)
    rc, out, err = c.install(fx["U2"])
    c.check("V1a: unstamped upgrade WITHOUT --adopt-legacy refused exit 4",
            rc == 4, f"rc={rc} err={err[:200]}")
    c.check("V1a: refusal text names --adopt-legacy",
            "--adopt-legacy" in (out + err), err[:300])
    c.check("V1a: zero writes (snapshot identical)", sha_tree(c.game) == before)
    rc, out, err = c.install(fx["U2"], ["--adopt-legacy"])
    c.check("V1b: unstamped upgrade WITH --adopt-legacy exit 0", rc == 0, err)
    xmap = c.game / "X.MAP"
    c.check("V1b: X.MAP orphan removed", not xmap.is_file())
    m2 = c.manifest()
    names = [e["name"] for e in m2["files"]]
    c.check("V1b: manifest lists only A' files (+ X exit recorded in removed_orphans)",
            "X.MAP" not in names and "Z.MAP" in names
            and any(o.get("name") == "X.MAP" for o in m2.get("removed_orphans", [])),
            str(names) + str(m2.get("removed_orphans")))
    c.check("V1b: manifest still package_id 'unknown' (package undeclared)",
            m2.get("package_id") == "unknown")
    c.check("V1b: supersedes records adopted_legacy=true",
            m2.get("supersedes", {}).get("adopted_legacy") is True,
            str(m2.get("supersedes")))
    return c


def case_V2(fx) -> Case:
    """V2 卸载还原: install A1 -> uninstall -> byte-identical to initial."""
    c = Case("V2")
    make_golden(c.game)
    initial = sha_tree(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("install A1 exit 0", rc == 0, err)
    rc, out, err = c.uninstall()
    c.check("uninstall exit 0", rc == 0, err)
    c.check("game dir byte-identical to initial", sha_tree(c.game) == initial)
    return c


def case_V3(fx) -> Case:
    """V3 升级后卸载: install A1 -> install A2 -> uninstall -> identical."""
    c = Case("V3")
    make_golden(c.game)
    initial = sha_tree(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("install A1 exit 0", rc == 0, err)
    rc, out, err = c.install(fx["A2"])
    c.check("install A2 (same id upgrade) exit 0, no flags needed", rc == 0, err)
    rc, out, err = c.uninstall()
    c.check("uninstall after upgrade exit 0", rc == 0, err)
    c.check("game dir byte-identical to initial", sha_tree(c.game) == initial)
    return c


def case_V4(fx) -> Case:
    """V4 用户同名文件不被删: user's own X.MAP is a content conflict (V4a,
    refused, zero writes) releasable only explicitly (V4b, user original
    lands in the backup slot)."""
    c = Case("V4")
    make_golden(c.game)
    user_x = "THE USER'S OWN X.MAP\n"
    w(c.game / "X.MAP", user_x)
    initial = sha_tree(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("V4a: install over user's X.MAP refused exit 1", rc == 1,
            f"rc={rc} err={err[:200]}")
    c.check("V4a: refusal is a content conflict",
            "definite content conflicts" in (out + err), err[:300])
    c.check("V4a: zero writes (snapshot identical)", sha_tree(c.game) == initial)
    rc, out, err = c.install(fx["A1"], ["--allow-content-conflict"])
    c.check("V4b: with --allow-content-conflict exit 0", rc == 0, err)
    bak = c.game / "X.MAP.ra2forge.bak"
    c.check("V4b: user original preserved in backup slot",
            bak.is_file() and bak.read_bytes() == user_x.encode("utf-8"))
    m = c.manifest()
    allowed = m.get("precheck", {}).get("allowed_content_conflicts") or []
    c.check("V4b: released conflict recorded in manifest",
            any("X.MAP" in a for a in allowed), str(allowed))
    rc, out, err = c.uninstall()
    c.check("V4b: uninstall exit 0 and user X.MAP restored", rc == 0
            and (c.game / "X.MAP").read_bytes() == user_x.encode("utf-8"), err)
    return c


def case_V5(fx) -> Case:
    """V5 中途失败回滚: injected write failures roll back to the exact
    pre-run state (fresh V5a / upgrade V5b / record write V5c)."""
    c = Case("V5")
    make_golden(c.game)
    initial = sha_tree(c.game)
    # V5a: fresh install fails at the first map copy
    rc, out = run_driver(c, fx["A1"], "X.MAP")
    c.check("V5a: driver exit 1", rc == 1, out[:200])
    c.check("V5a: rollback report present", "rollback" in out.lower(), out[:200])
    c.check("V5a: game dir byte-identical to initial", sha_tree(c.game) == initial)
    # V5b: upgrade fails mid-way, rolls back to exact post-A1 state
    rc, out, err = c.install(fx["A1"])
    c.check("V5b: install A1 exit 0", rc == 0, err)
    post_a1 = sha_tree(c.game)
    rc, out = run_driver(c, fx["A2"], "Z.MAP")
    c.check("V5b: driver exit 1", rc == 1, out[:200])
    c.check("V5b: game dir rolled back to exact post-A1 state",
            sha_tree(c.game) == post_a1)
    rc, out, err = c.uninstall()
    c.check("V5b: old record still valid - uninstall exit 0", rc == 0, err)
    c.check("V5b: uninstall returns to initial", sha_tree(c.game) == initial)
    # V5c: record-write failure AFTER the orphan exit -> orphan rolled back
    make_golden(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("V5c: install A1 exit 0", rc == 0, err)
    post_a1 = sha_tree(c.game)
    rc, out = run_driver(c, fx["A2"], "@record")
    c.check("V5c: driver exit 1", rc == 1, out[:200])
    c.check("V5c: rollback re-installed the removed orphan X.MAP from the "
            "previous package", "orphan removal of X.MAP" in out, out[:400])
    c.check("V5c: game dir byte-identical to post-A1", sha_tree(c.game) == post_a1)
    return c


def case_V6(fx) -> Case:
    """V6 路径穿越 / 非游戏目录 / 别名类拒绝（与 W21 相同的四个边缘）."""
    c = Case("V6")
    # V6a: non-game directory (no gamemd.exe)
    notgame = c.dir / "notgame"
    notgame.mkdir()
    c.game = notgame
    rc, out, err = c.install(fx["A1"])
    c.check("V6a: non-game dir refused exit 1", rc == 1, f"rc={rc} err={err[:200]}")
    c.check("V6a: message names the missing gamemd.exe",
            "does not look like a Yuri's Revenge directory" in (out + err),
            err[:300])
    c.check("V6a: nothing created in the fake dir",
            sorted(p.name for p in notgame.iterdir()) == [])
    c.game = c.dir / "game"
    # V6b: destination slot is a directory
    make_golden(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("V6b: install A1 exit 0", rc == 0, err)
    (c.game / "Z.MAP").mkdir()
    before = sha_tree(c.game)
    rc, out, err = c.install(fx["A2"])
    c.check("V6b: install over directory slot refused exit 1", rc == 1,
            f"rc={rc} err={err[:200]}")
    c.check("V6b: path-safety blocker named",
            "path-safety" in (out + err) and "not a regular file" in (out + err),
            err[:400])
    c.check("V6b: directory untouched, zero writes",
            sha_tree(c.game) == before and (c.game / "Z.MAP").is_dir())
    shutil.rmtree(c.game / "Z.MAP")
    # V6c: forged manifest with a traversal entry (canary outside the game dir)
    make_golden(c.game)
    canary_dir = c.dir / "canary"
    canary_dir.mkdir()
    w(canary_dir / "evil.MAP", "canary: must never be touched\n")
    canary_sha = sha_tree(canary_dir)
    user_sha = hashlib.sha256((c.game / "USERMAP1.MAP").read_bytes()).hexdigest()
    forged = {"tool": "ra2forge", "version": "0.6", "package_id": PKG_ID_A,
              "package_version": "1.0", "package_digest": "0" * 64,
              "installed_at": "2026-11-13T00:00:00",
              "package": str(c.dir / "forged_pkg"), "game_dir": str(c.game),
              "files": [
                  {"name": "..\\evil.MAP", "action": "created", "bytes": 1,
                   "sha256": "0" * 64, "backup": None},
                  {"name": "USERMAP1.MAP", "action": "created",
                   "bytes": (c.game / "USERMAP1.MAP").stat().st_size,
                   "sha256": user_sha, "backup": None}],
              "warnings": []}
    w(c.game / MANIFEST, json.dumps(forged, indent=2))
    rc, out, err = c.uninstall()
    c.check("V6c: uninstall exits 0 with refusals recorded", rc == 0,
            f"rc={rc} err={err[:200]}")
    c.check("V6c: traversal entry refused (not a plain file name)",
            "not a plain file name" in (out + err), out[:400])
    c.check("V6c: install record KEPT (refused entry stays visible)",
            (c.game / MANIFEST).is_file())
    c.check("V6c: canary untouched", sha_tree(canary_dir) == canary_sha)
    # V6d: legacy artefacts present -> strict risk refusal, zero writes
    make_golden(c.game)
    w(c.game / "ra2forge_uninstall.txt", "legacy record\nBATTLEMD.INI\n")
    before = sha_tree(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("V6d: install with legacy record refused exit 1", rc == 1,
            f"rc={rc} err={err[:200]}")
    c.check("V6d: unresolvable-risk refusal named",
            "unresolvable risks" in (out + err) and "legacy ra2forge_uninstall.txt"
            in (out + err), err[:400])
    c.check("V6d: zero writes (snapshot identical)", sha_tree(c.game) == before)
    return c


def case_P1(fx) -> Case:
    """P1 同 id 升级: declared same package_id upgrades with NO flags; all
    identity fields recorded; provenance per entry."""
    c = Case("P1")
    make_golden(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("install A1 (declared id) exit 0", rc == 0, err)
    m1 = c.manifest()
    dg1 = expected_digest(fx["A1"])
    c.check("A1 manifest: package_id/version/digest recorded",
            m1.get("package_id") == PKG_ID_A
            and m1.get("package_version") == "1.0"
            and m1.get("package_digest") == dg1,
            json.dumps({k: m1.get(k) for k in
                        ("package_id", "package_version", "package_digest")}))
    # W30 adaptation: the pin follows this card's TOOL_VERSION (1.0); the
    # assertion's intent is unchanged - manifest version == the TOOL version,
    # separate from the package_version.
    c.check("A1 manifest: tool version is the TOOL version 1.0, separate from "
            "package_version", m1.get("version") == "1.0"
            and m1.get("package_version") == "1.0",
            f"version={m1.get('version')} package_version={m1.get('package_version')}")
    before = sha_tree(c.game)
    rc, out, err = c.install(fx["A2"])
    c.check("install A2 (same id) exit 0 with NO flags", rc == 0, err)
    m2 = c.manifest()
    dg2 = expected_digest(fx["A2"])
    c.check("A2 manifest: package_id unchanged, package_version bumped",
            m2.get("package_id") == PKG_ID_A
            and m2.get("package_version") == "2.0")
    c.check("A2 manifest: package_digest == digest of A2's shipped set",
            m2.get("package_digest") == dg2,
            f"manifest={m2.get('package_digest')} expected={dg2}")
    c.check("A2 manifest: EVERY entry carries source_package_digest == A2 digest",
            m2["files"] and all(e.get("source_package_digest") == dg2
                                for e in m2["files"]),
            str([(e.get("name"), e.get("source_package_digest", "")[:8])
                 for e in m2["files"]]))
    c.check("A2 manifest: digest CHANGED vs A1 (content fingerprint works)",
            dg1 != dg2)
    c.check("A2 manifest: supersedes chain records A1 identity",
            m2.get("supersedes", {}).get("package_id") == PKG_ID_A
            and m2.get("supersedes", {}).get("package_version") == "1.0"
            and m2.get("supersedes", {}).get("package_digest") == dg1,
            str(m2.get("supersedes")))
    names = [e["name"] for e in m2["files"]]
    c.check("A2 manifest: X.MAP dropped, exit recorded in removed_orphans",
            "X.MAP" not in names
            and any(o.get("name") == "X.MAP"
                    for o in m2.get("removed_orphans", [])),
            str(names) + str(m2.get("removed_orphans")))
    c.check("A2: X.MAP really gone from disk", not (c.game / "X.MAP").is_file())
    c.check("A2: Y.MAP holds A2's revised bytes",
            (c.game / "Y.MAP").read_bytes()
            == (fx["A2"] / "Y.MAP").read_bytes())
    c.check("A2 path differs from A1 path yet upgrade ran (path is NOT identity)",
            str(fx["A1"]) != str(fx["A2"]))
    return c


def case_P2(fx) -> Case:
    """P2 异 id 拒绝（零写入）: a different declared package_id is refused
    with exit 3 and ZERO writes; --force and --allow-content-conflict do NOT
    bypass it."""
    c = Case("P2")
    make_golden(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("install A1 exit 0", rc == 0, err)
    before = sha_tree(c.game)
    rc, out, err = c.install(fx["B"])
    c.check("P2: different package_id refused exit 3", rc == 3,
            f"rc={rc} err={err[:200]}")
    c.check("P2: refusal says coexisting packages are not supported "
            "(初版不支持并存)",
            "coexisting packages" in err and "初版不支持并存" in err, err[:400])
    c.check("P2: refusal names both package ids",
            PKG_ID_A in err and PKG_ID_B in err, err[:400])
    c.check("P2: zero writes (snapshot identical)", sha_tree(c.game) == before)
    rc, out, err = c.install(fx["B"], ["--force"])
    c.check("P2: --force does NOT bypass the identity refusal (still exit 3)",
            rc == 3, f"rc={rc} err={err[:200]}")
    rc, out, err = c.install(fx["B"], ["--allow-content-conflict"])
    c.check("P2: --allow-content-conflict does NOT bypass it (still exit 3)",
            rc == 3, f"rc={rc} err={err[:200]}")
    rc, out, err = c.install(fx["B"], ["--adopt-legacy"])
    c.check("P2: --adopt-legacy does NOT bypass a declared mismatch (exit 3)",
            rc == 3, f"rc={rc} err={err[:200]}")
    c.check("P2: still zero writes after every attempt",
            sha_tree(c.game) == before)
    return c


def case_P3(fx) -> Case:
    """P3 旧清单无 package_id → 拒绝并要求 --adopt-legacy（零写入）.
    P3-main: synthetic faithful v0.3-schema state; P3-real: the REAL
    ra2youli manifest copy (read-only source)."""
    c = Case("P3")
    # P3-main: synthetic v0.3 state
    synthetic_v03_state(c.game)
    before = sha_tree(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("P3-main: install over v0.3 manifest refused exit 4", rc == 4,
            f"rc={rc} err={err[:200]}")
    c.check("P3-main: refusal demands --adopt-legacy",
            "--adopt-legacy" in err, err[:400])
    c.check("P3-main: zero writes (snapshot identical)", sha_tree(c.game) == before)
    # P3-real: the real manifest copy hits the same gate
    c.game = c.dir / "game_real"
    real_manifest_state(c.game)
    before_real = sha_tree(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("P3-real: install over the REAL ra2youli manifest copy refused "
            "exit 4", rc == 4, f"rc={rc} err={err[:200]}")
    c.check("P3-real: zero writes (snapshot identical)",
            sha_tree(c.game) == before_real)
    return c


def case_P4(fx) -> Case:
    """P4 --adopt-legacy 后正常升级: the synthetic v0.3 state is adopted,
    ECH originals restored from their backup slots, new identity recorded."""
    c = Case("P4")
    st = synthetic_v03_state(c.game)
    before = sha_tree(c.game)
    rc, out, err = c.install(fx["A1"], ["--adopt-legacy"])
    c.check("P4: adopt-legacy install exit 0", rc == 0, err)
    c.check("P4: recorded ECH originals restored from backup slots",
            all((c.game / n).read_bytes() == st["ech_originals"][n].encode("utf-8")
                for n in st["ech_originals"]),
            "ECH maps differ from their originals")
    c.check("P4: backup slots consumed",
            not (c.game / "ECH01.MAP.ra2forge.bak").is_file()
            and not (c.game / "ECH02.MAP.ra2forge.bak").is_file()
            and not (c.game / "ECH03.MAP.ra2forge.bak").is_file())
    m = c.manifest()
    names = [e["name"] for e in m["files"]]
    c.check("P4: manifest records the new declared identity",
            m.get("package_id") == PKG_ID_A
            and m.get("package_version") == "1.0")
    c.check("P4: ECH maps no longer recorded (they exited with the old record)",
            all(n not in names for n in st["ech_installed"]),
            str(names))
    c.check("P4: BATTLEMD98.INI entry carries original_absent=true "
            "(v0.3 had created it - no real original to restore)",
            any(e["name"] == "BATTLEMD98.INI"
                and e.get("original_absent") is True for e in m["files"]),
            str([e for e in m["files"] if e["name"] == "BATTLEMD98.INI"]))
    c.check("P4: supersedes records the adopted legacy identity",
            m.get("supersedes", {}).get("package_id") == "unknown"
            and m.get("supersedes", {}).get("adopted_legacy") is True,
            str(m.get("supersedes")))
    c.check("P4: state changed (adoption actually proceeded)",
            sha_tree(c.game) != before)
    rc, out, err = c.uninstall()
    c.check("P4: uninstall after adoption exit 0", rc == 0, err)
    c.check("P4: ra2forge campaign fully gone (recorded files removed, "
            "original_absent slots removed, not 'restored')",
            not (c.game / MANIFEST).is_file()
            and not (c.game / "BATTLEMD98.INI").is_file()
            and not (c.game / "expandmd98.mix").is_file()
            and not (c.game / "X.MAP").is_file()
            and not (c.game / "Y.MAP").is_file()
            and not any(p.name.endswith(".ra2forge.bak")
                        for p in c.game.iterdir()))
    c.check("P4: the user's golden files and the ECH originals survive",
            all((c.game / n).read_bytes() == st["ech_originals"][n].encode("utf-8")
                for n in st["ech_originals"])
            and (c.game / "USERMAP1.MAP").is_file()
            and (c.game / "BATTLEMD.INI").is_file())
    return c


def case_C1(fx) -> Case:
    """C1 向后兼容（真实旧清单副本 × uninstall）: the v0.9 behavior must
    match the W21 v0.5 build on the same input (byte-identical outputs modulo
    the game-dir path, v0.7+'s documented seal lines and v0.8+'s documented
    status summary line)."""
    c = Case("C1")
    c.note("v9-adaptation: comparison target is v0.9 (was v0.8 in W25); the "
           "extra v0.7+ output on this legacy input is the degraded-mode "
           "seal warning, and v0.8+ adds the explicit status summary line - "
           "both normalized out by _norm_for_compare")
    real_manifest_state(c.game)
    before = sha_tree(c.game)
    rc8, out8, err8 = c.uninstall()
    snap8 = sha_tree(c.game)
    c.check("C1: v0.9 uninstall of the REAL manifest copy exits 0", rc8 == 0,
            f"rc={rc8}")
    c.check("C1: v0.9 keeps the record (changed bytes refused, state visible)",
            (c.game / MANIFEST).is_file())
    c.note("v9-adaptation evidence: the v0.7+ run printed extra warning line(s) "
           "about the seal and v0.8+ prints the status summary line; shown in "
           "the command log above")
    # same scenario against the W21 v0.5 build (read-only use: -B, no pycache)
    game5 = c.dir / "game_v05"
    real_manifest_state(game5)
    before5 = sha_tree(game5)
    c.log.append(f"[cmd] v5-reference: same state built from the same manifest "
                 f"copy ({REAL_MANIFEST})")
    rc5, out5, err5 = c.run_module(W21_ROOT, ["uninstall", "--game", str(game5)],
                                   "v5(W21)")
    c.check("C1: v0.5 reference exits with the SAME code", rc5 == rc8,
            f"v5={rc5} v9={rc8}")
    c.check("C1: v0.5 and v0.9 outputs are byte-identical (modulo the game "
            "dir path in the header, the documented seal warning line(s) and "
            "v0.8+'s documented status summary line)",
            _norm_for_compare(out5 + err5, game5).rstrip()
            == _norm_for_compare(out8 + err8, c.game).rstrip(),
            "outputs differ - see log")
    c.check("C1: v0.5 and v0.9 end states are byte-identical",
            sha_tree(game5) == snap8)
    c.check("C1: both runs started from identical states",
            before5 == before)
    return c


def case_C2(fx) -> Case:
    """C2 向后兼容（新字段清单 × 旧工具卸载）: a v0.9 manifest (with
    package_id / package_digest / source_package_digest / seal) uninstalled
    by the W21 v0.5 build must behave identically to the v0.9 uninstall -
    except the ONE seal file the old tool leaves behind (it predates the
    seal), which is asserted explicitly."""
    c = Case("C2")
    c.note("v9-adaptation: the install runs v0.9 (manifest + seal); the "
           "end-state comparison excludes ra2forge_install.json.seal and "
           "asserts the v0.5 side keeps it while the v0.9 side removes it; "
           "the status summary line is normalized out of the output compare")
    make_golden(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("C2: install A1 exit 0 (v0.9 manifest with new fields)", rc == 0, err)
    m = c.manifest()
    c.check("C2: manifest really carries the new fields",
            all(k in m for k in ("package_id", "package_version",
                                 "package_digest"))
            and all("source_package_digest" in e for e in m["files"]))
    c.check("C2: install wrote the seal next to the manifest",
            (c.game / SEAL).is_file())
    game8, game5 = c.dir / "game_un_v9", c.dir / "game_un_v5"
    shutil.copytree(c.game, game8)
    shutil.copytree(c.game, game5)
    c.game = game8
    rc8, out8, err8 = c.uninstall()
    snap8 = sha_tree(game8)
    rc5, out5, err5 = c.run_module(W21_ROOT, ["uninstall", "--game", str(game5)],
                                   "v5(W21)")
    c.check("C2: v0.5 uninstall of a v0.9 manifest exits with the same code",
            rc5 == rc8 == 0, f"v5={rc5} v9={rc8}")
    c.check("C2: v0.5 and v0.9 outputs byte-identical (modulo the game dir "
            "path in the header, the documented seal lines and v0.8+'s "
            "documented status summary line)",
            _norm_for_compare(out5 + err5, game5).rstrip()
            == _norm_for_compare(out8 + err8, game8).rstrip())
    c.check("C2: v0.5 and v0.9 end states byte-identical EXCEPT the seal file "
            "the old tool leaves behind",
            sha_tree_excluding(game5, SEAL) == sha_tree_excluding(game8, SEAL))
    c.check("C2: the v0.5 run leaves the seal (it predates the seal and "
            "ignores the name) - documented artifact, not silent data loss",
            (game5 / SEAL).is_file())
    c.check("C2: the v0.9 run removes the seal with the record",
            not (game8 / SEAL).is_file())
    c.check("C2: both restore the golden files exactly (no manifest left)",
            not (game5 / MANIFEST).is_file()
            and not (game8 / MANIFEST).is_file()
            and (game5 / "USERMAP1.MAP").is_file())
    return c


def case_T4(fx) -> Case:
    """T4 demonstration: package_id and battle ID are independent namespaces.
    A1/A2: same package_id, same battle id, different content -> upgrade OK
    (P1). PKG_B: different package_id, SAME battle id -> refused by the
    identity gate (P2) - the battle-id merge collision can never even happen.
    The battle ids here are parsed from the shipped BATTLEMD98.INI files."""
    c = Case("T4")
    battle_ids = {}
    for label, pkg in (("A1", fx["A1"]), ("A2", fx["A2"]), ("B", fx["B"])):
        text = (pkg / "BATTLEMD98.INI").read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("15="):
                battle_ids[label] = line.split("=", 1)[1].strip()
        ids = json.loads((pkg / "ra2forge_package.json").read_text(encoding="utf-8")) \
            if (pkg / "ra2forge_package.json").is_file() else {"package_id": "<none>"}
        c.log.append(f"[fact] {label}: package_id={ids['package_id']} "
                     f"battle_id={battle_ids.get(label)}")
    c.log.append("[fact] B's BATTLEMD98.INI carries the SAME battle id RA2F1 "
                 "as A's - a deliberate collision fixture for the T4 argument")
    c.check("A1 and A2 share package_id AND battle id (upgrade path, P1)",
            battle_ids["A1"] == battle_ids["A2"] == "RA2F1"
            and fx["A1"].name != fx["A2"].name)
    c.check("B has a DIFFERENT package_id but the SAME battle id",
            battle_ids["B"] == "RA2F1"
            and battle_ids["B"] == battle_ids["A1"]
            and PKG_ID_B != PKG_ID_A)
    # the P2 judgment applies: B cannot enter a directory A owns
    make_golden(c.game)
    c.install(fx["A1"])
    rc, out, err = c.install(fx["B"])
    c.check("T4: same battle id, different package_id -> identity refusal "
            "exit 3 (installer-level judgment)", rc == 3, f"rc={rc}")
    c.log.append(
        "[conclusion] package_id decides whether the INSTALLER treats a "
        "directory as this package's own (exit 3/4 gates). battle_id decides "
        "how the ENGINE merges BATTLEMD*.INI entries (0x46CE10, by battle "
        "id). Same package_id + different battle id across versions would be "
        "an authoring bug (the campaign entry would orphan in the menu); "
        "different package_id + same battle id is rejected at install time "
        "here, and would collide in the campaign menu if coexistence were "
        "ever allowed - two independent checks over two independent fields.")
    return c


# ---------------------------------------------------------------------------
# S-series (SEAL-CHAIN01: verify + seal trust chain, W23, kept intact)
# ---------------------------------------------------------------------------

def case_S1(fx) -> Case:
    """S1 正常安装后 verify: exit 0, all ok; --json machine report; --help
    documents the exit-code table."""
    c = Case("S1")
    make_golden(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("install A1 exit 0", rc == 0, err)
    c.check("seal file written next to the manifest",
            (c.game / SEAL).is_file())
    rc, out, err = c.verify()
    c.check("S1: verify exit 0", rc == 0, f"rc={rc} out={out[:300]}")
    c.check("S1: seal-era manifest reported",
            "seal era (tool >= 0.7)" in out, out[:400])
    c.check("S1: structure OK", "structure: OK" in out, out[:400])
    c.check("S1: digest OK (self-consistency line present)",
            "package_digest: OK" in out
            and "self-consistency of the records only" in out, out[:400])
    c.check("S1: seal OK", "seal: OK" in out, out[:400])
    c.check("S1: counts 4 ok / 0 changed / 0 missing",
            "files: 4 ok, 0 changed, 0 missing/unreadable" in out, out[:400])
    c.check("S1: orphans none", "orphans: none" in out, out[:400])
    rc, out, err = c.verify(["--json"])
    c.check("S1: verify --json exit 0", rc == 0, f"rc={rc}")
    j = json.loads(out)
    c.check("S1: json exit_code 0 + clean counts",
            j["exit_code"] == 0 and j["counts"] == {"ok": 4, "changed": 0,
                                                    "missing": 0, "orphans": 0},
            json.dumps(j["counts"]))
    c.check("S1: json seal ok and expected",
            j["seal"]["state"] == "ok" and j["seal"]["expected"] is True,
            str(j["seal"]))
    c.check("S1: json digest match true",
            j["digest"]["match"] is True, str(j["digest"]))
    rc, out, err = c.run_module(V8_ROOT, ["verify", "--help"], "v8")
    c.check("S1: verify --help exit 0 and documents every exit code",
            rc == 0 and "exit codes:" in out
            and "5  manifest structure" in out
            and "6  package_digest mismatch" in out
            and "7  install seal MISSING" in out
            and "8  install seal MISMATCH" in out
            and "9  drift" in out, out[:900])
    return c


def case_S2(fx) -> Case:
    """S2 手工改动某个已装文件 1 字节后 verify: changed detected, exit 9,
    file named; digest STILL OK (records self-consistent - the digest is not
    a disk proof); restoring the byte restores exit 0."""
    c = Case("S2")
    make_golden(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("install A1 exit 0", rc == 0, err)
    y = c.game / "Y.MAP"
    original = y.read_bytes()
    y.write_bytes(original[:-1] + bytes([original[-1] ^ 0x01]))
    c.check("S2: exactly one byte flipped",
            len(original) == len(y.read_bytes())
            and sum(a != b for a, b in zip(original, y.read_bytes())) == 1)
    rc, out, err = c.verify()
    c.check("S2: verify exit 9 (drift)", rc == 9, f"rc={rc} out={out[:300]}")
    c.check("S2: CHANGED class + file name reported",
            "CHANGED" in out and "Y.MAP" in out, out[:400])
    c.check("S2: both hashes shown (recorded vs disk)",
            "recorded" in out and "disk" in out, out[:400])
    c.check("S2: digest still OK while a file drifted (records-only proof)",
            "package_digest: OK" in out, out[:400])
    c.check("S2: exit-code line 9 named", "exit code: 9" in out, out[:400])
    rc, out, err = c.verify(["--json"])
    j = json.loads(out)
    c.check("S2: json exit_code 9 + changed=1 + Y.MAP status changed",
            j["exit_code"] == 9 and j["counts"]["changed"] == 1
            and any(f["name"] == "Y.MAP" and f["status"] == "changed"
                    for f in j["files"]), json.dumps(j["counts"]))
    y.write_bytes(original)
    rc, out, err = c.verify()
    c.check("S2: after restoring the byte, verify exit 0 again", rc == 0,
            f"rc={rc}")
    return c


def case_S3(fx) -> Case:
    """S3 手工删除某个已装文件后 verify: missing detected, exit 9."""
    c = Case("S3")
    make_golden(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("install A1 exit 0", rc == 0, err)
    (c.game / "X.MAP").unlink()
    rc, out, err = c.verify()
    c.check("S3: verify exit 9", rc == 9, f"rc={rc} out={out[:300]}")
    c.check("S3: MISSING class + file name reported",
            "MISSING" in out and "X.MAP" in out, out[:400])
    rc, out, err = c.verify(["--json"])
    j = json.loads(out)
    c.check("S3: json exit_code 9 + missing=1",
            j["exit_code"] == 9 and j["counts"]["missing"] == 1
            and any(f["name"] == "X.MAP" and f["status"] == "missing"
                    for f in j["files"]), json.dumps(j["counts"]))
    return c


def case_S4(fx) -> Case:
    """S4 手工把清单某条 sha256 改成别的值: manifest self-consistency failure
    (package_digest mismatch, exit 6) - the digest check is exactly the
    guard; the seal ALSO trips (manifest bytes changed), digest wins by
    severity; the disk check shows the same file as changed against the
    forged record."""
    c = Case("S4")
    make_golden(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("install A1 exit 0", rc == 0, err)
    m = c.manifest()
    target = next(e for e in m["files"] if e["name"] == "Y.MAP")
    old_sha = target["sha256"]
    target["sha256"] = "ab" * 32
    (c.game / MANIFEST).write_text(
        json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rc, out, err = c.verify()
    c.check("S4: verify exit 6 (digest mismatch)", rc == 6,
            f"rc={rc} out={out[:300]}")
    c.check("S4: package_digest MISMATCH reported",
            "package_digest: MISMATCH" in out, out[:400])
    c.check("S4: disk check flags the same file (record vs disk disagree)",
            "CHANGED" in out and "Y.MAP" in out, out[:400])
    c.check("S4: exit-code line 6 named", "exit code: 6" in out, out[:400])
    rc, out, err = c.verify(["--json"])
    j = json.loads(out)
    c.check("S4: json exit_code 6 + digest.match False",
            j["exit_code"] == 6 and j["digest"]["match"] is False,
            str(j["digest"]))
    c.check("S4: json seal ALSO flags mismatch (manifest bytes changed)",
            j["seal"]["state"] == "mismatch", str(j["seal"]))
    c.check("S4: the forged sha differs from the original record",
            old_sha != "ab" * 32)
    return c


def case_S5(fx) -> Case:
    """S5 删掉 seal 后 uninstall: explicitly refused (exit 7), NOTHING
    deleted, --force does NOT bypass, verify flags the same state, and the
    documented recovery (re-install of the SAME package) works."""
    c = Case("S5")
    make_golden(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("install A1 exit 0", rc == 0, err)
    (c.game / SEAL).unlink()
    before = sha_tree(c.game)
    rc, out, err = c.verify()
    c.check("S5: verify exit 7 (seal missing)", rc == 7, f"rc={rc}")
    c.check("S5: verify names the missing seal",
            "MISSING" in out and SEAL in out, out[:400])
    rc, out, err = c.uninstall()
    c.check("S5: uninstall REFUSED exit 7 (never a silent delete)", rc == 7,
            f"rc={rc} out={out[:300]}")
    c.check("S5: refusal names the seal state",
            "uninstall REFUSED" in out and "seal missing" in out, out[:400])
    c.check("S5: refusal says nothing was touched and documents --force",
            "UNTOUCHED" in out and "--force does NOT bypass" in out, out[:400])
    c.check("S5: zero writes (snapshot identical)", sha_tree(c.game) == before)
    c.check("S5: manifest kept", (c.game / MANIFEST).is_file())
    c.check("S5: recorded files kept",
            (c.game / "X.MAP").is_file() and (c.game / "Y.MAP").is_file())
    rc, out, err = c.uninstall(["--force"])
    c.check("S5: --force does NOT bypass the seal gate (still exit 7)",
            rc == 7, f"rc={rc}")
    c.check("S5: still zero writes after --force", sha_tree(c.game) == before)
    # documented recovery: re-install the SAME package, then uninstall
    rc, out, err = c.install(fx["A1"])
    c.check("S5: recovery - re-install of the SAME package exit 0", rc == 0,
            err)
    c.check("S5: recovery - seal re-established",
            (c.game / SEAL).is_file())
    rc, out, err = c.uninstall()
    c.check("S5: recovery - uninstall now completes exit 0", rc == 0, err)
    c.check("S5: recovery - manifest and seal both gone",
            not (c.game / MANIFEST).is_file() and not (c.game / SEAL).is_file())
    return c


def case_S6(fx) -> Case:
    """S6 篡改 seal 后 uninstall: refused with the reason (exit 8) - valid
    seal JSON with a wrong hash (S6a), corrupt seal (S6b), and verify flags
    the same state (S6c)."""
    c = Case("S6")
    make_golden(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("install A1 exit 0", rc == 0, err)
    seal_path = c.game / SEAL
    # S6a: tampered seal - valid JSON, wrong manifest_sha256
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["manifest_sha256"] = "0" * 64
    seal_path.write_text(json.dumps(seal, indent=2) + "\n", encoding="utf-8")
    before_a = sha_tree(c.game)   # snapshot AFTER the case's own tamper
    rc, out, err = c.uninstall()
    c.check("S6a: tampered seal refused exit 8", rc == 8,
            f"rc={rc} out={out[:300]}")
    c.check("S6a: refusal explains the mismatch",
            "seal mismatch" in out and "does not match" in out, out[:400])
    c.check("S6a: zero writes by uninstall (snapshot identical)",
            sha_tree(c.game) == before_a)
    c.check("S6a: manifest kept", (c.game / MANIFEST).is_file())
    # S6b: corrupt seal - not JSON at all
    seal_path.write_text("not json {{{", encoding="utf-8")
    before_b = sha_tree(c.game)   # snapshot AFTER the case's own tamper
    rc, out, err = c.uninstall()
    c.check("S6b: corrupt seal refused exit 8", rc == 8, f"rc={rc} out={out[:200]}")
    c.check("S6b: refusal names the corruption", "seal corrupt" in out,
            out[:400])
    c.check("S6b: manifest kept, nothing deleted by uninstall",
            (c.game / MANIFEST).is_file() and sha_tree(c.game) == before_b)
    # S6c: verify flags the same corrupt seal
    rc, out, err = c.verify()
    c.check("S6c: verify exit 8 on the corrupt seal", rc == 8, f"rc={rc}")
    c.check("S6c: verify names the corruption", "CORRUPT" in out, out[:400])
    return c


def case_S7(fx) -> Case:
    """S7 旧清单（无 seal、无 package_id 的 v0.3 真实清单副本）verify:
    degraded mode - warns, still fully runs, no crash, and NEVER a false
    all-ok (S7a drift on fabricated bytes). S7b: a v0.3 state whose files
    all match verifies 0 - but with the degraded warning, never silently."""
    c = Case("S7")
    c.note("S7 uses the REAL ra2youli manifest (READ-only copy), same source "
           f"as C1/P3: {REAL_MANIFEST}")
    # S7a: real manifest copy over fabricated bytes
    real_manifest_state(c.game)
    rc, out, err = c.verify()
    c.check("S7a: verify runs without crashing", rc in (0, 5, 9), f"rc={rc}")
    c.check("S7a: exit 9 - drift detected on the fabricated bytes", rc == 9,
            f"rc={rc}")
    c.check("S7a: degraded-mode warning present (legacy manifest)",
            "legacy manifest" in out and "DEGRADED" in out, out[:400])
    c.check("S7a: digest check skipped for the legacy manifest",
            "package_digest: (skipped" in out, out[:400])
    c.check("S7a: NOT a false all-ok (changed/missing counted, exit 9)",
            "exit code: 9" in out and "MISSING" not in out and "CHANGED" in out,
            out[:400])
    rc, outj, err = c.verify(["--json"])
    j = json.loads(outj)
    c.check("S7a: json exit_code 9, legacy_degraded true, changed > 0",
            j["exit_code"] == 9 and j["legacy_degraded"] is True
            and j["counts"]["changed"] > 0, json.dumps(j["counts"]))
    c.check("S7a: json digest is None (skipped) and seal not expected",
            j["digest"] is None and j["seal"]["expected"] is False,
            str(j["seal"]))
    # S7b: v0.3 manifest whose files ALL match -> exit 0 WITH the warning
    synthetic_v03_state(c.game)
    rc, out, err = c.verify()
    c.check("S7b: fully-matching v0.3 state verifies exit 0 (degraded, "
            "runnable, no crash)", rc == 0, f"rc={rc} out={out[:300]}")
    c.check("S7b: degraded warning still present (never a silent legacy "
            "upgrade to ok)", "DEGRADED" in out, out[:400])
    c.check("S7b: recorded backup slots are NOT orphans (accounted by the "
            "manifest)", "orphans: none" in out, out[:400])
    return c


def case_S8(fx) -> Case:
    """S8 孤儿文件 verify: planted ra2forge-characteristic files are listed
    as orphans; the manifest and seal themselves are NOT; orphans do not
    change the exit code (documented)."""
    c = Case("S8")
    make_golden(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("install A1 exit 0", rc == 0, err)
    w(c.game / "X.MAP.ra2forge.bak", "manually planted orphan backup slot\n")
    w(c.game / "W.MAP.ra2forge.removed.bak", "manually planted removed-original\n")
    rc, out, err = c.verify()
    c.check("S8: verify exit 0 (orphans are listed, do not change the code - "
            "documented behavior)", rc == 0, f"rc={rc} out={out[:300]}")
    c.check("S8: orphan .bak listed", "X.MAP.ra2forge.bak" in out, out[:400])
    c.check("S8: orphan .removed.bak listed",
            "W.MAP.ra2forge.removed.bak" in out, out[:400])
    rc, outj, err = c.verify(["--json"])
    j = json.loads(outj)
    c.check("S8: json orphans == exactly the two planted names",
            sorted(j["orphans"]) == ["W.MAP.ra2forge.removed.bak",
                                     "X.MAP.ra2forge.bak"], str(j["orphans"]))
    c.check("S8: manifest/seal themselves NOT counted as orphans",
            all("ra2forge_install.json" not in o for o in j["orphans"]),
            str(j["orphans"]))
    c.check("S8: json exit_code 0 with orphans counted",
            j["exit_code"] == 0 and j["counts"]["orphans"] == 2,
            json.dumps(j["counts"]))
    return c


# ---------------------------------------------------------------------------
# F-series (W24: seal-write fault injection, kept intact except F7's
# uninstall section, which pinned the defect this card fixes)
# ---------------------------------------------------------------------------

def case_F0(fx) -> Case:
    """F0 对照组: the exact sequences the F-series injects into, run with NO
    injection, all succeed - proves the fixtures work and the v8 package's
    normal path is unchanged (the copied 30 cases are the systematic
    control; this is the local per-sequence control). Also proves the seal
    driver injects NOTHING without an explicit mode (usage refusal, game
    dir untouched)."""
    c = Case("F0")
    make_golden(c.game)
    golden_tree = sha_tree(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("F0: fresh install A1 exit 0 (no injection)", rc == 0, err)
    c.check("F0: manifest + seal written",
            (c.game / MANIFEST).is_file() and (c.game / SEAL).is_file())
    tree1 = sha_tree(c.game)
    rc, out, err = c.install(fx["A2"])
    c.check("F0: update install A2 exit 0 (the sequence F3 injects into)",
            rc == 0, err)
    c.check("F0: seal rewritten next to the updated manifest",
            (c.game / SEAL).is_file())
    rc, out, err = c.verify()
    c.check("F0: verify exit 0 with seal OK", rc == 0 and "seal: OK" in out,
            f"rc={rc} out={out[:300]}")
    rc, out, err = c.uninstall()
    c.check("F0: uninstall exit 0", rc == 0, err)
    c.check("F0: game dir back to golden byte-for-byte",
            sha_tree(c.game) == golden_tree)
    # driver default-off proof: no mode -> usage refusal BEFORE any install
    rc, out = run_seal_driver(c, fx["A1"], "@no_such_mode")
    c.check("F0: seal driver without a valid mode exits 3 (no injection)",
            rc == 3, f"rc={rc} out={out[:300]}")
    c.check("F0: game dir still golden after the refused driver run",
            sha_tree(c.game) == golden_tree)
    return c


def case_F1(fx) -> Case:
    """F1 形态 (a) 注入: fresh install, the seal write fails outright
    (driver @seal). Assert: install exit 1 with the rollback message; the
    manifest NEVER lands (state identical to pre-install); no staging
    residue; verify/uninstall immediately usable."""
    c = Case("F1")
    make_golden(c.game)
    pre_tree = sha_tree(c.game)
    c.note(f"pre-install game dir (sha256 len name):\n{pre_tree}")
    rc, out = run_seal_driver(c, fx["A1"], "@seal")
    c.check("F1: injected install exit 1", rc == 1, f"rc={rc} out={out[:400]}")
    c.check("F1: message names the seal write failure",
            "could not be written" in out and SEAL in out, out[:500])
    c.check("F1: message claims record rollback to previous bytes",
            "the install record was rolled back to its previous bytes" in out,
            out[:500])
    c.check("F1: message claims package files UNCHANGED + rollback lines",
            "the package files are UNCHANGED" in out
            and "install aborted mid-write" in out
            and "created file removed" in out, out[:600])
    c.check("F1: manifest ABSENT after failure (pre-install state had none)",
            not (c.game / MANIFEST).exists())
    c.check("F1: seal ABSENT after failure",
            not (c.game / SEAL).exists())
    c.check("F1: no staging/backup residue",
            stage_residue(c.game) == [], str(stage_residue(c.game)))
    c.check("F1: game dir byte-identical to pre-install golden",
            sha_tree(c.game) == pre_tree)
    c.note(f"post-failure game dir (sha256 len name):\n{sha_tree(c.game)}")
    rc, out, err = c.verify()
    c.check("F1: verify right after failure exit 0 (nothing to verify)",
            rc == 0 and "nothing to verify" in out, f"rc={rc} out={out[:300]}")
    rc, out, err = c.uninstall()
    c.check("F1: uninstall right after failure exit 0 (nothing recorded)",
            rc == 0 and "nothing recorded to remove" in out,
            f"rc={rc} out={out[:300]}")
    c.check("F1: still byte-identical to golden after verify+uninstall",
            sha_tree(c.game) == pre_tree)
    return c


def case_F2(fx) -> Case:
    """F2 形态 (b) 注入: fresh install, the seal's staged write lands a REAL
    partial prefix on disk then fails ENOSPC (driver @seal_half). Assert:
    same rollback outcome as F1; the partial staging file is cleaned by the
    production error path; no residue; directory back to golden."""
    c = Case("F2")
    make_golden(c.game)
    pre_tree = sha_tree(c.game)
    c.note(f"pre-install game dir (sha256 len name):\n{pre_tree}")
    rc, out = run_seal_driver(c, fx["A1"], "@seal_half")
    c.check("F2: injected install exit 1", rc == 1, f"rc={rc} out={out[:400]}")
    c.check("F2: ENOSPC-style failure with a real partial byte count",
            "simulated disk full (ENOSPC)" in out and "landed " in out
            and "bytes" in out, out[:500])
    c.check("F2: the partial write went through the production staged path "
            "(the driver wraps only the real staged seal write; the message "
            "carries the production rollback claim)",
            "could not be written" in out
            and "the install record was rolled back to its previous bytes" in out,
            out[:500])
    c.check("F2: manifest ABSENT after failure", not (c.game / MANIFEST).exists())
    c.check("F2: seal ABSENT after failure (no half-written seal standing)",
            not (c.game / SEAL).exists())
    c.check("F2: no staging residue (production cleanup unlinked the partial "
            "staging file)", stage_residue(c.game) == [],
            str(stage_residue(c.game)))
    c.check("F2: game dir byte-identical to pre-install golden",
            sha_tree(c.game) == pre_tree)
    c.note(f"post-failure game dir (sha256 len name):\n{sha_tree(c.game)}")
    rc, out, err = c.verify()
    c.check("F2: verify exit 0 immediately after failure",
            rc == 0 and "nothing to verify" in out, f"rc={rc} out={out[:300]}")
    rc, out, err = c.uninstall()
    c.check("F2: uninstall exit 0 immediately after failure",
            rc == 0 and "nothing recorded to remove" in out,
            f"rc={rc} out={out[:300]}")
    return c


def case_F3(fx) -> Case:
    """F3 形态 (c) 注入: an UPDATE over an existing seal-era install, the new
    seal write fails (driver @seal). The core byte-identity proof: the
    manifest must come back EXACTLY (SHA-256) to the pre-update bytes and
    the previous seal must stay untouched."""
    c = Case("F3")
    make_golden(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("F3: setup install A1 exit 0", rc == 0, err)
    m1, s1 = sha_file(c.game / MANIFEST), sha_file(c.game / SEAL)
    c.check("F3: setup produced manifest + seal",
            m1 is not None and s1 is not None)
    c.note(f"pre-update manifest sha256: {m1}\npre-update seal sha256:     {s1}")
    pre_tree = sha_tree(c.game)
    c.note(f"pre-update game dir (sha256 len name):\n{pre_tree}")
    rc, out = run_seal_driver(c, fx["A2"], "@seal")
    c.check("F3: injected update install exit 1", rc == 1,
            f"rc={rc} out={out[:400]}")
    c.check("F3: message names the seal write failure + rollback claim",
            "could not be written" in out
            and "the install record was rolled back to its previous bytes" in out,
            out[:500])
    c.check("F3: rollback lines present (replaced files restored, created removed)",
            "install aborted mid-write" in out and "rolled back" in out,
            out[:600])
    m2, s2 = sha_file(c.game / MANIFEST), sha_file(c.game / SEAL)
    c.note(f"post-failure manifest sha256: {m2}\npost-failure seal sha256:     {s2}")
    c.check("F3: manifest SHA-256 identical to pre-update (byte-exact rollback)",
            m2 == m1, f"pre={str(m1)[:16]} post={str(m2)[:16]}")
    c.check("F3: previous seal untouched (SHA-256 identical)",
            s2 == s1, f"pre={str(s1)[:16]} post={str(s2)[:16]}")
    c.check("F3: game dir byte-identical to the pre-update A1 state",
            sha_tree(c.game) == pre_tree)
    c.note(f"post-failure game dir (sha256 len name):\n{sha_tree(c.game)}")
    c.check("F3: no staging/backup residue",
            stage_residue(c.game) == [], str(stage_residue(c.game)))
    rc, out, err = c.verify()
    c.check("F3: verify right after failure: old pair intact, seal OK, exit 0",
            rc == 0 and "seal: OK" in out, f"rc={rc} out={out[:400]}")
    return c


def case_F4(fx) -> Case:
    """F4 失败后目录不处于拒绝卸载死锁态: rebuild F3's failure, then verify
    and uninstall must both succeed immediately, and the full lifecycle
    (re-install, verify, uninstall) must keep working."""
    c = Case("F4")
    make_golden(c.game)
    golden_tree = sha_tree(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("F4: setup install A1 exit 0", rc == 0, err)
    rc, out = run_seal_driver(c, fx["A2"], "@seal")
    c.check("F4: injected update exit 1 (F3 state rebuilt)", rc == 1, out[:300])
    rc, out, err = c.verify()
    c.check("F4: verify exit 0 (NOT in a refused state; seal OK)",
            rc == 0 and "seal: OK" in out, f"rc={rc} out={out[:400]}")
    rc, out, err = c.uninstall()
    c.check("F4: uninstall exit 0 (NOT refused; record consumable)", rc == 0,
            f"rc={rc} out={out[:400]}")
    c.check("F4: uninstall did NOT report a seal refusal",
            "uninstall refused" not in out, out[:400])
    c.check("F4: game dir back to golden after the uninstall",
            sha_tree(c.game) == golden_tree)
    rc, out, err = c.install(fx["A1"])
    c.check("F4: re-install A1 exit 0 after the failure+uninstall cycle",
            rc == 0, err)
    rc, out, err = c.verify()
    c.check("F4: verify exit 0 after re-install", rc == 0, f"rc={rc}")
    rc, out, err = c.uninstall()
    c.check("F4: uninstall exit 0 after re-install", rc == 0, f"rc={rc}")
    c.check("F4: game dir golden again", sha_tree(c.game) == golden_tree)
    return c


def case_F5(fx) -> Case:
    """F5 恢复路径 (docstring's own recipe): 're-run the install of the SAME
    package (it rewrites the record and a fresh seal), then uninstall' -
    exercised on top of a form (b) seal-write failure (the seal existed and
    was left untouched)."""
    c = Case("F5")
    make_golden(c.game)
    golden_tree = sha_tree(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("F5: setup install A1 exit 0", rc == 0, err)
    m1, s1 = sha_file(c.game / MANIFEST), sha_file(c.game / SEAL)
    rc, out = run_seal_driver(c, fx["A2"], "@seal_half")
    c.check("F5: injected update (form b) exit 1", rc == 1, out[:300])
    c.check("F5: record rolled back byte-exact, old seal untouched",
            sha_file(c.game / MANIFEST) == m1
            and sha_file(c.game / SEAL) == s1)
    rc, out, err = c.verify()
    c.check("F5: verify exit 0 on the surviving old pair", rc == 0,
            f"rc={rc} out={out[:300]}")
    rc, out, err = c.uninstall()
    c.check("F5: uninstall exit 0 (recipe step: remove the old record first)",
            rc == 0, f"rc={rc} out={out[:300]}")
    c.check("F5: game dir back to golden before the recovery install",
            sha_tree(c.game) == golden_tree)
    rc, out, err = c.install(fx["A1"])
    c.check("F5: recovery install of the SAME package A1 exit 0", rc == 0, err)
    c.check("F5: fresh seal written (recipe: rewrites the record + fresh seal)",
            "written    " + SEAL in out and (c.game / SEAL).is_file(),
            out[:400])
    m3, s3 = sha_file(c.game / MANIFEST), sha_file(c.game / SEAL)
    c.note(f"recovery: re-installed manifest sha256: {m3}\n"
           f"recovery: re-installed seal sha256:     {s3} "
           f"(covers the standing record: {seal_covers(c.game)})")
    c.check("F5: record + seal rewritten as a consistent pair (the fresh seal "
            "protects the standing record - byte-difference is not the "
            "criterion, sealed_at carries seconds precision)",
            m3 is not None and s3 is not None and seal_covers(c.game))
    rc, out, err = c.verify()
    c.check("F5: verify exit 0 with the fresh seal", rc == 0 and "seal: OK" in out,
            f"rc={rc} out={out[:300]}")
    rc, out, err = c.uninstall()
    c.check("F5: uninstall exit 0 with the fresh seal (recipe completes)",
            rc == 0, f"rc={rc} out={out[:300]}")
    c.check("F5: game dir golden - recovery path closed",
            sha_tree(c.game) == golden_tree)
    return c


def case_F6(fx) -> Case:
    """F6 形态 (a) 纯文件系统, ZERO code injection: a DIRECTORY occupies the
    seal slot; the plain CLI install must fail at the production landing-slot
    gate and roll the record back. The planted directory is a TEST SETUP
    artefact (present before install) - disclosed, not install residue."""
    c = Case("F6")
    make_golden(c.game)
    (c.game / SEAL).mkdir()          # the obstacle, planted BEFORE install
    pre_tree = sha_tree(c.game)      # sha_tree lists files only
    rc, out, err = c.install(fx["A1"])
    combined = out + err   # the CLI prints errors on stderr
    c.check("F6: plain CLI install exit 1 (real OS gate, no injection)",
            rc == 1, f"rc={rc} out={combined[:400]}")
    c.check("F6: failure raised by the production landing-slot identity gate",
            "exists but is not a regular file" in combined
            and "refusing to use it" in combined, combined[:500])
    c.check("F6: seal-write failure message + rollback claim",
            "could not be written" in combined
            and "the install record was rolled back to its previous bytes" in combined,
            combined[:500])
    c.check("F6: manifest ABSENT after failure", not (c.game / MANIFEST).exists())
    c.check("F6: package files rolled back (BATTLEMD98.INI not left standing)",
            not (c.game / "BATTLEMD98.INI").exists())
    c.check("F6: no staging/backup residue",
            stage_residue(c.game) == [], str(stage_residue(c.game)))
    c.check("F6: the ONLY extra object is the pre-planted directory (setup "
            "artefact, not install residue)",
            sorted(p.name for p in c.game.iterdir() if p.is_dir()) == [SEAL]
            and sha_tree(c.game) == pre_tree)
    listing = "\n".join(f"<DIR>  {p.name}" if p.is_dir()
                        else f"{hashlib.sha256(p.read_bytes()).hexdigest()} {p.stat().st_size:8d}  {p.name}"
                        for p in sorted(c.game.iterdir()))
    c.note(f"post-failure game dir full listing (dirs incl.; the planted "
           f"directory is the test-setup obstacle):\n{listing}")
    rc, out, err = c.verify()
    c.check("F6: verify exit 0 immediately after failure", rc == 0,
            f"rc={rc} out={out[:300]}")
    rc, out, err = c.uninstall()
    c.check("F6: uninstall exit 0 immediately after failure", rc == 0,
            f"rc={rc} out={out[:300]}")
    return c


def case_F7(fx) -> Case:
    """F7 形态 (c) 纯文件系统, ZERO code injection: the existing seal is
    READ-ONLY; the plain CLI update fails at os.replace (WinError 5).
    W25 ADAPTATION (documented, none-weakening): W24's F7 then pinned the
    DEFECT this card fixes - "uninstall exits 1 on the read-only seal after
    the record was removed, actions report lost". Under v8 (UNSEAL-FIX01)
    the same scenario must instead COMPLETE with the full report, an
    explicit warning naming the stray seal and the recovery, exit 10
    (partial completion), and the stray seal's bytes untouched - strictly
    stronger criteria than the old crash pin. The install-side part of F7
    (the update rollback) and the second-uninstall/recovery part are
    unchanged."""
    c = Case("F7")
    make_golden(c.game)
    golden_tree = sha_tree(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("F7: setup install A1 exit 0", rc == 0, err)
    m1, s1 = sha_file(c.game / MANIFEST), sha_file(c.game / SEAL)
    pre_tree = sha_tree(c.game)
    c.note(f"pre-update manifest sha256: {m1}\npre-update seal sha256:     {s1}\n"
           f"pre-update game dir (sha256 len name):\n{pre_tree}")
    set_read_only(c.game / SEAL)
    rc, out, err = c.install(fx["A2"])
    combined = out + err   # the CLI prints errors on stderr
    c.check("F7: plain CLI update exit 1 (read-only seal, no injection)",
            rc == 1, f"rc={rc} out={combined[:400]}")
    c.check("F7: failure is the REAL os.replace error (WinError 5)",
            "[WinError 5]" in combined, combined[:500])
    c.check("F7: seal-write failure message + rollback claim",
            "could not be written" in combined
            and "the install record was rolled back to its previous bytes" in combined,
            combined[:500])
    c.check("F7: manifest SHA-256 identical to pre-update (byte-exact rollback)",
            sha_file(c.game / MANIFEST) == m1)
    c.check("F7: previous seal untouched (SHA-256 identical, still read-only)",
            sha_file(c.game / SEAL) == s1)
    c.check("F7: game dir byte-identical to the pre-update state",
            sha_tree(c.game) == pre_tree)
    c.note(f"post-failed-update manifest sha256: {sha_file(c.game / MANIFEST)}\n"
           f"post-failed-update seal sha256:     {sha_file(c.game / SEAL)}\n"
           f"post-failed-update game dir (sha256 len name):\n{sha_tree(c.game)}")
    c.check("F7: no staging/backup residue",
            stage_residue(c.game) == [], str(stage_residue(c.game)))
    rc, out, err = c.verify()
    c.check("F7: verify exit 0 - the surviving old pair is immediately usable",
            rc == 0 and "seal: OK" in out, f"rc={rc} out={out[:400]}")
    # ---- W25-adapted section: the uninstall on the read-only seal ----
    rc, out, err = c.uninstall()
    combined = out + err
    c.check("F7 (W25): uninstall exit 10 = partial completion - the main "
            "lifecycle completed and the report SURVIVED (v0.7 exited 1 and "
            "lost it)", rc == 10, f"rc={rc} out={combined[:400]}")
    c.check("F7 (W25): status line names completed_with_warnings + exit 10",
            "status: completed_with_warnings (exit code 10)" in out, out[:400])
    c.check("F7 (W25/W26): actions intact - every recorded A1 entry removed "
            "and the record deleted (A2 failed and rolled back cleanly, so A1 "
            "entries have action='created' and no .bak)",
            "removed    " + MANIFEST in out
            and "removed    BATTLEMD98.INI" in out
            and "removed    Y.MAP" in out
            and "removed    X.MAP" in out
            and "removed    expandmd98.mix" in out, out[:800])
    c.check("F7 (W25): the cleanup failure is an explicit warning carrying the "
            "REAL OS error (WinError 5) at the seal slot - never swallowed "
            "silently",
            "could not be removed" in combined and "[WinError 5]" in combined
            and SEAL in combined, combined[:600])
    c.check("F7 (W25): the warning says the uninstall itself is COMPLETE and "
            "names the stray seal location + the recovery",
            "the uninstall itself is COMPLETE" in combined
            and "left standing at" in combined
            and "delete it by hand" in combined
            and "re-run the install of the SAME package" in combined,
            combined[:600])
    c.check("F7 (W25): the seal was NOT removed by the failed cleanup - stray "
            "read-only seal with the ORIGINAL bytes",
            not (c.game / MANIFEST).exists()
            and sha_file(c.game / SEAL) == s1
            and is_read_only(c.game / SEAL))
    # expected terminal tree: golden files + the stray seal (order-independent
    # line-set equality; every line carries sha256 + size + name)
    seal_line = f"{s1} {(c.game / SEAL).stat().st_size:8d} {SEAL}"
    got_lines = sorted(sha_tree(c.game).splitlines())
    want_lines = sorted(golden_tree.splitlines() + [seal_line])
    c.check("F7 (W25): package files were already restored/removed (only golden + "
            "stray seal remain)",
            not (c.game / "BATTLEMD98.INI").exists() and got_lines == want_lines,
            sha_tree(c.game))
    c.note(f"after the completed-with-warnings uninstall (record removed, stray "
           f"read-only seal), game dir (sha256 len name):\n{sha_tree(c.game)}")
    # ---- unchanged W24 section: the state is disclosed, not deadlocked ----
    rc, out, err = c.uninstall()
    c.check("F7: second uninstall exit 0 - state is disclosed, not deadlocked",
            rc == 0, f"rc={rc} out={out[:300]}")
    c.check("F7: second uninstall warns 'nothing recorded to remove' + stray "
            "seal disclosed and left in place",
            "nothing recorded to remove" in out
            and "present without an install record" in out, out[:400])
    # recovery: clear the filesystem obstacle, then the F5 recipe
    clear_read_only(c.game / SEAL)
    rc, out, err = c.install(fx["A1"])
    c.check("F7: recovery: after clearing the obstacle, re-install of the "
            "SAME package exit 0", rc == 0, err)
    c.check("F7: fresh seal re-stamped (protects the standing record)",
            "written    " + SEAL in out and seal_covers(c.game),
            out[:400])
    rc, out, err = c.verify()
    c.check("F7: verify exit 0 with the re-stamped seal",
            rc == 0 and "seal: OK" in out, f"rc={rc} out={out[:300]}")
    rc, out, err = c.uninstall()
    c.check("F7: uninstall exit 0 - recovery path closed", rc == 0, f"rc={rc}")
    c.check("F7: game dir back to golden", sha_tree(c.game) == golden_tree)
    # ---- W26 sub-checks: (a) backed-up .bak restore + read-only seal, and
    #      (b) read-only manifest unlink failure preserving full actions ----
    fbak = c.dir / "bak_seal_ro"
    make_golden(fbak)
    user_x = "user original X.MAP before A1\n"
    w(fbak / "X.MAP", user_x)
    rc, out, err = c.run_module(
        V9_ROOT, ["install", "--package", str(fx["A1"]),
                  "--game", str(fbak), "--allow-content-conflict"], "v9")
    c.check("F7-bak-ro-seal: install A1 with backed-up X.MAP exit 0",
            rc == 0, err)
    set_read_only(fbak / SEAL)
    rc, out, err = c.run_module(
        V9_ROOT, ["uninstall", "--game", str(fbak)], "v9")
    c.check("F7-bak-ro-seal: uninstall exit 10 with restored .bak + deleted "
            "record intact in actions",
            rc == 10
            and "status: completed_with_warnings (exit code 10)" in out
            and "restored   X.MAP.ra2forge.bak -> X.MAP" in out
            and "removed    BATTLEMD98.INI" in out
            and "removed    Y.MAP" in out
            and "removed    expandmd98.mix" in out
            and "removed    " + MANIFEST in out
            and (fbak / "X.MAP").read_bytes() == user_x.encode("utf-8"),
            out[:800])
    clear_read_only(fbak / SEAL)

    fman = c.dir / "manifest_ro"
    make_golden(fman)
    w(fman / "X.MAP", user_x)
    rc, out, err = c.run_module(
        V9_ROOT, ["install", "--package", str(fx["A1"]),
                  "--game", str(fman), "--allow-content-conflict"], "v9")
    c.check("F7-manifest-ro: install A1 with backed-up X.MAP exit 0",
            rc == 0, err)
    s_pre = sha_file(fman / SEAL)
    set_read_only(fman / MANIFEST)
    rc_j, out_j, err_j = c.run_module(
        V9_ROOT, ["uninstall", "--game", str(fman), "--json"], "v9")
    jm = json.loads(out_j)
    act_text = "\n".join(jm["actions"])
    c.check("F7-manifest-ro: read-only manifest unlink exits 1, status='failed', "
            "and STILL preserves every completed file action in actions",
            rc_j == 1 and jm["exit_code"] == 1 and jm["status"] == "failed"
            and "removed    expandmd98.mix" in act_text
            and "removed    Y.MAP" in act_text
            and "restored   X.MAP.ra2forge.bak -> X.MAP" in act_text
            and "removed    BATTLEMD98.INI" in act_text
            and ("removed    " + MANIFEST) not in act_text
            and ("removed    " + SEAL) not in act_text
            and (fman / MANIFEST).is_file()
            and sha_file(fman / SEAL) == s_pre
            and (fman / "X.MAP").read_bytes() == user_x.encode("utf-8")
            and any("[WinError 5]" in wmsg and MANIFEST in wmsg
                    for wmsg in jm["warnings"]),
            json.dumps(jm)[:900])
    clear_read_only(fman / MANIFEST)
    return c


# ---------------------------------------------------------------------------
# U-series (NEW in W25: the uninstall seal-cleanup fault tolerance, card T3)
# ---------------------------------------------------------------------------

def case_U1(fx) -> Case:
    """U1 (card T3): seal READ-ONLY at uninstall time - the exact W24 F7
    defect scenario, now on v8. Assert: the main flow completes (every
    recorded file processed, record deleted), the actions report survives,
    the failure is an explicit warning (real OS error + stray location +
    recovery), and the exit code is the partial-completion code 10."""
    c = Case("U1")
    make_golden(c.game)
    golden_tree = sha_tree(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("U1: setup install A1 exit 0", rc == 0, err)
    s1 = sha_file(c.game / SEAL)
    set_read_only(c.game / SEAL)
    rc, out, err = c.uninstall()
    combined = out + err
    c.check("U1: uninstall exit 10 = partial completion (not 0, not 1)",
            rc == 10, f"rc={rc} out={combined[:300]}")
    c.check("U1: explicit status line: completed_with_warnings (exit code 10)",
            "status: completed_with_warnings (exit code 10)" in out, out[:400])
    c.check("U1: actions report COMPLETE - every recorded file + the record "
            "removed (the main flow did not stop)",
            all(f"removed    {n}" in out for n in
                ("BATTLEMD98.INI", "X.MAP", "Y.MAP", "expandmd98.mix",
                 MANIFEST)), out[:800])
    c.check("U1: explicit warning carries the REAL OS error ([WinError 5]) "
            "and names the seal",
            "could not be removed" in combined and "[WinError 5]" in combined
            and SEAL in combined, combined[:600])
    c.check("U1: warning states the uninstall is COMPLETE and names the stray "
            "seal's standing location",
            "the uninstall itself is COMPLETE" in combined
            and "left standing at" in combined, combined[:600])
    c.check("U1: warning gives BOTH recovery routes (clear obstacle + delete "
            "by hand / re-install the SAME package and uninstall again)",
            "delete it by hand" in combined
            and "re-run the install of the SAME package" in combined,
            combined[:600])
    c.check("U1: seal NOT removed - stray READ-ONLY seal keeps its ORIGINAL "
            "bytes (the residue is disclosed, not consumed)",
            sha_file(c.game / SEAL) == s1 and is_read_only(c.game / SEAL))
    seal_line = f"{s1} {(c.game / SEAL).stat().st_size:8d} {SEAL}"
    c.check("U1: terminal state == golden + stray seal (record gone, package "
            "files restored)",
            not (c.game / MANIFEST).is_file()
            and sorted(sha_tree(c.game).splitlines())
            == sorted(golden_tree.splitlines() + [seal_line]),
            sha_tree(c.game))
    c.note(f"terminal game dir (sha256 len name):\n{sha_tree(c.game)}")
    return c


def case_U2(fx) -> Case:
    """U2 (card T3, CONTROL): normal uninstall on a writable seal - the seal
    IS removed, there are NO warnings, exit 0. Proves the fix does not touch
    the normal path."""
    c = Case("U2")
    make_golden(c.game)
    golden_tree = sha_tree(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("U2: setup install A1 exit 0", rc == 0, err)
    rc, out, err = c.uninstall()
    combined = out + err
    c.check("U2: exit 0", rc == 0, f"rc={rc} out={combined[:300]}")
    c.check("U2: NO warning lines on the normal path", "warning:" not in combined,
            combined[:500])
    c.check("U2: the seal IS removed with the record",
            "removed    " + SEAL in out
            and not (c.game / SEAL).exists()
            and not (c.game / MANIFEST).exists(), out[:500])
    c.check("U2: status line: completed (exit code 0)",
            "status: completed (exit code 0)" in out, out[:400])
    c.check("U2: game dir byte-identical to golden (normal path unchanged)",
            sha_tree(c.game) == golden_tree)
    return c


def case_U3(fx) -> Case:
    """U3 (card T3): run uninstall AGAIN on U1's residual state (record gone,
    stray read-only seal). Must explicitly report 'no record' + disclose the
    stray seal, not crash, not silently consume the seal."""
    c = Case("U3")
    golden_tree, s1 = build_u1_state(c, fx["A1"])
    c.check("U3: the stray read-only seal survived the first uninstall",
            sha_file(c.game / SEAL) == s1 and is_read_only(c.game / SEAL))
    rc, out, err = c.uninstall()
    combined = out + err
    c.check("U3: second uninstall exit 0 - no crash", rc == 0,
            f"rc={rc} out={combined[:300]}")
    c.check("U3: explicitly reports there is no record to remove",
            "nothing recorded to remove" in combined, combined[:400])
    c.check("U3: the stray seal is explicitly disclosed and left in place",
            "present without an install record" in combined
            and "left in place" in combined, combined[:400])
    c.check("U3: the stray seal is STILL there, bytes untouched (never "
            "silently consumed)",
            sha_file(c.game / SEAL) == s1, f"seal sha={sha_file(c.game / SEAL)}")
    c.check("U3: status line: completed (exit code 0)",
            "status: completed (exit code 0)" in out, out[:400])
    return c


def case_U4(fx) -> Case:
    """U4 (card T3): verify on U1's residual state (no record, stray seal).
    Must report the state honestly - the stray seal is NAMED - never a false
    all-ok; exit stays 0 (same policy as orphans: listed, do not change the
    code), in text AND --json."""
    c = Case("U4")
    golden_tree, s1 = build_u1_state(c, fx["A1"])
    rc, out, err = c.verify()
    c.check("U4: verify exit 0 (no record - nothing to check; the disclosure "
            "is a note, like orphans it does not change the code)", rc == 0,
            f"rc={rc} out={out[:300]}")
    c.check("U4: NOT a false all-ok: the stray seal is explicitly named",
            SEAL in out and "present without an install record" in out,
            out[:500])
    rc, outj, err = c.verify(["--json"])
    j = json.loads(outj)
    c.check("U4: --json carries the SAME disclosure in warnings",
            any(SEAL in wmsg and "present without an install record" in wmsg
                for wmsg in j["warnings"]), json.dumps(j["warnings"]))
    c.check("U4: --json exit_code 0 + manifest_present false (same semantics "
            "as the text report)",
            j["exit_code"] == 0 and j["manifest_present"] is False,
            json.dumps({k: j[k] for k in ("exit_code", "manifest_present")}))
    return c


def case_U5(fx) -> Case:
    """U5 (card T3): the recovery path out of U1's residual state - clear the
    obstacle, re-install the SAME package (re-stamps record + seal), verify,
    uninstall -> back to golden."""
    c = Case("U5")
    golden_tree, s1 = build_u1_state(c, fx["A1"])
    clear_read_only(c.game / SEAL)
    rc, out, err = c.install(fx["A1"])
    c.check("U5: obstacle cleared - re-install of the SAME package exit 0",
            rc == 0, err)
    c.check("U5: fresh seal written and protects the standing record",
            "written    " + SEAL in out and seal_covers(c.game), out[:400])
    rc, out, err = c.verify()
    c.check("U5: verify exit 0 with the re-stamped seal",
            rc == 0 and "seal: OK" in out, f"rc={rc} out={out[:300]}")
    rc, out, err = c.uninstall()
    c.check("U5: uninstall exit 0 (recovery closed)", rc == 0,
            f"rc={rc} out={out[:300]}")
    c.check("U5: game dir back to golden byte-for-byte",
            sha_tree(c.game) == golden_tree)
    return c


def case_U6(fx) -> Case:
    """U6 (card T3): uninstall --json carries the SAME three-state semantics
    as the text report - completed (exit 0) / completed_with_warnings
    (exit 10) / failed (exit 7 on the seal gate) - checked per state against
    a text-mode run of the identical scenario."""
    c = Case("U6")
    # --- (a) completed ---
    ga_t, ga_j = c.dir / "a_text", c.dir / "a_json"
    for g in (ga_t, ga_j):
        make_golden(g)
        rc, out, err = c.run_module(V8_ROOT,
                                    ["install", "--package", str(fx["A1"]),
                                     "--game", str(g)], "v8")
        c.check(f"U6a: setup install into {g.name} exit 0", rc == 0, err)
    rc_t, out_t, err_t = c.run_module(V8_ROOT,
                                      ["uninstall", "--game", str(ga_t)], "v8")
    rc_j, out_j, err_j = c.uninstall_json() if False else c.run_module(
        V8_ROOT, ["uninstall", "--game", str(ga_j), "--json"], "v8")
    ja = json.loads(out_j)
    c.check("U6a: text exit 0", rc_t == 0, f"rc={rc_t} out={out_t[:200]}")
    c.check("U6a: json process exit 0 and exit_code field 0 (identical)",
            rc_j == 0 and ja["exit_code"] == 0,
            f"rc={rc_j} json={json.dumps(ja)[:200]}")
    c.check("U6a: json status 'completed'", ja["status"] == "completed",
            str(ja.get("status")))
    c.check("U6a: text shows no warning; json warnings empty (same semantics)",
            "warning:" not in (out_t + err_t) and ja["warnings"] == [],
            f"text={(out_t + err_t)[:200]} json={json.dumps(ja['warnings'])}")
    c.check("U6a: the seal removal appears in BOTH reports (same actions)",
            "removed    " + SEAL in out_t
            and any("removed    " + SEAL in a for a in ja["actions"]),
            json.dumps(ja["actions"]))
    c.check("U6a: json exit_code_meaning matches the documented table",
            ja["exit_code_meaning"].startswith("completed"),
            ja["exit_code_meaning"])
    # --- (b) completed_with_warnings ---
    gb_t, gb_j = c.dir / "b_text", c.dir / "b_json"
    for g in (gb_t, gb_j):
        make_golden(g)
        rc, out, err = c.run_module(V8_ROOT,
                                    ["install", "--package", str(fx["A1"]),
                                     "--game", str(g)], "v8")
        c.check(f"U6b: setup install into {g.name} exit 0", rc == 0, err)
        set_read_only(g / SEAL)
    rc_t, out_t, err_t = c.run_module(V8_ROOT,
                                      ["uninstall", "--game", str(gb_t)], "v8")
    rc_j, out_j, err_j = c.run_module(
        V8_ROOT, ["uninstall", "--game", str(gb_j), "--json"], "v8")
    jb = json.loads(out_j)
    c.check("U6b: text exit 10 (partial completion)", rc_t == 10,
            f"rc={rc_t} out={out_t[:200]}")
    c.check("U6b: json process exit 10 and exit_code field 10 (identical)",
            rc_j == 10 and jb["exit_code"] == 10,
            f"rc={rc_j} json={json.dumps(jb)[:200]}")
    c.check("U6b: json status 'completed_with_warnings'",
            jb["status"] == "completed_with_warnings", str(jb.get("status")))
    c.check("U6b: json warnings name the stray seal + the real OS error (the "
            "same warning the text prints)",
            any("[WinError 5]" in wmsg and SEAL in wmsg
                and "could not be removed" in wmsg for wmsg in jb["warnings"])
            and "warning:" in (out_t + err_t),
            json.dumps(jb["warnings"])[:300])
    c.check("U6b: json actions complete - record removed, seal NOT removed "
            "(same facts as the text report)",
            any("removed    " + MANIFEST in a for a in jb["actions"])
            and not any("removed    " + SEAL in a for a in jb["actions"])
            and "removed    " + MANIFEST in out_t
            and "removed    " + SEAL not in out_t,
            json.dumps(jb["actions"]))
    c.check("U6b: json refused is null (this is NOT a refusal - it is a "
            "partial completion)", jb["refused"] is None, str(jb.get("refused")))
    # --- (c) failed (seal-gate refusal) ---
    gc_t, gc_j = c.dir / "c_text", c.dir / "c_json"
    for g in (gc_t, gc_j):
        make_golden(g)
        rc, out, err = c.run_module(V8_ROOT,
                                    ["install", "--package", str(fx["A1"]),
                                     "--game", str(g)], "v8")
        c.check(f"U6c: setup install into {g.name} exit 0", rc == 0, err)
        (g / SEAL).unlink()
    rc_t, out_t, err_t = c.run_module(V8_ROOT,
                                      ["uninstall", "--game", str(gc_t)], "v8")
    rc_j, out_j, err_j = c.run_module(
        V8_ROOT, ["uninstall", "--game", str(gc_j), "--json"], "v8")
    jc = json.loads(out_j)
    c.check("U6c: text exit 7 (seal-gate refusal)", rc_t == 7,
            f"rc={rc_t} out={out_t[:200]}")
    c.check("U6c: json process exit 7 and exit_code field 7 (identical)",
            rc_j == 7 and jc["exit_code"] == 7,
            f"rc={rc_j} json={json.dumps(jc)[:200]}")
    c.check("U6c: json status 'failed' + refused='seal_missing'",
            jc["status"] == "failed" and jc["refused"] == "seal_missing",
            json.dumps({k: jc[k] for k in ("status", "refused")}))
    c.check("U6c: json actions empty - NOTHING was removed (same as text's "
            "'nothing was removed or restored')",
            jc["actions"] == [] and "uninstall REFUSED" in (out_t + err_t),
            json.dumps(jc["actions"]))
    c.check("U6c: json warnings carry the refusal explanation (text prints "
            "the same lines)", len(jc["warnings"]) > 0
            and "REFUSED" in " ".join(jc["warnings"]),
            json.dumps(jc["warnings"])[:300])
    return c


# ---------------------------------------------------------------------------
# R-series (NEW in W25: T2 double-fault injection at the record-rollback
# `except OSError: pass`, W24 UNCOVERED §2)
# ---------------------------------------------------------------------------

def case_R0(fx) -> Case:
    """R0: the rollback driver injects NOTHING without an explicit mode
    (usage refusal before ra2forge is even imported; game dir untouched);
    a plain install afterwards works normally."""
    c = Case("R0")
    make_golden(c.game)
    golden_tree = sha_tree(c.game)
    rc, out = run_rollback_driver(c, fx["A1"], "@no_such_mode")
    c.check("R0: rollback driver without a valid mode exits 3 (no injection)",
            rc == 3, f"rc={rc} out={out[:200]}")
    c.check("R0: game dir still golden after the refused driver run",
            sha_tree(c.game) == golden_tree)
    rc, out, err = c.install(fx["A1"])
    c.check("R0: plain install after the refused driver run exit 0", rc == 0,
            err)
    c.check("R0: manifest + seal written (the driver left nothing behind)",
            (c.game / MANIFEST).is_file() and (c.game / SEAL).is_file())
    return c


def case_R1(fx) -> Case:
    """R1 (card T2, form 1 - the W24 UNCOVERED §2 path): UPDATE over an
    existing seal-era pair. The seal is read-only (pure FS, the test's own
    obstruction) AND the driver flips the freshly written manifest read-only
    in the window between the record write and the seal write -> the seal
    write fails with a REAL WinError 5 AND the byte-exact record restore
    fails with a REAL WinError 5 inside the production
    `except OSError: pass`. Measured: what state is left, is it recoverable.
    """
    c = Case("R1")
    make_golden(c.game)
    golden_tree = sha_tree(c.game)
    rc, out, err = c.install(fx["A1"])
    c.check("R1: setup install A1 exit 0", rc == 0, err)
    m1, s1 = sha_file(c.game / MANIFEST), sha_file(c.game / SEAL)
    pre_tree = sha_tree(c.game)
    c.note(f"pre-update manifest sha256: {m1}\npre-update seal sha256:     {s1}\n"
           f"pre-update game dir (sha256 len name):\n{pre_tree}")
    set_read_only(c.game / SEAL)      # pure FS: the seal obstruction
    rc, out = run_rollback_driver(c, fx["A2"], "@rollback_write")
    c.check("R1: injected update exit 1", rc == 1, f"rc={rc} out={out[:300]}")
    c.check("R1: the seal write failed with the REAL os.replace error "
            "(WinError 5, not a synthetic raise)",
            "[WinError 5]" in out and SEAL in out, out[:500])
    c.check("R1: record-rollback failure is explicitly reported (never swallowed) "
            "with real WinError 5, and package rollback ran cleanly",
            "install record rollback FAILED" in out
            and ("could not restore " + MANIFEST) in out
            and "[WinError 5]" in out
            and "package files rolled back cleanly" in out
            and "the install record was rolled back" not in out
            and "nothing was left in the unsealed state" not in out
            and "the package files are UNCHANGED" not in out,
            out[:700])
    m2, s2 = sha_file(c.game / MANIFEST), sha_file(c.game / SEAL)
    c.note(f"post-double-fault manifest sha256: {m2}\n"
           f"post-double-fault seal sha256:     {s2}")
    c.check("R1: the NEW record STANDS - the manifest is NOT the previous "
            "bytes (the restore write failed and was swallowed)",
            m2 is not None and m2 != m1,
            f"pre={str(m1)[:12]} post={str(m2)[:12]}")
    c.check("R1: the fresh manifest was locked read-only by the in-window act "
            "(its own undo is what failed)",
            is_read_only(c.game / MANIFEST))
    c.check("R1: the OLD seal is untouched (SHA-256 identical) - the pair on "
            "disk is BROKEN (stale seal + new record)",
            s2 == s1, f"pre={str(s1)[:12]} post={str(s2)[:12]}")
    c.check("R1: the PACKAGE files were rolled back to the pre-update A1 "
            "bytes (everything except the standing record/seal pair)",
            tree_lines_without(sha_tree(c.game), MANIFEST, SEAL)
            == tree_lines_without(pre_tree, MANIFEST, SEAL),
            sha_tree(c.game))
    c.check("R1: no staging/backup residue",
            stage_residue(c.game) == [], str(stage_residue(c.game)))
    c.note(f"post-double-fault game dir (sha256 len name):\n{sha_tree(c.game)}")
    # what the broken state does to the tool
    rc, out, err = c.verify()
    c.check("R1: verify exit 8 - the standing record is seal-era and the old "
            "seal no longer matches it (MISMATCH, not MISSING: the old seal "
            "still stands)", rc == 8 and "MISMATCH" in out,
            f"rc={rc} out={out[:400]}")
    rc, out, err = c.uninstall()
    c.check("R1: uninstall REFUSED exit 8 (the broken pair is a refused "
            "state; nothing removed)", rc == 8, f"rc={rc} out={out[:200]}")
    rc, out, err = c.install(fx["A1"])
    c.check("R1: reinstall A1 refused exit 1 - the standing record describes "
            "A2 bytes while the disk holds rolled-back A1 bytes (strict "
            "risks)", rc == 1, f"rc={rc} err={err[:300]}")
    rc, out, err = c.install(fx["A2"])
    c.check("R1: reinstall A2 refused too (the same wall - the record lies "
            "about the disk)", rc == 1, f"rc={rc} err={err[:300]}")
    c.note("T2 verdict (form 1): with the rollback write dead, the install "
           "leaves 'new record standing + stale old seal' - the refused "
           "state SEAL-CHAIN01 promises never to leave - while the error "
           "message claims the record was rolled back. NOT recoverable "
           "through the tool (uninstall refused by the seal gate; install "
           "refused by strict risks): the record and seal must be deleted "
           "by hand. Recovery below is manual surgery, documented.")
    # recovery = manual surgery: clear the read-only attributes, delete the
    # broken record + seal by hand, install fresh
    clear_read_only(c.game / MANIFEST)
    clear_read_only(c.game / SEAL)
    (c.game / MANIFEST).unlink()
    (c.game / SEAL).unlink()
    rc, out, err = c.install(fx["A1"])
    c.check("R1: recovery (manual record+seal removal) - fresh install exit 0",
            rc == 0, err)
    rc, out, err = c.verify()
    c.check("R1: recovery - verify exit 0 with seal OK",
            rc == 0 and "seal: OK" in out, f"rc={rc} out={out[:300]}")
    rc, out, err = c.uninstall()
    c.check("R1: recovery - uninstall exit 0", rc == 0, f"rc={rc}")
    c.check("R1: recovery - game dir back to golden",
            sha_tree(c.game) == golden_tree)
    return c


def case_R2(fx) -> Case:
    """R2 (card T2, form 2): FRESH install. A DIRECTORY occupies the seal
    slot (pure FS) so the seal write fails at the PRODUCTION landing-slot
    gate, and the driver flips the fresh manifest read-only in-window -> the
    rollback unlink() of the fresh record fails with a REAL WinError 5
    inside `except OSError: pass`. Measured: what state is left, is it
    recoverable."""
    c = Case("R2")
    make_golden(c.game)
    golden_tree = sha_tree(c.game)
    (c.game / SEAL).mkdir()           # the seal-slot obstacle (test setup)
    rc, out = run_rollback_driver(c, fx["A1"], "@rollback_unlink")
    c.check("R2: injected fresh install exit 1", rc == 1,
            f"rc={rc} out={out[:300]}")
    c.check("R2: the seal write was refused by the PRODUCTION landing-slot "
            "gate (a real gate, not a synthetic raise)",
            "exists but is not a regular file" in out
            and "refusing to use it" in out, out[:500])
    c.check("R2: record-rollback failure is explicitly reported (never swallowed) "
            "with real WinError 5, and package rollback ran cleanly",
            "install record rollback FAILED" in out
            and ("could not remove " + MANIFEST) in out
            and "[WinError 5]" in out
            and "package files rolled back cleanly" in out
            and "the install record was rolled back" not in out
            and "nothing was left in the unsealed state" not in out
            and "the package files are UNCHANGED" not in out,
            out[:700])
    m2 = sha_file(c.game / MANIFEST)
    c.check("R2: the FRESH record STANDS (the rollback unlink failed and was "
            "swallowed)", m2 is not None, f"manifest sha={str(m2)[:16]}")
    c.check("R2: the standing record is read-only (its own undo is what "
            "failed)", is_read_only(c.game / MANIFEST))
    c.check("R2: package files rolled back (created files removed) - the "
            "tree is exactly golden + the standing record",
            tree_lines_without(sha_tree(c.game), MANIFEST) == golden_tree,
            sha_tree(c.game))
    c.check("R2: no staging/backup residue",
            stage_residue(c.game) == [], str(stage_residue(c.game)))
    c.note(f"post-double-fault game dir (sha256 len name):\n{sha_tree(c.game)}")
    rc, out, err = c.verify()
    c.check("R2: verify exit 8 (seal slot ALIASED by the planted directory; "
            "the record's files are also MISSING on disk - drift is listed "
            "too, 8 wins by severity) - never a false ok",
            rc == 8 and "ALIASED" in out and "MISSING" in out,
            f"rc={rc} out={out[:400]}")
    rc, out, err = c.uninstall()
    c.check("R2: uninstall REFUSED exit 8", rc == 8, f"rc={rc} out={out[:200]}")
    c.note("T2 verdict (form 2): the fresh record stands read-only while its "
           "files are gone and the seal slot is occupied. The lie "
           "'recorded but absent' IS healable by a reinstall (the plan "
           "recreates missing files); the seal-slot obstacle must be "
           "removed first. Recovery below.")
    # recovery: remove the seal-slot obstacle, clear the read-only attribute,
    # reinstall (the record describes absent files -> they are recreated)
    (c.game / SEAL).rmdir()
    clear_read_only(c.game / MANIFEST)
    rc, out, err = c.install(fx["A1"])
    c.check("R2: recovery - reinstall A1 exit 0 (recorded-but-absent files "
            "are recreated)", rc == 0, err)
    rc, out, err = c.verify()
    c.check("R2: recovery - verify exit 0 with seal OK",
            rc == 0 and "seal: OK" in out, f"rc={rc} out={out[:300]}")
    rc, out, err = c.uninstall()
    c.check("R2: recovery - uninstall exit 0", rc == 0, f"rc={rc}")
    c.check("R2: recovery - game dir back to golden",
            sha_tree(c.game) == golden_tree)
    # ---- W26 sub-check: compound rollback fault (record rollback fails AND
    #      X.MAP rollback fails, while remaining files still roll back) ----
    comp = c.dir / "compound"
    make_golden(comp)
    (comp / SEAL).mkdir()
    rc, out = run_compound_rollback_driver(c, fx["A1"], comp, "@compound_unlink")
    c.check("R2-compound: exit 1 and BOTH record-rollback and file-rollback "
            "failures reported in the same error without stopping remaining files",
            rc == 1
            and "install record rollback FAILED" in out
            and ("could not remove " + MANIFEST) in out
            and "package file rollback had failures" in out
            and "rollback of X.MAP failed" in out
            and "[WinError 5]" in out
            and "rolled back BATTLEMD98.INI (created file removed)" in out
            and "rolled back Y.MAP (created file removed)" in out
            and "rolled back expandmd98.mix (created file removed)" in out
            and not (comp / "BATTLEMD98.INI").is_file()
            and not (comp / "Y.MAP").is_file()
            and not (comp / "expandmd98.mix").is_file()
            and (comp / "X.MAP").is_file()
            and (comp / MANIFEST).is_file()
            and tree_lines_without(sha_tree(comp), MANIFEST, "X.MAP") == golden_tree,
            out[:900])
    clear_read_only(comp / MANIFEST)
    clear_read_only(comp / "X.MAP")
    return c


# ---------------------------------------------------------------------------
# W30 CSF capability cases (CSF1..CSF6, mapping to T4 C1..C6)
# ---------------------------------------------------------------------------

def case_CSF1(_fx) -> Case:
    """C1 自建最小 CSF 往返（写→读） + 未知值类型保留与如实报告."""
    c = Case("CSF1")
    csf_file = c.dir / "minimal.csf"
    code = f"""
import json, struct
from pathlib import Path
from ra2forge import csf

p = Path({str(csf_file)!r})
doc = csf.create_csf([
    ("LBL:ONE", "First English string"),
    ("LBL:TWO", "中文繁體測試字串：紅警2"),
    ("LBL:THREE", "Special chars: !@#$%^&*()_+"),
], language=9)
csf.write_csf(p, doc)
r1 = csf.read_csf(p, strict=True)
assert r1.num_labels == 3 and r1.num_strings == 3
assert r1.get("LBL:ONE") == "First English string"
assert r1.get("LBL:TWO") == "中文繁體測試字串：紅警2"
assert r1.get("LBL:THREE") == "Special chars: !@#$%^&*()_+"

res = csf.append_or_set_label(p, "LBL:FOUR", "Appended 4th entry")
r2 = csf.read_csf(p, strict=True)
assert r2.num_labels == 4 and r2.num_strings == 4
assert r2.get("LBL:ONE") == "First English string"
assert r2.get("LBL:TWO") == "中文繁體測試字串：紅警2"
assert r2.get("LBL:THREE") == "Special chars: !@#$%^&*()_+"
assert r2.get("LBL:FOUR") == "Appended 4th entry"

# Unknown value type check (XFOO)
unk_payload = b"XFOO\\x04\\x00\\x00\\x00raw!"
raw_unk = (
    struct.pack("<4sIIIII", b" FSC", 3, 2, 2, 0, 9)
    + struct.pack("<4sII", b" LBL", 1, 5) + b"KNOWN"
    + csf.CsfValue(csf.STR_MAGIC, "ok").to_bytes()
    + struct.pack("<4sII", b" LBL", 1, 3) + b"UNK"
    + unk_payload
)
parsed_unk = csf.parse_csf(raw_unk, strict=False)
strict_err = None
try:
    csf.parse_csf(raw_unk, strict=True)
except csf.CsfError as exc:
    strict_err = str(exc)

print(json.dumps({{
    "labels": r2.num_labels,
    "strings": r2.num_strings,
    "lang": r2.language,
    "append_action": res["action"],
    "unk_warnings": parsed_unk.warnings,
    "unk_raw_preserved": parsed_unk.unknown_records[0]["raw_bytes"] == unk_payload,
    "strict_err": strict_err,
}}, ensure_ascii=False))
"""
    rc, out, err = c.run_python(V10_ROOT, code, "v10-csf1")
    c.check("CSF1: minimal CSF roundtrip exit 0", rc == 0, err)
    if rc == 0:
        data = json.loads(out.strip())
        c.check("CSF1: num_labels=4 and num_strings=4 after append",
                data["labels"] == 4 and data["strings"] == 4, str(data))
        c.check("CSF1: unknown value type honestly reported and raw bytes preserved",
                bool(data["unk_warnings"]) and "XFOO" in data["unk_warnings"][0]
                and data["unk_raw_preserved"] and data["strict_err"] is not None,
                str(data))
    return c


def case_CSF2(_fx) -> Case:
    """C2 对真实官方 CSF 追加一条后读回：新标签可读、原标签数与抽样文本不变."""
    c = Case("CSF2")
    mix_path = REPO_ROOT / "ra2youli" / "langmd.mix"
    mod_csf = c.dir / "ra2md_modified.csf"
    code = f"""
import json
from pathlib import Path
from ra2forge.mixlib import MixFile
from ra2forge import csf

with MixFile({str(mix_path)!r}) as mf:
    raw = mf.get("ra2md.csf")
assert raw is not None, "failed to extract ra2md.csf from langmd.mix"
orig = csf.parse_csf(raw, strict=True)
assert orig.to_bytes() == raw, "parsed official ra2md.csf did not re-encode byte-for-byte"

mod_path = Path({str(mod_csf)!r})
mod_path.write_bytes(raw)
new_label = "RA2F:TEST0001"
new_text = "測試戰役簡介 — Official CSF Append Roundtrip"
res = csf.append_or_set_label(mod_path, new_label, new_text)
after = csf.read_csf(mod_path, strict=True)

# Verify ALL original labels are unchanged byte-for-byte
orig_map = {{lbl.name: [(v.kind, v.text, v.extra) for v in lbl.values] for lbl in orig.labels}}
after_map = {{lbl.name: [(v.kind, v.text, v.extra) for v in lbl.values] for lbl in after.labels}}
all_orig_intact = all(after_map.get(k) == v for k, v in orig_map.items())

print(json.dumps({{
    "orig_labels": orig.num_labels,
    "orig_strings": orig.num_strings,
    "after_labels": after.num_labels,
    "after_strings": after.num_strings,
    "desc_all1": after.get("DESC:ALL1"),
    "desc_sov1": after.get("DESC:SOV1"),
    "vox_ceva001": [after.get("VOX:ceva001"), after.get_label("VOX:ceva001").values[0].extra],
    "new_text_match": after.get(new_label) == new_text,
    "all_orig_intact": all_orig_intact,
    "action": res["action"],
}}, ensure_ascii=False))
"""
    rc, out, err = c.run_python(V10_ROOT, code, "v10-csf2")
    c.check("CSF2: official ra2md.csf extract + append + roundtrip exit 0", rc == 0, err)
    if rc == 0:
        data = json.loads(out.strip())
        c.check("CSF2: official CSF has >= 100 labels and DESC:ALL1 readable",
                data["orig_labels"] >= 100 and bool(data["desc_all1"]), str(data))
        c.check("CSF2: label/string counts incremented by exactly 1",
                data["after_labels"] == data["orig_labels"] + 1
                and data["after_strings"] == data["orig_strings"] + 1, str(data))
        c.check("CSF2: new label readable and ALL 5211 original labels/WRTS intact",
                data["new_text_match"] and data["all_orig_intact"], str(data))
    return c


def case_CSF3(_fx) -> Case:
    """C3 标签名冲突（重复 append 同一标签）：更新而非重复追加，计数不翻倍."""
    c = Case("CSF3")
    csf_file = c.dir / "conflict.csf"
    code = f"""
import json
from pathlib import Path
from ra2forge import csf

p = Path({str(csf_file)!r})
csf.write_csf(p, csf.create_csf({{"BASE:A": "Base A", "BASE:B": "Base B"}}, language=9))
r1 = csf.append_or_set_label(p, "RA2F:CONFLICT", "First Version Text")
r2 = csf.append_or_set_label(p, "RA2F:CONFLICT", "Second Updated Text")
final = csf.read_csf(p, strict=True)
names = [lbl.name for lbl in final.labels]
print(json.dumps({{
    "r1_action": r1["action"],
    "r2_action": r2["action"],
    "num_labels": final.num_labels,
    "num_strings": final.num_strings,
    "conflict_count": names.count("RA2F:CONFLICT"),
    "text": final.get("RA2F:CONFLICT"),
    "base_a": final.get("BASE:A"),
    "base_b": final.get("BASE:B"),
}}, ensure_ascii=False))
"""
    rc, out, err = c.run_python(V10_ROOT, code, "v10-csf3")
    c.check("CSF3: duplicate label update exit 0", rc == 0, err)
    if rc == 0:
        data = json.loads(out.strip())
        c.check("CSF3: first append, second update, count stays 3 (not doubled)",
                data["r1_action"] == "appended"
                and data["r2_action"] == "updated"
                and data["num_labels"] == 3
                and data["num_strings"] == 3
                and data["conflict_count"] == 1, str(data))
        c.check("CSF3: updated text and preserved base labels match",
                data["text"] == "Second Updated Text"
                and data["base_a"] == "Base A"
                and data["base_b"] == "Base B", str(data))
    return c


def case_CSF4(_fx) -> Case:
    """C4 空文本 / 超长文本（4000+ 字符）：不崩溃，往返一致."""
    c = Case("CSF4")
    csf_file = c.dir / "edge_lengths.csf"
    code = f"""
import json
from pathlib import Path
from ra2forge import csf

p = Path({str(csf_file)!r})
csf.write_csf(p, csf.create_csf({{"INIT:0": "init"}}, language=9))
long_txt = "長文開頭-" + ("A" * 4000) + "-長文結尾"
csf.append_or_set_label(p, "RA2F:EMPTY", "")
csf.append_or_set_label(p, "RA2F:LONG", long_txt)
got = csf.read_csf(p, strict=True)
print(json.dumps({{
    "num_labels": got.num_labels,
    "num_strings": got.num_strings,
    "empty_eq": got.get("RA2F:EMPTY") == "",
    "long_eq": got.get("RA2F:LONG") == long_txt,
    "long_len": len(got.get("RA2F:LONG") or ""),
    "init_eq": got.get("INIT:0") == "init",
}}, ensure_ascii=False))
"""
    rc, out, err = c.run_python(V10_ROOT, code, "v10-csf4")
    c.check("CSF4: empty and 4000+ char text roundtrip exit 0", rc == 0, err)
    if rc == 0:
        data = json.loads(out.strip())
        c.check("CSF4: empty text, 4010-char text, and counts all exact",
                data["empty_eq"] and data["long_eq"] and data["long_len"] == 4010
                and data["init_eq"] and data["num_labels"] == 3
                and data["num_strings"] == 3, str(data))
    return c


def case_CSF5(_fx) -> Case:
    """C5 畸形 CSF（截断/魔数错）：明确报错，不崩溃、不写坏原文件."""
    c = Case("CSF5")
    bad_magic = c.dir / "bad_magic.csf"
    trunc_csf = c.dir / "truncated.csf"
    short_hdr = c.dir / "short_hdr.csf"
    design_p = c.dir / "design.json"
    design_p.write_text(json.dumps({
        "campaign": {"name": "BadCsfTest", "description": "Test desc", "side": "soviet"},
        "missions": [{"name": "M01", "title": "M01", "briefing": "B"}],
    }, indent=2), encoding="utf-8")

    code = f"""
import hashlib, json
from pathlib import Path
from ra2forge import csf

valid = csf.create_csf({{"A": "alpha", "B": "beta"}}, language=0).to_bytes()
bad_p = Path({str(bad_magic)!r})
bad_p.write_bytes(b"BAD!" + valid[4:])
bad_sha = hashlib.sha256(bad_p.read_bytes()).hexdigest()

trunc_p = Path({str(trunc_csf)!r})
trunc_p.write_bytes(valid[:len(valid) // 2])
trunc_sha = hashlib.sha256(trunc_p.read_bytes()).hexdigest()

hdr_p = Path({str(short_hdr)!r})
hdr_p.write_bytes(b" FSC\\x03\\x00")
hdr_sha = hashlib.sha256(hdr_p.read_bytes()).hexdigest()

errs = {{}}
for key, path in (("bad_magic", bad_p), ("truncated", trunc_p), ("short_hdr", hdr_p)):
    try:
        csf.append_or_set_label(path, "RA2F:NEW", "should fail")
    except csf.CsfError as exc:
        errs[key] = str(exc)

print(json.dumps({{
    "errs": errs,
    "bad_unchanged": hashlib.sha256(bad_p.read_bytes()).hexdigest() == bad_sha,
    "trunc_unchanged": hashlib.sha256(trunc_p.read_bytes()).hexdigest() == trunc_sha,
    "hdr_unchanged": hashlib.sha256(hdr_p.read_bytes()).hexdigest() == hdr_sha,
}}))
"""
    rc, out, err = c.run_python(V10_ROOT, code, "v10-csf5-api")
    c.check("CSF5: API malformed CSF probe exit 0", rc == 0, err)
    if rc == 0:
        data = json.loads(out.strip())
        c.check("CSF5: bad magic / truncated / short header all raise CsfError",
                set(data["errs"].keys()) == {"bad_magic", "truncated", "short_hdr"}
                and all(bool(v) for v in data["errs"].values()), str(data))
        c.check("CSF5: original malformed files untouched byte-for-byte",
                data["bad_unchanged"] and data["trunc_unchanged"]
                and data["hdr_unchanged"], str(data))

    bad_sha_before = hashlib.sha256(bad_magic.read_bytes()).hexdigest()
    rc_cli, out_cli, err_cli = c.run_module(
        V10_ROOT,
        ["build", "--design", str(design_p), "--out", str(c.dir / "cli_out"),
         "--csf-out", str(bad_magic)],
        "v10-csf5-cli",
    )
    c.check("CSF5: CLI build against corrupt --csf-out exits 1 with explicit error",
            rc_cli == 1 and ("bad CSF magic" in (out_cli + err_cli)
                             or "CSF emission failed" in (out_cli + err_cli)),
            f"rc={rc_cli} err={err_cli[:300]}")
    c.check("CSF5: CLI failure leaves corrupt file untouched",
            hashlib.sha256(bad_magic.read_bytes()).hexdigest() == bad_sha_before)
    return c


def case_CSF6(_fx) -> Case:
    """C6 不传 --csf-out 时构建与 v9 逐字节相同（向后兼容硬证据）+ 传 --csf-out 接线验证."""
    c = Case("CSF6")
    design_p = c.dir / "demo_design.json"
    design = {
        "package": {"id": "org.ra2forge.csf-compat-test", "version": "1.0.0"},
        "campaign": {
            "name": "CompatOps",
            "description": "Backward compatibility and CSF label wiring test.",
            "side": "soviet",
            "id": "RA2F1",
        },
        "missions": [
            {
                "name": "CMP01",
                "title": "Mission One",
                "briefing": "Hold the line.",
                "theater": "TEMPERATE",
                "size": [60, 60],
                "player": {"house": "Russians"},
                "structures": [
                    {"owner": "Russians", "type": "NACNST", "row": 40, "col": 30},
                    {"owner": "Americans", "type": "GACNST", "row": 15, "col": 30, "tag": "hq"},
                ],
                "objectives": [{"type": "destroy_building", "structure_tag": "hq"}],
            },
        ],
    }
    design_p.write_text(json.dumps(design, indent=2, ensure_ascii=False), encoding="utf-8")

    out_v9 = c.dir / "out_v9"
    out_v10 = c.dir / "out_v10"
    rc9, o9, e9 = c.run_module(
        V9_REF_ROOT, ["build", "--design", str(design_p), "--out", str(out_v9)], "v9-ref-build"
    )
    rc10, o10, e10 = c.run_module(
        V10_ROOT, ["build", "--design", str(design_p), "--out", str(out_v10)], "v10-default-build"
    )
    c.check("CSF6a: v9 and v10 builds without --csf-out both exit 0",
            rc9 == 0 and rc10 == 0, f"rc9={rc9} rc10={rc10} e9={e9} e10={e10}")
    t9 = sha_tree(out_v9)
    t10 = sha_tree(out_v10)
    c.note(f"v9 sha_tree:\n{t9}\nv10 sha_tree:\n{t10}")
    c.check("CSF6a: v10 build without --csf-out is BYTE-FOR-BYTE IDENTICAL to v9 across every file",
            t9 == t10, f"v9:\n{t9}\n\nv10:\n{t10}")

    # Part B: --csf-out + --csf-base (extract official ra2md.csf to sandbox first)
    base_csf = c.dir / "base_ra2md.csf"
    target_csf = c.dir / "patched_ra2md.csf"
    out_csf_pkg = c.dir / "out_v10_csf"
    mix_path = REPO_ROOT / "ra2youli" / "langmd.mix"
    extract_code = f"""
from pathlib import Path
from ra2forge.mixlib import MixFile
with MixFile({str(mix_path)!r}) as mf:
    data = mf.get("ra2md.csf")
assert data is not None
Path({str(base_csf)!r}).write_bytes(data)
print("extracted", len(data))
"""
    rc_ex, _, err_ex = c.run_python(V10_ROOT, extract_code, "v10-extract-base")
    c.check("CSF6b: extract base ra2md.csf exit 0", rc_ex == 0, err_ex)

    rc_b, ob, eb = c.run_module(
        V10_ROOT,
        ["build", "--design", str(design_p), "--out", str(out_csf_pkg),
         "--csf-out", str(target_csf), "--csf-base", str(base_csf)],
        "v10-csf-build",
    )
    c.check("CSF6b: build with --csf-out and --csf-base exit 0", rc_b == 0, eb)
    pkg_dir = out_csf_pkg / "CompatOps"
    ini_text = (pkg_dir / "BATTLEMD98.INI").read_text(encoding="gbk")
    report_text = (pkg_dir / "BUILD_REPORT.txt").read_text(encoding="utf-8")
    patch_json = json.loads((pkg_dir / "csf_patch.json").read_text(encoding="utf-8"))
    label = patch_json["label"]
    c.check("CSF6b: BATTLEMD98.INI Description= uses stable RA2F:<hex> label instead of raw text",
            label.startswith("RA2F:") and f"Description={label}" in ini_text
            and "Backward compatibility and CSF label wiring test." not in ini_text,
            ini_text)
    c.check("CSF6b: BUILD_REPORT.txt lists csf_target, csf_label, and csf_text",
            "csf_mode=enabled" in report_text
            and "csf_target=ra2md.csf" in report_text
            and f"csf_label={label}" in report_text
            and "csf_text=Backward compatibility and CSF label wiring test." in report_text,
            report_text)
    c.check("CSF6b: package dir contains ra2md.csf and csf_patch.json",
            (pkg_dir / "ra2md.csf").is_file() and (pkg_dir / "csf_patch.json").is_file())

    verify_code = f"""
import json
from ra2forge import csf
pkg_c = csf.read_csf({str(pkg_dir / "ra2md.csf")!r}, strict=True)
tgt_c = csf.read_csf({str(target_csf)!r}, strict=True)
print(json.dumps({{
    "pkg_labels": pkg_c.num_labels,
    "tgt_labels": tgt_c.num_labels,
    "got_pkg": pkg_c.get({label!r}),
    "got_tgt": tgt_c.get({label!r}),
    "desc_all1": pkg_c.get("DESC:ALL1"),
}}, ensure_ascii=False))
"""
    rc_v, ov, ev = c.run_python(V10_ROOT, verify_code, "v10-csf6-verify")
    c.check("CSF6b: readback of built ra2md.csf exit 0", rc_v == 0, ev)
    if rc_v == 0:
        vd = json.loads(ov.strip())
        c.check("CSF6b: built ra2md.csf has 5212 labels, DESC:ALL1 intact, and new label text exact",
                vd["pkg_labels"] == 5212 and vd["tgt_labels"] == 5212
                and vd["got_pkg"] == design["campaign"]["description"]
                and vd["got_tgt"] == design["campaign"]["description"]
                and bool(vd["desc_all1"]), str(vd))
    return c


# ---------------------------------------------------------------------------
# W34 cases MS1..MS6 (MAPSELMD.INI registration)
# ---------------------------------------------------------------------------

OFFICIAL_MAPSEL_SHA256 = (
    "074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52")
OFFICIAL_MAPSEL_SIZE = 5573


def _ms_design(camp_name: str, mission_names: list[str], *,
               side: str = "soviet",
               package_id: str = "org.ra2forge.w34-ms") -> dict:
    """A complete, valid 1..N-mission design for the W34 cases."""
    return {
        "package": {"id": package_id, "version": "1.0"},
        "campaign": {"name": camp_name, "description": "W34 MAPSELMD regression.",
                     "side": side, "id": "RA2F1"},
        "missions": [
            {
                "name": n, "title": n, "briefing": "W34 test mission.",
                "theater": "TEMPERATE", "size": [60, 60],
                "player": {"house": "Russians"},
                "structures": [
                    {"owner": "Russians", "type": "NACNST",
                     "row": 40, "col": 30},
                    {"owner": "Americans", "type": "GACNST",
                     "row": 15, "col": 30, "tag": "hq"},
                ],
                "objectives": [{"type": "destroy_building",
                                "structure_tag": "hq"}],
            }
            for n in mission_names
        ],
    }


def _ms_build(c: Case, design: dict, tag: str,
              extra: list[str] = ()) -> tuple[int, str, str, Path]:
    """Write design JSON into c.dir, run `build`, return (rc, out, err, pkg)."""
    dp = c.dir / f"design_{tag}.json"
    dp.write_text(json.dumps(design, indent=2, ensure_ascii=False),
                  encoding="utf-8")
    out_dir = c.dir / f"out_{tag}"
    rc, out, err = c.run_module(
        V11_ROOT, ["build", "--design", str(dp), "--out", str(out_dir),
                   *extra], f"v11-build-{tag}")
    pkg = out_dir / design["campaign"]["name"]
    return rc, out, err, pkg


def _ms_facts_code(pkg: Path) -> str:
    """Self-contained python -c body: parse MAPSELMD.INI and the bundled base."""
    return f"""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, {str(V11_ROOT)!r})
from ra2forge import mapselmd as ms
pkg = Path({str(pkg)!r})
gen = (pkg / "MAPSELMD.INI").read_bytes()
official = (V11 := Path({str(V11_ROOT)!r})) / "ra2forge" / "data" / "MAPSELMD.OFFICIAL.INI"
base = official.read_bytes()

def sections(raw):
    out = {{}}
    cur = None
    for line in raw.decode("latin-1").replace("\\r\\n", "\\n").split("\\n"):
        s = line.strip()
        if not s or s.startswith(";"):
            continue
        if s.startswith("[") and s.endswith("]"):
            cur = s[1:-1]
            out.setdefault(cur, {{}})
        elif cur is not None and "=" in s:
            k, _, v = s.partition("=")
            out[cur][k.strip()] = v.strip()
    return out

g = sections(gen)
b = sections(base)
blines = [x for x in base.split(b"\\r\\n") if x]
glines = gen.split(b"\\r\\n")
pos = 0
ordered = True
for line in blines:
    try:
        pos = glines.index(line, pos) + 1
    except ValueError:
        ordered = False
        break
print(json.dumps({{
    "base_size": len(base),
    "base_sha": hashlib.sha256(base).hexdigest(),
    "gen_size": len(gen),
    "gen_sha": hashlib.sha256(gen).hexdigest(),
    "crlf": gen.count(b"\\r\\n"),
    "lone_lf": gen.count(b"\\n") - gen.count(b"\\r\\n"),
    "lone_cr": gen.count(b"\\r") - gen.count(b"\\r\\n"),
    "official_lines_in_order": ordered,
    "official_sections": sorted(b),
    "missing_sections": sorted(set(b) - set(g)),
    "gen_sections": sorted(g),
    "gdi_1_7": [g.get("GDI", {{}}).get(str(i)) for i in range(1, 8)],
    "nod_1_7": [g.get("Nod", {{}}).get(str(i)) for i in range(1, 8)],
    "nod_8_10": [g.get("Nod", {{}}).get(str(i)) for i in range(8, 11)],
    "gdi_8": g.get("GDI", {{}}).get("8"),
    "changed_official_entries": [
        f"[{{sec}}] {{k}}={{b[sec][k]!r}}->{{g.get(sec, {{}}).get(k)!r}}"
        for sec in b for k in b[sec]
        if g.get(sec, {{}}).get(k) != b[sec][k]
    ],
    "appended": {{
        sec: {{"Scenario": g[sec].get("Scenario"),
               "kids": {{k: v for k, v in g[sec].items() if k.isdigit()}}}}
        for sec in g if sec.startswith("RA2F_")
    }},
}}, ensure_ascii=False))
"""


def case_MS1(_fx) -> Case:
    """MS1: --mapselmd emits a COMPLETE byte-exact official clone + stages."""
    c = Case("MS1")
    design = _ms_design("MS1Clone", ["MS01", "MS02", "MS03"])
    rc, _o, err, pkg = _ms_build(c, design, "ms1", ["--mapselmd"])
    c.check("MS1a: build --mapselmd exits 0", rc == 0, err)
    f = pkg / "MAPSELMD.INI"
    c.check("MS1b: package contains MAPSELMD.INI", f.is_file(), str(f))
    if not f.is_file():
        return c
    rc2, ov, ev = c.run_python(V11_ROOT, _ms_facts_code(pkg), "ms1-facts")
    c.check("MS1c: facts script exits 0", rc2 == 0, ev)
    if rc2 != 0:
        return c
    d = json.loads(ov.strip())
    c.note("MS1 facts: " + json.dumps(d, ensure_ascii=False)[:1400])
    c.check("MS1d: bundled base is the byte-exact official file "
            "(5573 B, sha256=074ccccd...)",
            d["base_size"] == OFFICIAL_MAPSEL_SIZE
            and d["base_sha"] == OFFICIAL_MAPSEL_SHA256,
            f"{d['base_size']} {d['base_sha']}")
    c.check("MS1e: generated file is LARGER than the official clone "
            "(not a minimal file)", d["gen_size"] > OFFICIAL_MAPSEL_SIZE,
            f"{d['gen_size']} B")
    c.check("MS1f: every official section survives (zero missing)",
            d["missing_sections"] == [], str(d["missing_sections"]))
    c.check("MS1g: every official line survives verbatim AND in order",
            d["official_lines_in_order"] is True)
    c.check("MS1h: generated file is 100% CRLF (no lone LF / CR)",
            d["lone_lf"] == 0 and d["lone_cr"] == 0 and d["crlf"] > 0,
            str({k: d[k] for k in ("crlf", "lone_lf", "lone_cr")}))
    c.check("MS1i: [Nod] 8/9/10 = 3 appended stages; [GDI] 8 absent "
            "(side=soviet registers to Nod only)",
            all(d["nod_8_10"]) and d["gdi_8"] is None,
            str(d["nod_8_10"]) + f" gdi8={d['gdi_8']}")
    stages = d["appended"]
    c.check("MS1j: 3 appended stage sections, each with Scenario=<MAP>.MAP",
            len(stages) == 3
            and sorted(v["Scenario"] for v in stages.values())
            == ["MS01.MAP", "MS02.MAP", "MS03.MAP"], str(stages))
    kids = [v["kids"] for _k, v in sorted(stages.items())]
    c.check("MS1k: stage 1/2 have a single child link 2=<stage name>, "
            "the LAST stage has NO child (EndOfGame=yes side)",
            len(kids) == 3 and all(len(k) == 1 and "2" in k for k in kids[:2])
            and kids[2] == {}, str(kids))
    return c


def case_MS2(_fx) -> Case:
    """MS2: after appending, ZERO official entries are lost or altered."""
    c = Case("MS2")
    design = _ms_design("MS2ZeroLoss", ["ZA", "ZB"], side="allied")
    rc, _o, err, pkg = _ms_build(c, design, "ms2", ["--mapselmd"])
    c.check("MS2a: build --mapselmd (side=allied) exits 0", rc == 0, err)
    if rc != 0 or not (pkg / "MAPSELMD.INI").is_file():
        return c
    rc2, ov, ev = c.run_python(V11_ROOT, _ms_facts_code(pkg), "ms2-facts")
    c.check("MS2b: facts script exits 0", rc2 == 0, ev)
    if rc2 != 0:
        return c
    d = json.loads(ov.strip())
    c.check("MS2c: all 20 official sections present in the generated file",
            d["missing_sections"] == [] and len(d["official_sections"]) >= 20,
            f"official={len(d['official_sections'])} missing={d['missing_sections']}")
    c.check("MS2d: ZERO official key/value entries changed",
            d["changed_official_entries"] == [],
            str(d["changed_official_entries"][:6]))
    c.check("MS2e: official [GDI] 1..7 = ALL01..ALL07 and [Nod] 1..7 = "
            "Sov01..Sov07 unchanged",
            d["gdi_1_7"] == [f"ALL0{i}" for i in range(1, 8)]
            and d["nod_1_7"] == [f"Sov0{i}" for i in range(1, 8)],
            f"{d['gdi_1_7']} / {d['nod_1_7']}")
    c.check("MS2f: side=allied appended to [GDI] (8/9 present), [Nod] 8 "
            "absent", bool(d["gdi_8"]) and d["nod_8_10"][0] is None,
            f"gdi8={d['gdi_8']} nod8={d['nod_8_10'][0]}")
    return c


def case_MS3(_fx) -> Case:
    """MS3: a minimal / partial MAPSELMD.INI base is REFUSED (hard error)."""
    c = Case("MS3")
    minimal = c.dir / "minimal_mapselmd.ini"
    minimal.write_bytes(
        b"[GDI]\r\n1=OURSTAGE\r\n\r\n[OURSTAGE]\r\nScenario=MS01.MAP\r\n")
    design = _ms_design("MS3Minimal", ["MS01", "MS02"])
    rc, out, err, pkg = _ms_build(c, design, "ms3minimal",
                                  ["--mapselmd", "--mapselmd-base",
                                   str(minimal)])
    c.check("MS3a: build with a minimal --mapselmd-base is REFUSED (exit!=0)",
            rc != 0, f"rc={rc} out={out.strip()[:200]}")
    c.check("MS3b: refusal names the minimal/partial base explicitly",
            "minimal" in (out + err).lower()
            or "missing official" in (out + err).lower()
            or "partial" in (out + err).lower(), (out + err)[:400])
    c.check("MS3c: NO MAPSELMD.INI was emitted on a refused build",
            not (pkg / "MAPSELMD.INI").exists(), str(pkg))
    # direct API-level proof
    api = f"""
import sys
sys.path.insert(0, {str(V11_ROOT)!r})
from ra2forge import mapselmd as ms
from pathlib import Path
raw = Path({str(minimal)!r}).read_bytes()
try:
    ms.validate_official_base(raw)
    print("NOT_REFUSED")
except ms.MapselmdError as exc:
    print("REFUSED", str(exc)[:120])
"""
    rc2, ov, ev = c.run_python(V11_ROOT, api, "ms3-api")
    c.check("MS3d: validate_official_base() raises MapselmdError on a "
            "minimal file", rc2 == 0 and ov.strip().startswith("REFUSED"),
            ov + ev)
    # default build must not emit MAPSELMD.INI at all
    rc3, _o, err3, pkg3 = _ms_build(c, design, "ms3default")
    c.check("MS3e: without --mapselmd no MAPSELMD.INI is generated "
            "(v10 behavior)", rc3 == 0 and not (pkg3 / "MAPSELMD.INI").exists(),
            err3)
    return c


def case_MS4(_fx) -> Case:
    """MS4: v11 WITHOUT the switch == v10 byte-for-byte (SHA-256 table)."""
    c = Case("MS4")
    design = _ms_design("MS4Compat", ["CMP1", "CMP2"])
    dp = c.dir / "design_ms4.json"
    dp.write_text(json.dumps(design, indent=2, ensure_ascii=False),
                  encoding="utf-8")
    o10, o11, o11m = (c.dir / "out_v10", c.dir / "out_v11",
                      c.dir / "out_v11_mapselmd")
    rc10, _o, e10 = c.run_module(
        V10_REF_ROOT, ["build", "--design", str(dp), "--out", str(o10)],
        "v10-ref-build")
    rc11, _o, e11 = c.run_module(
        V11_ROOT, ["build", "--design", str(dp), "--out", str(o11)],
        "v11-default-build")
    rc11m, _o, e11m = c.run_module(
        V11_ROOT, ["build", "--design", str(dp), "--out", str(o11m),
                   "--mapselmd"], "v11-mapselmd-build")
    c.check("MS4a: v10 reference, v11 default and v11 --mapselmd builds "
            "all exit 0", rc10 == 0 and rc11 == 0 and rc11m == 0,
            f"{rc10}/{rc11}/{rc11m} {e10} {e11} {e11m}")
    t10, t11, t11m = sha_tree(o10), sha_tree(o11), sha_tree(o11m)
    c.note("MS4 v10 tree:\n" + t10)
    c.note("MS4 v11 tree:\n" + t11)
    n10, n11 = len(t10.splitlines()), len(t11.splitlines())
    c.check("MS4b: v11 default output is BYTE-FOR-BYTE IDENTICAL to v10 "
            "across every file", t10 == t11 and n10 > 0,
            f"v10={n10} files, v11={n11} files")
    c.check("MS4c: neither default build emits MAPSELMD.INI",
            "MAPSELMD.INI" not in t10 and "MAPSELMD.INI" not in t11)
    set10 = {ln.split(None, 2)[2] for ln in t10.splitlines()}
    set11 = {ln.split(None, 2)[2] for ln in t11.splitlines()}
    set11m = {ln.split(None, 2)[2] for ln in t11m.splitlines()}
    extra = sorted(set11m - set11)
    c.check("MS4d: --mapselmd adds exactly ONE new artifact "
            "(MAPSELMD.INI)", len(extra) == 1
            and extra[0].endswith("MAPSELMD.INI"), str(extra))
    core = [n for n in set11 if n.endswith((".MAP", ".mix", "BATTLEMD98.INI",
                                            "story.md", "ra2forge_package.json"))]
    m11 = {ln.split(None, 2)[2]: ln.split(None, 2)[0]
           for ln in t11.splitlines()}
    m11m = {ln.split(None, 2)[2]: ln.split(None, 2)[0]
            for ln in t11m.splitlines()}
    c.check("MS4e: enabling --mapselmd leaves all pre-existing game "
            "artifacts byte-identical", bool(core)
            and all(m11m.get(n) == m11[n] for n in core), str(core))
    c.check("MS4f: --mapselmd-base without --mapselmd is a CLI usage error",
            c.run_module(V11_ROOT,
                         ["build", "--design", str(dp), "--out",
                          str(c.dir / "out_bad"), "--mapselmd-base",
                          str(c.dir / "x.ini")], "v11-bad-flag")[0] == 2)
    return c


def case_MS5(_fx) -> Case:
    """MS5: MAPSELMD.INI is in the manifest, backed up and restored."""
    c = Case("MS5")
    d1 = _ms_design("MS5P1", ["MS01", "MS02"])
    d2 = _ms_design("MS5P2", ["MS03", "MS04"])
    rc1, _o, e1, p1 = _ms_build(c, d1, "ms5p1", ["--mapselmd"])
    rc2, _o, e2, p2 = _ms_build(c, d2, "ms5p2", ["--mapselmd"])
    c.check("MS5a: both --mapselmd packages build", rc1 == 0 and rc2 == 0,
            e1 + e2)
    m1, m2 = (p1 / "MAPSELMD.INI").read_bytes(), (p2 / "MAPSELMD.INI").read_bytes()
    c.check("MS5b: the two packages have DIFFERENT MAPSELMD.INI bytes "
            "(different appended stages)", m1 != m2)

    make_golden(c.game)
    rc, out, err = c.install(p1)
    c.check("MS5c: install exits 0", rc == 0, out + err)
    c.check("MS5d: MAPSELMD.INI landed in the game dir with the package bytes",
            (c.game / "MAPSELMD.INI").is_file()
            and (c.game / "MAPSELMD.INI").read_bytes() == m1)
    man = c.manifest()
    entries = [e for e in man["files"] if e["name"] == "MAPSELMD.INI"]
    c.check("MS5e: MAPSELMD.INI is recorded in ra2forge_install.json "
            "with the exact sha256", len(entries) == 1
            and entries[0]["sha256"] == hashlib.sha256(m1).hexdigest(),
            str(entries))
    rcv, ov, ev = c.verify()
    c.check("MS5f: verify reports exit 0 with MAPSELMD.INI ok", rcv == 0
            and "MAPSELMD.INI" in ov and "ok" in ov, ov + ev)
    rcu, ou, eu = c.uninstall()
    c.check("MS5g: uninstall exits 0 and REMOVES MAPSELMD.INI "
            "(restores the pre-install state)", rcu == 0
            and not (c.game / "MAPSELMD.INI").exists()
            and "MAPSELMD.INI" in ou, ou + eu)
    c.check("MS5h: no MAPSELMD backup residue after uninstall",
            not (c.game / "MAPSELMD.INI.ra2forge.bak").exists())

    # restore path: install P1, plant the pre-install original in the backup
    # slot, upgrade to P2 (backup="keep"), then uninstall must restore it.
    make_golden(c.game)
    rc, out, err = c.install(p1)
    c.check("MS5i: first install for the restore scenario exits 0", rc == 0,
            out + err)
    original = b"; ORIGINAL USER MAPSELMD.INI (pre-install state)\r\n"
    (c.game / "MAPSELMD.INI.ra2forge.bak").write_bytes(original)
    rc, out, err = c.install(p2)
    c.check("MS5j: upgrading to a package with different MAPSELMD.INI is "
            "allowed (it IS ours, recorded in the manifest)", rc == 0,
            out + err)
    c.check("MS5k: the upgraded MAPSELMD.INI has P2's bytes and the "
            "backup slot is kept", (c.game / "MAPSELMD.INI").read_bytes() == m2
            and (c.game / "MAPSELMD.INI.ra2forge.bak").read_bytes() == original)
    rcu, ou, eu = c.uninstall()
    c.check("MS5l: uninstall RESTORES the exact original MAPSELMD.INI "
            "bytes from the backup", rcu == 0
            and (c.game / "MAPSELMD.INI").is_file()
            and (c.game / "MAPSELMD.INI").read_bytes() == original
            and "restored   MAPSELMD.INI.ra2forge.bak -> MAPSELMD.INI" in ou,
            ou + eu)
    return c


def case_MS6(_fx) -> Case:
    """MS6: a foreign MAPSELMD.INI is a definite preflight conflict."""
    c = Case("MS6")
    design = _ms_design("MS6Conflict", ["MS01", "MS02"])
    rc, _o, err, pkg = _ms_build(c, design, "ms6", ["--mapselmd"])
    c.check("MS6a: --mapselmd package builds", rc == 0, err)
    if rc != 0:
        return c
    mapsel = (pkg / "MAPSELMD.INI").read_bytes()
    foreign = b"; FOREIGN MAPSELMD.INI - another mod\r\n[GDI]\r\n1=ALL01\r\n"

    make_golden(c.game)
    (c.game / "MAPSELMD.INI").write_bytes(foreign)
    before = sha_tree(c.game)
    rc1, out1, err1 = c.install(pkg)
    c.check("MS6b: install over a foreign MAPSELMD.INI is REFUSED by "
            "preflight (default strict)", rc1 == 1, f"rc={rc1} {out1}{err1}")
    c.check("MS6c: refusal is classified as a definite content conflict "
            "and names MAPSELMD.INI", "definite content conflicts" in (out1 + err1)
            and "MAPSELMD.INI" in (out1 + err1), (out1 + err1)[:600])
    c.check("MS6d: refusal says it is NOT releasable by "
            "--allow-content-conflict", "NOT releasable" in (out1 + err1)
            or "never-releasable" in (out1 + err1).lower(),
            (out1 + err1)[:600])
    c.check("MS6e: ZERO bytes written on refusal (whole game dir tree "
            "byte-identical)", before == sha_tree(c.game))
    c.check("MS6f: foreign bytes intact, no manifest, no backup slot",
            (c.game / "MAPSELMD.INI").read_bytes() == foreign
            and not (c.game / "ra2forge_install.json").exists()
            and not (c.game / "MAPSELMD.INI.ra2forge.bak").exists())
    rc2, out2, err2 = c.install(pkg, ["--allow-content-conflict"])
    c.check("MS6g: --allow-content-conflict does NOT release the "
            "MAPSELMD.INI conflict (still refused, still zero writes)",
            rc2 == 1 and before == sha_tree(c.game), f"rc={rc2} {out2}{err2}")

    # byte-identical but unrecorded ("adopt" state) must be refused too
    make_golden(c.game)
    (c.game / "MAPSELMD.INI").write_bytes(mapsel)
    before2 = sha_tree(c.game)
    rc3, out3, err3 = c.install(pkg)
    c.check("MS6h: even a byte-identical but UNRECORDED MAPSELMD.INI is "
            "refused (never silently adopted)", rc3 == 1
            and before2 == sha_tree(c.game), f"rc={rc3} {out3}{err3}")

    # control: with NO foreign MAPSELMD.INI the install proceeds
    make_golden(c.game)
    rc4, out4, err4 = c.install(pkg)
    c.check("MS6i: control - install succeeds when the game dir has no "
            "MAPSELMD.INI", rc4 == 0
            and (c.game / "MAPSELMD.INI").read_bytes() == mapsel,
            f"rc={rc4} {out4}{err4}")
    return c


# ---------------------------------------------------------------------------
# W41 cases CSF_INST1..CSF_INST5 (CSF into install/backup/uninstall + guards)
# ---------------------------------------------------------------------------

def _csfi_design(camp_name: str, mission_names: list[str], *,
                 package_id: str = "org.ra2forge.w41-csf") -> dict:
    """A complete, valid 1..N-mission design with a non-empty description
    (so --csf-out actually emits a CSF label)."""
    d = _ms_design(camp_name, mission_names, package_id=package_id)
    d["campaign"]["description"] = ("W41 CSF install regression campaign "
                                    "description.")
    return d


def _csfi_pkg_csf_facts_code(pkg: Path) -> str:
    """Self-contained python -c: parse the package ra2md.csf and assert the
    complete official baseline survives + our label is present."""
    return f"""
import json, sys
from pathlib import Path
sys.path.insert(0, {str(V12_ROOT)!r})
from ra2forge import csf
pkg = Path({str(pkg)!r})
raw = (pkg / "ra2md.csf").read_bytes()
doc = csf.parse_csf(raw, strict=True)
rep = csf.assert_complete_csf(doc)
names = {{l.name.upper() for l in doc.labels}}
missing = csf.official_baseline_labels() - names
print(json.dumps({{
    "size": len(raw),
    "version": doc.version,
    "language": doc.language,
    "num_labels": doc.num_labels,
    "num_strings": doc.num_strings,
    "baseline_labels": rep["baseline_labels"],
    "missing_official": len(missing),
    "extra_labels": rep["extra_labels"],
    "desc_all1": doc.get("DESC:ALL1") is not None,
    "mapselect": doc.get("MSG:UnableMapSelect"),
    "reencode_identical": doc.to_bytes() == raw,
}}, ensure_ascii=False))
"""


def case_CSF_INST1(_fx) -> Case:
    """CSF_INST1: completeness guard - a COMPLETE official clone passes, a
    minimal/partial CSF is refused (API + build + require_complete writes)."""
    c = Case("CSF_INST1")
    # (1a) API guard: official passes; minimal/partial refused; guarded writer
    # refuses a minimal CSF with ZERO bytes written.
    api = c.dir / "api_guard"
    api.mkdir(parents=True, exist_ok=True)
    code = f"""
import json, os
from pathlib import Path
from ra2forge import csf
d = Path({str(api)!r})
rep_official = csf.assert_complete_csf(csf.load_official_csf())
baseline = csf.official_baseline_labels()
minimal = csf.create_csf({{"RA2F:ONLY": "x"}}, language=9).to_bytes()
partial = csf.create_csf(
    {{"MSG:UnableMapSelect": "x", "DESC:ALL1": "y"}}, language=9).to_bytes()
err_min = err_part = None
for key, payload in (("minimal", minimal), ("partial", partial)):
    try:
        csf.assert_complete_csf(payload)
    except csf.CsfIncompleteError as exc:
        if key == "minimal": err_min = str(exc)
        else: err_part = str(exc)
p = d / "must_not_exist.csf"
guard_write_refused = False
try:
    csf.write_csf(p, csf.create_csf({{"A": "a"}}), require_complete=True)
except csf.CsfIncompleteError:
    guard_write_refused = True
print(json.dumps({{
    "official_version": rep_official["version"],
    "official_labels": rep_official["num_labels"],
    "baseline_labels": len(baseline),
    "minimal_refused": err_min is not None and "PARTIAL" in err_min,
    "partial_refused": err_part is not None and "PARTIAL" in err_part,
    "guard_write_refused": guard_write_refused,
    "guard_write_zero_bytes": not p.exists(),
}}, ensure_ascii=False))
"""
    rc, out, err = c.run_python(V12_ROOT, code, "v12-csf-inst1-api")
    c.check("CSF_INST1a: API completeness guard exit 0", rc == 0, err)
    if rc == 0:
        d = json.loads(out.strip())
        c.check("CSF_INST1b: official clone passes (v3, 5211 labels, "
                "5211-label baseline)", d["official_version"] == 3
                and d["official_labels"] == 5211
                and d["baseline_labels"] == 5211, str(d))
        c.check("CSF_INST1c: minimal AND partial CSF both refused as PARTIAL",
                d["minimal_refused"] and d["partial_refused"], str(d))
        c.check("CSF_INST1d: write_csf(require_complete=True) refuses a "
                "minimal CSF with ZERO bytes written",
                d["guard_write_refused"] and d["guard_write_zero_bytes"],
                str(d))

    # (1b) BUILD: --csf-out with NO base and a MISSING target -> complete
    # official clone (bundled byte-exact resource) + our label, guard passes.
    design = _csfi_design("INST1Clone", ["IN01"])
    target = c.dir / "csf_out_complete.csf"
    rc_b, _o, e_b, pkg = _ms_build(c, design, "inst1_clone",
                                   ["--csf-out", str(target)])
    c.check("CSF_INST1e: build --csf-out (no base, missing target) exits 0",
            rc_b == 0, e_b)
    if rc_b == 0:
        c.check("CSF_INST1f: package contains ra2md.csf + csf_patch.json",
                (pkg / "ra2md.csf").is_file()
                and (pkg / "csf_patch.json").is_file())
        facts_code = _csfi_pkg_csf_facts_code(pkg)
        rc_f, of, ef = c.run_python(V12_ROOT, facts_code, "v12-csf-inst1-facts")
        c.check("CSF_INST1g: complete-clone facts script exits 0", rc_f == 0, ef)
        if rc_f == 0:
            fd = json.loads(of.strip())
            c.note("INST1 complete clone facts: " + json.dumps(fd, ensure_ascii=False))
            c.check("CSF_INST1h: cloned ra2md.csf is a COMPLETE legal CSF "
                    "(v3, 5212 labels, 0 missing official, +1 extra, "
                    "byte-exact re-encode)", fd["version"] == 3
                    and fd["num_labels"] == 5212
                    and fd["num_strings"] == 5212
                    and fd["baseline_labels"] == 5211
                    and fd["missing_official"] == 0
                    and fd["extra_labels"] == 1
                    and fd["desc_all1"]
                    and fd["reencode_identical"], str(fd))
        pj = json.loads((pkg / "csf_patch.json").read_text(encoding="utf-8"))
        c.check("CSF_INST1i: csf_patch.json records complete_baseline_labels=5211",
                pj.get("complete_baseline_labels") == 5211, str(pj))

    # (1c) BUILD: --csf-out pointing at an EXISTING minimal/partial CSF is
    # REFUSED and the file is left untouched (no silent create_if_missing).
    minimal_path = c.dir / "preexisting_minimal.csf"
    mk_min = f"""
from pathlib import Path
from ra2forge import csf
csf.write_csf(Path({str(minimal_path)!r}),
              csf.create_csf({{"A": "alpha"}}, language=0))
print("wrote minimal", Path({str(minimal_path)!r}).stat().st_size)
"""
    rc_mk, _om, em = c.run_python(V12_ROOT, mk_min, "v12-csf-inst1-mk-minimal")
    c.check("CSF_INST1j-pre: minimal CSF fixture written", rc_mk == 0
            and minimal_path.is_file(), em)
    min_sha_before = hashlib.sha256(minimal_path.read_bytes()).hexdigest()
    design2 = _csfi_design("INST1Partial", ["IN02"])
    dp2 = c.dir / "design_inst1partial.json"
    dp2.write_text(json.dumps(design2, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    rc_p, op, ep = c.run_module(
        V12_ROOT,
        ["build", "--design", str(dp2), "--out", str(c.dir / "out_inst1partial"),
         "--csf-out", str(minimal_path)],
        "v12-csf-inst1-partial")[0:3]
    c.check("CSF_INST1j: build against a partial --csf-out is REFUSED (exit 1)",
            rc_p == 1 and ("PARTIAL" in (op + ep)
                           or "CSF emission failed" in (op + ep)),
            f"rc={rc_p} out={op[:200]} err={ep[:200]}")
    c.check("CSF_INST1k: refused build leaves the partial file untouched",
            hashlib.sha256(minimal_path.read_bytes()).hexdigest()
            == min_sha_before)

    # (1d) BUILD: --csf-base pointing at a partial CSF is REFUSED, zero writes.
    partial_base = c.dir / "partial_base.csf"
    partial_base.write_bytes(minimal_path.read_bytes())
    tgt = c.dir / "from_partial_base.csf"
    dp3 = c.dir / "design_inst1base.json"
    dp3.write_text(json.dumps(_csfi_design("INST1Base", ["IN03"]), indent=2,
                             ensure_ascii=False), encoding="utf-8")
    rc_bb, ob, eb = c.run_module(
        V12_ROOT,
        ["build", "--design", str(dp3), "--out", str(c.dir / "out_inst1base"),
         "--csf-out", str(tgt), "--csf-base", str(partial_base)],
        "v12-csf-inst1-partial-base")[0:3]
    c.check("CSF_INST1l: build with a partial --csf-base is REFUSED and no "
            "target CSF is created", rc_bb == 1 and not tgt.exists(),
            f"rc={rc_bb} {ob[:150]}{eb[:150]}")
    return c


def case_CSF_INST2(_fx) -> Case:
    """CSF_INST2: install -> verify -> uninstall -> BYTE-EXACT restore.
    The official game dir has NO loose ra2md.csf, so install is CREATE and
    uninstall must DELETE (W21 original_absent trap)."""
    c = Case("CSF_INST2")
    design = _csfi_design("INST2Lifecycle", ["LC01", "LC02"])
    target = c.dir / "csf_out_lifecycle.csf"
    rc_b, _o, e_b, pkg = _ms_build(c, design, "inst2_lifecycle",
                                   ["--csf-out", str(target)])
    c.check("CSF_INST2a: --csf-out package builds", rc_b == 0, e_b)
    if rc_b != 0:
        return c
    pkg_csf = (pkg / "ra2md.csf").read_bytes()
    pkg_csf_sha = hashlib.sha256(pkg_csf).hexdigest()

    make_golden(c.game)
    # golden game dir must NOT contain a loose ra2md.csf (CREATE case)
    c.check("CSF_INST2b: pre-install game dir has NO loose ra2md.csf",
            not (c.game / "ra2md.csf").exists())
    before = sha_tree(c.game)

    rc_i, oi, ei = c.install(pkg)
    c.check("CSF_INST2c: install exits 0", rc_i == 0, oi + ei)
    c.check("CSF_INST2d: ra2md.csf landed with the package bytes",
            (c.game / "ra2md.csf").is_file()
            and (c.game / "ra2md.csf").read_bytes() == pkg_csf)
    man = c.manifest()
    entries = [e for e in man["files"] if e["name"] == "ra2md.csf"]
    c.check("CSF_INST2e: ra2md.csf recorded in ra2forge_install.json with "
            "exact sha256 and action=created", len(entries) == 1
            and entries[0]["sha256"] == pkg_csf_sha
            and entries[0].get("action") == "created", str(entries))
    c.check("CSF_INST2f: no backup slot was created for the CREATE case",
            not (c.game / "ra2md.csf.ra2forge.bak").exists())

    rcv, ov, ev = c.verify()
    c.check("CSF_INST2g: verify reports exit 0 with ra2md.csf ok",
            rcv == 0 and "ra2md.csf" in ov and "ok" in ov, ov + ev)

    rc_u, ou, eu = c.uninstall()
    after = sha_tree(c.game)
    c.check("CSF_INST2h: uninstall exits 0 and REMOVES ra2md.csf",
            rc_u == 0 and not (c.game / "ra2md.csf").exists()
            and "ra2md.csf" in ou, ou + eu)
    c.check("CSF_INST2i: game dir is BYTE-FOR-BYTE IDENTICAL to the "
            "pre-install state (no loose csf, no manifest/seal/backup residue)",
            after == before, f"before:\n{before}\n\nafter:\n{after}")
    c.note("INST2 sha_tree before install:\n" + before)
    c.note("INST2 sha_tree after uninstall:\n" + after)
    return c


def case_CSF_INST3(_fx) -> Case:
    """CSF_INST3: a foreign loose ra2md.csf is a definite preflight conflict
    that refuses by default (and stays refused with --allow-content-conflict),
    with ZERO bytes written."""
    c = Case("CSF_INST3")
    design = _csfi_design("INST3Conflict", ["CF01"])
    target = c.dir / "csf_out_conflict.csf"
    rc_b, _o, e_b, pkg = _ms_build(c, design, "inst3_conflict",
                                   ["--csf-out", str(target)])
    c.check("CSF_INST3a: --csf-out package builds", rc_b == 0, e_b)
    if rc_b != 0:
        return c
    pkg_csf = (pkg / "ra2md.csf").read_bytes()
    foreign = b"FOREIGN ra2md.csf - placed by another mod / by hand\r\n"

    make_golden(c.game)
    (c.game / "ra2md.csf").write_bytes(foreign)
    before = sha_tree(c.game)
    rc1, out1, err1 = c.install(pkg)
    c.check("CSF_INST3b: install over a foreign ra2md.csf is REFUSED "
            "(default strict)", rc1 == 1, f"rc={rc1} {out1}{err1}")
    c.check("CSF_INST3c: refusal is a definite content conflict and names "
            "ra2md.csf", "definite content conflicts" in (out1 + err1)
            and "ra2md.csf" in (out1 + err1), (out1 + err1)[:700])
    c.check("CSF_INST3d: refusal says it is NOT releasable by "
            "--allow-content-conflict", "NOT releasable" in (out1 + err1)
            or "NEVER-releasable" in (out1 + err1), (out1 + err1)[:700])
    c.check("CSF_INST3e: ZERO bytes written on refusal (whole game dir "
            "byte-identical)", before == sha_tree(c.game))
    c.check("CSF_INST3f: foreign bytes intact, no manifest, no backup slot",
            (c.game / "ra2md.csf").read_bytes() == foreign
            and not (c.game / "ra2forge_install.json").exists()
            and not (c.game / "ra2md.csf.ra2forge.bak").exists())

    rc2, out2, err2 = c.install(pkg, ["--allow-content-conflict"])
    c.check("CSF_INST3g: --allow-content-conflict does NOT release the "
            "ra2md.csf conflict (still refused, still zero writes)",
            rc2 == 1 and before == sha_tree(c.game),
            f"rc={rc2} {out2}{err2}")

    # byte-identical but unrecorded ("adopt" state) must be refused too
    make_golden(c.game)
    (c.game / "ra2md.csf").write_bytes(pkg_csf)
    before2 = sha_tree(c.game)
    rc3, out3, err3 = c.install(pkg)
    c.check("CSF_INST3h: even a byte-identical but UNRECORDED ra2md.csf is "
            "refused (never silently adopted)", rc3 == 1
            and before2 == sha_tree(c.game), f"rc={rc3} {out3}{err3}")

    # control: with NO foreign ra2md.csf the install proceeds
    make_golden(c.game)
    rc4, out4, err4 = c.install(pkg)
    c.check("CSF_INST3i: control - install succeeds when the game dir has no "
            "ra2md.csf", rc4 == 0
            and (c.game / "ra2md.csf").read_bytes() == pkg_csf,
            f"rc={rc4} {out4}{err4}")
    return c


def case_CSF_INST4(_fx) -> Case:
    """CSF_INST4: --csf-out landing INSIDE a game directory must be treated as
    an install-level write entry: REFUSED by default with ZERO writes (W38
    CRITICAL). The explicit --allow-csf-out-in-game flag is required to write."""
    c = Case("CSF_INST4")
    design = _csfi_design("INST4Guard", ["GD01"])
    dp = c.dir / "design_inst4.json"
    dp.write_text(json.dumps(design, indent=2, ensure_ascii=False),
                  encoding="utf-8")
    make_golden(c.game)
    in_game = c.game / "ra2md.csf"
    before = sha_tree(c.game)

    rc1, o1, e1 = c.run_module(
        V12_ROOT,
        ["build", "--design", str(dp), "--out", str(c.dir / "out_inst4"),
         "--csf-out", str(in_game)],
        "v12-csf-inst4-in-game")[0:3]
    c.check("CSF_INST4a: build with --csf-out inside a game dir is REFUSED "
            "(exit 1)", rc1 == 1, f"rc={rc1} {o1[:200]}{e1[:200]}")
    c.check("CSF_INST4b: refusal names the install-level write entry and "
            "the explicit flag", "install-level write entry" in (o1 + e1)
            and "resolves inside the game directory" in (o1 + e1)
            and "--allow-csf-out-in-game" in (o1 + e1), (o1 + e1)[:700])
    c.check("CSF_INST4c: ZERO bytes written into the game dir (guard fired "
            "before any write)", before == sha_tree(c.game)
            and not in_game.exists(), f"before:\n{before}\n\nafter:\n{sha_tree(c.game)}")
    c.check("CSF_INST4c2: guard runs BEFORE the build's first filesystem "
            "write, so even the package output dir is NOT created",
            not (c.dir / "out_inst4").exists())

    # explicit confirmation flag permits the write (with identity checks),
    # proving the guard is about target identity + explicit confirmation.
    rc2, o2, e2 = c.run_module(
        V12_ROOT,
        ["build", "--design", str(dp), "--out", str(c.dir / "out_inst4_allow"),
         "--csf-out", str(in_game), "--allow-csf-out-in-game"],
        "v12-csf-inst4-allow")[0:3]
    c.check("CSF_INST4d: --allow-csf-out-in-game explicitly permits the "
            "in-game write (and the CSF is complete)", rc2 == 0
            and in_game.is_file(), f"rc={rc2} {o2[:200]}{e2[:200]}")
    if rc2 == 0 and in_game.is_file():
        facts = f"""
import json, sys
sys.path.insert(0, {str(V12_ROOT)!r})
from pathlib import Path
from ra2forge import csf
raw = Path({str(in_game)!r}).read_bytes()
d = csf.parse_csf(raw, strict=True)
print(json.dumps({{"labels": d.num_labels,
                  "baseline_ok": csf.assert_complete_csf(d)["baseline_labels"] == 5211}},
                 ensure_ascii=False))
"""
        rc_f, of, ef = c.run_python(V12_ROOT, facts, "v12-csf-inst4-allow-facts")
        c.check("CSF_INST4e: the explicitly-allowed in-game CSF is still a "
                "complete legal clone (guard not bypassed)", rc_f == 0
                and json.loads(of.strip())["baseline_ok"] == True,
                of + ef)
        report = (c.dir / "out_inst4_allow" / "INST4Guard"
                  / "BUILD_REPORT.txt").read_text(encoding="utf-8")
        c.check("CSF_INST4f: the in-game write is LOUDLY logged in the build "
                "report (WARN install-level write entry)",
                "[WARN]" in report and "install-level write entry" in report,
                report[-600:])
    return c


def case_CSF_INST5(_fx) -> Case:
    """CSF_INST5: with NO CSF-related switch, the v12 build is BYTE-FOR-BYTE
    IDENTICAL to the v11 build across every file; emit a SHA-256 comparison
    table to out/SHA256_COMPAT.txt (backward-compatibility hard evidence)."""
    c = Case("CSF_INST5")
    design = _ms_design("INST5Compat", ["CP1", "CP2"])
    dp = c.dir / "design_inst5.json"
    dp.write_text(json.dumps(design, indent=2, ensure_ascii=False),
                  encoding="utf-8")
    o11 = c.dir / "out_v11"
    o12 = c.dir / "out_v12"
    rc11, _o11, e11 = c.run_module(
        V11_REF_ROOT, ["build", "--design", str(dp), "--out", str(o11)],
        "v11-ref-default-build")
    rc12, _o12, e12 = c.run_module(
        V12_ROOT, ["build", "--design", str(dp), "--out", str(o12)],
        "v12-default-build")
    c.check("CSF_INST5a: v11 reference and v12 no-flag builds both exit 0",
            rc11 == 0 and rc12 == 0, f"{rc11}/{rc12} {e11} {e12}")
    t11, t12 = sha_tree(o11), sha_tree(o12)
    c.check("CSF_INST5b: v12 no-CSF-switch build is BYTE-FOR-BYTE IDENTICAL "
            "to v11 across every file", t11 == t12 and bool(t11.splitlines()),
            f"v11:\n{t11}\n\nv12:\n{t12}")
    c.check("CSF_INST5c: neither build emits ra2md.csf (CSF switches off)",
            "ra2md.csf" not in t11 and "ra2md.csf" not in t12)

    # SHA-256 comparison table (deliverable out/SHA256_COMPAT.txt).
    def _tree_map(tree: str) -> dict:
        out = {}
        for ln in tree.splitlines():
            sha, size, rel = ln.split(None, 2)
            out[rel.strip()] = (sha, int(size))
        return out
    m11, m12 = _tree_map(t11), _tree_map(t12)
    rows = ["W43 S3 backward-compatibility SHA-256 table (v13 vs v11 ref)",
            "build: NO CSF-related switch (no --csf-out / --csf-base / "
            "--mapselmd / --allow-csf-out-in-game) AND no new S3 switch",
            f"v11 (READ-ONLY ref): {V11_REF_ROOT}",
            f"v13 (this card):     {V12_ROOT}",
            "",
            f"{'file':40s} {'bytes':>8s}  {'v11 sha256':64s}  "
            f"{'v13 sha256':64s}  match"]
    all_names = sorted(set(m11) | set(m12))
    n_match = 0
    for rel in all_names:
        s11 = m11.get(rel, ("<missing>", -1))
        s12 = m12.get(rel, ("<missing>", -1))
        match = s11 == s12
        n_match += int(match)
        rows.append(f"{rel:40s} {s11[1]:8d}  {s11[0]:64s}  "
                    f"{s12[0]:64s}  {'MATCH' if match else 'DIFF'}")
    rows += ["", f"files: {len(all_names)}  identical: {n_match}  "
             f"different: {len(all_names) - n_match}",
             f"VERDICT: {'IDENTICAL' if t11 == t12 else 'DIFFERENT'}"]
    table = "\n".join(rows) + "\n"
    (OUT / "SHA256_COMPAT.txt").write_text(table, encoding="utf-8")
    c.note("INST5 SHA-256 table written to out/SHA256_COMPAT.txt:\n" + table)
    c.check("CSF_INST5d: every file in the SHA-256 table is a MATCH",
            t11 == t12 and n_match == len(all_names) and len(all_names) > 0,
            f"{n_match}/{len(all_names)} match")

    # The CSF-related switches, when OFF, must not appear at all; and when ON,
    # pre-existing artifacts stay byte-identical (mirror of MS4e).
    o12_csf = c.dir / "out_v12_csf"
    rc_csf, _o, e_csf = c.run_module(
        V12_ROOT,
        ["build", "--design", str(dp), "--out", str(o12_csf),
         "--csf-out", str(c.dir / "inst5_csf_out.csf")],
        "v12-csf-build")
    c.check("CSF_INST5e: v12 --csf-out build exits 0", rc_csf == 0, e_csf)
    if rc_csf == 0:
        set12 = {ln.split(None, 2)[2] for ln in t12.splitlines()}
        set_csf = {ln.split(None, 2)[2] for ln in sha_tree(o12_csf).splitlines()}
        extra = sorted(set_csf - set12)
        c.check("CSF_INST5f: --csf-out adds exactly the CSF artifacts "
                "(ra2md.csf + csf_patch.json) and nothing else changes",
                len(extra) == 2
                and any(n.endswith("ra2md.csf") for n in extra)
                and any(n.endswith("csf_patch.json") for n in extra),
                str(extra))
    return c


def case_CSF_INST6(_fx) -> Case:
    """CSF_INST6: the upgrade / BACKUP / RESTORE path also covers ra2md.csf.
    Mirrors W34 MS5's restore scenario: install P1, plant a user original in
    the backup slot, upgrade to P2 (backup="keep"), uninstall must RESTORE the
    exact original bytes (not our own P1 bytes -> W21 original_absent flag)."""
    c = Case("CSF_INST6")
    d1 = _csfi_design("INST6P1", ["U01"])
    d2 = _csfi_design("INST6P2", ["U02"])
    d1["campaign"]["description"] = "W41 CSF restore probe - P1 description."
    d2["campaign"]["description"] = "W41 CSF restore probe - P2 DIFFERENT."
    t1 = c.dir / "inst6_csf_p1.csf"
    t2 = c.dir / "inst6_csf_p2.csf"
    rc1, _o, e1, p1 = _ms_build(c, d1, "inst6p1", ["--csf-out", str(t1)])
    rc2, _o, e2, p2 = _ms_build(c, d2, "inst6p2", ["--csf-out", str(t2)])
    c.check("CSF_INST6a: both --csf-out packages build (same package_id)",
            rc1 == 0 and rc2 == 0, e1 + e2)
    if rc1 != 0 or rc2 != 0:
        return c
    m1 = (p1 / "ra2md.csf").read_bytes()
    m2 = (p2 / "ra2md.csf").read_bytes()
    c.check("CSF_INST6b: the two packages have DIFFERENT ra2md.csf bytes "
            "(different label text)", m1 != m2)

    make_golden(c.game)
    rc_i1, oi1, ei1 = c.install(p1)
    c.check("CSF_INST6c: first install (P1) exits 0", rc_i1 == 0, oi1 + ei1)
    c.check("CSF_INST6d: P1's ra2md.csf landed", (c.game / "ra2md.csf").is_file()
            and (c.game / "ra2md.csf").read_bytes() == m1)

    # plant a USER original in the backup slot -> upgrade must "keep" it
    original = (c.dir / "user_original.csf")
    # a complete official clone + a distinct user label (still a valid loose CSF)
    mk_orig = f"""
from pathlib import Path
from ra2forge import csf
d = csf.load_official_csf()
d.set("USER:ORIGINAL", "pre-install user original CSF")
csf.write_csf(Path({str(original)!r}), d, require_complete=True)
print("wrote", Path({str(original)!r}).stat().st_size)
"""
    rc_o, _oo, eo = c.run_python(V12_ROOT, mk_orig, "v12-csf-inst6-mk-original")
    c.check("CSF_INST6e: user-original CSF fixture written", rc_o == 0, eo)
    (c.game / "ra2md.csf.ra2forge.bak").write_bytes(original.read_bytes())

    rc_i2, oi2, ei2 = c.install(p2)
    c.check("CSF_INST6f: upgrading to P2 (same package_id) is allowed",
            rc_i2 == 0, oi2 + ei2)
    c.check("CSF_INST6g: upgraded ra2md.csf has P2 bytes and the user "
            "backup slot is KEPT", (c.game / "ra2md.csf").read_bytes() == m2
            and (c.game / "ra2md.csf.ra2forge.bak").read_bytes()
            == original.read_bytes())
    man2 = c.manifest()
    e2 = [e for e in man2["files"] if e["name"] == "ra2md.csf"]
    c.check("CSF_INST6h: upgraded manifest records ra2md.csf with "
            "original_absent absent/False (there IS a real original)",
            len(e2) == 1 and not e2[0].get("original_absent", False),
            str(e2))

    rc_u, ou, eu = c.uninstall()
    c.check("CSF_INST6i: uninstall RESTORES the exact user original "
            "ra2md.csf bytes from the backup", rc_u == 0
            and (c.game / "ra2md.csf").is_file()
            and (c.game / "ra2md.csf").read_bytes() == original.read_bytes()
            and "restored   ra2md.csf.ra2forge.bak -> ra2md.csf" in ou,
            ou + eu)
    c.check("CSF_INST6j: no backup residue after a completed restore",
            not (c.game / "ra2md.csf.ra2forge.bak").exists())
    return c


# ---------------------------------------------------------------------------
# W43 / S3 cases.  Implemented in s3_cases.py and bound into THIS module's
# namespace so they reuse the exact same Case harness / fixtures / log format.
# The 57 inherited cases above are untouched.
# ---------------------------------------------------------------------------
import s3_cases as _s3_cases
_s3_cases.bind_s3(globals())
S3_CASES = _s3_cases.S3_CASES
# W46/S4: the 82 v13 cases above are preserved verbatim (57 inherited + 25 S3).
# The NEW integration cases live in s4_cases.py and use the SAME Case harness.
import s4_cases as _s4_cases
_s4_cases.bind_s4(globals())
S4_CASES = _s4_cases.S4_CASES
# W60: six NEW inplace regression cases, same Case harness.
import s5_cases as _s5_cases
_s5_cases.bind_s5(globals())
S5_CASES = _s5_cases.S5_CASES

# ---------------------------------------------------------------------------
# W77 -- ONE new case: the EXIT 33 refusal message is product language.
# W74 measured that a second install in the same sandbox lands on the W60
# inplace preflight (exit 33) BEFORE the PKG-IDENT01 gate, so the user saw
# the internal invariant name, never the EXIT 3 package_mismatch story.
# v16 rewords ONLY the message.  This case adds an assertion surface for the
# new wording and for the preserved machine-readable parts; it does NOT
# modify any inherited case body, exit code, gate or threshold.
# ---------------------------------------------------------------------------

W77_PKG_A = "org.ra2forge.w77.alpha"
W77_PKG_B = "org.ra2forge.w77.beta"


def case_W77_1(fx) -> object:
    c = _s5_cases.G.Case("W77_1")
    S5 = _s5_cases.G
    # ---- package A installs cleanly (official baseline present) -----------
    fsA = _s5_cases._fsfile(c, "fs_w77_a.json",
                            _s5_cases._inplace_fs("W77-A"))
    dA = _s5_cases._design("W77A", package_id=W77_PKG_A)
    rc_a, o_a, e_a, pkgA = _s5_cases._build(
        c, dA, "w77a", ["--feature-set", str(fsA)])
    c.check("W77_1a: package A inplace build exits 0",
            rc_a == 0 and pkgA.is_dir(), o_a + e_a)
    g = _s5_cases._golden_official(c)
    rc_1, o_1, e_1 = _s5_cases._install(c, pkgA, g, fsA)
    c.check("W77_1b: package A install exits 0 (route (a) inplace)",
            rc_1 == 0, o_1 + e_1)
    m1 = _s5_cases._manifest(g)
    c.check("W77_1c: install record names package A (id + version) - this is "
            "what the v16 message quotes back at the user",
            m1.get("package_id") == W77_PKG_A
            and m1.get("package_version") == "1.0",
            f"{m1.get('package_id')}/{m1.get('package_version')}")
    before_b = S5.sha_tree(g)
    # ---- package B (different id) into the SAME directory -----------------
    fsB = _s5_cases._fsfile(c, "fs_w77_b.json",
                            _s5_cases._inplace_fs("W77-B"))
    dB = _s5_cases._design("W77B", package_id=W77_PKG_B)
    rc_bb, o_bb, e_bb, pkgB = _s5_cases._build(
        c, dB, "w77b", ["--feature-set", str(fsB)])
    c.check("W77_1d: package B inplace build exits 0",
            rc_bb == 0 and pkgB.is_dir(), o_bb + e_bb)
    rc_2, o_2, e_2 = _s5_cases._install(c, pkgB, g, fsB)
    blob = o_2 + e_2
    c.check("W77_1e: second install REFUSED with exit 33 and the "
            "INPLACE_OFFICIAL_MISMATCH reason code (both preserved verbatim)",
            rc_2 == 33 and "INPLACE_OFFICIAL_MISMATCH" in blob,
            f"rc={rc_2} " + blob)
    c.check("W77_1f: PRODUCT language present: the message names the already "
            "installed package (id + version), states one-package-at-a-time "
            "and gives the uninstall remedy",
            W77_PKG_A in blob and "version 1.0" in blob
            and "ONE campaign package at a time" in blob
            and "uninstall" in blob, blob)
    c.check("W77_1g: remedy command is concrete: 'ra2forge uninstall --game "
            "<this game dir>'",
            "ra2forge uninstall --game" in blob and str(g) in blob, blob)
    c.check("W77_1h: machine-readable parts preserved (sha pair, 'Zero bytes "
            "written') and the v15 misleading 'content conflict' wording is "
            "GONE",
            "sha=" in blob and "expected " in blob
            and "Zero bytes written" in blob
            and "content conflict" not in blob, blob)
    c.check("W77_1i: ZERO writes on the refused second install: game dir "
            "byte-identical, package A's manifest still owns the directory",
            S5.sha_tree(g) == before_b
            and _s5_cases._manifest(g).get("package_id") == W77_PKG_A,
            str(S5.sha_tree(g) == before_b))
    return c


CASES = {
    "P0": case_P0, "V1": case_V1, "V2": case_V2, "V3": case_V3,
    "V4": case_V4, "V5": case_V5, "V6": case_V6,
    "P1": case_P1, "P2": case_P2, "P3": case_P3, "P4": case_P4,
    "C1": case_C1, "C2": case_C2, "T4": case_T4,
    "S1": case_S1, "S2": case_S2, "S3": case_S3, "S4": case_S4,
    "S5": case_S5, "S6": case_S6, "S7": case_S7, "S8": case_S8,
    "F0": case_F0, "F1": case_F1, "F2": case_F2, "F3": case_F3,
    "F4": case_F4, "F5": case_F5, "F6": case_F6, "F7": case_F7,
    "U1": case_U1, "U2": case_U2, "U3": case_U3, "U4": case_U4,
    "U5": case_U5, "U6": case_U6,
    "R0": case_R0, "R1": case_R1, "R2": case_R2,
    "CSF1": case_CSF1, "CSF2": case_CSF2, "CSF3": case_CSF3,
    "CSF4": case_CSF4, "CSF5": case_CSF5, "CSF6": case_CSF6,
    "MS1": case_MS1, "MS2": case_MS2, "MS3": case_MS3,
    "MS4": case_MS4, "MS5": case_MS5, "MS6": case_MS6,
    "CSF_INST1": case_CSF_INST1, "CSF_INST2": case_CSF_INST2,
    "CSF_INST3": case_CSF_INST3, "CSF_INST4": case_CSF_INST4,
    "CSF_INST5": case_CSF_INST5, "CSF_INST6": case_CSF_INST6,
    **S3_CASES, **S4_CASES, **S5_CASES,
    "W77_1": case_W77_1,
}


def main(argv: list[str]) -> int:
    OUT.mkdir(exist_ok=True)
    if W21_ROOT.name != "ra2forge_patched" or not (W21_ROOT / "ra2forge" / "install.py").is_file():
        print(f"FATAL: v0.5 reference build not found at {W21_ROOT}", file=sys.stderr)
        return 1
    if not REAL_MANIFEST.is_file():
        print(f"FATAL: real manifest not found at {REAL_MANIFEST}", file=sys.stderr)
        return 1
    fx = build_fixtures()
    selected = argv or list(CASES)
    results = []
    for name in selected:
        fn = CASES.get(name)
        if fn is None:
            print(f"unknown case: {name}", file=sys.stderr)
            return 1
        case = fn(fx)
        case.finish()
        n_pass = sum(1 for _, ok, _ in case.checks if ok)
        n_fail = sum(1 for _, ok, _ in case.checks if not ok)
        results.append((name, not case.failed, n_pass, n_fail))
        print(f"{'PASS' if not case.failed else 'FAIL'}  {name:4s}  "
              f"checks: {n_pass} passed / {n_fail} failed")
    total_checks_pass = sum(r[2] for r in results)
    total_checks_fail = sum(r[3] for r in results)
    n_cases = len(results)
    n_ok = sum(1 for r in results if r[1])
    n_bad = n_cases - n_ok
    summary = [
        "W77 v16 regression summary (regress_dlc_v16.py; v15 suite + 1 "
        "message case)",
        f"cases: {n_cases}  passed: {n_ok}  failed: {n_bad}",
        f"assertions: {total_checks_pass} passed / {total_checks_fail} failed",
        f"exit: {0 if n_bad == 0 else 1}",
        f"inherited v13 cases: {sum(1 for name, *_ in results if name not in S4_CASES)}",
        f"S4 cases: {sum(1 for name, *_ in results if name in S4_CASES)}",
        f"W60 S5 cases: {sum(1 for name, *_ in results if name in S5_CASES)}",
        f"W77 EXIT-33 message cases: {sum(1 for name, *_ in results if name == 'W77_1')}",
        "",
        *[f"{'PASS' if ok else 'FAIL'}  {name}  ({p}/{p + f} checks)"
          for name, ok, p, f in results],
        "",
        "logs: out/<case>.log  (每条: 命令 + 原始输出 + 退出码 + 逐项判据)",
        "SHA-256 compat tables: out/SHA256_COMPAT.txt (v14 vs v11), "
        "out/SHA256_COMPAT_V13_V12.txt (v14 vs v12, inherited S3_25) and "
        "out/SHA256_COMPAT_V14_V13.txt (v14 vs v13, S4_8)",
        "NOTE: regression green proves the FILE-LAYER plan/guard/integration "
        "behaviour ONLY. It does NOT prove real-machine game behaviour, that "
        "the version guard is universally enabled (it is opt-in), or that "
        "battlemd:inplace is implemented OFFLINE ONLY (Lead D5.2 unfrozen; "
        "live-machine acceptance belongs to a later card). See "
        "INTEGRATION.md / UNCOVERED.md.",
    ]
    (OUT / "SUMMARY.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print()
    print("\n".join(summary[:4]))
    print(f"logs written to {OUT}")
    return 0 if n_bad == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
