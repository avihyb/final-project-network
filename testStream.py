import unittest
from unittest.mock import Mock
from QuicStream import QuicStream
from QuicPacket import Packet, PacketType

class TestQuicStream(unittest.TestCase):
    
    def setUp(self):
        # Mocking the connection for testing
        self.connection_mock = Mock()
        self.connection_mock.connection_id = 1
        self.connection_mock.peer_id = 2
        self.connection_mock.peer_address = ("127.0.0.1", 7000)
        
        # Initialize a test QuicStream
        self.stream = QuicStream(self.connection_mock, 1, "test_file.txt")

    def test_prepare_file(self):
        # Mocking file reading for prepare_file test
        with open('test_file.txt', 'wb') as file:
            file.write(b'TestData')
        
        self.stream.prepare_file()
        
        # Check that outgoing_packets dictionary is populated correctly
        self.assertEqual(len(self.stream.outgoing_packets), 1)

    def test_run_sender(self):
        # Mocking send_packet and recv_packet for run_sender test
        self.connection_mock.send_packet = Mock()
        self.connection_mock.recv_packet = Mock(return_value=(Packet(2, 1, 0, 1, PacketType.Command, b"ACK 0"), ("127.0.0.1", 7000)))
        
        # Set up outgoing packet
        self.stream.outgoing_packets[0] = Packet(1, 2, 0, 1, PacketType.Data, b"TestData")
        
        self.stream.run_sender()
        
        # Check that stats are updated correctly
        self.assertEqual(self.stream.stats["total_packets_sent"], 1)
        self.assertEqual(self.stream.stats["total_packets_received"], 1)

if __name__ == "__main__":
    unittest.main()
