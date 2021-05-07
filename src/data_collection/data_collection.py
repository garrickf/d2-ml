# Collect data from the Bungie API.
import os

import requests
from dotenv import load_dotenv

dotenv_path = os.path.normpath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "../..", ".env")
)
load_dotenv(dotenv_path)

API_KEY = os.environ["BUNGIE_NET_API_KEY"]

HEADERS = {"X-API-Key": API_KEY}

# Get Gjallarhorn
r = requests.get(
    "https://www.bungie.net/platform/Destiny/Manifest/InventoryItem/1274330687/",
    headers=HEADERS,
)

inventoryItem = r.json()
print(inventoryItem["Response"]["data"]["inventoryItem"]["itemDescription"])
