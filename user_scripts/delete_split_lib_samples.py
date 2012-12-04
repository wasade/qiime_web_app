#!/usr/bin/env python
# File created on 16 Mar 2011
from __future__ import division

__author__ = "Jesse Stombaugh"
__copyright__ = "Copyright 2011, The QIIME-webdev project"
__credits__ = ["Jesse Stombaugh"]
__license__ = "GPL"
__version__ = "1.2.0-dev"
__maintainer__ = "Jesse Stombaugh"
__email__ = "jesse.stombaugh@colorado.edu"
__status__ = "Development"
 
from os import path


try:
    from data_access_connections import data_access_factory
    from enums import ServerConfig,DataAccessType
    import cx_Oracle

    data_access = data_access_factory(ServerConfig.data_access_type)
except ImportError:
    print "NOT IMPORTING QIIMEDATAACCESS"
    pass

sample_arr=[\
'L4S228.274625',
'L4S90.274104',
'L4S123.274541',
'L4S130.274090',
'L4S46.274317',
'L4S92.274560',
'L4S75.274965',
'L4S47.273816',
'L4S64.273421',
'L4S214.273364',
'L4S58.274981',
'L4S195.274073',
'L4S183.273842',
'L4S72.274334',
'L4S217.274713',
'L4S256.274495',
'L4S137.274447',
'L4S263.274538',
'L4S16.274238',
'L4S14.273726',
'L4S3.274049',
'L4S136.274563',
'L4S235.274693',
'L4S15.275110',
'L4S2.275115',
'L4S227.273305',
'L4S61.274575',
'L4S175.274654',
'L4S152.274701',
'L4S151.274948',
'L4S77.273849',
'L4S56.273478',
'L4S95.275048',
'L4S252.273716',
'L4S134.275056',
'L4S255.273681',
'L4S122.274726',
'L4S208.273997',
'L4S101.274773',
'L4S34.273419',
'L4S32.274443',
'L4S173.273443',
'L4S215.274341',
'L4S89.274390',
'L4S63.274255',
'L4S260.274084',
'L4S170.273867',
'L4S221.275124',
'L4S135.273226',
'L4S39.274588',
'L4S118.273855',
'L4S38.275158',
'L4S185.274210',
'L4S233.273529',
'L4S286.274055',
'L4S49.274247',
'L4S187.274677',
'L4S225.274377',
'L4S117.273939',
'L4S133.273639',
'L4S110.274943',
'L4S66.273817',
'L4S251.274384',
'L4S8.274786',
'L4S285.274217',
'L4S204.274577',
'L4S28.274864',
'L4S36.273864',
'L4S6.274137',
'L4S176.275098',
'L4S198.273770',
'L4S4.273869',
'L4S254.275097',
'L4S120.274601',
'L4S76.274075',
'L4S194.275019',
'L4S26.274218',
'L4S67.274944',
'L4S42.273513',
'L4S129.275011',
'L4S159.274898',
'L4S142.273680',
'L4S91.274790',
'L4S259.274847',
'L4S206.273845',
'L4S11.274407',
'L4S262.273472',
'L4S19.274791',
'L4S157.274913',
'L4S74.273368',
'L4S35.274301',
'L4S132.273739',
'L4S282.273852',
'L4S201.274355',
'L4S115.273837',
'L4S87.274154',
'L4S103.273853',
'L4S190.274189',
'L4S219.273703',
'L4S5.273376',
'L4S203.274402',
'L4S156.274308',
'L4S98.273763',
'L4S29.274036',
'L4S1.273228',
'L4S243.274813',
'L4S12.275133',
'L4S82.275123',
'L4S273.274149',
'L4S283.274460',
'L4S27.273795',
'L4S23.275107',
'L4S193.273943',
'L4S62.274646',
'L4S57.274432',
'L4S160.274108',
'L4S94.273505',
'L4S278.274739',
'L4S71.274481',
'L4S202.273235',
'L4S253.274274',
'L4S261.274930',
'L4S21.273906',
'L4S154.274326',
'L4S229.273698',
'L4S249.273807',
'L4S93.273870',
'L4S266.274150',
'L4S165.274427',
'L4S69.274668',
'L4S181.274912',
'L4S40.274573',
'L4S25.274037',
'L4S45.274753',
'L4S65.275071',
'L4S149.274438',
'L4S150.273537',
'L4S245.273426',
'L4S146.273317',
'L4S86.274094',
'L4S186.273861',
'L4S143.274451',
'L4S52.273378',
'L4S247.273983',
'L4S88.273311',
'L4S184.274599',
'L4S18.274426',
'L4S240.275147',
'L4S207.274801',
'L4S128.273697',
'L4S106.273395',
'L4S155.273702',
'L4S250.273987',
'L4S81.273408',
'L4S54.274756',
'L4S24.274064',
'L4S162.273791',
'L4S163.274482',
'L4S200.274383',
'L4S218.275057',
'L4S171.273212',
'L4S37.274769',
'L4S44.274578',
'L4S147.274736',
'L4S59.274899',
'L4S164.274024',
'L4S242.275018',
'L4S114.273756',
'L4S78.273629',
'L4S70.275142',
'L4S30.274615',
'L4S274.273701',
'L4S100.273740',
'L4S43.274641',
'L4S179.274591',
'L4S17.273844',
'L4S119.274207',
'L4S153.273928',
'L4S284.273517',
'L4S230.274429',
'L4S257.274976',
'L4S112.273401',
'L4S265.274767',
'L4S161.275088',
'L4S104.274716',
'L4S182.274989',
'L4S31.274252',
'L4S121.273488',
'L4S178.274459',
'L4S102.275028',
'L4S138.274376',
'L4S167.274554',
'L4S10.274622',
'L4S127.274754',
'L4S189.275114',
'L4S223.273496',
'L4S108.274991',
'L4S158.274062',
'L4S125.274323',
'L4S212.274802',
'L4S269.275022',
'L4S41.273728',
'L4S22.273742',
'L4S68.275042',
'L4S236.274820',
'L4S60.274173',
'L4S241.273621',
'L4S97.273347',
'L4S109.273641',
'L4S220.274525',
'L4S131.275135',
'L4S105.274484',
'L4S33.274689',
'L4S216.273617',
'L4S148.274292',
'L4S107.275064',
'L4S126.273575',
'L4S271.273427',
'L4S124.274897',
'L4S209.274347',
'L4S48.273908',
'L4S7.273295',
'L4S166.274315',
'L4S9.275080',
'L4S144.274046',
'L4S84.274980',
'L4S287.274631',
'L4S168.274699',
'L4S116.274550',
'L4S55.273741',
'L4S211.273225',
'L4S196.273506',
'L4S79.274410',
'L4S231.273354',
'L4S239.275052',
'L4S210.274611',
'L4S234.273397',
'L4S53.273343',
'L4S238.273642',
'L4S226.273510',
'L4S248.274393',
'L4S169.274837',
'L4S174.273514',
'L4S275.273953',
'L4S113.274623',
'L4S224.273365',
'L4S177.274729',
'L4S258.273669',
'L4S139.273988',
'L4S180.275094',
'L4S13.273883',
'L4S50.274371',
'L4S246.274195',
'L4S111.275082',
'L4S244.273659',
'L4S140.274194',
'L4S270.273519',
'L4S191.273409',
'L4S80.274159',
'L4S222.274752',
'L4S172.273773',
'L4S188.274117',
'L4S51.273968',
'L4S199.273553',
'L4S279.273227',
'L4S145.273686',
'L4S73.274762']





for i,sample in enumerate(sample_arr):
    con = data_access.getSFFDatabaseConnection()
    cur = con.cursor()
    print str(i)
    statement='delete from split_library_read_map where split_library_run_id=1036 and sample_name=\'%s\'' % (str(sample))
    print statement
    results = cur.execute(statement)
    con.commit()
    

    

