# Sonar ultrassônico com Arduino

Radar de 180°: um sensor HC-SR04 gira em cima de um servo SG90, o Arduino mede a distância a cada grau e manda os dados pela serial para a tela de radar no computador.

![Esquema elétrico](esquema-eletrico.png)

## Componentes

| Qtd | Peça | Observação |
|---|---|---|
| 1 | Arduino Uno R3 (compatível, chip CH340) | precisa do driver CH340 no Windows |
| 1 | Sensor ultrassônico HC-SR04 | alcance de 2 cm a ~4 m |
| 1 | Micro servo SG90 | braço reto + parafuso do eixo |
| 1 | Capacitor eletrolítico 470 µF / 16 V | estabiliza o 5V quando o servo puxa corrente |
| 1 | Protoboard (400 ou 830 pontos) | |
| — | Jumpers macho-macho e macho-fêmea | |

## Ligações

| Componente | Pino / fio | Liga em |
|---|---|---|
| Arduino | 5V | fileira **+** da protoboard |
| Arduino | GND | fileira **−** da protoboard |
| HC-SR04 | VCC | fileira + |
| HC-SR04 | Trig | pino **D10** |
| HC-SR04 | Echo | pino **D11** |
| HC-SR04 | GND | fileira − |
| Servo SG90 | laranja (sinal) | pino **D12** |
| Servo SG90 | vermelho (+) | fileira + |
| Servo SG90 | marrom (−) | fileira − |
| Capacitor | perna + | fileira + |
| Capacitor | perna da faixa (−) | fileira − |

## Cuidados

- **Fileira dividida:** em muitas protoboards a linha vermelha/azul lateral é interrompida no meio, e as duas metades não se conectam. Deixe todos os fios de 5V e GND na mesma metade, ou faça uma ponte com um jumper.
- **Polaridade do capacitor:** a perna do lado da faixa vai no GND. Invertido, ele pode estufar.
- **Centralizar o servo antes de prender o sensor:** grave um código com `servo.write(90)`, encaixe o braço apontando para a frente e só então cole o sensor.
- **Folga nos fios do sensor:** os jumpers precisam acompanhar o giro sem puxar.

## Software

| Arquivo | O que faz |
|---|---|
| `src/main.cpp` | Código do Arduino (conteúdo do `sonar.ino` com `#include <Arduino.h>` no topo). Varre de 15° a 165° e envia `angulo,distancia` pela serial a 9600 baud. |
| `radar.py` | Tela de radar no PC. Instale com `pip install pygame-ce pyserial` e rode com `python radar.py`. Ajuste `PORTA` para a porta do Arduino. |
| `radar.pde` | Versão alternativa da tela de radar para o Processing. |

`platformio.ini`:

```ini
[env:uno]
platform = atmelavr
board = uno
framework = arduino
lib_deps = arduino-libraries/Servo
upload_port = COM6
monitor_port = COM6
monitor_speed = 9600
```

## Medidas para a case

Medidas típicas dessas peças. Confira com régua ou paquímetro antes de cortar ou imprimir, porque clones variam um pouco.

| Peça | Medidas aproximadas | Detalhes úteis |
|---|---|---|
| Arduino Uno | 68,6 × 53,4 mm (placa) | furos de fixação de ~3,2 mm; o conector USB e o de energia saem pela borda menor; altura total ~15 mm com os conectores |
| HC-SR04 | 45 × 20 mm (placa), ~15 mm de profundidade | dois transdutores de ~16 mm de diâmetro com ~26 mm entre centros; pinos saindo por uma borda longa |
| Servo SG90 | corpo 22,5 × 12 mm, ~23 mm de altura (sem o eixo) | ~32 mm de largura com as abas de fixação; eixo fora do centro do corpo |
| Protoboard 400 pontos | ~83 × 55 mm | ~10 mm de altura |

Ideias para a case:

- A abertura frontal do sensor precisa ficar livre em todo o arco de 15° a 165°. Uma tampa em semicírculo, ou o sensor por cima da caixa, resolve.
- Deixe uma abertura para o cabo USB do Arduino na lateral.
- Prenda o servo pelas abas laterais com os parafusos compridos que vêm no saquinho.
- Passe os fios do sensor por um furo perto do eixo do servo, com folga, para não enrolar.
