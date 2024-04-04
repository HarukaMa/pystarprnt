#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os.path
import pathlib
from abc import ABC, abstractmethod
from asyncio import StreamReader, StreamWriter
from enum import Enum
from io import BytesIO
from ipaddress import IPv4Address
import asyncio
from struct import pack

from PIL import Image, ImageOps
from .asb import ASB, parse_asb
from .enums import Alignment, PrintSpeed, Model, UTF8Font, PrintDensity


class StarPRNT(ABC):

    class InterfaceType(Enum):
        Ethernet = 0
        Bluetooth = 1
        USB = 2

    def __init__(self, interface_type: InterfaceType, model: Model = Model.Unknown):
        self.interface_type = interface_type
        self.model = model
        self.version = "0.0"
        self.status: ASB

    @abstractmethod
    async def connect(self, address: str):
        pass

    @abstractmethod
    async def close(self):
        pass

    @abstractmethod
    async def write_raw(self, data: bytes):
        pass

    async def print(self, data: str):
        await self.write_raw(data.encode())

    async def print_line(self, data: str):
        await self.print(data + "\n")

    # 2.3.1 Font style and character set

    async def set_font_scale(self, width: int, height: int):
        if not 1 <= width <= 6 or not 1 <= height <= 6:
            raise ValueError("font scale out of range (1-6)")
        await self.write_raw(b"\x1bi" + bytes([height - 1, width - 1]))

    # 2.3.9 Cutter control

    async def cut(self):
        # FIXME: support type 2, don't hardcode
        await self.write_raw(b"\x1bd2")

    # 2.3.12 Dot image graphics

    async def raster_test(self):
        await self.write_raw(b"\x1b\x1dS\x01\x48\x00\x30\x00\x00")
        for i in range(48):
            if i % 2 == 1:
                await self.write_raw(b"\x55" * 72)
            else:
                await self.write_raw(b"\xaa" * 72)

    async def print_image(self, image: str | BytesIO, alignment: Alignment = Alignment.Center):
        with Image.open(image) as img:
            width, height = img.size
            if img.mode == "RGBA":
                bg = Image.new("RGBA", (width, height), (255, 255, 255, 255))
                img = Image.alpha_composite(bg, img)
            if width > 576:
                img = img.resize((576, height * 576 // width), Image.LANCZOS)
                width, height = img.size

            if img.mode == "RGB" or img.mode == "RGBA":
                # convert to luma with BT.709
                new_img = Image.new("L", img.size)
                img_data = img.getdata()
                new_img.putdata([round((((0.2126 * pixel[0] + 0.7152 * pixel[1] + 0.0722 * pixel[2]) / 255) ** (1 / 2.2)) ** 1.5 * 255) for pixel in img_data])
                img = new_img
            elif img.mode not in ("1", "L"):
                # convert to grayscale with Pillow directly
                img = img.convert("L")
            if img.mode == "L":
                new_img = Image.new("1", img.size)
                img_data = list(img.getdata())
                img_data = [img_data[i * width:(i + 1) * width] for i in range(height)]
                # completely non-optimized snake sierra-3
                for y in range(height):
                    if y % 2 == 0:
                        for x in range(width):
                            old_pixel = img_data[y][x]
                            new_pixel = 0 if old_pixel < 128 else 255
                            error = old_pixel - new_pixel
                            new_img.putpixel((x, y), 1 if new_pixel < 128 else 0)
                            if x + 1 < width:
                                img_data[y][x + 1] += error * 5 / 32
                            if x + 2 < width:
                                img_data[y][x + 2] += error * 3 / 32
                            if y + 1 < height:
                                if x - 2 >= 0:
                                    img_data[y + 1][x - 2] += error * 2 / 32
                                if x - 1 >= 0:
                                    img_data[y + 1][x - 1] += error * 4 / 32
                                img_data[y + 1][x] += error * 5 / 32
                                if x + 1 < width:
                                    img_data[y + 1][x + 1] += error * 4 / 32
                                if x + 2 < width:
                                    img_data[y + 1][x + 2] += error * 2 / 32
                                if y + 2 < height:
                                    if x - 1 >= 0:
                                        img_data[y + 2][x - 1] += error * 2 / 32
                                    img_data[y + 2][x] += error * 3 / 32
                                    if x + 1 < width:
                                        img_data[y + 2][x + 1] += error * 2 / 32
                    else:
                        for x in range(width - 1, -1, -1):
                            old_pixel = img_data[y][x]
                            new_pixel = 0 if old_pixel < 128 else 255
                            error = old_pixel - new_pixel
                            new_img.putpixel((x, y), 1 if new_pixel < 128 else 0)
                            if x - 1 >= 0:
                                img_data[y][x - 1] += error * 5 / 32
                            if x - 2 >= 0:
                                img_data[y][x - 2] += error * 3 / 32
                            if y + 1 < height:
                                if x + 2 < width:
                                    img_data[y + 1][x + 2] += error * 2 / 32
                                if x + 1 < width:
                                    img_data[y + 1][x + 1] += error * 4 / 32
                                img_data[y + 1][x] += error * 5 / 32
                                if x - 1 >= 0:
                                    img_data[y + 1][x - 1] += error * 4 / 32
                                if x - 2 >= 0:
                                    img_data[y + 1][x - 2] += error * 2 / 32
                                if y + 2 < height:
                                    if x + 1 < width:
                                        img_data[y + 2][x + 1] += error * 2 / 32
                                    img_data[y + 2][x] += error * 3 / 32
                                    if x - 1 >= 0:
                                        img_data[y + 2][x - 1] += error * 2 / 32
                img = new_img
            if width % 8 != 0:
                padded = Image.new("1", (width + 8 - width % 8, height), 255)
                padded.paste(img, (0, 0))
                img = padded
                width, height = img.size
            if alignment == Alignment.Center:
                img = ImageOps.expand(img, (288 - width // 2, 0, 288 - width // 2, 0))
                width, height = img.size
            elif alignment == Alignment.Right:
                img = ImageOps.expand(img, (0, 0, 576 - width, 0))
                width, height = img.size
            data = img.tobytes()
            await self.write_raw(b"\x1b\x1dS\x01" + pack("<HH", width // 8, height) + b"\x00" + data)

    # 2.3.18 Initialization

    async def initialize(self):
        await self.write_raw(b"\x1b@")

    # 2.3.21 Print settings

    async def set_print_speed(self, speed: PrintSpeed):
        command = b"\x1b\x1er"
        if self.model in (Model.SM_L200, Model.SM_L300, Model.mC_Print2):
            raise ValueError("model doesn't support this command")
        if self.model in (Model.mC_Print3_G1, Model.TSP100, Model.mC_Label3, Model.mC_Print3_G2):
            # Type 1
            if speed == PrintSpeed.Fast:
                command += b"\x00"
            elif speed == PrintSpeed.Normal:
                command += b"\x01"
            elif speed == PrintSpeed.Slow:
                command += b"\x02"
            else:
                raise ValueError("invalid speed")
        elif self.model == Model.mPOP:
            # Type 2
            if speed == PrintSpeed.Fast:
                command += b"\x00"
            elif speed == PrintSpeed.Slow:
                command += b"\x02"
            else:
                raise ValueError("invalid speed")
        elif self.model == Model.SM_S_T:
            # Type 3
            if speed == PrintSpeed.Fast:
                command += b"\x02"
            elif speed == PrintSpeed.Normal:
                command += b"\x01"
            elif speed == PrintSpeed.Slow:
                command += b"\x00"
            else:
                raise ValueError("invalid speed")
        else:
            raise ValueError("model not supported")
        await self.write_raw(command)

    async def set_print_density(self, density: PrintDensity):
        command = b"\x1b\x1ed"
        if self.model in (Model.mPOP, Model.TSP100, Model.mC_Label3) \
            or self.model == Model.mC_Print3_G1 and self.version <= "2.4":
            # Type 1
            table = {
                PrintDensity.Plus3: "0",
                PrintDensity.Plus2: "1",
                PrintDensity.Plus1: "2",
                PrintDensity.Standard: "3",
                PrintDensity.Minus1: "4",
                PrintDensity.Minus2: "5",
                PrintDensity.Minus3: "6",
            }
        elif self.model == Model.mC_Print2:
            # Type 2
            table = {
                PrintDensity.Plus3: "0",
                PrintDensity.Plus2: "1",
                PrintDensity.Plus1: "2",
                PrintDensity.Standard: "3",
            }
        elif self.model in (Model.SM_L200, Model.SM_L300):
            # Type 3
            table = {
                PrintDensity.Medium: "0",
                PrintDensity.Low: "1",
                PrintDensity.High: "2",
                PrintDensity.Special: "3",
            }
        elif self.model == Model.SM_S_T:
            # Type 4
            table = {
                PrintDensity.Medium: "0",
                PrintDensity.Low: "1",
                PrintDensity.High: "2",
            }
        elif self.model == Model.mC_Print3_G1 and self.version >= "3.0" \
            or self.model == Model.mC_Print3_G2:
            # Type 5
            table = {
                PrintDensity.Plus3: "0",
                PrintDensity.Plus2: "1",
                PrintDensity.Plus1: "2",
                PrintDensity.Standard: "3",
                PrintDensity.Minus1: "4",
                PrintDensity.Minus2: "5",
                PrintDensity.Minus3: "6",
                PrintDensity.Plus4: "7",
            }
        else:
            raise ValueError("model not supported")
        if density not in table:
            raise ValueError("invalid density for model")
        command += bytes([ord(table[density])])
        await self.write_raw(command)

    # 2.3.23 UTF related commands

    async def set_utf8_font(self, font: UTF8Font):
        if self.model in (Model.mPOP, Model.SM_L200, Model.SM_L300, Model.SM_S_T):
            raise ValueError("model doesn't support this command")
        if font == UTF8Font.Japanese:
            font_order = [1, 2, 3, 4]
        elif font == UTF8Font.SimplifiedChinese:
            font_order = [2, 3, 1, 4]
        elif font == UTF8Font.TraditionalChinese:
            font_order = [3, 2, 1, 4]
        elif font == UTF8Font.Korean:
            font_order = [4, 1, 2, 3]
        else:
            raise ValueError("invalid font")
        await self.write_raw(b"\x1b\x1d)U\x05\x00A" + bytes(font_order))

    # 2.3.26 External device control

    async def trigger_external_device_1(self):
        if self.model in (Model.SM_L200, Model.SM_L300, Model.SM_S_T):
            raise ValueError("model doesn't support this command")
        await self.write_raw(b"\x07")

    async def trigger_external_device_2(self):
        if self.model in (Model.SM_L200, Model.SM_L300, Model.SM_S_T) \
            or self.model == Model.mPOP and self.version < "2.0":
            raise ValueError("model doesn't support this command")
        await self.write_raw(b"\x1a")


class StarPRNTEthernet(StarPRNT):

    def __init__(self, interface_type: StarPRNT.InterfaceType, address: IPv4Address,
                 reader: StreamReader, writer: StreamWriter, reset: bool = False, model: Model = Model.Unknown):
        super().__init__(interface_type, model)
        self.address = address
        self._reader = reader
        self._writer = writer
        self._reset = reset
        self._read_task = asyncio.create_task(self._read_worker())
        self.status = ASB()

    async def _read_worker(self):
        if self._reset:
            await self.write_raw(b"\x1b@")
        await self.write_raw(b"\x1b#*\n\0")
        await self.write_raw(b"\x1b\x1d)I\x01\x001")
        while True:
            try:
                asb = await self._reader.read(524288)
                self.status, extra = parse_asb(asb)
                if extra is not None:
                    print(extra)
                    if "printer_version" in extra:
                        self.version = extra["printer_version"].split("Ver")[1]
            except:
                await self.close()
                raise

    @classmethod
    async def connect(cls, address: str, model: Model = Model.Unknown, reset = False):
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

        res = cls(cls.InterfaceType.Ethernet, address, reader, writer, reset, model)
        await asyncio.sleep(0.5)
        return res

    async def write_raw(self, data: bytes):
        if self._writer.is_closing():
            raise ConnectionError("connection closed")
        self._writer.write(data)
        await self._writer.drain()

    async def close(self):
        if not self._writer.is_closing():
            self._writer.close()
            await self._writer.wait_closed()