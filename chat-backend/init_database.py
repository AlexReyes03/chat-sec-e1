import pymysql
from sqlalchemy import create_engine, text
from src.config.config import Config
import sys


def create_database():
    """
    Crea la base de datos si no existe
    """
    try:
        connection = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )

        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")

        print(f"[OK] Base de datos '{Config.DB_NAME}' creada o ya existe")

        cursor.close()
        connection.close()

        return True

    except Exception as e:
        print(f"[ERROR] No se pudo crear la base de datos: {str(e)}")
        return False


def create_tables():
    """
    Crea las tablas usando SQLAlchemy
    """
    try:
        from src.database.models import Base
        from src.database.connection import engine

        Base.metadata.create_all(bind=engine)

        print("[OK] Tablas creadas exitosamente")
        return True

    except Exception as e:
        print(f"[ERROR] No se pudieron crear las tablas: {str(e)}")
        return False


def verify_tables():
    """
    Verifica que las tablas se hayan creado correctamente
    """
    try:
        from src.database.connection import engine

        with engine.connect() as connection:
            result = connection.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]

            print(f"\n[OK] Tablas encontradas: {', '.join(tables)}")

            if 'usuarios' in tables:
                result = connection.execute(text("DESCRIBE usuarios"))
                print("\n[OK] Estructura de tabla 'usuarios':")
                for row in result:
                    print(f"  - {row[0]}: {row[1]}")

        return True

    except Exception as e:
        print(f"[ERROR] No se pudieron verificar las tablas: {str(e)}")
        return False


def main():
    print("=" * 70)
    print("INICIALIZACION DE BASE DE DATOS - CHATSEC v5.0")
    print("=" * 70)
    print(f"\nHost: {Config.DB_HOST}:{Config.DB_PORT}")
    print(f"Base de datos: {Config.DB_NAME}")
    print(f"Usuario: {Config.DB_USER}")
    print()

    print("[1/3] Creando base de datos...")
    if not create_database():
        sys.exit(1)

    print("\n[2/3] Creando tablas...")
    if not create_tables():
        sys.exit(1)

    print("\n[3/3] Verificando estructura...")
    if not verify_tables():
        sys.exit(1)

    print("\n" + "=" * 70)
    print("INICIALIZACION COMPLETADA EXITOSAMENTE")
    print("=" * 70)
    print("\nPuedes iniciar el servidor con: python start.py")
    print()


if __name__ == "__main__":
    main()
