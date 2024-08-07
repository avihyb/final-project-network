import socket
import random
import threading
import sys
from QuicStream import *

# Constants
TIMEOUT = 5

class QuicClient:
    def __init__(self, host='localhost', port=7000, num_flows=4):
        # Convert the host name to an IP address
        host = socket.gethostbyname(host)
        self.server_address = (host, port)  # Server address
        self.connection_id = random.randint(0, 2**16 - 1)  # Random connection ID
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a UDP socket
        self.num_flows = num_flows  # Number of flows (streams)
        self.flows: Dict[int, QuicStream] = {}  # Dictionary to hold QuicStream objects
        self.flow_status: Dict[int, bool] = {i+1: False for i in range(num_flows)}  # Track the status of each flow
        self.lock = threading.Lock()  # Lock for thread safety
        self.peer_address = None  # Address of the peer (server)
        self.peer_id = None  # Peer ID (server's connection ID)
        self.packet_num = 0  # Packet number for sending packets
        self.expected_packet_num = 0  # Expected packet number for receiving packets

    def send_packet(self, address, packet: Packet):
        # Send a packet to the specified address
        with self.lock:
            self.sock.sendto(packet.pack(), address)

    def recv_packet(self):
        # Receive a packet from the socket
        try:
            data, addr = self.sock.recvfrom(MAX_PACKET_SIZE)
            packet = Packet.unpack(data)

            if self.peer_id is None:
                return packet, addr

            if packet.source_id != self.peer_id or packet.destination_id != self.connection_id:
                print("Packet is not for this connection")
                return None
            return packet

        except (TimeoutError, TypeError):
            return None
        except Exception as e:
            exit()

    def connect(self):
        # Initiate a connection to the server
        print("Connecting to", self.server_address)
        handshake_packet = Packet(self.connection_id, 0, self.packet_num, 0, PacketType.Handshake, b"Hello")
        self.packet_num += 1
        self.send_packet(self.server_address, handshake_packet)

        while True:
            packet, addr = self.recv_packet()
            if packet.packet_type == PacketType.Handshake and addr == self.server_address and packet.destination_id == self.connection_id:
                self.peer_address = addr
                self.peer_id = packet.source_id
                self.expected_packet_num = packet.packet_id + 1
                print("Handshake completed. Connection established with", addr)
                self.sock.settimeout(TIMEOUT)
                break

    def run(self):
        # Run the client
        self.connect()
        self.request_files()

        while True:
            packet = self.recv_packet()
            if packet is None:
                continue
            if packet.stream_id != 0 and packet.stream_id in self.flows:
                self.flows[packet.stream_id].incoming_packets[packet.packet_id] = packet
            elif packet.stream_id == 0:
                self.handle_packet(packet)

    def handle_packet(self, packet):
        # Handle received packets
        if packet.packet_type == PacketType.Command:
            self.handle_command(packet)
        elif packet.packet_type == PacketType.Close:
            self.close_connection()
            exit()

    def close_connection(self):
        # Close the connection
        print("Closing connection")
        ack_packet = Packet(self.connection_id, self.peer_id, self.packet_num, 0, PacketType.Close, b"Bye")
        self.packet_num += 1
        self.send_packet(self.peer_address, ack_packet)
        print("Connection closed, exiting")
        try:
            time.sleep(1)
            self.sock.close()
            exit()
        except Exception as e:
            exit()

    def handle_command(self, packet):
        # Handle command packets (not implemented)
        pass

    def request_files(self):
        # Request files and run streams in separate threads
        for i in range(self.num_flows):
            self.flows[i+1] = QuicStream(self, i+1, f"file_{i}.txt", self.flow_completed)
            threading.Thread(target=self.flows[i+1].run_receiver).start()

        message = f"StartFlow {self.num_flows}".encode()
        packet = Packet(self.connection_id, self.peer_id, 0, 0, PacketType.Command, message)
        self.send_packet(self.peer_address, packet)

    def flow_completed(self, stream_id):
        # Callback when a flow is completed
        self.flow_status[stream_id] = True
        if all(self.flow_status.values()):
            for stream in self.flows.values():
                stream.write_file()
            self.close_connection()

if __name__ == "__main__":
    # Run the client with command line arguments or defaults
    if len(sys.argv) <= 4:
        host = socket.gethostbyname(sys.argv[1])
        port = int(sys.argv[2])
        num_flows = int(sys.argv[3])
        client = QuicClient(host, port, num_flows)
        client.run()
        exit()

    client = QuicClient()
    client.run()
