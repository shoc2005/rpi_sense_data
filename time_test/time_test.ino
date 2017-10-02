
#include <TimeLib.h>

#include <Time.h>

#define TIME_MSG_LEN 18 // time sync to PC is HEADER followed by Unix time_t as ten ASCII digits
#define TIME_HEADER 'TIMESYNQ' // Header tag for serial time sync message
#define TIME_REQUEST 7 // ASCII bell character requests a time sync message

class Datetime_mini {
  bool synhronized;
  time_t shutdown_time = 0;

  Datetime_mini() {
    synhronized = false;
  }

  int set_time(time_t time_t_value) {
    setTime(time_t_value);
  }

  time_t get_time() {
    return now();
  }

  void set_shutdown_time(time_t shut_time) {
    shutdown_time = shut_time;
  }

  bool check_to_shutdown() {
    time_t current_time = now();
    if (current_time >= shutdown_time && synhronized)
      return true;
    else
      return false;
  }
};

class Messenger { 
  // class for sending and receiving messages within Serial port

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

  bool serial_data_exists() {
    // check if data exists in serial
    
    return Serial.available();
  }

  String send_message(String message) {
    Serial.print(message);
    }

};

Messenger *msg;

void setup() {
  
   Serial.begin(9600);
   msg = new Messenger();
}

String serial_msg;

void loop() {

  if  (msg->serial_data_exists()) {
    serial_msg =  msg->read_data();
    Serial.println((unsigned int)&serial_msg, HEX);
    Serial.println(serial_msg);
    if (serial_msg == "")
      Serial.println("read timeout");
  }
  else
    Serial.println("No msg");
    
  delay(1000);
  
}
