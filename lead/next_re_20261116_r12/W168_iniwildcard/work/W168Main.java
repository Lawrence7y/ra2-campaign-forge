// W168 main: double-channel xrefs (Ghidra side) + decompile enumeration fns, INI loader, callers.
// @category W168
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;

public class W168Main extends GhidraScript {
    Address va(long v) { return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v); }
    void xrefs(long t, String label) throws Exception {
        Address a = va(t);
        println("### XREFSTO " + label + " @ " + a + " ###");
        ReferenceIterator it = currentProgram.getReferenceManager().getReferencesTo(a);
        int n = 0;
        java.util.LinkedHashSet<Long> fns = new java.util.LinkedHashSet<Long>();
        while (it.hasNext()) {
            Reference r = it.next();
            Address from = r.getFromAddress();
            Function cf = currentProgram.getFunctionManager().getFunctionContaining(from);
            Instruction ins = currentProgram.getListing().getInstructionContaining(from);
            String insstr = (ins==null? "?" : ins.getAddress()+": "+ins.toString());
            println("   ref@" + from + " type=" + r.getReferenceType()
                    + " in=" + (cf==null? "?" : cf.getEntryPoint()+" "+cf.getName())
                    + " insn=" + insstr);
            if (cf!=null) fns.add(cf.getEntryPoint().getOffset());
            n++;
        }
        if (n==0) println("   (none)");
        println("   total=" + n + " distinct_fns=" + fns.size());
        for (Long f : fns) println("   fnset " + va(f.longValue()));
        println("");
    }
    void dumpFn(long t, int cap) throws Exception {
        Address a = va(t);
        Function f = currentProgram.getFunctionManager().getFunctionAt(a);
        if (f==null) { println("=== no fn at " + a + " ==="); return; }
        println("=== FN " + a + " " + f.getName() + " size=" + f.getBody().getNumAddresses() + " ===");
        DecompInterface di = new DecompInterface(); di.openProgram(currentProgram);
        DecompileResults r = di.decompileFunction(f, 120, monitor);
        if (r==null || !r.decompileCompleted()) { println("   decompile FAILED"); return; }
        int k=0;
        for (String ln : r.getDecompiledFunction().getC().split("\n")) {
            println("C| " + ln);
            if (++k>cap) { println("C| ...TRUNCATED"); break; }
        }
        println("=== END FN " + a + " ===");
    }
    public void run() throws Exception {
        println("imageBase=" + currentProgram.getImageBase());
        println("funcTotal=" + currentProgram.getFunctionManager().getFunctionCount());
        println("========== PART 1: XREFS (Ghidra channel) ==========");
        xrefs(0x008261A8L, "BATTLEMD*.INI");
        xrefs(0x0082626CL, "RULEMD*.INI");
        xrefs(0x00826198L, "BATTLEMD.INI");
        xrefs(0x00826260L, "RULESMD.INI");
        // IAT slots - who calls them
        xrefs(0x007E1208L, "IAT FindFirstFileA");
        xrefs(0x007E120CL, "IAT FindNextFileA");
        xrefs(0x007E1300L, "IAT FindClose");

        println("========== PART 2: ENUM FNS ==========");
        dumpFn(0x0052CB90L, 320);   // BATTLE
        dumpFn(0x0052CD70L, 340);   // RULE

        println("========== PART 3: INI LOAD / FILE OPEN ==========");
        dumpFn(0x004739F0L, 200);   // set INI filename / open wrapper
        dumpFn(0x004741F0L, 320);   // parse INI into object
        dumpFn(0x007C8D20L, 90);    // stricmp (RULE base-file ordering)

        println("========== PART 4: CALLERS OF THE TWO ENUM FNS ==========");
        // xrefs to function entries == callers
        xrefs(0x0052CB90L, "fn 0x52CB90 (BATTLE enum)");
        xrefs(0x0052CD70L, "fn 0x52CD70 (RULE enum)");
        long[] callers = { 0x0052C605L, 0x0052DF25L, 0x0052E0C4L, 0x00685609L, 0x0052C95CL };
        for (long c : callers) dumpFn(c, 90);
        println("========== DONE ==========");
    }
}
