import unittest
import struct
from QuicPacket import *

class TestPacket(unittest.TestCase):

    def setUp(self):
        # Initialize common test data here if needed
        self.source_id = 123
        self.destination_id = 456
        self.packet_id = 789
        self.stream_id = 1
        self.packet_type = PacketType.Handshake
        self.content = b"Test content"

    def test_pack(self):
        packet = Packet(self.source_id, self.destination_id, self.packet_id, self.stream_id, self.packet_type, self.content)
        packed_data = packet.pack()

        # Assert that packed data is bytes
        self.assertIsInstance(packed_data, bytes)

        

    def test_unpack(self):
        packed_data = struct.pack('!IIIIH', self.source_id, self.destination_id, self.packet_id, self.stream_id, self.packet_type.value) + self.content
        unpacked_packet = Packet.unpack(packed_data)

        # Assert that unpacked_packet is an instance of Packet
        self.assertIsInstance(unpacked_packet, Packet)

        # Assert that unpacked_packet attributes match the original data
        self.assertEqual(unpacked_packet.source_id, self.source_id)
        self.assertEqual(unpacked_packet.destination_id, self.destination_id)
        self.assertEqual(unpacked_packet.packet_id, self.packet_id)
        self.assertEqual(unpacked_packet.stream_id, self.stream_id)
        self.assertEqual(unpacked_packet.packet_type, self.packet_type)
        self.assertEqual(unpacked_packet.content, self.content)

    def test_invalid_unpack(self):
        invalid_data = b"Invalid data"
        
        # Assert that unpacking invalid data raises a TypeError
        with self.assertRaises(TypeError):
            Packet.unpack(invalid_data)

    def test_str_representation(self):
        packet = Packet(self.source_id, self.destination_id, self.packet_id, self.stream_id, self.packet_type, self.content)
        packet_str = str(packet)

        # Assert that the string representation contains expected information
        self.assertIn(f"source_id = {self.source_id}", packet_str)
        self.assertIn(f"destination_id = {self.destination_id}", packet_str)
        self.assertIn(f"packet_id = {self.packet_id}", packet_str)
        self.assertIn(f"stream_id = {self.stream_id}", packet_str)
        self.assertIn(f"packet_type = {self.packet_type.name}", packet_str)
        self.assertIn(f"content = {self.content.decode()}", packet_str)

    # Additional test cases

    def test_unpack_empty_data(self):
        # Test unpacking empty data
        with self.assertRaises(TypeError):
            Packet.unpack(b"")

    def test_pack_unpack_round_trip(self):
        # Test pack and then unpack to ensure round-trip integrity
        packet = Packet(self.source_id, self.destination_id, self.packet_id, self.stream_id, self.packet_type, self.content)
        packed_data = packet.pack()
        unpacked_packet = Packet.unpack(packed_data)

        # Assert that unpacked_packet attributes match the original packet
        self.assertEqual(unpacked_packet.source_id, self.source_id)
        self.assertEqual(unpacked_packet.destination_id, self.destination_id)
        self.assertEqual(unpacked_packet.packet_id, self.packet_id)
        self.assertEqual(unpacked_packet.stream_id, self.stream_id)
        self.assertEqual(unpacked_packet.packet_type, self.packet_type)
        self.assertEqual(unpacked_packet.content, self.content)

    def test_pack_unpack_edge_cases(self):
        # Test edge cases for pack and unpack methods
        # Edge case 1: Minimum packet size
        packet_min_size = Packet(self.source_id, self.destination_id, self.packet_id, self.stream_id, self.packet_type, b"")
        packed_min_size = packet_min_size.pack()
        unpacked_min_size = Packet.unpack(packed_min_size)
        self.assertEqual(unpacked_min_size.content, b"")

        # Edge case 2: Maximum packet size
        max_content = b"A" * (MAX_PACKET_SIZE - HEADER_SIZE)  # Max content size based on given packet structure header size is
        packet_max_size = Packet(self.source_id, self.destination_id, self.packet_id, self.stream_id, self.packet_type, max_content)
        packed_max_size = packet_max_size.pack()
        unpacked_max_size = Packet.unpack(packed_max_size)
        self.assertEqual(unpacked_max_size.content, max_content)

if __name__ == '__main__':
    unittest.main()

