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
        Gets the historical storage levels (in acre-feet) for each reservoir in CA. Then estimates when all of them
        will reach zero, using linear regression.
        """
        stations = get_storages(get_stations())

        with multiprocessing.Pool(processes=4) as pool:
            zero_dates = pool.map(_worker, stations)

        zero_dates = list(filter(lambda x: x is not None, zero_dates))

        for zd, st in zero_dates:
            if zd > datetime.date.today():
                logger.info(st.station_name + " will dry out on " + repr(zd))
            else:
                logger.info(st.station_name + "(" + st.station_id + ") isn't drying out just yet: " + repr(zd))

        zero_dates = filter(lambda x: x[0] > datetime.date.today(), zero_dates)
        max_el = max(zero_dates, key=lambda x: x[0])
        logger.info("The last reservoir ({}) will dry out on: " .format(max_el[1].station_id) + repr(max_el))

        from catastrophe_clock.models import Catastrophe  # import here to avoid error loading django w/ multiprocessing
        Catastrophe.objects.get_or_create(
            name="California dries up",
            arrival_date=datetime.datetime(max_el[0].year, max_el[0].month, max_el[0].day)
        )


def _worker(station):
    """
    Used for our pool, but can't be a local object to the class, or something, because it must be pickleable.
    """
    try:
        return get_zero_date(station), station
    except ValueError as e:
        logger.error("Couldn't calculate a zero date for {sn} ({sid}).".format(sn=station.station_name,
                                                                               sid=station.station_id))
        logger.error(e)
        return None


def get_stations() -> [Station]:
    """
    Gets a list of stations for which data is collected.
    The `storages` property must still be filled.
    :return: A list of Station objects.
    """
    blacklist = ["own"]  # station_ids to exclude, for various reasons
    resp = requests.get("http://cdec.water.ca.gov/misc/daily_res.html")
    soup = BeautifulSoup(resp.content, "html.parser")
    trs = soup.find_all("tr")
    stations = []
    for tr in trs:
        if tr.find("th") or len(tr.find_all("td")) == 1:
            continue
        station_name = tr.td.a.text
        station_id = tr.td.next_sibling.next_sibling.b.text
        if station_id not in blacklist:
            stations.append(Station(station_id, [], station_name))
    return stations


def get_storage(station : Station, start_date=datetime.date(2012, 1, 1)) -> Station:
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


def get_storages(stations: [Station]) -> [Station]:
    """
    Takes a list of Stations and populates the `storages` property. Returns a new list
    :param stations: A list of Stations to populate
    :return: A new list of Stations
    """
    new_stations = []
    for station in stations:
        try:
            new_stations.append(get_storage(station))
        except ValueError as e:
            logger.error("Unable to get storage data for {sn} ({sid}).".format(sn=station.station_name,
                                                                               sid=station.station_id))
            logger.error(e)
    return new_stations


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
    zero_date = datetime.date.fromordinal(zero_date_ord)
    line = [rate*dates_ord[i] + intercept for i in range(0, len(dates_ord))]
    return zero_date
