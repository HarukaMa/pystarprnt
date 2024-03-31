#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio

from StarPRNT import StarPRNTEthernet, Model, PrintDensity


async def main():
    conn = await StarPRNTEthernet.connect("10.224.0.100", model=Model.mC_Print3_G1)
    print(conn.status)
    await conn.initialize()
    await conn.print_line("Heat up")
    await conn.raster_test()
    await asyncio.sleep(0.5)
    await conn.set_print_density(PrintDensity.Minus3)
    await conn.print_line("-3")
    await conn.raster_test()
    await asyncio.sleep(0.5)
    await conn.set_print_density(PrintDensity.Minus2)
    await conn.print_line("-2")
    await conn.raster_test()
    await asyncio.sleep(0.5)
    await conn.set_print_density(PrintDensity.Minus1)
    await conn.print_line("-1")
    await conn.raster_test()
    await asyncio.sleep(0.5)
    await conn.set_print_density(PrintDensity.Standard)
    await conn.print_line("Standard")
    await conn.raster_test()
    await asyncio.sleep(0.5)
    await conn.set_print_density(PrintDensity.Plus1)
    await conn.print_line("+1")
    await conn.raster_test()
    await asyncio.sleep(0.5)
    await conn.set_print_density(PrintDensity.Plus2)
    await conn.print_line("+2")
    await conn.raster_test()
    await asyncio.sleep(0.5)
    await conn.set_print_density(PrintDensity.Plus3)
    await conn.print_line("+3")
    await conn.raster_test()
    await asyncio.sleep(0.5)
    await conn.set_print_density(PrintDensity.Plus4)
    await conn.print_line("+4")
    await conn.raster_test()
    await asyncio.sleep(0.5)
    await conn.cut()
    # await conn.raster_test()
    # await conn.initialize()
    # await conn.cut()

if __name__ == '__main__':
    asyncio.run(main())