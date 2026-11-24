// W156 core Ghidra pass: authoritative xref model + decompilation of target functions.
// One headless run, -noanalysis. All output via println -> redirected log.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class W156Core extends GhidraScript {
    AddressFactory af;
    FunctionManager fm;
    ReferenceManager rm;
    DecompInterface di;

    void dumpRefs(long addr, String label) throws Exception {
        Address a = af.getDefaultAddressSpace().getAddress(addr);
        println("=== REFS @ " + label + " = " + a + " ===");
        ReferenceIterator it = rm.getReferencesTo(a);
        TreeMap<String,String> m = new TreeMap<String,String>();
        int n = 0, nr = 0, nw = 0, nc = 0, nd = 0;
        while (it.hasNext()) {
            Reference r = it.next();
            RefType rt = r.getReferenceType();
            Address from = r.getFromAddress();
            Function f = fm.getFunctionContaining(from);
            String fn = (f == null) ? "NOFUNC" : f.getEntryPoint().toString();
            String kind;
            if (rt.isRead())  { kind = "R"; nr++; }
            else if (rt.isWrite()) { kind = "W"; nw++; }
            else if (rt.isCall())  { kind = "C"; nc++; }
            else if (rt.isData())  { kind = "D"; nd++; }
            else kind = "?";
            String key = "  " + kind + " " + fn;
            String prev = m.get(key);
            m.put(key, (prev == null ? "" : prev) + " " + from);
            n++;
        }
        println(" total=" + n + " R=" + nr + " W=" + nw + " C=" + nc + " D=" + nd
                + " distinctFns=" + m.size());
        for (Map.Entry<String,String> e : m.entrySet()) {
            println(e.getKey() + " @" + e.getValue());
        }
    }

    void decomp(long addr) throws Exception {
        Address a = af.getDefaultAddressSpace().getAddress(addr);
        Function f = fm.getFunctionAt(a);
        if (f == null) f = fm.getFunctionContaining(a);
        println("=== DECOMP " + a + " ===");
        if (f == null) { println("  NO FUNCTION"); return; }
        println("  entry=" + f.getEntryPoint() + " size=" + f.getBody().getNumAddresses()
                + " name=" + f.getName());
        DecompileResults res = di.decompileFunction(f, 90, monitor);
        if (res == null || !res.decompileCompleted()) { println("  FAILED"); return; }
        println(res.getDecompiledFunction().getC());
    }

    public void run() throws Exception {
        af = currentProgram.getAddressFactory();
        fm = currentProgram.getFunctionManager();
        rm = currentProgram.getReferenceManager();
        di = new DecompInterface();
        di.openProgram(currentProgram);

        println("PROGRAM=" + currentProgram.getName() + " imageBase=" + currentProgram.getImageBase()
                + " funcTotal=" + fm.getFunctionCount());

        dumpRefs(0x00A8EB50L, "BuildingClass::Array.Count");
        dumpRefs(0x00A8EB44L, "BuildingClass::Array.Items");
        dumpRefs(0x0087F924L, "CellTable");
        dumpRefs(0x005687F0L, "DetachWrapper");
        dumpRefs(0x005683C0L, "AttachWrapper");
        dumpRefs(0x007E127CL, "HeapFree_IAT");
        dumpRefs(0x007E1278L, "HeapAlloc_IAT");

        long[] dec = {
            0x44FE60L, 0x452D40L, 0x44FEC0L, 0x452DC0L, 0x4533A0L,
            0x43B740L, 0x6D9B50L, 0x6D9CE0L, 0x47D210L,
            0x43F180L, 0x4D3780L, 0x71BFB0L, 0x4151E0L,
            0x7C93E8L, 0x7C946EL, 0x7CF77FL, 0x7CF7E8L, 0x7CFE1CL, 0x7D0F45L, 0x7D3374L, 0x7DCE3BL
        };
        for (long t : dec) decomp(t);
        println("W156Core DONE");
    }
}
