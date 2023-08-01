# Project Title
Scalable and Low Server-to-Server Latency Data Center Network Architecture Based on Optical Packet Inter-Rack and Intra-Rack Switching 

## Description
Source-code for the simulation environment described in the paper "Scalable and Low Server-to-Server Latency Data Center Network Architecture Based on Optical Packet Inter-Rack and Intra-Rack Switching"

## Getting Started
This is a Python-based simulation environment that emulates an end-to-end Data Centre Network (DCN) communication. Servers are assumed to be organized into racks. Intra-rack servers are interconnected via the intra-rack network, as described in “Collision-free distributed MAC protocol for passive optical intra-rack data center networks”. In each rack, a Top-of-Rack (ToR) switch lies to enable ToR-to-ToR (inter-rack) communication, as shown in “P-Torus: wavelength-based switching in packet granularity for intra-data-center networks”. 

The simulation contains all functions and respective scripts to generate synthetic traffic datasets with a 3-level priority class (High, Medium, Low) at various configurations, as modeled in "Dual MAC based hierarchical optical access network for hyperscale data centers". The DCN modeling and architecture is defined within the "entrypoint.py" script (number of servers, channels, buffers, switches, datarates, strategies/policies, etc.). The outcome of the simulation (on a per-packet basis) is saved in the logs/ folder in a .csv format. Packet features include: packet id, packet generation time, packet size, packet priority class, source server id, source ToR id, destination server id, destination tor id and all timestamps that relate to the packet's entrance/exit from a buffer/channel (note that -1 refer to NaN values e.g., when a packet is dropped from a buffer).

### Dependencies
Python 3.8, Numpy, Pandas, Matplotlib

### Installing
No special requirements

### Executing program
* Create synthetic datasets using the script "build_traffic_datasets.py"
* Set system and DCN parameters in the following scripts "myglobal.py", "entrypoint.py"
* Run simulation
```
python entrypoint.py
```
* Per packet Statistics are collected in the logs/ folder
