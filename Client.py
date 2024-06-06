import asyncio

class QUICClient:
    async def connect_to_server(self, server_address):
        try:
            reader, writer = await asyncio.open_connection(*server_address)
            # Receive files from the server
            await self.receive_files(reader)
        except Exception as e:
            print(f"Error: {e}")

    async def receive_files(self, reader):
        # Receive files sent by the server
        while True:
            data = await reader.read(1024)
            if not data:
                break
            # Process received data (e.g., write to file)
            # Here you would write the received data to a file
            print(f"Received {len(data)} bytes from server")

async def main():
    client = QUICClient()
    server_address = ('localhost', 8888)
    await client.connect_to_server(server_address)

if __name__ == "__main__":
    asyncio.run(main())
