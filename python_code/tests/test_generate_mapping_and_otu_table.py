#!/usr/bin/env python
# File created on 19 Apr 2011
from __future__ import division

__author__ = "Jesse Stombaugh"
__copyright__ = "Copyright 2011, The QIIME-webdev project"
__credits__ = ["Jesse Stombaugh"]
__license__ = "GPL"
__version__ = "1.2.1-dev"
__maintainer__ = "Jesse Stombaugh"
__email__ = "jesse.stombaugh@colorado.edu"
__status__ = "Development"
 

from cogent.util.unit_test import TestCase, main
from os.path import join, splitext, abspath
from os import listdir, remove, environ
from shutil import rmtree
import time
from biom.parse import parse_biom_table
from qiime.parse import parse_mapping_file
from qiime.util import create_dir,get_tmp_filename
from data_access_connections import data_access_factory
from enums import ServerConfig
from generate_mapping_and_otu_table import (combine_map_header_cols,
                                           get_mapping_data,
                                           write_mapping_and_otu_table,
                                           write_otu_table,
                                           zip_and_add_filepaths,
                                           rarefy_otu_table,
                                           check_job_state_id)

class TopLevelTests(TestCase):
    """Tests of top-level functions"""

    def setUp(self):
        self._paths_to_clean_up = []
        self._folders_to_cleanup = []
        
        self.map = [['SampleID','BarcodeSequence','LinkerPrimerSequence',
                     'Description'],['Sample1','AA','GGCC','Test1'],
                     ['Sample2','CC','AAGG','Test2']]
        self.data_access = data_access_factory(ServerConfig.data_access_type)
        self.is_admin = True
        self.user_id = 12171 # This is Jesse Stombaugh's user_id
        self.table_col_value = \
            {'SAMPLE####SEP####COUNTRY####STUDIES####0': '####ALL####',
            'STUDY####SEP####STUDY_ID####STUDIES####0': '####ALL####'}
        
        self.fs_fp = '%s/tmp/' % (environ['HOME'])
        create_dir(self.fs_fp)
        self.web_fp = 'http://test'
        self.file_name_prefix = 'test'
        self.meta_id = 0
        self.rarefied_at = 0
        self.otutable_rarefied_at = None
        self.jobs_to_start = 'showTE,bdiv,sumtaxa,heatmap'
        self.tax_name = 'PHPR'
        self.tree_fp = '%s/software/gg_otus_4feb2011/trees/gg_97_otus_4feb2011.tre' % (environ['HOME'])
        self.samples_list=['test.PCx354.630848','test.PCx355.630846',
                           'test.PCx636.630852','test.PCx481.630849',
                           'test.PCx635.630853','test.PCx356.630847',
                           'test.PCx634.630850','test.PCx593.630851', 
                           'test.PCx607.630845']
        self.tmp_prefix = 'test'
        
        # create directory
        self.heatmap_dir = join(self.fs_fp,'heatmap')
        create_dir(self.heatmap_dir)
        self._folders_to_cleanup.append(self.heatmap_dir)
        self.bdiv_dir = join(self.fs_fp,'bdiv')
        create_dir(self.bdiv_dir)
        self._folders_to_cleanup.append(self.bdiv_dir)
        self.sumtaxa_dir = join(self.fs_fp,'sumtaxa')
        create_dir(self.sumtaxa_dir)
        self._folders_to_cleanup.append(self.sumtaxa_dir)
        self.te_dir = join(self.fs_fp,'topiaryexplorer_files')
        create_dir(self.te_dir)
        self._folders_to_cleanup.append(self.te_dir)
        self.mapping_dir = join(self.fs_fp,'mapping_files')
        create_dir(self.mapping_dir)
        self._folders_to_cleanup.append(self.mapping_dir)
        self.otu_table_dir = join(self.fs_fp,'otu_table_files')
        create_dir(self.otu_table_dir)
        self._folders_to_cleanup.append(self.otu_table_dir)
        self.zip_file_dir = join(self.fs_fp,'zip_files')
        create_dir(self.zip_file_dir)
        self._folders_to_cleanup.append(self.zip_file_dir)
        
        # write params_file
        self.params_path=get_tmp_filename(prefix='ParamsTests_',suffix='.txt')
        
        # write params file
        params=open(self.params_path,'w')
        params.write(params_data)
        params.close()
        self._paths_to_clean_up.append(self.params_path)

    def tearDown(self):
        '''This function removes the generated files'''
        
        map(remove,self._paths_to_clean_up)
        map(rmtree,self._folders_to_cleanup)
        
        
    def test_combine_map_header_cols(self):
        """ combine_map_header_cols: this combines 2 cols in mapping file"""
        
        obs=combine_map_header_cols(['SampleID','Description'],self.map)
        exp = [['SampleID','BarcodeSequence','LinkerPrimerSequence',
                     'Description','SampleID_and_Description'],
                     ['Sample1','AA','GGCC','Test1','Sample1_Test1'],
                     ['Sample2','CC','AAGG','Test2','Sample2_Test2']]
        
        self.assertEqual(obs,exp)
        
    def test_get_mapping_data(self):
        """ get_mapping_data: this gets the metadata from DB """
        
        obs = get_mapping_data(self.data_access, self.is_admin, 
                               self.table_col_value, self.user_id,
                               get_count=False)
        
        self.assertEqual(obs[0],exp_get_mapping_data_results)
        
    def test_write_mapping_and_otu_table(self):
        """ write_mapping_and_otu_table: this writes the mapping file and \
OTU Table """

        ### For this function I am testing a lot of functionality,
        ### since this function can kick off torque_jobs
        ### For most of the visualizations, I am checking a single file output
        ### if that one is correct, then the rest of the script should
        ### behave correctly
        ### I am not testing 2D, 3D, Distance-histograms and alpha-rarefaction
        
        obs=write_mapping_and_otu_table(self.data_access, self.table_col_value, 
                                        self.fs_fp, self.web_fp, 
                                        self.file_name_prefix,self.user_id,
                                        self.meta_id,self.params_path,
                                        self.rarefied_at,
                                        self.otutable_rarefied_at,
                                        self.jobs_to_start,self.tax_name,
                                        self.tree_fp)
        
        for i in listdir(self.mapping_dir):
            # remove mapping filepaths from DB
            mapping_web_fp = join(self.web_fp, 'mapping_files', i)
            self.data_access.clearMetaFiles(self.meta_id, mapping_web_fp)
            
            # check the mapping file looks correct
            if i.endswith('map.txt'):
                obs_mapping_file = open(join(self.mapping_dir,i),'U').read()
                
                self.assertEqual(obs_mapping_file,exp_mapping_file)
            
        for i in listdir(self.otu_table_dir):
            # remove OTU table filepaths from DB
            otu_table_web_fp=join(self.web_fp, 'otu_table_files', i)
            self.data_access.clearMetaFiles(self.meta_id, otu_table_web_fp)
            if i.endswith('otu_table.biom'):
                # check the otu table looks correct
                obs_otu_table = \
                        parse_biom_table(open(join(self.otu_table_dir,i),'U'))
                
                self.assertEqual(obs_otu_table.delimitedSelf(),exp_otu_table)
            elif i.endswith('otu_table_even10.biom'):
                # check the rarefied OTU table looks correct 
                # note this is arbitrary so just reading the headers
                obs_otu_table = \
                        parse_biom_table(open(join(self.otu_table_dir,i),'U'))
                        
                # since rarefation is arbitrary, I just make sure the sample
                # list is consistent
                self.assertEqual(obs_otu_table.SampleIds,
                                  self.samples_list)
            
        for i in listdir(self.zip_file_dir):
            # remove zip filepaths from DB
            zip_web_fp=join(self.web_fp, 'zip_files', i)
            self.data_access.clearMetaFiles(self.meta_id, zip_web_fp)
        
        for i in listdir(self.te_dir):
            # check the TopiaryExplorer Project file looks correct 
            if i.endswith('.tep'):
                obs_tep=open(join(self.te_dir,i),'U').read()
                self.assertEqual(obs_tep,exp_tep)
                
            # remove TE filepaths from DB
            zip_web_fp=join(self.web_fp, 'topiaryexplorer_files', i)
            self.data_access.clearMetaFiles(self.meta_id, zip_web_fp)
        
        # check the status of beta-diversity
        job_type_id=8 # bdiv
        # wait for either an okay or error
        while check_job_state_id(self.data_access, self.meta_id, 
                    job_type_id)['job_state_name'] not in \
                    ( 'COMPLETED_ERROR', 'COMPLETED_OKAY'):
            time.sleep(0.15)
        
        # if there is an error, write msg
        if check_job_state_id(self.data_access, self.meta_id, 
                              job_type_id)['job_state_name'] == \
                              'COMPLETED_ERROR':
            print check_job_state_id(self.data_access, self.meta_id, 
                                     job_type_id)['job_notes']
        
        # remove the torque_job
        self.data_access.clearTorqueJob(check_job_state_id(self.data_access, 
                                                        self.meta_id, 
                                                        job_type_id)['job_id'])
        
        # verify the principal-coordinate file looks correct
        bdiv_dir=join(self.fs_fp,'bdiv')
        for i in listdir(bdiv_dir):
            pc_fpath=join(bdiv_dir,i,'unweighted_unifrac_pc.txt')
            obs=open(pc_fpath,'U').read()
            self.assertEqual(obs,exp_unweighted_pc)
                
        # check the status of summarized taxonomy
        job_type_id=11 # sumtaxa
        # wait for either an okay or error
        while check_job_state_id(self.data_access, self.meta_id, 
                    job_type_id)['job_state_name'] not in \
                    ( 'COMPLETED_ERROR', 'COMPLETED_OKAY'):
            time.sleep(0.15)
        
        # if there is an error, write msg
        if check_job_state_id(self.data_access, self.meta_id, 
                              job_type_id)['job_state_name'] == \
                              'COMPLETED_ERROR':
            print check_job_state_id(self.data_access, self.meta_id, 
                                     job_type_id)['job_notes']
        
        # remove the torque_job
        self.data_access.clearTorqueJob(check_job_state_id(self.data_access, 
                                                        self.meta_id, 
                                                        job_type_id)['job_id'])
        
        # verify the raw data from plot_taxa_summary.py looks correct
        sumtaxa_dir=join(self.fs_fp,'sumtaxa')
        for i in listdir(sumtaxa_dir):
            if i.endswith('sorted.biom'):
                otu_table_basename=splitext(i)[0]
                raw_L2_fpath=join(sumtaxa_dir,i,'taxa_summary_plots','raw_data',
                              otu_table_basename + '_sorted_L2.txt')
                obs=open(raw_L2_fpath,'U').read()
                
                self.assertEqual(obs,exp_sum_taxa_raw_data_L2)
            
            # remove summarized taxa html filepath from DB
            area_chart_web_fp=join(self.web_fp, 'sumtaxa', i, 
                                   'taxa_summary_plots', 'area_charts.html')
            self.data_access.clearMetaFiles(self.meta_id, area_chart_web_fp)
            
        # check the status of summarized taxonomy
        job_type_id=9 # heatmap
        # wait for either an okay or error
        while check_job_state_id(self.data_access, self.meta_id, 
                    job_type_id)['job_state_name'] not in \
                    ( 'COMPLETED_ERROR', 'COMPLETED_OKAY'):
            time.sleep(0.15)
        
        # if there is an error, write msg
        if check_job_state_id(self.data_access, self.meta_id, 
                              job_type_id)['job_state_name'] == \
                              'COMPLETED_ERROR':
            print check_job_state_id(self.data_access, self.meta_id, 
                                     job_type_id)['job_notes']
        
        # remove the torque_job
        self.data_access.clearTorqueJob(check_job_state_id(self.data_access, 
                                                        self.meta_id, 
                                                        job_type_id)['job_id'])
        
        # verify the heatmap js table file iooks correct
        heatmap_dir=join(self.fs_fp,'heatmap')
        for i in listdir(heatmap_dir):
            tmp_heatmap_dir = join(heatmap_dir,i)
            for j in listdir(tmp_heatmap_dir):
                if j.startswith('test'):
                    otu_table_basename = splitext(j)[0]
                    heatmap_js_fpath = join(tmp_heatmap_dir, 'js', 
                                            otu_table_basename + '.js')
                    obs=open(heatmap_js_fpath,'U').read()
                    
                    self.assertEqual(obs,exp_heatmap_js_table)
                    
                    # remove summarized taxa html filepath from DB
                    heatmap_web_fpath=join(self.web_fp,'heatmap',i,j)
                    self.data_access.clearMetaFiles(self.meta_id,
                                                    heatmap_web_fpath)
        
    def test_write_otu_table(self):
        """ write_otu_table: this writes the OTU Table """
        
        otu_table_dir_web_fp=join(self.web_fp, 'otu_table_files')
        
        otu_table_filepath, otu_table_filepath_db, otu_table_fname = \
            write_otu_table(self.data_access, self.samples_list, self.tax_name, 
                            self.file_name_prefix, self.tmp_prefix, 
                            self.otu_table_dir, otu_table_dir_web_fp)
        
        obs_otu_table = parse_biom_table(open(otu_table_filepath,'U'))
        self._paths_to_clean_up.append(otu_table_filepath)
        
        self.assertEqual(obs_otu_table,obs_otu_table)
    
    def test_zip_and_add_filepaths(self):
        """ zip and add filepaths to DB """
        
        # this is tested in test_write_mapping_and_otu_table
        
    def test_rarefy_otu_table(self):
        """ rarefy_otu_table: rarefy the OTU table """
        
        # this is tested in test_write_mapping_and_otu_table
        
    def test_run_other_qiime_analysis(self):
        """ run_other_qiime_analysis: generate other visualizations """
        
        # this is tested in test_write_mapping_and_otu_table
        
    

exp_get_mapping_data_results=\
[('test.PCx354.630848', 'AGCACGAGCCTA', 'CATGCTGCCTCCCGTAGGAGT', 0, 'Fasting_subset', 0, 'GAZ:United States of America', 'test_dataset'), 
 ('test.PCx355.630846', 'AACTCGTCGATG', 'CATGCTGCCTCCCGTAGGAGT', 0, 'Fasting_subset', 0, 'GAZ:United States of America', 'test_dataset'), 
 ('test.PCx636.630852', 'ACGGTGAGTGTC', 'CATGCTGCCTCCCGTAGGAGT', 0, 'Fasting_subset', 0, 'GAZ:United States of America', 'test_dataset'), 
 ('test.PCx481.630849', 'ACCAGCGACTAG', 'CATGCTGCCTCCCGTAGGAGT', 0, 'Fasting_subset', 0, 'GAZ:United States of America', 'test_dataset'), 
 ('test.PCx635.630853', 'ACCGCAGAGTCA', 'CATGCTGCCTCCCGTAGGAGT', 0, 'Fasting_subset', 0, 'GAZ:United States of America', 'test_dataset'), 
 ('test.PCx356.630847', 'ACAGACCACTCA', 'CATGCTGCCTCCCGTAGGAGT', 0, 'Fasting_subset', 0, 'GAZ:United States of America', 'test_dataset'), 
 ('test.PCx634.630850', 'ACAGAGTCGGCT', 'CATGCTGCCTCCCGTAGGAGT', 0, 'Fasting_subset', 0, 'GAZ:United States of America', 'test_dataset'), 
 ('test.PCx593.630851', 'AGCAGCACTTGT', 'CATGCTGCCTCCCGTAGGAGT', 0, 'Fasting_subset', 0, 'GAZ:United States of America', 'test_dataset'), 
 ('test.PCx607.630845', 'AACTGTGCGTAC', 'CATGCTGCCTCCCGTAGGAGT', 0, 'Fasting_subset', 0, 'GAZ:United States of America', 'test_dataset')]

exp_mapping_file="""\
#SampleID\tBarcodeSequence\tLinkerPrimerSequence\tSTUDY_ID\tCOUNTRY\tRUN_PREFIX\tDescription
test.PCx354.630848\tAGCACGAGCCTA\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx355.630846\tAACTCGTCGATG\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx636.630852\tACGGTGAGTGTC\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx481.630849\tACCAGCGACTAG\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx635.630853\tACCGCAGAGTCA\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx356.630847\tACAGACCACTCA\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx634.630850\tACAGAGTCGGCT\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx593.630851\tAGCAGCACTTGT\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx607.630845\tAACTGTGCGTAC\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset"""

exp_otu_table="""\
# Constructed from biom file
#OTU ID\ttest.PCx354.630848\ttest.PCx355.630846\ttest.PCx636.630852\ttest.PCx481.630849\ttest.PCx635.630853\ttest.PCx356.630847\ttest.PCx634.630850\ttest.PCx593.630851\ttest.PCx607.630845
412648\t1.0\t1.0\t1.0\t0.0\t1.0\t6.0\t0.0\t8.0\t0.0
342948\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
195470\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
185989\t1.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t2.0\t0.0
578025\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
318106\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
266771\t14.0\t1.0\t0.0\t1.0\t0.0\t14.0\t0.0\t0.0\t0.0
135493\t12.0\t13.0\t0.0\t13.0\t0.0\t5.0\t0.0\t0.0\t0.0
132165\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
413456\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
331820\t2.0\t18.0\t4.0\t1.0\t4.0\t0.0\t21.0\t0.0\t0.0
278423\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t1.0\t0.0
230541\t1.0\t2.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
164638\t1.0\t4.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
319134\t3.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t3.0\t0.0
228512\t29.0\t1.0\t0.0\t0.0\t0.0\t10.0\t0.0\t0.0\t0.0
274084\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
269378\t1.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0
268581\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
209907\t6.0\t0.0\t0.0\t0.0\t0.0\t4.0\t0.0\t2.0\t0.0
194822\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
189531\t1.0\t0.0\t0.0\t2.0\t0.0\t4.0\t0.0\t16.0\t0.0
175432\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
386087\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
328536\t14.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t7.0\t0.0
273626\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t10.0\t0.0
271480\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
271014\t1.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
255362\t1.0\t4.0\t0.0\t5.0\t0.0\t2.0\t0.0\t0.0\t0.0
233169\t1.0\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
183428\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
441301\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
346400\t1.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
270351\t1.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0
269815\t1.0\t1.0\t0.0\t5.0\t0.0\t0.0\t0.0\t0.0\t1.0
195445\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
178596\t1.0\t4.0\t1.0\t0.0\t0.0\t3.0\t0.0\t0.0\t0.0
169379\t1.0\t3.0\t5.0\t2.0\t4.0\t1.0\t2.0\t1.0\t8.0
569818\t4.0\t9.0\t0.0\t1.0\t2.0\t0.0\t0.0\t0.0\t0.0
567604\t1.0\t1.0\t0.0\t1.0\t0.0\t0.0\t0.0\t3.0\t0.0
403497\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
346275\t1.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
264496\t2.0\t2.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
258899\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
184585\t1.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
299668\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t3.0\t0.0\t0.0
269169\t0.0\t19.0\t0.0\t0.0\t0.0\t2.0\t3.0\t2.0\t0.0
232773\t0.0\t2.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
165986\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0
385188\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
302407\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
272819\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
174272\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
309188\t0.0\t2.0\t0.0\t4.0\t4.0\t2.0\t1.0\t0.0\t5.0
259056\t0.0\t1.0\t0.0\t7.0\t2.0\t0.0\t0.0\t0.0\t0.0
183384\t0.0\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
303491\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
275888\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
260756\t0.0\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
260666\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
204547\t0.0\t1.0\t0.0\t0.0\t1.0\t0.0\t1.0\t4.0\t0.0
191199\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
180097\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0
400879\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
275869\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
263876\t0.0\t4.0\t1.0\t0.0\t2.0\t3.0\t0.0\t1.0\t2.0
197240\t0.0\t1.0\t3.0\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0
186526\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
169479\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
249661\t0.0\t1.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
212750\t0.0\t2.0\t1.0\t1.0\t0.0\t0.0\t3.0\t3.0\t0.0
190047\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
234635\t0.0\t2.0\t0.0\t2.0\t1.0\t0.0\t0.0\t0.0\t0.0
176858\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
95638\t0.0\t0.0\t6.0\t0.0\t2.0\t0.0\t5.0\t0.0\t3.0
265730\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
328391\t0.0\t0.0\t1.0\t0.0\t1.0\t0.0\t0.0\t0.0\t1.0
269994\t0.0\t0.0\t2.0\t0.0\t1.0\t2.0\t0.0\t0.0\t0.0
264035\t0.0\t0.0\t19.0\t1.0\t2.0\t0.0\t1.0\t0.0\t0.0
199177\t0.0\t0.0\t1.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0
170545\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
272270\t0.0\t0.0\t3.0\t0.0\t0.0\t2.0\t0.0\t5.0\t1.0
227953\t0.0\t0.0\t2.0\t1.0\t5.0\t0.0\t1.0\t0.0\t0.0
213896\t0.0\t0.0\t2.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0
204144\t0.0\t0.0\t2.0\t0.0\t0.0\t3.0\t2.0\t1.0\t0.0
182470\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
322991\t0.0\t0.0\t1.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
322112\t0.0\t0.0\t1.0\t1.0\t0.0\t1.0\t1.0\t0.0\t0.0
164612\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
393399\t0.0\t0.0\t1.0\t0.0\t3.0\t0.0\t1.0\t2.0\t2.0
230364\t0.0\t0.0\t3.0\t0.0\t5.0\t0.0\t9.0\t0.0\t5.0
15711\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t4.0\t0.0
269726\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
170836\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0
264373\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
260352\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0
258202\t0.0\t0.0\t1.0\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0
182033\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
175843\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
569158\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0
267066\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0
169943\t0.0\t0.0\t3.0\t0.0\t0.0\t0.0\t2.0\t2.0\t0.0
97294\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
275913\t0.0\t0.0\t0.0\t2.0\t1.0\t0.0\t0.0\t0.0\t0.0
263334\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
240571\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t2.0
192659\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
191109\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0
321220\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
282677\t0.0\t0.0\t0.0\t1.0\t0.0\t1.0\t0.0\t0.0\t0.0
269003\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
204911\t0.0\t0.0\t0.0\t6.0\t1.0\t0.0\t0.0\t0.0\t0.0
265813\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t1.0
233411\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
232142\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0
173192\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
319219\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
267123\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
259451\t0.0\t0.0\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0\t0.0
231904\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
172705\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
400627\t0.0\t0.0\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0\t0.0
318370\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
259965\t0.0\t0.0\t0.0\t3.0\t0.0\t0.0\t0.0\t9.0\t5.0
232037\t0.0\t0.0\t0.0\t1.0\t1.0\t1.0\t0.0\t0.0\t0.0
210178\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0
176977\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t4.0\t0.0
170555\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
307595\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
272454\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
235071\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
216933\t0.0\t0.0\t0.0\t9.0\t0.0\t0.0\t3.0\t0.0\t0.0
215193\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
182621\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
268947\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
256899\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
422931\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0
353820\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0
241287\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
231997\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
191814\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
173697\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0
163240\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
131203\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0
115098\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t8.0\t7.0
104780\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0
568692\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
407754\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
332311\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t2.0\t0.0\t0.0
320141\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
266214\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
261434\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t2.0
274125\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
232941\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
170335\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t3.0\t0.0\t0.0
423411\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
366044\t0.0\t0.0\t0.0\t0.0\t3.0\t0.0\t1.0\t0.0\t0.0
309206\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
270825\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
261606\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
205987\t0.0\t0.0\t0.0\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0
309361\t0.0\t0.0\t0.0\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0
266639\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
230573\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
14035\t0.0\t0.0\t0.0\t0.0\t3.0\t0.0\t0.0\t2.0\t0.0
333219\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
308269\t0.0\t0.0\t0.0\t0.0\t3.0\t0.0\t0.0\t0.0\t6.0
230534\t0.0\t0.0\t0.0\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0
174476\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
407007\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
321808\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
270840\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
264734\t0.0\t0.0\t0.0\t0.0\t1.0\t2.0\t0.0\t0.0\t0.0
166592\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
331317\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
270519\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
262375\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
190522\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0
251891\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
231169\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
191951\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
317740\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
263443\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0
325036\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0
274021\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
181443\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
180864\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
355178\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
338887\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
264889\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
275543\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
196240\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
355771\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0
339743\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
334098\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
269914\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0
322062\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
275847\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
273706\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
178173\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0
131681\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0
332547\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0
267590\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0
188969\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0
362383\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t4.0\t0.0\t0.0
343906\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0
289177\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0
274578\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t2.0\t0.0
367581\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0
291090\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0
197301\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0
163413\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0
328453\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0
248140\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0
469832\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t13.0\t0.0\t0.0
353985\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0
335530\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t5.0\t0.0\t0.0
263592\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0
262247\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0
261177\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t1.0
313166\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0
229761\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t1.0
300748\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0
194202\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0
470494\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t5.0\t2.0
447694\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t9.0\t1.0
270244\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0
269872\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0
269645\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0
187078\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0
316842\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0
353711\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0
271439\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0
263014\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0
2000\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t3.0\t0.0
335952\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
227950\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0
215086\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
171239\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
133453\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
212758\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
208222\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0
185403\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
268856\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
231684\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
170502\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
398943\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t5.0
273549\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
270015\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
269618\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
175699\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t8.0
461524\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0
303652\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
285281\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
209866\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
178026\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
288931\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
263106\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
259868\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0
167204\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t6.0"""

exp_tep="""\
>>tre
>>otm
#OTU ID\tOTU Metadata
412648\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
342948\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
195470\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
185989\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
578025\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
318106\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
266771\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Lactobacillales; f__Lactobacillaceae; g__Lactobacillus; s__;
135493\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
132165\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
413456\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Coprobacillus; s__;
331820\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__;
278423\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Peptococcaceae; g__; s__;
230541\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
164638\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
319134\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
228512\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
274084\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Allobaculum; s__Allobaculum sp ID4;
269378\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Ruminococcus; s__;
268581\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
209907\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
194822\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
189531\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
175432\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
386087\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__;
328536\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
273626\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__; g__; s__;
271480\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
271014\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Lactobacillales; f__Lactobacillaceae; g__Lactobacillus; s__;
255362\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
233169\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__; g__; s__;
183428\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
441301\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
346400\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
270351\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
269815\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
195445\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
178596\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
169379\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
569818\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
567604\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Lactobacillales; f__Lactobacillaceae; g__Lactobacillus; s__;
403497\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
346275\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
264496\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
258899\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
184585\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
299668\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Clostridiaceae; g__Clostridium; s__;
269169\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
232773\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
165986\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
385188\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
302407\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
272819\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
174272\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
309188\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__;
259056\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
183384\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
303491\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
275888\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
260756\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
260666\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
204547\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
191199\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
180097\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
400879\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
275869\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__;
263876\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
197240\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
186526\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
169479\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
249661\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Porphyromonadaceae; g__Parabacteroides; s__;
212750\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
190047\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
234635\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
176858\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
95638\tk__Bacteria; p__Deferribacteres; c__Deferribacteres (class); o__Deferribacterales; f__Deferribacteraceae; g__Mucispirillum; s__Mucispirillum schaedleri;
265730\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
328391\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
269994\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
264035\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__;
199177\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
170545\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Bacillales; f__Staphylococcaceae; g__Staphylococcus; s__;
272270\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
227953\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__;
213896\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
204144\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
182470\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
322991\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
322112\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__; g__; s__;
164612\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Bacillales; f__Staphylococcaceae; g__Staphylococcus; s__;
393399\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
230364\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__;
15711\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Clostridium; s__Clostridium cocleatum;
269726\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
170836\tk__Bacteria; p__Proteobacteria; c__Deltaproteobacteria; o__Desulfovibrionales; f__Desulfovibrionaceae; g__; s__;
264373\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
260352\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
258202\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
182033\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
175843\tk__Bacteria; p__Actinobacteria; c__Actinobacteria (class); o__Coriobacteriales; f__Coriobacteriaceae; g__Adlercreutzia; s__;
569158\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__; s__;
267066\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
169943\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
97294\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
275913\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
263334\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
240571\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
192659\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__;
191109\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
321220\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
282677\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
269003\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
204911\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
265813\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
233411\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
232142\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
173192\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
319219\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
267123\tk__Bacteria; p__Actinobacteria; c__Actinobacteria (class); o__Coriobacteriales; f__Coriobacteriaceae; g__Adlercreutzia; s__;
259451\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
231904\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
172705\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__;
400627\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
318370\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
259965\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Allobaculum; s__Allobaculum sp ID4;
232037\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
210178\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
176977\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
170555\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
307595\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
272454\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
235071\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
216933\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Erysipelotrichales; f__Erysipelotrichaceae; g__; s__;
215193\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
182621\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__;
268947\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Eubacterium; s__;
256899\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
422931\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Lactobacillales; f__Lactobacillaceae; g__Lactobacillus; s__;
353820\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
241287\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
231997\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
191814\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
173697\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
163240\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
131203\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
115098\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Allobaculum; s__Allobaculum sp ID4;
104780\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__;
568692\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__; g__; s__;
407754\tk__Bacteria; p__Proteobacteria; c__Deltaproteobacteria; o__Desulfovibrionales; f__Desulfovibrionaceae; g__; s__;
332311\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__Bacteroides eggerthii;
320141\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
266214\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
261434\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
274125\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
232941\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__;
170335\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Porphyromonadaceae; g__Odoribacter; s__;
423411\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
366044\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Porphyromonadaceae; g__; s__;
309206\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__;
270825\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
261606\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
205987\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
309361\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
266639\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
230573\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__;
14035\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
333219\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__;
308269\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
230534\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Oscillospira; s__;
174476\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
407007\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Ruminococcus; s__;
321808\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
270840\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
264734\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
166592\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
331317\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
270519\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
262375\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__; s__;
190522\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Prevotellaceae; g__Prevotella; s__;
251891\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
231169\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
191951\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__; g__; s__;
317740\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
263443\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
325036\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
274021\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
181443\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
180864\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__; g__; s__;
355178\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
338887\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Oscillospira; s__;
264889\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
275543\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
196240\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
355771\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
339743\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
334098\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
269914\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
322062\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
275847\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
273706\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
178173\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
131681\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
332547\tk__Bacteria; p__Actinobacteria; c__Actinobacteria (class); o__Coriobacteriales; f__Coriobacteriaceae; g__Adlercreutzia; s__;
267590\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
188969\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
362383\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__; s__Clostridium innocuum;
343906\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
289177\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
274578\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
367581\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Porphyromonadaceae; g__Parabacteroides; s__;
291090\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Porphyromonadaceae; g__Parabacteroides; s__Parabacteroides distasonis;
197301\tk__Bacteria; p__Actinobacteria; c__Actinobacteria (class); o__Coriobacteriales; f__Coriobacteriaceae; g__Adlercreutzia; s__;
163413\tk__Bacteria; p__TM7; c__TM7-3; o__CW040; f__; g__; s__;
328453\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__;
248140\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__Bacteroides caccae;
469832\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__Bacteroides uniformis;
353985\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Porphyromonadaceae; g__Parabacteroides; s__Parabacteroides distasonis;
335530\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__;
263592\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
262247\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
261177\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
313166\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__;
229761\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Clostridiales Family XIII. Incertae Sedis; g__; s__;
300748\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
194202\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
470494\tk__Bacteria; p__Proteobacteria; c__Epsilonproteobacteria; o__Campylobacterales; f__Helicobacteraceae; g__Flexispira; s__Helicobacter cinaedi;
447694\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
270244\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
269872\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
269645\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
187078\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
316842\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
353711\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__;
271439\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
263014\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__;
2000\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__Bacteroides fragilis;
335952\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
227950\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Catabacteriaceae; g__; s__;
215086\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Catabacteriaceae; g__; s__;
171239\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Oscillospira; s__;
133453\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
212758\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Catabacteriaceae; g__; s__;
208222\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
185403\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Peptococcaceae; g__; s__;
268856\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
231684\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
170502\tk__Bacteria; p__Proteobacteria; c__Deltaproteobacteria; o__Desulfovibrionales; f__Desulfovibrionaceae; g__Desulfovibrio; s__;
398943\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__;
273549\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
270015\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
269618\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
175699\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Allobaculum; s__Allobaculum sp ID4;
461524\tk__Bacteria; p__Actinobacteria; c__Actinobacteria (class); o__Coriobacteriales; f__Coriobacteriaceae; g__; s__;
303652\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Lactobacillales; f__Streptococcaceae; g__Streptococcus; s__;
285281\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
209866\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__;
178026\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__;
288931\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
263106\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Oscillospira; s__;
259868\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Oscillospira; s__;
167204\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__;
>>osm
# Constructed from biom file
#OTU ID\ttest.PCx354.630848\ttest.PCx355.630846\ttest.PCx636.630852\ttest.PCx481.630849\ttest.PCx635.630853\ttest.PCx356.630847\ttest.PCx634.630850\ttest.PCx593.630851\ttest.PCx607.630845\tConsensus Lineage
412648\t1.0\t1.0\t1.0\t0.0\t1.0\t6.0\t0.0\t8.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
342948\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
195470\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
185989\t1.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t2.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
578025\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
318106\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
266771\t14.0\t1.0\t0.0\t1.0\t0.0\t14.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Lactobacillales; f__Lactobacillaceae; g__Lactobacillus; s__
135493\t12.0\t13.0\t0.0\t13.0\t0.0\t5.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
132165\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
413456\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Coprobacillus; s__
331820\t2.0\t18.0\t4.0\t1.0\t4.0\t0.0\t21.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__
278423\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t1.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Peptococcaceae; g__; s__
230541\t1.0\t2.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
164638\t1.0\t4.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
319134\t3.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t3.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
228512\t29.0\t1.0\t0.0\t0.0\t0.0\t10.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
274084\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Allobaculum; s__Allobaculum sp ID4
269378\t1.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Ruminococcus; s__
268581\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
209907\t6.0\t0.0\t0.0\t0.0\t0.0\t4.0\t0.0\t2.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
194822\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
189531\t1.0\t0.0\t0.0\t2.0\t0.0\t4.0\t0.0\t16.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
175432\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
386087\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__
328536\t14.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t7.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
273626\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t10.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__; g__; s__
271480\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
271014\t1.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Lactobacillales; f__Lactobacillaceae; g__Lactobacillus; s__
255362\t1.0\t4.0\t0.0\t5.0\t0.0\t2.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
233169\t1.0\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__; g__; s__
183428\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
441301\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
346400\t1.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
270351\t1.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
269815\t1.0\t1.0\t0.0\t5.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
195445\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
178596\t1.0\t4.0\t1.0\t0.0\t0.0\t3.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
169379\t1.0\t3.0\t5.0\t2.0\t4.0\t1.0\t2.0\t1.0\t8.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
569818\t4.0\t9.0\t0.0\t1.0\t2.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
567604\t1.0\t1.0\t0.0\t1.0\t0.0\t0.0\t0.0\t3.0\t0.0\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Lactobacillales; f__Lactobacillaceae; g__Lactobacillus; s__
403497\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
346275\t1.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
264496\t2.0\t2.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
258899\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
184585\t1.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
299668\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t3.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Clostridiaceae; g__Clostridium; s__
269169\t0.0\t19.0\t0.0\t0.0\t0.0\t2.0\t3.0\t2.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
232773\t0.0\t2.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
165986\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
385188\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
302407\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
272819\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
174272\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
309188\t0.0\t2.0\t0.0\t4.0\t4.0\t2.0\t1.0\t0.0\t5.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__
259056\t0.0\t1.0\t0.0\t7.0\t2.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
183384\t0.0\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
303491\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
275888\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
260756\t0.0\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
260666\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
204547\t0.0\t1.0\t0.0\t0.0\t1.0\t0.0\t1.0\t4.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
191199\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
180097\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
400879\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
275869\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__
263876\t0.0\t4.0\t1.0\t0.0\t2.0\t3.0\t0.0\t1.0\t2.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
197240\t0.0\t1.0\t3.0\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
186526\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
169479\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
249661\t0.0\t1.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Porphyromonadaceae; g__Parabacteroides; s__
212750\t0.0\t2.0\t1.0\t1.0\t0.0\t0.0\t3.0\t3.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
190047\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
234635\t0.0\t2.0\t0.0\t2.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
176858\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
95638\t0.0\t0.0\t6.0\t0.0\t2.0\t0.0\t5.0\t0.0\t3.0\tk__Bacteria; p__Deferribacteres; c__Deferribacteres (class); o__Deferribacterales; f__Deferribacteraceae; g__Mucispirillum; s__Mucispirillum schaedleri
265730\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
328391\t0.0\t0.0\t1.0\t0.0\t1.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
269994\t0.0\t0.0\t2.0\t0.0\t1.0\t2.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
264035\t0.0\t0.0\t19.0\t1.0\t2.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__
199177\t0.0\t0.0\t1.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
170545\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Bacillales; f__Staphylococcaceae; g__Staphylococcus; s__
272270\t0.0\t0.0\t3.0\t0.0\t0.0\t2.0\t0.0\t5.0\t1.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
227953\t0.0\t0.0\t2.0\t1.0\t5.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__
213896\t0.0\t0.0\t2.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
204144\t0.0\t0.0\t2.0\t0.0\t0.0\t3.0\t2.0\t1.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
182470\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
322991\t0.0\t0.0\t1.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
322112\t0.0\t0.0\t1.0\t1.0\t0.0\t1.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__; g__; s__
164612\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Bacillales; f__Staphylococcaceae; g__Staphylococcus; s__
393399\t0.0\t0.0\t1.0\t0.0\t3.0\t0.0\t1.0\t2.0\t2.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
230364\t0.0\t0.0\t3.0\t0.0\t5.0\t0.0\t9.0\t0.0\t5.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__
15711\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t4.0\t0.0\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Clostridium; s__Clostridium cocleatum
269726\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
170836\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\tk__Bacteria; p__Proteobacteria; c__Deltaproteobacteria; o__Desulfovibrionales; f__Desulfovibrionaceae; g__; s__
264373\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
260352\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
258202\t0.0\t0.0\t1.0\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
182033\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
175843\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Actinobacteria; c__Actinobacteria (class); o__Coriobacteriales; f__Coriobacteriaceae; g__Adlercreutzia; s__
569158\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__; s__
267066\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
169943\t0.0\t0.0\t3.0\t0.0\t0.0\t0.0\t2.0\t2.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
97294\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
275913\t0.0\t0.0\t0.0\t2.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
263334\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
240571\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t2.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
192659\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__
191109\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
321220\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
282677\t0.0\t0.0\t0.0\t1.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
269003\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
204911\t0.0\t0.0\t0.0\t6.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
265813\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
233411\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
232142\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
173192\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
319219\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
267123\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Actinobacteria; c__Actinobacteria (class); o__Coriobacteriales; f__Coriobacteriaceae; g__Adlercreutzia; s__
259451\t0.0\t0.0\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
231904\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
172705\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__
400627\t0.0\t0.0\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
318370\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
259965\t0.0\t0.0\t0.0\t3.0\t0.0\t0.0\t0.0\t9.0\t5.0\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Allobaculum; s__Allobaculum sp ID4
232037\t0.0\t0.0\t0.0\t1.0\t1.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
210178\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
176977\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t4.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
170555\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
307595\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
272454\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
235071\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
216933\t0.0\t0.0\t0.0\t9.0\t0.0\t0.0\t3.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Erysipelotrichales; f__Erysipelotrichaceae; g__; s__
215193\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
182621\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__
268947\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Eubacterium; s__
256899\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
422931\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t1.0\t0.0\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Lactobacillales; f__Lactobacillaceae; g__Lactobacillus; s__
353820\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
241287\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
231997\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
191814\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
173697\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
163240\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
131203\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
115098\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t8.0\t7.0\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Allobaculum; s__Allobaculum sp ID4
104780\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__
568692\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__; g__; s__
407754\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Proteobacteria; c__Deltaproteobacteria; o__Desulfovibrionales; f__Desulfovibrionaceae; g__; s__
332311\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t2.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__Bacteroides eggerthii
320141\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
266214\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
261434\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t2.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
274125\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
232941\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__
170335\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t3.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Porphyromonadaceae; g__Odoribacter; s__
423411\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
366044\t0.0\t0.0\t0.0\t0.0\t3.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Porphyromonadaceae; g__; s__
309206\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__
270825\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
261606\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
205987\t0.0\t0.0\t0.0\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
309361\t0.0\t0.0\t0.0\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
266639\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
230573\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__
14035\t0.0\t0.0\t0.0\t0.0\t3.0\t0.0\t0.0\t2.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
333219\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__
308269\t0.0\t0.0\t0.0\t0.0\t3.0\t0.0\t0.0\t0.0\t6.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
230534\t0.0\t0.0\t0.0\t0.0\t1.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Oscillospira; s__
174476\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
407007\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Ruminococcus; s__
321808\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
270840\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
264734\t0.0\t0.0\t0.0\t0.0\t1.0\t2.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
166592\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
331317\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
270519\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
262375\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__; s__
190522\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Prevotellaceae; g__Prevotella; s__
251891\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
231169\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
191951\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__; g__; s__
317740\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
263443\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
325036\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
274021\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
181443\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
180864\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__; g__; s__
355178\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
338887\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Oscillospira; s__
264889\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
275543\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
196240\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
355771\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
339743\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
334098\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
269914\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
322062\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
275847\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
273706\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
178173\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
131681\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
332547\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Actinobacteria; c__Actinobacteria (class); o__Coriobacteriales; f__Coriobacteriaceae; g__Adlercreutzia; s__
267590\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
188969\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
362383\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t4.0\t0.0\t0.0\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__; s__Clostridium innocuum
343906\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
289177\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
274578\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t2.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
367581\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Porphyromonadaceae; g__Parabacteroides; s__
291090\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Porphyromonadaceae; g__Parabacteroides; s__Parabacteroides distasonis
197301\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Actinobacteria; c__Actinobacteria (class); o__Coriobacteriales; f__Coriobacteriaceae; g__Adlercreutzia; s__
163413\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\tk__Bacteria; p__TM7; c__TM7-3; o__CW040; f__; g__; s__
328453\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__
248140\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__Bacteroides caccae
469832\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t13.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__Bacteroides uniformis
353985\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Porphyromonadaceae; g__Parabacteroides; s__Parabacteroides distasonis
335530\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t5.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__
263592\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
262247\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
261177\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t1.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
313166\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__
229761\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Clostridiales Family XIII. Incertae Sedis; g__; s__
300748\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
194202\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
470494\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t5.0\t2.0\tk__Bacteria; p__Proteobacteria; c__Epsilonproteobacteria; o__Campylobacterales; f__Helicobacteraceae; g__Flexispira; s__Helicobacter cinaedi
447694\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t9.0\t1.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
270244\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
269872\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
269645\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
187078\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
316842\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
353711\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__
271439\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
263014\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\t0.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Coprococcus; s__
2000\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t3.0\t0.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__Bacteroides fragilis
335952\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
227950\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Catabacteriaceae; g__; s__
215086\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Catabacteriaceae; g__; s__
171239\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Oscillospira; s__
133453\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
212758\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Catabacteriaceae; g__; s__
208222\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
185403\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Peptococcaceae; g__; s__
268856\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
231684\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
170502\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Proteobacteria; c__Deltaproteobacteria; o__Desulfovibrionales; f__Desulfovibrionaceae; g__Desulfovibrio; s__
398943\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t5.0\tk__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__
273549\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
270015\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
269618\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
175699\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t8.0\tk__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Allobaculum; s__Allobaculum sp ID4
461524\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t2.0\tk__Bacteria; p__Actinobacteria; c__Actinobacteria (class); o__Coriobacteriales; f__Coriobacteriaceae; g__; s__
303652\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Bacilli; o__Lactobacillales; f__Streptococcaceae; g__Streptococcus; s__
285281\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
209866\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__
178026\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__
288931\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
263106\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Oscillospira; s__
259868\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t1.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__Oscillospira; s__
167204\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t0.0\t6.0\tk__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__
>>sam
#SampleID\tBarcodeSequence\tLinkerPrimerSequence\tSTUDY_ID\tCOUNTRY\tRUN_PREFIX\tDescription
test.PCx354.630848\tAGCACGAGCCTA\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx355.630846\tAACTCGTCGATG\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx636.630852\tACGGTGAGTGTC\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx481.630849\tACCAGCGACTAG\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx635.630853\tACCGCAGAGTCA\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx356.630847\tACAGACCACTCA\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx634.630850\tACAGAGTCGGCT\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx593.630851\tAGCAGCACTTGT\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset
test.PCx607.630845\tAACTGTGCGTAC\tCATGCTGCCTCCCGTAGGAGT\t0\tGAZ:United States of America\tFasting_subset\ttest_dataset"""

exp_unweighted_pc="""\
pc vector number\t1\t2\t3\t4\t5\t6\t7\t8\t9
test.PCx354.630848\t-0.25471567359\t0.167443905697\t0.0222579312598\t0.170274691321\t-0.0670295277293\t-0.0197776106642\t0.0677049909292\t-0.199406064434\t3.08689689285e-09
test.PCx355.630846\t-0.209263952027\t-0.189177972445\t-0.152064136192\t-0.0205732628796\t-0.0293040116838\t0.251517592389\t0.0373392244253\t0.0488472074558\t3.08689689285e-09
test.PCx636.630852\t0.212621924188\t-0.128429943369\t-0.147215304934\t-0.0248190450139\t-0.0420208256249\t-0.0270679050163\t-0.235916315829\t-0.116137353475\t3.08689689285e-09
test.PCx481.630849\t-0.0742432717353\t0.0126561135493\t-0.0250330791301\t0.211342529807\t0.298208276079\t-0.0590687091778\t-0.0603373049211\t0.0935239874459\t3.08689689285e-09
test.PCx635.630853\t0.171385193781\t-0.129375333999\t0.360899386824\t0.118654346954\t-0.0975564091346\t0.0634323578041\t-0.0152845042213\t0.0369903625807\t3.08689689285e-09
test.PCx356.630847\t-0.216371670631\t-0.238997607938\t0.0845382803606\t-0.239488946953\t0.038042484536\t-0.17199629051\t0.0555257034381\t-0.0103912370157\t3.08689689285e-09
test.PCx634.630850\t0.326083723958\t-0.0347053898802\t-0.177622070509\t0.0697392629165\t-0.0618005800146\t-0.0808686340294\t0.209021161679\t0.0330098753449\t3.08689689285e-09
test.PCx593.630851\t-0.128538704993\t0.266786173747\t-0.0388761414712\t-0.048009233051\t-0.197760771539\t-0.0652057238905\t-0.090395477605\t0.158949679258\t3.08689689285e-09
test.PCx607.630845\t0.173042431049\t0.273800054638\t0.0731151337927\t-0.237120343101\t0.159221365111\t0.109034923095\t0.0323425221047\t-0.0453864571604\t3.08689689285e-09


eigvals\t0.388377683187\t0.301683824534\t0.221719783431\t0.209526697677\t0.175290169547\t0.124160561869\t0.121499228866\t0.0942742969399\t8.57603918436e-17
% variation explained\t23.7317464489\t18.4343342615\t13.5481463299\t12.8030900817\t10.7110733669\t7.58680815294\t7.42418789235\t5.76061346591\t5.24037287078e-15"""

exp_sum_taxa_raw_data_L2="""\
Taxon	test.PCx354.283437	test.PCx355.283435	test.PCx356.283436	test.PCx481.283438	test.PCx593.283440	test.PCx607.283434	test.PCx634.283439	test.PCx635.283442	test.PCx636.283441
k__Bacteria; p__Actinobacteria	0.0	0.0	0.0	0.00833333333333	0.0	0.0194174757282	0.0178571428571	0.0	0.0120481927711
k__Bacteria; p__Bacteroidetes	0.0650406504065	0.322314049587	0.231481481481	0.158333333333	0.407407407407	0.300970873786	0.669642857143	0.45652173910.578313253012
k__Bacteria; p__Deferribacteres	0.0	0.0	0.0	0.0	0.0	0.0291262135922	0.0446428571429	0.0217391304348	0.0722891566265
k__Bacteria; p__Firmicutes	0.918699186992	0.677685950413	0.768518518519	0.791666666667	0.4	0.427184466019	0.196428571429	0.5	0.301204819277
k__Bacteria; p__Proteobacteria	0.0	0.0	0.0	0.0	0.037037037037	0.0291262135922	0.0178571428571	0.0108695652174	0.0120481927711
k__Bacteria; p__TM7	0.0	0.0	0.0	0.0	0.0	0.0	0.0178571428571	0.0	0.0
k__Bacteria; p__Tenericutes	0.0162601626016	0.0	0.0	0.0416666666667	0.155555555556	0.194174757282	0.0357142857143	0.0108695652174	0.0240963855422
"""

exp_heatmap_js_table="""\
var otu_num_cutoff=5;    var OTU_table=new Array();
    var i=0;
    for (i==0;i<11;i++) {
    OTU_table[i]=new Array();}
OTU_table[0][0]='#OTU ID';
OTU_table[0][1]='95638';
OTU_table[0][2]='15711';
OTU_table[0][3]='175699';
OTU_table[0][4]='259965';
OTU_table[0][5]='115098';
OTU_table[0][6]='470494';
OTU_table[0][7]='169379';
OTU_table[0][8]='393399';
OTU_table[0][9]='178596';
OTU_table[0][10]='412648';
OTU_table[0][11]='189531';
OTU_table[0][12]='272270';
OTU_table[0][13]='204547';
OTU_table[0][14]='264496';
OTU_table[0][15]='398943';
OTU_table[0][16]='212750';
OTU_table[0][17]='204144';
OTU_table[0][18]='447694';
OTU_table[0][19]='469832';
OTU_table[0][20]='331820';
OTU_table[0][21]='264035';
OTU_table[0][22]='309188';
OTU_table[0][23]='230364';
OTU_table[0][24]='227953';
OTU_table[0][25]='335530';
OTU_table[0][26]='273626';
OTU_table[0][27]='269994';
OTU_table[0][28]='169943';
OTU_table[0][29]='569818';
OTU_table[0][30]='319134';
OTU_table[0][31]='228512';
OTU_table[0][32]='234635';
OTU_table[0][33]='209907';
OTU_table[0][34]='269815';
OTU_table[0][35]='255362';
OTU_table[0][36]='167204';
OTU_table[0][37]='176977';
OTU_table[0][38]='135493';
OTU_table[0][39]='197240';
OTU_table[0][40]='164638';
OTU_table[0][41]='14035';
OTU_table[0][42]='259056';
OTU_table[0][43]='328536';
OTU_table[0][44]='269169';
OTU_table[0][45]='308269';
OTU_table[0][46]='204911';
OTU_table[0][47]='263876';
OTU_table[0][48]='216933';
OTU_table[0][49]='567604';
OTU_table[0][50]='266771';
OTU_table[1][0]='test.PCx354.630848';
OTU_table[1][1]=0.0000;
OTU_table[1][2]=0.0000;
OTU_table[1][3]=0.0000;
OTU_table[1][4]=0.0000;
OTU_table[1][5]=0.0000;
OTU_table[1][6]=0.0000;
OTU_table[1][7]=1.0000;
OTU_table[1][8]=0.0000;
OTU_table[1][9]=1.0000;
OTU_table[1][10]=1.0000;
OTU_table[1][11]=1.0000;
OTU_table[1][12]=0.0000;
OTU_table[1][13]=0.0000;
OTU_table[1][14]=2.0000;
OTU_table[1][15]=0.0000;
OTU_table[1][16]=0.0000;
OTU_table[1][17]=0.0000;
OTU_table[1][18]=0.0000;
OTU_table[1][19]=0.0000;
OTU_table[1][20]=2.0000;
OTU_table[1][21]=0.0000;
OTU_table[1][22]=0.0000;
OTU_table[1][23]=0.0000;
OTU_table[1][24]=0.0000;
OTU_table[1][25]=0.0000;
OTU_table[1][26]=1.0000;
OTU_table[1][27]=0.0000;
OTU_table[1][28]=0.0000;
OTU_table[1][29]=4.0000;
OTU_table[1][30]=3.0000;
OTU_table[1][31]=29.0000;
OTU_table[1][32]=0.0000;
OTU_table[1][33]=6.0000;
OTU_table[1][34]=1.0000;
OTU_table[1][35]=1.0000;
OTU_table[1][36]=0.0000;
OTU_table[1][37]=0.0000;
OTU_table[1][38]=12.0000;
OTU_table[1][39]=0.0000;
OTU_table[1][40]=1.0000;
OTU_table[1][41]=0.0000;
OTU_table[1][42]=0.0000;
OTU_table[1][43]=14.0000;
OTU_table[1][44]=0.0000;
OTU_table[1][45]=0.0000;
OTU_table[1][46]=0.0000;
OTU_table[1][47]=0.0000;
OTU_table[1][48]=0.0000;
OTU_table[1][49]=1.0000;
OTU_table[1][50]=14.0000;
OTU_table[2][0]='test.PCx355.630846';
OTU_table[2][1]=0.0000;
OTU_table[2][2]=0.0000;
OTU_table[2][3]=0.0000;
OTU_table[2][4]=0.0000;
OTU_table[2][5]=0.0000;
OTU_table[2][6]=0.0000;
OTU_table[2][7]=3.0000;
OTU_table[2][8]=0.0000;
OTU_table[2][9]=4.0000;
OTU_table[2][10]=1.0000;
OTU_table[2][11]=0.0000;
OTU_table[2][12]=0.0000;
OTU_table[2][13]=1.0000;
OTU_table[2][14]=2.0000;
OTU_table[2][15]=0.0000;
OTU_table[2][16]=2.0000;
OTU_table[2][17]=0.0000;
OTU_table[2][18]=0.0000;
OTU_table[2][19]=0.0000;
OTU_table[2][20]=18.0000;
OTU_table[2][21]=0.0000;
OTU_table[2][22]=2.0000;
OTU_table[2][23]=0.0000;
OTU_table[2][24]=0.0000;
OTU_table[2][25]=0.0000;
OTU_table[2][26]=0.0000;
OTU_table[2][27]=0.0000;
OTU_table[2][28]=0.0000;
OTU_table[2][29]=9.0000;
OTU_table[2][30]=0.0000;
OTU_table[2][31]=1.0000;
OTU_table[2][32]=2.0000;
OTU_table[2][33]=0.0000;
OTU_table[2][34]=1.0000;
OTU_table[2][35]=4.0000;
OTU_table[2][36]=0.0000;
OTU_table[2][37]=0.0000;
OTU_table[2][38]=13.0000;
OTU_table[2][39]=1.0000;
OTU_table[2][40]=4.0000;
OTU_table[2][41]=0.0000;
OTU_table[2][42]=1.0000;
OTU_table[2][43]=0.0000;
OTU_table[2][44]=19.0000;
OTU_table[2][45]=0.0000;
OTU_table[2][46]=0.0000;
OTU_table[2][47]=4.0000;
OTU_table[2][48]=0.0000;
OTU_table[2][49]=1.0000;
OTU_table[2][50]=1.0000;
OTU_table[3][0]='test.PCx636.630852';
OTU_table[3][1]=6.0000;
OTU_table[3][2]=2.0000;
OTU_table[3][3]=0.0000;
OTU_table[3][4]=0.0000;
OTU_table[3][5]=0.0000;
OTU_table[3][6]=0.0000;
OTU_table[3][7]=5.0000;
OTU_table[3][8]=1.0000;
OTU_table[3][9]=1.0000;
OTU_table[3][10]=1.0000;
OTU_table[3][11]=0.0000;
OTU_table[3][12]=3.0000;
OTU_table[3][13]=0.0000;
OTU_table[3][14]=0.0000;
OTU_table[3][15]=0.0000;
OTU_table[3][16]=1.0000;
OTU_table[3][17]=2.0000;
OTU_table[3][18]=0.0000;
OTU_table[3][19]=0.0000;
OTU_table[3][20]=4.0000;
OTU_table[3][21]=19.0000;
OTU_table[3][22]=0.0000;
OTU_table[3][23]=3.0000;
OTU_table[3][24]=2.0000;
OTU_table[3][25]=0.0000;
OTU_table[3][26]=0.0000;
OTU_table[3][27]=2.0000;
OTU_table[3][28]=3.0000;
OTU_table[3][29]=0.0000;
OTU_table[3][30]=0.0000;
OTU_table[3][31]=0.0000;
OTU_table[3][32]=0.0000;
OTU_table[3][33]=0.0000;
OTU_table[3][34]=0.0000;
OTU_table[3][35]=0.0000;
OTU_table[3][36]=0.0000;
OTU_table[3][37]=0.0000;
OTU_table[3][38]=0.0000;
OTU_table[3][39]=3.0000;
OTU_table[3][40]=0.0000;
OTU_table[3][41]=0.0000;
OTU_table[3][42]=0.0000;
OTU_table[3][43]=0.0000;
OTU_table[3][44]=0.0000;
OTU_table[3][45]=0.0000;
OTU_table[3][46]=0.0000;
OTU_table[3][47]=1.0000;
OTU_table[3][48]=0.0000;
OTU_table[3][49]=0.0000;
OTU_table[3][50]=0.0000;
OTU_table[4][0]='test.PCx481.630849';
OTU_table[4][1]=0.0000;
OTU_table[4][2]=0.0000;
OTU_table[4][3]=0.0000;
OTU_table[4][4]=3.0000;
OTU_table[4][5]=2.0000;
OTU_table[4][6]=0.0000;
OTU_table[4][7]=2.0000;
OTU_table[4][8]=0.0000;
OTU_table[4][9]=0.0000;
OTU_table[4][10]=0.0000;
OTU_table[4][11]=2.0000;
OTU_table[4][12]=0.0000;
OTU_table[4][13]=0.0000;
OTU_table[4][14]=1.0000;
OTU_table[4][15]=0.0000;
OTU_table[4][16]=1.0000;
OTU_table[4][17]=0.0000;
OTU_table[4][18]=0.0000;
OTU_table[4][19]=0.0000;
OTU_table[4][20]=1.0000;
OTU_table[4][21]=1.0000;
OTU_table[4][22]=4.0000;
OTU_table[4][23]=0.0000;
OTU_table[4][24]=1.0000;
OTU_table[4][25]=0.0000;
OTU_table[4][26]=0.0000;
OTU_table[4][27]=0.0000;
OTU_table[4][28]=0.0000;
OTU_table[4][29]=1.0000;
OTU_table[4][30]=0.0000;
OTU_table[4][31]=0.0000;
OTU_table[4][32]=2.0000;
OTU_table[4][33]=0.0000;
OTU_table[4][34]=5.0000;
OTU_table[4][35]=5.0000;
OTU_table[4][36]=0.0000;
OTU_table[4][37]=1.0000;
OTU_table[4][38]=13.0000;
OTU_table[4][39]=1.0000;
OTU_table[4][40]=0.0000;
OTU_table[4][41]=0.0000;
OTU_table[4][42]=7.0000;
OTU_table[4][43]=0.0000;
OTU_table[4][44]=0.0000;
OTU_table[4][45]=0.0000;
OTU_table[4][46]=6.0000;
OTU_table[4][47]=0.0000;
OTU_table[4][48]=9.0000;
OTU_table[4][49]=1.0000;
OTU_table[4][50]=1.0000;
OTU_table[5][0]='test.PCx635.630853';
OTU_table[5][1]=2.0000;
OTU_table[5][2]=0.0000;
OTU_table[5][3]=0.0000;
OTU_table[5][4]=0.0000;
OTU_table[5][5]=0.0000;
OTU_table[5][6]=0.0000;
OTU_table[5][7]=4.0000;
OTU_table[5][8]=3.0000;
OTU_table[5][9]=0.0000;
OTU_table[5][10]=1.0000;
OTU_table[5][11]=0.0000;
OTU_table[5][12]=0.0000;
OTU_table[5][13]=1.0000;
OTU_table[5][14]=0.0000;
OTU_table[5][15]=0.0000;
OTU_table[5][16]=0.0000;
OTU_table[5][17]=0.0000;
OTU_table[5][18]=0.0000;
OTU_table[5][19]=0.0000;
OTU_table[5][20]=4.0000;
OTU_table[5][21]=2.0000;
OTU_table[5][22]=4.0000;
OTU_table[5][23]=5.0000;
OTU_table[5][24]=5.0000;
OTU_table[5][25]=0.0000;
OTU_table[5][26]=0.0000;
OTU_table[5][27]=1.0000;
OTU_table[5][28]=0.0000;
OTU_table[5][29]=2.0000;
OTU_table[5][30]=0.0000;
OTU_table[5][31]=0.0000;
OTU_table[5][32]=1.0000;
OTU_table[5][33]=0.0000;
OTU_table[5][34]=0.0000;
OTU_table[5][35]=0.0000;
OTU_table[5][36]=0.0000;
OTU_table[5][37]=0.0000;
OTU_table[5][38]=0.0000;
OTU_table[5][39]=0.0000;
OTU_table[5][40]=0.0000;
OTU_table[5][41]=3.0000;
OTU_table[5][42]=2.0000;
OTU_table[5][43]=0.0000;
OTU_table[5][44]=0.0000;
OTU_table[5][45]=3.0000;
OTU_table[5][46]=1.0000;
OTU_table[5][47]=2.0000;
OTU_table[5][48]=0.0000;
OTU_table[5][49]=0.0000;
OTU_table[5][50]=0.0000;
OTU_table[6][0]='test.PCx356.630847';
OTU_table[6][1]=0.0000;
OTU_table[6][2]=0.0000;
OTU_table[6][3]=0.0000;
OTU_table[6][4]=0.0000;
OTU_table[6][5]=0.0000;
OTU_table[6][6]=0.0000;
OTU_table[6][7]=1.0000;
OTU_table[6][8]=0.0000;
OTU_table[6][9]=3.0000;
OTU_table[6][10]=6.0000;
OTU_table[6][11]=4.0000;
OTU_table[6][12]=2.0000;
OTU_table[6][13]=0.0000;
OTU_table[6][14]=0.0000;
OTU_table[6][15]=0.0000;
OTU_table[6][16]=0.0000;
OTU_table[6][17]=3.0000;
OTU_table[6][18]=0.0000;
OTU_table[6][19]=0.0000;
OTU_table[6][20]=0.0000;
OTU_table[6][21]=0.0000;
OTU_table[6][22]=2.0000;
OTU_table[6][23]=0.0000;
OTU_table[6][24]=0.0000;
OTU_table[6][25]=0.0000;
OTU_table[6][26]=0.0000;
OTU_table[6][27]=2.0000;
OTU_table[6][28]=0.0000;
OTU_table[6][29]=0.0000;
OTU_table[6][30]=0.0000;
OTU_table[6][31]=10.0000;
OTU_table[6][32]=0.0000;
OTU_table[6][33]=4.0000;
OTU_table[6][34]=0.0000;
OTU_table[6][35]=2.0000;
OTU_table[6][36]=0.0000;
OTU_table[6][37]=0.0000;
OTU_table[6][38]=5.0000;
OTU_table[6][39]=0.0000;
OTU_table[6][40]=0.0000;
OTU_table[6][41]=0.0000;
OTU_table[6][42]=0.0000;
OTU_table[6][43]=0.0000;
OTU_table[6][44]=2.0000;
OTU_table[6][45]=0.0000;
OTU_table[6][46]=0.0000;
OTU_table[6][47]=3.0000;
OTU_table[6][48]=0.0000;
OTU_table[6][49]=0.0000;
OTU_table[6][50]=14.0000;
OTU_table[7][0]='test.PCx634.630850';
OTU_table[7][1]=5.0000;
OTU_table[7][2]=0.0000;
OTU_table[7][3]=0.0000;
OTU_table[7][4]=0.0000;
OTU_table[7][5]=0.0000;
OTU_table[7][6]=0.0000;
OTU_table[7][7]=2.0000;
OTU_table[7][8]=1.0000;
OTU_table[7][9]=0.0000;
OTU_table[7][10]=0.0000;
OTU_table[7][11]=0.0000;
OTU_table[7][12]=0.0000;
OTU_table[7][13]=1.0000;
OTU_table[7][14]=0.0000;
OTU_table[7][15]=0.0000;
OTU_table[7][16]=3.0000;
OTU_table[7][17]=2.0000;
OTU_table[7][18]=0.0000;
OTU_table[7][19]=13.0000;
OTU_table[7][20]=21.0000;
OTU_table[7][21]=1.0000;
OTU_table[7][22]=1.0000;
OTU_table[7][23]=9.0000;
OTU_table[7][24]=1.0000;
OTU_table[7][25]=5.0000;
OTU_table[7][26]=0.0000;
OTU_table[7][27]=0.0000;
OTU_table[7][28]=2.0000;
OTU_table[7][29]=0.0000;
OTU_table[7][30]=0.0000;
OTU_table[7][31]=0.0000;
OTU_table[7][32]=0.0000;
OTU_table[7][33]=0.0000;
OTU_table[7][34]=0.0000;
OTU_table[7][35]=0.0000;
OTU_table[7][36]=0.0000;
OTU_table[7][37]=0.0000;
OTU_table[7][38]=0.0000;
OTU_table[7][39]=0.0000;
OTU_table[7][40]=0.0000;
OTU_table[7][41]=0.0000;
OTU_table[7][42]=0.0000;
OTU_table[7][43]=0.0000;
OTU_table[7][44]=3.0000;
OTU_table[7][45]=0.0000;
OTU_table[7][46]=0.0000;
OTU_table[7][47]=0.0000;
OTU_table[7][48]=3.0000;
OTU_table[7][49]=0.0000;
OTU_table[7][50]=0.0000;
OTU_table[8][0]='test.PCx593.630851';
OTU_table[8][1]=0.0000;
OTU_table[8][2]=4.0000;
OTU_table[8][3]=0.0000;
OTU_table[8][4]=9.0000;
OTU_table[8][5]=8.0000;
OTU_table[8][6]=5.0000;
OTU_table[8][7]=1.0000;
OTU_table[8][8]=2.0000;
OTU_table[8][9]=0.0000;
OTU_table[8][10]=8.0000;
OTU_table[8][11]=16.0000;
OTU_table[8][12]=5.0000;
OTU_table[8][13]=4.0000;
OTU_table[8][14]=0.0000;
OTU_table[8][15]=0.0000;
OTU_table[8][16]=3.0000;
OTU_table[8][17]=1.0000;
OTU_table[8][18]=9.0000;
OTU_table[8][19]=0.0000;
OTU_table[8][20]=0.0000;
OTU_table[8][21]=0.0000;
OTU_table[8][22]=0.0000;
OTU_table[8][23]=0.0000;
OTU_table[8][24]=0.0000;
OTU_table[8][25]=0.0000;
OTU_table[8][26]=10.0000;
OTU_table[8][27]=0.0000;
OTU_table[8][28]=2.0000;
OTU_table[8][29]=0.0000;
OTU_table[8][30]=3.0000;
OTU_table[8][31]=0.0000;
OTU_table[8][32]=0.0000;
OTU_table[8][33]=2.0000;
OTU_table[8][34]=0.0000;
OTU_table[8][35]=0.0000;
OTU_table[8][36]=0.0000;
OTU_table[8][37]=4.0000;
OTU_table[8][38]=0.0000;
OTU_table[8][39]=1.0000;
OTU_table[8][40]=0.0000;
OTU_table[8][41]=2.0000;
OTU_table[8][42]=0.0000;
OTU_table[8][43]=7.0000;
OTU_table[8][44]=2.0000;
OTU_table[8][45]=0.0000;
OTU_table[8][46]=0.0000;
OTU_table[8][47]=1.0000;
OTU_table[8][48]=0.0000;
OTU_table[8][49]=3.0000;
OTU_table[8][50]=0.0000;
OTU_table[9][0]='test.PCx607.630845';
OTU_table[9][1]=3.0000;
OTU_table[9][2]=0.0000;
OTU_table[9][3]=8.0000;
OTU_table[9][4]=5.0000;
OTU_table[9][5]=7.0000;
OTU_table[9][6]=2.0000;
OTU_table[9][7]=8.0000;
OTU_table[9][8]=2.0000;
OTU_table[9][9]=0.0000;
OTU_table[9][10]=0.0000;
OTU_table[9][11]=0.0000;
OTU_table[9][12]=1.0000;
OTU_table[9][13]=0.0000;
OTU_table[9][14]=0.0000;
OTU_table[9][15]=5.0000;
OTU_table[9][16]=0.0000;
OTU_table[9][17]=0.0000;
OTU_table[9][18]=1.0000;
OTU_table[9][19]=0.0000;
OTU_table[9][20]=0.0000;
OTU_table[9][21]=0.0000;
OTU_table[9][22]=5.0000;
OTU_table[9][23]=5.0000;
OTU_table[9][24]=0.0000;
OTU_table[9][25]=0.0000;
OTU_table[9][26]=0.0000;
OTU_table[9][27]=0.0000;
OTU_table[9][28]=0.0000;
OTU_table[9][29]=0.0000;
OTU_table[9][30]=0.0000;
OTU_table[9][31]=0.0000;
OTU_table[9][32]=0.0000;
OTU_table[9][33]=0.0000;
OTU_table[9][34]=1.0000;
OTU_table[9][35]=0.0000;
OTU_table[9][36]=6.0000;
OTU_table[9][37]=0.0000;
OTU_table[9][38]=0.0000;
OTU_table[9][39]=0.0000;
OTU_table[9][40]=0.0000;
OTU_table[9][41]=0.0000;
OTU_table[9][42]=0.0000;
OTU_table[9][43]=0.0000;
OTU_table[9][44]=0.0000;
OTU_table[9][45]=6.0000;
OTU_table[9][46]=0.0000;
OTU_table[9][47]=2.0000;
OTU_table[9][48]=0.0000;
OTU_table[9][49]=0.0000;
OTU_table[9][50]=0.0000;
OTU_table[10][0]='Consensus Lineage';
OTU_table[10][1]='k__Bacteria; p__Deferribacteres; c__Deferribacteres (class); o__Deferribacterales; f__Deferribacteraceae; g__Mucispirillum; s__Mucispirillum schaedleri';
OTU_table[10][2]='k__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Clostridium; s__Clostridium cocleatum';
OTU_table[10][3]='k__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Allobaculum; s__Allobaculum sp ID4';
OTU_table[10][4]='k__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Allobaculum; s__Allobaculum sp ID4';
OTU_table[10][5]='k__Bacteria; p__Tenericutes; c__Erysipelotrichi; o__Erysipelotrichales; f__Erysipelotrichaceae; g__Allobaculum; s__Allobaculum sp ID4';
OTU_table[10][6]='k__Bacteria; p__Proteobacteria; c__Epsilonproteobacteria; o__Campylobacterales; f__Helicobacteraceae; g__Flexispira; s__Helicobacter cinaedi';
OTU_table[10][7]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__';
OTU_table[10][8]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__';
OTU_table[10][9]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__';
OTU_table[10][10]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__';
OTU_table[10][11]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__';
OTU_table[10][12]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__';
OTU_table[10][13]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__';
OTU_table[10][14]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__';
OTU_table[10][15]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__';
OTU_table[10][16]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__';
OTU_table[10][17]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__';
OTU_table[10][18]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__; g__; s__';
OTU_table[10][19]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__Bacteroides uniformis';
OTU_table[10][20]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__';
OTU_table[10][21]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Bacteroidaceae; g__Bacteroides; s__';
OTU_table[10][22]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__';
OTU_table[10][23]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__';
OTU_table[10][24]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__';
OTU_table[10][25]='k__Bacteria; p__Bacteroidetes; c__Bacteroidia; o__Bacteroidales; f__Rikenellaceae; g__Alistipes; s__';
OTU_table[10][26]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__; g__; s__';
OTU_table[10][27]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__';
OTU_table[10][28]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Ruminococcaceae; g__; s__';
OTU_table[10][29]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__';
OTU_table[10][30]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__';
OTU_table[10][31]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__';
OTU_table[10][32]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__';
OTU_table[10][33]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__';
OTU_table[10][34]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__';
OTU_table[10][35]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__';
OTU_table[10][36]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__';
OTU_table[10][37]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__';
OTU_table[10][38]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__';
OTU_table[10][39]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__';
OTU_table[10][40]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__';
OTU_table[10][41]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__';
OTU_table[10][42]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__';
OTU_table[10][43]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__';
OTU_table[10][44]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__Clostridium; s__';
OTU_table[10][45]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__';
OTU_table[10][46]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__';
OTU_table[10][47]='k__Bacteria; p__Firmicutes; c__Clostridia; o__Clostridiales; f__Lachnospiraceae; g__; s__';
OTU_table[10][48]='k__Bacteria; p__Firmicutes; c__Bacilli; o__Erysipelotrichales; f__Erysipelotrichaceae; g__; s__';
OTU_table[10][49]='k__Bacteria; p__Firmicutes; c__Bacilli; o__Lactobacillales; f__Lactobacillaceae; g__Lactobacillus; s__';
OTU_table[10][50]='k__Bacteria; p__Firmicutes; c__Bacilli; o__Lactobacillales; f__Lactobacillaceae; g__Lactobacillus; s__';
"""

params_data="""\
####QIIME WEB PARAMS FILE####

make_3d_plots:ellipsoid_smoothness	1
plot_taxa_summary:label_type	categorical
make_distance_histograms:fields	SampleID
plot_taxa_summary:dpi	80
make_rarefaction_plots:background_color	white
plot_taxa_summary:chart_type	area
make_3d_plots:vectors_axes	3
beta_diversity:metrics	unweighted_unifrac
make_3d_plots:scaling_method	unscaled
serial_or_parallel:method	Serial
make_rarefaction_plots:std_type	stddev
make_rarefaction_plots:resolution	75
plot_taxa_summary:x_width	12
make_3d_plots:background_color	black
plot_taxa_summary:y_height	6
plot_taxa_summary:labels	Phylum,Class,Order,Family,Genus
make_3d_plots:n_taxa_keep	10
make_3d_plots:polyhedron_offset	1.5
make_3d_plots:output_format	king
make_3d_plots:ellipsoid_opacity	0.33
make_2d_plots:ellipsoid_method	IQR
summarize_taxa:delimiter	';'
summarize_taxa:level	2,3,4,5,6
plot_taxa_summary:background_color	white
multiple_rarefactions:num-reps	10
make_otu_heatmap_html:num_otu_hits	5
make_rarefaction_plots:output_type	file_creation
make_2d_plots:background_color	white
summarize_taxa:md_identifier	taxonomy
make_3d_plots:ellipsoid_method	IQR
make_2d_plots:ellipsoid_opacity	0.33
plot_taxa_summary:type_of_file	pdf
plot_taxa_summary:num_categories	20
make_distance_histograms:background_color	white
make_rarefaction_plots:imagetype	png
plot_taxa_summary:bar_width	0.75
make_3d_plots:polyhedron_points	4
alpha_diversity:metrics	chao1,observed_species,PD_whole_tree"""


if __name__ == "__main__":
    main()