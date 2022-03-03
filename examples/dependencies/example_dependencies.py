import asyncio
from typing import List

from conflagrate import BlockingBehavior, dependency, nodetype
import json


@nodetype("read_messages_from_file")
def read_messages_from_file(*, config) -> List[str]:
    with open(config["input_filename"]) as f:
        return json.load(f)


@nodetype("send_to_listener")
async def send_messages_to_listener(
        messages: List[str], *,
        send_datagram_interface
) -> None:
    for message in messages:
        send_datagram_interface.send(message)


@nodetype("listener")
async def listener(*_, receive_datagram_interface) -> str:
    return await receive_datagram_interface.receive()


@nodetype("write_to_disk")
def write_to_disk(message: str, *, config) -> None:
    with open(config["output_filename"], 'a') as f:
        f.write(f"{message}\n")


@nodetype("print_to_screen", blocking_behavior=BlockingBehavior.NON_BLOCKING)
def print_to_screen(message: str) -> None:
    print(f"Message received: {message}", flush=True)


@dependency
async def config():
    loop = asyncio.get_running_loop()
    f = await loop.run_in_executor(None, open, "config.json")
    try:
        return await loop.run_in_executor(None, json.load, f)
    finally:
        loop.run_in_executor(None, f.close)


class DatagramBaseProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.transport = None
        self.ready = False

    def connection_made(self, transport) -> None:
        self.transport = transport
        self.ready = True

    def connection_lost(self, exc) -> None:
        self.ready = False


class DatagramSenderProtocol(DatagramBaseProtocol):
    def datagram_received(self, data, addr):
        pass

    def error_received(self, exc):
        pass

    def send(self, message: str):
        if self.ready:
            self.transport.sendto(message.encode())


class DatagramReceiverProtocol(DatagramBaseProtocol):
    def __init__(self, queue: asyncio.Queue):
        super().__init__()
        self.queue = queue

    def datagram_received(self, data: bytes, addr) -> None:
        self.queue.put_nowait(data.decode("utf-8"))

    async def receive(self):
        return await self.queue.get()


@dependency
async def send_datagram_interface(config):
    loop = asyncio.get_running_loop()
    _, protocol = await loop.create_datagram_endpoint(
        lambda: DatagramSenderProtocol(),
        remote_addr=('localhost', config["port"])
    )
    return protocol


@dependency
async def receive_datagram_interface(config):
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()
    _, protocol = await loop.create_datagram_endpoint(
        lambda: DatagramReceiverProtocol(queue),
        local_addr=('localhost', config["port"])
    )
    return protocol
