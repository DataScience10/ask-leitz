from pathlib import Path
import tomllib
import json
import oracledb


# --------------------------------------------------
# Load configuration
# --------------------------------------------------

with open(Path(".streamlit") / "secrets.toml", "rb") as f:
    config = tomllib.load(f)

oracle = config["oracle"]
team_name = config["agent"]["team_name"]


def read_value(value):
    if value is None:
        return ""

    if hasattr(value, "read"):
        return value.read()

    return str(value)


# --------------------------------------------------
# Connect
# --------------------------------------------------

connection = oracledb.connect(
    user=oracle["user"],
    password=oracle["password"],
    dsn=oracle["dsn"],
    config_dir=oracle["wallet_dir"],
    wallet_location=oracle["wallet_dir"],
    wallet_password=oracle["wallet_password"],
)

cursor = connection.cursor()

print("Oracle connection successful")


# --------------------------------------------------
# Verify agent team
# --------------------------------------------------

cursor.execute(
    """
    SELECT
        agent_team_name,
        status
    FROM user_ai_agent_teams
    WHERE agent_team_name = :team_name
    """,
    {"team_name": team_name}
)

row = cursor.fetchone()

if not row:
    raise RuntimeError(
        f"Agent team '{team_name}' was not found."
    )

print("Agent team:", row[0])
print("Status:", row[1])


# --------------------------------------------------
# Create conversation
# --------------------------------------------------

cursor.execute(
    """
    SELECT DBMS_CLOUD_AI.CREATE_CONVERSATION()
    FROM dual
    """
)

conversation_id = read_value(cursor.fetchone()[0])

print("Conversation ID:", conversation_id)


# --------------------------------------------------
# Ask question
# --------------------------------------------------

question = (
    "Find carbide tools between 200 and 250 mm "
    "suitable for very clean hardwood furniture finishing."
)

params = json.dumps({
    "conversation_id": conversation_id
})


print("\nQUESTION")
print(question)

print("\nCalling Oracle AI Agent...")


# --------------------------------------------------
# Run team
# --------------------------------------------------

cursor.execute(
    """
    SELECT DBMS_CLOUD_AI_AGENT.RUN_TEAM(
        :team_name,
        :user_prompt,
        :params
    )
    FROM dual
    """,
    {
        "team_name": team_name,
        "user_prompt": question,
        "params": params
    }
)

result = cursor.fetchone()[0]
result = read_value(result)


print("\nAGENT RESPONSE")
print(result)


# --------------------------------------------------
# Close
# --------------------------------------------------

cursor.close()
connection.close()

print("\nAgent test completed successfully")