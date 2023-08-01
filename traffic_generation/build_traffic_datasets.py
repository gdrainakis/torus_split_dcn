from torus_integrated.traffic_generation.generator import *

# params
t_begin=0 #sec (float)
t_end=0.010 #sec (float)
avg_throughput=400e9 # 300avg=75intra+170inter, 640avg=140intra+200inter #4a2_1600, 4a3_2400# exp5=1800avgtry1
qos='all'# qos packets allowed in our config {'low','med','high','all'}
total_intra_nodes=8
total_inter_nodes=16
tor_server_id=9999 # if tor_id in total_intra_nodes -> co-location (eg torid=16), else separate (eg torid=999)
low_thru_shape_param=3 # float - calibrates low packet density
med_thru_shape_param=5 # float - calibrates med packet density
high_thru_shape_param=0.005 # float - calibrates high packet density
intra_perc=0.75 # float in [0,1], percentage of traffic to be served in intra network (eg. 0.75 with high_in gives 80-20)
high_traffic_in=True # boolean - strategy to keep high qos packets in intra
###

tg=Generator(t_begin=t_begin,t_end=t_end,avg_throughput=avg_throughput,qos=qos,
                     total_intra_nodes=total_intra_nodes,total_inter_nodes=total_inter_nodes,
                     tor_server_id=tor_server_id,low_thru_shape_param=low_thru_shape_param,
                     med_thru_shape_param=med_thru_shape_param, high_thru_shape_param=high_thru_shape_param,
                    intra_perc=intra_perc,high_traffic_in=high_traffic_in)



