import asyncio

from StarPRNT import StarPRNTEthernet

async def main():
    conn = await StarPRNTEthernet.connect("10.224.0.100")
    await asyncio.sleep(1)
    print(conn.status)

if __name__ == '__main__':
    asyncio.run(main())