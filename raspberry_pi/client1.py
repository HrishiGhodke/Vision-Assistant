import serial
import time
import cv2
from skimage.metrics import structural_similarity as compare_ssim
from deep_translator import GoogleTranslator
from playsound import playsound
from gtts import gTTS
import os
import socket
import RPi.GPIO as GPIO

# Constants for server connection
SERVER_IP = "172.21.11.69"
SERVER_PORT = 8080

# Supported languages and their codes for translation
languages = {
    '1': ('hi', 'Hindi'),
    '2': ('en', 'English'),
    '3': ('kn', 'Kannada'),
    '4': ('ta', 'Tamil'),
    '5': ('te', 'Telugu')
}

# GPIO Pin setup
button_pins = {
    '1': 17,  # Hindi
    '2': 18,  # English
    '3': 27,  # Kannada
    '4': 22,  # Tamil
    '5': 23   # Telugu
}

# Setup GPIO mode and pins
GPIO.setmode(GPIO.BCM)
for pin in button_pins.values():
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Enable internal pull-up resistors

def get_language_selection():
    print("\nPress a button to select your language:")
    print("1: Hindi\n2: English\n3: Kannada\n4: Tamil\n5: Telugu")

    while True:
        for key, pin in button_pins.items():
            if not GPIO.input(pin):  # Button pressed
                print(f"Language selected: {languages[key][1]}")
                return key
        time.sleep(0.1)  # Debounce delay

# Connect to the server first
print("Connecting to the server...")
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, SERVER_PORT))
print(client_socket.recv(1024).decode())  # Receive "connected" message

# Initialize serial communication with Arduino
arduino = serial.Serial('/dev/ttyACM0', 9600)  # Adjust the port to /dev/ttyACM0
time.sleep(2)  # Wait for Arduino to reset

# Step 1: Send the 'Move upwards' command to Arduino
print("Sending 'Move upwards' command to Arduino.")
arduino.write('Move upwards\n'.encode())
response = arduino.readline().decode().strip()  # Read Arduino response
print(f"Arduino: {response}")

# Step 2: Wait for Arduino to signal to start paper detection
response = arduino.readline().decode().strip()
print(f"Arduino: {response}")

# Step 3: Wait for the top limit switch to be triggered
print("Waiting for Arduino to trigger top limit switch...")
response = arduino.readline().decode().strip()  # Arduino will send a message when top limit switch is triggered
print(f"Arduino: {response}")

# Step 4: Add a 12-second delay before paper detection
print("Waiting for 12 seconds before starting paper detection...")
time.sleep(12)  # Delay to ensure the motor movement and other operations are complete

# Step 5: Start paper detection
print("Starting paper detection... Please hold steady for 5 seconds.")
time.sleep(1)  # Delay to ensure the motor movement has completed

# Initialize the webcam for paper detection
cap = cv2.VideoCapture(0)  # Use '0' for the default webcam
if not cap.isOpened():
    print("Error: Could not access the webcam.")
    exit()

captured_frame = None
start_time = time.time()

while time.time() - start_time < 5:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read from the webcam.")
        cap.release()
        exit()

    # Display live preview during capture
    cv2.imshow("Live Preview", frame)
    captured_frame = frame
    cv2.waitKey(1)

cap.release()
cv2.destroyAllWindows()

# Check if an image was captured
if captured_frame is None:
    print("Error: Could not capture an image from the webcam.")
    exit()

# Convert the captured frame to grayscale
captured_image = cv2.cvtColor(captured_frame, cv2.COLOR_BGR2GRAY)

# Load the reference image (A4 paper)
reference_image_path = "/home/pi/Desktop/Indore/venv/ref.jpg"  # Adjust the path
reference_image = cv2.imread(reference_image_path, cv2.IMREAD_GRAYSCALE)

if reference_image is None:
    print("Error: Could not load the reference image.")
    exit()

# Resize both images to the same size for comparison
reference_resized = cv2.resize(reference_image, (500, 700))  # Resize to standard A4 size (approx.)
captured_resized = cv2.resize(captured_image, (500, 700))

# Verify that both images are of the same shape before comparing
if reference_resized.shape != captured_resized.shape:
    print(f"Error: Images have different shapes. Reference shape: {reference_resized.shape}, Captured shape: {captured_resized.shape}")
    exit()

# Compute the Structural Similarity Index (SSIM) to compare images
score, _ = compare_ssim(reference_resized, captured_resized, full=True)
print(f"SSIM score: {score}")

# Set a threshold for determining A4 or A5 paper size
threshold = 0.37  # Adjust the threshold based on experimentation

# Determine paper size based on SSIM score
if score >= threshold:
    print("Detected: A4")
    paper_size = "A4"
else:
    print("Detected: A5")
    paper_size = "A5"

# Step 6: Send the paper size (A4 or A5) to Arduino
time.sleep(1)
arduino.write(f'{paper_size}\n'.encode())
print(f"Sent paper size to Arduino: {paper_size}")

# Step 7: Wait for Arduino to confirm it's ready to capture
response = arduino.readline().decode().strip()
print(f"Arduino: {response}")

# Step 8: Capture Final Photo and Send to Server
print("Capturing photo and saving to disk...")
cap = cv2.VideoCapture(0)  # Re-initialize the webcam for final photo capture

# Live preview for 3 seconds before final capture
start_time = time.time()
while time.time() - start_time < 3:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read from the webcam.")
        cap.release()
        exit()

    # Display live preview during the final capture
    cv2.imshow("Final Photo Preview", frame)
    captured_frame = frame
    cv2.waitKey(1)

cap.release()
cv2.destroyAllWindows()

# Check if an image was captured
if captured_frame is None:
    print("Error: Could not capture an image from the webcam.")
    exit()

# Save the final captured image
image_filename = f"/home/pi/Desktop/Indore/venv/{paper_size}_paper_capture.jpg"
cv2.imwrite(image_filename, captured_frame)
print(f"Image saved as {image_filename}")

print("Sending 'CaptureComplete' command to Arduino.")
arduino.write('CaptureComplete\n'.encode())

# Function to send the file to the server
def send_file(client_socket, file_path):
    file_size = os.path.getsize(file_path)
    client_socket.sendall(str(file_size).encode())  # Send file size
    client_socket.recv(4096)  # Wait for acknowledgment
    print("Sending image to the server...")

    with open(file_path, "rb") as f:
        sent = 0
        while chunk := f.read(4096):
            client_socket.sendall(chunk)
            sent += len(chunk)
            percent = (sent / file_size) * 100
            print(f"Upload progress: {percent:.2f}%")

    print("Image successfully sent.")

# Send the image to the server
send_file(client_socket, image_filename)

# Function to receive the response from the server
def receive_response(client_socket):
    response_size = int(client_socket.recv(4096).decode())  # Receive response size
    client_socket.sendall("SIZE_RECEIVED".encode())  # Acknowledge response size
    print("Receiving response from the server...")

    response = b""
    total_received = 0
    while total_received < response_size:
        chunk = client_socket.recv(4096)
        response += chunk
        total_received += len(chunk)
        percent = (total_received / response_size) * 100
        print(f"Download progress: {percent:.2f}%")

    print("Response successfully received.")
    return response.decode()

# Receive the server's response
response = receive_response(client_socket)
print(f"Server response: {response}")

intro_audio_file = "/home/pi/Desktop/Indore/venv/multi.mp3"  # Replace with your MP3 file path
try:
    print("Playing the intro audio message...")
    playsound(intro_audio_file)
except Exception as e:
    print(f"Error playing the audio file: {e}")

# Language selection and response handling
try:
    selected_lang = get_language_selection()
    lang_code, lang_name = languages[selected_lang]
    translated_response = GoogleTranslator(source='auto', target=lang_code).translate(response)
    print(f"\nTranslated response ({lang_name}): {translated_response}")

    # Speak the translated response
    print("Speaking the response...")
    tts = gTTS(text=translated_response, lang=lang_code, slow=False)
    audio_file = "temp_audio.mp3"
    tts.save(audio_file)
    playsound(audio_file)
    os.remove(audio_file)
except KeyError:
    print("Invalid language selection.")
finally:
    GPIO.cleanup()  # Clean up GPIO settings on exit

# Close the server connection
client_socket.close()
print("Server connection closed.")
