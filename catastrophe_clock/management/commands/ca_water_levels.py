import collections
import datetime
import logging
import numpy as np
import requests
import multiprocessing

from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

Station = collections.namedtuple('Station', ['station_id', 'storages', 'station_name'])
Storage = collections.namedtuple('Storage', ['date', 'level_af'])


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Gets the historical storage levels (in acre-feet) for each reservoir in CA, then estimates when CA will use up
        all its water.

        Aggregates total storage for across all reservoirs, then estimates the rate using linear regression, and
        finally extrapolates when the total storage will reach zero.
        """
        no_storage_stations = get_stations()
        with multiprocessing.Pool(processes=int(len(no_storage_stations)/2)) as pool:
            stations = pool.map(get_storage, no_storage_stations)

        stations = filter(lambda x: x is not None, stations)
        meta_station = Station("META", [], "META")
        for station in stations:
            for storage in station.storages:
                try:
                    matches = list([s for s in meta_station.storages if s.date == storage.date])
                    old_val = matches[0]
                    assert len(matches) == 1
                    ind = meta_station.storages.index(old_val)
                    meta_station.storages[ind] = Storage(storage.date, old_val.level_af + storage.level_af)
                except IndexError:
                    meta_station.storages.append(Storage(storage.date, storage.level_af))

        zero_date = get_zero_date(meta_station)
        logger.info("Based on current rates the reservoirs will dry up on: {}" .format(zero_date))

        from catastrophe_clock.models import Catastrophe  # import here to avoid error loading django w/ multiprocessing
        catastrophe, created = Catastrophe.objects.get_or_create(
            name="California dries up"
        )
        catastrophe.arrival_date = datetime.datetime(zero_date.year, zero_date.month, zero_date.day)
        catastrophe.save()


def get_stations() -> [Station]:
    """
    Gets a list of stations for which data is collected.
    The `storages` property must still be filled.
    :return: A list of Station objects.
    """
    # blacklist contains station_ids to exclude, since they appear to have constant levels or are too noisy
    blacklist = []
    resp = requests.get("http://cdec.water.ca.gov/misc/daily_res.html")
    soup = BeautifulSoup(resp.content, "html.parser")
    trs = soup.find_all("tr")
    stations = []
    for tr in trs:
        if tr.find("th") or len(tr.find_all("td")) == 1:
            continue
        station_name = tr.td.a.text
        station_id = tr.td.next_sibling.next_sibling.b.text
        if station_id.upper() not in blacklist:
            stations.append(Station(station_id, [], station_name))
    return stations


def real_get_storage(station: Station, start_date=datetime.date(2012, 1, 1)) -> Station:
    """
    Takes a Station object and populates the `storages` property. Returns a new Station.
    Returns data from 2012 to present.

    :param station: A list of Stations to populate
    :param start_date: When to start getting data from. A datetime.date object.
    :return: A new Station
    """
    end_date = datetime.date.today()
    query_addr = ("http://cdec.water.ca.gov/cgi-progs/getDailyCSV?station_id={station_id}"
                  "&dur_code=D&sensor_num=15&start_date={sd_year}/{sd_month}/{sd_day}"
                  "&end_date={ed_year}/{ed_month}/{ed_day}")
    resp = requests.get(query_addr.format(
        station_id=station.station_id,
        sd_year=start_date.year,
        sd_month=start_date.month,
        sd_day=start_date.day,
        ed_year=end_date.year,
        ed_month=end_date.month,
        ed_day=end_date.day
    ))
    new_station = Station(station_id=station.station_id, storages=_parse_raw_data(resp.text),
                          station_name=station.station_name)
    return new_station


def _parse_raw_data(raw_data):
    """
    CA's site has a weird format... :(
    We'll parse it here, burning the headers/footers and returning only storage levels

    :param raw_data: a string, of the type returned by the http://cdec.water.ca.gov/ endpoints.
    :return: A list Storage objects.
    """
    storages = []
    for line in raw_data.splitlines():
        if line.startswith("'"):
            continue
        words = line.split(",")
        year = int(words[2])
        month = int(words[3])
        for day, storage in enumerate(words[4:], 1):
            day = int(day)
            if storage != "m":  # that value indicates it's missing
                storages.append(Storage(
                    date=datetime.date(year, month, day),
                    level_af=int(storage)
                ))
    if len(storages) == 0:
        raise ValueError("Couldn't parse any useful data.")
    return storages


def get_storage(station: Station) -> Station:
    """
    Takes a Station and returns a new Station with its `storages` populated.
    Meant to play nicely with multiprocessing.Pool.map.
    :param stations: A Station to populate
    :return: A new Station
    """
    try:
        return real_get_storage(station)
    except ValueError as e:
        logger.error("Unable to get storage data for {sn} ({sid}).".format(sn=station.station_name,
                                                                           sid=station.station_id))
        logger.error(e)
        return None


def get_zero_date(station):
    """
    Perform a linear regression on the station's storages levels_af property, to determine when it will reach zero.

    :param station:
    :return:
    """
    dates_ord, levels_af = [s.date.toordinal() for s in station.storages], [s.level_af for s in station.storages]
    A = np.vstack([dates_ord, np.ones(len(dates_ord))]).T
    rate, intercept = np.linalg.lstsq(A, levels_af)[0]
    if rate > 0:
        raise ValueError("Rate must be negative.")
    zero_date_ord = int(-1*intercept / rate)
    return datetime.date.fromordinal(zero_date_ord)
