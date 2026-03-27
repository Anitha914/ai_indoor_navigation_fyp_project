

# import cv2
# import time
# import sqlite3
# import networkx as nx
# import pyttsx3
# import threading
# from ultralytics import YOLO
# from db_utils import get_db_conn
# from localization import localize
# from navigation_logic import get_turn, distance

# # ---------------- TEXT TO SPEECH ----------------
# engine = pyttsx3.init()
# engine.setProperty('rate', 150)
# speech_lock = threading.Lock()

# def speak(text):
#     print("VOICE:", text)
#     threading.Thread(target=_speak, args=(text,), daemon=True).start()

# def _speak(text):
#     with speech_lock:
#         engine.say(text)
#         engine.runAndWait()

# message_memory = {}
# def speak_once(text, cooldown=5):
#     now = time.time()
#     if text in message_memory:
#         if now - message_memory[text] < cooldown:
#             return
#     speak(text)
#     message_memory[text] = now

# # ---------------- CAMERA & MODEL ----------------
# cap = cv2.VideoCapture(0)
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

# # Load YOLO model directly (removed try/except to see errors if they happen)
# print("Loading YOLO model...")
# model = YOLO("yolov8n.pt")
# print("YOLO model loaded.")

# # ---------------- GRAPH & HELPERS ----------------
# def load_graph():
#     conn = get_db_conn()
#     cur = conn.cursor()
#     G = nx.Graph()
#     cur.execute("SELECT id, name FROM nodes")
#     for node_id, name in cur.fetchall():
#         G.add_node(node_id, name=name)
#     cur.execute("SELECT a, b, weight FROM edges")
#     for a, b, w in cur.fetchall():
#         G.add_edge(a, b, weight=w)
#     conn.close()
#     return G

# def get_node_name(node):
#     conn = get_db_conn()
#     cur = conn.cursor()
#     cur.execute("SELECT name FROM nodes WHERE id=?", (node,))
#     row = cur.fetchone()
#     conn.close()
#     return row[0] if row else f"Node {node}"

# def plan_route(start, end):
#     G = load_graph()
#     if not G.has_node(start) or not G.has_node(end):
#         return None
#     try:
#         return nx.shortest_path(G, start, end, weight="weight")
#     except:
#         return None

# # ---------------- OBSTACLE DETECTION ----------------
# def detect_obstacle(frame):

#     results = model(frame, conf=0.5, verbose=False)
#     frame_width = frame.shape[1]

#     detected = None

#     for r in results:
#         for box in r.boxes:

#             conf = float(box.conf[0])
#             if conf < 0.45:
#                 continue

#             cls = int(box.cls[0])
#             label = model.names[cls]

#             x1,y1,x2,y2 = map(int, box.xyxy[0])

#             center = (x1+x2)//2

#             if center < frame_width*0.33:
#                 direction="left"
#             elif center > frame_width*0.66:
#                 direction="right"
#             else:
#                 direction="ahead"

#             # draw bounding box
#             cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),3)

#             cv2.putText(frame,
#                         f"{label} {conf:.2f}",
#                         (x1,y1-10),
#                         cv2.FONT_HERSHEY_SIMPLEX,
#                         0.7,
#                         (0,255,0),
#                         2)

#             detected = (label,direction)

#     return detected

# # ---------------- GUIDE FUNCTION ----------------
# def guide(path):
#     if not path or len(path) < 2:
#         speak("No valid path found")
#         return

#     speak("Navigation started.")
#     prev_point = None

#     for i in range(len(path) - 1):
#         current_node = path[i]
#         target_node = path[i+1]
#         target_name = get_node_name(target_node)
        
#         # Turn calculation
#         conn = get_db_conn()
#         cur = conn.cursor()
#         cur.execute("SELECT x,y FROM nodes WHERE id=?", (current_node,))
#         p1 = cur.fetchone()
#         cur.execute("SELECT x,y FROM nodes WHERE id=?", (target_node,))
#         p2 = cur.fetchone()
#         conn.close()

#         if prev_point and p1 and p2:
#             turn = get_turn(prev_point, p1, p2)
#             if turn != "Go straight":
#                 speak(turn)
        
#         speak(f"Walk forward towards {target_name}")

#         confirmation_count = 0
#         start_time = time.time()
#         frame_count = 0 # FIX: Added frame counter
        
#         while True:
#             ret, frame = cap.read()
#             if not ret: continue
            
#             frame_count += 1

#             # --- 1. Localization ---
#             detected_node = None

#             if frame_count % 5 == 0:

#                 votes = []

#                 for _ in range(8):
#                     ret2, f = cap.read()
#                     if not ret2:
#                         continue

#                     node = localize(f)

#                     if node is not None:
#                         votes.append(node)

#                 if votes:
#                     detected_node = max(set(votes), key=votes.count)
#             # prevent jumping nodes
#             if detected_node is not None:
#                 G = load_graph()

#                 if detected_node is not None:
#                     if detected_node != current_node and detected_node not in G.neighbors(current_node):
#                         detected_node = None

#             # --- 2. UI Display ---
#             cv2.putText(frame, f"Target: {target_name}", (20, 30), 
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
#             if detected_node:
#                 cv2.putText(frame, f"See: {get_node_name(detected_node)}", (20, 60), 
#                             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
#             cv2.imshow("Navigation Camera", frame)

#             # --- 3. Obstacle Detection (FIX: Using Frame Counter) ---
#             # Run obstacle detection every 15 frames
#             if frame_count % 8 == 0:
#                 obstacle = detect_obstacle(frame)
#                 if obstacle:
#                     label, direction = obstacle
#                     if direction == "ahead":
#                         speak_once(f"{label} ahead. Be careful.")
#                     else:
#                         speak_once(f"{label} on your {direction}.")

#             cv2.imshow("Navigation Camera", frame)
            
#             # --- 4. Wall/Path Logic (Simple Heuristic) ---
#             # Run every 30 frames (less frequent)
#             if frame_count % 30 == 0:
#                 gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#                 edges = cv2.Canny(gray, 50, 150)
#                 density = edges.sum() / (frame.shape[0] * frame.shape[1])
#                 if density > 30: 
#                     speak_once("Possible obstacle ahead.", cooldown=8)

#             # --- 5. ARRIVAL CHECK ---
#             # --- ARRIVAL CHECK ---
#             if detected_node == target_node:
#                 confirmation_count += 1

#                 if confirmation_count >=2:
#                     speak(f"You reached {target_name}")

#                     # FINAL NODE
#                     if i == len(path) - 2:
#                         speak("You have arrived at your final destination")
#                         return

#                     break# SUCCESS: Move to next path segment
#             else:
#                 confirmation_count = 0
#                 # Feedback if stuck at start
#                 if detected_node == current_node:
#                      if time.time() - start_time > 5:
#                          speak_once(f"You are still at {get_node_name(current_node)}. Please walk forward.", cooldown=6)

#             # --- EXIT KEY ---
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 speak("Navigation stopped")
#                 cap.release()
#                 cv2.destroyAllWindows()
#                 return

#         prev_point = p1

#     speak("You have arrived at your final destination.")

# # ---------------- OBJECT FINDING ----------------
# def guide_to_object(target):
#     speak(f"Searching for {target}")
#     while True:
#         ret, frame = cap.read()
#         if not ret: continue

#         results = model(frame)
#         frame_width = frame.shape[1]
#         found = False
        
#         for r in results:
#             for box in r.boxes:
#                 cls = int(box.cls[0])
#                 label = model.names[cls]
#                 if label == target:
#                     x1, y1, x2, y2 = map(int, box.xyxy[0])
#                     center = (x1 + x2) // 2
#                     size = x2 - x1

#                     if center < frame_width * 0.33:
#                         speak_once(f"{target} is on your left")
#                     elif center > frame_width * 0.66:
#                         speak_once(f"{target} is on your right")
#                     else:
#                         speak_once(f"{target} is ahead")

#                     if size > 200:
#                         speak(f"You reached the {target}")
#                         return
#                     else:
#                         speak_once("Walk forward")
                    
#                     cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#                     found = True
#                     break
#             if found: break

#         cv2.imshow("Object Guidance", frame)
#         if cv2.waitKey(1) == 27: break

# # ---------------- MAIN ----------------
# if __name__ == "__main__":
#     print("🦯 AI Navigation System")
#     mode = input("Select navigation mode (indoor/outdoor): ").lower()

#     if mode == "outdoor":
#         try:
#             from outdoor.outdoor_controller import start_outdoor_navigation
#             start_outdoor_navigation()
#         except ImportError:
#             print("Outdoor module not found.")
#     elif mode == "indoor":
#         speak("Indoor navigation system started")
#         while True:
#             cmd = input("\nType route / find / exit: ").lower()
#             if cmd == "exit":
#                 break
#             elif cmd == "route":
#                 print("Enter your current location manually")

#                 start = int(input("Enter start node ID: "))
#                 end = int(input("Enter destination node ID: "))

#                 path = plan_route(start, end)

#                 if path:
#                     guide(path)
#                 else:
#                     speak("No path found")
#             elif cmd == "find":
#                 obj = input("Enter object name: ")
#                 guide_to_object(obj)
#     else:
#         print("Invalid mode")


import cv2
import time
import sqlite3
import networkx as nx
import pyttsx3
import threading
from ultralytics import YOLO
from db_utils import get_db_conn
from localization import localize
from navigation_logic import get_turn
from collections import deque
from collections import Counter
import speech_recognition as sr
from rapidfuzz import process

# ---------------- TEXT TO SPEECH ----------------
engine = pyttsx3.init()
engine.setProperty('rate', 150)
speech_lock = threading.Lock()

def speak(text):
    print("VOICE:", text)
    threading.Thread(target=_speak, args=(text,), daemon=True).start()

def _speak(text):
    with speech_lock:
        engine.say(text)
        engine.runAndWait()

message_memory = {}
def speak_once(text, cooldown=5):
    now = time.time()
    if text in message_memory and now - message_memory[text] < cooldown:
        return
    speak(text)
    message_memory[text] = now

# ---------------- CAMERA & MODEL ----------------
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

print("Loading YOLO model...")
model = YOLO("yolov8n.pt")
print("YOLO model loaded.")

# ---------------- GRAPH ----------------
def load_graph():
    conn = get_db_conn()
    cur = conn.cursor()
    G = nx.Graph()
    cur.execute("SELECT id, name FROM nodes")
    for node_id, name in cur.fetchall():
        G.add_node(node_id, name=name)
    cur.execute("SELECT a, b, weight FROM edges")
    for a, b, w in cur.fetchall():
        G.add_edge(a, b, weight=w)
    conn.close()
    return G

def get_node_name(node):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM nodes WHERE id=?", (node,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else f"Node {node}"

def plan_route(start, end):
    G = load_graph()
    if not G.has_node(start) or not G.has_node(end):
        return None
    try:
        return nx.shortest_path(G, start, end, weight="weight")
    except:
        return None

# ---------------- OBSTACLE DETECTION ----------------
def detect_obstacle(frame):
    results = model(frame, conf=0.5, verbose=False)
    frame_width = frame.shape[1]
    detected = None
    for r in results:
        for box in r.boxes:
            conf = float(box.conf[0])
            if conf < 0.45: continue
            cls = int(box.cls[0])
            label = model.names[cls]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            center = (x1 + x2) // 2
            if center < frame_width * 0.33:
                direction = "left"
            elif center > frame_width * 0.66:
                direction = "right"
            else:
                direction = "ahead"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 3)
            cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
            detected = (label, direction)
    return detected


# ---------------- VOICE HELPERS ----------------

def listen():
    try:
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening...")
            r.adjust_for_ambient_noise(source, duration=1)  # 🔥 important
            audio = r.listen(source)

        text = r.recognize_google(audio)
        print("You said:", text)
        return text.lower()

    except sr.WaitTimeoutError:
        print("I didn't hear anything")
        return None

    except sr.UnknownValueError:
        print("Sorry, I didn't catch that")
        return None

    except Exception as e:
        print("Mic error:", e)
        print("Microphone error, please type input")
        return input("Type location: ").lower()


def parse_locations(text):
    text = text.replace("go to", "")
    text = text.replace("take me to", "")
    text = text.replace("from", "")

    if "to" in text:
        parts = text.split("to")
        start = parts[0].strip()
        dest = parts[1].strip()
        return start, dest

    return None, None



def get_node_id_by_name_fuzzy(name):
    conn = get_db_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT id, name FROM nodes")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return None

    names = [r[1].lower() for r in rows]

    match, score, index = process.extractOne(name.lower(), names)

    print(f"[DEBUG] Input: {name} → Matched: {match} (Score: {score})")

    if score > 55:  # adjust threshold if needed
        return rows[index][0]

    return None

def get_direction_from_flow(prev_gray, curr_gray):
    flow = cv2.calcOpticalFlowFarneback(
        prev_gray, curr_gray,
        None, 0.5, 3, 15, 3, 5, 1.2, 0
    )

    flow_x = flow[..., 0]
    mean_flow_x = flow_x.mean()

    if mean_flow_x > 2:
        return "left"
    elif mean_flow_x < -2:
        return "right"
    else:
        return "forward"
    

def voice_navigation():
    # 🔹 Step 1: Ask starting location
    print("Say your starting location")
    start_text = listen()

    if not start_text:
        print("I didn't get the starting location")
        return

    print(f"You said {start_text}")


    # 🔹 Step 2: Ask destination
    for _ in range(3):  # try 3 times
        print("Say your destination location")
        dest_text = listen()
        if dest_text:
            print(f"You said {dest_text}")
            break
        else:
            print("I didn't get the destination, please repeat")
    else:
        print("Failed to get destination")
        return


    # 🔹 Step 3: Convert to node IDs
    start_id = get_node_id_by_name_fuzzy(start_text)
    dest_id = get_node_id_by_name_fuzzy(dest_text)


    # 🔹 Step 4: Validation
    if start_id is None:
        print(f"Start location {start_text} not found")
        return

    if dest_id is None:
        print(f"Destination {dest_text} not found")
        return


    # 🔹 Step 5: Start navigation
    speak(f"Starting from {start_text} to {dest_text}")

    path = plan_route(start_id, dest_id)

    if not path:
        speak("No path found")
        return

    guide(path)
    
# ---------------- GUIDE FUNCTION ----------------
def guide(path):
    if not path or len(path) < 2:
        speak("No valid path found")
        return

    speak("Navigation started.")
    prev_point = None
    G = load_graph()  # load graph once

    for i in range(len(path) - 1):
        current_node = path[i]
        target_node = path[i+1]
        target_name = get_node_name(target_node)

        # Turn calculation
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT x,y FROM nodes WHERE id=?", (current_node,))
        p1 = cur.fetchone()
        cur.execute("SELECT x,y FROM nodes WHERE id=?", (target_node,))
        p2 = cur.fetchone()
        conn.close()

        if prev_point and p1 and p2:
            turn = get_turn(prev_point, p1, p2)
            if turn == "Turn left":
                speak("Turn left and continue walking")
            elif turn == "Turn right":
                speak("Turn right and continue walking")
            else:
                speak("Go straight")
        speak(f"Walk forward towards {target_name}")

        confirmation_count = 0
        start_time = time.time()
        frame_count = 0

        stable_count = 0
        node_buffer = deque(maxlen=15) 
        # state = "moving"   # moving / turning / reached
        last_direction = None
        node_start_time = None
        prev_gray = None
        flow_history = deque(maxlen=5)

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame_count += 1
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if prev_gray is not None:
                raw_direction = get_direction_from_flow(prev_gray, gray)
                flow_history.append(raw_direction)

                # majority vote
                direction_hint = Counter(flow_history).most_common(1)[0][0]
            else:
                direction_hint = "forward"

            prev_gray = gray

            detected_node,similarity = localize(frame)
            
            if detected_node is not None and similarity > 0.70:
                node_buffer.append(detected_node)

            cv2.putText(frame, f"Node: {detected_node} | Sim: {similarity:.2f}",
                (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            
            
            if len(node_buffer) < 5 and detected_node is None:
                    speak_once("Looking for path...", cooldown=5)
                    
            # --- Stability Check using buffer ---
            if len(node_buffer) == 15:
                most_common_node, count = Counter(node_buffer).most_common(1)[0]

                # print(f"[DEBUG] Buffer: {list(node_buffer)}")
                # print(f"[DEBUG] Most common: {most_common_node}, count: {count}")
                
        
                # ✅ Destination reached
                if most_common_node == target_node and count >= 12:
                    if node_start_time is None:
                        node_start_time = time.time()

                    elif time.time() - node_start_time > 2:  # 2 sec stability
                        speak(f"You reached {target_name}")
                        node_buffer.clear()
                        last_direction = None
                        flow_history.clear()
                        break
                else:
                    node_start_time = None
                
                # --- Direction guidance (ALWAYS active) ---
                if direction_hint == "left" and last_direction != "left":
                    speak_once("Move slightly left", cooldown=3)
                    last_direction = "left"

                elif direction_hint == "right" and last_direction != "right":
                    speak_once("Move slightly right", cooldown=3)
                    last_direction = "right"

                elif direction_hint == "forward" and last_direction != "forward":
                    speak_once("Keep walking forward", cooldown=3)
                    last_direction = "forward"

                # --- Node confirmation (ONLY when stable) ---
                if most_common_node == current_node and count >= 10:
                    speak_once(f"You are at {get_node_name(current_node)}", cooldown=15)
                

            
            # --- Obstacle Detection ---
            if frame_count % 8 == 0:
                obstacle = detect_obstacle(frame)
                if obstacle:
                    label, direction = obstacle
                    if direction == "ahead":
                        speak_once(f"{label} ahead. Be careful.")
                    else:
                        speak_once(f"{label} on your {direction}.")

            # --- UI ---
            cv2.putText(frame, f"Target: {target_name}", (20,30), cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,0,255),2)
            if detected_node is not None:
                cv2.putText(frame, f"See: {get_node_name(detected_node)}", (20,60), cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)
            cv2.imshow("Navigation Camera", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                speak("Navigation stopped")
                cap.release()
                cv2.destroyAllWindows()
                return

        prev_point = p1

    speak("You have arrived at your final destination.")

# ---------------- OBJECT GUIDANCE ----------------
def guide_to_object(target):
    speak(f"Searching for {target}")
    while True:
        ret, frame = cap.read()
        if not ret: continue
        results = model(frame)
        frame_width = frame.shape[1]
        found = False
        for r in results:
            for box in r.boxes:
                cls = int(box.cls[0])
                label = model.names[cls]
                if label == target:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    center = (x1 + x2) // 2
                    size = x2 - x1
                    if center < frame_width * 0.33:
                        speak_once(f"{target} is on your left")
                    elif center > frame_width * 0.66:
                        speak_once(f"{target} is on your right")
                    else:
                        speak_once(f"{target} is ahead")
                    if size > 200:
                        speak(f"You reached the {target}")
                        return
                    else:
                        speak_once("Walk forward")
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    found = True
                    break
            if found: break
        cv2.imshow("Object Guidance", frame)
        if cv2.waitKey(1) == 27: break

# ---------------- MAIN ----------------
if __name__ == "__main__":
    print("🦯 AI Navigation System")
    mode = input("Select navigation mode (indoor/outdoor): ").lower()

    if mode == "outdoor":
        try:
            from outdoor.outdoor_controller import start_outdoor_navigation
            start_outdoor_navigation()
        except ImportError:
            print("Outdoor module not found.")
    elif mode == "indoor":
        speak("Indoor navigation system started")
        while True:
            cmd = input("\nType route / find / exit: ").lower()
            if cmd == "exit":
                break
            elif cmd == "route":
                voice_navigation()
            elif cmd == "find":
                obj = input("Enter object name: ")
                guide_to_object(obj)
    else:
        print("Invalid mode")