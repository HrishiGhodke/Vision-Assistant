#include <Stepper.h>

// Stepper motor configuration
#define STEPS_PER_REV 200  // Steps per revolution for NEMA 17
Stepper myStepper(STEPS_PER_REV, 8, 9); // Stepper on pins 8 (step) and 9 (dir)

// Limit switch pins
const int topSwitchPin = 6;    // Top limit switch
const int bottomSwitchPin = 7; // Bottom limit switch

// Flags and variables
long paperDetectionDistance = 0;  // Distance moved upward to detect paper
const int distanceA4 = -8000;     // Steps to move downward for A4
const int distanceA5 = -10000;    // Steps to move downward for A5
boolean paperDetected = false;    // Flag to indicate paper detection stage

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  Serial.println("Stepper Motor Program Started");

  // Configure stepper motor speed
  myStepper.setSpeed(1000); // Set speed in RPM

  // Configure limit switches
  pinMode(topSwitchPin, INPUT_PULLUP);   // Internal pull-up for top switch
  pinMode(bottomSwitchPin, INPUT_PULLUP); // Internal pull-up for bottom switch

  // Stepper motor sound demonstration
  Serial.println("Playing stepper motor sound...");
  for (int freq = 100; freq <= 1000; freq += 50) { // Increase frequency
    playTone(freq, 100); // Play each frequency for 100ms
  }
  for (int freq = 1000; freq >= 100; freq -= 50) { // Decrease frequency
    playTone(freq, 100);
  }
  Serial.println("Stepper motor sound complete.");
}

void loop() {
  // Step 1: Wait for the Raspberry Pi command to move upwards
  Serial.println("Waiting for Raspberry Pi command: 'Move upwards'");
  while (true) {
    if (Serial.available()) {
      String command = Serial.readStringUntil('\n');
      if (command == "Move upwards") {
        Serial.println("Command received: Moving upwards...");
        break; // Exit the loop and proceed
      } else {
        Serial.println("Invalid command. Waiting for 'Move upwards'.");
      }
    }
  }

  // Step 2: Move the motor upwards until the top limit switch is triggered
  Serial.println("Moving motor upwards...");
  while (digitalRead(topSwitchPin) == HIGH) {
    myStepper.step(1); // Move upwards step-by-step
  }
  Serial.println("Top limit switch triggered!");

  // Add a 1 second delay before signaling paper detection
  delay(1000);

  // Step 3: Signal Raspberry Pi to detect paper
  Serial.println("Signal to Raspberry Pi: Start Paper Detection");

  // Wait for Raspberry Pi to send the paper size
  while (Serial.available() == 0); // Wait for input
  String paperSize = Serial.readStringUntil('\n');

  // Step 4: Handle Raspberry Pi's response
  if (paperSize == "A4") {
    Serial.println("Paper Detected: A4");
    myStepper.step(distanceA4);  // Move downward to A4 position
    delay(2000);                 // Stabilization delay
    Serial.println("Signal to Raspberry Pi: Ready to Capture A4");
  } else if (paperSize == "A5") {
    Serial.println("Paper Detected: A5");
    myStepper.step(distanceA5);  // Move downward to A5 position
    delay(2000);                 // Stabilization delay
    Serial.println("Signal to Raspberry Pi: Ready to Capture A5");
  } else {
    Serial.println("Invalid Command from Raspberry Pi!");
    return; // Exit loop on invalid command
  }

  // Step 5: Wait for Raspberry Pi to confirm the image capture
  Serial.println("Waiting for Raspberry Pi: Image Capture Complete");
  while (Serial.available() == 0); // Wait for Raspberry Pi signal
  String captureConfirmation = Serial.readStringUntil('\n');

  if (captureConfirmation == "CaptureComplete") {
    Serial.println("Image Capture Confirmed") ;
  } else {
    Serial.println("Error: Expected 'CaptureComplete' from Raspberry Pi");
    return;
  }

  // Step 6: Move downward to the original position until the bottom limit switch is triggered
  Serial.println("Returning to Original Position...");
  while (digitalRead(bottomSwitchPin) == HIGH) {
    myStepper.step(-1); // Move downward step-by-step
  }
  Serial.println("Bottom limit switch triggered!");

  // Step 7: End the program
  Serial.println("Program Complete. Motor Halted.");
  while (true); // Stop further execution
}

// Function to play tones using the stepper motor
void playTone(int frequency, int duration) {
  int halfPeriod = 1000000 / (frequency * 2); // Half-period in microseconds
  long cycles = (long)frequency * duration / 1000; // Number of cycles

  for (long i = 0; i < cycles; i++) {
    myStepper.step(1); // Move a single step
    delayMicroseconds(halfPeriod);
    myStepper.step(-1); // Step back
    delayMicroseconds(halfPeriod);
  }
}
