from pathlib import Path
import tomllib
import oracledb


with open(Path(".streamlit") / "secrets.toml", "rb") as f:
    config = tomllib.load(f)


oracle = config["oracle"]


connection = oracledb.connect(
    user=oracle["user"],
    password=oracle["password"],
    dsn=oracle["dsn"],
    config_dir=oracle["wallet_dir"],
    wallet_location=oracle["wallet_dir"],
    wallet_password=oracle["wallet_password"],
)


cursor = connection.cursor()


cursor.execute("""
    SELECT COUNT(*)
    FROM LEITZ_TOOLS
""")

count = cursor.fetchone()[0]

print("Oracle connection successful")
print("Products:", count)


cursor.execute("""
    SELECT SYS_CONTEXT('USERENV', 'DB_NAME'),
           SYS_CONTEXT('USERENV', 'CURRENT_USER')
    FROM dual
""")

db_name, current_user = cursor.fetchone()

print("Database:", db_name)
print("Connected as:", current_user)


cursor.close()
connection.close()

print("Connection test completed successfully")