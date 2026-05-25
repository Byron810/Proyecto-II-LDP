import pygame
import random
from config import *
from objetos import ObjetivoPrimario, ObjetivoTipoB
from tanques import TanqueEnemigo


class Mapa:
    """
    Representa la cuadrícula del nivel.
    Cada celda de self.malla puede ser 'libre' o 'muro'.
    También se encarga de colocar los objetivos y los tanques enemigos
    en posiciones válidas al inicio de cada nivel.
    """

    def __init__(self, ancho, alto):
        self.ancho = ancho
        self.alto = alto
        # Inicializar toda la cuadrícula como libre
        self.malla = [['libre' for _ in range(alto)] for _ in range(ancho)]

    def generar_muros(self, cantidad=30):
        """Genera muros aleatorios en el interior del mapa."""
        colocados = 0
        while colocados < cantidad:
            x = random.randint(1, self.ancho - 2)
            y = random.randint(1, self.alto - 2)
            if self.malla[x][y] == 'libre':
                self.malla[x][y] = 'muro'
                colocados += 1

    def colocar_objetivos(self, cantidad):
        """
        Coloca objetivos primarios aleatoriamente.
        50 % de probabilidad de ser TipoA (cuadrado verde, 1 hit)
        50 % de probabilidad de ser TipoB (rombo amarillo, 2 hits)
        """
        objetivos = []
        while len(objetivos) < cantidad:
            x = random.randint(1, self.ancho - 2)
            y = random.randint(1, self.alto - 2)
            if self.malla[x][y] == 'libre':
                if random.random() < 0.5:
                    objetivo = ObjetivoPrimario(x, y)   # Tipo A
                else:
                    objetivo = ObjetivoTipoB(x, y)      # Tipo B
                objetivos.append(objetivo)
        return objetivos

    def colocar_tanques_enemigos(self, objetivos, motor_prolog):
        """
        Coloca exactamente UN tanque defensor por cada objetivo.
        El tanque se ubica en la primera celda libre adyacente al objetivo.
        """
        tanques = []
        for i, objetivo in enumerate(objetivos):
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                x = objetivo.x + dx
                y = objetivo.y + dy
                if (0 <= x < self.ancho and 0 <= y < self.alto
                        and self.malla[x][y] == 'libre'):
                    tipo = random.choice([TIPO_1, TIPO_2, TIPO_3])
                    tanque = TanqueEnemigo(x, y, tipo, motor_prolog, i)
                    tanque.objetivo_asignado = objetivo
                    objetivo.tanque_defensor = tanque   # vínculo bidireccional
                    tanques.append(tanque)
                    break
        return tanques

    def dibujar(self, pantalla):
        for x in range(self.ancho):
            for y in range(self.alto):
                rect = pygame.Rect(
                    x * TAMANO_CELDA, y * TAMANO_CELDA,
                    TAMANO_CELDA, TAMANO_CELDA
                )
                if self.malla[x][y] == 'muro':
                    pygame.draw.rect(pantalla, GRIS, rect)
                    pygame.draw.rect(pantalla, NEGRO, rect, 2)
                else:
                    pygame.draw.rect(pantalla, NEGRO, rect, 1)
