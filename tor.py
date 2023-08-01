import os
import itertools
import math
import random
from torus_integrated import myglobal
from torus_integrated.channel import *
from torus_integrated.traffic import Control_Packet
from torus_integrated.transmission_info.torus_matrix import *
from torus_integrated.buffer import *
from torus_integrated.node import *
import datetime
import pandas as pd

class Tors:
    def __init__(self):
        self.total_tors=None
        self.total_inter_channels=None
        self.inter_bitrate=None
        self.intra_bitrate=None
        self.intra_dedicated_bitrate=None
        self.tx_per_tor=None

        self.db=[]
        self.channels=Channels()
        self.current_cycle = 0

    def create_inter_channels(self,total_inter_channels,inter_bitrate,tx_per_tor):
        self.total_inter_channels=total_inter_channels
        self.inter_bitrate=inter_bitrate
        self.tx_per_tor=tx_per_tor
        inter_channel_id_list=[1000*x for x in range(1,self.total_inter_channels+1)]
        for ch_id in inter_channel_id_list:
            new_channel = Channel(ch_id, self.inter_bitrate)
            self.channels.add_new(new_channel)
        for tor in self.db:
            tor.inter_bitrate=self.inter_bitrate
        print('Created '+str(len(self.channels.db))+' inter channels @'+str(self.channels.get_common_bitrate())+' bps')

    def create_tors(self,total_tors):
        self.total_tors=total_tors
        for tor_id in range(1, self.total_tors + 1):
            new_tor = Tor(id=tor_id,total_tors=self.total_tors)
            self.add_new(new_tor)

    def create_tor_outbound_buffers(self,buffer_size_low,buffer_size_med,buffer_size_high):
        for tor in self.db:
            tor.create_tor_outbound_buffers(buffer_size_low,buffer_size_med,buffer_size_high)

    def create_tor_inbound_buffers(self,buffer_size_low,buffer_size_med,buffer_size_high):
        for tor in self.db:
            tor.create_tor_inbound_buffers(buffer_size_low,buffer_size_med,buffer_size_high)

    def create_nodes(self):
        for tor in self.db:
            tor.create_nodes()

    def init_nodes(self,total_nodes_per_tor,tor_node_id):
        for tor in self.db:
            tor.init_nodes(total_nodes_per_tor=total_nodes_per_tor,tor_node_id=tor_node_id)

    def create_intra_data_channels(self,total_intra_data_channels,intra_bitrate):
        self.intra_bitrate=intra_bitrate
        for tor in self.db:
            tor.create_intra_data_channels(total_intra_data_channels,intra_bitrate)

    def create_intra_control_channel(self,intra_control_channel_id,shared):
        for tor in self.db:
            tor.create_intra_control_channel(intra_control_channel_id,shared)

    def create_intra_dedicated_data_channels_dl(self,total_intra_data_channels_dl,intra_dedicated_bitrate):
        self.intra_dedicated_bitrate=intra_dedicated_bitrate
        for tor in self.db:
            tor.create_intra_dedicated_data_channels_dl(total_intra_data_channels_dl,intra_dedicated_bitrate)

    def create_intra_dedicated_data_channels_ul(self,total_intra_data_channels_ul,intra_dedicated_bitrate):
        for tor in self.db:
            tor.create_intra_dedicated_data_channels_ul(total_intra_data_channels_ul,intra_dedicated_bitrate)

    def create_intra_dedicated_control_channel(self,intra_dedicated_control_channel_id,shared):
        for tor in self.db:
            tor.create_intra_dedicated_control_channel(intra_dedicated_control_channel_id,shared)

    def create_intra_traffic_datasets(self,remove_inter):
        for tor in self.db:
            tor.create_intra_traffic_datasets(remove_inter=remove_inter)

    def create_node_output_buffers_for_intra_packs(self,low_size,med_size,high_size):
        for tor in self.db:
            tor.create_node_output_buffers_for_intra_packs(low_size,med_size,high_size)

    def create_node_output_buffers_for_inter_packs(self,low_size,med_size,high_size):
        for tor in self.db:
            tor.create_node_output_buffers_for_inter_packs(low_size,med_size,high_size)

    def get_per_cycle_time(self):
        return (myglobal.MAX_PACKET_SIZE*8)/self.channels.get_common_bitrate()

    def is_new_cycle(self,current_time):
        cycle_time = self.get_per_cycle_time()

        time_guard_band=myglobal.INTER_CYCLE_GUARD_BAND*8/self.inter_bitrate
        entered_new_cycle = (current_time >= cycle_time * self.current_cycle+time_guard_band)
        if entered_new_cycle:
            self.current_cycle = self.current_cycle + 1
        return entered_new_cycle

    def inter_transmit(self,current_time):
        if self.is_new_cycle(current_time):
            print('Entered new inter cycle=' + str(self.current_cycle) + ' at=' + str(current_time))

            # Get list of all per tor requests, shuffled and sorted
            all_tors_reqs=[]
            for tor in self.db:
                reqs=tor.check_per_tor_requests()
                all_tors_reqs.extend(reqs)
            random.shuffle(all_tors_reqs)
            all_tors_reqs.sort(key=lambda x: x.size, reverse=True)

            # Filtering algorithm: Add reqs to tx_train, subject to 3 restriction rules
            # 1) Each TOR can tx up to self.tx_per_tor
            # 2) Each direction at each TOR can tx only one request
            # 3) Each direction at each TOR can rx only one request
            chosen_reqs = []
            max_allowed_reqs=self.tx_per_tor*self.total_tors
            i=0
            while ((len(chosen_reqs)<max_allowed_reqs) and (i<len(all_tors_reqs))):
                curr_req=all_tors_reqs[i]
                current_txs = 0
                is_conflict_tx=False
                is_conflict_rx = False

                for chosen_req in chosen_reqs:
                    if chosen_req.tx == curr_req.tx:
                        current_txs=current_txs+1
                        if chosen_req.out_dir==curr_req.out_dir:
                            is_conflict_tx=True
                    if curr_req.rx == chosen_req.rx and curr_req.in_dir == chosen_req.in_dir:
                        is_conflict_rx=True
                # if ok, add to chosen requests
                if ((not is_conflict_tx) and (not is_conflict_rx) and (current_txs<self.tx_per_tor)):
                    chosen_reqs.append(curr_req)
                i=i+1

            # debug
            print('INTER will transmit a total of recs='+str(len(chosen_reqs)))
            for el in chosen_reqs:
                el.show()

            for tor in self.db:
                tor.inter_transmit(current_time,chosen_reqs)

    def inter_check_arrival_and_add_to_inbound_buffers(self,current_time,split):
        list_of_arrived_packs=[]
        for tor in self.db:
            list_of_arrived_packs.extend(tor.inter_check_arrival_and_add_to_inbound_buffers(current_time))
        for pack in list_of_arrived_packs:
            self.add_inter_packet_to_local_tor(pack.destination_tor,pack,current_time,split)

    def add_inter_packet_to_local_tor(self,dest_tor,pack,current_time,split):
        for tor in self.db:
            if tor.id==dest_tor:
                tor.add_inter_packet_to_local_tor(pack,current_time,split)

    def have_buffers_packets(self):
        for tor in self.db:
            if tor.have_buffers_packets():
                return True

    def check_generated_packets(self,current_time,split):
        for tor in self.db:
            tor.check_generated_packets(current_time,split)

    def check_arrival_intra_and_add_to_outbound_buffers(self,current_time):
        for tor in self.db:
            tor.check_arrival_intra_and_add_to_outbound_buffers(current_time)

    def check_arrival_dedicated_ul_and_add_to_outbound_buffers(self,current_time):
        for tor in self.db:
            tor.check_arrival_dedicated_ul_and_add_to_outbound_buffers(current_time)

    def check_arrival_dedicated_dl(self,current_time):
        for tor in self.db:
            tor.check_arrival_dedicated_dl(current_time)

    def process_new_cycle(self,current_time):
        new_cycle=False
        for tor in self.db:
            new_cycle=tor.process_new_cycle(current_time)
        return new_cycle

    def process_new_cycle_dedicated_ul(self,current_time):
        new_cycle=False
        for tor in self.db:
            new_cycle=tor.process_new_cycle_dedicated_ul(current_time)
        return new_cycle

    def process_new_cycle_dedicated_dl(self,current_time):
        new_cycle=False
        for tor in self.db:
            new_cycle=tor.process_new_cycle_dedicated_dl(current_time)
        return new_cycle

    def transmit_intra(self, current_time):
        for tor in self.db:
            tor.transmit_intra(current_time)

    def transmit_dedicated_ul(self, current_time):
        for tor in self.db:
            tor.transmit_dedicated_ul(current_time)

    def transmit_dedicated_dl(self, current_time):
        for tor in self.db:
            tor.transmit_dedicated_dl(current_time)

    def write_log(self):
        # estimate actual time
        real_time = str(datetime.datetime.now())
        real_time = real_time.replace('-', '_')
        real_time = real_time.replace(' ', '_')
        real_time = real_time.replace(':', '_')
        real_time = real_time.replace('.', '_')
        tor_names=[]
        # log for each tor
        for tor in self.db:
            tor_names.append(tor.write_log(real_time))

        print('Merging all ToR logs to single everything file...')
        combined_csv = pd.concat([pd.read_csv(f) for f in tor_names])
        mystr='log' + str(real_time) + '_everything.csv'
        combined_name = os.path.join(myglobal.LOGS_FOLDER, mystr)
        combined_csv.to_csv(combined_name, index=False)

        #print('Sorting ALL:')
        #with open(combined_name, 'r', newline='') as f_input:
        #    csv_input = csv.DictReader(f_input)
        #    data = sorted(csv_input, key=lambda row: (float(row['time']), float(row['packet_id'])))

        #print('Rewriting ALL:')
        #with open(combined_name, 'w', newline='') as f_output:
        #    csv_output = csv.DictWriter(f_output, fieldnames=csv_input.fieldnames)
        #    csv_output.writeheader()
        #    csv_output.writerows(data)

    def add_new(self,node):
        self.db.append(node)

    def get_node_from_id(self,id):
        for node in self.db:
            if node.id==id:
                return node

class Tor:
    def __init__(self,id,total_tors):
        self.id=id
        self.total_tors=total_tors
        self.inter_bitrate=None

        self.outbound_buffers_low_list=[]
        self.outbound_buffers_med_list=[]
        self.outbound_buffers_high_list=[]
        self.data_dropped=[]
        self.meta_buffer_S=[]
        self.meta_buffer_E=[]
        self.meta_buffer_N=[]
        self.meta_buffer_W=[]
        self.torus_matrix = Torus_Matrix()
        self.nodes = None

    def create_tor_outbound_buffers(self,buffer_size_low,buffer_size_med,buffer_size_high):
        for tor_dest_buff in range(1, self.total_tors + 1):
            if tor_dest_buff != self.id:
                self.outbound_buffers_low_list.append(
                    Tor_Outbound_Buffer(buffer_size_low, tor_dest_buff))
                self.outbound_buffers_med_list.append(
                    Tor_Outbound_Buffer(buffer_size_med, tor_dest_buff))
                self.outbound_buffers_high_list.append(
                    Tor_Outbound_Buffer(buffer_size_high, tor_dest_buff))

    def create_tor_inbound_buffers(self,buffer_size_low,buffer_size_med,buffer_size_high):
        self.nodes.create_tor_inbound_buffers(buffer_size_low,buffer_size_med,buffer_size_high)

    def create_nodes(self):
        nodes=Nodes(tor_id=self.id)
        self.nodes=nodes

    def init_nodes(self,total_nodes_per_tor,tor_node_id):
        self.nodes.init_nodes(total_nodes_per_tor=total_nodes_per_tor,tor_node_id=tor_node_id)
        print('Created TOR id' + str(self.id) + ',with new nodes=' + str(len(self.nodes.db)))

    def create_intra_data_channels(self, total_intra_data_channels, intra_bitrate):
        self.nodes.create_intra_data_channels(total_intra_data_channels, intra_bitrate)

    def create_intra_control_channel(self, intra_control_channel_id,shared):
        self.nodes.create_intra_control_channel(intra_control_channel_id,shared)

    def create_intra_dedicated_data_channels_dl(self, total_intra_data_channels_dl, intra_dedicated_bitrate):
        self.nodes.create_intra_dedicated_data_channels_dl(total_intra_data_channels_dl, intra_dedicated_bitrate)

    def create_intra_dedicated_data_channels_ul(self, total_intra_data_channels_ul, intra_dedicated_bitrate):
        self.nodes.create_intra_dedicated_data_channels_ul(total_intra_data_channels_ul, intra_dedicated_bitrate)

    def create_intra_dedicated_control_channel(self, intra_dedicated_control_channel_id,shared):
        self.nodes.create_intra_dedicated_control_channel(intra_dedicated_control_channel_id,shared)

    def create_intra_traffic_datasets(self,remove_inter):
        self.nodes.create_intra_traffic_datasets(remove_inter=remove_inter)

    def create_node_output_buffers_for_intra_packs(self,low_size,med_size,high_size):
        self.nodes.create_node_output_buffers_for_intra_packs(low_size,med_size,high_size)

    def create_node_output_buffers_for_inter_packs(self, low_size, med_size, high_size):
        self.nodes.create_node_output_buffers_for_inter_packs(low_size, med_size, high_size)

    def add_inter_packet_to_local_tor(self,pack,current_time,split):
        if split:
            self.nodes.add_inter_packet_to_local_tor_split(pack,current_time)
        else:
            self.nodes.add_inter_packet_to_local_tor(pack, current_time)

    def check_per_tor_requests(self):
        # 1) Each TOR makes a total request to transmit (sub-requests) to all trx_directions.
        # 2) Each sub-request (1500-message) must be targeted to one destination (rx). Cannot couple multiple.
        # 3) Each sub-request has a maximum size of trx window (1500)
        rx_torus_rec_list=[]
        for rx_id in range(1, self.total_tors + 1):
            if rx_id!=self.id:
                can_fill_with_bigs = False
                for out_buffer in self.outbound_buffers_med_list:
                    # find buffer according to rx id
                    if out_buffer.destination_tor == rx_id:
                        if out_buffer.has_packets() and out_buffer.db[0].packet_size == myglobal.MAX_PACKET_SIZE:
                            can_fill_with_bigs = True
                if not can_fill_with_bigs:
                    for out_buffer in self.outbound_buffers_low_list:
                        # find buffer according to rx id
                        if out_buffer.destination_tor == rx_id:
                            if out_buffer.has_packets() and out_buffer.db[0].packet_size == myglobal.MAX_PACKET_SIZE:
                                can_fill_with_bigs = True
                if not can_fill_with_bigs:
                    fill_with_smalls_size = 0
                    for out_buffer in self.outbound_buffers_high_list:
                        # find buffer according to rx id
                        if out_buffer.destination_tor == rx_id:
                            i = 0
                            while i < len(out_buffer.db) and out_buffer.db[i].packet_size < myglobal.MAX_PACKET_SIZE \
                                    and fill_with_smalls_size < (myglobal.MAX_PACKET_SIZE / myglobal.MIN_PACKET_SIZE):
                                i = i + 1
                                fill_with_smalls_size = fill_with_smalls_size + 1
                    for out_buffer in self.outbound_buffers_med_list:
                        # find buffer according to rx id
                        if out_buffer.destination_tor == rx_id:
                            i = 0
                            while i < len(out_buffer.db) and out_buffer.db[i].packet_size < myglobal.MAX_PACKET_SIZE \
                                    and fill_with_smalls_size < (myglobal.MAX_PACKET_SIZE / myglobal.MIN_PACKET_SIZE):
                                i = i + 1
                                fill_with_smalls_size = fill_with_smalls_size + 1
                    for out_buffer in self.outbound_buffers_low_list:
                        # find buffer according to rx id
                        if out_buffer.destination_tor == rx_id:
                            i = 0
                            while i < len(out_buffer.db) and out_buffer.db[i].packet_size < myglobal.MAX_PACKET_SIZE \
                                    and fill_with_smalls_size < (myglobal.MAX_PACKET_SIZE / myglobal.MIN_PACKET_SIZE):
                                i = i + 1
                                fill_with_smalls_size = fill_with_smalls_size + 1

                out_dir,in_dir,lamda=self.torus_matrix.get_trx_info_from_tx_rx_id(self.id,rx_id)
                new_torus_rec=Torus_Record(rx_id,self.id,out_dir,in_dir,lamda)
                if can_fill_with_bigs:
                    new_torus_rec.size=myglobal.MAX_PACKET_SIZE
                else:
                    new_torus_rec.size=fill_with_smalls_size*myglobal.MIN_PACKET_SIZE
                rx_torus_rec_list.append(new_torus_rec)

        # Split list into actual requests/backup requests according to max TRX for all directions
        #rx_torus_rec_list.sort(key=lambda x: x.size, reverse=True)
        #actual_list=rx_torus_rec_list[:myglobal.INTER_TX_PER_TOR]
        #backup_list=rx_torus_rec_list[myglobal.INTER_TX_PER_TOR:]

        return rx_torus_rec_list

    def get_meta_buffer_S_size(self):
        size=0
        for pack in self.meta_buffer_S:
            size=size+pack.packet_size
        return size
    def get_meta_buffer_E_size(self):
        size=0
        for pack in self.meta_buffer_E:
            size=size+pack.packet_size
        return size
    def get_meta_buffer_N_size(self):
        size=0
        for pack in self.meta_buffer_N:
            size=size+pack.packet_size
        return size
    def get_meta_buffer_W_size(self):
        size=0
        for pack in self.meta_buffer_W:
            size=size+pack.packet_size
        return size

    def fill_S_meta_buffer(self,current_time,rx_id):
        can_fill_with_bigs = False
        for out_buffer in self.outbound_buffers_med_list:
            if out_buffer.destination_tor == rx_id:
                if out_buffer.has_packets() and out_buffer.db[0].packet_size == myglobal.MAX_PACKET_SIZE:
                    mypack=out_buffer.db[0]
                    mypack.time_tor_buffer_out=current_time
                    mypack.time_tor_trx_in = current_time
                    trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                    mypack.time_tor_trx_out = mypack.time_tor_trx_in+ trx_time_theor+ myglobal.PROPAGATION_TIME * 1
                    self.meta_buffer_S.append(mypack)
                    out_buffer.db.pop(0)
                    can_fill_with_bigs = True
        if not can_fill_with_bigs:
            for out_buffer in self.outbound_buffers_low_list:
                if out_buffer.destination_tor == rx_id:
                    if out_buffer.has_packets() and out_buffer.db[0].packet_size == myglobal.MAX_PACKET_SIZE:
                        mypack = out_buffer.db[0]
                        mypack.time_tor_buffer_out = current_time
                        mypack.time_tor_trx_in = current_time
                        trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                        mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                        self.meta_buffer_S.append(mypack)
                        out_buffer.db.pop(0)
                        can_fill_with_bigs = True
        if not can_fill_with_bigs:
            fill_with_smalls_size = 0
            for out_buffer in self.outbound_buffers_high_list:
                if out_buffer.destination_tor == rx_id:
                    i = 0
                    to_delete_list = []  #
                    while i < len(out_buffer.db) and out_buffer.db[i].packet_size < myglobal.MAX_PACKET_SIZE \
                            and fill_with_smalls_size < (
                            myglobal.MAX_PACKET_SIZE / myglobal.MIN_PACKET_SIZE):
                        mypack = out_buffer.db[i]
                        copy_pack=mypack
                        to_delete_list.append(copy_pack)  #
                        mypack.time_tor_buffer_out = current_time
                        mypack.time_tor_trx_in = current_time
                        trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                        mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                        self.meta_buffer_S.append(mypack)
                        i = i + 1
                        fill_with_smalls_size = fill_with_smalls_size + 1
                    for item in to_delete_list:  #
                        out_buffer.db.remove(item) #
            for out_buffer in self.outbound_buffers_med_list:
                i = 0
                to_delete_list = []  #
                while i < len(out_buffer.db) and out_buffer.db[i].packet_size < myglobal.MAX_PACKET_SIZE \
                        and fill_with_smalls_size < (
                        myglobal.MAX_PACKET_SIZE / myglobal.MIN_PACKET_SIZE):
                    mypack = out_buffer.db[i]
                    copy_pack = mypack
                    to_delete_list.append(copy_pack)  #
                    mypack.time_tor_buffer_out = current_time
                    mypack.time_tor_trx_in = current_time
                    trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                    mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                    self.meta_buffer_S.append(mypack)
                    #out_buffer.db.pop(i)
                    i = i + 1
                    fill_with_smalls_size = fill_with_smalls_size + 1
                for item in to_delete_list:  #
                    out_buffer.db.remove(item)  #
            for out_buffer in self.outbound_buffers_low_list:
                i = 0
                to_delete_list = []  #
                while i < len(out_buffer.db) and out_buffer.db[i].packet_size < myglobal.MAX_PACKET_SIZE \
                        and fill_with_smalls_size < (
                        myglobal.MAX_PACKET_SIZE / myglobal.MIN_PACKET_SIZE):
                    mypack = out_buffer.db[i]
                    copy_pack = mypack
                    to_delete_list.append(copy_pack)  #
                    mypack.time_tor_buffer_out = current_time
                    mypack.time_tor_trx_in = current_time
                    trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                    mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                    self.meta_buffer_S.append(mypack)
                    #out_buffer.db.pop(i)
                    i = i + 1
                    fill_with_smalls_size = fill_with_smalls_size + 1
                for item in to_delete_list:  #
                    out_buffer.db.remove(item)  #
        if can_fill_with_bigs:
            print('Tor'+str(self.id)+'(S)'+':Will InterTRXing bigs')
        else:
            print('Tor'+str(self.id)+'(S)'+':Will InterTRXing smalls='+str(fill_with_smalls_size))
    def fill_N_meta_buffer(self,current_time,rx_id):
        can_fill_with_bigs = False
        for out_buffer in self.outbound_buffers_med_list:
            if out_buffer.destination_tor == rx_id:
                if out_buffer.has_packets() and out_buffer.db[0].packet_size == myglobal.MAX_PACKET_SIZE:
                    mypack=out_buffer.db[0]
                    mypack.time_tor_buffer_out=current_time
                    mypack.time_tor_trx_in = current_time
                    trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                    mypack.time_tor_trx_out = current_time+ trx_time_theor+ myglobal.PROPAGATION_TIME * 1
                    self.meta_buffer_N.append(mypack)
                    out_buffer.db.pop(0)
                    can_fill_with_bigs = True
        if not can_fill_with_bigs:
            for out_buffer in self.outbound_buffers_low_list:
                if out_buffer.destination_tor == rx_id:
                    if out_buffer.has_packets() and out_buffer.db[0].packet_size == myglobal.MAX_PACKET_SIZE:
                        mypack = out_buffer.db[0]
                        mypack.time_tor_buffer_out = current_time
                        mypack.time_tor_trx_in = current_time
                        trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                        mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                        self.meta_buffer_N.append(mypack)
                        out_buffer.db.pop(0)
                        can_fill_with_bigs = True
        if not can_fill_with_bigs:
            fill_with_smalls_size = 0
            for out_buffer in self.outbound_buffers_high_list:
                if out_buffer.destination_tor == rx_id:
                    i = 0
                    to_delete_list=[] #
                    while i < len(out_buffer.db) and out_buffer.db[i].packet_size < myglobal.MAX_PACKET_SIZE \
                            and fill_with_smalls_size < (
                            myglobal.MAX_PACKET_SIZE / myglobal.MIN_PACKET_SIZE):
                        mypack = out_buffer.db[i]
                        copy_pack=mypack
                        to_delete_list.append(copy_pack)  #
                        mypack.time_tor_buffer_out = current_time
                        mypack.time_tor_trx_in = current_time
                        trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                        mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                        self.meta_buffer_N.append(mypack)
                        #out_buffer.db.pop(i)
                        i = i + 1
                        fill_with_smalls_size = fill_with_smalls_size + 1
                    for item in to_delete_list:  #
                        out_buffer.db.remove(item) #
            for out_buffer in self.outbound_buffers_med_list:
                i = 0
                to_delete_list = []  #
                while i < len(out_buffer.db) and out_buffer.db[i].packet_size < myglobal.MAX_PACKET_SIZE \
                        and fill_with_smalls_size < (
                        myglobal.MAX_PACKET_SIZE / myglobal.MIN_PACKET_SIZE):
                    mypack = out_buffer.db[i]
                    copy_pack = mypack
                    to_delete_list.append(copy_pack)  #
                    mypack.time_tor_buffer_out = current_time
                    mypack.time_tor_trx_in = current_time
                    trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                    mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                    self.meta_buffer_N.append(mypack)
                    #out_buffer.db.pop(i)
                    i = i + 1
                    fill_with_smalls_size = fill_with_smalls_size + 1
                for item in to_delete_list:  #
                    out_buffer.db.remove(item)  #
            for out_buffer in self.outbound_buffers_low_list:
                i = 0
                to_delete_list = []  #
                while i < len(out_buffer.db) and out_buffer.db[i].packet_size < myglobal.MAX_PACKET_SIZE \
                        and fill_with_smalls_size < (
                        myglobal.MAX_PACKET_SIZE / myglobal.MIN_PACKET_SIZE):
                    mypack = out_buffer.db[i]
                    copy_pack = mypack
                    to_delete_list.append(copy_pack)  #
                    mypack.time_tor_buffer_out = current_time
                    mypack.time_tor_trx_in = current_time
                    trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                    mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                    self.meta_buffer_N.append(mypack)
                    #out_buffer.db.pop(i)
                    i = i + 1
                    fill_with_smalls_size = fill_with_smalls_size + 1
                for item in to_delete_list:  #
                    out_buffer.db.remove(item)  #
        if can_fill_with_bigs:
            print('Tor'+str(self.id)+'(N)'+':Will InterTRXing bigs')
        else:
            print('Tor'+str(self.id)+'(N)'+':Will InterTRXing smalls='+str(fill_with_smalls_size))
    def fill_W_meta_buffer(self,current_time,rx_id):
        can_fill_with_bigs = False
        for out_buffer in self.outbound_buffers_med_list:
            if out_buffer.destination_tor == rx_id:
                if out_buffer.has_packets() and out_buffer.db[0].packet_size == myglobal.MAX_PACKET_SIZE:
                    mypack=out_buffer.db[0]
                    mypack.time_tor_buffer_out=current_time
                    mypack.time_tor_trx_in = current_time
                    trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                    mypack.time_tor_trx_out = current_time+ trx_time_theor+ myglobal.PROPAGATION_TIME * 1
                    self.meta_buffer_W.append(mypack)
                    out_buffer.db.pop(0)
                    can_fill_with_bigs = True
        if not can_fill_with_bigs:
            for out_buffer in self.outbound_buffers_low_list:
                if out_buffer.destination_tor == rx_id:
                    if out_buffer.has_packets() and out_buffer.db[0].packet_size == myglobal.MAX_PACKET_SIZE:
                        mypack = out_buffer.db[0]
                        mypack.time_tor_buffer_out = current_time
                        mypack.time_tor_trx_in = current_time
                        trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                        mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                        self.meta_buffer_W.append(mypack)
                        out_buffer.db.pop(0)
                        can_fill_with_bigs = True
        if not can_fill_with_bigs:
            fill_with_smalls_size = 0
            for out_buffer in self.outbound_buffers_high_list:
                if out_buffer.destination_tor == rx_id:
                    i = 0
                    to_delete_list=[] #
                    while i < len(out_buffer.db) and out_buffer.db[i].packet_size < myglobal.MAX_PACKET_SIZE \
                            and fill_with_smalls_size < (
                            myglobal.MAX_PACKET_SIZE / myglobal.MIN_PACKET_SIZE):
                        mypack = out_buffer.db[i]
                        to_delete_list.append(mypack) #
                        mypack.time_tor_buffer_out = current_time
                        mypack.time_tor_trx_in = current_time
                        trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                        mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                        self.meta_buffer_W.append(mypack)
                        #out_buffer.db.pop(i)
                        i = i + 1
                        fill_with_smalls_size = fill_with_smalls_size + 1
                    for item in to_delete_list:  #
                        out_buffer.db.remove(item) #
            for out_buffer in self.outbound_buffers_med_list:
                i = 0
                to_delete_list = []  #
                while i < len(out_buffer.db) and out_buffer.db[i].packet_size < myglobal.MAX_PACKET_SIZE \
                        and fill_with_smalls_size < (
                        myglobal.MAX_PACKET_SIZE / myglobal.MIN_PACKET_SIZE):
                    mypack = out_buffer.db[i]
                    copy_pack = mypack
                    to_delete_list.append(copy_pack)  #
                    mypack.time_tor_buffer_out = current_time
                    mypack.time_tor_trx_in = current_time
                    trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                    mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                    self.meta_buffer_W.append(mypack)
                    #out_buffer.db.pop(i)
                    i = i + 1
                    fill_with_smalls_size = fill_with_smalls_size + 1
                for item in to_delete_list:  #
                    out_buffer.db.remove(item)  #
            for out_buffer in self.outbound_buffers_low_list:
                i = 0
                to_delete_list = []  #
                while i < len(out_buffer.db) and out_buffer.db[i].packet_size < myglobal.MAX_PACKET_SIZE \
                        and fill_with_smalls_size < (
                        myglobal.MAX_PACKET_SIZE / myglobal.MIN_PACKET_SIZE):
                    mypack = out_buffer.db[i]
                    copy_pack = mypack
                    to_delete_list.append(copy_pack)  #
                    mypack.time_tor_buffer_out = current_time
                    mypack.time_tor_trx_in = current_time
                    trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                    mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                    self.meta_buffer_W.append(mypack)
                    #out_buffer.db.pop(i)
                    i = i + 1
                    fill_with_smalls_size = fill_with_smalls_size + 1
                for item in to_delete_list:  #
                    out_buffer.db.remove(item)  #
        if can_fill_with_bigs:
            print('Tor'+str(self.id)+'(W)'+':Will InterTRXing bigs')
        else:
            print('Tor'+str(self.id)+'(W)'+':Will InterTRXing smalls='+str(fill_with_smalls_size))
    def fill_E_meta_buffer(self,current_time,rx_id):
        can_fill_with_bigs = False
        for out_buffer in self.outbound_buffers_med_list:
            if out_buffer.destination_tor == rx_id:
                if out_buffer.has_packets() and out_buffer.db[0].packet_size == myglobal.MAX_PACKET_SIZE:
                    mypack=out_buffer.db[0]
                    mypack.time_tor_buffer_out=current_time
                    mypack.time_tor_trx_in = current_time
                    trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                    mypack.time_tor_trx_out = current_time+ trx_time_theor+ myglobal.PROPAGATION_TIME * 1
                    self.meta_buffer_E.append(mypack)
                    out_buffer.db.pop(0)
                    can_fill_with_bigs = True
        if not can_fill_with_bigs:
            for out_buffer in self.outbound_buffers_low_list:
                if out_buffer.destination_tor == rx_id:
                    if out_buffer.has_packets() and out_buffer.db[0].packet_size == myglobal.MAX_PACKET_SIZE:
                        mypack = out_buffer.db[0]
                        mypack.time_tor_buffer_out = current_time
                        mypack.time_tor_trx_in = current_time
                        trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                        mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                        self.meta_buffer_E.append(mypack)
                        out_buffer.db.pop(0)
                        can_fill_with_bigs = True
        if not can_fill_with_bigs:
            fill_with_smalls_size = 0
            for out_buffer in self.outbound_buffers_high_list:
                if out_buffer.destination_tor == rx_id:
                    i = 0
                    to_delete_list=[] #
                    while i < len(out_buffer.db) and out_buffer.db[i].packet_size < myglobal.MAX_PACKET_SIZE \
                            and fill_with_smalls_size < (
                            myglobal.MAX_PACKET_SIZE / myglobal.MIN_PACKET_SIZE):
                        mypack = out_buffer.db[i]
                        to_delete_list.append(mypack) #
                        mypack.time_tor_buffer_out = current_time
                        mypack.time_tor_trx_in = current_time
                        trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                        mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                        self.meta_buffer_E.append(mypack)
                        #out_buffer.db.pop(i)
                        i = i + 1
                        fill_with_smalls_size = fill_with_smalls_size + 1
                    for item in to_delete_list:  #
                        out_buffer.db.remove(item) #
            for out_buffer in self.outbound_buffers_med_list:
                i = 0
                to_delete_list = []  #
                while i < len(out_buffer.db) and out_buffer.db[i].packet_size < myglobal.MAX_PACKET_SIZE \
                        and fill_with_smalls_size < (
                        myglobal.MAX_PACKET_SIZE / myglobal.MIN_PACKET_SIZE):
                    mypack = out_buffer.db[i]
                    copy_pack = mypack
                    to_delete_list.append(copy_pack)  #
                    mypack.time_tor_buffer_out = current_time
                    mypack.time_tor_trx_in = current_time
                    trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                    mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                    self.meta_buffer_E.append(mypack)
                    #out_buffer.db.pop(i)
                    i = i + 1
                    fill_with_smalls_size = fill_with_smalls_size + 1
                for item in to_delete_list:  #
                    out_buffer.db.remove(item)  #
            for out_buffer in self.outbound_buffers_low_list:
                i = 0
                to_delete_list = []  #
                while i < len(out_buffer.db) and out_buffer.db[i].packet_size < myglobal.MAX_PACKET_SIZE \
                        and fill_with_smalls_size < (
                        myglobal.MAX_PACKET_SIZE / myglobal.MIN_PACKET_SIZE):
                    mypack = out_buffer.db[i]
                    copy_pack = mypack
                    to_delete_list.append(copy_pack)  #
                    mypack.time_tor_buffer_out = current_time
                    mypack.time_tor_trx_in = current_time
                    trx_time_theor=(8*mypack.packet_size)/self.inter_bitrate
                    mypack.time_tor_trx_out = current_time + trx_time_theor + myglobal.PROPAGATION_TIME * 1
                    self.meta_buffer_E.append(mypack)
                    # out_buffer.db.pop(i)
                    i = i + 1
                    fill_with_smalls_size = fill_with_smalls_size + 1
                for item in to_delete_list:  #
                    out_buffer.db.remove(item)  #
        if can_fill_with_bigs:
            print('Tor'+str(self.id)+'(E)'+':Will InterTRXing bigs')
        else:
            print('Tor'+str(self.id)+'(E)'+':Will InterTRXing smalls='+str(fill_with_smalls_size))

    def inter_transmit(self,current_time,filtered_recs):
        for rec in filtered_recs:
            if rec.tx==self.id:
                if rec.out_dir=='S':
                    self.fill_S_meta_buffer(current_time,rec.rx)
                elif rec.out_dir=='N':
                    self.fill_N_meta_buffer(current_time,rec.rx)
                elif rec.out_dir=='W':
                    self.fill_W_meta_buffer(current_time,rec.rx)
                elif rec.out_dir=='E':
                    self.fill_E_meta_buffer(current_time,rec.rx)
                else:
                    print('Error, cannot ifnd SNWE metabuffer')

    def inter_check_arrival_and_add_to_inbound_buffers(self,current_time):
        list_of_sent_packs=[]
        for pack in self.meta_buffer_S:
            has_packet_arrived_inter=pack.time_tor_trx_in<pack.time_tor_trx_out and pack.time_tor_trx_out<=current_time
            if has_packet_arrived_inter:
                print('INTER connection arrived to TOR='+str(self.id)+',pack='+str(pack.show_mini()))
                list_of_sent_packs.append(pack)
                self.meta_buffer_S.remove(pack)
        for pack in self.meta_buffer_N:
            has_packet_arrived_inter=pack.time_tor_trx_in<pack.time_tor_trx_out and pack.time_tor_trx_out<=current_time
            if has_packet_arrived_inter:
                print('INTER connection arrived to TOR='+str(self.id)+',pack='+str(pack.show_mini()))
                list_of_sent_packs.append(pack)
                self.meta_buffer_N.remove(pack)
        for pack in self.meta_buffer_W:
            has_packet_arrived_inter=pack.time_tor_trx_in<pack.time_tor_trx_out and pack.time_tor_trx_out<=current_time
            if has_packet_arrived_inter:
                print('INTER connection arrived to TOR='+str(self.id)+',pack='+str(pack.show_mini()))
                list_of_sent_packs.append(pack)
                self.meta_buffer_W.remove(pack)
        for pack in self.meta_buffer_E:
            has_packet_arrived_inter=pack.time_tor_trx_in<pack.time_tor_trx_out and pack.time_tor_trx_out<=current_time
            if has_packet_arrived_inter:
                print('INTER connection arrived to TOR='+str(self.id)+',pack='+str(pack.show_mini()))
                list_of_sent_packs.append(pack)
                self.meta_buffer_E.remove(pack)
        return list_of_sent_packs

    def have_buffers_packets(self):
        # check inter buffers
        for buffer in self.outbound_buffers_high_list:
            if buffer.has_packets():
                return True
        for buffer in self.outbound_buffers_med_list:
            if buffer.has_packets():
                return True
        for buffer in self.outbound_buffers_low_list:
            if buffer.has_packets():
                return True
        # check intra buffers
        return self.nodes.have_buffers_packets()

    def check_generated_packets(self,current_time,split):
        self.nodes.check_generated_packets(current_time,split)

    def check_arrival_intra_and_add_to_outbound_buffers(self,current_time):
        outgoing_packets_list=self.nodes.check_arrival_intra_and_add_to_outbound_buffers(current_time)
        for pack in outgoing_packets_list:
            self.add_pack_to_outbound_buffers(pack,current_time)

    def check_arrival_dedicated_ul_and_add_to_outbound_buffers(self,current_time):
        outgoing_packets_list=self.nodes.check_arrival_dedicated_ul_and_add_to_outbound_buffers(current_time)
        for pack in outgoing_packets_list:
            self.add_pack_to_outbound_buffers(pack,current_time)

    def check_arrival_dedicated_dl(self,current_time):
        self.nodes.check_arrival_dedicated_dl(current_time)

    def process_new_cycle(self,current_time):
        new_cycle=self.nodes.process_new_cycle(current_time)
        return new_cycle

    def process_new_cycle_dedicated_ul(self,current_time):
        self.nodes.process_new_cycle_dedicated_ul(current_time)

    def process_new_cycle_dedicated_dl(self,current_time):
        self.nodes.process_new_cycle_dedicated_dl(current_time)

    def transmit_intra(self, current_time):
        self.nodes.transmit_intra(current_time)

    def transmit_dedicated_ul(self, current_time):
        self.nodes.transmit_dedicated_ul(current_time)

    def transmit_dedicated_dl(self, current_time):
        self.nodes.transmit_dedicated_dl(current_time)

    def write_log(self,real_time):

        # create logfile for this ToR
        mystr='log' + str(real_time) + '_tor' + str(self.id) + '_combo.csv'
        logfile = os.path.join(myglobal.LOGS_FOLDER, mystr)
        with open(logfile, mode='a') as file:
            file.write(myglobal.OUTPUT_TABLE_TITLE)

        # write info for all ToR nodes and ToR node (intra)
        self.nodes.write_log(real_time,logfile)

        # write ToR-level info (inter)
        print('Writing level info for tor='+str(self.id)+',drop/inter-outbound='+str(len(self.data_dropped)))
        with open(logfile, mode='a') as file:
            for packet in self.data_dropped:
                curr_str = packet.show() + '\n'
                file.write(curr_str)

        # sort ToR
        print('Re Sorting TOR='+str(self.id))
        with open(logfile, 'r', newline='') as f_input:
            csv_input = csv.DictReader(f_input)
            data = sorted(csv_input, key=lambda row: (float(row['time']), float(row['packet_id'])))

        print('Rewriting TOR='+str(self.id))
        with open(logfile, 'w', newline='') as f_output:
            csv_output = csv.DictWriter(f_output, fieldnames=csv_input.fieldnames)
            csv_output.writeheader()
            csv_output.writerows(data)
        return logfile

    def add_pack_to_outbound_buffers(self,pack,current_time):
        can_add_pack = False
        if pack.packet_qos == 'low':
            for buff in self.outbound_buffers_low_list:
                if pack.destination_tor==buff.destination_tor:
                    can_add_pack = buff.can_add_pack(pack)
                    if can_add_pack:
                        pack.time_tor_buffer_in = current_time
                        buff.add_pack(pack)
        elif pack.packet_qos == 'med':
            for buff in self.outbound_buffers_med_list:
                if pack.destination_tor==buff.destination_tor:
                    can_add_pack = buff.can_add_pack(pack)
                    if can_add_pack:
                        pack.time_tor_buffer_in = current_time
                        buff.add_pack(pack)
        elif pack.packet_qos == 'high':
            for buff in self.outbound_buffers_high_list:
                if pack.destination_tor==buff.destination_tor:
                    can_add_pack = buff.can_add_pack(pack)
                    if can_add_pack:
                        pack.time_tor_buffer_in = current_time
                        buff.add_pack(pack)
        if not can_add_pack:
            print('Dropping to interconnection buffers from TOR=' + str(self.id) + ',pack=' + str(pack.show_mini()))
            self.data_dropped.append(pack)
        else:
            print('Adding to interconnection buffers from TOR=' + str(self.id) + ',pack=' + str(pack.show_mini()))





