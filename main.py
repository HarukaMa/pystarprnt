#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at https://mozilla.org/MPL/2.0/.

import asyncio

from StarPRNT import StarPRNTEthernet

async def main():
    conn = await StarPRNTEthernet.connect("10.224.0.100")
    await asyncio.sleep(1)
    print(conn.status)

if __name__ == '__main__':
    asyncio.run(main())