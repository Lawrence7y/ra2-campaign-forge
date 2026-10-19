"""Extract interesting files from game MIX archives by content sniffing."""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from ra2forge.mixlib import MixFile  # noqa: E402


def looks_like_ini(data: bytes) -> bool:
    head = data[:64].lstrip()
    return head.startswith(b"[") or head.startswith(b";") or b"[General]" in data[:512]


def main(mix_path: str, out_dir: str, mode: str = "all"):
    out_root = (PROJECT_ROOT / out_dir).resolve()
    # keep extraction strictly inside the project tree
    if not str(out_root).startswith(str(PROJECT_ROOT.resolve())):
        raise ValueError("output dir must stay inside project")
    out_root.mkdir(parents=True, exist_ok=True)
    m = MixFile(mix_path)
    print(f"{mix_path}: {len(m.entries)} entries, data_start={m.data_start}")
    n_text = n_map = 0
    for e in m.entries:
        if e.size == 0 or e.size > 3_000_000:
            continue
        head = m.read_entry(e)
        if not (looks_like_ini(head) or head[:1] == b";"):
            continue
        data = m.read_entry(e)
        name = None
        if b"[Basic]" in data[:4096] and (b"IsoMapPack5" in data[:20000] or b"[Map]" in data[:2000]):
            name = f"map_{e.id:08X}.map"
            n_map += 1
        elif mode == "all" or b"campaign" in data[:2048].lower():
            name = f"ini_{e.id:08X}.ini"
            n_text += 1
        if name:
            (out_root / name).write_bytes(data)
    print(f"saved maps={n_map} ini={n_text} -> {out_root}")
    m.close()


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "all")
