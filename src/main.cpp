// Sonar com Arduino: HC-SR04 em cima de um servo SG90, varredura de 180°
// Envia pela serial uma linha por medida no formato "angulo,distancia"

#include <Arduino.h>
#include <Servo.h>

const int PINO_TRIG  = 10;
const int PINO_ECHO  = 11;
const int PINO_SERVO = 12;

const int ANGULO_MIN = 15;   // evita forçar o servo nas pontas
const int ANGULO_MAX = 165;

Servo servo;

// Retorna a distância em cm (0 = sem eco / fora do alcance)
int medirDistancia() {
  digitalWrite(PINO_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PINO_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PINO_TRIG, LOW);

  long duracao = pulseIn(PINO_ECHO, HIGH, 30000);  // timeout de 30 ms (~5 m)
  if (duracao == 0) return 0;
  return duracao * 0.034 / 2;  // velocidade do som: 0,034 cm/µs, ida e volta
}

void medirEEnviar(int angulo) {
  servo.write(angulo);
  delay(30);  // tempo para o servo chegar na posição

  int distancia = medirDistancia();
  Serial.print(angulo);
  Serial.print(",");
  Serial.println(distancia);
}

void setup() {
  pinMode(PINO_TRIG, OUTPUT);
  pinMode(PINO_ECHO, INPUT);
  Serial.begin(9600);
  servo.attach(PINO_SERVO);
}

void loop() {
  for (int a = ANGULO_MIN; a <= ANGULO_MAX; a++) medirEEnviar(a);
  for (int a = ANGULO_MAX; a >= ANGULO_MIN; a--) medirEEnviar(a);
}
