#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

from asyncio import StreamReader, StreamWriter
from enum import Enum
from ipaddress import IPv4Address
import asyncio

from StarPRNT.asb import ASB, parse_asb


class StarPRNT:

    class InterfaceType(Enum):
        Ethernet = 0
        Bluetooth = 1
        USB = 2

    def __init__(self, interface_type: InterfaceType):
        self.interface_type = interface_type
        self.status: ASB


class StarPRNTEthernet(StarPRNT):

    def __init__(self, interface_type: StarPRNT.InterfaceType, address: IPv4Address,
                 reader: StreamReader, writer: StreamWriter):
        super().__init__(interface_type)
        self.address = address
        self._reader = reader
        self._writer = writer
        self._read_task = asyncio.create_task(self._read_worker())

    async def _read_worker(self):
        self._writer.write(b"\x1b#*\n\0")
        while True:
            try:
                asb = await self._reader.read(1024)
                self.status, extra = parse_asb(asb)
                if extra is not None:
                    print(extra)
            except:
                await self.close()
                raise

    @classmethod
    async def connect(cls, address: str):
        try:
            address = IPv4Address(address)
        except ValueError:
            raise ValueError("invalid IP address")
        try:
            reader, writer = await asyncio.wait_for(asyncio.open_connection(str(address), 9100), timeout=5)
        except asyncio.TimeoutError:
            raise TimeoutError("connection timed out")
        except ConnectionRefusedError:
            raise ConnectionRefusedError("connection refused")

        return cls(cls.InterfaceType.Ethernet, address, reader, writer)

    async def write(self, data: bytes):
        if self._writer.is_closing():
            raise ConnectionError("connection closed")
        self._writer.write(data)
        await self._writer.drain()

    async def close(self):
        if not self._writer.is_closing():
            self._writer.close()
            await self._writer.wait_closed()