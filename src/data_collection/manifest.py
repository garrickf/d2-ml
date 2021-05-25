# Fetch and save manifest for reference localization.
# Some code adapted from http://destinydevs.github.io/BungieNetPlatform/docs/Manifest
import json
import os
import sqlite3
import zipfile
from os.path import dirname, join, normpath, realpath
from urllib.parse import urljoin
import pickle

import requests
from dotenv import load_dotenv


def get_headers():
    """Get X-API-Key and place in header for all requests"""
    dotenv_path = os.path.normpath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "../..", ".env")
    )
    load_dotenv(dotenv_path)

    api_key = os.environ["BUNGIE_NET_API_KEY"]
    headers = {"X-API-Key": api_key}
    return headers


HEADERS = get_headers()
API_URL = "https://www.bungie.net/platform/"
CONTENT_URL = "http://www.bungie.net"
GET_MANIFEST = "Destiny2/Manifest/"
DATA_DIR = normpath(join(dirname(realpath(__file__)), "../data"))


def get_manifest():

    path = urljoin(API_URL, GET_MANIFEST)
    r = requests.get(path, headers=HEADERS)
    manifest = r.json()

    # mobileWorldContentPaths holds static definitions of objects in Destiny
    mani_url = urljoin(
        CONTENT_URL, manifest["Response"]["mobileWorldContentPaths"]["en"]
    )
    r = requests.get(mani_url)

    save_path = join(DATA_DIR, "manifest.zip")
    with open(save_path, "wb") as f:
        f.write(r.content)

    print("Downloaded zipped manifest")

    # Extract contents
    os.chdir(DATA_DIR)
    with zipfile.ZipFile(save_path) as zip:
        name = zip.namelist()
        zip.extractall()

    # TODO can check name and verify it using md5sum
    os.rename(name[0], "Manifest.content")

    print("Extracted manifest")


def get_tables(cursor):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    tables = [t[0] for t in tables]
    tables = sorted(tables)
    return tables


def build_index(tables):
    # XXX How does it find the db file when it's in another folder?
    os.chdir(DATA_DIR)
    index = {}

    with sqlite3.connect("Manifest.content") as db:
        print("Connected to database")
        cursor = db.cursor()

        for table_name in tables:
            print(f"Building index for table: {table_name}...")

            cursor.execute(f"SELECT json from {table_name};")
            items = cursor.fetchall()
            item_jsons = [json.loads(item[0]) for item in items]

            item_dict = {}

            for item in item_jsons:
                item_dict[item["hash"]] = item

            index[table_name] = item_dict

        cursor.close()

    # TODO pickle the data
    with open("manifest.pickle", "wb") as f:
        pickle.dump(index, f)
        print("Created pickle. Done!")


# What tables to process
tables = [
    "DestinyAchievementDefinition",
    "DestinyActivityDefinition",
    "DestinyActivityGraphDefinition",
    "DestinyActivityModeDefinition",
    "DestinyActivityModifierDefinition",
    "DestinyActivityTypeDefinition",
    "DestinyArtifactDefinition",
    "DestinyBondDefinition",
    "DestinyBreakerTypeDefinition",
    "DestinyChecklistDefinition",
    "DestinyClassDefinition",
    "DestinyCollectibleDefinition",
    "DestinyDamageTypeDefinition",
    "DestinyDestinationDefinition",
    # Table went away 5/12/21
    # "DestinyEnemyRaceDefinition",
    "DestinyEnergyTypeDefinition",
    "DestinyEquipmentSlotDefinition",
    "DestinyFactionDefinition",
    "DestinyGenderDefinition",
    # NOTE items in this hash table DO NOT have a hash code
    # "DestinyHistoricalStatsDefinition",
    "DestinyInventoryBucketDefinition",
    "DestinyInventoryItemDefinition",
    "DestinyItemCategoryDefinition",
    "DestinyItemTierTypeDefinition",
    "DestinyLocationDefinition",
    "DestinyLoreDefinition",
    "DestinyMaterialRequirementSetDefinition",
    "DestinyMedalTierDefinition",
    "DestinyMetricDefinition",
    "DestinyMilestoneDefinition",
    "DestinyObjectiveDefinition",
    "DestinyPlaceDefinition",
    "DestinyPlugSetDefinition",
    "DestinyPowerCapDefinition",
    "DestinyPresentationNodeDefinition",
    "DestinyProgressionDefinition",
    "DestinyProgressionLevelRequirementDefinition",
    "DestinyRaceDefinition",
    "DestinyRecordDefinition",
    "DestinyReportReasonCategoryDefinition",
    "DestinyRewardSourceDefinition",
    "DestinySackRewardItemListDefinition",
    "DestinySandboxPatternDefinition",
    "DestinySandboxPerkDefinition",
    "DestinySeasonDefinition",
    "DestinySeasonPassDefinition",
    "DestinySocketCategoryDefinition",
    "DestinySocketTypeDefinition",
    "DestinyStatDefinition",
    "DestinyStatGroupDefinition",
    "DestinyTalentGridDefinition",
    "DestinyTraitCategoryDefinition",
    "DestinyTraitDefinition",
    "DestinyUnlockDefinition",
    "DestinyVendorDefinition",
    "DestinyVendorGroupDefinition",
]


if __name__ == "__main__":
    # TODO: Don't download the manifest if it already has been downloaded
    print(f"Data directory: {DATA_DIR}")
    get_manifest()
    build_index(tables)
