import struct
import enum

# QuicPacket: This class is used to represent a QUIC packet. It has the following attributes:
# source_id: The ID of the source node
# destination_id: The ID of the destination node
# packet_id: The ID of the packet
# stream_id: The ID of the stream
# packet_type: The type of the packet. It is an enum of type PacketType
# content: The content of the packet

MIN_PACKET_SIZE = 1000
MAX_PACKET_SIZE = 2000
HEADER_SIZE = 18

class PacketType(enum.Enum):
    Handshake = 1
    Data = 2
    Command = 3
    Close = 4
    
class Packet:
    def __init__(self, source_id, destination_id, packet_id, stream_id, packet_type : PacketType, content):
        self.source_id = source_id
        self.destination_id = destination_id
        self.packet_id = packet_id
        self.stream_id = stream_id
        self.packet_type: PacketType = packet_type
        self.content = content
# pack: This method is used to pack the packet into a byte array. It returns the byte array
    def pack(self):
        header = struct.pack('!IIIIH', self.source_id, self.destination_id, self.packet_id, self.stream_id, self.packet_type.value)
        return header + self.content
# unpack: This method is used to unpack the byte array into a packet. It returns the packet
    def unpack(data):
        try :
            header = data[:HEADER_SIZE]
            content = data[HEADER_SIZE:]
            source_id, destination_id, packet_id, stream_id, packet_type_val = struct.unpack('!IIIIH', header)
            packet_type = PacketType(packet_type_val)
            return Packet(source_id, destination_id, packet_id, stream_id, packet_type, content)
        except Exception as e:
            raise TypeError("Invalid packet data")
        
    def __str__(self):
        return f"""Packet:
    source_id = {self.source_id}
    destination_id = {self.destination_id}
    packet_id = {self.packet_id}
    stream_id = {self.stream_id}
    packet_type = {self.packet_type.name},
    content = {self.content.decode()}"""

#TODO: Implement the QuicStream class