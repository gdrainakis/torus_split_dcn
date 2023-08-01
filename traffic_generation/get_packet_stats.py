from torus_integrated import myglobal
from torus_integrated.traffic import *

# params
investigation_folder='C:\Pycharm\Projects\polydiavlika\\torus_integrated\\traffic_datasets\\torus200_80in\\'
tors=16
servers=16
###

tf=Traffic_system(dataset_folder=investigation_folder,
                  tors=tors,
                  servers=servers,
                  remove_inter=False)
tf.get_stats()


