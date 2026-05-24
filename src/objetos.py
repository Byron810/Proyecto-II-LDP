import pygame
from config import *

class Bala:
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
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.destruido = False
        self.tanque_defensor = None
        
    def destruir(self):
        self.destruido = True
        
    def dibujar(self, pantalla):
        if not self.destruido:
            pygame.draw.rect(pantalla, VERDE, 
                           (self.x * TAMANO_CELDA, self.y * TAMANO_CELDA, 
                            TAMANO_CELDA, TAMANO_CELDA))