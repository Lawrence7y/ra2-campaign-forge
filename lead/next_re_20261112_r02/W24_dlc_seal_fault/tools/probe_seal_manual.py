#!/usr/bin/env python3
"""W24 manual smoke run (pre-regression): prove the @seal injection reaches
the seal write and the pure-filesystem obstacles do too. Throwaway-quality
output; the formal evidence lives in regress_dlc_v7i.py's out/*.log."""
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

W24 = Path(__file__).resolve().parent.parent
V7I = W24 / "ra2forge_patched_v7i"
DRIVER = W24 / "tools" / "v7i_seal_fault_driver.py"
SB = W24 / "sandbox" / "_probe"
MANIFEST = "ra2forge_install.json"
SEAL = MANIFEST + ".seal"
PY = sys.executable
ENV = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}


def w(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.encode("utf-8"))


def make_pkg(root: Path) -> Path:
    pkg = root / "pkgS"
    pkg.mkdir(parents=True, exist_ok=True)
    w(pkg / "BATTLEMD98.INI", "; probe\n[Battles]\n15=RA2F1\n\n[RA2F1]\nDescription=SEAL PROBE\n")
    w(pkg / "X.MAP", "probe map X\n")
    w(pkg / "expandmd98.mix", "probe mix\n")
    w(pkg / "ra2forge_package.json", json.dumps(
        {"tool": "ra2forge", "package_id": "org.ra2forge.seal-probe",
         "package_version": "1.0"}, indent=2) + "\n")
    return pkg


def make_game(game: Path) -> None:
    if game.exists():
        # a read-only seal left by an earlier probe run blocks rmtree
        # (WinError 5) - clear the attribute first, then remove
        for p in game.rglob("*"):
            if p.is_file():
                os.chmod(p, stat.S_IWRITE)
            elif p.is_dir():
                os.chmod(p, stat.S_IWRITE | stat.S_IEXEC)
        shutil.rmtree(game)
    game.mkdir(parents=True)
    w(game / "gamemd.exe", "INERT\n")
    w(game / "RA2MD.INI", "[General]\n")


def tree(game: Path) -> str:
    lines = []
    for p in sorted(game.iterdir()):
        if p.is_dir():
            lines.append(f"<DIR>  {p.name}")
        else:
            data = p.read_bytes()
            lines.append(f"{hashlib.sha256(data).hexdigest()[:16]} {len(data):6d}  {p.name}")
    return "\n".join(lines) or "(empty)"


def cli(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run([PY, "-B", "-X", "utf8", "-m", "ra2forge", *args],
                          cwd=str(V7I), env=ENV, capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=120)
    return proc.returncode, proc.stdout + proc.stderr


def driver(pkg: Path, game: Path, mode: str) -> tuple[int, str]:
    proc = subprocess.run([PY, "-B", "-X", "utf8", str(DRIVER),
                           str(pkg), str(game), mode, str(V7I)],
                          cwd=str(W24), env=ENV, capture_output=True,
                          text=True, encoding="utf-8", errors="replace",
                          timeout=120)
    return proc.returncode, proc.stdout + proc.stderr


def probe(name: str) -> None:
    print(f"\n{'=' * 72}\nPROBE {name}\n{'=' * 72}")


def show(rc: int, out: str, game: Path) -> None:
    print(f"exit={rc}")
    tail = out.rstrip().splitlines()
    for ln in tail[-8:]:
        print("  | " + ln)
    print("--- game dir after ---")
    print(tree(game))


PKG = make_pkg(SB)

# 1) @seal - form (a) fresh install
g = SB / "g_seal"
make_game(g)
probe("1 driver @seal (fresh install, seal unwritable)")
rc, out = driver(PKG, g, "@seal")
show(rc, out, g)
print("[probe1] manifest gone:", not (g / MANIFEST).exists(),
      "| seal gone:", not (g / SEAL).exists(),
      "| no stage residue:", not list(g.glob("*.ra2forge-stage*")),
      "| pkg files rolled back:", not (g / "BATTLEMD98.INI").exists())

# 2) @seal_half - form (b) fresh install
g = SB / "g_half"
make_game(g)
probe("2 driver @seal_half (fresh install, disk full mid seal write)")
rc, out = driver(PKG, g, "@seal_half")
show(rc, out, g)
print("[probe2] manifest gone:", not (g / MANIFEST).exists(),
      "| seal gone:", not (g / SEAL).exists(),
      "| no stage residue:", not list(g.glob("*.ra2forge-stage*")),
      "| pkg files rolled back:", not (g / "BATTLEMD98.INI").exists())

# 3) @seal_open - form (a) variant fresh install
g = SB / "g_open"
make_game(g)
probe("3 driver @seal_open (staging creation fails)")
rc, out = driver(PKG, g, "@seal_open")
show(rc, out, g)
print("[probe3] manifest gone:", not (g / MANIFEST).exists(),
      "| seal gone:", not (g / SEAL).exists(),
      "| pkg files rolled back:", not (g / "BATTLEMD98.INI").exists())

# 4) pure-FS form (a): a DIRECTORY occupies the seal slot
g = SB / "g_fsdir"
make_game(g)
(g / SEAL).mkdir()
probe("4 pure-FS: directory planted at the seal slot, plain CLI install")
rc, out = cli(["install", "--package", str(PKG), "--game", str(g)])
show(rc, out, g)
print("[probe4] manifest gone:", not (g / MANIFEST).exists(),
      "| pkg files rolled back:", not (g / "BATTLEMD98.INI").exists())

# 5) pure-FS form (c): existing install, seal made read-only, plain CLI update
g = SB / "g_fsro"
make_game(g)
rc, out = cli(["install", "--package", str(PKG), "--game", str(g)])
print(f"\n{'=' * 72}\nPROBE 5 pure-FS: read-only seal, plain CLI update\n{'=' * 72}")
print(f"setup install exit={rc}")
pre_m = (g / MANIFEST).read_bytes()
pre_s = (g / SEAL).read_bytes()
print("pre-update manifest sha:", hashlib.sha256(pre_m).hexdigest()[:16])
print("pre-update seal sha    :", hashlib.sha256(pre_s).hexdigest()[:16])
# no recorded file is touched here: the ONLY obstacle is the read-only seal.
# (a drifted file would make the preflight refuse before the seal write -
# measured once and removed; preflight drift-refusal is NOT the seal fault.)
os.chmod(g / SEAL, stat.S_IREAD)
print("seal set read-only:", not (g / SEAL).stat().st_mode & stat.S_IWRITE)
rc, out = cli(["install", "--package", str(PKG), "--game", str(g)])
show(rc, out, g)
post_m = (g / MANIFEST).read_bytes() if (g / MANIFEST).exists() else None
print("[probe5] manifest == pre bytes:", post_m == pre_m,
      "| seal still old:", (g / SEAL).read_bytes() == pre_s if (g / SEAL).exists() else False)
rc, out = cli(["verify", "--game", str(g)])
print(f"verify after failed update: exit={rc}")
print("  | " + "\n  | ".join(out.rstrip().splitlines()[-6:]))
rc, out = cli(["uninstall", "--game", str(g)])
print(f"uninstall after failed update: exit={rc}")
for ln in out.rstrip().splitlines()[-10:]:
    print("  | " + ln)
print("--- game dir after uninstall attempt ---")
print(tree(g))
