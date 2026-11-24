#!/usr/bin/env python3
"""Generate BASELINE_V9_POST.sha256.txt and cumulative PATCH_RELATIVE.diff
(repo HEAD ra2forge/ 0.4 -> W26 ra2forge_patched_v9/ra2forge/ 0.9), and verify
byte-exact replay inside W26_dlc_unseal_fix/sandbox/_replay_check/.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

W26_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = W26_ROOT.parents[2]
ORIG_PKG = REPO_ROOT / "ra2forge"
PATCHED_PKG = W26_ROOT / "ra2forge_patched_v9" / "ra2forge"
POST_HASH_FILE = W26_ROOT / "BASELINE_V9_POST.sha256.txt"
PATCH_FILE = W26_ROOT / "PATCH_RELATIVE.diff"
REPLAY_SANDBOX = W26_ROOT / "sandbox" / "_replay_check"


def sha256_tree(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or ".mimosa" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        hashes[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def write_post_hashes(hashes: dict[str, str]) -> None:
    lines = [f"{digest}  ra2forge_patched_v9/ra2forge/{rel}"
             for rel, digest in sorted(hashes.items())]
    POST_HASH_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _git_env(empty_cfg: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["GIT_CONFIG_GLOBAL"] = str(empty_cfg)
    env["GIT_CONFIG_SYSTEM"] = str(empty_cfg)
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    return env


def _relativize_diff(raw_diff: str, old_prefix: str, new_prefix: str) -> str:
    # Rewrite staged clean snapshot prefixes back to repo-relative "ra2forge".
    out_lines: list[str] = []
    for line in raw_diff.splitlines():
        if line.startswith(("diff --git ", "--- ", "+++ ", "rename from ",
                            "rename to ", "copy from ", "copy to ")):
            line = (line
                    .replace(new_prefix, "ra2forge")
                    .replace(old_prefix, "ra2forge"))
        out_lines.append(line)
    return "\n".join(out_lines) + "\n"


def generate_patch(env: dict[str, str]) -> None:
    cmp_root = REPLAY_SANDBOX / "cmp"
    old_stage = cmp_root / "orig_pkg"
    new_stage = cmp_root / "patched_pkg"
    ignore = shutil.ignore_patterns("__pycache__", ".mimosa", "*.pyc")
    shutil.copytree(ORIG_PKG, old_stage, ignore=ignore)
    shutil.copytree(PATCHED_PKG, new_stage, ignore=ignore)

    old_rel = old_stage.relative_to(REPO_ROOT).as_posix()
    new_rel = new_stage.relative_to(REPO_ROOT).as_posix()
    cmd = ["git", "-c", "core.autocrlf=false",
           "diff", "--no-index", "--binary", "--", old_rel, new_rel]
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), env=env, capture_output=True,
                          text=True, encoding="utf-8", errors="surrogateescape")
    # git diff --no-index exits 1 when differences exist, 0 when identical.
    if proc.returncode not in (0, 1):
        raise RuntimeError(f"git diff failed ({proc.returncode}): {proc.stderr}")
    rel_diff = _relativize_diff(proc.stdout, old_rel, new_rel)
    PATCH_FILE.write_bytes(rel_diff.encode("utf-8"))


def verify_replay(expected_hashes: dict[str, str], env: dict[str, str]) -> None:
    replay_dir = REPLAY_SANDBOX / "tree"
    if replay_dir.exists():
        shutil.rmtree(replay_dir)
    replay_dir.mkdir(parents=True)
    target_pkg = replay_dir / "ra2forge"
    shutil.copytree(ORIG_PKG, target_pkg,
                    ignore=shutil.ignore_patterns("__pycache__", ".mimosa", "*.pyc"))
    replay_rel = replay_dir.relative_to(REPO_ROOT).as_posix()
    apply_cmd = [
        "git", "-c", "core.autocrlf=false", "-c", "core.eol=lf",
        "apply", f"--directory={replay_rel}",
        "--check", "--verbose", str(PATCH_FILE.resolve()),
    ]
    chk = subprocess.run(apply_cmd, cwd=str(REPO_ROOT), env=env,
                         capture_output=True, text=True)
    if chk.returncode != 0:
        raise RuntimeError(f"replay --check failed: {chk.stderr}")

    real_apply = [
        "git", "-c", "core.autocrlf=false", "-c", "core.eol=lf",
        "apply", f"--directory={replay_rel}", str(PATCH_FILE.resolve()),
    ]
    app = subprocess.run(real_apply, cwd=str(REPO_ROOT), env=env,
                         capture_output=True, text=True)
    if app.returncode != 0:
        raise RuntimeError(f"replay apply failed: {app.stderr}")

    replayed = sha256_tree(target_pkg)
    if replayed != expected_hashes:
        diff_keys = set(replayed) ^ set(expected_hashes)
        changed = [k for k in expected_hashes if replayed.get(k) != expected_hashes[k]]
        raise RuntimeError(
            f"hash mismatch after replay: missing/extra={diff_keys}, changed={changed}"
        )

    # Read-only check at repo root against untouched working tree.
    root_chk = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "apply", "--check",
         str(PATCH_FILE.resolve())],
        cwd=str(REPO_ROOT), env=env, capture_output=True, text=True,
    )
    if root_chk.returncode != 0:
        raise RuntimeError(f"repo root git apply --check failed: {root_chk.stderr}")


def main() -> int:
    hashes = sha256_tree(PATCHED_PKG)
    write_post_hashes(hashes)
    if REPLAY_SANDBOX.exists():
        shutil.rmtree(REPLAY_SANDBOX)
    REPLAY_SANDBOX.mkdir(parents=True)
    try:
        empty_cfg = REPLAY_SANDBOX / "empty.gitconfig"
        empty_cfg.write_text("", encoding="utf-8")
        env = _git_env(empty_cfg)
        generate_patch(env)
        verify_replay(hashes, env)
    finally:
        if REPLAY_SANDBOX.exists():
            shutil.rmtree(REPLAY_SANDBOX)
    print(f"OK: {len(hashes)} files hashed -> {POST_HASH_FILE.name}")
    print(f"OK: cumulative diff -> {PATCH_FILE.name} ({PATCH_FILE.stat().st_size} bytes)")
    print("OK: sandbox replay + repo-root git apply --check matched 100%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
