import asyncio
import random

class QUICServer:
    def __init__(self, num_flows):
        self.num_flows = num_flows
        self.connections = {}  # Dictionary to store client connections

    async def handle_client(self, reader, writer):
        # Handle each client connection
        client_id = len(self.connections)
        self.connections[client_id] = writer

        # Start sending files in separate flows
        for flow_id in range(self.num_flows):
            file_size = 10 * 1024 * 1024  # 10 MB file
            filename = f"file_{flow_id}.txt"
            # Generate random data for the file
            file_data = bytearray(random.getrandbits(8) for _ in range(file_size))
            # Send file data to the client
            await self.send_file(client_id, flow_id, filename, file_data)

    async def send_file(self, client_id, flow_id, filename, data):
        # Simulate sending the file data over the connection
        writer = self.connections[client_id]
        writer.write(data)
        await writer.drain()
        print(f"Sent file {filename} in flow {flow_id} to client {client_id}")

async def main():
    server = QUICServer(num_flows=5)
    server_address = ('localhost', 8888)

    server_coroutine = asyncio.start_server(server.handle_client, *server_address)
    server = await server_coroutine

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
