# S10-K11 progress
- Read-at: 2026-11-18T05:45:52+08:00; source S10_K8F/coverage_delta.tsv SHA-256 9b430c0d55b8f19c8b011b5fe11c6f97430a7b8c8f9b7de30aaacb4d8f471d67; merged COVERAGE/coverage.tsv SHA-256 9ef239c22f5c100e3a5ac65e83fafa15ca44cd626c591465c195ecfb496eec94.
- On-disk check at that time: 004DFCB0 name=AircraftClass::QueueMissionId8_NearHouseFilter_behavior grade=[已证]; 004DFE00 name=AircraftClass::QueueMissionId8_NearGlobalFilter_behavior grade=[已证]; merged file agrees.
- Independent disassembly: capstone 5.0.7 (skipdata=True) + pefile 2024.8.26; target SHA-256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476; Ghidra not used.
- 004DFE00 byte evidence @004DFF00: 8b8ea4050000 c6869106000001 3bc8 7509 83beac00000008 741b => cmp ecx,eax; jne; only then cmp [this+0xAC],8; je skip => AND, not OR.
- 004DFCB0 byte evidence @004DFDBA: 8b8ea4050000 c6869006000001 3bc8 7509 83beac00000008 741b => same AND; this skip condition was missing in the disk wording.
- Best-pointer trace: 004DFCF3/004DFD96/004DFDA1 (House list) and 004DFE36/004DFED4/004DFEE7 (global list) put the selected candidate into eax at the compare.
- Wording changes only: DFE00 "or cur==8" -> "and [this+0xAC]==8"; DFCB0 gained the same skip clause. All other 8 fields kept byte-identical.
- coverage_delta.tsv: exactly 2 rows, 9 columns, disk order (004DFCB0, 004DFE00), no header.
- DISAGREE.md: N/A (no disagreement; no no_change row). Game files untouched; no ledger; no git commit.
