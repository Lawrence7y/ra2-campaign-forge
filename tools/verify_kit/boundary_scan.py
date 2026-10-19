#!/usr/bin/env python3
"""boundary_scan.py -- find forbidden-API tokens in scripts / command lists.

Scans text files (any extension) for a configurable token wordlist and
reports file:line hits. Exit codes: 0 = zero hits, 1 = findings, 2 = error.

Self-exclusion: lines wrapped in the marker pair
  # >>> verify_kit wordlist (self) >>>
  # <<< verify_kit wordlist (self) <<<
are treated as QUOTED LITERALS (e.g. this scanner's own wordlist) and are
not counted. Line numbers stay stable. Use --no-self-exclude to disable the
mask -- that switch exists so you can PROVE the mask is real and not a
silent no-op: the excluded scan must be clean and the unmasked scan of this
same file must hit.

Token matching is literal with identifier boundaries: a token that is a
prefix of a longer name only matches the exact token (list every variant
you want caught, e.g. a copy helper and its file/2/tree variants).
"""
import argparse
import fnmatch
import os
import re
import sys

SELF_BEGIN = "# >>> verify_kit wordlist (self) >>>"
SELF_END = "# <<< verify_kit wordlist (self) <<<"

# >>> verify_kit wordlist (self) >>>
DEFAULT_WORDLIST = [
    "WriteProcessMemory",
    "ReadProcessMemory",
    "VirtualAllocEx",
    "VirtualProtectEx",
    "CreateRemoteThread",
    "shutil.copy",
    "shutil.copy2",
    "shutil.copyfile",
    "shutil.copytree",
]
# <<< verify_kit wordlist (self) <<<

MAX_LINE_PRINT = 160


def load_wordlist(path):
    tokens = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            t = line.strip()
            if t and not t.startswith("#"):
                tokens.append(t)
    if not tokens:
        raise ValueError("empty wordlist: %s" % path)
    return tokens


def compile_tokens(tokens):
    pats = []
    for t in tokens:
        rx = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(t) + r"(?![A-Za-z0-9_])")
        pats.append((t, rx))
    return pats


def mask_self_regions(text):
    """Blank out self-quotation marker regions, preserving line count."""
    lines = text.splitlines()
    inside = False
    for i, ln in enumerate(lines):
        if SELF_BEGIN in ln:
            inside = True
            lines[i] = ""
            continue
        if SELF_END in ln:
            inside = False
            lines[i] = ""
            continue
        if inside:
            lines[i] = ""
    return lines, inside  # inside=True at EOF means unterminated marker


def iter_target_files(targets, excludes, max_bytes):
    for t in targets:
        if os.path.isfile(t):
            yield t
        elif os.path.isdir(t):
            for dirpath, dirnames, filenames in os.walk(t, topdown=True):
                dirnames[:] = sorted(
                    d for d in dirnames
                    if not any(fnmatch.fnmatch(d, e) for e in excludes))
                for name in sorted(filenames):
                    yield os.path.join(dirpath, name)
        else:
            raise OSError("no such file or directory: %s" % t)


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="scan files for forbidden-API tokens (rc 0 clean / 1 findings)")
    ap.add_argument("targets", nargs="+", help="files and/or directories")
    ap.add_argument("--wordlist", help="token list file, one token per line, # comments")
    ap.add_argument("--exclude", action="append", default=[],
                    metavar="GLOB", help="basename glob to skip inside directories")
    ap.add_argument("--max-bytes", type=int, default=8 * 1024 * 1024,
                    help="skip files larger than this (default 8 MiB)")
    ap.add_argument("--no-self-exclude", action="store_true",
                    help="disable self-literal masking (for positive control)")
    args = ap.parse_args(argv)

    try:
        tokens = load_wordlist(args.wordlist) if args.wordlist else list(DEFAULT_WORDLIST)
        pats = compile_tokens(tokens)
        files = list(iter_target_files(args.targets, args.exclude, args.max_bytes))
    except (OSError, ValueError) as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2

    scanned = 0
    skipped = 0
    hits = []
    files_with_hits = set()
    for fp in files:
        try:
            if os.path.getsize(fp) > args.max_bytes:
                print("SKIP (too large, > %d bytes): %s" % (args.max_bytes, fp))
                skipped += 1
                continue
            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as e:
            print("ERROR reading %s: %s" % (fp, e), file=sys.stderr)
            return 2
        scanned += 1
        if args.no_self_exclude:
            lines = text.splitlines()
        else:
            lines, unterminated = mask_self_regions(text)
            if unterminated:
                print("WARNING: unterminated self-marker in %s (masked to EOF)" % fp)
        for lineno, ln in enumerate(lines, 1):
            for tok, rx in pats:
                if rx.search(ln):
                    hits.append((fp, lineno, tok, ln.strip()[:MAX_LINE_PRINT]))
                    files_with_hits.add(fp)

    for fp, lineno, tok, snippet in hits:
        print("HIT %s:%d token=%s :: %s" % (fp, lineno, tok, snippet))
    print("scanned: %d file(s), skipped: %d, tokens: %d, self-exclude: %s"
          % (scanned, skipped, len(tokens), "off" if args.no_self_exclude else "on"))
    if hits:
        print("VERDICT: FINDINGS (%d hit(s) in %d file(s))"
              % (len(hits), len(files_with_hits)))
        return 1
    print("VERDICT: CLEAN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
