import json
from pathlib import Path


service_account_file = Path("/Users/indapa/HagePTA/ServiceAccounts/hage-pta-fab6351c88f5.json")

with open(service_account_file) as f:
    creds = json.load(f)

# Step 2: Escape newline characters in private_key
creds["private_key"] = creds["private_key"].replace("\n", "\\n")

# Step 3: Dump the JSON as a single line
escaped_json = json.dumps(creds)

# Step 4: Format it as TOML
secrets_toml = f'GOOGLE_CREDS = """{escaped_json}"""'

# Step 5: Write to .streamlit/secrets.toml

with open(".streamlit/secrets.toml", "w") as f:
    f.write(secrets_toml)

print("✅ .streamlit/secrets.toml written successfully.")
