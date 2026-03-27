import cv2
import time

from outdoor.detector import run_once
from outdoor.ors_navigation import (
    outdoor_navigation_instructions,
    show_route_on_map
)

from outdoor.tts import SpeechService


speech = SpeechService()


def speak(text):
    print("VOICE:", text)
    speech.speak(text)


def detect_obstacles(frame):

    detections = run_once(frame)

    obstacles = []

    for d in detections:
        obstacles.append({
            "object": d["class"],
            "distance": d.get("distance_m", None)
        })

    return obstacles


def step_by_step_navigation(instructions):

    cap = cv2.VideoCapture(0,cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("Camera error")
        return

    index = 0
    last_spoken = time.time()

    print("\n🎥 Live Outdoor Navigation Started")
    print("ENTER → Next instruction")
    print("Q → Exit\n")

    while True:

        ret, frame = cap.read()
        if not ret:
            continue

        detections = run_once(frame)
        obstacles = []

        for d in detections:

            name = d["class"]
            x1, y1, x2, y2 = d["bbox"]

            # draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)

            label = name
            if d["distance_m"]:
                label += f" {d['distance_m']:.1f}m"

            cv2.putText(frame, label, (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

            obstacles.append({
                "object": name,
                "distance": d["distance_m"]
            })

        if obstacles and time.time() - last_spoken > 2:

            spoken = set()

            for obj in obstacles:

                name = obj["object"]
                dist = obj["distance"]

                if name not in spoken:

                    if dist:
                        speak(f"{name} ahead {dist:.1f} meters")
                    else:
                        speak(f"{name} ahead")

                    spoken.add(name)

            last_spoken = time.time()

        cv2.imshow("Outdoor Navigation", frame)

        key = cv2.waitKey(1) & 0xFF

        # ENTER
        if key == 13:

            if index < len(instructions):

                speak(instructions[index])
                index += 1

            else:
                speak("You have reached your destination")
                break

        # Q
        elif key == ord('q'):

            speak("Navigation stopped")
            break

    cap.release()
    cv2.destroyAllWindows()


def start_outdoor_navigation():

    print("\n🌍 OUTDOOR NAVIGATION")

    start = input("Enter starting location: ")
    destination = input("Enter destination: ")

    speak("Generating outdoor route")

    instructions, route, start_coord, end_coord = outdoor_navigation_instructions(
        start,
        destination
    )

    if not instructions:
        speak("No route found")
        return

    # SHOW MAP
    show_route_on_map(route, start_coord, end_coord)

    print("\n📋 Navigation Instructions:\n")

    for i, ins in enumerate(instructions, 1):
        print(f"{i}. {ins}")

    input("\nPress ENTER to start navigation...")

    step_by_step_navigation(instructions)