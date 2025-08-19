import socket
import os
import cv2
from PIL import Image
import pytesseract
from ultralytics import YOLO

# Socket Constants
HOST = "0.0.0.0"
PORT = 8080
SAVE_PATH = "received_image.jpg"
TIMEOUT = 1  # Socket timeout in seconds

# Setup for Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Initialize YOLOv8 for object detection
model = YOLO('yolov8m.pt')  # Load YOLOv8 model


def preprocess_image(image_path):
    """Preprocess the image to improve OCR results."""
    try:
        # Load the image in grayscale
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError("Error loading image for preprocessing.")

        # Apply Gaussian blur to reduce noise
        blurred_image = cv2.GaussianBlur(image, (5, 5), 0)

        # Thresholding to convert the image to binary
        _, binary_image = cv2.threshold(
            blurred_image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        return binary_image
    except Exception as e:
        print(f"Preprocessing error: {e}")
        return None


def image_to_text(image_path, lang='eng'):
    """Extract text from an image using Tesseract OCR with preprocessing."""
    try:
        # Preprocess the image
        preprocessed_image = preprocess_image(image_path)
        if preprocessed_image is None:
            return "Error: Preprocessed image is not available."

        # Save preprocessed image for debugging (optional)
        cv2.imwrite("preprocessed_image.jpg", preprocessed_image)

        # Use Tesseract to extract text
        text = pytesseract.image_to_string(preprocessed_image, lang=lang)
        return text.strip()
    except Exception as e:
        print(f"OCR error: {e}")
        return ""


def detect_objects(image_path, confidence_threshold=0.4):
    """Detect objects in an image using YOLOv8 with expanded output."""
    results = model(image_path)
    detected_objects = []
    for box in results[0].boxes:
        label_index = int(box.cls)
        confidence = float(box.conf)
        if confidence > confidence_threshold:
            detected_objects.append({
                "label": model.names[label_index],
                "confidence": round(confidence, 2),
                "coordinates": {
                    "x1": int(box.xyxy[0][0]),
                    "y1": int(box.xyxy[0][1]),
                    "x2": int(box.xyxy[0][2]),
                    "y2": int(box.xyxy[0][3])
                }
            })
    return detected_objects


def process_image(image_path):
    """Processes the image for OCR and object detection."""
    print("Processing the image...")

    # Extract text using OCR
    extracted_text = image_to_text(image_path, lang='eng')

    # Detect objects using YOLOv8
    detected_objects = detect_objects(image_path, confidence_threshold=0.4)

    # Combine results
    results = {
        "text": extracted_text,
        "objects": detected_objects
    }

    print("Processing complete.")
    return results


def receive_file(client_socket, save_path):
    """Receives a file from the client with a progress indicator."""
    with open(save_path, "wb") as f:
        print("Receiving image...")
        total_received = 0
        file_size = int(client_socket.recv(4096).decode())  # First, receive the file size
        client_socket.sendall("SIZE_RECEIVED".encode())  # Acknowledge file size
        while total_received < file_size:
            data = client_socket.recv(4096)
            if not data:
                break
            f.write(data)
            total_received += len(data)
            percent = (total_received / file_size) * 100
            print(f"Progress: {percent:.2f}%")

    print("Image successfully received.")


def send_response(client_socket, response):
    """Sends a response back to the client with a progress indicator."""
    print("Sending response to the client...")
    response_bytes = response.encode()
    response_size = len(response_bytes)
    client_socket.sendall(str(response_size).encode())  # Send response size
    client_socket.recv(4096)  # Wait for acknowledgment
    sent = 0
    while sent < response_size:
        chunk = response_bytes[sent:sent + 4096]
        client_socket.sendall(chunk)
        sent += len(chunk)
        percent = (sent / response_size) * 100
        print(f"Response upload progress: {percent:.2f}%")

    print("Response successfully sent.")


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    server_socket.settimeout(TIMEOUT)  # Set timeout to allow graceful shutdown
    print(f"Server listening on {HOST}:{PORT}")

    try:
        while True:
            try:
                print("\nWaiting for a new connection...")
                client_socket, client_address = server_socket.accept()
                print(f"Connection from {client_address}")

                try:
                    client_socket.sendall("connected".encode())

                    # Receive the image
                    receive_file(client_socket, SAVE_PATH)

                    # Process the image
                    results = process_image(SAVE_PATH)

                    # Format results for sending
                    response = f"Extracted Text: {results['text']}\n" \
                               f"Detected Objects: {', '.join(obj['label'] for obj in results['objects'])}"

                    # Send the result back to the client
                    send_response(client_socket, response)

                except Exception as e:
                    print(f"An error occurred during the client session: {e}")
                finally:
                    client_socket.close()
                    print(f"Connection with {client_address} closed.\n")

            except socket.timeout:
                pass  # Allow timeout to check for KeyboardInterrupt
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
