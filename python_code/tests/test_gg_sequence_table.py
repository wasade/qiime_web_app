#!/usr/bin/env python

"""This is a functional test of the SFF.GREENGENES_REFERENCE table

For this test, we are making sure that we

a) have information for each prokMSA id in our test set
b) make sure we only have a single SSU_SEQUENCE_ID per test prokMSA
c) have only a single sequence for the SSU_SEQUENCE_ID
d) make sure we have the correct sequence and metadata
"""

from cogent.util.unit_test import TestCase, main
from data_access_connections import data_access_factory
from enums import ServerConfig

__author__ = "Daniel McDonald"
__copyright__ = "Copyright 2009-2010, Qiime Web Analysis"
__credits__ = ["Daniel McDonald", "Jesse Stombaugh"]
__license__ = "GPL"
__version__ = "1.0.0.dev"
__maintainer__ = ["Daniel McDonald"]
__email__ = "mcdonadt@colorado.edu"
__status__ = "Production"

qda = data_access_factory(ServerConfig.data_access_type)


class LoadDBGreenGenesReferenceTable(TestCase):
    def setUp(self):
        """Grab a connection"""
        self.con = qda.getSFFDatabaseConnection()
        self.cur = self.con.cursor()
    def tearDown(self):
        """Make sure to close the connection"""
        self.con.close()

    def test_verify_regerence_data(self):
        """Grab sequences and metadata strings from test prokmsas and test"""
        for prokmsa in test_mapping:
            res = self.cur.execute("""SELECT SSU_SEQUENCE_ID 
                                      FROM GREENGENES_REFERENCE 
                                      WHERE PROKMSA_ID=%d""" % prokmsa)
            all_res = list(res)
            if len(all_res) == 0:
                self.fail("No records found for prokMSA id %d" % prokmsa)
            if len(all_res) > 1:
                self.fail("Multiple records found for prokMSA id %d" % prokmsa)
            ssu_id = all_res[0][0]

            acc, decision, coreset_member, seq = test_mapping[prokmsa]
            exp = (acc, decision, coreset_member)
            res = self.cur.execute("""SELECT GENBANK_ACC_ID,DECISION,CORE_SET_MEMBER 
                            FROM GREENGENES_REFERENCE
                            WHERE SSU_SEQUENCE_ID=%d""" % ssu_id)
            all_res = list(res)
            if len(all_res) == 0: 
                self.fail("No records found for ssu id %d" % ssu_id)
            if len(all_res) > 1:
                self.fail("Multiple records found for ssu id %d" % ssu_id)
            self.assertEqual(all_res[0], exp)

            res = self.cur.execute("""SELECT SEQUENCE_STRING
                                      FROM SSU_SEQUENCE
                                      WHERE SSU_SEQUENCE_ID=%d""" % ssu_id)
            all_res = list(res)
            if len(all_res) == 0:
                self.fail("No sequences found for ssu id %d" % ssu_id)
            if len(all_res) > 1:
                self.fail("Multiple sequences found for ssu id %d" % ssu_id)
            self.assertEqual(all_res[0][0], seq)

# the following 100 prokMSA id and other information were randomly 
# (without replacement) chosen from the set of all prokMSA ids 
# known as of 7/26/10

test_seqs = """\
357423	FM873861.1	clone	0	GACGAACGCUGGCGGCGUGCUUAACACAUGCAAGUCGAGCGGAAGGCCCUUCGGGGUACUCGAGCGGCGAACGGGUGAGUAACACGUGAGCAACCUGCCCUAGACUUUGGGAUAACCCUCGGAAACGGGGGCUAAUACCGGAUAUUCCGAUUCUGUCGCAAGGCGGUUUUGGGAAAGUUUUCGGUCUGGGAUGGGCUCGCGGCCUAUCAGCUUGUUGGUGGGGUGAUGGCCUACCAAGGCGACGACGGGUAGCCGGCCUGAGAGGGCGACCGGCCACACUGGGACUGAGACACGGCCCAGACUCCUACGGGAGGCAGCAGUGGGGAAUAUUGCACAAUGGGCGGAAGCCUGAUGCAGCGACGCCGCGUGAGGGAUGACGGCCUUCGGGUUGUAAACCUCUUUCAGCUCCGACGAAGCGCAAGUGACGGUAGGAGCAGAAGAAGCGCCGGCCAACUACGUGCCAGCAGCCGCGGUAAGACGUAGGGCGCGAGCGUUGUCCGGAAUUAUUGGGCGUAAAGAGCUCGUAGGCGGCUUGUCGCGUCGACUGUGAAAACCCGCGGCUCAACUGCGGACCUGCAGCCGAUACGGGCAGGCUAGAGUUCGGUAGGGGAGACUGGAAUUCCUGGUGUAGCGGUGAAAUGCGCAGAUAUCAGGAGGAACACCGAUGGCGAAGGCUGGUCUCUGGGCCGAUACUGACGCUGAGGAGCGAAAGCGUGGGGAGCGAACAGGAUUAGAUACCCUGGUAGUCCACGCUGUAAACGUUGGGCGCUAGGUGUGGGGGACCUCCGGUUCUCUGUGCCGCAGCUAACGCAUUAAGCGCCCCGCCUGGGGAGUACGGCCGCAAGGCUAAAACUCAAAGGAAUUGACGGGGGCCCGCACAAGCGGCGGAGCAUGCGGAUUAAUUCGAUGCAACGCGAAGAACCUUACCUGGGUUUGACAUCCCGGAAAACUCGCAGAGAUGCGGGGUCCUUCGGGGCCGGUGACAGGUGGUGCAUGGCUGUCGUCAGCUCGUGUCGUGAGAUGUUGGGUUAAGUCCCGCAACGAGCGCAACCCUCGUUCGAUGUUGCCAGCGGGUUAUGCCGGGGACUCAUCGAAGACUGCCGGGGUCAACUCGGAGGAAGGUGGGGAUGACGUCAAGUCAUCAUGCCCCUUAUGUCCAGGGCUUCACGCAUGCUACAAUGGCCGGUACAAAGGGCUGCGAUACCGUGAGGUGGAGCGAAUCCCAAAAAGCCGGUCUCAGUUCGGAUCGGGGUCUGCAACUCGACCCCGUGAAGUCGGAGUCGCUAGUAAUCGCAGAUCAGCAACGCUGCGGUGAAUACGUUCCCGGGCCUUGUACACACCGCCCGUCACGUCACGAAAGUCGGCAACACCCGAAGCCCAUGGCCUAACCCCUUGGGGAGGGAGUGGUCGAAGGUGGGGCUGGCGAUUGGGACGAAGUCGUAACAAGGUAGCCGUACCGGAAGG
131847	AY993427.1	clone	0	CGAACGGGCUAUAUUGAAACUAGUGAUGUGGUUAGUGGCGGACGGGUGAGUAACGCGUGGAGAACCUGCCGUAUACUGGGGGAUAACACUUAGAAAUAGGUGCUAAUACCGCAUAAGCGCACAGCUUCGCAUGAAGCAGUGUGAAAAACUCCGGUGGUAUACGAUGGAUCCGCGUCUGAUUAGCUGGUUGGCGGGGUAACAGCCCACCAAGGCGACGAUCAGUAGCCGGCCUGAGAGGGUGAACGGCCACAUUGGGACUGAGACACGGCCCAAACUCCUACGGGAGGCAGCAGUGGGGAAUAUUGCACAAUGGGGGAAACCCUGAUGCAGCGACGCCGCGUGAGUGAAGAAGUAUUUCGGUAUGUAAAGCUCUAUCAGCAGGGAAGAAAAUGACGGUACCUGACUAAGAAGCCCCGGCUAACUACGUGCCAGCAGCCGCGGUAAUACGUAGGGGGCAAGCGUUAUCCGGAUUUACUGGGUGUAAAGGGAGCGUAGACGGCAGCGCAAGUCUGAAGUGAAAUCCCAUGGCUUAACCAUGGAACUGCUUUGGAAACUGUGCAGCUAGAGUGCAGGAGAGGUAAGCGGAAUUCCUAGUGUAGCGGUGAAAUGCGUAGAUAUUAGGAGGAACACCAGUGGCGAAGGCGGCUUACUGGACUGUAACUGACGUUGAGGCUCGAAAGCGUGGGGAGCAAACAGGAUUAGAUACCCUGGUAGUCCACGCCGUAAACGAUGAUUACUAGGUGUUGGGGGACCAAGGUCCUUCGGUGCCGGCGCAAACGCAUUAAGUAAUCCACCUGGGGAGUACGUUCGCAAGAAUGAAACUCAAAGGAAUUGACGGGGACCCGCACAAGCGGUGGAGCAUGUGGUUUAAUUCGAAGCAACGCGAAGAACCUUACCUGGUCUUGACAUCCCGAUACAAGUGAGCAAAGUCACUUUCCCUUCGGGGAUUGGAGACAGGUGGUGCAUGGUUGUCGUCAGCUCGUGUCGUGAGAUGUUGGGUUAAGUCCCGCAACGAGCGCAACCCCUAUUUCCAGUAGCCAGCAGGUAGAGCUGGGCACUCUGGAGAGACUGCCCGGGAUAACCGGGAGGAAGGCGGGGAUGACGUCAAAUUAUCAUGCCCCUUAUGAUCAGGGCUACACACGUGCUACAAUGGCGUAAACAAAGGGAAGCGAGACGGUGACGUUGAGCAAAUCCCAAAAAUAACGUCCCAGUUCGGAUUGUAGUCUGCAACUCGACUACAUGAAGCUGGAAUCGCUAGUA
""".splitlines()

test_mapping = {}
for l in test_seqs:
    fields = l.strip().split('\t')
    test_mapping[int(fields[0])] = (fields[1], fields[2], int(fields[3]), fields[4])

if __name__ == '__main__':
    main()
            

