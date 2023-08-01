import os
import csv
import datetime
import math
import random
from torus_integrated import myglobal
from scipy.stats import genpareto
import numpy as numpy
from scipy.stats import weibull_min
from pathlib import Path

class Generator():
    def __init__(self, t_begin, t_end, avg_throughput, qos, total_intra_nodes, total_inter_nodes, tor_server_id,
                 low_thru_shape_param, med_thru_shape_param, high_thru_shape_param, intra_perc, high_traffic_in):

        # basic config params
        self.t_begin = t_begin
        self.t_end = t_end
        self.avg_throughput = avg_throughput
        self.qos = qos
        self.total_intra_nodes = total_intra_nodes
        self.total_inter_nodes = total_inter_nodes
        self.tor_server_id = tor_server_id
        self.low_thru_shape_param = low_thru_shape_param
        self.med_thru_shape_param = med_thru_shape_param
        self.high_thru_shape_param = high_thru_shape_param
        self.intra_perc = intra_perc
        self.high_traffic_in = high_traffic_in

        # support params
        self.high_big_packs_size = 1500
        self.high_big_packs_prob = 0
        self.high_small_packs_size = 64
        self.high_small_packs_prob = 1

        self.med_big_packs_size = 1500
        self.med_big_packs_prob = 0.3
        self.med_small_packs_size = 64
        self.med_small_packs_prob = 0.7

        self.low_big_packs_size = 1500
        self.low_big_packs_prob = 0.4
        self.low_small_packs_size = 64
        self.low_small_packs_prob = 0.6

        self.sigma_lognormal_low = 6
        self.sigma_lognormal_med = 3
        self.alpha_weibull = 0.1
        self.c_pareto = 0.5

        self.intra_nodes_list = [x for x in range(1, total_intra_nodes + 1)]
        self.inter_tor_list = [x for x in range(1, total_inter_nodes + 1)]
        self.avg_throughput_per_node = self.avg_throughput / self.total_intra_nodes
        self.csv_names = 'packet_id,time,packet_size,packet_qos,source_id,tor_id,destination_id,destination_tor\n'
        self.config_file_name='config.txt'
        self.curr_packet_id = 0

        # run generator
        self.save_folder = self.create_folder()
        self.log_config()
        self.run()

    def create_folder(self):
        mynewfolder = self.get_timestamp_to_string()
        mypath = os.path.join(myglobal.ROOT, myglobal.TRAFFIC_DATASETS_FOLDER)
        mypath = os.path.join(mypath, mynewfolder)
        Path(mypath).mkdir(parents=True, exist_ok=True)
        return mypath

    def get_timestamp_to_string(self):
        mytime = str(datetime.datetime.now())
        mytime = mytime.replace('-', '_')
        mytime = mytime.replace(' ', '_')
        mytime = mytime.replace(':', '_')
        mytime = mytime.replace('.', '_')
        return mytime

    def log_config(self):
        print('Logging config...')
        current_file = os.path.join(self.save_folder, self.config_file_name)
        mystr=self.get_config()
        with open(current_file, mode='a') as file:
            file.write(mystr)

    def get_config(self):
        mystr=''
        mystr = mystr + 't_begin=' + str(self.t_begin) + '\n'
        mystr = mystr + 't_end=' + str(self.t_end) + '\n'
        mystr = mystr + 'avg_throughput=' + str(self.avg_throughput) + '\n'
        mystr = mystr + 'qos=' + str(self.qos) + '\n'
        mystr = mystr + 'total_intra_nodes=' + str(self.total_intra_nodes) + '\n'
        mystr = mystr + 'total_inter_nodes=' + str(self.total_inter_nodes) + '\n'
        mystr = mystr + 'tor_server_id=' + str(self.tor_server_id) + '\n'
        mystr = mystr + 'low_thru_shape_param=' + str(self.low_thru_shape_param) + '\n'
        mystr = mystr + 'med_thru_shape_param=' + str(self.med_thru_shape_param) + '\n'
        mystr = mystr + 'high_thru_shape_param=' + str(self.high_thru_shape_param) + '\n'
        mystr = mystr + 'intra_perc=' + str(self.intra_perc) + '\n'
        mystr = mystr + 'high_traffic_in=' + str(self.high_traffic_in) + '\n'
        return mystr

    def run(self):
        for tor in self.inter_tor_list:
            for node in self.intra_nodes_list:
                if node!=self.tor_server_id:
                    my_tor = [tor]
                    my_node = [node]
                    intra_dest_list = [item for item in self.intra_nodes_list if item not in my_node]
                    intra_dest_list = [item for item in intra_dest_list if item != self.tor_server_id]
                    inter_dest_list = [item for item in self.inter_tor_list if item not in my_tor]

                    self.export_per_node_dataset(intra_source_node=node, intra_dest_list=intra_dest_list,
                                                 inter_source_tor=tor, inter_dest_list=inter_dest_list)

    def export_per_node_dataset(self, intra_source_node, intra_dest_list, inter_source_tor, inter_dest_list):

        csv_content = ''

        if self.qos == 'all' or self.qos == 'low':
            low_packets = self.generate_packets_low_qos(intra_source_node=intra_source_node,
                                                        intra_dest_list=intra_dest_list,
                                                        inter_source_tor=inter_source_tor,
                                                        inter_dest_list=inter_dest_list)

            if low_packets is None:
                print('Warning: No low packets generated - check distribution params')
                return 0
            else:
                print(len(low_packets))
                csv_content = csv_content + low_packets

        if self.qos == 'all' or self.qos == 'med':
            med_packets = self.generate_packets_med_qos(intra_source_node=intra_source_node,
                                                        intra_dest_list=intra_dest_list,
                                                        inter_source_tor=inter_source_tor,
                                                        inter_dest_list=inter_dest_list)
            if med_packets is None:
                print('Warning: No med packets generated - check distribution params')
                return 0
            else:
                print(len(med_packets))
                csv_content = csv_content + med_packets

        if self.qos == 'all' or self.qos == 'high':
            high_packets = self.generate_packets_high_qos(intra_source_node=intra_source_node,
                                                          intra_dest_list=intra_dest_list,
                                                          inter_source_tor=inter_source_tor,
                                                          inter_dest_list=inter_dest_list)
            if high_packets is None:
                print('Warning: No high packets generated - check distribution params')
                return 0
            else:
                print(len(high_packets))
                csv_content = csv_content + high_packets

        output_table = self.csv_names + csv_content

        print('Writing...')
        curr_dataset_name = 'tor' + str(inter_source_tor) + 'node' + str(intra_source_node) + ".csv"
        current_file = os.path.join(self.save_folder, curr_dataset_name)
        with open(current_file, mode='a') as file:
            file.write(output_table + '\n')
        print('Sorting...')
        with open(current_file, 'r', newline='') as f_input:
            csv_input = csv.DictReader(f_input)
            data = sorted(csv_input, key=lambda row: (float(row['time']), float(row['packet_id'])))
            print(len(data))
        print('Rewriting...')
        with open(current_file, 'w', newline='') as f_output:
            csv_output = csv.DictWriter(f_output, fieldnames=csv_input.fieldnames)
            csv_output.writeheader()
            csv_output.writerows(data)

    def generate_packets_low_qos(self, intra_source_node, intra_dest_list, inter_source_tor, inter_dest_list):
        csv_reader = ''
        debug_curr_packet_id = self.curr_packet_id
        avg_packet_size_low = self.get_avg_packet_size(small_size=self.low_small_packs_size,
                                                       small_prob=self.low_small_packs_prob,
                                                       big_size=self.low_big_packs_size,
                                                       big_prob=self.low_big_packs_prob)
        avg_node_thru = self.avg_throughput_per_node * self.low_thru_shape_param
        avg_traffic = avg_node_thru * (self.t_end - self.t_begin)  # bytes
        avg_packet_num = round(avg_traffic / avg_packet_size_low)

        on_times = self.get_on_off_times(start=self.t_begin, stop=self.t_end, packet_num=avg_packet_num,
                                         c_pareto=self.c_pareto, sigma=self.sigma_lognormal_low)
        total_len = len(on_times)

        for on_time in on_times:
            avg_traffic = avg_node_thru * (on_time[1] - on_time[0])
            avg_packet_num = max(round(avg_traffic / avg_packet_size_low), 1)
            interval_times = self.get_interval_times_weibull(start=on_time[0], stop=on_time[1], packet_num=avg_packet_num, alpha=self.alpha_weibull)
            for inttime in interval_times:
                new_time = inttime
                packet_size = self.get_variable_packet_size(small_size=self.low_small_packs_size,
                                                            big_size=self.low_big_packs_size,
                                                            small_prob=self.low_small_packs_prob)
                qos = 'low'
                luckynum = random.uniform(0, 1)
                if luckynum <= self.intra_perc:
                    destination_id = random.sample(intra_dest_list, 1)[0]
                    destination_tor = inter_source_tor
                else:
                    destination_id = 0
                    destination_tor = random.sample(inter_dest_list, 1)[0]

                csv_reader = csv_reader + str(self.curr_packet_id) + ',' + str(new_time) + ',' \
                             + str(packet_size) + ',' + str(qos) + ',' + str(intra_source_node) + ',' \
                             + str(inter_source_tor) + ',' + str(destination_id) + ',' + str(destination_tor) + '\n'

                self.curr_packet_id = self.curr_packet_id + 1
                print('tor' + str(inter_source_tor) + ',node' + str(intra_source_node) +
                      ',low progress %=' + str((self.curr_packet_id - debug_curr_packet_id) * 100 / total_len))
        return csv_reader

    def generate_packets_med_qos(self, intra_source_node, intra_dest_list, inter_source_tor, inter_dest_list):
        csv_reader = ''
        debug_curr_packet_id = self.curr_packet_id
        avg_packet_size_med = self.get_avg_packet_size(small_size=self.med_small_packs_size,
                                                       small_prob=self.med_small_packs_prob,
                                                       big_size=self.med_big_packs_size,
                                                       big_prob=self.med_big_packs_prob)
        avg_node_thru = self.avg_throughput_per_node * self.med_thru_shape_param
        avg_traffic = avg_node_thru * (self.t_end - self.t_begin)  # bytes
        avg_packet_num = round(avg_traffic / avg_packet_size_med)
        interval_times = self.get_interval_times_lognormal(start=self.t_begin, stop=self.t_end, packet_num=avg_packet_num,
                                                           sigma=self.sigma_lognormal_med)
        total_len = len(interval_times)
        for inttime in interval_times:
            new_time = inttime
            packet_size = self.get_variable_packet_size(small_size=self.med_small_packs_size,
                                                        big_size=self.med_big_packs_size,
                                                        small_prob=self.med_small_packs_prob)
            qos = 'med'
            luckynum = random.uniform(0, 1)
            if luckynum <= self.intra_perc:
                destination_id = random.sample(intra_dest_list, 1)[0]
                destination_tor = inter_source_tor
            else:
                destination_id = 0
                destination_tor = random.sample(inter_dest_list, 1)[0]

            csv_reader = csv_reader + str(self.curr_packet_id) + ',' + str(new_time) + ',' \
                         + str(packet_size) + ',' + str(qos) + ',' + str(intra_source_node) + ',' \
                         + str(inter_source_tor) + ',' + str(destination_id) + ',' + str(destination_tor) + '\n'
            self.curr_packet_id = self.curr_packet_id + 1
            print('tor' + str(inter_source_tor) + ',node' + str(intra_source_node) +
                  ',med progress %=' + str((self.curr_packet_id - debug_curr_packet_id) * 100 / total_len))
        return csv_reader

    def generate_packets_high_qos(self, intra_source_node, intra_dest_list, inter_source_tor, inter_dest_list):
        csv_reader = ''
        debug_curr_packet_id = self.curr_packet_id
        avg_packet_size_high = self.get_avg_packet_size(small_size=self.high_small_packs_size,
                                                        small_prob=self.high_small_packs_prob,
                                                        big_size=self.high_big_packs_size,
                                                        big_prob=self.high_big_packs_prob)
        avg_node_thru = self.avg_throughput_per_node * self.high_thru_shape_param
        avg_traffic = avg_node_thru * (self.t_end - self.t_begin)  # bytes
        avg_packet_num = round(avg_traffic / avg_packet_size_high)
        interval_times = self.get_interval_times_exponential(start=self.t_begin, stop=self.t_end, packet_num=avg_packet_num)
        total_len = len(interval_times)
        for inttime in interval_times:
            new_time = inttime
            packet_size = avg_packet_size_high
            qos = 'high'
            luckynum = random.uniform(0, 1)
            if (luckynum <= self.intra_perc) or self.high_traffic_in:
                destination_id = random.sample(intra_dest_list, 1)[0]
                destination_tor = inter_source_tor
            else:
                destination_id = 0
                destination_tor = random.sample(inter_dest_list, 1)[0]

            csv_reader = csv_reader + str(self.curr_packet_id) + ',' + str(new_time) + ',' \
                         + str(packet_size) + ',' + str(qos) + ',' + str(intra_source_node) + ',' \
                         + str(inter_source_tor) + ',' + str(destination_id) + ',' + str(destination_tor) + '\n'
            self.curr_packet_id = self.curr_packet_id + 1
            print('tor' + str(inter_source_tor) + ',node' + str(intra_source_node) +
                  ',high progress %=' + str((self.curr_packet_id - debug_curr_packet_id) * 100 / total_len))
        return csv_reader

    def get_variable_packet_size(self, small_size, big_size, small_prob):
        myrand = random.random()
        if (myrand <= small_prob):
            ret = small_size
        else:
            ret = big_size
        return ret

    def get_avg_packet_size(self, small_size, small_prob, big_size, big_prob):
        ret = small_size * small_prob + big_size * big_prob
        return ret

    def get_interval_times_exponential(self, start, stop, packet_num):
        mean_interval_time = (stop - start) / packet_num
        interval_times_abs = numpy.random.exponential(scale=mean_interval_time, size=packet_num)
        interval_times_actual = []

        new_sample_time = start
        for abs_time in interval_times_abs:
            new_sample_time = new_sample_time + abs_time
            if new_sample_time > stop:
                break
            else:
                interval_times_actual.append(new_sample_time)
        return interval_times_actual

    def get_interval_times_lognormal(self, start, stop, packet_num, sigma):
        mean_interval_time = (stop - start) / packet_num
        interval_times_abs = numpy.random.lognormal(mean=math.log(mean_interval_time, 3), sigma=sigma, size=packet_num)
        interval_times_actual = []
        new_sample_time = start
        for abs_time in interval_times_abs:
            new_sample_time = new_sample_time + abs_time
            if new_sample_time > stop:
                break
            else:
                interval_times_actual.append(new_sample_time)
        return interval_times_actual

    def get_interval_times_weibull(self, start, stop, packet_num, alpha):
        mean_interval_time = (stop - start) / packet_num
        interval_times_abs = weibull_min.rvs(alpha, loc=0, scale=mean_interval_time, size=packet_num)
        interval_times_actual = []
        new_sample_time = start
        for abs_time in interval_times_abs:
            new_sample_time = new_sample_time + abs_time
            if new_sample_time > stop:
                break
            else:
                interval_times_actual.append(new_sample_time)
        return interval_times_actual

    def get_on_off_times(self, start, stop, packet_num, c_pareto, sigma):
        mean_interval_time = (stop - start) / packet_num
        on_times_abs = genpareto.rvs(c_pareto, scale=mean_interval_time, size=packet_num)
        off_times_abs = numpy.random.lognormal(mean=math.log(mean_interval_time, 2), sigma=sigma, size=packet_num)
        on_periods = []
        counter = 1
        current_time = start

        while current_time <= stop:
            # off phase
            current_time = current_time + off_times_abs[counter]
            new_on_start = current_time
            # on phase
            current_time = current_time + on_times_abs[counter]
            new_off_start = current_time
            if current_time <= stop:
                on_periods.append([new_on_start, new_off_start])
            counter = counter + 1
        return on_periods
