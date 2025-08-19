# Vision-Assistant
Vision Assistant is an assistive technology project for visually impaired users. It uses Raspberry Pi, Arduino, and Computer Vision to detect paper, extract and translate text via OCR/YOLO, and provide audio output. The system enables real-time, multi-language reading assistance with braille controls.

##  Abstract
Visually impaired people often face difficulties in accessing printed documents independently.
This project integrates **Raspberry Pi, Arduino, and Computer Vision** to build a **smart document reader**.
The system detects paper, captures its content, processes it with OCR + YOLO, and finally **reads aloud** the results in multiple Indian languages.

---


### Components:
- **Raspberry Pi 4B**: Paper detection, image capture, client socket, language translation, text-to-speech.  
- **Arduino Uno**: Motor control with NEMA 17 + A4988, limit switch handling, paper positioning.  
- **Server (Laptop)**: Runs OCR (Tesseract) + Object Detection (YOLOv8).  
- **User Interface**: Braille printed buttons for language selection + Audio output.  

---

##  Hardware Requirements
- Raspberry Pi 4B  
- Arduino Uno  
- Webcam  
- Stepper Motor (NEMA 17)  
- A4988 Motor Driver  
- Limit switches (Top/Bottom)  
- Braille-printed buttons  
- Laptop (Server)  

---

##  Software Requirements
- **Raspberry Pi**: Python 3.9+, OpenCV, scikit-image, gTTS, playsound, deep-translator  
- **Server (Laptop)**: Python 3.9+, OpenCV, pytesseract, YOLOv8 (Ultralytics), PyTorch, Pillow  
- **Arduino**: Arduino IDE  

---

## 🔧 Installation

###  Raspberry Pi Setup
```bash
cd raspberry_pi
pip install -r requirements.txt
python3 raspberry_pi.py
```

###  Server Setup
```bash
cd server
pip install -r requirements.txt
python server.py
```

###  Arduino Setup
1. Open `arduino/arduino.ino` in Arduino IDE  
2. Select correct board (Arduino Uno) & COM port  
3. Upload code  

---

##  Usage Flow
1. User places paper in the setup.  
2. Raspberry Pi commands Arduino → motor aligns paper.  
3. Raspberry Pi detects paper size (A4/A5) via camera.  
4. Raspberry Pi captures final image → sends to server.  
5. Server runs OCR (text) + YOLOv8 (objects) → sends results back.  
6. User presses a **Braille button** to select language.  
7. Raspberry Pi translates text → converts to speech → plays audio.  

---

##  Results
- OCR extracts printed text.  
- YOLO detects objects/figures on paper.  
- Audio feedback provided in Hindi, English, Kannada, Tamil, Telugu.  

---
