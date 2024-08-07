import threading
import socket
import time
import random
import sys
from typing import Dict
from QuicPacket import *
# QuicStream: This class is used to represent a QUIC stream. It has the following attributes:
# connection: The connection object
# stream_id: The ID of the stream
# file_name: The name of the file to send or receive
# packet_num: The packet number
# file_data: The data of the file
# outgoing_packets: The packets to send
# incoming_packets: The packets received from the main thread
# mtu: The maximum transmission unit
# total_bytes: The total bytes
# callback: The callback function
# stats: The statistics of the stream


TIMEOUT = 0.5
US = 0.000001
SEND_INTERVAL = 50 * US

class QuicStream:
    def __init__(self, connection, stream_id, file_name=None, callback=None):
        self.connection = connection # UDP socket of the client or server
        self.stream_id = stream_id
        self.file_name = file_name
        self.packet_num = 0
        self.file_data: Dict[int, Packet] = {}
        self.outgoing_packets: Dict[int, Packet] = {} # file_data to send
        self.incoming_packets: Dict[int, Packet] = {} # packets received from main thread
        self.mtu = random.randint(MIN_PACKET_SIZE, MAX_PACKET_SIZE)
        self.total_bytes = 0
        self.callback = callback
        self.stats = {
            "total_bytes_sent": 0,
            "total_bytes_received": 0,
            "total_packets_sent": 0,
            "total_packets_received": 0,
            "time_taken": 0,
        }

    # Sender functions
# prepare_file: This method is used to prepare the file to send. It reads the file and splits it into packets.
    def prepare_file(self):
        with open(self.file_name, 'rb') as file:
            data = file.read()
            for i in range(0, len(data), self.mtu):
                packet_id = i // self.mtu
                packet = Packet(self.connection.connection_id, self.connection.peer_id,
                                packet_id, self.stream_id, PacketType.Data, data[i:i+self.mtu])
                self.outgoing_packets[packet_id] = packet

# send_packets: This method is used to send the packets to the peer. It sends the packets in a loop.
    def send_packets(self):
        timer = time.time()
        timeout = 0.1
        keys: list = list(self.outgoing_packets.keys())
        while len(keys) > 0 and time.time() - timer < timeout:
            packet = self.outgoing_packets[keys.pop(0)]
            self.connection.send_packet(self.connection.peer_address, packet)
            self.stats["total_bytes_sent"] += len(packet.content)
            self.stats["total_packets_sent"] += 1
            time.sleep(US)

# handle_incoming_packets: This method is used to handle the incoming packets. 
# It receives the ACK packets and removes the packets from the outgoing_packets list.
    def handle_incoming_packets(self):
        timer = time.time()
        timeout = 0.1
        acks = []
        packet_keys = list(self.incoming_packets.keys())
        while time.time() - timer < timeout and self.outgoing_packets:
            if not packet_keys:
                time.sleep(0.01)  # Avoid busy waiting
                continue
            packet_id = packet_keys.pop(0)
            packet = self.incoming_packets.pop(packet_id)
            if packet.packet_type == PacketType.Command and packet.content.startswith(b"ACK"):
                acked_packet_id = int(packet.content.split()[1])
                if acked_packet_id in self.outgoing_packets:
                    del self.outgoing_packets[acked_packet_id]
                    self.stats["total_bytes_received"] += len(
                        packet.content)
                    self.stats["total_packets_received"] += 1

        self.stats["time_taken"] += time.time() - timer

        if not self.outgoing_packets:
            print("Stream", self.stream_id, "completed sending")
            print("Time taken:", self.stats["time_taken"])
            if self.callback:
                self.callback(self.stream_id)

        # time.sleep(3)  # Debugging
        
# run_sender: This method is used to run the sender thread. It prepares the file and sends the packets.
    def run_sender(self):
        self.prepare_file()
        while self.outgoing_packets:
            self.send_packets()
            self.handle_incoming_packets()

        # Send EndFlow command
        end_flow_packet = Packet(self.connection.connection_id, self.connection.peer_id,
                                 self.packet_num, self.stream_id, PacketType.Command, b"EndFlow")

        self.connection.send_packet(
            self.connection.peer_address, end_flow_packet)
        
        time.sleep(1)  # Debugging

    # Receiver functions
    # receiver_handle_packets: This method is used to handle the incoming packets.
    # It receives the data packets and sends the ACK packets.
    def receiver_handle_packets(self):
        while True:
            if not self.incoming_packets:
                time.sleep(0.01)  # Avoid busy waiting
                continue
            packet_id = list(self.incoming_packets.keys())[0]
            # print("Stream", self.stream_id, "received packet", packet_id)
            # print("packets:", len(self.incoming_packets))
            packet = self.incoming_packets.pop(packet_id)
            # print("After pop packets:", len(self.incoming_packets))
            if packet.packet_type == PacketType.Data:
                if packet.packet_id not in self.file_data:
                    self.file_data[packet.packet_id] = packet
                    self.stats["total_bytes_received"] += len(packet.content)
                    self.stats["total_packets_received"] += 1
                # Send ACK
                ack_packet = Packet(self.connection.connection_id, self.connection.peer_id, self.packet_num,
                                    self.stream_id, PacketType.Command, b"ACK " + str(packet.packet_id).encode())
                self.connection.send_packet(
                    self.connection.peer_address, ack_packet)
                self.packet_num += 1

            elif packet.packet_type == PacketType.Command:
                if packet.content.startswith(b"EndFlow"):
                    print("Stream", self.stream_id, "completed receiving")
                    ack_packet = Packet(self.connection.connection_id, self.connection.peer_id,
                                        self.packet_num, self.stream_id, PacketType.Command, b"FlowEnded")
                    self.connection.send_packet(
                        self.connection.peer_address, ack_packet)
                    self.stats["time_taken"] = time.time() - \
                        self.stats["time_taken"]
                    if self.callback:
                        self.callback(self.stream_id)
                    break
            else:
                print("Invalid packet type")
                print(packet)
                time.sleep(2)  # Debugging
                continue

    # write_file: This method is used to write the file to the disk.
    def write_file(self):
        with open(self.file_name, 'wb') as file:
            for i in range(len(self.file_data)):
                file.write(self.file_data[i].content)

    # run_receiver: This method is used to run the receiver thread. It handles the incoming packets.
    def run_receiver(self):
        self.file_data = {}
        self.receiver_handle_packets()
        # self.write_file()
        # close this thread
        return
