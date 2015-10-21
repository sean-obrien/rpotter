/*
* A slightly modified version of arduino crossfade code by 
* Clay Shirky.  
* 
* Modifed to allow for random fades and pin trigger.
*/ 

// Output
int redPin = PB0;   // Red LED,   connected to digital pin 9
int grnPin = PB1;  // Green LED, connected to digital pin 10
int bluPin = PB2;  // Blue LED,  connected to digital pin 11
int trigPin = PB4;

// Color arrays
int black[3]  = { 100, 100, 100 };
int white[3]  = { 0, 0, 0 };
int red[3]    = { 0, 100, 100 };
int fuscia[3]  = { 0, 100, 0 };
int green[3]  = { 100, 0, 100 };
int blue[3]   = { 100, 100, 0 };
int aqua[3]   = { 100, 0, 0 };
int yellow[3] = { 60, 5, 100 };
int orange[3] = { 0, 0, 100 };
int dimWhite[3] = { 40, 40, 40 };
// etc.

// Set initial color
int redVal = black[0];
int grnVal = black[1]; 
int bluVal = black[2];

int wait = 1;      // 10ms internal crossFade delay; increase for slower fades
int hold = 0;       // Optional hold when a color is complete, before the next crossFade
int DEBUG = 1;      // DEBUG counter; if set to 1, will write values back via serial
int loopCount = 60; // How often should DEBUG report?
int repeat = 0;     // How many times should we loop before stopping? (0 for no stop)
int j = 0;          // Loop counter for repeat
int val = 0;

// Initialize color variables
int prevR = redVal;
int prevG = grnVal;
int prevB = bluVal;

//color Array
int* colors[9]   = {white,red,fuscia,blue,aqua,green,yellow,orange};

// Set up the LED outputs
void setup()
{
  pinMode(redPin, OUTPUT);   // sets the pins as output
  pinMode(grnPin, OUTPUT);   
  pinMode(bluPin, OUTPUT); 
  pinMode(trigPin, INPUT);
  crossFade(green);
}

// Main program: list the order of crossfades
void loop()
{
  //crossFade(red);
  //crossFade(blue);
  //crossFade(yellow);
  val = digitalRead(trigPin);
  if (val==HIGH) {
       //do noting.. just go 'roind and round this
       //    inner loop until button pressed again
     //int randColor[3] = {colors[0][random (0, 9)]};
     //crossFade(randColor);
      int randColor[3] = {random (0, 100),random (0, 100),random (0, 100)};
      crossFade(randColor);
      delay(1000);
  }// end of main loop

}

/* BELOW THIS LINE IS THE MATH -- YOU SHOULDN'T NEED TO CHANGE THIS FOR THE BASICS
* 
* The program works like this:
* Imagine a crossfade that moves the red LED from 0-10, 
*   the green from 0-5, and the blue from 10 to 7, in
*   ten steps.
*   We'd want to count the 10 steps and increase or 
*   decrease color values in evenly stepped increments.
*   Imagine a + indicates raising a value by 1, and a -
*   equals lowering it. Our 10 step fade would look like:
* 
*   1 2 3 4 5 6 7 8 9 10
* R + + + + + + + + + +
* G   +   +   +   +   +
* B     -     -     -
* 
* The red rises from 0 to 10 in ten steps, the green from 
* 0-5 in 5 steps, and the blue falls from 10 to 7 in three steps.
* 
* In the real program, the color percentages are converted to 
* 0-255 values, and there are 1020 steps (255*4).
* 
* To figure out how big a step there should be between one up- or
* down-tick of one of the LED values, we call calculateStep(), 
* which calculates the absolute gap between the start and end values, 
* and then divides that gap by 1020 to determine the size of the step  
* between adjustments in the value.
*/

int calculateStep(int prevValue, int endValue) {
  int step = endValue - prevValue; // What's the overall gap?
  if (step) {                      // If its non-zero, 
    step = 1020/step;              //   divide by 1020
  } 
  return step;
}

/* The next function is calculateVal. When the loop value, i,
*  reaches the step size appropriate for one of the
*  colors, it increases or decreases the value of that color by 1. 
*  (R, G, and B are each calculated separately.)
*/

int calculateVal(int step, int val, int i) {

  if ((step) && i % step == 0) { // If step is non-zero and its time to change a value,
    if (step > 0) {              //   increment the value if step is positive...
      val += 1;           
    } 
    else if (step < 0) {         //   ...or decrement it if step is negative
      val -= 1;
    } 
  }
  // Defensive driving: make sure val stays in the range 0-255
  if (val > 255) {
    val = 255;
  } 
  else if (val < 0) {
    val = 0;
  }
  return val;
}

/* crossFade() converts the percentage colors to a 
*  0-255 range, then loops 1020 times, checking to see if  
*  the value needs to be updated each time, then writing
*  the color values to the correct pins.
*/

void crossFade(int color[3]) {
  // Convert to 0-255
  int R = (color[0] * 255) / 100;
  int G = (color[1] * 255) / 100;
  int B = (color[2] * 255) / 100;

  int stepR = calculateStep(prevR, R);
  int stepG = calculateStep(prevG, G); 
  int stepB = calculateStep(prevB, B);

  for (int i = 0; i <= 1020; i++) {
    redVal = calculateVal(stepR, redVal, i);
    grnVal = calculateVal(stepG, grnVal, i);
    bluVal = calculateVal(stepB, bluVal, i);

    analogWrite(redPin, redVal);   // Write current values to LED pins
    analogWrite(grnPin, grnVal);      
    analogWrite(bluPin, bluVal); 

    delay(wait); // Pause for 'wait' milliseconds before resuming the loop
  }
  // Update current values for next loop
  prevR = redVal; 
  prevG = grnVal; 
  prevB = bluVal;
  delay(hold); // Pause for optional 'wait' milliseconds before resuming the loop
}
