import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://openpg:openpgpwd@localhost:5432/template1')
    try:
        user_exists = await conn.fetchval("SELECT 1 FROM pg_roles WHERE rolname = 'mrgreen'")
        if not user_exists:
            await conn.execute("CREATE ROLE mrgreen WITH LOGIN PASSWORD 'mrgreen_dev_password' SUPERUSER CREATEDB")
            print("Role mrgreen created")
        else:
            await conn.execute("ALTER ROLE mrgreen WITH LOGIN PASSWORD 'mrgreen_dev_password' SUPERUSER CREATEDB")
            print("Role mrgreen updated")

        db_exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = 'mrgreen_db'")
        if not db_exists:
            await conn.execute("CREATE DATABASE mrgreen_db OWNER mrgreen")
            print("Database mrgreen_db created")
        else:
            print("Database mrgreen_db already exists")
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
