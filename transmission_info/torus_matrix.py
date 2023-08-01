import csv
import os
from torus_integrated import myglobal

class Torus_Matrix:
    def __init__(self):
        self.db = []
        self.load()

    def load(self):
        with open(myglobal.TORUS_MATRIX_FILE) as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=',')
            for row in csv_reader:
                new_rec=Torus_Record(row['rx'],row['tx'],row['out_dir'],row['in_dir'],row['lamda'])
                self.db.append(new_rec)

    def get_trx_info_from_tx_rx_id(self,tx_id,rx_id):
        for rec in self.db:
            if tx_id==rec.tx and rx_id==rec.rx:
                return rec.out_dir,rec.in_dir,rec.lamda

class Torus_Record:
    def __init__(self, rx,tx,out_dir,in_dir,lamda):
        self.rx=int(rx)
        self.tx=int(tx)
        self.out_dir=str(out_dir)
        self.in_dir=str(in_dir)
        self.lamda=int(lamda)
        self.size=0

    def show(self):
        print('tx='+str(self.tx)+',outdir='+str(self.out_dir)+',rx='+str(self.rx)+',indir='+str(self.in_dir))