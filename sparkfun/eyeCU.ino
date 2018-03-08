#include <SparkFunCCS811.h>
#include <SparkFunBME280.h>
#include "Wire.h"
#include <SparkFunTSL2561.h>
#include <ESP8266WiFi.h>

#define SOUND_GATE_IN 4
#define SOUND_ANALOG_IN A0
#define PIR_IN 5
#define BUTTON 15
#define CCS811_ADDR 0x5B

// Global variables:

boolean gain;     // Gain setting, 0 = X1, 1 = X16;
unsigned int ms;  // Integration ("shutter") time in milliseconds
const char ssid[] = "UCB Wireless";
const char password[] = "";
int buttonPressed = 0;
int motionDetected = 0;

CCS811 myCCS811(CCS811_ADDR);
BME280 bme;
SFE_TSL2561 light;

void setup() {

  
  
  pinMode(BUTTON, INPUT); // Red button
  
  Serial.begin(9600);
  Serial.println("Started Serial, running connectWiFi");

 /* IPAddress ip(192, 168, 20, 86);
  IPAddress gateway(192, 168, 20, 1);
  IPAddress subnet(255, 255, 255, 0);
  WiFi.config(ip, gateway, subnet); */
  
  connectWiFi();
  Serial.println("exited connectWiFi");


  /////////////// PIR Sensor Setup ///////////////

  pinMode(PIR_IN, INPUT);
 
  /////////////// Luminosity Sensor Setup ///////////////
  
  pinMode(SOUND_GATE_IN, INPUT);
  light.begin();
  gain = 0;
  
  unsigned char time = 2;

  light.setTiming(gain,time,ms);

  light.setPowerUp();

  /////////////// Environment Sensor Setup ///////////////
    
  bme.settings.commInterface = I2C_MODE;
  bme.settings.I2CAddress = 0x77;
  bme.settings.runMode = 3; // Normal mode
  bme.settings.tStandby = 0; // 0.5ms
  bme.settings.filter = 0; // Filter Off
  bme.settings.tempOverSample = 1;
  bme.settings.pressOverSample = 1;
  bme.settings.humidOverSample = 1;

  delay(10);  //Make sure sensor had enough time to turn on. BME280 requires 2ms to start up.
  byte id = bme.begin(); //Returns ID of 0x60 if successful
  if (id != 0x60)
  {
    Serial.println("Problem with BME280");
  }
  else
  {
    Serial.println("BME280 online");
  }
   
  CCS811Core::status returnCode = myCCS811.begin();
  if (returnCode != CCS811Core::SENSOR_SUCCESS)
  {
    Serial.println("Problem with CCS811");
    printDriverError(returnCode);
  }
  else
  {
    Serial.println("CCS811 online");
  }
  
}

void loop() {

   delay(1000); //Wait for next reading


 
  
  /////////////// Button ///////////////

  if(digitalRead(BUTTON) == HIGH){
    buttonPressed = 1;
    Serial.println("Button Pressed!");

  }

  /////////////// PIR Sensor Data ///////////////

  int proximity = digitalRead(PIR_IN);
  if (proximity == LOW) // If the sensor's output goes low, motion is detected
  {
    Serial.println("Motion detected!");
    motionDetected = 1;
  }

  /////////////// Sound Sensor Data ///////////////

  int soundLevel;

  // Check the envelope input
  soundLevel = analogRead(SOUND_ANALOG_IN);
  Serial.print("RAW SOUND LEVEL:" );
  Serial.println(soundLevel);

  // Convert envelope soundLevel into a message
  
  
 /* Serial.print("Status: ");
  if(soundLevel <= 80)
  {
    Serial.println("Quiet.");
  }
  else if( (soundLevel > 80) && ( soundLevel <= 100) )
  {
    Serial.println("Moderate.");
  }
  else if(soundLevel > 100)
  {
    Serial.println("Loud.");
  }*/

  delay(1000); //not sure why this is here, but afraid to mess with it

  /////////////// Luminosity Sensor Data ///////////////

  unsigned int dataIR, datVIS;
  double lux;
  if (light.getData(dataIR,datVIS))
  {
    // getData() returned true, communication was successful
    
    Serial.print("IR Light: ");
    Serial.print(dataIR);
    Serial.print(" Visibile: "); //1 lumen/m^2
    Serial.print(datVIS);
  
        // Resulting lux value
    boolean good;  // True if neither sensor is saturated

    good = light.getLux(gain,ms,dataIR,datVIS,lux);
    
    Serial.print(" lux: ");
    Serial.print(lux);
    if (good) Serial.println(" (Not Saturated)"); else Serial.println(" (Saturated [adjust sensor])");
  }
  else
  {
    // getData() returned false because of an I2C error, inform the user.
    byte error = light.getError();
    printError(error);
  }

  /////////////// Environment Sensor Data ///////////////
  
  float tempC = bme.readTempC();
  float pressure = bme.readFloatPressure();
  float altitude = bme.readFloatAltitudeFeet();
  float humidity = bme.readFloatHumidity();

  Serial.print("Temperature: ");
  Serial.println(tempC);
  Serial.print("Pressure: ");
  Serial.println(pressure);
  Serial.print("Altitude: ");
  Serial.println(altitude);
  Serial.print("Humidity: ");
  Serial.println(humidity);

 if (myCCS811.dataAvailable())
  {
    //Calling this function updates the global tVOC and eCO2 variables
    myCCS811.readAlgorithmResults();
    //printData fetches the values of tVOC and eCO2
    Serial.print("CO2: ");
    Serial.print(myCCS811.getCO2());
    Serial.println(" ppm");

    Serial.print("TVOC: ");
    Serial.print(myCCS811.getTVOC());
    Serial.println(" ppb");

    //This sends the temperature data to the CCS811
    myCCS811.setEnvironmentalData(humidity, tempC);
  }
  else if (myCCS811.checkForStatusError())
  {
    Serial.println(myCCS811.getErrorRegister()); //Prints whatever CSS811 error flags are detected
  }


//////////// Connecting to Back End /////////
  if(WiFi.status() != WL_CONNECTED){
    ESP.reset();
   
  }

  String url = "http://128.138.75.7";
  //Serial.println(host + url + data);
  WiFiClient client;
  const int httpPort = 80;
  if (!client.connect("128.138.75.7", httpPort)) {
    Serial.println("connection failed");
    
    return;
  }

  /////////////// POST Request to Server ///////////////

  String data = "temperature=" + String(tempC) + "&humidity=" + String(humidity)
       + "&pressure=" + String(pressure) + "&altitude=" + String(altitude) + 
       "&co2=" + String(myCCS811.getCO2()) + "&voc=" + String(myCCS811.getTVOC()) +
       "&light=" + String(lux) + "&sound=" + String(soundLevel) +
       "&button=" + String(buttonPressed) + "&motion=" + String(digitalRead(PIR_IN)) +
       "&MAC=" + String(WiFi.macAddress());

  


  client.print(String("POST ")   + "/ HTTP/1.1\r\n" +  
               "Host: " + "128.138.75.7" + "\r\n" + 
               "User-Agent: eyeCU-IoT-Device" + "\r\n" +
               "Accept: */*" + "\r\n" +
               "Content-Length: " + data.length() + "\r\n" +
               //"Connection: close" + "\r\n" + 
               "Content-Type: application/x-www-form-urlencoded\r\n\r\n"  + data + "\n");

   // Serial.println(String("POST ")   + "/ HTTP/1.1\r\n" +
    //           "Host: " + "128.138.75.7" + "\r\n" + 
    //           "User-Agent: eyeCU-IoT-Device" + "\r\n" +
    //           "Accept: */*" + "\r\n" +
    //           "Content-Length: " + data.length() + "\r\n" +
              // "Connection: close" + "\r\n" + 
     //          "Content-Type: application/x-www-form-urlencoded\r\n\r\n"  + data + "\n");  //sanity check on our end


            
  buttonPressed = 0; //Reset button status for next time around the loop
  motionDetected = 0; //Reset motion status a well.
  delay(300000); //wait 5 minutes before next reading
 

}

/////////////// Helper Functions ///////////////

void printDriverError( CCS811Core::status errorCode )
{
  switch ( errorCode )
  {
    case CCS811Core::SENSOR_SUCCESS:
      Serial.print("SUCCESS");
      break;
    case CCS811Core::SENSOR_ID_ERROR:
      Serial.print("ID_ERROR");
      break;
    case CCS811Core::SENSOR_I2C_ERROR:
      Serial.print("I2C_ERROR");
      break;
    case CCS811Core::SENSOR_INTERNAL_ERROR:
      Serial.print("INTERNAL_ERROR");
      break;
    case CCS811Core::SENSOR_GENERIC_ERROR:
      Serial.print("GENERIC_ERROR");
      break;
    default:
      Serial.print("Unspecified error.");
  }
}

void printError(byte error)
  // If there's an I2C error, this function will
  // print out an explanation.
{
  Serial.print("I2C error: ");
  Serial.print(error,DEC);
  Serial.print(", ");
  
  switch(error)
  {
    case 0:
      Serial.println("success");
      break;
    case 1:
      Serial.println("data too long for transmit buffer");
      break;
    case 2:
      Serial.println("received NACK on address (disconnected?)");
      break;
    case 3:
      Serial.println("received NACK on data");
      break;
    case 4:
      Serial.println("other error");
      break;
    default:
      Serial.println("unknown error");
  }
}

// IP Address of the backend server is 128.138.75.7

void connectWiFi()
{
  byte ledStatus = LOW;
  Serial.println();
  Serial.println("Connecting to: " + String(ssid));
  // Set WiFi mode to station (as opposed to AP or AP_STA)
  WiFi.mode(WIFI_STA);

  // WiFI.begin([ssid], [passkey]) initiates a WiFI connection
  // to the stated [ssid], using the [passkey] as a WPA, WPA2,
  // or WEP passphrase.
  WiFi.begin(ssid, password);

  // Use the WiFi.status() function to check if the ESP8266
  // is connected to a WiFi network.
  while (WiFi.status() != WL_CONNECTED)
  {
    // Blink the LED
    ledStatus = (ledStatus == HIGH) ? LOW : HIGH;

    // Delays allow the ESP8266 to perform critical tasks
    // defined outside of the sketch. These tasks include
    // setting up, and maintaining, a WiFi connection.
    delay(100);
    // Potentially infinite loops are generally dangerous.
    // Add delays -- allowing the processor to perform other
    // tasks -- wherever possible.
  }
  Serial.println("WiFi connected");  
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}


