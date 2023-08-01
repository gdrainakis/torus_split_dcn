import csv
from torus_integrated import myglobal

class Buffer():
    def __init__(self,size):
        self.size=size
        self.db=[]

    def has_packets(self):
        if len(self.db)>0:
            return True

    def remove_packet(self,id):
        for pack in self.db:
            if pack.id==id:
                self.db.remove(pack)
                break

    def get_next_packet(self):
        mypacket=self.db[0]
        self.db.pop(0)
        return mypacket

    def delete_by_id(self,id):
        for element in self.db:
            if element.id==id:
                self.db.remove(element)
                break

    def get_current_size(self):
        mysize=0
        for element in self.db:
            mysize=mysize+element.packet_size
        return mysize

    def can_add_pack(self,packet):
        current_buffer_size=self.get_current_size()
        if current_buffer_size+packet.packet_size<=self.size:
            return True
        else:
            return False

    def add_pack(self,packet):
        self.db.append(packet)

class Node_Output_Buffer(Buffer):
    def __init__(self,size,parent_tor_id):
        self.parent_tor_id=parent_tor_id
        Buffer.__init__(self,size)

class Tor_Outbound_Buffer(Buffer):
    def __init__(self,size,destination_tor):
        self.destination_tor=int(destination_tor)
        Buffer.__init__(self,size)