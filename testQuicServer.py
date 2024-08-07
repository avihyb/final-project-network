import unittest
from unittest.mock import Mock
from QuicServer import *


class TestQuicServer(unittest.TestCase):

    def setUp(self):
        # Mocking the QuicServer for testing
        self.server = QuicServer("localhost", 7000)
        self.server.sock = Mock()
        self.server.send_packet = Mock()

    def test_listen(self):
        # Mocking the return value of recv_packet
        mock_packet = Packet(8, 0, 0, 0, PacketType.Handshake, b"Hello")
        mock_address = ("126.52.144.52", 8000)
        self.server.recv_packet = Mock(
            return_value=(mock_packet, mock_address))

        # Call listen method
        self.server.listen()

        # Assertions
        self.assertEqual(self.server.peer_address, mock_address)
        self.assertEqual(self.server.peer_id, mock_packet.source_id)

    def test_send_packet(self):
        self.test_listen()

        # Call send_packet method
        packet = Packet(self.server.connection_id, 8, 0,
                        0, PacketType.Handshake, b"Hello")
        self.server.send_packet(self.server.peer_address, packet)

        ackPacket = Packet(8, self.server.connection_id, 0,
                           0, PacketType.Handshake, b"Hello")

        self.server.recv_packet = Mock(
            return_value=(ackPacket, self.server.peer_address))
        
        
        # Assertions

        self.server.send_packet.assert_called_with(self.server.peer_address, packet)

    def test_recv_packet(self):
        self.test_listen()

        mock_Packet = Packet(8, self.server.connection_id,
                             0, 0, PacketType.Handshake, b"Hello")
        mock_data = mock_Packet.pack()


if __name__ == "__main__":
    unittest.main()
