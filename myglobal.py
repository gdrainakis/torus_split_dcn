import os

# Param set
ROOT='[add_root_path_here]'
CURR_DATASET='[add_dataset_name_here]'

###
TRAFFIC_DATASETS_FOLDER=os.path.join(ROOT,'traffic_datasets')
CURR_TRAFFIC_DATASET_FOLDER=os.path.join(TRAFFIC_DATASETS_FOLDER,CURR_DATASET)
TRANSMISSION_INFO_FOLDER=os.path.join(ROOT,'transmission_info')
TORUS_MATRIX_FILE=os.path.join(TRANSMISSION_INFO_FOLDER,'torus_matrix.txt')
LOGS_FOLDER=os.path.join(ROOT,'logs')

CABLE_LEN=2.5 # m
FIBER_FACTOR=1.5 # 1.5 if typical fyber, 1 if hollow-core (=refraction index)
SPEED=3e8/FIBER_FACTOR # speed in fiber=speed of light/factor
PROPAGATION_TIME=(2*CABLE_LEN)/(SPEED) #PROPAGATION_TIME= 2 * cable_len (RTT) /speed
print('propagationtime (ns)='+str(PROPAGATION_TIME*1e9))
ID_DIFF=1
MAX_PACKET_SIZE=1500 #bytes
MIN_PACKET_SIZE=64 #bytes
CYCLE_SIZE=1500 #bytes
TOTAL_BUFFS_PER_NODE=3
DEFAULT_UNLUCKY_NODE_ID=1
DEFAULT_LUCKY_NUM=10

# Will be set on startup
CONTROL_MSG_PACKS_PER_BUFF=46
CONTROL_MSG_PACKS_PER_BUFF_FOR_INTRA=46 # apply in split network with shared channel
CONTROL_MSG_PACKS_PER_BUFF_FOR_INTER=46 # apply in split network with shared channel
CONTROL_MINIPACK_SIZE=9 #bits
BONUS_MSG_BITSIZE=7 #bits
BREAK_POSITION=3
CUT_1=3
CUT_2=6
CUT_3=8
LUCKY_SLOT_LEN=3
UNLUCKY_SLOT_LEN=2
STR_SOURCE_DEST_ID="{0:03b}"
TOTAL_UNLUCKY_NODES=1
TOTAL_LUCKY_NODES=1
ASSIGN_CHANNEL_POLICY='ALL_BIG'
INTRA_CYCLE_GUARD_BAND=3 # bytes
MAX_SLOTS_FOR_SMALL_PACKS=None
INTER_CYCLE_GUARD_BAND=3 # bytes
DEDICATED_UL_CYCLE_GUARD_BAND=3 # bytes

# logging
OUTPUT_TABLE_TITLE='packet_id,time,packet_size,packet_qos,source_id,tor_id,destination_id,destination_tor,' \
                    'time_intra_buffer_in,time_intra_buffer_out,time_intra_trx_in,time_intra_trx_out,' \
                   'time_tor_buffer_in,time_tor_buffer_out,time_tor_trx_in,time_tor_trx_out,' \
                   'time_inter_buffer_in,time_inter_buffer_out,time_inter_trx_in,time_inter_trx_out\n'

