// W134: explain the persistent 370-entry gap in the function manager.
// @category W134
//
// The atlas recorded, twice and independently:
//     getFunctionCount()      = 8948  while getFunctions(true) enumerates 8578
//     after creating 4333 more functions:
//     getFunctionCount()      = 13286 while getFunctions(true) enumerates 12916
// i.e. the difference is 370 both times -- systematic, not a bug in the export.
//
// Hypothesis: getFunctionCount() counts functions in ALL address spaces of the
// program, whereas the getFunctions(...) iterator only walks the default space.
// Note that `getFunctions(true)`'s argument is the iteration DIRECTION, not
// "include externals" -- a point that was misread when the gap was first logged
// (the export reported external=0, which is only possible if the iterator
// skips the EXTERNAL space entirely).
//
// This script settles it by counting, explicitly and separately:
//   - the manager total,
//   - what the plain iterator yields,
//   - externals via getExternalFunctions(),
//   - the address space of every function it can see,
//   - every address space the program has at all.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.util.*;

public class GapProbe extends GhidraScript {

    public void run() throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();

        int total = fm.getFunctionCount();

        int enumN = 0, ext = 0, thunk = 0, noBody = 0, noBodyNonExt = 0;
        Map<String, Integer> bySpace = new TreeMap<>();
        for (Function f : fm.getFunctions(true)) {
            enumN++;
            Address ep = f.getEntryPoint();
            String sp = ep.getAddressSpace().getName();
            bySpace.put(sp, bySpace.getOrDefault(sp, 0) + 1);
            boolean isExt = f.isExternal();
            if (isExt) ext++;
            if (f.isThunk()) thunk++;
            if (f.getBody() == null) {
                noBody++;
                if (!isExt) noBodyNonExt++;
            }
        }

        int extFns = 0;
        Set<String> extSpaces = new TreeSet<>();
        Map<String, Integer> extBySpace = new TreeMap<>();
        for (Function f : fm.getExternalFunctions()) {
            extFns++;
            String sp = f.getEntryPoint().getAddressSpace().getName();
            extSpaces.add(sp);
            extBySpace.put(sp, extBySpace.getOrDefault(sp, 0) + 1);
        }

        println("### getFunctionCount()            = " + total);
        println("### enumerated getFunctions(true) = " + enumN);
        println("### GAP                          = " + (total - enumN));
        println("### isExternal among enumerated   = " + ext);
        println("### isThunk among enumerated      = " + thunk);
        println("### getBody()==null (all)         = " + noBody);
        println("### getBody()==null (non-external)= " + noBodyNonExt);
        println("### getExternalFunctions().size   = " + extFns);
        println("### external spaces seen          = " + extSpaces);
        println("### external funcs by space       = " + extBySpace);

        List<String> spaces = new ArrayList<>();
        for (AddressSpace sp : currentProgram.getAddressFactory().getAddressSpaces()) {
            spaces.add(sp.getName() + "(type=" + sp.getType() + ","
                    + sp.getMinAddress() + ".." + sp.getMaxAddress() + ")");
        }
        println("### enumerate-by-space            = " + bySpace);
        println("### all address spaces           = " + spaces);

        // the decisive comparison
        int gap = total - enumN;
        println("### VERDICT gap==externals       = " + (gap == extFns));
        if (gap == extFns) {
            println("### => the 370 are the program's EXTERNAL (import) functions,");
            println("###    which getFunctionCount() includes but the iterator skips.");
        } else {
            println("### => externals do NOT explain the gap; " + gap
                    + " vs " + extFns + " external. Needs another explanation.");
        }
        println("### DONE");
    }
}
