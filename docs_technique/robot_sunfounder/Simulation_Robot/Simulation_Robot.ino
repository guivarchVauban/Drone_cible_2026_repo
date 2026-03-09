#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pca9685 = Adafruit_PWMServoDriver(0x40);

/************* CONSTANTES *************/

// Channels PCA9685
const uint8_t SERVO_CH = 0;
const uint8_t PWMA_CH  = 4;
const uint8_t PWMB_CH  = 5;

// Broches direction L298N
const uint8_t IN1 = 2;
const uint8_t IN2 = 3;
const uint8_t IN3 = 8;
const uint8_t IN4 = 9;

// Servo
const uint16_t SERVO_MIN = 123; 
const uint16_t SERVO_MAX = 492;

// PWM moteur
const uint16_t PWM_MAX = 4095;

/*************************************/

String input = "";

/************* FONCTIONS *************/

void setMotor1(int speed)
{
  bool forward = speed >= 0;
  speed = abs(speed);

  speed = constrain(speed,0,255);

  uint16_t pwm = map(speed,0,255,0,PWM_MAX);

  digitalWrite(IN1, forward);
  digitalWrite(IN2, !forward);

  pca9685.setPWM(PWMA_CH,0,pwm);
}

void setMotor2(int speed)
{
  bool forward = speed >= 0;
  speed = abs(speed);

  speed = constrain(speed,0,255);

  uint16_t pwm = map(speed,0,255,0,PWM_MAX);

  digitalWrite(IN3, forward);
  digitalWrite(IN4, !forward);

  pca9685.setPWM(PWMB_CH,0,pwm);
}

void stopMotors()
{
  pca9685.setPWM(PWMA_CH,0,0);
  pca9685.setPWM(PWMB_CH,0,0);
}

void setServo(int angle)
{
  angle = constrain(angle,0,180);

  uint16_t pulse = map(angle,0,180,SERVO_MIN,SERVO_MAX);

  pca9685.setPWM(SERVO_CH,0,pulse);
}

/*************************************/

void setup()
{
  Serial.begin(115200);

  pinMode(IN1,OUTPUT);
  pinMode(IN2,OUTPUT);
  pinMode(IN3,OUTPUT);
  pinMode(IN4,OUTPUT);

  Wire.begin();

  pca9685.begin();
  pca9685.setPWMFreq(50);

  stopMotors();
  Serial.println("Test du servomoteur en cours");
  /*  for(int i=0;i<180;i++)
  {
    setServo(i);
    delay(100);
  }*/

  Serial.println("Robot Test Ready");
}

/*************************************/

void loop()
{
  if (Serial.available())
  {
    input = Serial.readStringUntil('\n');
    input.trim();

    if(input.startsWith("m1"))
    {
      int val = input.substring(3).toInt();
      setMotor1(val);
      Serial.println("Motor1 OK");
    }

    else if(input.startsWith("m2"))
    {
      int val = input.substring(3).toInt();
      setMotor2(val);
      Serial.println("Motor2 OK");
    }

    else if(input.startsWith("servo"))
    {
      int angle = input.substring(6).toInt();
      setServo(angle);
      Serial.println("Servo OK");
    }

    else if(input == "stop")
    {
      stopMotors();
      Serial.println("Motors stopped");
    }
  }
}