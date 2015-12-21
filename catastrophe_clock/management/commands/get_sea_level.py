import datetime
import logging
import math
import numpy as np
import requests

from django.core.management.base import BaseCommand
from catastrophe_clock.models import Catastrophe

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Fetching sea level & updating Catastrophe model...")
        sea_level_increase_mm_year, intercept_mm = self.get_lin_fit(*self.get_raw_data())

        miami_elevation_mm = 1828  # in mm, according to wikipedia
        year_submerged_dec = (miami_elevation_mm - intercept_mm) / sea_level_increase_mm_year  # Decimal years
        logger.debug("decimal year submerged is " + repr(year_submerged_dec))

        year, year_rem = int(math.floor(year_submerged_dec)), year_submerged_dec % 1
        month, month_rem = int(year_rem * 12) % 12, year_rem * 12 % 1
        day = int(math.floor(month_rem * 30.5))
        logger.debug("year is " + repr(year))

        datetime_submerged = datetime.datetime(year=year, month=month, day=day)
        logger.debug("Miami will be submerged on: " + repr(datetime_submerged))

        # Alternate calculation
        years_from_now = miami_elevation_mm / sea_level_increase_mm_year
        alt_datetime_submerged = datetime.datetime.now() + datetime.timedelta(days=(365*years_from_now))
        logger.info("Alternate date for submersion is: " + repr(alt_datetime_submerged))

        miami_sinks, created = Catastrophe.objects.get_or_create(
            name="Miami sinks"
        )
        if created:
            logging.info("Creating new Catastrophe model...")
        miami_sinks.arrival_date = datetime_submerged
        miami_sinks.save()

    def get_raw_data(self):
        """
        Fetches the raw data from nasa's website.
        :return: A tuple of np.arrays, the year and observed deviation in mm that year, respectively
        """
        resp = requests.get(
            "http://climate.nasa.gov/system/internal_resources/details/original/121_Global_Sea_Level_Data_File.txt")

        header_started = False
        header_finished = False
        dates_year, deviations_mm = np.array([]), np.array([])
        for line in resp.content.splitlines():
            if not header_started:
                if b"HDR" not in line:
                    logger.debug(b"before header started" + line)
                    continue
                else:
                    header_started = True
                    continue

            if not header_finished:
                if b"HDR" not in line:
                    header_finished = True
                    continue
                else:
                    logger.debug(b"after header started " + line)
                    continue

            try:
                date, dev = line.split()[2], line.split()[11]
                dates_year = np.append(dates_year, date)
                deviations_mm = np.append(deviations_mm, dev)
            except IndexError:
                logger.debug(b"couldn't parse" + line)

        assert deviations_mm.shape == dates_year.shape
        assert len(deviations_mm) == len(dates_year)
        return dates_year, deviations_mm

    def get_lin_fit(self, dates_year, deviations_mm):
        """
        Calculates the rate of increase of sea level by linear regressions
        :param dates_year: np.array of dates, in years
        :param deviations_mm: np.array of sea level deviations, in mm
        :return: a tuple, the rate of increase in mm/year, and the intercept in mm
        """
        A = np.vstack([dates_year, np.ones(len(dates_year))]).T
        rate_mm_per_year, intercept_mm = np.linalg.lstsq(A, deviations_mm)[0]
        return rate_mm_per_year, intercept_mm
