import unittest
from unittest.mock import Mock, patch
from QuicClient import QuicClient
from QuicPacket import Packet, PacketType

class TestQuicClient(unittest.TestCase):
    
    def setUp(self):
        # Mocking the QuicClient for testing
        self.client = QuicClient("localhost", 7000, 2)
        self.client.sock = Mock()
        self.client.send_packet = Mock()
        self.client.recv_packet = Mock(return_value=(Packet(2, 1, 0, 0, PacketType.Handshake, b"Hello"), ("127.0.0.1", 7000)))
        
    def test_connect(self):
        self.client.connect()
        self.assertEqual(self.client.peer_address, ("127.0.0.1", 7000))
        self.assertEqual(self.client.peer_id, 2)
    
    def test_handle_packet(self):
        packet = Packet(2, 1, 0, 0, PacketType.Close, b"Bye")
        self.client.handle_packet(packet)
        self.assertTrue(self.client.close_connection.called)

if __name__ == "__main__":
    unittest.main()
