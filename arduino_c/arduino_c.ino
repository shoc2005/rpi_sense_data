
#include <TimeLib.h>

#include <Time.h>
bool maintenance = true; // default mode

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
    char buffer_[100];
    int bytes = Serial.readBytesUntil('\n', buffer_, 100);
     
    String line_ = "";
    if (bytes > 0) {
      for (int i=0; i<bytes; i++){
        line_ += (String)buffer_[i];
      }
    }

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

    // if message is not "ack"
    int read_timeout=1000;
    
    String ack_msg = read_data(read_timeout);
    //Serial.println("got answ:"+ack_msg+String(ack_msg.length()));
    if (ack_msg == "ack")
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

  
  public:
  
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

  void reset_time() {
    synhronized = false;
  }

/*
  bool ckeck_triggers_ready() {
    // # check time is synchronized and both triggers ready
    if  ((shutdown_time_initialized &&  wakeup_time_initialized) && synhronized)
      return true;
    else
      return false;    
  }
*/

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
    //Serial.println((String)"Time sync: "+(String)hour(time_t_value)+":"+(String)minute(time_t_value));
    //Serial.println((String) time_t_value);
    synhronized = true;
    shutdown_time_initialized = false;
    wakeup_time_initialized = false;
  }

  time_t get_time() {
    return now();
  }

  void set_shutdown_time(time_t shut_time) {
    shutdown_time = shut_time;
    shutdown_time_initialized = true;
  }

  time_t get_shutdown_time() {
    return shutdown_time;
  }

  void set_wakeup_time(time_t wake_time) {
    wakeup_time = wake_time;
    wakeup_time_initialized = true;
  }

  time_t get_wakeup_time() {
    return wakeup_time;
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
      while (true) {
        delay(20);
        buttonState = digitalRead(buttonPin); 
        if (buttonState == HIGH &&  (millis() - time_push) >= off_delay_time) {
          event_length = off_delay_time;
          time_push = -1;
          return;
        }
        if (buttonState == LOW) {
          event_length = millis() - time_push;
          time_push = -1;
          return;          
        }
      }
      delay(10);
      return;
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
      controlState = digitalRead(controlPin); //rpi is powered
      if (controlState == HIGH) {
        if (event_length >= off_delay_time) {
          event_length = 0;
          time_push = -1;
          return 2;
        }
        else
          {
            event_length = 0;
            time_push = -1;
            return 1;
          }
          
      }
      else {
        event_length = 0;
        time_push = -1;
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
       //beep(500);
    }
  }

  int schedule_rpi_power_off(int xseconds) {
    // wait X seconds and turn off rpi power pin
    
    long int t1 = millis();
    while (true) {
      if ((millis() - t1) >= xseconds * 1000)
        break;
    }
    power_off_rpi();
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

class Communicator 
{
   // variables
   Messenger *serial_obj;
   Datetime_mini *dateTime;
   Pin_controller *pin_ctrl;

  public:
  Communicator(Datetime_mini *date_time_obj, Pin_controller *pin_control) {
    // class's constructor
    int tmp = 0;
    serial_obj = new Messenger();
    dateTime = date_time_obj;
    pin_ctrl = pin_control;
  }

  void schedule_rpi_shutdown(String msg) {
    // schedule rpi shutdown and turn off rpi power pin

    int start_index = msg.lastIndexOf(":") + 1;
    int seconds = msg.substring(start_index).toInt();
    pin_ctrl -> schedule_rpi_power_off(seconds);
    
  }

  int check_rpi_status() {
    // check status of rpi - is it online or not
    int tmp = 0;
  }

  int get_current_time() {
    serial_obj->send_message("ack");
    if (dateTime->check_sync_status()) {
      time_t curt = now();
      Serial.println(time_to_str(curt));
    }
    else
      Serial.println("Time not synchronized!");
  }
  
  String time_to_str(time_t time_) {
    // returns the current Arduino time

    String res = (String)"Year:"+(String)year(time_) + (String)" Month:"+(String)month(time_) + " Day:" + (String)day(time_) + ", " +
      (String)hour(time_) + ":" + (String)minute(time_) + ":" + (String)second(time_);
    return res;
  }

  int check_rpi_error() {
    // check rpi has been expirienced any error
    int tmp = 0;
  }

  int get_time_triggers() {
    // ask the repi for return of the next shutdown and wakeup time
    bool answ = serial_obj->send_message("trigger_time");
    if (answ) {
      while (!dateTime->check_triggers() && !maintenance) {
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
    delay(50);
    check_for_data();
    if (answ) {
      while (!dateTime->check_sync_status() && !maintenance) {
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

  int reset_ardu() {
    // reset ardu: time and triggers
    serial_obj->send_message("ack");
    dateTime->reset_triggers();
    dateTime->reset_time();
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
    time_t curt;
    String msg;
    int a;
    
    for (int i = 0; i < 3; i++){
      curt= now();
      msg = "current_status";
      a = serial_obj->send_message(msg);
      if (a)
        return 1;
    }
    return 0;
  }

  long int get_unix_time(String msg, String keyword){
    // returns unix time from from String after the keyword
    int start_index = msg.lastIndexOf(":") + 1;
    int len = msg.length();
    //Serial.println(msg.substring(start_index));
    return msg.substring(start_index).toInt();
  }

  int send_ardu_time() {
    // sends current ardu time
    serial_obj->send_message("ack");
    if (dateTime->check_sync_status()) {
      time_t curt;
      String msg;
      int a;
      
      for (int i = 0; i < 3; i++){
        curt= now();
        msg = "curr_time:" + (String)curt;
        a = serial_obj->send_message(msg);
        if (a)
          return 1;
      }

      return 0;
      
    }
  }

  void check_for_data() {
    // check any data exists in serial port

    // read until Serial buffer will be empty
    while (Serial.available()) {
      String msg = serial_obj->read_data(1000);
      //Serial.println(msg); // TEST ONLY
      if (msg.length() == 0)
        return;
    
      // check time synch message
      if (msg.startsWith("time_synch"))
      {

        time_t time_ = (time_t)get_unix_time(msg, "time_synch");
        Serial.println((String)"Time sync: " + time_to_str(time_));
        dateTime->set_current_time(time_);
        serial_obj->send_message("ack");
      }
    
      // check sleep trigger time message
      if (msg.startsWith("sleep_time"))
      {
        time_t time_ = (time_t)get_unix_time(msg, "sleep_time");
        Serial.println((String)"Shutdown Time: " + time_to_str(time_));
        dateTime->set_shutdown_time(time_);
        serial_obj->send_message("ack");
      }
    
      // check sleep trigger time message
      if (msg.startsWith("wakeup_time"))
      {
        time_t time_ = (time_t)get_unix_time(msg, "wakeup_time");
        Serial.println((String)"Wakeup Time: " + time_to_str(time_));
        dateTime->set_wakeup_time(time_);
        serial_obj->send_message("ack");
      }
  
      if (msg.startsWith("curr_time")) {
        get_current_time();
        
      }
  
      if (msg.startsWith("get_ardu_time")) {
        send_ardu_time();
      }
  
      if (msg.startsWith("enable_maint")) {
        maintenance = true;
        serial_obj->send_message("ack");
        Serial.println("Ardu in maintenance mode");
      }
  
      if (msg.startsWith("turn_off_rpi")) {
        serial_obj->send_message("ack");
        Serial.println("Rpi schedule shutdown");
        schedule_rpi_shutdown(msg);
        
      }
  
      if (msg.startsWith("disable_maint")) {
        maintenance = false;
        serial_obj->send_message("ack");
        Serial.println("Ardu exit from maintenance mode");
      }
  
      if (msg.startsWith("status")) {
        serial_obj->send_message("ack");
        int ctrlState = digitalRead(3);
        String timestr = time_to_str(now());
        Serial.println("Maintenance=" + (String)maintenance + ", RpiPower=" + (String)ctrlState + ", TimeSynh=" + dateTime->check_sync_status() + " " + timestr);
        Serial.println("Sleep time:(init=" + (String)dateTime->shutdown_time_initialized + ") "+ time_to_str(dateTime->get_shutdown_time()));
        Serial.println("Wakeup time:(init=" + (String)dateTime->wakeup_time_initialized + ") "+ time_to_str(dateTime->get_wakeup_time()));
        
      }
  
      if (msg.startsWith("reset")) {
        reset_ardu();
      }
    }
  }  
};





Messenger *msg;
Datetime_mini *ardu_time;
Communicator *serial_communicator;
Pin_controller * pin_contr; 





String serial_msg;

void check_button_pressed_() {
  // check if button pressed
  pin_contr->check_button_state();

  int button = pin_contr->check_button_type();
  if (button == 2) {
    // shutdown the rpi
    Serial.println("Rpi shutdown with Button");
    int sh_result = serial_communicator->send_rpi_shutdown();
    if (sh_result > 0) {
      pin_contr->beep(200);
      ardu_time->shutdown_done();
      Serial.println("Waiting 60 secs");
      time_t tt = now();
      while (now() - tt <= 60) {
        serial_communicator->check_for_data();
        delay(100);
      }
      pin_contr->power_off_rpi();
      pin_contr->beep(200);
      delay(200);
      pin_contr->beep(200);
      Serial.println("Rpi shutdown successfull");
    }
    else
      Serial.println("Rpi shutdown fails");
  }

  if (button == 3) {
    // turnon the rpi
    if (!maintenance) {
      ardu_time->wakeup_done();
    
    }
    pin_contr->power_on_rpi();
    pin_contr->beep(200);
    Serial.println("Rpi turned on with button");
  }

  if (button == 1) {
    serial_communicator->check_rpi_space_available();
  }  
}

void setup() {
  
   Serial.begin(9600);
   msg = new Messenger();
   ardu_time = new Datetime_mini();
   pin_contr = new Pin_controller();
   pin_contr->init_pins();

   serial_communicator = new Communicator(ardu_time, pin_contr);
}

void loop() {
  
  check_button_pressed_();
  serial_communicator->check_for_data();
  
  if (maintenance) {
    // arduino in maintenance mode
    delay(50);
    //continue;
  }
  else {
    if (ardu_time->check_sync_status()) {
      // the arduino is not in maintenance mode and time is synchronized
  
      if (ardu_time->check_triggers()) {
        // all/or single time trigger is initialized (shutdown and/or wakeup time)
  
        // check shutdown time (rpi sleep time)
        if (ardu_time->check_to_shutdown()) {
  
          // shutdown rpi and wait 60 sec until rpi shutdown
          int sh_result = serial_communicator->send_rpi_shutdown();
          if (sh_result > 0) {
            Serial.println("Waiting 60 secs");
            time_t t1 = now();
            while (now() - t1 <= 60) {
              serial_communicator->check_for_data();
              delay(100);
            }
            pin_contr->power_off_rpi();
            ardu_time->shutdown_done();
            time_t tt = now();
            Serial.println("Shutdown successfull " + serial_communicator->time_to_str(tt));
          }
          else
            //Serial.println("Shutdown fails");
          delay(50);
          
        }
  
        // check wakeup time (rpi wakeup time)
        if (ardu_time->check_to_wakeup()) {
          
          pin_contr->power_on_rpi();
          ardu_time->wakeup_done();
          time_t tt = now();
          Serial.println("Rpi turned on " + serial_communicator->time_to_str(tt));
          
        }
      }
      else // if triggers are not initialized
      {
        serial_communicator->get_time_triggers();
        //delay(50);
      }
    }
    else // if time is not synchronized
    {
      serial_communicator->get_rpi_time(); // request for time synhronization from rpi
      //delay(50);
    }
  }  

}
