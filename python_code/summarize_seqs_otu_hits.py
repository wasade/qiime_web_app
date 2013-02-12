from os import listdir, getcwd
from os.path import isdir, join, exists
from qiime.util import get_qiime_scripts_dir, load_qiime_config
from subprocess import Popen, PIPE, STDOUT

def get_processed_data_dirs(study_dir):
    """ Returns a list of processed_data_ directories for a study_dir
    """
    processed_data_dirs = []
    prefix = 'processed_data_'
    
    for name in listdir(study_dir):
        #print name
        if name.startswith(prefix):
            processed_data_dirs.append(name)

    return processed_data_dirs

def parse_log_file(log_path, start_lines):
    """ Parses one of several log files produced in the qiime pipeline. Returns 
        aggregated counts of either seqs per sample or otus per sampe. A factory
        method derivitave.
    """

    summary_dict = {}
    header_lines = []
    start_read = False
    debug = True
    
    if debug:
    	print log_path

    log = open(log_path, 'U')
    
    for l in log:
        l = l.strip()
        header_lines.append(l)

        #if debug:
        #    print l

        if not start_read:            
            for start_line in start_lines:
                if l.startswith(start_line):
                    if debug:
                        print 'Start line found: {0}'.format(start_line)
                    start_read = True
            continue

        # Exit read loop when we reach end of sample list
        if l == '' or l == None:
            break

        # Start reading samples
        items = l.split()
        if len(items) < 2:
            continue

        sample_name = items[0]
        if sample_name.endswith(':'):
            sample_name = sample_name[:-1]
        count = items[1]
        summary_dict[sample_name] = count

    log.close()

    return header_lines, summary_dict 

def summarize_seqs(processed_dir):
    """ 
    """
    log_path = join(processed_dir, 'split_libraries/split_library_log.txt')
    start_lines = []
    start_lines.append('Median sequence length:')
    start_lines.append('Sample\tSequence Count\tBarcode')
    header_lines, seq_summary_dict = parse_log_file(log_path, start_lines)
    return header_lines, seq_summary_dict

def summarize_otus(processed_dir):
    """
    """
    per_library_stats_file = join(processed_dir, 'gg_97_otus/per_library_stats.txt')

    # Generate the per_library_stats_file if it doesn't already exist
    if not exists (per_library_stats_file):
        qiime_config = load_qiime_config()
        biom_file = join(processed_dir, 'gg_97_otus/exact_uclust_ref_otu_table.biom')
        python_exe_fp = qiime_config['python_exe_fp']
        script_dir = get_qiime_scripts_dir()
        per_library_stats_script = join(script_dir, 'per_library_stats.py')
        command = '{0} {1} -i {2}'.format(python_exe_fp, per_library_stats_script, biom_file)

        # Run the script and produce the per_library_stats.txt
        proc = Popen(command, shell = True, universal_newlines = True, stdout = PIPE, stderr = STDOUT)
        return_value = proc.wait()
        f = open(per_library_stats_file, 'w')
        f.write(proc.stdout.read())
        f.close()

    # File exists, parse out details
    start_lines = ['Seqs/sample detail:']
    header_lines, otu_summary_dict = parse_log_file(per_library_stats_file, start_lines)
    return header_lines, otu_summary_dict

def summarize_all_stats(study_id):
    """
    """

    # Get the processed data directories
    study_dir = 'study_{0}'.format(study_id)
    study_dir = join('/home/wwwuser/user_data/studies/', study_dir)
    processed_data_dirs = get_processed_data_dirs(study_dir)

    #print str(processed_data_dirs)

    # For each processed data folder, get the seq and otu sumamries
    for processed_dir in processed_data_dirs:
        seq_header_lines, seq_summary_dict = summarize_seqs(join(study_dir, processed_dir))
        otu_header_lines, otu_summary_dict = summarize_otus(join(study_dir, processed_dir))

        # Create the tuples
        mapping = []
        for sample_name in seq_summary_dict:
            sequence_count = seq_summary_dict[sample_name]
            otu_count = None
            percent_assignment = None

            if sample_name in otu_summary_dict:
                otu_count = otu_summary_dict[sample_name]
                percent_assignment = (float(otu_count) / float(sequence_count)) * 100.0

            mapping.append((sample_name, sequence_count, otu_count, percent_assignment))

        return mapping, seq_header_lines, otu_header_lines


