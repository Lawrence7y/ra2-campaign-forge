import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.Program;
import ghidra.program.model.symbol.Reference;
import ghidra.program.model.symbol.ReferenceIterator;
import ghidra.program.model.symbol.RefType;

import java.util.ArrayList;
import java.util.List;

public class ClassId6 extends GhidraScript {

    private DecompInterface decomp;

    private void dumpDisasm(String tag, long a, int n) {
        Address ad = toAddr(a);
        println("== DISASM " + tag + " @ " + ad + " ==");
        Instruction i = currentProgram.getListing().getInstructionAt(ad);
        int c = 0;
        while (i != null && c < n) {
            println("  " + i.getAddress() + "  " + i.toString());
            i = currentProgram.getListing().getInstructionAfter(i.getAddress());
            c++;
        }
        if (c == 0) println("  <no instruction at this address>");
    }

    private void decompileFn(Function f) {
        if (f == null) { println("  <null function>"); return; }
        DecompileResults r = decomp.decompileFunction(f, 90, monitor);
        if (r != null && r.getDecompiledFunction() != null) {
            println("---- DECOMPILE " + f.getName() + " @ " + f.getEntryPoint() + " ----");
            println(r.getDecompiledFunction().getC());
        } else {
            println("---- DECOMPILE FAILED for " + f.getEntryPoint() + " ----");
        }
    }

    private void analyzeTarget(long siteAddr) {
        Address ad = toAddr(siteAddr);
        println("### SITE " + ad + " ###");
        dumpDisasm("site", siteAddr, 4);
        Function f = getFunctionContaining(ad);
        if (f == null) {
            println("  <no function containing site>");
            return;
        }
        println("  containing function: " + f.getName() + " entry=" + f.getEntryPoint()
                + " body=[" + f.getBody().getMinAddress() + ".." + f.getBody().getMaxAddress() + "]"
                + " size=" + f.getBody().getNumAddresses());
        decompileFn(f);
        // callers of this function
        ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(f.getEntryPoint());
        int ncallers = 0;
        List<Address> callSites = new ArrayList<Address>();
        while (refs.hasNext()) {
            Reference r = refs.next();
            if (r.getReferenceType().isCall()) {
                callSites.add(r.getFromAddress());
                ncallers++;
            }
        }
        println("  CALLER count: " + ncallers);
        for (Address cs : callSites) {
            Function cf = getFunctionContaining(cs);
            String cfname = (cf == null) ? "?" : cf.getName() + "@" + cf.getEntryPoint();
            // walk back up to 6 instructions looking for push imm32 (allocation size)
            String pushInfo = "";
            Instruction w = currentProgram.getListing().getInstructionBefore(cs);
            for (int k = 0; k < 6 && w != null; k++) {
                String mn = w.getMnemonicString();
                if (mn.equals("PUSH")) {
                    Object[] ops = w.getOpObjects(0);
                    if (ops.length == 1 && ops[0] instanceof ghidra.program.model.scalar.Scalar) {
                        long v = ((ghidra.program.model.scalar.Scalar) ops[0]).getValue();
                        pushInfo = " push=0x" + Long.toHexString(v) + "(" + v + ") before-call";
                        break;
                    }
                }
                w = currentProgram.getListing().getInstructionBefore(w.getAddress());
            }
            println("    caller site " + cs + "  in " + cfname + pushInfo);
        }
    }

    private void refsTo(long target) {
        Address ad = toAddr(target);
        println("### REFS TO " + ad + " ###");
        ReferenceIterator refs = currentProgram.getReferenceManager().getReferencesTo(ad);
        int n = 0;
        while (refs.hasNext()) {
            Reference r = refs.next();
            RefType t = r.getReferenceType();
            Function f = getFunctionContaining(r.getFromAddress());
            println("  from=" + r.getFromAddress() + " type=" + t
                    + (f == null ? "" : " fn=" + f.getName() + "@" + f.getEntryPoint()));
            n++;
        }
        println("  total=" + n);
    }

    @Override
    public void run() throws Exception {
        decomp = new DecompInterface();
        decomp.openProgram(currentProgram);
        println("FunctionCount=" + currentProgram.getFunctionManager().getFunctionCount());

        // A) the three vptr-write sites
        analyzeTarget(0x0043B721L);
        analyzeTarget(0x0043B9FCL);
        analyzeTarget(0x0043BCFFL);

        // B) references to primary and secondary vtable
        refsTo(0x007E3EBCL);
        refsTo(0x007E3EA0L);

        // C) secondary vtable neighborhood: dump pointer run 0x7E3E60..0x7E3F00
        println("### RAW DWORDS 0x7E3E60..0x7E3F00 ###");
        for (long a = 0x7E3E60L; a < 0x7E3F00L; a += 4) {
            Address ad = toAddr(a);
            Object v = currentProgram.getListing().getDataAt(ad);
            long val = getIntAt(ad);
            String tag = "";
            if (getFunctionAt(toAddr(val)) != null) tag = " FN";
            println("  " + ad + " : " + String.format("%08X", val) + tag);
        }

        // D) quick identity of a few vtable slots of class 6
        dumpDisasm("slot03_0x459E80", 0x00459E80L, 2);
        dumpDisasm("slot107_0x449440", 0x00449440L, 2);
        dumpDisasm("slot00_0x410260", 0x00410260L, 2);
        dumpDisasm("secondary_slot_0x410450", 0x00410450L, 2);

        // E) Lead's allocator call site context
        dumpDisasm("allocsite_0x7C8E17", 0x007C8E10L, 6);
        Function af = getFunctionContaining(toAddr(0x007C8E17L));
        println("alloc fn: " + (af == null ? "?" : af.getName() + "@" + af.getEntryPoint()));

        // F) whatami fns near 0x459EC0: 0x459E80/0x459ED0/0x459EE0/0x459EF0 disasm 2 each
        dumpDisasm("0x459ED0", 0x00459ED0L, 2);
        dumpDisasm("0x459EE0", 0x00459EE0L, 2);
        dumpDisasm("0x459EF0", 0x00459EF0L, 2);

        decomp.dispose();
    }

    private long getIntAt(Address ad) {
        try {
            ghidra.program.model.mem.Memory mem = currentProgram.getMemory();
            return mem.getInt(ad) & 0xFFFFFFFFL;
        } catch (Exception e) {
            return 0;
        }
    }
}
