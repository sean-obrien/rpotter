#include "InternetButton/InternetButton.h"

InternetButton b = InternetButton();

int state = 0;      // the current state of the lamp.  Possible values 0 (off), 1 (on), and 2 (fire)
int reading;           // the current reading from the input pin
int myLEDVals[12] = {50,30,20,200,10,120,40,20,50,10,100,10}; // array of flickerValues for realistic fire effect.  Use this to check to if it's ok to change LED color
int flickerTable[] = { // table with flickering times
60, 60, 50, 50, 50, 60, 70, 80, 90, 100,
240,280,320,240,250,200,300,250,250,280,
120,140,160,240,250,100,150,250,250,140,
1000,500,700,800,1300,1400,1300,1400,1300,1400,
240,230,220,100, 80,70,70, 70, 80, 80,
140,130,120,110,200,210,220,220,100, 90,
40, 30, 30, 30, 20, 10, 10 };

int lumosPin = A1; // pin for lumos
int noxPin = A2; // pin for nox
int incendioPin = A0; // pin for incendio


// The code in setup() runs once when the device is powered on or reset. Used for setting up states, modes, etc
void setup() {
    // Tell b to get everything ready to go
    // Use b.begin(1); if you have the original SparkButton, which does not have a buzzer or a plastic enclosure
    // to use, just add a '1' between the parentheses in the code below.
    pinMode(lumosPin,INPUT);
    pinMode(noxPin,INPUT);
    pinMode(incendioPin,INPUT);
    analogWrite(lumosPin,LOW);
    analogWrite(noxPin,LOW);
    analogWrite(incendioPin,LOW);    
    b.begin();
}

void lumos() {
    // turn on LEDS
   for (int i=0; i <= 11; i++){
      b.ledOn(i, 255, 255, 255);
   } 
}

void nox() {
    // turn off LEDS
   for (int i=0; i <= 11; i++){
      b.ledOff(i);
   }
}

void incendio() {
    // LED fire effect.  For each LED, check if the flicker value is zero, if not count it down.  On zero, change color and reset counter randomly.
   for (int i=0; i <= 11; i++){
        if (myLEDVals[i]>0) {
            myLEDVals[i] = myLEDVals[i]-1;
        } else {
            b.ledOff(i);
            int myVal = random(160,255);
            b.ledOn(i, myVal, myVal, 20);
            myLEDVals[i] = flickerTable[random((sizeof(flickerTable)/sizeof(int)))];
        }
   }
}

/* loop(), in contrast to setup(), runs all the time. Over and over again.
Remember this particularly if there are things you DON'T want to run a lot. Like Spark.publish() */
void loop() {   
    if (analogRead(incendioPin)>4000) {
        state = 2;
    }
    if (analogRead(lumosPin)>4000) {
        state = 1;
    }
    if (analogRead(noxPin)>4000) {
        state = 0;
    }    
    // Let's turn the LEDs on.
    if (state == 0) {
        nox();
    }
    if (state == 1) {
        lumos();
    }
    if (state == 2) {
        incendio();
    }
}
    
