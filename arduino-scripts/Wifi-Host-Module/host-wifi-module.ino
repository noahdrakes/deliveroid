///Host Wifi Module (Sender

#include <ESP8266WiFi.h>
#include <espnow.h>

String last_value;
char my_string[30];
String string_data = "";


// REPLACE WITH THE MAC Address of your receiver 
uint8_t broadcastAddress[] = {0x8C, 0xAA, 0xB5, 0x50, 0xFA, 0x57};

unsigned long lastTime = 0;  
unsigned long timerDelay = 200;  // send readings timer

//this variable will determine what state the robot is in 

char state1[4];

// Variable to store if sending data was successful
String success;

//Structure example to send data
//Must match the receiver structure
typedef struct send_message {
    char ste1[4];

 
} send_message;



// Create a struct_message to hold directions to send to deliveroid
send_message apriltag;

// Create a struct_message to hold incoming value from the deliveroid


// Callback when data is sent
void OnDataSent(uint8_t *mac_addr, uint8_t sendStatus) {
  Serial.print("Last Packet Send Status: ");
  if (sendStatus == 0){
    Serial.println("Delivery success");
  }
  else{
    Serial.println("Delivery fail");
  }
}


//////////////////This is where we'll do apriltag calculations//////////////////////////
void aprilcalc(){
 while(Serial.available() > 2){
      Serial.println("inside april tag method");
      string_data = Serial.readString();
      Serial.println(string_data[0]);
      Serial.println(string_data[1]);
      Serial.println(string_data[2]);
      }
  
 state1[0]=string_data[0];
 state1[1]=string_data[1];
 state1[2]=string_data[2];
 
  
}


 
void setup() {
  // Init Serial Monitor
  Serial.begin(115200);

 
 
  // Set device as a Wi-Fi Station
  WiFi.mode(WIFI_STA);

  Serial.println("");
  Serial.println("");
  Serial.println("");
  Serial.println("");
  Serial.println(WiFi.macAddress());


  // Init ESP-NOW
  if (esp_now_init() != 0) {
    Serial.println("Error initializing ESP-NOW");
    return;
  }

  // Set ESP-NOW Role
  esp_now_set_self_role(ESP_NOW_ROLE_CONTROLLER);

  esp_now_register_send_cb(OnDataSent);
  
  
  
}
 
void loop() {

  
   if ((millis() - lastTime) > timerDelay) {
    
     aprilcalc();

    //Set values to send
    strcpy(apriltag.ste1, state1);
    

    // Send message via ESP-NOW
    esp_now_send(broadcastAddress, (uint8_t *) &apriltag, sizeof(apriltag));

 lastTime = millis();
  }
}
 
