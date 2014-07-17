import re
import sys
import gzip

def average_depth(cov_summary):
        '''
        Get average depth for the entire genome.
        '''

        avg_depth = 0
        r = open(cov_summary, 'r')
        for line in r:
                if re.search("average_depth:\s+([0-9|\.]+)", line): 
                        avg_depth = re.search("average_depth:\s+([0-9|\.]+)", line).group(1)
                        avg_depth = float(avg_depth)
        r.close()
        
        return avg_depth

def ditched_sites(genome, cov_data, avg_depth):
        '''
        Get depth file and figure out ditched
        Uh oh! this assumes that the file starts with 'chr1'
                need to make it smarter
        '''

        ditch = dict()
        for chr in genome:
                ditch[chr] = dict()
        r = open(cov_data, 'r')
        cur_pos = 0
        cur_chr = 'chr1'
        for line in r:
                d = re.split("\t", line)
        
                if d[0] in genome:
                        d[1] = int(d[1])
                        d[2] = float(d[2])
			
                        # this super kludgy section accounts for the small portion 
                        #       of sites that never got called for depth ... maybe 
                        #       because never a single read got mapped?
                        if d[0] == cur_chr:
                                if d[1] - cur_pos > 1:
                                        for i in range(cur_pos + 1, d[1]):
                                                ditch[d[0]][i] = 1
                        else:
                                print "ditch %s" % cur_chr

                        cur_pos = d[1] 
                        cur_chr = d[0]
                        if (d[2] < 0.5 * avg_depth) or (d[2] > 2 *avg_depth):
                                ditch[d[0]][d[1]] = 1
        r.close()
        return ditch

def get_mendel(genome, mendel_file):
        '''
        Get positions that are in Mendelian error.
        '''

        me = dict()
        for chr in genome:
                me[chr] = dict() 
        if mendel_file:
                r = open(mendel_file, 'r')
                for line in r:
                        if re.search('^(\S+)\s+(\S+)', line):
                                match = re.search('^(\S+)\s+(\S+)', line)
                                me[ match.group(1) ][int( match.group(2) )] = 1
                r.close()
        return me


def print_filtered_vcf(out_dir, vcf_file, ditch, me):
	
	r = gzip.open(vcf_file, 'r')
	cur_chr = 'NA'
	out_file = ''
	header = []

	for line in r:
		if re.search('^#', line):
			header.append(line)
		else:
			d = re.split('\t', line)
			if d[0] != cur_chr:
				if out_file:
					o.close()
				out_file = '%sgatk.ug.zf_fam.%s.variable.coverage.vqsr.vcf.gz' % (out_dir, d[0])
				o = gzip.open(out_file, 'w')
				for head in header:
					o.write(head)
			cur_chr = d[0]
			d[1] = int(d[1])
			if d[1] not in ditch[cur_chr]:
				if d[1] not in me[cur_chr]:
					o.write(line)
	r.close()
	return
					

def main():     
        '''
        Running all the subroutines.
        Currently requires editing of script for different runs ... will port to ArgParser if necessary.
        Note that this script is slow and requires a lot of memory ~20 g.
        '''
        
        # vcf file with FILTERED variants only
	# assumed to be gzipped
	vcf_file = '/mnt/lustre/home/sonal.singhal1/ZF/phasing/family_approach/family_vcf/gatk.ug.MP1-5.allchrs.snps.indels.vqsr.variable.vcf.gz'
 
        # file with coverage summary, created by 'get_average_depth.pl'
        cov_summary = '/mnt/lustre/home/sonal.singhal1/ZF/masked_genome/zebrafinch_depth_summary.txt'
        # file with average coverage data, created by 'get_average_depth.pl'
        cov_data = '/mnt/lustre/home/sonal.singhal1/ZF/masked_genome/zebrafinch_avg_depth.txt' 

	# file with mendel errors
	mendel_file = '/mnt/gluster/home/emleffler/genotype_callsets/zebrafinch/zf_family/unified_genotyper/after_vqsr/mendelian_errors/gatk.ug.MP1-5.allchrs.vqsr.filtered.allsites.with.errors.positions'

        # out directory      
	out_dir = '/mnt/lustre/home/sonal.singhal1/ZF/phasing/family_approach/family_vcf/by_chr/'

        # chromosome names
        chrs = [ 'chr1', 'chr1A', 'chr1B', 'chr2', 'chr3', 'chr4', 'chr4A', 'chr5', 'chr6', 'chr7', 'chr8',
		 'chr9', 'chr10', 'chr11', 'chr12', 'chr13', 'chr14', 'chr15', 'chr16', 'chr17', 'chr18',
                 'chr19', 'chr20', 'chr21', 'chr22', 'chr23', 'chr24', 'chr25', 'chr26', 'chr27', 'chr28',
                 'chrLG2', 'chrLG5', 'chrLGE22', 'chrZ', 'chrM']
	
	avg_depth = average_depth(cov_summary)
	ditch = ditched_sites(chrs, cov_data, avg_depth) 
	me = get_mendel(chrs, mendel_file)
	print_filtered_vcf(out_dir, vcf_file, ditch, me)

if __name__ == "__main__":
        main()

