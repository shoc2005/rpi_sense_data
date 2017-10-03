
#include <TimeLib.h>

#include <Time.h>

#define TIME_MSG_LEN 18 // time sync to PC is HEADER followed by Unix time_t as ten ASCII digits
#define TIME_HEADER 'TIMESYNQ' // Header tag for serial time sync message
#define TIME_REQUEST 7 // ASCII bell character requests a time sync message

class Messenger { 
  // class for low-lovel sending and receiving messages within Serial port

  public:
  Messenger() {
    int i = 0;    
    }
  String data = "";

  String read_data(int read_timeout = 100) {
    // reads data from serial, if no data in serial after read_timeout then returns empty string
    // read_timeout in miliseconds
    Serial.setTimeout(read_timeout);
    String line_ = Serial.readString();

    return line_;
  }

  bool write_data(String msg) {
    // send ack for message recieved
    // first trial
    
    long bytes = Serial.println(msg);

    // second trial
    if (msg.length() != bytes - 2) {
      bytes = Serial.println(msg);
      
    }
    
    if (msg.length() != bytes - 2)
      return false;
    else
      return true;
  }

  bool send_message(String msg) {
    bool res = write_data(msg);
    if (!res)
      return false;
    if (msg == "ack")
      return true;      
      
    int read_timeout=5000;
    String ack_msg = read_data(read_timeout);
    Serial.println("got answ:"+ack_msg+String(ack_msg.length()));
    if (ack_msg == "ack\n")
      return true;
    else
      return false;
    
    }

  bool serial_data_exists() {
    // check if data exists in serial
    
    return Serial.available();
  }

};

class Datetime_mini {
  bool synhronized = false;
  time_t shutdown_time = 0;
  time_t wakeup_time = 0;
  bool shutdown_time_initialized = false;
  bool wakeup_time_initialized = false;
  
  public:
  Datetime_mini() {
    synhronized = false;
  }

  void reset_triggers() {
    // reset all triggers: shutdown_time and wakeup_time
    shutdown_time_initialized = false;
    wakeup_time_initialized = false;
  }

  bool ckeck_triggers_ready() {
    // # check time is synchronized and both triggers ready
    if  ((shutdown_time_initialized &&  wakeup_time_initialized) && synhronized)
      return true;
    else
      return false;    
  }

  bool check_triggers() {
    // check all trigers are set up
    if  ((shutdown_time_initialized ||  wakeup_time_initialized) && synhronized)
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

  int set_current_time(time_t time_t_value) {
    setTime(time_t_value);
    Serial.println((String)"Time sync: "+(String)hour(time_t_value)+":"+(String)minute(time_t_value));
    Serial.println((String) time_t_value);
    synhronized = true;
  }

  time_t get_time() {
    return now();
  }

  void set_shutdown_time(time_t shut_time) {
    shutdown_time = shut_time;
    shutdown_time_initialized = true;
  }

  void set_wakeup_time(time_t wake_time) {
    wakeup_time = wake_time;
    wakeup_time_initialized = true;
  }

  bool check_to_shutdown() {
    // check shutdown time
    time_t current_time = now();
    if (current_time >= shutdown_time && shutdown_time_initialized && synhronized)
      return true;
    else
      return false;
  }

  bool check_to_wakeup() {
    // check wakeup time
    time_t current_time = now();
    if (current_time >= wakeup_time && wakeup_time_initialized && synhronized)
      return true;
    else
      return false;
  }  
};

class Communicator 
{
   // variables
   Messenger *serial_obj;
   Datetime_mini *dateTime;

  public:
  Communicator(Datetime_mini *date_time_obj) {
    // class's constructor
    int tmp = 0;
    serial_obj = new Messenger();
    dateTime = date_time_obj;
  }

  int check_rpi_status() {
    // check status of rpi - is it online or not
    int tmp = 0;
  }

  int check_rpi_error() {
    // check rpi has been expirienced any error
    int tmp = 0;
  }

  int get_time_triggers() {
    // ask the repi for return of the next shutdown and wakeup time
    bool answ = serial_obj->send_message("trigger_time");
    if (answ) {
      while (!dateTime->ckeck_triggers_ready()) {
        check_for_data();
        delay(50);   
      }
      return 1;
    }
    return -1;
  }

  int get_rpi_time() {
    // ask the repi for return of the next shutdown and wakeup time
    bool answ = serial_obj->send_message("curr_time");
    if (answ) {
      while (!dateTime->check_sync_status()) {
        check_for_data();
        delay(50);
      }
    }
  }

  int send_rpi_shutdown() {
    // send messaga for rpi shutdown
    
    if (serial_obj->send_message("shutdown")) {
      delay(60);

      //** TURN OFF PIN **
      return 1;
    }
    else
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

  long int get_unix_time(String msg, String keyword){
    // returns unix time from from String after the keyword
    int start_index = msg.lastIndexOf(":") + 1;
    int len = msg.length();
    Serial.println(msg.substring(start_index));
    return msg.substring(start_index).toInt();
  }

  void check_for_data() {
    // check any data exists in serial port
    String msg = serial_obj->read_data();

    if (msg.length() == 0)
      return;
  
    // check time synch message
    if (msg.startsWith("time_synch"))
    {
      time_t time_ = (time_t)get_unix_time(msg, "time_synch");
      dateTime->set_current_time(time_);
      serial_obj->send_message("ack");
    }
  
    // check sleep trigger time message
    if (msg.startsWith("sleep_time"))
    {
      time_t time_ = (time_t)get_unix_time(msg, "sleep_time");
      dateTime->set_shutdown_time(time_);
      serial_obj->send_message("ack");
    }
  
    // check sleep trigger time message
    if (msg.startsWith("wakeup_time"))
    {
      time_t time_ = (time_t)get_unix_time(msg, "wakeup_time");
      dateTime->set_wakeup_time(time_);
      serial_obj->send_message("ack");
    }
  }  
};




class Pin_controller {
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


String serial_msg;

void check_button_pressed_() {
  // check if button pressed
  pin_contr->check_button_state();

  int button = pin_contr->check_button_type();
  if (button == 2) {
    // shutdown the rpi
    int sh_result = serial_communicator->send_rpi_shutdown();
    if (sh_result > 0) {
      Serial.println("Rpi shutdown successfull");
      ardu_time->shutdown_done();
      pin_contr->power_off_rpi();
      pin_contr->beep(200);
      delay(200);
      pin_contr->beep(200);
    }
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

void setup() {
  
   Serial.begin(9600);
   msg = new Messenger();
   ardu_time = new Datetime_mini();
   serial_communicator = new Communicator(ardu_time);
   pin_contr = new Pin_controller();
   pin_contr->init_pins();
}

void loop() {

  check_button_pressed_();
  serial_communicator->check_for_data();
  
  if (maintenance) {
    // arduino in maintenance mode
    delay(50);
    //continue;
  }

  if (ardu_time->check_sync_status()) {
    // the arduino is not in maintenance mode and time is synchronized

    if (ardu_time->check_triggers()) {
      // all time triggers are initialized (shutdown and wakeup time)

      // check shutdown time (rpi sleep time)
      if (ardu_time->check_to_shutdown()) {

        // shutdown rpi and wait 60 sec until rpi shutdown
        int sh_result = serial_communicator->send_rpi_shutdown();
        if (sh_result > 0) {
          pin_contr->power_off_rpi();
          ardu_time->shutdown_done();
          time_t tt = now();
          Serial.println("Shutdown successfull"+(String)hour(tt)+":"+(String)minute(tt));
        }
        else
          //Serial.println("Shutdown fails");
        delay(50);
        
      }

      // check wakeup time (rpi wakeup time)
      if (ardu_time->check_to_wakeup()) {
        ardu_time->wakeup_done();
        pin_contr->power_on_rpi();
        time_t tt = now();
        Serial.println("Rpi turned on"+(String)hour(tt)+":"+(String)minute(tt));
        
      }
    }
    else // if triggers are not initialized
    {
      serial_communicator->get_time_triggers();
      delay(50);
    }
  }
  else // if time is not synchronized
  {
    serial_communicator->get_rpi_time(); // request for time synhronization from rpi
  }
  

}
