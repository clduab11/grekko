import logging
import asyncio
import websockets

class DataStreamer:
    def __init__(self, sources):
        self.logger = logging.getLogger(__name__)
        self.sources = sources
        self.buffer = []

    async def stream_data(self, source):
        async with websockets.connect(source) as websocket:
            while True:
                data = await websocket.recv()
                self.buffer.append(data)
                self.logger.info(f"Received data from {source}: {data}")

    async def start_streaming(self):
        tasks = [self.stream_data(source) for source in self.sources]
        await asyncio.gather(*tasks)

    def get_buffered_data(self):
        return self.buffer

    def clear_buffer(self):
        self.buffer = []
        self.logger.info("Buffer cleared")
