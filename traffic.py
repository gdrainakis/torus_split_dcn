import csv
import math
import os
from torus_integrated import myglobal

class Packet:
    def __init__(self,packet_id,time,packet_size,packet_qos,source_id,
                 tor_id,destination_id,destination_tor):
        self.packet_id=int(packet_id)
        self.time=float(time)
        self.packet_size=float(packet_size)
        self.packet_qos=packet_qos
        self.source_id=int(source_id)
        self.destination_id=int(destination_id)
        self.tor_id=int(tor_id)
        self.destination_tor=int(destination_tor)
        self.time_intra_buffer_in=-1
        self.time_intra_buffer_out=-1
        self.time_intra_trx_in=-1
        self.time_intra_trx_out=-1
        self.time_tor_buffer_in=-1
        self.time_tor_buffer_out=-1
        self.time_tor_trx_in=-1
        self.time_tor_trx_out=-1
        self.time_inter_buffer_in=-1
        self.time_inter_buffer_out=-1
        self.time_inter_trx_in=-1
        self.time_inter_trx_out=-1
        self.channel_id=0
        self.annotated=False

    def is_intra(self):
        return (self.tor_id==self.destination_tor)

    def is_intra_for_tor(self, parent_tor_id):
        return (self.is_intra() and self.tor_id == parent_tor_id)

    def is_outgoing_for_tor(self, parent_tor_id):
        return ((not self.is_intra()) and self.tor_id == parent_tor_id)

    def is_incoming_for_tor(self, parent_tor_id):
        return ((not self.is_intra()) and self.destination_tor == parent_tor_id)

    def show_mini(self):
        outp='id='+str(self.packet_id)+',source='+str(self.tor_id)+'-'+str(self.source_id)+',dest='+\
             str(self.destination_tor)+'-'+str(self.destination_id)
        return outp

    def show(self):
        outp=str(self.packet_id)+','+\
             str(self.time) + ','+\
            str(self.packet_size) + ',' +\
                str(self.packet_qos) + ',' +\
             str(self.source_id) + ',' + \
             str(self.tor_id) + ',' + \
             str(self.destination_id) + ','+ \
             str(self.destination_tor) + ',' + \
             str(self.time_intra_buffer_in) + ',' + \
             str(self.time_intra_buffer_out) + ',' + \
             str(self.time_intra_trx_in) + ',' + \
             str(self.time_intra_trx_out) + ',' + \
             str(self.time_tor_buffer_in) + ',' + \
             str(self.time_tor_buffer_out) + ',' + \
             str(self.time_tor_trx_in) + ',' + \
             str(self.time_tor_trx_out) + ',' + \
             str(self.time_inter_buffer_in) + ',' + \
             str(self.time_inter_buffer_out) + ',' + \
             str(self.time_inter_trx_in) + ',' + \
             str(self.time_inter_trx_out)
        return outp

class Control_Packet:
    def __init__(self,time,source_id):
        self.time=float(time)
        self.source_id=int(source_id)
        self.time_intra_trx_in=-1
        self.time_intra_trx_out=-1
        self.packet_size=0 #bytes
        self.channel_id=0
        self.is_bonus_packet=False
        self.bonus_info=None
        self.annotated=False
        self.minipack_list=[]

class Traffic_Per_Node():
    def __init__(self,file,remove_inter):
        self.remove_inter=remove_inter
        self.db=[]
        self.load(file)

    def load(self,file):
        with open(file) as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',')
            for row in csv_reader:
                new_packet = Packet(row['packet_id'], row['time'], row['packet_size'],row['packet_qos'],
                                    row['source_id'],row['tor_id'],row['destination_id'],row['destination_tor']
                                    )
                self.add(new_packet)

    def add(self,packet):
        self.db.append(packet)

    def get_next_arrival(self,current_time):
        for packet in self.db:
            if packet.time>=current_time:
                return packet.time

    def get_new_packets(self,current_time):
        packet_list=[]
        for packet in self.db:
            #if math.isclose(current_time,packet.time,abs_tol=myglobal.TOLERANCE): # legacy
            if packet.time<=current_time:
                # if not account for inter traffic and come up with inter packet, remove it
                if self.remove_inter and (not packet.is_intra()):
                    pass
                else:
                    packet_list.append(packet)
                self.db.remove(packet)
            else:
                break
        return packet_list

class Traffic_system():
    def __init__(self,dataset_folder,tors,servers,remove_inter):
        self.dataset_folder=dataset_folder
        self.remove_inter=remove_inter
        self.tors=tors
        self.servers=servers
        self.db=[]
        self.load()

    def load(self):
        for tor_id in range(1, self.tors + 1):
            for server_id in range(1, self.servers + 1):
                node_csv = 'tor' + str(tor_id) + 'node' + str(server_id) + '.csv'
                filename = os.path.join(self.dataset_folder, node_csv)
                with open(filename) as csv_file:
                    csv_reader = csv.DictReader(csv_file, delimiter=',')
                    for row in csv_reader:
                        new_pack = Packet(row['packet_id'], row['time'], row['packet_size'], row['packet_qos'],
                                          row['source_id'], row['tor_id'], row['destination_id'],
                                          row['destination_tor'])
                        self.db.append(new_pack)

    def add(self,packet):
        self.db.append(packet)

    def get_next_arrival(self,current_time):
        for packet in self.db:
            if packet.time>=current_time:
                return packet.time

    def get_new_packets(self,current_time):
        packet_list=[]
        for packet in self.db:
            #if math.isclose(current_time,packet.time,abs_tol=myglobal.TOLERANCE): # legacy
            if packet.time<=current_time:
                # if not account for inter traffic and come up with inter packet, remove it
                if self.remove_inter and (not packet.is_intra()):
                    pass
                else:
                    packet_list.append(packet)
                self.db.remove(packet)
            else:
                break
        return packet_list

    def get_stats(self):

        print('Statistics for dataset folder=' + str(self.dataset_folder))
        per_tor_load={}

        for tor_id in range(1, self.tors + 1):
            per_tor_load[tor_id]=0

        intra_high_bytes = 0
        intra_high_packets = 0
        intra_med_bytes = 0
        intra_med_packets = 0
        intra_low_bytes = 0
        intra_low_packets = 0
        inter_high_bytes = 0
        inter_high_packets = 0
        inter_med_bytes = 0
        inter_med_packets = 0
        inter_low_bytes = 0
        inter_low_packets = 0
        total_bytes = 0
        total_packets = 0
        intra_bytes = 0
        intra_packets = 0
        inter_bytes = 0
        inter_packets = 0
        high_bytes = 0
        high_packets = 0
        med_bytes = 0
        med_packets = 0
        low_bytes = 0
        low_packets = 0

        dbg = 0
        for pack in self.db:
            print(str(100 * dbg / len(self.db)))
            total_packets = total_packets + 1
            total_bytes = total_bytes + pack.packet_size

            per_tor_load[pack.tor_id] = per_tor_load[pack.tor_id] + pack.packet_size

            if pack.is_intra():
                intra_packets = intra_packets + 1
                intra_bytes = intra_bytes + pack.packet_size
                if pack.packet_qos == 'high':
                    high_packets = high_packets + 1
                    high_bytes = high_bytes + pack.packet_size
                    intra_high_packets = intra_high_packets + 1
                    intra_high_bytes = intra_high_bytes + pack.packet_size
                elif pack.packet_qos == 'med':
                    med_packets = med_packets + 1
                    med_bytes = med_bytes + pack.packet_size
                    intra_med_packets = intra_med_packets + 1
                    intra_med_bytes = intra_med_bytes + pack.packet_size
                elif pack.packet_qos == 'low':
                    low_packets = low_packets + 1
                    low_bytes = low_bytes + pack.packet_size
                    intra_low_packets = intra_low_packets + 1
                    intra_low_bytes = intra_low_bytes + pack.packet_size
            else:
                inter_packets = inter_packets + 1
                inter_bytes = inter_bytes + pack.packet_size
                if pack.packet_qos == 'high':
                    high_packets = high_packets + 1
                    high_bytes = high_bytes + pack.packet_size
                    inter_high_packets = inter_high_packets + 1
                    inter_high_bytes = inter_high_bytes + pack.packet_size
                elif pack.packet_qos == 'med':
                    med_packets = med_packets + 1
                    med_bytes = med_bytes + pack.packet_size
                    inter_med_packets = inter_med_packets + 1
                    inter_med_bytes = inter_med_bytes + pack.packet_size
                elif pack.packet_qos == 'low':
                    low_packets = low_packets + 1
                    low_bytes = low_bytes + pack.packet_size
                    inter_low_packets = inter_low_packets + 1
                    inter_low_bytes = inter_low_bytes + pack.packet_size
            dbg = dbg + 1

        verification_matrix = []
        verification_matrix.append(total_packets - intra_packets - inter_packets)
        verification_matrix.append(total_bytes - intra_bytes - inter_bytes)
        verification_matrix.append(total_packets - high_packets - med_packets - low_packets)
        verification_matrix.append(total_bytes - high_bytes - med_bytes - low_bytes)
        verification_matrix.append(intra_packets - intra_high_packets - intra_med_packets - intra_low_packets)
        verification_matrix.append(intra_bytes - intra_high_bytes - intra_med_bytes - intra_low_bytes)
        verification_matrix.append(inter_packets - inter_high_packets - inter_med_packets - inter_low_packets)
        verification_matrix.append(inter_bytes - inter_high_bytes - inter_med_bytes - inter_low_bytes)

        print('Verify measurements')
        i = 0
        for ver in verification_matrix:
            if ver != 0:
                print('Error in position' + str(i))
            else:
                print('OK in position' + str(i))
            i = i + 1
        print('----')
        print('Total packets=' + str(total_packets))
        print('Total bytes=' + str(total_bytes))
        print('Total high packets=' + str(high_packets) + ',perc%=' + str(100 * high_packets / total_packets))
        print('Total high bytes=' + str(high_bytes) + ',perc%=' + str(100 * high_bytes / total_bytes))
        print('Total med packets=' + str(med_packets) + ',perc%=' + str(100 * med_packets / total_packets))
        print('Total med bytes=' + str(med_bytes) + ',perc%=' + str(100 * med_bytes / total_bytes))
        print('Total low packets=' + str(med_packets) + ',perc%=' + str(100 * low_packets / total_packets))
        print('Total low bytes=' + str(med_bytes) + ',perc%=' + str(100 * low_bytes / total_bytes))
        print('----')
        print('Total intra packets=' + str(intra_packets) + ',perc%=' + str(100 * intra_packets / total_packets))
        print('Total intra bytes=' + str(intra_bytes) + ',perc%=' + str(100 * intra_bytes / total_bytes))
        print('Total inter packets=' + str(inter_packets) + ',perc%=' + str(100 * inter_packets / total_packets))
        print('Total inter bytes=' + str(inter_bytes) + ',perc%=' + str(100 * inter_bytes / total_bytes))
        print('----')
        print('Total high intra packets=' + str(intra_high_packets) + ',perc%=' + str(
            100 * intra_high_packets / intra_packets))
        print('Total high intra bytes=' + str(intra_high_bytes) + ',perc%=' + str(100 * intra_high_bytes / intra_bytes))
        print('Total high inter packets=' + str(inter_high_packets) + ',perc%=' + str(
            100 * inter_high_packets / inter_packets))
        print('Total high inter bytes=' + str(inter_high_bytes) + ',perc%=' + str(100 * inter_high_bytes / inter_bytes))
        print('Total med intra packets=' + str(intra_med_packets) + ',perc%=' + str(
            100 * intra_med_packets / intra_packets))
        print('Total med intra bytes=' + str(intra_med_bytes) + ',perc%=' + str(100 * intra_med_bytes / intra_bytes))
        print('Total med inter packets=' + str(inter_med_packets) + ',perc%=' + str(
            100 * inter_med_packets / inter_packets))
        print('Total med inter bytes=' + str(inter_med_bytes) + ',perc%=' + str(100 * inter_med_bytes / inter_bytes))
        print('Total low intra packets=' + str(intra_low_packets) + ',perc%=' + str(
            100 * intra_low_packets / intra_packets))
        print('Total low intra bytes=' + str(intra_low_bytes) + ',perc%=' + str(100 * intra_low_bytes / intra_bytes))
        print('Total low inter packets=' + str(inter_low_packets) + ',perc%=' + str(
            100 * inter_low_packets / inter_packets))
        print('Total low inter bytes=' + str(inter_low_bytes) + ',perc%=' + str(100 * inter_low_bytes / inter_bytes))
        print('----')

        for key, value in per_tor_load.items():
            print('Tor' + str(key) + ',bytes:' + str(value))








