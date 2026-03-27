


# outdoor/ors_navigation.py

import openrouteservice
import folium
import os
import webbrowser
from outdoor.tts import SpeechService


ORS_API_KEY = os.getenv("ORS_API_KEY")
client = openrouteservice.Client(key=ORS_API_KEY)
speech = SpeechService()

# Approx conversion: 1 meter ≈ 2 steps
def meters_to_steps(meters):
    return int(meters * 2)



def generate_chunked_instructions(total_steps):
    instructions = []

    CHUNK = 40
    chunks = total_steps // CHUNK
    remainder = total_steps % CHUNK

    phrases = [
        "Walk straight for about {n} steps.",
        "Continue forward on the same path for another {n} steps.",
        "Keep moving straight for roughly {n} more steps.",
        "Walk forward a little more, around {n} steps."
    ]

    for i in range(chunks):
        phrase = phrases[i % len(phrases)]
        instructions.append(phrase.format(n=CHUNK))

        if chunks >= 3 and i == chunks // 2:
            instructions.append("You are about halfway to the next turn.")

        if i == chunks - 2:
            instructions.append("The turn is coming up soon.")

    if remainder > 0:
        instructions.append(f"Walk straight for about {remainder} steps.")

    return instructions


def get_coordinates(place_name):
    geocode = client.pelias_search(text=place_name)
    coords = geocode["features"][0]["geometry"]["coordinates"]
    return coords  


# GET ROUTE

def get_route(start_place, end_place):
    start_coord = get_coordinates(start_place)
    end_coord = get_coordinates(end_place)

    route = client.directions(
        coordinates=[start_coord, end_coord],
        profile="foot-walking",
        format="geojson"
    )

    return route, start_coord, end_coord



def outdoor_navigation_instructions(start_place, end_place):
    route, start_coord, end_coord = get_route(start_place, end_place)

    raw_steps = route["features"][0]["properties"]["segments"][0]["steps"]
    instructions = []

    for step in raw_steps:
        distance = step["distance"]
        instruction_text = step["instruction"].lower()
        steps = meters_to_steps(distance)

        # 1️⃣ TURN INSTRUCTION
        if "arrive" in instruction_text:
            instructions.append("You are close to your destination.")
            break

        elif "left" in instruction_text:
            instructions.append("Stop. Turn left.")

        elif "right" in instruction_text:
            instructions.append("Stop. Turn right.")

        elif "slight left" in instruction_text:
            instructions.append("Stay slightly left.")

        elif "slight right" in instruction_text:
            instructions.append("Stay slightly right.")

        else:
            instructions.append("Face forward.")

        # 2️⃣ WALKING DISTANCE (ALWAYS CHUNKED)
        if steps > 0:
            instructions.extend(generate_chunked_instructions(steps))

    instructions.append("You have arrived at your destination.")
    return instructions, route, start_coord, end_coord



def show_route_on_map(route, start_coord, end_coord):
    coords = route["features"][0]["geometry"]["coordinates"]
    path = [(c[1], c[0]) for c in coords]

    m = folium.Map(location=[start_coord[1], start_coord[0]], zoom_start=14)

    folium.Marker(
        [start_coord[1], start_coord[0]],
        tooltip="Start"
    ).add_to(m)

    folium.Marker(
        [end_coord[1], end_coord[0]],
        tooltip="Destination"
    ).add_to(m)

    folium.PolyLine(path, weight=5).add_to(m)

    map_file = "outdoor_route.html"
    m.save(map_file)
    webbrowser.open("file://" + os.path.realpath(map_file))
