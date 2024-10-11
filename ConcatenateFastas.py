#importing Biopython
import Bio
import os
#import seqIO to parse through sequence files
from Bio import SeqIO
#imports for writing fasta files
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
#get the list of enriched protein sequences and parse through it with
#the SeqIO parse function
SIZ1Truncated = SeqRecord(Seq("""KVRCVCGNSLETDSMIQCEDPRCHVWQHVGCVILPDKPMDGNPPLPESFYCEICRLTRADPFWVTVAHPLSPVRLTATTIPNDGASTMQSVERTFQITRADKDLLAKPEYDVQAWCMLLNDKVLFRMQWPQYADLQVNGVPVRAINRPGGQLLGVNGRDDGPIITSCIRDGVNRISLSGGDVRIFCFGVRLVKRRTLQQVLNLIPEEGKGETFEDALARVRRCIGGGGGDDNADSDSDIEVVADFFGVNLRCPMSGSRIKVAGRFLPCVHMGCFDLDVFVELNQRSRKWQCPICLKNYSVEHVIVDPYFNRITSKMKHCDEEVTEIEVKPDGSWRVKFKRESERRELGELSQWHAPDGSLC"""),
                 id="AT5G60410", name="SIZ1Truncated")

#Warning: before running these next lines make sure to be in the final destination directory
os.chdir('/global/scratch/users/enricocalvane/SIZ1/fastas')
for seq_record in SeqIO.parse("SIZ1set.fasta", "fasta"):
    newseq=seq_record.seq.replace("*", "")
    comb=SIZ1Truncated.seq+":"+newseq
    combname=SIZ1Truncated.id+"_"+seq_record.id
    os.system(f"mkdir {combname}")
    with open (combname + "/" + combname + ".fasta", "w") as o:
        o.write(f">{combname}\n{comb}")

    
