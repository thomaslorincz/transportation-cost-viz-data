import csv
import json
import random
import sys

import brotli
import rtree
from pyproj import Transformer
from shapely.errors import TopologicalError
from shapely.geometry import shape, Point

# Operating cost per vehicle KM travelled: 17.5 cents for operating and 5 cents
# for depreciation and marginal insurance
AUTO_OP_COST = 0.225

# Annual fixed cost of owning a single car
AUTO_FIXED_COST = 3750

# Annual pass by person type:
PERSON_TO_PASS_COST = {
    "YO": 0,       # Preschool
    "Elem": 560,   # Elementary
    "JHS": 560,    # Junior High School
    "SHS": 560,    # High School
    "PSE": 800,    # Post-Secondary
    "WFT": 1200,   # Worker Full-Time
    "WPT": 1200,   # Worker Part-Time
    "AO": 1200,    # Adult (Other)
    "SEN": 135,    # Senior
}

# Average transit fare (average is needed because it is unclear whether
# riders are using change, tickets, book of tickets, etc.)
AVG_TRANSIT_FARE = 3

# Annual operator's license cost
ANNUAL_LICENSE_COST = 25

# Average number of days vehicle is used (by people who use their vehicle to
# commute)
ANNUAL_VEHICLE_DAYS = 330

# Average number of days transit is used (by people who use transit to
# commute)
ANNUAL_TRANSIT_DAYS = 300

# Scale person trips to vehicle trips
VKT_SCALE = {"SOV": 1, "HOV2": 0.5, "HOV3": 0.3125, "SB": 0.3125}

# List of all Auto modes
AUTO_MODES = ["SOV", "HOV2", "HOV3", "SB"]

# List of all transit modes
TRANSIT_MODES = ["WAT", "DAT", "PNR", "RNUP", "KNR", "RNK"]

# List of all active modes
ACTIVE_MODES = ["Walk", "Bike"]


def main():
    if len(sys.argv) != 5:
        print("Error: Incorrect number of arguments. Expected 4.")
        print(
            "Usage: python main.py <path to households file> "
            "<path to persons file> <path to trips file> <output file name>"
        )
        print(
            "Example: python main.py households_2020.csv "
            "persons_2020.csv total_trips_2020.csv output_2020.csv"
        )
        exit(1)

    households_file, persons_file, trips_file, output_file = sys.argv[1:]

    hh_data = calculate(households_file, persons_file, trips_file)
    generate_points(hh_data, output_file)


def calculate(households_file, persons_file, trips_file):
    """
    Calculate annual transportation cost per household and proportion of annual
    income spent on transportation per household. Output a CSV where each row
    represents a household and contains zone, cost, and proportion columns.
    """
    print("Calculating transportation costs...")

    # Total household data. Maps household ID to household data.
    hh_data = {}

    # Process household file for household-level cost components
    with open(households_file, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            hh_id = int(row["Unique"])
            hh_data[hh_id] = {}

            hh_data[hh_id]["income"] = float(row["Inc"])
            hh_data[hh_id]["zone"] = int(row["Zone"])

            # Annual cost of owned vehicles (fixed cost)
            hh_data[hh_id]["cost"] = int(row["Veh"]) * AUTO_FIXED_COST

    # Map person ID to whether they own a transit pass
    transit_pass_dict = {}

    # Process persons file for person-level cost components
    with open(persons_file, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            person_id = row["Unique"] + row["Serial"] + row["Per#"]
            has_transit_pass = int(row["Transit Pass"])

            transit_pass_dict[person_id] = has_transit_pass

            hh = hh_data[int(row["Unique"])]

            # If the person has an operator's license
            if int(row["Lic"]):
                # Add annual license cost
                hh["cost"] += ANNUAL_LICENSE_COST

            if has_transit_pass:
                # Add transit pass cost (based on person age/type)
                hh["cost"] += PERSON_TO_PASS_COST[row["Per Type"]]

    # Process daily trips file for trip-level cost components
    with open(trips_file, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            hh = hh_data[int(row["UniqueID"])]

            mode = row["Mode"]
            if mode in AUTO_MODES:
                vkt = float(row["Dist"]) * VKT_SCALE[mode]
                vkt_cost = vkt * AUTO_OP_COST * ANNUAL_VEHICLE_DAYS

                # Annual cost of driving (based on vehicle KMs travelled)
                hh["cost"] += vkt_cost
            elif mode in TRANSIT_MODES:
                person_id = row["UniqueID"] + row["Serial"] + row["Person#"]
                if transit_pass_dict[person_id] == 0:
                    # Annual transit cost (without transit pass)
                    hh["cost"] += (AVG_TRANSIT_FARE * ANNUAL_TRANSIT_DAYS)
                else:
                    # Do nothing, transit pass cost is already accounted for
                    continue
            elif mode in ACTIVE_MODES:
                # Active trips are free
                continue

    # Iterate over all household data
    output = []
    for hh in hh_data.values():
        if hh["income"] == 0:
            continue
        proportion = (hh["cost"] / (hh["income"] * 1000)) * 100
        if proportion > 100:
            continue
        output.append({
            "zone": hh["zone"],
            "cost": round(hh["cost"] / 12),
            "proportion": round(proportion)
        })

    return output
            
            
def generate_points(households, output_file):
    """
    For each household, generate a random point that falls within a residential
    parcel boundary that is within its zone.
    """
    print("Generating points...")

    # Open residences GeoJSON file
    # Note: residences.json is not proper GeoJSON, it is edited to make it small
    with open("config/residences.json.br", "rb") as f:
        residences = json.loads(brotli.decompress(f.read()))

    # Load spatial index and residence information
    id_to_residence = {}  # Map residence ID to residence polygon
    spatial_index = rtree.index.Index()  # R-Tree
    residence_zones = set()  # Set of all zones that have at least one residence
    for i, feature in enumerate(residences["features"]):
        residence_zones.add(feature["properties"]["zone"])
        polygon = shape(feature["geometry"])
        spatial_index.insert(i, polygon.bounds)
        id_to_residence[i] = polygon

    # Open zones GeoJSON file
    with open("config/zones.json", "r") as f:
        zones = json.load(f)

    # Load zone information
    id_to_zone = {}  # Map zone ID to zone polygon
    id_to_zone_bbox = {}  # Map zone ID to zone bounding box
    for feature in zones["features"]:
        feature_id = feature["properties"]["id"]
        id_to_zone[feature_id] = shape(feature["geometry"])
        bbox = shape(feature["geometry"]).bounds
        id_to_zone_bbox[feature_id] = bbox
        
    with open(output_file, "w", newline="") as w:
        fieldnames = ["lon", "lat", "cost", "proportion"]
        writer = csv.DictWriter(w, fieldnames=fieldnames)
        writer.writeheader()

        transformer = Transformer.from_crs("EPSG:3776", "EPSG:4326")

        total_households = len(households)
        for progress, hh in enumerate(households):
            # Print progress
            print("{} / {}".format(progress + 1, total_households))

            zone = int(hh["zone"])
            if zone not in id_to_zone:
                continue
            polygon = id_to_zone[zone]
            bbox = id_to_zone_bbox[zone]

            # Generate random points until one is within the zone and a
            # residence within that zone (or skip the household if it misses
            # 10000 times)
            tries = 0
            error = False
            while True:
                dest_x = random.uniform(bbox[0], bbox[2])
                dest_y = random.uniform(bbox[1], bbox[3])
                point = Point(dest_x, dest_y)
                if polygon.contains(point):
                    if zone in residence_zones:
                        intersections = spatial_index.intersection(
                            (point.x, point.y, point.x, point.y)
                        )

                        contains_point = []
                        for i in intersections:
                            try:
                                contains_point.append(
                                    id_to_residence[i].contains(point)
                                )
                            except TopologicalError:
                                continue

                        if any(contains_point):
                            break
                    else:
                        break
                if tries == 10000:
                    break
                tries += 1

            if tries < 10000 and not error:
                lat, lon = transformer.transform(dest_x, dest_y)

                writer.writerow({
                    "lon": round(lon, 5),
                    "lat": round(lat, 5),
                    "cost": hh["cost"],
                    "proportion": hh["proportion"]
                })


if __name__ == "__main__":
    main()
