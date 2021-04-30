import time
import datetime
import crcmod
import sys
from optparse import OptionParser
from binascii import hexlify, unhexlify

parser = OptionParser()    
parser.add_option("-s", "--stmsi", dest="stmsi", help="S-TMSI in hex digits (full or last 32 bits)")
parser.add_option("-t", "--tedrx", dest="tedrx", help="Tedrx value in Hyper-Frames (2-1024)")
parser.add_option("-p", "--ptw", dest="ptw", help="PTW in seconds") 
parser.add_option("-U", "--reference", dest="reference", action="store_true", default=False, help="UTC time reference (1972/06/30 00:00:00). Default is GPS (1980/01/06 00:00:00)")
parser.add_option("-D", "--date", dest="date", help="Specify start date. Default is to use current time.")
  
(options, args) = parser.parse_args()

#####################
####  VARIABLES  ####
#####################

H_SFN_SIZE = 1024
SFN_DURATION = 10.24   # seconds
FRAME_DURATION = 0.01  # seconds

stmsi = options.stmsi
tedrx = int(options.tedrx)
ptw = float(options.ptw)
utc_time_reference = options.reference
current_date = options.date

hyperframe_cycle = H_SFN_SIZE * SFN_DURATION  # 1024*10,24 seconds = 2 hours, 54 minutes and 46 seconds

if current_date is None:
    current_date = datetime.datetime.fromtimestamp(time.time())
else:
    try:
        current_date = datetime.datetime.strptime(current_date, '%Y-%m-%d %H:%M:%S')
    except:
        try:
            current_date = datetime.datetime.strptime(current_date, '%Y/%m/%d %H:%M:%S')        
        except:
            print('Wrong data format. Use format yyyy-mm-dd hh:mm:ss or yyyy/mm/dd hh:mm:ss\nExiting.')
            exit(1)

if utc_time_reference is False: #gps
    initial_date = datetime.datetime(1980,1,6,0,0,0)
    leap_seconds = 18
else:
    initial_date = datetime.datetime(1972,6,30,0,0,0)
    leap_seconds = 27    


################################################
#####  36.304 - 7.3	Paging in extended DRX #####
################################################

s_tmsi_last32 = unhexlify(stmsi[-8:])  # 32 least significant bits

crc32_func = crcmod.mkCrcFun(0x104c11db7, initCrc=0, xorOut=0xFFFFFFFF, rev=False)
hashed_id = crc32_func(s_tmsi_last32)

ue_id_h_nbiot = hashed_id >> 20  # first 12 bits for NB-IOT

paging_hyperframe = ue_id_h_nbiot % tedrx #first H-SPN
ptw_start = 256*((ue_id_h_nbiot // tedrx) % 4)
ptw_end = int((ptw_start + ptw*100 -1) % 1024)

tedrx_interval = tedrx * SFN_DURATION

diff_seconds = (current_date-initial_date).total_seconds()

last_tedrx_interval = diff_seconds // tedrx_interval
last_hyperframe_cycle = diff_seconds // hyperframe_cycle
last_hsfn = (last_tedrx_interval*tedrx - last_hyperframe_cycle*H_SFN_SIZE) #number of SFNs since last H-SFN 0

print('\nLast H-SFN 0:', initial_date + datetime.timedelta(seconds=last_hyperframe_cycle*hyperframe_cycle - leap_seconds))
print('Last possible H-SFN start for given Tedrx:', initial_date + datetime.timedelta(seconds=last_tedrx_interval*tedrx_interval - leap_seconds))
print('\nUE_ID_H:',ue_id_h_nbiot,'\nFirst H-SPN for PH:',paging_hyperframe,'\nPTW_Start:',ptw_start,'\nPTW_End',ptw_end)
print('\nPossible paging times (UTC) :\n')
for i in range(20):
    date_hsfn = int((last_hsfn+paging_hyperframe+i*tedrx) % H_SFN_SIZE)
    date_hsfn_bits = '{0:010b}'.format(date_hsfn)
    print('\t->', 'H-SFN:',date_hsfn, '\t', '('+date_hsfn_bits+')', '\tdate:', initial_date + datetime.timedelta(seconds=last_tedrx_interval*tedrx_interval + i*tedrx_interval + paging_hyperframe*SFN_DURATION + ptw_start*FRAME_DURATION - leap_seconds))
print()
