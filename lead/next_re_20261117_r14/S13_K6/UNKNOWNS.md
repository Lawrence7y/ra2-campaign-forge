# S13-K6 UNKNOWNS

- U1: 4 provable-looking DynamicVectorClass rows were not delivered: 0040F630/0040FC00 (slot6) and 0054E8F0/0062B0D0 (slot1). They remain [静态推断]; 45 was the assigned target and no placeholder padding was added.
- U2: Exact same-vtable virtual callers were found for slot2/4 families with a global-array anchor; slot0/1/3/5 rows use a graded slot-dispatch baseline (call [reg+slot*4] in a [已证] owner outside this batch). This is strong structural reachability, not a per-object dataflow proof for every slot; see EVIDENCE/ring4_callsites.txt and slot_call_baseline.txt.
- U3: UDamage (0x7E5170) and Kamikaze (0x7ECE7C) have no usable global-array xref owner in coverage for exact slot2/4 anchoring; their rows use the graded slot baseline only.
- U4: 92 VectorClass/vslot rows remain unresolved here. They have RTTI, but inherited-base slots and exact call ownership need separate work; they are not counted.
- U5: S13-K5 D1 denominator dispute remains open: if container templates are migrated to S22, the 240-denominator claim must be recomputed by Lead.
- U6: coverage.tsv was not modified; post-delta 120/240 is a simulation from live col5 plus this delta. Verify with work/base.py and EVIDENCE/baseline_recompute.txt.
