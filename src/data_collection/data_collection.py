# Collect data from the Bungie API.
import json
import logging
import os
import pickle
import time
from os.path import dirname, join, normpath, realpath
from urllib.parse import urljoin

import pandas as pd
import requests
from dotenv import load_dotenv

from threadpool import ThreadPool

logging.basicConfig(level=logging.INFO)
logging.getLogger("threadpool").setLevel(logging.DEBUG)
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

# Constants
STARTING_ACTIVITY_ID = 8400554258
# ENDING_ACTIVITY_ID = STARTING_ACTIVITY_ID + int(100)
# ENDING_ACTIVITY_ID = STARTING_ACTIVITY_ID + int(1000)  # 1K
# ENDING_ACTIVITY_ID = STARTING_ACTIVITY_ID + int(10000)  # 10K
ENDING_ACTIVITY_ID = STARTING_ACTIVITY_ID + int(100000)  # 100K
# ENDING_ACTIVITY_ID = STARTING_ACTIVITY_ID + int(1e6)  # 1M

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
API_URL = "https://www.bungie.net/Platform/"
GET_ACTIVITY_HISTORY = "Destiny2/{membershipType}/Account/{destinyMembershipId}/Character/{characterId}/Stats/Activities/"
GET_POST_GAME_CARNAGE_REPORT = "Destiny2/Stats/PostGameCarnageReport/{activityId}/"
# TODO: get character stats
# TODO: get weapon stats per weapon

# r = requests.get(path, headers=HEADERS)
# print(json.dumps(r.json(), indent=4))  # Example of prettyprint


def get_director_activity_name(activity):
    # Uses the directorActivityHash of the
    # HistoricalStats.DestinyHistoricalStatsActivity (i.e., the entries of the
    # activity history)
    activity_hash = activity["activityDetails"]["directorActivityHash"]

    # Localize using manifest
    return INDEX["DestinyActivityDefinition"][activity_hash]["displayProperties"][
        "name"
    ]


def get_activity_period(activity):
    # TODO may want to parse datetime string or use for certain things
    return activity["period"]


def get_activity_reference_id(activity):
    # NOTE more properly thought of as the activityHash. Maps to
    # DestinyActivityDefinition in manifest.
    return activity["activityDetails"]["referenceId"]


def get_activity_instance_id(activity):
    # Used for looking up post-game carnage reports (PGCRs)
    return activity["activityDetails"]["instanceId"]


def get_activity_values(activity):
    return activity["values"]


def get_value_kills(values):
    if "kills" in values:
        return values["kills"]["basic"]["value"]
    else:
        return None


def get_value_deaths(values):
    if "deaths" in values:
        return values["deaths"]["basic"]["value"]
    else:
        return None


def get_value_assists(values):
    # NOTE: takes in values object from activity summary
    if "assists" in values:
        return values["assists"]["basic"]["value"]
    else:
        return None


def get_value_score(values):
    if "score" in values:
        return values["score"]["basic"]["value"]
    else:
        return None


def get_value_completed(values):
    # 1 if completed, NOTE haven't seen not completed but assuming it's 0
    if "completed" in values:
        return values["completed"]["basic"]["value"]
    else:
        return None


def get_value_opponents_defeated(values):
    # TODO what is the difference between this and kills?
    if "opponentsDefeated" in values:
        return values["opponentsDefeated"]["basic"]["value"]
    else:
        return None


def get_value_combat_efficiency(values):
    if "efficiency" in values:
        return values["efficiency"]["basic"]["value"]
    else:
        return None


def get_value_kdr(values):
    if "killsDeathsRatio" in values:
        return values["killsDeathsRatio"]["basic"]["value"]
    else:
        return None


def get_value_kda(values):
    if "killsDeathsAssists" in values:
        return values["killsDeathsAssists"]["basic"]["value"]
    else:
        return None


def get_value_activity_duration(values, in_units_of="seconds"):
    # Returns activity duration in seconds
    # TODO allow translation to other units if need be
    if "activityDurationSeconds" in values:
        return values["activityDurationSeconds"]["basic"]["value"]
    else:
        return None


def get_value_team(values):
    if "team" in values:
        return values["team"]["basic"]["value"]
    else:
        return None


def get_value_standing(values):
    # The API marks 1 as defeat, 0 as victory; we invert that
    if "standing" in values:
        return 1 - values["standing"]["basic"]["value"]
    else: 
        return None


def get_value_team_score(values):
    if "teamScore" in values:
        return values["teamScore"]["basic"]["value"]
    else:
        return None


def get_activity_history(character_data, params=None):
    path = urljoin(API_URL, GET_ACTIVITY_HISTORY.format(**character_data))
    r = requests.get(path, headers=HEADERS, params=params)

    activities = r.json()["Response"]["activities"]
    print(f"{len(activities)} activities found")

    history = []

    for activity in activities:
        period = get_activity_period(activity)
        details = activity["activityDetails"]
        activity_name = get_director_activity_name(activity)
        values = get_activity_values(activity)
        id = get_activity_instance_id(activity)

        # TODO: filter and bucket activities. get more. use recent activities as features per player
        # print(f"{period}, {activity_name}, victory?: {get_value_standing(values)}, kills: {get_value_kills(values)}, oppDef: {get_value_opponents_defeated(values)}")
        print(f"{period}, {activity_name}, {id}")
        history.append(
            {
                "period": period,
                "activity_name": activity_name,
                "details": details,
                "values": values,
            }
        )

    return history


def scrape_pgcr(instance_id):
    """Given an instance id, make a request to Platform API, scrape data from
    the JSON response, and assembler and return a dict mapping column names to
    values.

    Args:
      instance_id (int): The ID of the activity instance. Activities are 
        numbered in roughly increasing order and uniquely identify an activity.
    """
    path = urljoin(
        API_URL, GET_POST_GAME_CARNAGE_REPORT.format(**{"activityId": instance_id})
    )
    try:
        r = requests.get(path, headers=HEADERS, timeout=1)
    except requests.ConnectionError:
        # A connection error occurred. Probably some network issue.
        return None
    except requests.Timeout:
        # A timeout error occurred
        return None

    try:
        pgcr = r.json()["Response"]
    except json.JSONDecodeError:
        # This can mean we've gone over our request rate limit, or something else
        print(f"Error: got status {r.status_code}")
        # print(f"Error {r['ErrorStatus']} ({r['ErrorCode']}): {r['Message']}")
        # print(f"Throttle seconds {r['ThrottleSeconds']}")
        # raise RuntimeError

        # Just return silently
        return None

    period = get_activity_period(pgcr)
    director_activity_name = get_director_activity_name(pgcr)

    # TODO: different games have different values; our implementation should be robust to this
    # if director_activity_name != "Gambit":
    #     return {
    #         "instance_id": instance_id,
    #         "period": period,
    #         "director_activity_name": director_activity_name,
    #     }

    entries = pgcr["entries"]
    # print(f"Activity {instance_id} has {len(entries)} entries...")

    player_entries = {}
    for i, entry in enumerate(entries):
        # TODO handle extended and other props
        characterId = entry["characterId"]
        player_entries[f"player{i + 1}_char_id"] = characterId

        # Values (kills, assists, etc.)
        if "values" not in entry: 
            continue
        
        values = entry["values"]
        player_entries[f"player{i + 1}_kills"] = get_value_kills(values)
        player_entries[f"player{i + 1}_deaths"] = get_value_deaths(values)
        player_entries[f"player{i + 1}_assists"] = get_value_assists(values)
        player_entries[f"player{i + 1}_kdr"] = get_value_kdr(values)
        player_entries[f"player{i + 1}_kda"] = get_value_kda(values)
        player_entries[f"player{i + 1}_efficiency"] = get_value_combat_efficiency(
            values
        )
        player_entries[f"player{i + 1}_score"] = get_value_score(values)

        player_entries[f"player{i + 1}_standing"] = get_value_standing(values)
        player_entries[f"player{i + 1}_team_score"] = get_value_team_score(values)
        player_entries[
            f"player{i + 1}_activity_duration"
        ] = get_value_activity_duration(values)

    # Return dict
    return {
        "instance_id": instance_id,
        "period": period,
        "director_activity_name": director_activity_name,
        **player_entries,
    }


def scrape_pgcrs(filter=None):
    data = []  # List of dicts

    for instance_id in range(STARTING_ACTIVITY_ID, ENDING_ACTIVITY_ID):
        entry = scrape_pgcr(instance_id)
        if filter is None or entry["director_activity_name"] == filter:
            data.append(entry)

    df = pd.DataFrame(data)
    df.to_csv("test.csv")


# TODO: filter only activities we want/attributes we want
def scrape_pgcrs_multithreaded(filter=None):
    data = []  # List of dicts
    t = ThreadPool()

    for instance_id in range(STARTING_ACTIVITY_ID, ENDING_ACTIVITY_ID):
        # Create a closure
        def make_func(id):
            def func():
                entry = scrape_pgcr(id)
                if entry == None:
                    return  # Error happened/malformed entry
                if filter is None or entry["director_activity_name"] == filter:
                    data.append(entry)

            return func

        # Needed to create a new scope around the current value of instance_id
        t.schedule(make_func(instance_id))

    t.shutdown()

    df = pd.DataFrame(data)
    df.to_csv("test.csv")


if __name__ == "__main__":
    # TODO: crawl over characters and collect relevant data
    character_data = {
        "membershipType": "3",
        "destinyMembershipId": "4611686018497112157",
        "characterId": "2305843009574374200",
    }

    # Example activity history call with params
    params = {"count": 10}
    history = get_activity_history(character_data, params=params)

    # Add rudimentary timing...
    start_time = time.time()
    start_perf_ctr = time.perf_counter()

    # scrape_pgcrs()
    # scrape_pgcrs_multithreaded(filter="Gambit")
    # scrape_pgcrs_multithreaded(filter="Control")
    scrape_pgcrs_multithreaded()

    time_elapsed = time.time() - start_time
    perf_ctr_elapsed = time.perf_counter() - start_perf_ctr
    print(f"time: {time_elapsed}")
    print(f"perf time: {perf_ctr_elapsed}")
