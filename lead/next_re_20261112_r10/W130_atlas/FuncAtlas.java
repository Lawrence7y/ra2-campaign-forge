// W130: FUNCTION ATLAS for gamemd.exe -- milestone (2) of the whole-program RE goal.
// @category W130
//
// For every function emit:
//   entry, size(bytes), n_instr, n_callers(direct call/jmp), n_callees,
//   is_vtable_slot (its entry appears as a dword in .rdata/.data),
//   strings: up to 3 distinct ASCII strings >=6 chars referenced from its body
//            (these are the cheapest semantic labels: "Starting scenario %s")
//   first_import: name of the first imported API it calls (if any)
//
// Output is TSV on stdout; the driver redirects it to function_atlas.tsv.
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.mem.*;
import java.util.*;

public class FuncAtlas extends GhidraScript {

    FunctionManager fm;
    ReferenceManager rm;
    Memory mem;
    Set<Long> fnptr = new HashSet<>();
    Map<Long, String> importNames = new HashMap<>();

    Address a(long va) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(va);
    }

    void buildFnPtrs() {
        for (MemoryBlock blk : mem.getBlocks()) {
            if (!blk.isInitialized()) continue;
            String n = blk.getName();
            if (!n.equals(".rdata") && !n.equals(".data")) continue;
            long s = blk.getStart().getOffset(), sz = blk.getSize();
            if (sz > 8_000_000L) sz = 8_000_000L;
            for (long o = 0; o + 4 <= sz; o += 4) {
                long v;
                try { v = mem.getInt(a(s + o)) & 0xffffffffL; } catch (Exception e) { continue; }
                if (v < 0x00401000L || v > 0x00900000L || (v & 3) != 0) continue;
                if (fm.getFunctionAt(a(v)) != null) fnptr.add(v);
            }
        }
    }

    void buildImportNames() {
        for (SymbolIterator si = currentProgram.getSymbolTable().getAllSymbols(true); si.hasNext(); ) {
            Symbol sym = si.next();
            Address ea = sym.getAddress();
            if (ea == null || !ea.isExternalAddress()) continue;
            importNames.put(ea.getOffset(), sym.getName());
        }
    }

    /** up to `cap` distinct printable strings referenced by this function's code. */
    List<String> stringsOf(Function f, int cap) {
        LinkedHashSet<String> out = new LinkedHashSet<>();
        for (Address src : f.getBody().getAddresses(true)) {
            Data d = getDataAt(src);
            if (d != null && d.hasStringValue()) {
                String s = d.getValue() == null ? null : d.getValue().toString();
                if (s != null && s.length() >= 6 && isPrintableAscii(s)) {
                    out.add(s.length() > 60 ? s.substring(0, 60) : s);
                    if (out.size() >= cap) break;
                }
            }
        }
        return new ArrayList<>(out);
    }

    boolean isPrintableAscii(String s) {
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c < 0x20 || c > 0x7E) return false;
        }
        return true;
    }

    String firstImport(Function f) {
        for (Address src : f.getBody().getAddresses(true)) {
            for (Reference r : rm.getReferencesFrom(src)) {
                Address to = r.getToAddress();
                if (to != null && to.isExternalAddress()) {
                    String n = importNames.get(to.getOffset());
                    if (n != null) return n;
                }
            }
        }
        return "";
    }

    public void run() throws Exception {
        fm = currentProgram.getFunctionManager();
        rm = currentProgram.getReferenceManager();
        mem = currentProgram.getMemory();
        buildFnPtrs();
        buildImportNames();
        println("### funcs=" + fm.getFunctionCount() + " fnptrs=" + fnptr.size()
                + " imports=" + importNames.size());
        println("entry\tsize\tn_instr\tn_callers\tn_callees\tis_fnptr\tfirst_import\tstrings");

        int done = 0;
        for (Function f : fm.getFunctions(true)) {
            long e = f.getEntryPoint().getOffset();
            long size = f.getBody().getNumAddresses();

            int nInstr = 0;
            InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
            while (it.hasNext()) { it.next(); nInstr++; }

            int nCallers = 0, nCallees = 0;
            for (Reference r : rm.getReferencesTo(f.getEntryPoint())) {
                if (r.getReferenceType().isCall() || r.getReferenceType().isJump()) nCallers++;
            }
            Set<Long> callees = new HashSet<>();
            it = currentProgram.getListing().getInstructions(f.getBody(), true);
            while (it.hasNext()) {
                Instruction ins = it.next();
                for (Reference r : ins.getReferencesFrom()) {
                    if (!r.getReferenceType().isCall()) continue;
                    Function tf = fm.getFunctionAt(r.getToAddress());
                    if (tf == null) tf = fm.getFunctionContaining(r.getToAddress());
                    if (tf != null) callees.add(tf.getEntryPoint().getOffset());
                }
            }
            nCallees = callees.size();

            List<String> ss = stringsOf(f, 3);
            String sjoin = String.join(" | ", ss).replace('\t', ' ').replace('\n', ' ');
            println(String.format("%08x\t%d\t%d\t%d\t%d\t%d\t%s\t%s",
                    e, size, nInstr, nCallers, nCallees,
                    fnptr.contains(e) ? 1 : 0, firstImport(f), sjoin));

            if ((++done % 1000) == 0) println("### progress " + done);
        }
        println("### DONE " + done);
    }
}
