import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://odoo:odoopwd@localhost:5432/template1')
    try:
        roles = await conn.fetch("SELECT rolname, rolsuper, rolcreaterole, rolcreatedb FROM pg_roles")
        for r in roles:
            print(dict(r))
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
