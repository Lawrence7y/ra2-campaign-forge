"""W24 seal-fault driver: install a package while the SEAL WRITE fails.

The W23 card's gap (W23 UNCOVERED.md §5): v7_fail_driver.py's @record
injection raises during the manifest write, which happens BEFORE the seal is
written - so the "manifest written, seal write fails => install rolls the
record back to the exact previous bytes" claim (install.py docstring, the
bullet beginning "a failed install rolls the record back...") never had an
execution witness. This driver adds the missing @seal injection point.

Injection is EXTERNAL (driver-level monkeypatching, the same methodology W23
established with @record): the ra2forge_patched_v7i package is byte-identical
to W23's ra2forge_patched_v7 (SHA-256 per file, see SEAL_FAULT.md) and carries
no injection code at all. Nothing is injected unless an explicit mode is
passed on the command line; there is no default failure.

Usage:
    python v7i_seal_fault_driver.py <package_dir> <game_dir> <mode> [patched_root]

modes (explicit, switchable, default none):
    @seal       write_install_seal raises OSError at entry
                - form (a): the seal target is completely unwritable
                (read-only directory, occupied slot, simulated IO error).
    @seal_open  _open_staging_file raises OSError when the destination is the
                seal - form (a) variant: the staging file cannot even be
                created next to the seal (unwritable directory).
    @seal_half  the seal's staged write lands a REAL partial prefix of the
                seal bytes on disk (flushed), then raises OSError(ENOSPC)
                - form (b): disk fills up mid-write.
                The partial write happens inside the production
                _stage_text_and_replace path (real staging file, real bytes
                on disk); only the write() call itself is wrapped, gated on
                the armed seal write so nothing else in the run is affected.

form (c) - a seal ALREADY EXISTS and the NEW seal write fails - needs no
injection at all: it is any of the modes above (or a plain filesystem
obstacle, e.g. the read-only attribute) run as an UPDATE over an existing
seal-era install. regress_dlc_v7i.py wires that sequence.

Exit codes: 1 = install failed as injected (expected); 2 = install
unexpectedly SUCCEEDED (the injection did not fire - a test harness fault,
never a pass); 3 = bad usage.
"""
import os
import sys
from pathlib import Path

package, game, mode = sys.argv[1], sys.argv[2], sys.argv[3]
if len(sys.argv) > 5 or mode not in ("@seal", "@seal_open", "@seal_half"):
    print(__doc__)
    sys.exit(3)
patched_root = sys.argv[4] if len(sys.argv) > 4 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "ra2forge_patched_v7i")
sys.path.insert(0, os.path.abspath(patched_root))

from ra2forge import install as inst  # noqa: E402

print("using install module:", inst.__file__)
print("injection mode:", mode, "(explicit; none = no injection)")
sys.stdout.flush()

# ---------------------------------------------------------------------------
# the @seal injection point (default OFF: no mode -> no patch below is made)
# ---------------------------------------------------------------------------

if mode == "@seal":
    def broken_seal(game_dir, manifest):
        raise OSError("simulated seal-write failure (injected at "
                      "write_install_seal: seal target unwritable)")

    inst.write_install_seal = broken_seal

elif mode == "@seal_open":
    real_open = inst._open_staging_file

    def sealed_open(dest, what):
        if Path(dest).name == inst.SEAL_NAME:
            raise OSError("simulated staging-creation failure (injected at "
                          f"_open_staging_file for the {what})")
        return real_open(dest, what)

    inst._open_staging_file = sealed_open

elif mode == "@seal_half":
    armed = {"seal": False}
    real_seal_writer = inst.write_install_seal
    real_fdopen = os.fdopen

    def arming_seal_writer(game_dir, manifest):
        armed["seal"] = True
        try:
            real_seal_writer(game_dir, manifest)
        finally:
            armed["seal"] = False

    inst.write_install_seal = arming_seal_writer

    class _HalfWriteFile:
        """Wraps the real staged-write file object: land half the bytes on
        disk (flushed), then fail like a full disk. Only the seal write is
        ever wrapped (the arm is set around write_install_seal alone)."""

        def __init__(self, f):
            self._f = f

        def write(self, data):
            half = max(1, len(data) // 2)
            self._f.write(data[:half])
            self._f.flush()          # the prefix is REAL bytes on disk
            raise OSError(28, "simulated disk full (ENOSPC) mid seal write "
                              f"(injected; landed {half}/{len(data)} bytes)")

        def __enter__(self):
            self._f.__enter__()
            return self

        def __exit__(self, *exc):
            return self._f.__exit__(*exc)

    def gated_fdopen(fd, *args, **kwargs):
        f = real_fdopen(fd, *args, **kwargs)
        if armed["seal"] and "b" in (args[0] if args else "r"):
            return _HalfWriteFile(f)
        return f

    os.fdopen = gated_fdopen

# ---------------------------------------------------------------------------
# the real production path, exactly as W23's driver ran it
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
