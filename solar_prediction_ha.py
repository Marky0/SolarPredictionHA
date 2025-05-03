import appdaemon.plugins.hass.hassapi as hass
import numpy as np
import datetime

class SolarApp(hass.Hass):
    """
    AppDaemon app to calculate maximum expected solar power
    In this implementation two panel groups are calculated and 
    stored in Home Assistant entities `sensor.solar_1` and `sensor.solar_2`
    Can be easily configured for any number of panels

    Runs every 60 seconds
    """

    def initialize(self):
        # Schedule the update every 60 seconds (1 minutes), starting now
        self.run_every(self.update_solar, self.datetime(), 60)
        self.log(f"My app namespace is: {self.namespace}")

    def update_solar(self, kwargs):
        # Get current local time with timezone info
        now = datetime.datetime.now().astimezone()
        day = now.timetuple().tm_yday
        # timezone offset in hours
        tz_offset = int(now.utcoffset().total_seconds() // 3600)
        hour = now.hour
        minute = now.minute

        # Site-specific configuration
        latitude = XXXX				#Add solar panel latitude in degrees
        longitude = XXXX			#Add solar panel longditude in degrees
        inclination = 60			#Add inclination of panel in degrees from horizontal
        efficiency = 0.2			#Efficiency of panels 20%
        
        area_1 = 1.769 * 1.052 * 8	#Add area of panels
        area_2 = area_1
        direction_1 = 80			#Solar panel direction - degrees from south e.g. North = 180, East = 90, South = 0, West = 270
        direction_2 = 260

        # Calculate solar power
        solar_1 = self._solar_power(day, hour, minute, tz_offset,
                                        latitude, longitude,
                                        inclination, direction_1,
                                        area_1, efficiency)
        solar_2 = self._solar_power(day, hour, minute, tz_offset,
                                        latitude, longitude,
                                        inclination, direction_2,
                                        area_2, efficiency)

        # Update Home Assistant entities
        self.set_state("sensor.solar_1", state=solar_1, attributes={"friendly_name": "Solar Panel 1", "unit_of_measurement": "W"}, namespace="default")
        self.set_state("sensor.solar_2", state=solar_2, attributes={"friendly_name": "Solar Panel 2", "unit_of_measurement": "W"}, namespace="default")
        # Add additional panels if neccessary with additional calls.
        self.set_state("sensor.solar_total", state=solar_1 + solar_1, attributes={"friendly_name": "Solar Total", "unit_of_measurement": "W"}, namespace="default")

    def _deg2rad(self, deg):
        return deg * np.pi / 180

    def _solar_power(self, day, hour, minute, timezone, latitude,
                     longitude, inclination, direction, area, efficiency):
        
        lat_rad = self._deg2rad(latitude)

        # Insolation parameters from https://pubs.nmsu.edu/_circulars/CR674/CR674.xlsm
        solar_insolation = 1160 + 75 * np.sin(self._deg2rad((360/365) * (day - 275)))
        optical_depth = 0.174 + 0.035 * np.sin(self._deg2rad(360/365 * (day - 100)))
        sky_diffuse = 0.095 + 0.04 * np.sin(self._deg2rad(360/365 * (day - 100)))

        # Solar geometry from https://gml.noaa.gov/grad/solcalc/solareqns.PDF
        gamma = 2 * np.pi / 365 * (day - 1 + (hour - 12) / 24)
        eqtime = 229.18 * (
            0.000075 + 0.001868 * np.cos(gamma)
            - 0.032077 * np.sin(gamma)
            - 0.014615 * np.cos(2 * gamma)
            - 0.040849 * np.sin(2 * gamma)
        )
        decl = (
            0.006918
            - 0.399912 * np.cos(gamma)
            + 0.070257 * np.sin(gamma)
            - 0.006758 * np.cos(2 * gamma)
            + 0.000907 * np.sin(2 * gamma)
            - 0.002697 * np.cos(3 * gamma)
            + 0.00148 * np.sin(3 * gamma)
        )
        time_offset = eqtime + 4 * longitude - 60 * timezone

        tst = 60 * hour + minute + time_offset
        ha_rad = self._deg2rad((tst / 4) - 180)

        zenith = np.arccos(
            np.sin(lat_rad) * np.sin(decl)
            + np.cos(lat_rad) * np.cos(decl) * np.cos(ha_rad)
        )
        elevation = np.pi/2 - zenith

        # Solar azimuth from https://en.wikipedia.org/wiki/Solar_azimuth_angle
        azimuth = np.arccos(
            (np.sin(decl) - np.cos(zenith) * np.sin(lat_rad))
            / (np.sin(zenith) * np.cos(lat_rad))
        )
        if ha_rad > 0:
            azimuth = 2 * np.pi - azimuth

        # Irradiance
        air_mass = abs(1 / np.sin(elevation))
        irradiance = solar_insolation * np.exp(-optical_depth * air_mass)

        # Incidence factor
        dot_inc = (
            np.sin(azimuth) * np.cos(elevation) * np.sin(self._deg2rad(direction)) * np.cos(self._deg2rad(inclination))
            + np.cos(azimuth) * np.cos(elevation) * np.cos(self._deg2rad(direction)) * np.cos(self._deg2rad(inclination))
            + np.sin(elevation) * np.sin(self._deg2rad(inclination))
        )

        if elevation < 0 or dot_inc < 0:
            return 0

        return irradiance * dot_inc * (1 + sky_diffuse) * area * efficiency

