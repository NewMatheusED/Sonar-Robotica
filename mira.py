import math
import sys
import time

import pygame
import serial

from radar import BAUD, PORTA, criar_som_retorno

ALCANCE_CM = 30        # raio da tela, em cm
DISTANCIA_SEGUIR = 22  # igual ao DISTANCIA_SEGUIR do src/mira.cpp
TEMPO_RASTRO = 2.0   # segundos que um ponto leva para sumir da tela

LARGURA, ALTURA = 1000, 720
VERDE = (40, 255, 40)
VERDE_ESCURO = (0, 110, 0)
VERMELHO = (255, 50, 50)
VERMELHO_ESCURO = (120, 0, 0)
CINZA = (22, 22, 22)
CINZA_CLARO = (70, 70, 70)
PRETO = (0, 0, 0)


def ler_linha(linha):
    """'angulo,distancia,travado,alvo' -> (angulo, distancia, travado, alvo), ou None se vier quebrada."""
    partes = linha.strip().split(",")
    if len(partes) != 4:
        return None
    try:
        a, d, t, alvo = map(int, partes)
    except ValueError:
        return None
    if not 0 <= a <= 180:
        return None
    return a, d, t == 1, alvo


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
        som_trava = criar_som_retorno()
    except pygame.error as erro:
        print(f"Não consegui iniciar o som: {erro}")
        ser.close()
        pygame.quit()
        sys.exit(1)
    tela = pygame.display.set_mode((LARGURA, ALTURA))
    pygame.display.set_caption("Mira - Sonar Arduino")
    fonte_grande = pygame.font.SysFont("consolas", 34, bold=True)
    fonte = pygame.font.SysFont("consolas", 22)
    fonte_peq = pygame.font.SysFont("consolas", 15)
    relogio = pygame.time.Clock()

    cx, cy = LARGURA // 2, ALTURA // 2
    raio = ALTURA // 2 - 45

    pontos = [(0, 0.0)] * 181   # (distância, instante da medida) por ângulo
    angulo, distancia = 90, 0
    travado, alvo, dist_alvo = False, 90, 0
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
                medida = ler_linha(linha)
                if medida is None:
                    continue
                a, d, t, alvo = medida
                if t and not travado:
                    som_trava.play()
                    dist_alvo = 0
                travado = t
                angulo, distancia = a, d
                pontos[a] = (d, time.time())
                if t and 0 < d <= DISTANCIA_SEGUIR and abs(a - alvo) <= 20:
                    dist_alvo = d

        agora = time.time()
        cor = VERMELHO if travado else VERDE
        cor_escura = VERMELHO_ESCURO if travado else VERDE_ESCURO

        tela.fill(PRETO)

        # Metade de trás: o servo só gira 180°, o sensor nunca olha para lá
        meia_lua = [(cx, cy)] + [polar(a, raio) for a in range(180, 361, 5)]
        pygame.draw.polygon(tela, CINZA, meia_lua)
        rotulo = fonte.render("PONTO CEGO", True, CINZA_CLARO)
        tela.blit(rotulo, (cx - rotulo.get_width() // 2, cy + raio // 2))

        # Anéis de distância, raios a cada 30° e marquinhas a cada 10° na borda
        for i in range(1, 5):
            pygame.draw.circle(tela, cor_escura, (cx, cy), raio * i // 4, 1)
            rotulo = fonte_peq.render(f"{ALCANCE_CM * i // 4}", True, cor_escura)
            tela.blit(rotulo, (cx + 4, cy - raio * i // 4 - 16))
        pygame.draw.circle(tela, cor, (cx, cy), raio, 2)
        for a in range(0, 360, 10):
            interno = raio - (14 if a % 30 == 0 else 7)
            pygame.draw.line(tela, cor, polar(a, interno), polar(a, raio), 2)
            if a % 30 == 0:
                pygame.draw.line(tela, cor_escura, (cx, cy), polar(a, interno), 1)
                rotulo = fonte_peq.render(f"{a}°", True, cor)
                x, y = polar(a, raio + 22)
                tela.blit(rotulo, (x - rotulo.get_width() // 2, y - rotulo.get_height() // 2))

        # Pontos detectados, apagando com o tempo
        for a, (d, instante) in enumerate(pontos):
            idade = agora - instante
            if 0 < d <= ALCANCE_CM and idade < TEMPO_RASTRO:
                brilho = 1 - idade / TEMPO_RASTRO
                pygame.draw.circle(tela, tuple(int(c * brilho) for c in VERMELHO),
                                   polar(a, d / ALCANCE_CM * raio), 5)

        pygame.draw.line(tela, cor, (cx, cy), polar(angulo, raio), 3)

        if travado and dist_alvo:
            # Retícula em cima do alvo, com colchetes girando
            px, py = polar(alvo, min(dist_alvo, ALCANCE_CM) / ALCANCE_CM * raio)
            pygame.draw.line(tela, VERMELHO, (cx, cy), (px, py), 1)
            caixa = pygame.Rect(px - 30, py - 30, 60, 60)
            giro = agora * 2
            for i in range(4):
                inicio = giro + i * math.pi / 2
                pygame.draw.arc(tela, VERMELHO, caixa, inicio, inicio + 0.8, 3)
            pygame.draw.line(tela, VERMELHO, (px - 12, py), (px + 12, py), 2)
            pygame.draw.line(tela, VERMELHO, (px, py - 12), (px, py + 12), 2)

        if travado:
            if int(agora * 3) % 2 == 0:   # pisca
                titulo = fonte_grande.render("ALVO TRAVADO", True, VERMELHO)
                tela.blit(titulo, (20, 20))
            texto_dist = f"{dist_alvo} cm" if dist_alvo else "--"
            info = fonte.render(f"Alvo: {alvo}°   Distância: {texto_dist}", True, VERMELHO)
        else:
            pontinhos = "." * (int(agora * 2) % 4)
            titulo = fonte_grande.render(f"BUSCANDO ALVO{pontinhos}", True, VERDE)
            tela.blit(titulo, (20, 20))
            texto_dist = f"{distancia} cm" if 0 < distancia <= ALCANCE_CM else "--"
            info = fonte.render(f"Ângulo: {angulo}°   Distância: {texto_dist}", True, VERDE)
        tela.blit(info, (20, ALTURA - 35))

        pygame.display.flip()
        relogio.tick(60)

    ser.close()
    pygame.quit()


if __name__ == "__main__":
    main()
