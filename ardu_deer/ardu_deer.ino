/*

*/

#include <Time.h>

// the setup function runs once when you press reset or power the board

const int controlPin =  3;      // the number of the Control pin
const int buttonPin =  5;
const int beepPin =  2;

int buttonState;
int controlState;
long int time_push = -1;
int release_time = 0;
bool released = true;
int off_delay_time = 5000;


class Communicator 
{
   // variables

  public:
  Communicator() {
    // class's constructor
    int tmp = 0;
  }

  int check_rpi_status() {
    // check status of rpi - is it online or not
    int tmp = 0;
  }

  int check_rpi_error() {
    // check rpi has been expirienced any error
    int tmp = 0;
  }

  int get_clock() {
    // get current time from the rpi, time and date
    int tmp = 0;
  }

  int get_next_shutdown() {
    // get next shutdown date and time from the rpi
    int tmp = 0;
  }

  int set_rpi_clock() {
    // set current date and time for the rpi
    int tmp = 0;
  }

  int check_rpi_space_available() {
    // check how many space are available in the rpi
    // 1 - <= 25%
    // 2 - > 25% and < 50%
    // 3 - > 50%
    // 0 - can't get data from rpi
    int tmp = 0;
  }
};


void setup() {
  // initialize digital pin LED_BUILTIN as an output.
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(controlPin, OUTPUT);
  pinMode(buttonPin,  INPUT);
  pinMode(beepPin, OUTPUT);
  Serial.begin(9600);
}

void beep(int interval) {
  digitalWrite(beepPin, LOW);
  long int t1 = millis();
  while (true) {
    if ((millis() - t1) >= interval) {
      break;
    }
    else {
      digitalWrite(beepPin, HIGH);
      delay(20);
      digitalWrite(beepPin, LOW);
    }
    
  }
  digitalWrite(beepPin, LOW);
}

// the loop function runs over and over again forever
void loop() {
  buttonState = digitalRead(buttonPin);
  controlState = digitalRead(controlPin);

  if (buttonState == HIGH && released) {
    time_push = millis(); 
    while (true) {
      buttonState = digitalRead(buttonPin);
      //Serial.println(millis() - time_push);
      if ((buttonState == LOW) || ((millis() - time_push) >= off_delay_time)){
        release_time = millis() - time_push;
        
        if (buttonState == LOW) {
          released = true;
        }
        else {
          released = false;
        }
        
        break;
      }
      delay(10);
    }

   if ((controlState == LOW)) {
    digitalWrite(controlPin, HIGH);
    Serial.println("Turned on");
    beep(100);
    release_time = -1;
    }
  }
  buttonState = digitalRead(buttonPin);
  if (buttonState == LOW ) {
        released = true;
        
  }
    
  if (release_time >= off_delay_time) {
    // check rpi is off and not communicate within serial
    String ack = "";
    Serial.setTimeout(4000);
    
    while (true) {
      Serial.println("hi");
      delay(100);
      
      ack = Serial.readString();
      Serial.println(ack);
      if (ack == "hi") {
        beep(10);
      }
      else {
        break;
      }
    }
    
    digitalWrite(controlPin, LOW);
    Serial.println("Turned off");
    beep(200);
    delay(200);
    beep(100);
    release_time = -1;
    
  }
  delay(10);
 }
  


