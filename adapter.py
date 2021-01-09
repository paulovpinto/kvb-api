# encoding: utf8

import requests
from bs4 import BeautifulSoup
from functools import wraps
from flask import request
import re
from cachelib import SimpleCache

cache = SimpleCache()

# URL templates fuer den Scraper
URL_TEMPLATES = {
    "station_details": "/haltestellen/overview/{station_id:d}/",
    "line_details": "/haltestellen/showline/{station_id:d}/{line_id:d}/",
    "schedule_table": "/haltestellen/aushang/{station_id:d}/",
    "schedule_pocket": "/haltestellen/miniplan/{station_id:d}/",
    "departures": "/qr/{station_id:d}/"
}

# Die brauchen wir bei jeder Anfrage
HEADERS = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.137 Safari/537.36"}


def cached(timeout=5 * 60, key='view/%s'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = key % request.path
            rv = cache.get(cache_key)
            if rv is not None:
                return rv
            rv = f(*args, **kwargs)
            cache.set(cache_key, rv, timeout=timeout)
            return rv
        return decorated_function
    return decorator


def get_stations():
    # Ruft Liste aller Stationen ab und gibt
    # Dict mit ID als Schlüssel und Name als Wert aus.
    result = None
    url = "https://www.kvb.koeln/haltestellen/overview/"
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, features="html.parser")
    mystations = []
    for a in soup.find_all("a"):
        # print(a, a.get("href"), a.text)
        href = a.get("href")
        if href is None:
            continue
        if "/haltestellen/overview/" in href:
            station_id = href.split("/")[3]
            result = {"station_id": station_id}
        if result is None:
            continue
        mystations.append({
            "id": int(result["station_id"]),
            "name": a.text
            })
    # sort by id
    mystations.sort(key=lambda k: k.get("id"))
    station_dict = {}
    for s in mystations:
        station_dict[s["id"]] = s["name"]
    return station_dict


# Liest Details zu einer Station.
def get_station_details(station_id):
    result = {}
    url = "https://www.kvb.koeln/haltestellen/overview/%d/" % station_id
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text)
    details = {
        "station_id": station_id,
        "name": stations[station_id],
        "line_ids": []
    }
    div = soup.find("ul", class_="info-list")
    for a in div.find_all("a"):
        href = a.get("href")
        if href is None:
            continue
        if "/haltestellen/showline/{id}/".format(id=station_id) in href:
            line = href.split("/")[4]
            result = {"line_ids": line}
        if result is None:
            continue
        details["line_ids"].append(result["line_ids"])
    return details


# Findet heraus, welche Stationen eine Linie anfährt
def get_line_details(station_id, line_id):
    result = {}
    url = "https://www.kvb.koeln/haltestellen/showline/%d/%d/" % (
        station_id, line_id)
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text)
    details = {
        "station_id": station_id,
        "line_id": line_id,
        "stations_forward": [],
        "stations_reverse": []
    }
    station_key = "stations_forward"
    count = 0
    for td in soup.find_all("td", class_=re.compile(".*station")):
        tdclass = td.get("class")[0]
        if tdclass == u'station-top':
            count = count + 1
            if count == 2:
                station_key = "stations_reverse"
        a = td.find("a")
        if a is None:
            continue
        href = a.get("href")
        if href is None:
            continue
        if "/haltestellen/showline/{id}/".format(id=station_id) in href:
            line = href.split("/")[4]
            result = {"station_id": line}
        if result is None:
            continue
        details[station_key].append(int(result["station_id"]))
    return details


# Aktuelle Abfahrten von einer Station laden
def get_departures(station_id):
    url = "https://www.kvb.koeln/qr/%d/" % station_id
    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text)
    tables = soup.find_all("table", class_="display")
    departures = []
    for row in tables[0].find_all("tr"):
        tds = row.find_all("td")
        (line_id, direction, time) = (tds[0].text, tds[1].text, tds[2].text)
        line_id = line_id.replace(u"\xa0", "")
        direction = direction.replace(u"\xa0", "")
        time = time.replace(u"\xa0", " ").strip().lower()
        try:
            line_id = int(line_id)
        except:
            pass
        print(line_id, direction, time)
        departures.append({
            "line_id": line_id,
            "direction": direction,
            "wait_time": time
        })
    return departures


stations = get_stations()
