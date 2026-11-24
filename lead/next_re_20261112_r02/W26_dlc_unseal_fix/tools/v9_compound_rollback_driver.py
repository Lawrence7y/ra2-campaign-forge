#!/usr/bin/env python3
"""W26 regression-only compound rollback fault driver.

Used ONLY by regress_dlc_v9.py (never imported by production ra2forge).
Flips BOTH the freshly written manifest AND X.MAP read-only (os.chmod S_IREAD)
in the window between record write and seal write, so the seal-write failure
triggers BOTH:
  1) a real OS PermissionError on install-record rollback; AND
  2) a real OS PermissionError rolling back X.MAP inside _rollback(),
testing that record rollback, failing file rollback, and remaining file
rollbacks are strictly isolated and aggregated cleanly without swallowing any
error.
"""
from __future__ import annotations

import os
import stat
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print("usage: v9_compound_rollback_driver.py <pkg> <game> <mode> <v9_root>",
              file=sys.stderr)
        return 3
    pkg, game, mode, v9_root = argv
    if mode != "@compound_unlink":
        print(f"refusing unknown mode {mode!r} (no injection performed)",
              file=sys.stderr)
        return 3

    sys.path.insert(0, str(Path(v9_root).resolve()))
    import ra2forge.cli as cli
    import ra2forge.install as inst

    orig_write_seal = inst.write_install_seal

    def wrapped_write_seal(game_dir, manifest):
        g = Path(game_dir)
        manifest_path = g / inst.MANIFEST_NAME
        target_pkg_file = g / "X.MAP"
        if manifest_path.is_file():
            os.chmod(manifest_path, stat.S_IREAD)
        if target_pkg_file.is_file():
            os.chmod(target_pkg_file, stat.S_IREAD)
        return orig_write_seal(game_dir, manifest)

    inst.write_install_seal = wrapped_write_seal
    cli.install_package = inst.install_package
    return cli.main(["install", "--package", pkg, "--game", game])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
