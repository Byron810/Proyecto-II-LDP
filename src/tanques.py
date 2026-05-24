import pygame
import random
from config import *
from objetos import Bala

class Tanque:
    def __init__(self, x, y, color, velocidad):
        self.x = x
        self.y = y
        self.color = color
        self.velocidad = velocidad
        self.direccion = ARRIBA
        self.vida = 3
        self.ultimo_disparo = 0
        self.x_pixel = x * TAMANO_CELDA
        self.y_pixel = y * TAMANO_CELDA
        
    def mover(self, direccion, mapa, otros_tanques):
        nueva_x, nueva_y = self.x, self.y
        
        if direccion == ARRIBA:
            nueva_y -= 1
        elif direccion == ABAJO:
            nueva_y += 1
        elif direccion == IZQUIERDA:
            nueva_x -= 1
        elif direccion == DERECHA:
            nueva_x += 1
            
        # Verificar límites y colisiones
        if (0 <= nueva_x < len(mapa) and 0 <= nueva_y < len(mapa[0]) and
            mapa[nueva_x][nueva_y] != 'muro'):
            
            # Verificar colisión con otros tanques
            colision = False
            for tanque in otros_tanques:
                if tanque != self and tanque.x == nueva_x and tanque.y == nueva_y:
                    colision = True
                    break
                    
            if not colision:
                self.x = nueva_x
                self.y = nueva_y
                self.x_pixel = self.x * TAMANO_CELDA
                self.y_pixel = self.y * TAMANO_CELDA
                
        self.direccion = direccion
    
    def mover_a_punto(self, destino_x, destino_y, mapa, otros_tanques):
        """Mueve el tanque un paso hacia el destino"""
        if destino_x > self.x:
            self.mover(DERECHA, mapa, otros_tanques)
        elif destino_x < self.x:
            self.mover(IZQUIERDA, mapa, otros_tanques)
        elif destino_y > self.y:
            self.mover(ABAJO, mapa, otros_tanques)
        elif destino_y < self.y:
            self.mover(ARRIBA, mapa, otros_tanques)
        
    def disparar(self, tiempo_actual):
        if tiempo_actual - self.ultimo_disparo >= TIEMPO_ENTRE_DISPAROS:
            self.ultimo_disparo = tiempo_actual
            return Bala(self.x_pixel + TAMANO_CELDA//2, 
                       self.y_pixel + TAMANO_CELDA//2,
                       self.direccion, self)
        return None
    
    def dibujar(self, pantalla):
        rect = pygame.Rect(self.x_pixel, self.y_pixel, TAMANO_CELDA, TAMANO_CELDA)
        pygame.draw.rect(pantalla, self.color, rect)
        
        centro_x = self.x_pixel + TAMANO_CELDA//2
        centro_y = self.y_pixel + TAMANO_CELDA//2
        
        if self.direccion == ARRIBA:
            pygame.draw.line(pantalla, NEGRO, (centro_x, centro_y), 
                           (centro_x, centro_y - 15), 3)
        elif self.direccion == ABAJO:
            pygame.draw.line(pantalla, NEGRO, (centro_x, centro_y), 
                           (centro_x, centro_y + 15), 3)
        elif self.direccion == IZQUIERDA:
            pygame.draw.line(pantalla, NEGRO, (centro_x, centro_y), 
                           (centro_x - 15, centro_y), 3)
        elif self.direccion == DERECHA:
            pygame.draw.line(pantalla, NEGRO, (centro_x, centro_y), 
                           (centro_x + 15, centro_y), 3)

class TanqueJugador(Tanque):
    def __init__(self, x, y):
        super().__init__(x, y, AZUL, VELOCIDAD_TANQUE)
        self.vidas_nivel = 3
        
    def recibir_dano(self):
        self.vida -= 1
        self.vidas_nivel -= 1
        return self.vida <= 0

class TanqueEnemigo(Tanque):
    def __init__(self, x, y, tipo, motor_prolog, id_tanque):
        colores = {1: GRIS, 2: MARRON, 3: (100, 100, 100)}
        velocidades = {1: 2, 2: 4, 3: 1}
        vidas = {1: 3, 2: 1, 3: 5}
        
        super().__init__(x, y, colores[tipo], velocidades[tipo])
        self.tipo = tipo
        self.vida = vidas[tipo]
        self.ruta_actual = []
        self.objetivo_asignado = None
        self.frame_counter = 0
        self.motor_prolog = motor_prolog
        self.id_tanque = id_tanque
        self.ultima_actualizacion = 0
        
    def actualizar_ruta(self, jugador_x, jugador_y, frame_actual):
        """Actualiza la ruta usando Prolog cada cierto tiempo"""
        if frame_actual - self.ultima_actualizacion >= TIEMPO_DECISION_ENEMIGO:
            self.ultima_actualizacion = frame_actual
            self.ruta_actual = self.motor_prolog.obtener_ruta(
                self.id_tanque, self.x, self.y, jugador_x, jugador_y
            )
        
    def mover_segun_ruta(self, mapa, otros_tanques):
        """Mueve el tanque según la ruta actual"""
        if self.ruta_actual and len(self.ruta_actual) > 1:
            siguiente = self.ruta_actual[1]
            self.mover_a_punto(siguiente[0], siguiente[1], mapa, otros_tanques)
            if self.x == siguiente[0] and self.y == siguiente[1]:
                if len(self.ruta_actual) > 1:
                    self.ruta_actual.pop(0)