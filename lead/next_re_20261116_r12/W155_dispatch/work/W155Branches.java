// W155: branch/back-edge dump using textual operands (independent of getOpObjects).
// @category W155
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.*;
import java.util.*;
import java.util.regex.*;

public class W155Branches extends GhidraScript {
    Address addr(long v){ return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(v); }

    int countBack(long v){
        Function f=currentProgram.getFunctionManager().getFunctionAt(addr(v));
        if(f==null) return -1;
        int n=0;
        InstructionIterator it=currentProgram.getListing().getInstructions(f.getBody(),true);
        Pattern p=Pattern.compile("(0x[0-9a-fA-F]+)");
        while(it.hasNext()){
            Instruction ins=it.next();
            String m=ins.getMnemonicString().toLowerCase();
            if(!(m.startsWith("j")||m.startsWith("loop"))) continue;
            String s=ins.toString().toLowerCase();
            Matcher mt=p.matcher(s);
            long at=ins.getAddress().getOffset();
            while(mt.find()){
                try{
                    long t=Long.parseLong(mt.group(1).substring(2),16);
                    if(t<=at){ n++; println("  BACK 0x"+Long.toHexString(at)+" "+m+" -> 0x"+Long.toHexString(t)+"  | "+s); break; }
                }catch(Exception e){}
            }
        }
        return n;
    }
    public void run() throws Exception {
        println("W155BR start");
        long[] fs={0x4666E0L,0x427CB0L,0x468D80L,0x47C3D0L,0x47C520L,0x480510L,0x65FA70L,0x5B20F0L,0x55AFB0L,0x55D360L};
        for(long f:fs) println("FN 0x"+Long.toHexString(f)+" backEdges="+countBack(f));
        println("W155BR done");
    }
}
