// Trava de mira com Arduino: mesmo hardware do sonar (HC-SR04 em cima de um servo SG90)
// Varre até algo chegar perto, aí trava a mira e segue o alvo com varreduras curtas em volta dele
// Envia pela serial uma linha por medida no formato "angulo,distancia,travado,alvo"

#include <Arduino.h>
#include <Servo.h>

const int PINO_TRIG  = 10;
const int PINO_ECHO  = 11;
const int PINO_SERVO = 12;

const int ANGULO_MIN = 0;    // se o servo zumbir ou forçar nas pontas, volte para 15 / 165
const int ANGULO_MAX = 180;

// Os dois precisam ficar abaixo da coisa parada mais próxima do sensor, senão a mira trava nela
const int DISTANCIA_TRAVA  = 12;   // cm: algo mais perto que isso trava a mira
const int DISTANCIA_SEGUIR = 22;   // cm: já travado, continua seguindo até essa distância
const int JANELA = 20;             // graus para cada lado do alvo na varredura curta
const int PASSO_SEGUIR = 4;        // graus entre as medidas da varredura curta
const unsigned long TEMPO_PERDER = 1000;  // ms sem ver o alvo para destravar

Servo servo;

int angulo = 90;
int sentido = 1;   // +1 ou -1, sentido da varredura
bool travado = false;
int alvo = 90;     // ângulo do centro do alvo travado
unsigned long ultimoVisto = 0;

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

bool perto(int distancia, int limite) {
  return distancia > 0 && distancia <= limite;
}

int medirEEnviar(int a) {
  servo.write(a);
  delay(30);  // tempo para o servo chegar na posição

  int distancia = medirDistancia();
  Serial.print(a);
  Serial.print(",");
  Serial.print(distancia);
  Serial.print(",");
  Serial.print(travado ? 1 : 0);
  Serial.print(",");
  Serial.println(alvo);
  return distancia;
}

// Varre de um lado ao outro do alvo e recentra a mira no meio de onde ele apareceu
void seguir() {
  int inicio = constrain(alvo - JANELA, ANGULO_MIN, ANGULO_MAX);
  int fim    = constrain(alvo + JANELA, ANGULO_MIN, ANGULO_MAX);
  if (sentido < 0) {  // alterna o sentido para o servo não dar o pulo de volta
    int t = inicio;
    inicio = fim;
    fim = t;
  }

  int primeiro = -1, ultimo = -1;
  for (int a = inicio; sentido > 0 ? a <= fim : a >= fim; a += sentido * PASSO_SEGUIR) {
    if (perto(medirEEnviar(a), DISTANCIA_SEGUIR)) {
      if (primeiro < 0) primeiro = a;
      ultimo = a;
    }
  }
  sentido = -sentido;

  if (primeiro >= 0) {
    alvo = (primeiro + ultimo) / 2;
    ultimoVisto = millis();
  } else if (millis() - ultimoVisto > TEMPO_PERDER) {
    travado = false;
    angulo = alvo;  // volta a varrer a partir de onde perdeu
  }
}

void setup() {
  pinMode(PINO_TRIG, OUTPUT);
  pinMode(PINO_ECHO, INPUT);
  Serial.begin(9600);
  servo.attach(PINO_SERVO);
}

void loop() {
  if (travado) {
    seguir();
    return;
  }

  if (perto(medirEEnviar(angulo), DISTANCIA_TRAVA)) {
    travado = true;
    alvo = angulo;
    ultimoVisto = millis();
    return;
  }

  if (angulo + sentido > ANGULO_MAX || angulo + sentido < ANGULO_MIN) sentido = -sentido;
  angulo += sentido;
}
