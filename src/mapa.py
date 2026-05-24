import pygame
import random
from config import *
from objetos import ObjetivoPrimario
from tanques import TanqueEnemigo

class Mapa:
    def __init__(self, ancho, alto):
        self.ancho = ancho
        self.alto = alto
        self.malla = [['libre' for _ in range(alto)] for _ in range(ancho)]
        
    def generar_muros(self, cantidad=30):
        """Genera muros aleatorios en el mapa"""
        muros_colocados = 0
        while muros_colocados < cantidad:
            x = random.randint(1, self.ancho-2)
            y = random.randint(1, self.alto-2)
            if self.malla[x][y] == 'libre':
                self.malla[x][y] = 'muro'
                muros_colocados += 1
                
    def colocar_objetivos(self, cantidad):
        """Coloca objetivos primarios aleatoriamente"""
        objetivos = []
        while len(objetivos) < cantidad:
            x = random.randint(1, self.ancho-2)
            y = random.randint(1, self.alto-2)
            if self.malla[x][y] == 'libre':
                objetivo = ObjetivoPrimario(x, y)
                objetivos.append(objetivo)
        return objetivos
    
    def colocar_tanques_enemigos(self, cantidad, objetivos, motor_prolog):
        """Coloca tanques enemigos cerca de los objetivos"""
        tanques = []
        
        for i, objetivo in enumerate(objetivos):
            if i < cantidad:
                # Colocar tanque cerca del objetivo
                for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                    x = objetivo.x + dx
                    y = objetivo.y + dy
                    if (0 <= x < self.ancho and 0 <= y < self.alto and 
                        self.malla[x][y] == 'libre'):
                        tipo = random.choice([TIPO_1, TIPO_2, TIPO_3])
                        tanque = TanqueEnemigo(x, y, tipo, motor_prolog, i)
                        tanque.objetivo_asignado = objetivo
                        tanques.append(tanque)
                        break
        return tanques
    
    def dibujar(self, pantalla):
        for x in range(self.ancho):
            for y in range(self.alto):
                rect = pygame.Rect(x * TAMANO_CELDA, y * TAMANO_CELDA, 
                                 TAMANO_CELDA, TAMANO_CELDA)
                if self.malla[x][y] == 'muro':
                    pygame.draw.rect(pantalla, GRIS, rect)
                    pygame.draw.rect(pantalla, NEGRO, rect, 2)
                else:
                    pygame.draw.rect(pantalla, NEGRO, rect, 1)