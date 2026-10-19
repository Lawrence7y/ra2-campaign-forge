#!/usr/bin/env python3
"""
validate_package_manifest.py - DLC Package Manifest Validator

Part of RA2 Campaign Forge IMPL001 (DLC line C-IMPL).
Strictly Python 3 standard library only.
Validates package manifests against schema, naming, security, and integrity rules.
Does not access network, does not modify input files, does not touch game assets.
"""

import sys
import os
import json
import re
import argparse
from typing import Any, Dict, List, Optional, Set, Tuple

# Reserved filenames (case-insensitive comparison after Windows trailing space/dot stripping)
RESERVED_FILENAMES = {
    "game.exe",
    "gamemd.exe",
    "ra2.exe",
    "ra2md.exe",
    "battlemd.ini",
}

# Allowed executables (canonical lowercase)
ALLOWED_TARGET_EXES = {
    "game.exe",
    "gamemd.exe",
}

# Allowed top-level fields (strict schema)
ALLOWED_TOP_LEVEL_KEYS = {
    "schema_version",
    "package_id",
    "version",
    "target_exe",
    "target_sha256",
    "files",
    "dependencies",
    "conflicts",
}

# Allowed file entry fields (strict schema)
ALLOWED_FILE_KEYS = {
    "path",
    "sha256",
}

PACKAGE_ID_REGEX = re.compile(r"^[a-z0-9][a-z0-9-]*$")
VERSION_REGEX = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
SHA256_REGEX = re.compile(r"^[0-9a-fA-F]{64}$")
WIN_DRIVE_REGEX = re.compile(r"^[a-zA-Z]:")
UNC_REGEX = re.compile(r"^(\\\\|//)")


def is_strict_int(val: Any) -> bool:
    """Check if value is an integer and strictly not a boolean."""
    return isinstance(val, int) and not isinstance(val, bool)


def is_strict_str(val: Any) -> bool:
    """Check if value is a string."""
    return isinstance(val, str)


def is_strict_list(val: Any) -> bool:
    """Check if value is a list."""
    return isinstance(val, list)


def is_strict_dict(val: Any) -> bool:
    """Check if value is a dict."""
    return isinstance(val, dict)


class ValidationError:
    def __init__(self, path: str, message: str):
        self.path = path
        self.message = message

    def to_dict(self) -> Dict[str, str]:
        return {"path": self.path, "message": self.message}

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def validate_manifest(data: Any) -> Tuple[List[ValidationError], Optional[Dict[str, Any]]]:
    """
    Validate a parsed manifest object against all D1-D16 rules.
    Returns (errors, normalized_manifest_dict).
    If errors is non-empty, normalized_manifest_dict is None.
    """
    errors: List[ValidationError] = []

    if not is_strict_dict(data):
        errors.append(ValidationError("/", "Root of manifest must be a JSON object"))
        return errors, None

    # D11: Strict schema check on top-level keys
    for key in sorted(data.keys()):
        if key not in ALLOWED_TOP_LEVEL_KEYS:
            errors.append(ValidationError(f"/{key}", f"Unrecognized top-level field '{key}' (strict schema rejection)"))

    # D1 & D16: schema_version
    if "schema_version" not in data:
        errors.append(ValidationError("/schema_version", "Missing required field 'schema_version'"))
    else:
        sv = data["schema_version"]
        if not is_strict_int(sv):
            errors.append(ValidationError("/schema_version", "Field 'schema_version' must be integer 1 (boolean or non-integer rejected)"))
        elif sv != 1:
            errors.append(ValidationError("/schema_version", f"Field 'schema_version' must be 1, got {sv}"))

    # D2: package_id
    pkg_id_clean: Optional[str] = None
    if "package_id" not in data:
        errors.append(ValidationError("/package_id", "Missing required field 'package_id'"))
    else:
        pid = data["package_id"]
        if not is_strict_str(pid):
            errors.append(ValidationError("/package_id", "Field 'package_id' must be a string"))
        elif len(pid) == 0:
            errors.append(ValidationError("/package_id", "Field 'package_id' cannot be empty"))
        elif len(pid) > 64:
            errors.append(ValidationError("/package_id", f"Field 'package_id' length ({len(pid)}) exceeds maximum of 64 characters"))
        elif not PACKAGE_ID_REGEX.match(pid):
            errors.append(ValidationError("/package_id", "Field 'package_id' must start with a lowercase letter or digit and contain only lowercase letters, digits, and hyphens"))
        else:
            pkg_id_clean = pid

    # D3: version
    version_clean: Optional[str] = None
    if "version" not in data:
        errors.append(ValidationError("/version", "Missing required field 'version'"))
    else:
        ver = data["version"]
        if not is_strict_str(ver):
            errors.append(ValidationError("/version", "Field 'version' must be a string"))
        elif not VERSION_REGEX.match(ver):
            errors.append(ValidationError("/version", "Field 'version' must be a 3-part non-negative integer version (e.g. '1.0.0') with no leading zeros (e.g. '01.0.0' is invalid)"))
        else:
            version_clean = ver

    # D4: target_exe
    target_exe_clean: Optional[str] = None
    if "target_exe" not in data:
        errors.append(ValidationError("/target_exe", "Missing required field 'target_exe'"))
    else:
        te = data["target_exe"]
        if not is_strict_str(te):
            errors.append(ValidationError("/target_exe", "Field 'target_exe' must be a string"))
        elif te.lower() not in ALLOWED_TARGET_EXES:
            errors.append(ValidationError("/target_exe", f"Field 'target_exe' must be one of {sorted(ALLOWED_TARGET_EXES)} (case-insensitive), got '{te}'"))
        else:
            target_exe_clean = te.lower()

    # D5: target_sha256
    target_sha256_clean: Optional[str] = None
    if "target_sha256" not in data:
        errors.append(ValidationError("/target_sha256", "Missing required field 'target_sha256'"))
    else:
        tsha = data["target_sha256"]
        if not is_strict_str(tsha):
            errors.append(ValidationError("/target_sha256", "Field 'target_sha256' must be a string"))
        elif not SHA256_REGEX.match(tsha):
            errors.append(ValidationError("/target_sha256", "Field 'target_sha256' must be a 64-character hexadecimal string"))
        else:
            target_sha256_clean = tsha.lower()

    # D6, D7, D8, D9, D11: files
    normalized_files: List[Dict[str, str]] = []
    if "files" not in data:
        errors.append(ValidationError("/files", "Missing required field 'files'"))
    else:
        files = data["files"]
        if not is_strict_list(files):
            errors.append(ValidationError("/files", "Field 'files' must be an array"))
        elif len(files) == 0:
            errors.append(ValidationError("/files", "Field 'files' must be a non-empty array"))
        else:
            seen_paths: Dict[str, int] = {}
            for idx, item in enumerate(files):
                item_ptr = f"/files/{idx}"
                if not is_strict_dict(item):
                    errors.append(ValidationError(item_ptr, "File entry must be a JSON object"))
                    continue

                # D11: Strict check on file entry keys
                for fkey in sorted(item.keys()):
                    if fkey not in ALLOWED_FILE_KEYS:
                        errors.append(ValidationError(f"{item_ptr}/{fkey}", f"Unrecognized file entry field '{fkey}' (strict schema rejection)"))

                # D7 & D9: path validation
                valid_entry_path = False
                clean_norm_path: Optional[str] = None
                if "path" not in item:
                    errors.append(ValidationError(f"{item_ptr}/path", "Missing required field 'path'"))
                else:
                    raw_p = item["path"]
                    if not is_strict_str(raw_p):
                        errors.append(ValidationError(f"{item_ptr}/path", "Field 'path' must be a string"))
                    elif len(raw_p) == 0:
                        errors.append(ValidationError(f"{item_ptr}/path", "Field 'path' cannot be empty"))
                    elif "\0" in raw_p:
                        errors.append(ValidationError(f"{item_ptr}/path", "Field 'path' contains prohibited NUL character"))
                    elif UNC_REGEX.match(raw_p):
                        errors.append(ValidationError(f"{item_ptr}/path", f"UNC path '{raw_p}' is prohibited"))
                    elif WIN_DRIVE_REGEX.match(raw_p):
                        errors.append(ValidationError(f"{item_ptr}/path", f"Windows drive path '{raw_p}' is prohibited"))
                    elif raw_p.startswith("/") or raw_p.startswith("\\"):
                        errors.append(ValidationError(f"{item_ptr}/path", f"Absolute path '{raw_p}' is prohibited"))
                    else:
                        norm_p_temp = raw_p.replace("\\", "/")
                        components = norm_p_temp.split("/")

                        has_comp_err = False
                        if any(c == "" for c in components):
                            errors.append(ValidationError(f"{item_ptr}/path", f"Path '{raw_p}' contains empty component or redundant/trailing separators"))
                            has_comp_err = True

                        if any(c in (".", "..") for c in components):
                            errors.append(ValidationError(f"{item_ptr}/path", f"Path '{raw_p}' contains prohibited '.' or '..' components"))
                            has_comp_err = True

                        # D7 Hardening (r3): Windows equivalence - component cannot collapse to empty under trailing space/dot stripping
                        if not has_comp_err and any(c.rstrip(" .") == "" for c in components):
                            errors.append(ValidationError(f"{item_ptr}/path", f"Path '{raw_p}' contains prohibited component consisting only of spaces or dots (collapses to empty after Windows trailing space/dot stripping)"))
                            has_comp_err = True

                        if not has_comp_err:
                            has_path_item_err = False
                            clean_norm_path = "/".join(components)
                            # D7 & D9 Hardening: Windows equivalence (case-insensitive + trailing spaces/dots on each component)
                            canonical_path = "/".join(c.rstrip(" .") for c in components).lower()
                            if canonical_path in seen_paths:
                                first_idx = seen_paths[canonical_path]
                                errors.append(ValidationError(f"{item_ptr}/path", f"Duplicate path '{clean_norm_path}' (case-insensitive Windows equivalence collision with /files/{first_idx}/path)"))
                                has_path_item_err = True
                            else:
                                seen_paths[canonical_path] = idx

                            # D9: Reserved file check on last component (filename)
                            # Hardening: strip Windows trailing spaces and dots
                            filename = components[-1]
                            clean_filename = filename.rstrip(" .")
                            if clean_filename.lower() in RESERVED_FILENAMES:
                                errors.append(ValidationError(f"{item_ptr}/path", f"Reserved filename '{filename}' (Windows equivalent '{clean_filename}') is prohibited"))
                                has_path_item_err = True

                            if not has_path_item_err:
                                valid_entry_path = True

                # D8: sha256 validation
                valid_entry_sha = False
                clean_sha: Optional[str] = None
                if "sha256" not in item:
                    errors.append(ValidationError(f"{item_ptr}/sha256", "Missing required field 'sha256'"))
                else:
                    sha = item["sha256"]
                    if not is_strict_str(sha):
                        errors.append(ValidationError(f"{item_ptr}/sha256", "Field 'sha256' must be a string"))
                    elif not SHA256_REGEX.match(sha):
                        errors.append(ValidationError(f"{item_ptr}/sha256", "Field 'sha256' must be a 64-character hexadecimal string"))
                    else:
                        valid_entry_sha = True
                        clean_sha = sha.lower()

                if valid_entry_path and valid_entry_sha and clean_norm_path is not None and clean_sha is not None:
                    normalized_files.append({"path": clean_norm_path, "sha256": clean_sha})

    # D10: Optional dependencies and conflicts
    dep_ids_lower: Set[str] = set()
    conf_ids_lower: Set[str] = set()
    normalized_dependencies: List[str] = []
    normalized_conflicts: List[str] = []
    pkg_id_lower = pkg_id_clean.lower() if pkg_id_clean is not None else None

    # dependencies
    if "dependencies" in data:
        deps = data["dependencies"]
        if not is_strict_list(deps):
            errors.append(ValidationError("/dependencies", "Field 'dependencies' must be an array"))
        else:
            seen_dep_in_list: Set[str] = set()
            for didx, dep in enumerate(deps):
                dptr = f"/dependencies/{didx}"
                if not is_strict_str(dep):
                    errors.append(ValidationError(dptr, "Dependency item must be a string"))
                elif len(dep) == 0 or len(dep) > 64 or not PACKAGE_ID_REGEX.match(dep):
                    errors.append(ValidationError(dptr, f"Dependency '{dep}' does not satisfy package_id format rules"))
                else:
                    d_lower = dep.lower()
                    if d_lower in seen_dep_in_list:
                        errors.append(ValidationError(dptr, f"Duplicate dependency '{dep}' (case-insensitive collision)"))
                    else:
                        seen_dep_in_list.add(d_lower)
                        dep_ids_lower.add(d_lower)
                        normalized_dependencies.append(dep)

                    if pkg_id_lower is not None and d_lower == pkg_id_lower:
                        errors.append(ValidationError(dptr, f"Self-referencing dependency '{dep}' is prohibited"))

    # conflicts
    if "conflicts" in data:
        confs = data["conflicts"]
        if not is_strict_list(confs):
            errors.append(ValidationError("/conflicts", "Field 'conflicts' must be an array"))
        else:
            seen_conf_in_list: Set[str] = set()
            for cidx, conf in enumerate(confs):
                cptr = f"/conflicts/{cidx}"
                if not is_strict_str(conf):
                    errors.append(ValidationError(cptr, "Conflict item must be a string"))
                elif len(conf) == 0 or len(conf) > 64 or not PACKAGE_ID_REGEX.match(conf):
                    errors.append(ValidationError(cptr, f"Conflict '{conf}' does not satisfy package_id format rules"))
                else:
                    c_lower = conf.lower()
                    if c_lower in seen_conf_in_list:
                        errors.append(ValidationError(cptr, f"Duplicate conflict '{conf}' (case-insensitive collision)"))
                    else:
                        seen_conf_in_list.add(c_lower)
                        conf_ids_lower.add(c_lower)
                        normalized_conflicts.append(conf)

                    if pkg_id_lower is not None and c_lower == pkg_id_lower:
                        errors.append(ValidationError(cptr, f"Self-referencing conflict '{conf}' is prohibited"))

    # D10: Check overlap between dependencies and conflicts
    overlapping = dep_ids_lower.intersection(conf_ids_lower)
    if overlapping:
        for overlap_id in sorted(overlapping):
            errors.append(ValidationError("/conflicts", f"Package ID '{overlap_id}' appears in both 'dependencies' and 'conflicts'"))

    if errors:
        return errors, None

    # Sort files by normalized path ascending (D12)
    normalized_files.sort(key=lambda x: x["path"])

    normalized_manifest = {
        "schema_version": data["schema_version"],
        "package_id": pkg_id_clean,
        "version": version_clean,
        "target_exe": target_exe_clean,
        "target_sha256": target_sha256_clean,
        "files": normalized_files,
        "dependencies": normalized_dependencies,
        "conflicts": normalized_conflicts,
    }

    return [], normalized_manifest


class ManifestArgumentParser(argparse.ArgumentParser):
    """Custom ArgumentParser to exit with code 3 on usage error."""

    def error(self, message: str) -> None:
        sys.stderr.write(f"Usage error (exit code 3): {message}\n")
        self.print_usage(sys.stderr)
        sys.exit(3)


def main() -> int:
    parser = ManifestArgumentParser(
        description="Validate RA2 Campaign / DLC package manifest JSON against schema and safety rules."
    )
    parser.add_argument("manifest", help="Path to manifest JSON file (read-only, UTF-8)")
    parser.add_argument("--json", action="store_true", help="Output errors in structured JSON format on validation failure")
    parser.add_argument("--quiet", action="store_true", help="Suppress stdout output on successful validation")
    parser.add_argument("--out", type=str, default=None, help="Write normalized JSON manifest to specified output file path")

    args = parser.parse_args()

    manifest_path = args.manifest

    # Check file accessibility (D14: exit 3 on IO / read / parse error)
    if not os.path.exists(manifest_path):
        sys.stderr.write(f"IO error (exit code 3): File not found: '{manifest_path}'\n")
        return 3

    if not os.path.isfile(manifest_path):
        sys.stderr.write(f"IO error (exit code 3): Path is not a regular file: '{manifest_path}'\n")
        return 3

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except UnicodeDecodeError as exc:
        sys.stderr.write(f"IO error (exit code 3): File is not valid UTF-8: {exc}\n")
        return 3
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"Parse error (exit code 3): Invalid JSON syntax at line {exc.lineno}, col {exc.colno}: {exc.msg}\n")
        return 3
    except Exception as exc:
        sys.stderr.write(f"IO error (exit code 3): Failed to read file '{manifest_path}': {exc}\n")
        return 3

    errors, normalized_manifest = validate_manifest(raw_data)

    if errors:
        if args.json:
            out_err = {
                "valid": False,
                "error_count": len(errors),
                "errors": [e.to_dict() for e in errors],
            }
            sys.stdout.write(json.dumps(out_err, indent=2, ensure_ascii=False) + "\n")
        else:
            sys.stderr.write(f"Validation FAILED (exit code 2): {len(errors)} error(s) found:\n")
            for err in errors:
                sys.stderr.write(f"  - {err}\n")
        return 2

    # Validation succeeded (exit code 0)
    formatted_json = json.dumps(normalized_manifest, indent=2, ensure_ascii=False)

    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as out_f:
                out_f.write(formatted_json + "\n")
        except Exception as exc:
            sys.stderr.write(f"IO error (exit code 3): Failed to write normalized manifest to '{args.out}': {exc}\n")
            return 3

    if not args.quiet:
        sys.stdout.write(formatted_json + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
