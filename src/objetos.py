import pygame
from config import *


class Bala:
    """Proyectil disparado por un tanque. Se mueve en línea recta en una de las 4 direcciones."""

    def __init__(self, x, y, direccion, dueno):
        self.x = x
        self.y = y
        self.direccion = direccion
        self.dueno = dueno
        self.activa = True

    def mover(self):
        if self.direccion == ARRIBA:
            self.y -= VELOCIDAD_BALA
        elif self.direccion == ABAJO:
            self.y += VELOCIDAD_BALA
        elif self.direccion == IZQUIERDA:
            self.x -= VELOCIDAD_BALA
        elif self.direccion == DERECHA:
            self.x += VELOCIDAD_BALA

    def dibujar(self, pantalla):
        if self.activa:
            pygame.draw.rect(pantalla, ROJO, (self.x, self.y, 5, 5))


class ObjetivoPrimario:
    """
    Objetivo Tipo A — Base enemiga.
    Cuadrado verde. Se destruye con 1 impacto.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.destruido = False
        self.tanque_defensor = None

    def recibir_golpe(self):
        """Aplica 1 impacto. Retorna True si el objetivo fue destruido."""
        self.destruido = True
        return True

    def destruir(self):
        self.destruido = True

    def dibujar(self, pantalla):
        if not self.destruido:
            pygame.draw.rect(
                pantalla, VERDE,
                (self.x * TAMANO_CELDA, self.y * TAMANO_CELDA,
                 TAMANO_CELDA, TAMANO_CELDA)
            )


class ObjetivoTipoB:
    """
    Objetivo Tipo B — Generador de energía.
    Rombo amarillo. Necesita 2 impactos para destruirse.
    Al recibir el primer golpe cambia a naranja como indicador de daño.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.destruido = False
        self.tanque_defensor = None
        self.vida = 2

    def recibir_golpe(self):
        """Aplica 1 impacto. Retorna True si el objetivo fue destruido."""
        self.vida -= 1
        if self.vida <= 0:
            self.destruido = True
            return True
        return False

    def destruir(self):
        self.destruido = True

    def dibujar(self, pantalla):
        if not self.destruido:
            cx = self.x * TAMANO_CELDA + TAMANO_CELDA // 2
            cy = self.y * TAMANO_CELDA + TAMANO_CELDA // 2
            r  = TAMANO_CELDA // 2 - 3
            # Forma de rombo (cuatro vértices)
            puntos = [
                (cx,     cy - r),   # arriba
                (cx + r, cy),       # derecha
                (cx,     cy + r),   # abajo
                (cx - r, cy),       # izquierda
            ]
            # Amarillo con vida completa, naranja con 1 vida restante
            color = AMARILLO if self.vida == 2 else NARANJA
            pygame.draw.polygon(pantalla, color, puntos)
            pygame.draw.polygon(pantalla, NEGRO, puntos, 2)  # borde
