"""W25 double-fault driver (T2 of UNSEAL_FIX.md): the seal write fails AND
the install-record rollback ALSO fails - the exact path W24 UNCOVERED.md §2
recorded as having no injection evidence: install.py's seal-failure handler
wraps the record rollback in `except OSError: pass` and then raises the
seal-messaging error ("the install record was rolled back to its previous
bytes"), silently skipping a rollback that just failed - i.e. with the
rollback write dead the install DOES leave "new record standing, no seal"
(the refused-uninstall state) while claiming otherwise.

Package code is untouched (the W24 methodology: driver-level monkeypatching
only, no injection code inside ra2forge_patched_v8).

Why the second obstruction cannot be a static filesystem act: the record
write and the rollback write hit the SAME destination (the manifest slot)
in adjacent statements, so any obstacle standing on that slot before the run
breaks the FIRST write instead (a different, already-covered path). The
only deterministic way to make the second write fail is an external act
inside the window between the record write and the seal write - the driver
wraps write_install_seal (which is called exactly there) and flips the
READ-ONLY attribute on the freshly written manifest. Both actual failures
stay REAL OS errors on real filesystem objects:

  - the seal write fails on the test's own pre-set obstruction (read-only
    seal file / a directory occupying the seal slot): real
    PermissionError [WinError 5] at os.replace, or the production
    landing-slot refusal - never a synthetic raise;
  - the record rollback fails on the read-only manifest: real
    PermissionError [WinError 5] at os.replace (restore mode) or at
    unlink (DeleteFile on a read-only file), swallowed by the production
    `except OSError: pass`.

Usage:
    python v8_rollback_fault_driver.py <package_dir> <game_dir> <mode> [patched_root]

modes (explicit, switchable, default none):
    @rollback_write  UPDATE install over an existing seal-era pair. The
                     TEST pre-sets the existing seal READ-ONLY (pure
                     filesystem, before the install). The driver wraps
                     write_install_seal and sets the fresh manifest
                     read-only right before the seal attempt -> the seal
                     write fails (WinError 5) AND the byte-exact record
                     restore fails (WinError 5) inside `except OSError:
                     pass`.
    @rollback_unlink FRESH install. The TEST plants a DIRECTORY at the
                     seal slot (pure filesystem) so the seal write fails
                     at the production landing-slot gate; the driver sets
                     the fresh manifest read-only before the seal attempt
                     -> the rollback unlink() of the fresh record fails
                     (WinError 5) inside `except OSError: pass`.

Without an explicit mode the driver refuses (exit 3) BEFORE importing
ra2forge - no injection, no game-dir contact.

Exit codes: 1 = install failed as injected (expected); 2 = install
unexpectedly SUCCEEDED (the injection did not fire - a test harness fault,
never a pass); 3 = bad usage.
"""
import os
import sys
from pathlib import Path

package, game, mode = sys.argv[1], sys.argv[2], sys.argv[3]
if len(sys.argv) > 5 or mode not in ("@rollback_write", "@rollback_unlink"):
    print(__doc__)
    sys.exit(3)
patched_root = sys.argv[4] if len(sys.argv) > 4 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "ra2forge_patched_v8")
sys.path.insert(0, os.path.abspath(patched_root))

from ra2forge import install as inst  # noqa: E402

print("using install module:", inst.__file__)
print("injection mode:", mode, "(explicit; none = no injection)")
print("injected act: os.chmod(<fresh install record>, S_IREAD) inside the "
      "window between the record write and the seal write - both failures "
      "remain real OS errors (read-only destination)")
sys.stdout.flush()

# ---------------------------------------------------------------------------
# the injection point (default OFF: no mode -> no patch below is made)
# ---------------------------------------------------------------------------

real_seal_writer = inst.write_install_seal
manifest_path = Path(game) / inst.MANIFEST_NAME


def arming_seal_writer(game_dir, manifest):
    # write_install_seal is called immediately AFTER the record write, so
    # this is the one deterministic external moment between the two writes;
    # stat.S_IREAD = 0o444 user-read-only (same attribute W24's F7 used).
    os.chmod(manifest_path, 0o444)
    print(f"[inject] manifest set read-only in-window: {manifest_path}")
    sys.stdout.flush()
    return real_seal_writer(game_dir, manifest)


inst.write_install_seal = arming_seal_writer

# ---------------------------------------------------------------------------
# the real production path, exactly as W24's drivers ran it
# ---------------------------------------------------------------------------

try:
    report = inst.install_package(package, game, allow_content_conflict=True)
except Exception as exc:  # noqa: BLE001 - driver must print whatever escapes
    print(f"install failed as injected (exit 1). exception type: "
          f"{type(exc).__name__}")
    print("--- exception message ---")
    print(str(exc))
    print("--- end exception message ---")
    sys.exit(1)
else:
    print("UNEXPECTED SUCCESS - the injection did not fire:")
    for a in report["actions"]:
        print("  " + a)
    sys.exit(2)
