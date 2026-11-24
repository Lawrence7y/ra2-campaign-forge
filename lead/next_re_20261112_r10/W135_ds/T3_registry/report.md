# T3 — Is `0xB0F720` a complete `AbstractClass` registry?

## Verdict

```
INCOMPLETE
```

Reasoning summary:

- **No `AbstractClass` constructor registers.** The 5 function bodies that install AbstractClass's four vtables (`0x00410170`, `0x004101C0`, `0x004101F0`, `0x004105A0`, `0x006E8000`) encode no occurrence of `0xB0F720`/`24`/`28`/`30`/`34` at all.
- Across `.text` **23** distinct functions reference the registry block; **13** of them contain an inlined `AddItem` (+1) and/or `RemoveItem` (−1): 8 AddItem blocks, 5 RemoveItem blocks.
- The following functions are individually **unbalanced** (a constructor that removes, or a destructor that adds/removes twice): `0x00420960` [AlphaShapeClass]: AddItem x1 / RemoveItem x0; `0x00420AF0` [AlphaShapeClass]: AddItem x1 / RemoveItem x0; `0x00421730` [AlphaShapeClass]: AddItem x0 / RemoveItem x1; `0x004C98B0` [FactoryClass]: AddItem x1 / RemoveItem x0; `0x004CA770` [FactoryClass]: AddItem x0 / RemoveItem x1; `0x004F54A0` [HouseClass]: AddItem x1 / RemoveItem x0; `0x005F3900` [ObjectClass]: AddItem x1 / RemoveItem x0; `0x005F3B80` [ObjectClass]: AddItem x0 / RemoveItem x1; `0x0062DC50` [ParticleSystemClass]: AddItem x1 / RemoveItem x0; `0x0062DF20` [ParticleSystemClass]: AddItem x1 / RemoveItem x0; `0x0062E070` [ParticleSystemClass]: AddItem x0 / RemoveItem x1; `0x006E8A90` [TeamClass]: AddItem x1 / RemoveItem x0; `0x006E8DE0` [TeamClass]: AddItem x0 / RemoveItem x1.
- Classes reached from the `AbstractClass` chain, with the registry direction observed in the function that installs their own vtable: ObjectClass -> `0x005F3900` (push x1 / pop x0), `0x005F3B80` (push x0 / pop x1); TechnoClass -> `0x006F2B40` (push x0 / pop x0), `0x006F4300` (push x0 / pop x0).
- Concrete counter-example to completeness: `0x00421730` is an `AlphaShapeClass` constructor that installs all four `AlphaShapeClass` vtables, runs the field initialisation, and then performs an inline `RemoveItem` on `0xB0F720` (`dec ecx` @`0x4217BE`, `mov [0xB0F730], ecx` @`0x4217C1`) before returning — with **no** `AddItem` anywhere in the body. A construction path that only removes. The matching insertion happens only in `0x00420960`/`0x00420AF0`. `[已证]`
- `0x7258D0` does **not** mutate `Count`; it is a broadcast/notification helper that iterates the array and calls slot `+0x28` on each element. Counting it as a push site (as the 'Items once + Count thrice' heuristic would) is wrong. `[已证]`
- Independently of the above, `0xB0F720` is **not the only** `DynamicVectorClass<AbstractClass*>` in the process: **12** distinct globals are initialised with that exact vftable (`0x7E91EC`) by static initialisers, at `0xB0F5B8`, `0xB0F5D8`, `0xB0F5F0`, `0xB0F618`, `0xB0F640`, `0xB0F658`, `0xB0F670`, `0xB0F698`, `0xB0F6C8`, `0xB0F6F0`, `0xB0F708`, `0xB0F720`. Even a perfectly balanced `0xB0F720` would therefore count at most one of them. `[已证]`

## Evidence base

- Input SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` (matches the brief). `[已证]`
- 1394120 instructions decoded by linear sweep over the whole of `.text`. `[已证]`
- 143 instruction-anchored references to the registry block. `[已证]`
- `0xB0F720` is in the BSS tail (`.data` is file-backed only to `0x87E000`), so the vector's *contents* are permanently unobservable statically. All conclusions below are about the **code** that writes it. `[已证]`

## Method

1. Little-endian byte scan for `0xB0F720/24/28/2D/30/34` and `0x7E91EC` in `.text`, re-attributed to the instruction that encodes the immediate — anchored on linear-sweep instruction starts, never on `hit-k`.
2. `push` vs `pop` decided by the direction of the store into `[0xB0F730]`: find `mov [0xB0F730], reg`, walk backwards to the `inc`/`dec` producing `reg`.
3. Class attribution by MSVC RTTI on the vftable stored into `[obj]` in the same function.
4. Constructor analysis: every function installing ≥3 of AbstractClass's four vtables is a candidate `AbstractClass::AbstractClass`; check for registry immediates.

## Honest limits `[未证]`

- **Coverage is sampled, not exhaustive.** 23 distinct functions touch the registry block; 13 of them actually mutate `Count` (8 AddItem / 5 RemoveItem). We attributed every mutating site to a class, but we did **not** enumerate and decompile every concrete constructor in the engine to check whether it inlines `AddItem`. That is the one measurement that would turn this from "demonstrably incomplete" into a full census, and it is not done here.
- **Function boundaries.** Entries are direct `call` targets plus atlas entries that are preceded by padding (5 atlas entries were rejected as intra-function branch targets, e.g. `0x420C35`). A registry block could still belong to a helper reached only by fallthrough; we report each block inside the function that owns it up to its first `ret`, but a few attributions to a *specific* function name may be off by one.
- **`0x421730` is reached only through a vtable slot.** It has zero direct `call`ers, so it is a `scalar deleting destructor`-style thunk or a virtual member; its `pop` is real, but which call site reaches it is `[未证]`.
- **Heap-level behaviour is out of reach.** We can prove a code path increments or decrements `Count`; we cannot prove a given execution reaches it, nor what the array contains at runtime. The `[未证]` part is execution frequency and runtime content, not static direction.
- **The twelve sibling arrays are unstudied.** We establish that they exist and share the type; we did **not** determine which classes go into which array, nor whether the twelve are disjoint or overlapping. `[未证]`
- **`ObjectClass`'s ctor/dtor (`0x5F3900`/`0x5F3B80`) are balanced**, but `0x5F3B80` is a *destructor*, not a push site. Treating 'function references `Items` once and `Count` three times' as a push signature is **wrong**; direction must come from the `inc`/`dec` in front of the store. `[已证]`

