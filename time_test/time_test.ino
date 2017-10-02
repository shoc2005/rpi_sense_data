
#include <TimeLib.h>

#include <Time.h>

#define TIME_MSG_LEN 18 // time sync to PC is HEADER followed by Unix time_t as ten ASCII digits
#define TIME_HEADER 'TIMESYNQ' // Header tag for serial time sync message
#define TIME_REQUEST 7 // ASCII bell character requests a time sync message

class Datetime_mini {
  bool synhronized = false;
  time_t shutdown_time = 0;
  time_t wakeup_time = 0;
  bool shutdown_time_initialized = false;
  bool wakeup_time_initialized = false;
  

  Datetime_mini() {
    synhronized = false;
  }

  void reset_triggers() {
    // reset all triggers: shutdown_time and wakeup_time
    shutdown_time_initialized = false;
    wakeup_time_initialized = false;
  }

  void check_triggers() {
    // check all trigers are set up
    if  (shutdown_time_initialized ||  wakeup_time_initialized)
      return true;
    else
      return false;
  }

  void shutdown_done() {
    shutdown_time_initialized = false;
  }

  void wakeup_done() {
    wakeup_time_initialized = false;
  }  

  bool check_sync_status() {
    // check is time synchronized or not

    return synhronized;
  }

  int set_time(time_t time_t_value) {
    setTime(time_t_value);
    synhronized = true;
  }

  time_t get_time() {
    return now();
  }

  void set_shutdown_time(time_t shut_time) {
    shutdown_time = shut_time;
  }

  void wakeup_time_initialized(time_t wake_time) {
    wakeup_time = wake_time;
  }

  bool check_to_shutdown() {
    // check shutdown time
    time_t current_time = now();
    if (current_time >= shutdown_time && shutdown_time_initialized)
      return true;
    else
      return false;
  }

  bool check_to_wakeup() {
    // check wakeup time
    time_t current_time = now();
    if (current_time >= wakeup_time && wakeup_time_initialized)
      return true;
    else
      return false;
  }  
};

class Communicator 
{
   // variables
   Messenger *serial_obj;

  public:
  Communicator() {
    // class's constructor
    int tmp = 0;
    serial_obj = new Messenger();
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

  int send_rpi_shutdown() {
    // send messaga for rpi shutdown
    
    if (serial_obj->send_message("shutdown")) {
      delay(60);

      //** TURN OFF PIN **
      return 1;
    }

    return 0;
      
  }

  int get_next_shutdown() {
    // get next shutdown date and time from the rpi
    if (serial_obj->send_message("trigger_time"));
    
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

    void check_for_data() {
    // check any data exists in serial port
    String msg = serial_obj->read_data();
    if (msg.startsWith("time_synch")) {
      // rpi send time synch message

      // get time string
      int start_index = msg.lastIndexOf("time_synch");
      long int = (int)(msg.substring(start_index));
    }
  }
};


class Messenger { 
  // class for low-lovel sending and receiving messages within Serial port

  public:
  Messenger() {
    int i = 0;    
    }
  String data = "";

  String read_line() {
    // data from serial port until termination symbol detected - new line
    
    int counter =0;

    data = "";

    while (Serial.available()) {
      char c = Serial.read();
      if (c == '\n' || counter >= 50)
        break;
      data += String(c);
    }

    return data;
  }

  String read_data(int read_timeout = 100) {
    // reads data from serial, if no data in serial after read_timeout then returns empty string
    // read_timeout in miliseconds
    
    long int t1 = millis();
    String data = "";

    while(data == "") {
      if  ((millis() - t1) >= read_time_out) {
        break;
      }
      data = read_line();
      
    }

    return data;
  }

  bool write_data(String msg) {
    // send ack for message recieved
    // first trial
    
    int bytes = Serial.write(msg);

    // second trial
    if (length(msg) != bytes) {
      bytes = Serial.write(msg);
    }
    
    if (length(msg) != bytes)
      return false;
    else
      return true;
  }

  bool send_message(String msg) {

    bool send_result = send_msg(msg);
    if (!send_result)
      return false;

    ack_msg = read_data(read_timeout=500);
    if (ack_msg == "ack")
      return true;
    else
      return false;
    
    }

  bool serial_data_exists() {
    // check if data exists in serial
    
    return Serial.available();
  }

  String send_message(String message) {
    Serial.print(message);
    }

};

class Pin_controller() {
  const int controlPin =  3;  // turn power for the RPI
  const int buttonPin =  5; // check button pressed on the Arduino
  const int beepPin =  2; // beeper pin
  int buttonState; // push button' state
  int controlState; // the rpi VCC pin's state

  long int time_push = -1;
  long int event_length = 0;
  int release_time = 0;
  bool released = true;
  int off_delay_time = 5000;
  
  public:
    Pin_controller() {
      
    }

  void init_pins() {
    pinMode(LED_BUILTIN, OUTPUT);
    pinMode(controlPin, OUTPUT);
    pinMode(buttonPin,  INPUT);
    pinMode(beepPin, OUTPUT);
  }

  void check_button_state() {
    // check button state
    buttonState = digitalRead(buttonPin);
    controlState = digitalRead(controlPin);
    if (buttonState == HIGH && time_push == -1) {
      // the button pressed now
      event_length = 0;
      time_push = millis();
      return;
    }

    if (time_push > 0) {
      // button has been pressed

      // check maximal time for hold
      if ((millis() - time_push) >= off_delay_time) {
        // shutdown rpi after 5 second than button has been pressed
        event_length = off_delay_time;
        time_push = -1;
        return;
      }
      
      if (controlState == LOW) {
        event_length = millis() - time_push;
        time_push = -1;
        return;
      }

    }
  }

  bool check_button_pressed() {
    // check if the button is pressed
    if (event_length > 0)
      return true;
    else
      return false;
  }

  int check_button_type() {
    // 0 - nothing happen
    // 1 - get RPI status
    // 2 - turn off RPI
    // 3 - turn on RPI

    if (check_button_pressed()) {
      controlState = digitalRead(controlPin);
      if (controlState == HIGH) {
        if (event_length >= off_delay_time) 
          return 2;
        else
          return 1;
      }
      else {
        return 3;
      }
    }
    else
      return 0;
  }

  int power_on_rpi() {
    // power on the rpi
    
    controlState = digitalRead(controlPin);
    if (controlState == LOW) {
      digitalWrite(controlPin, HIGH);
    }

  int power_off_rpi() {
    // power off the rpi

    controlState = digitalRead(controlPin);
    if (controlState == HIGH) {
      digitalWrite(controlPin, LOW);
       beep(500);
    }
  }

  void beep(int interval) {
    // make beep
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
  
  
};

Messenger *msg;
Datetime_mini *ardu_time;
Communicator *serial_communicator;
Pin_controller * pin_contr; 


bool maintenance = true; // default mode

void setup() {
  
   Serial.begin(9600);
   msg = new Messenger();
   ardu_time = new Datetime_mini();
   serial_communicator = new Communicator();
   pin_contr = new Pin_controller();
   pin_contr->init_pins();

String serial_msg;

void check_button_pressed() {
  // check if button pressed
  pin_contr->check_button_state();

  int button = pin_contr->check_button_type();
  if (button == 2) {
    // shutdown the rpi
    int sh_result = serial_communicator->send_rpi_shutdown();
    if (sh_result > 0)
      Serial.println("Rpi shutdown successfull");
      ardu_time->shutdown_done();
      pin_contr->power_off_rpi();
      pin_contr->beep(200);
      delay(200);
      pin_contr->beep(200);
    else
      Serial.println("Rpi shutdown fails");
  }

  if (button == 3) {
    // turnon the rpi
    pin_contr->power_on_rpi();
    pin_contr->beep(200);
    Serial.println("Rpi turned on");
  }

  if (button == 1) {
    serial_communicator->check_rpi_status();
  }  
}

void loop() {

  check_button_pressed();
  
  if (maintenance) {
    // arduino in maintenance mode
    serial_communicator->check_for_data();
    delay(20);
    continue;
  }

  if (ardu_time->check_sync_status()) {
    // the arduino is not in maintenance mode and time is synchronized

    if (ardu_time->check_triggers()) {
      // all time triggers are initialized (shutdown and wakeup time)

      // check shutdown
      if (ardu_time ->check_to_shutdown()) {

        // shutdown rpi and wait 60 sec until rpi shutdown
        int sh_result = serial_communicator->send_rpi_shutdown();
        if (sh_result > 0)
          pin_contr->power_off_rpi();
          ardu_time->shutdown_done();
          Serial.println("Shutdown successfull");
        else
          Serial.println("Shutdown fails");
        
      }

      // check wakeup
      if (ardu_time ->check_to_wakeup()) {
        pin_contr->power_on_rpi();
        if (sh_result > 0)
          Serial.println("Rpi turned on");
          ardu_time->shutdown_done();
        else
          Serial.println("Rpi turning on fails");
        
      }
      
    }
    
    else
    
    {
      serial_communicator->check_for_data();
    }
  }
  else
    serial_communicator->check_for_data();

}
