# Collect data from the Bungie API.
import json
import os
import pickle
from os.path import dirname, join, normpath, realpath
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv


# TODO pull out into common utils
def get_headers():
    """Get X-API-Key and place in header for all requests"""
    dotenv_path = os.path.normpath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "../..", ".env")
    )
    load_dotenv(dotenv_path)

    api_key = os.environ["BUNGIE_NET_API_KEY"]
    headers = {"X-API-Key": api_key}
    return headers


def load_manifest():
    # TODO: check and abort if no manifest found
    DATA_DIR = normpath(join(dirname(realpath(__file__)), "../data"))
    manifest_path = join(DATA_DIR, "manifest.pickle")

    with open(manifest_path, "rb") as data:
        return pickle.load(data)


INDEX = load_manifest()
HEADERS = get_headers()
API_URL = "https://www.bungie.net/platform/"
GET_ACTIVITY_HISTORY = "Destiny2/{membershipType}/Account/{destinyMembershipId}/Character/{characterId}/Stats/Activities/"
GET_POST_GAME_CARNAGE_REPORT = "Destiny2/Stats/PostGameCarnageReport/{activityId}/"

# r = requests.get(path, headers=HEADERS)
# print(json.dumps(r.json(), indent=4))  # Example of prettyprint


def get_activity_name(activity):
    activity_hash = activity["activityDetails"]["directorActivityHash"]

    # Localize using manifest
    return INDEX["DestinyActivityDefinition"][activity_hash]["displayProperties"][
        "name"
    ]


def get_activity_period(activity):
    # TODO may want to parse datetime string or use for certain things
    return activity["period"]


def get_activity_reference_id(activity):
    return activity["activityDetails"]["referenceId"]


def get_activity_instance_id(activity):
    # Used for looking up post-game carnage reports (PGCRs)
    return activity["activityDetails"]["instanceId"]


def get_activity_values(activity):
    return activity["values"]


def get_value_kills(values):
    return values["kills"]["basic"]["value"]


def get_value_deaths(values):
    return values["deaths"]["basic"]["value"]


def get_value_assists(values):
    # NOTE: takes in values object from activity summary
    return values["assists"]["basic"]["value"]


def get_value_score(values):
    return values["score"]["basic"]["value"]


def get_value_completed(values):
    # 1 if completed, NOTE haven't seen not completed but assuming it's 0
    return values["completed"]["basic"]["value"]


def get_value_opponents_defeated(values):
    # TODO what is the difference between this and kills?
    return values["opponentsDefeated"]["basic"]["value"]


def get_value_activity_duration(values, in_units_of="seconds"):
    # Returns activity duration in seconds
    # TODO allow translation to other units if need be
    return values["activityDurationSeconds"]["basic"]["value"]


def get_value_standing(values):
    # The API marks 1 as defeat, 0 as victory; we invert that
    return 1 - values["standing"]["basic"]["value"]


def get_activity_history(character_data):
    path = urljoin(API_URL, GET_ACTIVITY_HISTORY.format(**character_data))
    r = requests.get(path, headers=HEADERS)

    activities = r.json()["Response"]["activities"]
    print(f"{len(activities)} activities found")

    history = []

    for activity in activities:
        period = get_activity_period(activity)
        details = activity["activityDetails"]
        activity_name = get_activity_name(activity)
        values = get_activity_values(activity)

        # TODO: filter and bucket activities. get more. use recent activities as features per player
        # print(f"{period}, {activity_name}, victory?: {get_value_standing(values)}, kills: {get_value_kills(values)}, oppDef: {get_value_opponents_defeated(values)}")
        print(f"{period}, {activity_name}")
        history.append(
            {
                "period": period,
                "activity_name": activity_name,
                "details": details,
                "values": values,
            }
        )

    return history


if __name__ == "__main__":
    # TODO: crawl over characters and collect relevant data
    character_data = {
        "membershipType": "3",
        "destinyMembershipId": "4611686018497112157",
        "characterId": "2305843009574374200",
    }

    history = get_activity_history(character_data)
