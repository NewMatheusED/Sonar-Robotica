import math
import sys
from array import array

import pygame
import serial

PORTA = "COM7"
BAUD = 9600
ALCANCE_CM = 40      # pode aumentar até 200, por ai
ANGULO_MIN, ANGULO_MAX = 15, 165

LARGURA, ALTURA = 1200, 700
VERDE = (40, 255, 40)
VERDE_ESCURO = (0, 140, 0)
VERMELHO = (255, 50, 50)
PRETO = (0, 0, 0)


def criar_som_retorno():
    frequencia = 44100
    total = int(frequencia * 0.12)
    amostras = array("h", (
        int(8000 * math.sin(2 * math.pi * 880 * i / frequencia)
            * math.sin(math.pi * i / (total - 1)))
        for i in range(total)
    ))
    return pygame.mixer.Sound(buffer=amostras)


def main():
    try:
        ser = serial.Serial(PORTA, BAUD, timeout=0)
    except serial.SerialException as erro:
        print(f"Não consegui abrir a porta {PORTA}: {erro}")
        print("Confira o número da porta e feche o monitor serial do PlatformIO.")
        sys.exit(1)

    pygame.mixer.pre_init(44100, -16, 1)
    pygame.init()
    try:
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()
        som_retorno = criar_som_retorno()
    except pygame.error as erro:
        print(f"Não consegui iniciar o som do radar: {erro}")
        ser.close()
        pygame.quit()
        sys.exit(1)
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Radar - Sonar Arduino")
    fonte = pygame.font.SysFont("consolas", 22)
    fonte_peq = pygame.font.SysFont("consolas", 16)
    relogio = pygame.time.Clock()

    cx, cy = LARGURA // 2, ALTURA - 60
    raio = min(LARGURA // 2, ALTURA - 80) - 20

    pontos = [0] * 181
    angulo, distancia = 90, 0
    ultimo_angulo = None
    buffer = ""

    def polar(ang, r):
        rad = math.radians(ang)
        return (cx + r * math.cos(rad), cy - r * math.sin(rad))

    rodando = True
    while rodando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                rodando = False

        # Lê o que chegou da serial e processa as linhas completas
        if ser.in_waiting:
            buffer += ser.read(ser.in_waiting).decode(errors="ignore")
            *linhas, buffer = buffer.split("\n")
            for linha in linhas:
                partes = linha.strip().split(",")
                if len(partes) != 2:
                    continue
                try:
                    a, d = int(partes[0]), int(partes[1])
                except ValueError:
                    continue
                if 0 <= a <= 180:
                    if (a in (ANGULO_MIN, ANGULO_MAX)
                            and ultimo_angulo is not None and a != ultimo_angulo):
                        som_retorno.play()
                    ultimo_angulo = a
                    angulo, distancia = a, d
                    pontos[a] = d

        tela.fill(PRETO)

        for i in range(1, 5):
            r = raio * i / 4
            pygame.draw.arc(tela, VERDE_ESCURO,
                            pygame.Rect(cx - r, cy - r, 2 * r, 2 * r),
                            0, math.pi, 2)
            rotulo = fonte_peq.render(f"{ALCANCE_CM * i // 4} cm", True, VERDE_ESCURO)
            tela.blit(rotulo, (cx + r - rotulo.get_width(), cy + 8))
        for a in range(0, 181, 30):
            pygame.draw.line(tela, VERDE_ESCURO, (cx, cy), polar(a, raio), 1)

        for a, d in enumerate(pontos):
            if 0 < d <= ALCANCE_CM:
                pygame.draw.circle(tela, VERMELHO, polar(a, d / ALCANCE_CM * raio), 5)

        pygame.draw.line(tela, VERDE, (cx, cy), polar(angulo, raio), 3)

        texto_dist = f"{distancia} cm" if 0 < distancia <= ALCANCE_CM else "fora do alcance"
        info = fonte.render(f"Ângulo: {angulo}°   Distância: {texto_dist}", True, VERDE)
        tela.blit(info, (20, ALTURA - 35))

        pygame.display.flip()
        relogio.tick(60)

    ser.close()
    pygame.quit()


if __name__ == "__main__":
    main()