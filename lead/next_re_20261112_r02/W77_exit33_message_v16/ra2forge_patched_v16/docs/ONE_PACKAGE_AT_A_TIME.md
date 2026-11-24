# One campaign package at a time (v16 product constraint)

**Rule: this ra2forge version supports exactly ONE installed campaign package
per game directory, one install at a time.**

What a user sees when they try to install a second campaign package into the
same game directory (the W74-measured route (a) / `battlemd.mode=inplace`
path):

```
error: [INPLACE_OFFICIAL_MISMATCH exit=33] INPLACE_OFFICIAL_MISMATCH: campaign
package '<package_id>' (version <version>) is already installed in <game>:
its install rewrote the official loose BATTLEMD.INI, and this version
supports ONE campaign package at a time, so installing another package here
is refused BEFORE any write (the loose BATTLEMD.INI on disk is no longer the
official baseline, sha=<on-disk-16hex>..., expected <official-16hex>...).
To install the new package, first run: ra2forge uninstall --game <game>.
Zero bytes written.
```

Why the refusal exists
----------------------

Route (a) installs rewrite the **official loose `BATTLEMD.INI` in place** and
keep the untouched official bytes in `BATTLEMD.INI.ra2forge.bak`. The install
record (`ra2forge_install.json`) owns that rewrite. A second campaign package
would need to rewrite the file a *previous package* already rewrote, and this
version has no multi-package reconciliation: instead of silently corrupting
the first package, the install refuses before writing anything (zero bytes
written; the first package stays fully working and fully uninstallable).

What to do
----------

1. `python -m ra2forge uninstall --game <game>` — removes the installed
   package and restores the official `BATTLEMD.INI` byte-for-byte.
2. Install the new package with `python -m ra2forge install --package <pkg>
   --game <game> --feature-set <fs>`.

History / provenance
--------------------

* W74 measured that a second install in the same directory exits with code 33
  (`INPLACE_OFFICIAL_MISMATCH`), **not** with the EXIT 3 `package_mismatch`
  text: the W60 inplace preflight (`resolve_integration.inplace_preflight`)
  runs before the package-identity gate, so the "one package" story had no
  user-facing wording at all (v15 showed the internal invariant name instead).
* REVIEW/LEAD_VERIFY_W74.md §5 ruled: adopt "reword the EXIT 33 message",
  reject "implement true multi-package coexistence" for this version.
* v16 changes **only the message text** (and this document). Exit codes,
  reason codes, gates, thresholds and every decision branch are unchanged;
  the full v15 regression suite (96 cases) plus one new W77_1 message case
  passes unchanged.
