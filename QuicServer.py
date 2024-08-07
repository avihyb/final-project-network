import threading
import socket
import random
import sys
import time
from QuicStream import *

# Constants
TIMEOUT = 5
MAX_PACKET_SIZE = 2000

class QuicServer:
    def __init__(self, host='', port=7000):
        self.server_address = (host, port)  # Server address
        self.connection_id = random.randint(0, 2**16 - 1)  # Random connection ID
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a UDP socket
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Enable address reuse
        self.sock.bind(self.server_address)  # Bind the socket to the address
        print("Server started on", self.server_address)
        
        self.flows: Dict[int, QuicStream] = {}  # Dictionary to hold QuicStream objects
        self.threads: Dict[QuicStream, threading.Thread] = {}  # Dictionary to hold threads for each stream
        self.lock = threading.Lock()  # Lock for thread safety
        
        self.peer_address = None  # Address of the peer (client)
        self.peer_id = None  # Peer ID (client's connection ID)
        self.packet_num = 0  # Packet number for sending packets
        self.expected_packet_num = 0  # Expected packet number for receiving packets
        
        self.send_start = None  # Timestamp for when sending starts
        self.send_end = None  # Timestamp for when sending ends
        
    def send_packet(self, address, packet):
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
            self.close_connection()
            exit()

    def listen(self):
        # Listen for incoming handshake packets
        print("Server is listening...")
        while True:
            packet, addr = self.recv_packet()
            if packet is None or packet.packet_type != PacketType.Handshake:
                print("Discarding packet")
                continue

            self.peer_address = addr  # Store peer address
            self.peer_id = packet.source_id  # Store peer ID
            self.expected_packet_num = packet.packet_id + 1

            # Send handshake acknowledgement
            ack_packet = Packet(self.connection_id, self.peer_id, 0, 0, PacketType.Handshake, b"Hello")
            self.send_packet(addr, ack_packet)
            print("Handshake completed. Connection established with", addr)
            self.sock.settimeout(TIMEOUT)
            break

    def run(self):
        # Run the server
        self.listen()

        while True:
            packet = self.recv_packet()
            if packet is None:
                continue
            if packet.stream_id != 0 and packet.stream_id in self.flows:
                self.flows[packet.stream_id].incoming_packets[packet.packet_id] = packet
            elif packet.stream_id == 0:
                self.handle_command(packet)

    def handle_command(self, packet):
        if packet.content.startswith(b"StartFlow"): # StartFlow int(number_of_streams)
            num_of_streams = int(packet.content.split()[1]) 
            for i in range(num_of_streams):
                self.flows[i+1] = QuicStream(self, i+1, f"randomFile{i+1}.txt")
            ack_packet = Packet(self.connection_id, self.peer_id,
                                self.packet_num, 0, PacketType.Command, b"FlowStarted")
            self.packet_num += 1
            self.send_packet(self.peer_address, ack_packet)
            # run the streams each in a separate thread
            self.send_start = time.time()
            for stream_id, stream in self.flows.items():
                self.send_thread_start_indicator(stream_id)
                thread = threading.Thread(target=stream.run_sender)
                self.threads[stream] = thread
                thread.start()
        if packet.packet_type == PacketType.Close:
            
            print("Closing connection")
            while self.threads:
                stream, thread = self.threads.popitem()
                thread.join()
            self.send_end = time.time()
            self.print_stats()
            self.sock.close()
            sys.exit()

    def send_thread_start_indicator(self, stream_id):
            indicator_packet = Packet(
                self.connection_id,
                self.peer_id,
                self.packet_num,
                0,  
                PacketType.Command,
                f"ThreadStart_{stream_id}".encode()
            )
            self.packet_num += 1
            self.send_packet(self.peer_address, indicator_packet)
            print(f"Sent thread start indicator for stream {stream_id}")

    def print_stats(self):
        # Print statistics for all streams
        total_bytes = 0
        total_packets = 0
        total_time_taken = self.send_end - self.send_start

        for stream in self.flows.values():
            total_stream_bytes = stream.stats['total_bytes_received'] + stream.stats['total_bytes_sent']
            total_stream_packets = stream.stats['total_packets_received'] + stream.stats['total_packets_sent']
            time_taken = stream.stats['time_taken']

            total_bytes += total_stream_bytes
            total_packets += total_stream_packets

            print(f"\nStream {stream.stream_id} stats:")
            print(f"Packet size:", stream.mtu)
            print("Time taken:", '%.2f' % stream.stats['time_taken'] + " seconds")
            print(f"Total bytes: {str_bytes(total_stream_bytes)}")
            print(f"Total packets: {total_stream_packets}")
            print(f"Avg bytes per second: {str_bytes('%.2f' % ((total_stream_bytes) / time_taken))}/s")
            print(f"Avg packets per second: {int(((total_stream_packets) / time_taken))} Packets/s\n")

        print("Total stats:")
        print(f"Total bytes received: {str_bytes(total_bytes)}")
        print(f"Total packets received: {total_packets}")
        print(f"Total time taken: {'%.2f' % total_time_taken} seconds")
        print(f"Avg bytes per second: {str_bytes('%.2f' % (total_bytes / total_time_taken))}/s")
        print(f"Avg packets per second: {int((total_packets / total_time_taken))} Packets/s")

def str_bytes(number_of_bytes) -> str:
    # Convert bytes to a human-readable string
    if type(number_of_bytes) == str:
        number_of_bytes = float(number_of_bytes)
    if number_of_bytes < 1024:
        return f"{'%.2f' % number_of_bytes}B"
    elif number_of_bytes < 1024**2:
        return f"{'%.2f' % (number_of_bytes / 1024)}KB"
    elif number_of_bytes < 1024**3:
        return f"{'%.2f' % (number_of_bytes / 1024**2)}MB"
    else:
        return f"{'%.2f' % (number_of_bytes / 1024**3)}GB"

if __name__ == "__main__":
    # Run the server with optional port argument
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        server = QuicServer(port=port)
    else:
        server = QuicServer()
    server.run()
