# SolarPredictionHA
Home Assistant AppDaemon script to calculate maximum expected solar at a given location

Calculates the maximum expected solar power generated at a given latitude and longditude for any time of day (day, month, minute).
This is configured through AppDaemon to automatically update in Home Assistance every 60secs (configurable in the script).

Requires parameters to be set to your installation

        latitude     Add solar panel latitude in degrees 
        longitude    Add solar panel longditude in degrees
        inclination  Add inclination of panel in degrees from horizontal
        efficiency   Efficiency of panels (between 0 and 1)
        area         Panel area
        direction    Solar panel direction in degrees from south e.g. North = 180, East = 90, South = 0, West = 270

Function _solar_power calculates the expected solar generation for a given panel

In this implementation two panel groups are calculated and returned to home assistant as entities 

        solar_1
        solar_2
        solar_total
