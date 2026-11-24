// W157: comprehensive independent probe for the 0x67D300 ruling.
// Dumps: full disassembly (bytes+mnemonic+operands+resolved call/data refs+backedge marks),
//        unique strings, unique callees, backedge count, and xrefs for key targets.
// @category W157
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import ghidra.program.model.symbol.*;
import java.util.*;

public class W157Dump extends GhidraScript {
    Address addr(long v) {
        return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v);
    }
    String hexbytes(Instruction ins) {
        StringBuilder sb = new StringBuilder();
        try {
            for (byte b : ins.getBytes()) sb.append(String.format("%02x", b & 0xff));
        } catch (Exception e) { return "??"; }
        return sb.toString();
    }
    String ops(Instruction ins) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < ins.getNumOperands(); i++) {
            if (i > 0) sb.append(",");
            sb.append(ins.getDefaultOperandRepresentation(i));
        }
        return sb.toString();
    }
    // NUL-terminated printable ASCII string at address a (up to 256 bytes)
    String readAscii(Address a) {
        try {
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < 256; i++) {
                int b = currentProgram.getMemory().getByte(a.add(i)) & 0xff;
                if (b == 0) break;
                if (b < 0x20 || b >= 0x7f) return null;
                sb.append((char) b);
            }
            return sb.length() >= 2 ? sb.toString() : null;
        } catch (Exception e) { return null; }
    }
    void dumpFn(long entry, String label) throws Exception {
        FunctionManager fm = currentProgram.getFunctionManager();
        Function f = fm.getFunctionAt(addr(entry));
        if (f == null) {
            f = fm.getFunctionContaining(addr(entry));
            println("### " + label + " requested=" + String.format("%08x", entry)
                    + " -> (not an entry) containing=" + (f == null ? "NULL" : f.getEntryPoint().toString()));
        } else {
            println("### " + label + " requested=" + String.format("%08x", entry) + " -> exact entry");
        }
        if (f == null) { println("### " + label + " NO FUNCTION"); return; }
        println("### " + label + " ACTUAL_ENTRY=" + f.getEntryPoint().getOffset()
                + " SIZE=" + f.getBody().getNumAddresses() + " PARAMS=" + f.getParameterCount());
        InstructionIterator it = currentProgram.getListing().getInstructions(f.getBody(), true);
        int nback = 0;
        Set<String> strings = new LinkedHashSet<String>();
        Set<String> callees = new LinkedHashSet<String>();
        while (it.hasNext()) {
            Instruction ins = it.next();
            StringBuilder sb = new StringBuilder();
            sb.append(ins.getAddress()).append("  ")
              .append(String.format("%-22s", hexbytes(ins))).append("  ")
              .append(String.format("%-8s", ins.getMnemonicString())).append("  ")
              .append(ops(ins));
            for (Reference r : ins.getReferencesFrom()) {
                Address t = r.getToAddress();
                if (t == null) continue;
                if (r.getReferenceType().isCall()) {
                    Function tf = fm.getFunctionAt(t);
                    sb.append("  ;CALL->").append(t);
                    if (tf != null) sb.append("(sz=").append(tf.getBody().getNumAddresses()).append(")");
                    callees.add(t.toString() + (tf == null ? "" : (" sz=" + tf.getBody().getNumAddresses())));
                } else {
                    String s = readAscii(t);
                    sb.append("  ;DATA->").append(t);
                    if (s != null) { sb.append(" \"").append(s).append("\""); strings.add(t + "=\"" + s + "\""); }
                }
            }
            String mn = ins.getMnemonicString().toLowerCase();
            if (mn.startsWith("j") || mn.startsWith("loop")) {
                Address[] flows = ins.getFlows();
                for (Address t : flows) {
                    if (t.getOffset() <= ins.getAddress().getOffset()) {
                        sb.append("  ;BACKEDGE->").append(t);
                        nback++;
                        break;
                    }
                }
            }
            println(sb.toString());
        }
        println("### " + label + " BACKEDGE_ASM_COUNT=" + nback);
        println("### " + label + " STRINGS(" + strings.size() + "):");
        for (String s : strings) println("###   STR " + s);
        println("### " + label + " CALLEES(" + callees.size() + "):");
        for (String c : callees) println("###   CALL " + c);
    }
    void xrefs(long target, String label) {
        println("### XREFS->" + label + " (" + String.format("%08x", target) + ")");
        ReferenceIterator ri = currentProgram.getReferenceManager().getReferencesTo(addr(target));
        int cnt = 0;
        while (ri.hasNext()) {
            Reference r = ri.next();
            println("###   from=" + r.getFromAddress() + " type=" + r.getReferenceType()
                    + " primary=" + r.isPrimary());
            cnt++;
        }
        println("### XREFS->" + label + " COUNT=" + cnt);
    }
    public void run() throws Exception {
        println("### IMAGEBASE=" + currentProgram.getImageBase());
        // big functions
        dumpFn(0x0067D300L, "FN_67D300");
        dumpFn(0x0067CEF0L, "FN_67CEF0");
        // small / semantic anchors
        dumpFn(0x005F6250L, "FN_5F6250");
        dumpFn(0x004A1D50L, "FN_4A1D50");
        dumpFn(0x004A1CA0L, "FN_4A1CA0");
        dumpFn(0x00680F70L, "FN_680F70");
        dumpFn(0x007DC720L, "FN_7DC720");
        dumpFn(0x00410410L, "FN_410410");
        // caller containing 0x67D1AF
        Function cf = currentProgram.getFunctionManager().getFunctionContaining(addr(0x0067D1AFL));
        if (cf != null) dumpFn(cf.getEntryPoint().getOffset(), "FN_CALLER_67D1AF");
        // xrefs
        xrefs(0x0067D300L, "67D300");
        xrefs(0x0067CEF0L, "67CEF0");
        xrefs(0x005F6250L, "5F6250");
        println("### DONE");
    }
}
