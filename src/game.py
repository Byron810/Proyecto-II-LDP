import pygame
import random
from config import *
from mapa import Mapa
from tanques import TanqueJugador, TanqueEnemigo
from motor_prolog import MotorProlog

class Game:
    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
        pygame.display.set_caption("Tank Attack")
        self.reloj = pygame.time.Clock()
        
        self.motor_prolog = MotorProlog()
        self.nivel_actual = 1
        self.max_niveles = 3
        self.jugando = True
        self.pausa = False
        
        self.iniciar_nivel(self.nivel_actual)
        
    def iniciar_nivel(self, nivel):
        self.mapa = Mapa(ANCHO_VENTANA // TAMANO_CELDA, 
                        ALTO_VENTANA // TAMANO_CELDA)
        self.mapa.generar_muros(cantidad=40 + nivel * 10)
        self.objetivos = self.mapa.colocar_objetivos(cantidad=2 + nivel)
        
        # Aquí está la línea corregida:
        self.tanques_enemigos = self.mapa.colocar_tanques_enemigos(
            cantidad=2, 
            objetivos=self.objetivos,
            motor_prolog=self.motor_prolog
        )
        
        # Colocar jugador
        posicion_valida = False
        while not posicion_valida:
            x = random.randint(1, self.mapa.ancho-2)
            y = random.randint(1, self.mapa.alto-2)
            if (self.mapa.malla[x][y] == 'libre' and
                not any(tanque.x == x and tanque.y == y for tanque in self.tanques_enemigos)):
                posicion_valida = True
        self.jugador = TanqueJugador(x, y)
        
        self.actualizar_prolog()
        self.balas = []
        self.tiempo_desde_ultimo_disparo = 0
        
    def actualizar_prolog(self):
        self.motor_prolog.actualizar_mapa(
            self.mapa.malla,
            self.tanques_enemigos,
            (self.jugador.x, self.jugador.y)
        )
        
    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.jugando = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_p:
                    self.pausa = not self.pausa
                    
    def manejar_teclado_jugador(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.jugador.mover(ARRIBA, self.mapa.malla, 
                             self.tanques_enemigos + [self.jugador])
        elif keys[pygame.K_DOWN]:
            self.jugador.mover(ABAJO, self.mapa.malla, 
                             self.tanques_enemigos + [self.jugador])
        elif keys[pygame.K_LEFT]:
            self.jugador.mover(IZQUIERDA, self.mapa.malla, 
                             self.tanques_enemigos + [self.jugador])
        elif keys[pygame.K_RIGHT]:
            self.jugador.mover(DERECHA, self.mapa.malla, 
                             self.tanques_enemigos + [self.jugador])
        if keys[pygame.K_SPACE]:
            bala = self.jugador.disparar(pygame.time.get_ticks())
            if bala:
                self.balas.append(bala)
                
    def actualizar_enemigos(self):
        frame_actual = pygame.time.get_ticks()
        for i, enemigo in enumerate(self.tanques_enemigos):
            # Solo un enemigo por frame actualiza su ruta (distribuir carga)
            if frame_actual % len(self.tanques_enemigos) == i:
                enemigo.actualizar_ruta(self.jugador.x, self.jugador.y, frame_actual)
            enemigo.mover_segun_ruta(self.mapa.malla, self.tanques_enemigos + [self.jugador])
            if random.randint(1, 100) < 2:
                bala = enemigo.disparar(pygame.time.get_ticks())
                if bala:
                    self.balas.append(bala)
                    
    def actualizar_balas(self):
        nuevas_balas = []
        for bala in self.balas:
            bala.mover()
            eliminar = False

            # 1. Límites de pantalla
            if (bala.x < 0 or bala.x > ANCHO_VENTANA or
                bala.y < 0 or bala.y > ALTO_VENTANA):
                eliminar = True

            # 2. Colisión con muros
            if not eliminar:
                celda_x = int(bala.x // TAMANO_CELDA)
                celda_y = int(bala.y // TAMANO_CELDA)
                if (0 <= celda_x < self.mapa.ancho and 
                    0 <= celda_y < self.mapa.alto and
                    self.mapa.malla[celda_x][celda_y] == 'muro'):
                    eliminar = True

            # 3. Colisión con tanques
            if not eliminar:
                if bala.dueno != self.jugador:  # Bala enemiga
                    if (abs(bala.x - self.jugador.x_pixel) < TAMANO_CELDA and
                        abs(bala.y - self.jugador.y_pixel) < TAMANO_CELDA):
                        if self.jugador.recibir_dano():
                            self.reiniciar_nivel()
                        eliminar = True
                else:  # Bala del jugador
                    for enemigo in self.tanques_enemigos[:]:
                        if (abs(bala.x - enemigo.x_pixel) < TAMANO_CELDA and
                            abs(bala.y - enemigo.y_pixel) < TAMANO_CELDA):
                            enemigo.vida -= 1
                            if enemigo.vida <= 0:
                                self.tanques_enemigos.remove(enemigo)
                            eliminar = True
                            break

            # 4. Colisión con objetivos (solo balas del jugador)
            if not eliminar and bala.dueno == self.jugador:
                for objetivo in self.objetivos:
                    if (not objetivo.destruido and
                        abs(bala.x - objetivo.x * TAMANO_CELDA) < TAMANO_CELDA and
                        abs(bala.y - objetivo.y * TAMANO_CELDA) < TAMANO_CELDA):
                        objetivo.destruir()
                        eliminar = True
                        break

            # Conservar la bala solo si no fue eliminada
            if not eliminar:
                nuevas_balas.append(bala)

        self.balas = nuevas_balas
                        
    def reiniciar_nivel(self):
        self.iniciar_nivel(self.nivel_actual)
        
    def verificar_fin_nivel(self):
        if all(objetivo.destruido for objetivo in self.objetivos):
            self.nivel_actual += 1
            if self.nivel_actual > self.max_niveles:
                print("¡Juego completado!")
                self.jugando = False
            else:
                self.iniciar_nivel(self.nivel_actual)
                
    def dibujar(self):
        print("Dibujando...")  # Debug
        self.pantalla.fill(NEGRO)
        self.mapa.dibujar(self.pantalla)
        for objetivo in self.objetivos:
            objetivo.dibujar(self.pantalla)
        for tanque in self.tanques_enemigos:
            tanque.dibujar(self.pantalla)
        self.jugador.dibujar(self.pantalla)
        for bala in self.balas:
            bala.dibujar(self.pantalla)
        
        font = pygame.font.Font(None, 36)
        texto_nivel = font.render(f"Nivel: {self.nivel_actual}", True, BLANCO)
        texto_vidas = font.render(f"Vidas: {self.jugador.vidas_nivel}", True, BLANCO)
        objetivos_restantes = sum(1 for o in self.objetivos if not o.destruido)
        texto_objetivos = font.render(f"Objetivos: {objetivos_restantes}", True, BLANCO)
        self.pantalla.blit(texto_nivel, (10, 10))
        self.pantalla.blit(texto_vidas, (10, 50))
        self.pantalla.blit(texto_objetivos, (10, 90))
        pygame.display.flip()
        
    def ejecutar(self):
        print("Iniciando bucle del juego...")  # Debug
        while self.jugando:
            print("Tick...")  # Debug
            self.manejar_eventos()
            if not self.pausa:
                self.manejar_teclado_jugador()
                
                self.actualizar_enemigos()
                self.actualizar_balas()
                self.verificar_fin_nivel()
                self.actualizar_prolog()
            self.dibujar()
            self.reloj.tick(60)
        pygame.quit()