import cv2
import time
import os

# Load Haar cascades
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

if face_cascade.empty() or eye_cascade.empty():
    print("Error loading Haar cascades.")
    exit()

# Initialize webcam with DSHOW backend for Windows to fix MSMF errors
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow backend
attempts = 0
max_attempts = 3
while not cap.isOpened() and attempts < max_attempts:
    print(f"Attempt {attempts + 1}: Webcam not accessible, retrying in 5 seconds...")
    time.sleep(5)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    attempts += 1
if not cap.isOpened():
    print(f"Error: Webcam not accessible after {max_attempts} attempts.")
    exit()

total_frames = 0
focused_frames = 0
blink_count = 0
last_eye_count = 0
nervousness_score = 0
accuracy = 0.0  # Initialize accuracy to avoid undefined error

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        print("Retrying frame capture...")
        cap.release()
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Retry with DSHOW
        time.sleep(1)
        continue

    total_frames += 1
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    eye_contact = "Not Focusing"

    for (x, y, w, h) in faces:
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = frame[y:y+h, x:x+w]
        eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        if len(eyes) >= 2:
            eye_contact = "Focused"
            focused_frames += 1
            # Detect blinks (simplified: rapid change in eye detection)
            if last_eye_count > 0 and len(eyes) == 0:
                blink_count += 1
            last_eye_count = len(eyes)

        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        for (ex, ey, ew, eh) in eyes:
            cv2.rectangle(roi_color, (ex, ey), (ex + ew, ey + eh), (0, 255, 0), 2)

    # Simplified nervousness: higher blink rate = more nervous
    nervousness_score = min(blink_count * 10, 100)  # Cap at 100%

    # Compute accuracy before loop exit
    accuracy = (focused_frames / total_frames) * 100 if total_frames > 0 else 0.0
    focus_text = f"Focus: {eye_contact}"
    accuracy_text = f"Accuracy: {accuracy:.2f}%"
    cv2.putText(frame, focus_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0) if eye_contact == "Focused" else (0, 0, 255), 2)
    cv2.putText(frame, accuracy_text, (frame.shape[1] - 200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow("Eye Contact Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# Save results to a file with error handling
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
results_file = os.path.join(desktop_path, "eye_contact_results.txt")

try:
    os.makedirs(desktop_path, exist_ok=True)
    with open(results_file, "w", encoding="utf-8") as f:
        f.write(f"Total Frames: {total_frames}\n")
        f.write(f"Focused Frames: {focused_frames}\n")
        f.write(f"Accuracy: {accuracy:.2f}%\n")
        f.write(f"Nervousness Score: {nervousness_score}%\n")
        f.write(f"Blink Count: {blink_count}\n")
    print(f"Results successfully saved to {results_file}")
except Exception as e:
    print(f"An error occurred while saving results: {str(e)}")