import pygame
import random
from config import *
from mapa import Mapa
from tanques import TanqueJugador, TanqueEnemigo
from motor_prolog import MotorProlog


class Game:
    """
    Controlador principal del juego.
    Gestiona la máquina de estados, el bucle principal y la interacción
    entre todos los actores (jugador, enemigos, balas, objetivos).

    Estados posibles: ESTADO_MENU → ESTADO_JUGANDO → ESTADO_GAME_OVER
                                                    → ESTADO_VICTORIA
    """

    def __init__(self):
        pygame.init()
        self.pantalla = pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))
        pygame.display.set_caption("Tank Attack")
        self.reloj = pygame.time.Clock()
        self.font_hud    = pygame.font.Font(None, 36)
        self.font_titulo = pygame.font.Font(None, 72)
        self.font_medio  = pygame.font.Font(None, 48)

        # Movimiento por casilla: primer press mueve 1 casilla,
        # si se mantiene la tecla espera 180 ms y luego repite cada 100 ms.
        pygame.key.set_repeat(180, 100)

        self.motor_prolog = MotorProlog()
        self.nivel_actual = 1
        self.max_niveles  = 3
        self.jugando = True
        self.pausa   = False

        # Referencias de botones (se crean al dibujar cada pantalla)
        self._boton_jugar     = None
        self._boton_salir     = None
        self._boton_menu      = None
        self._boton_fin_juego = None

        # Empieza en el menú (no carga nivel hasta que el jugador presione "Jugar")
        self.estado = ESTADO_MENU

    # ------------------------------------------------------------------
    # Inicialización de nivel
    # ------------------------------------------------------------------

    def iniciar_nivel(self, nivel, vidas_previas=3):
        """
        Genera un mapa nuevo, coloca enemigos, objetivos y al jugador,
        y carga toda la información en Prolog para que la IA funcione.
        Se llama al comenzar cada nivel (no al perder una vida).
        """
        self.mapa = Mapa(ANCHO_VENTANA // TAMANO_CELDA,
                         ALTO_VENTANA  // TAMANO_CELDA)
        self.mapa.generar_muros(cantidad=40 + nivel * 10)
        self.objetivos = self.mapa.colocar_objetivos(cantidad=2 + nivel)

        # Un tanque defensor por objetivo
        self.tanques_enemigos = self.mapa.colocar_tanques_enemigos(
            objetivos=self.objetivos,
            motor_prolog=self.motor_prolog
        )

        # Buscar celda libre para el jugador alejada de enemigos y objetivos.
        # Después de 200 intentos fallidos se acepta la mejor posición disponible
        # (puede ocurrir en mapas con muchos muros).
        intentos = 0
        while True:
            x = random.randint(1, self.mapa.ancho - 2)
            y = random.randint(1, self.mapa.alto - 2)
            if self.mapa.malla[x][y] != 'libre':
                continue
            lejos_de_enemigos = all(
                abs(t.x - x) + abs(t.y - y) >= MIN_DISTANCIA_SPAWN
                for t in self.tanques_enemigos
            )
            lejos_de_objetivos = all(
                abs(o.x - x) + abs(o.y - y) >= MIN_DISTANCIA_SPAWN
                for o in self.objetivos
            )
            intentos += 1
            if lejos_de_enemigos and lejos_de_objetivos:
                break
            if intentos > 200:
                break
        self.jugador = TanqueJugador(x, y)
        self.jugador.vidas_nivel = vidas_previas
        # Invulnerabilidad inicial para que el jugador pueda orientarse
        self.jugador.invulnerable_hasta = pygame.time.get_ticks() + TIEMPO_INVULNERABLE

        # Cargar mapa en Prolog UNA sola vez por nivel (los muros no cambian)
        self.motor_prolog.cargar_mapa_nivel(self.mapa.malla)

        # Decirle a Prolog qué objetivo defiende cada tanque (comportamiento 'defender')
        for t in self.tanques_enemigos:
            if t.objetivo_asignado:
                self.motor_prolog.registrar_objetivo_tanque(
                    t.id_tanque,
                    t.objetivo_asignado.x,
                    t.objetivo_asignado.y
                )

        self.balas = []

    # ------------------------------------------------------------------
    # Manejo de eventos (unificado para todos los estados)
    # ------------------------------------------------------------------

    def manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.jugando = False

            elif evento.type == pygame.KEYDOWN:
                if self.estado == ESTADO_JUGANDO and not self.pausa:
                    # Movimiento del jugador: una celda por tecla presionada
                    otros = self.tanques_enemigos + [self.jugador]
                    if evento.key == pygame.K_UP:
                        self.jugador.mover(ARRIBA, self.mapa.malla, otros)
                    elif evento.key == pygame.K_DOWN:
                        self.jugador.mover(ABAJO, self.mapa.malla, otros)
                    elif evento.key == pygame.K_LEFT:
                        self.jugador.mover(IZQUIERDA, self.mapa.malla, otros)
                    elif evento.key == pygame.K_RIGHT:
                        self.jugador.mover(DERECHA, self.mapa.malla, otros)
                    elif evento.key == pygame.K_SPACE:
                        bala = self.jugador.disparar(pygame.time.get_ticks())
                        if bala:
                            self.balas.append(bala)
                if evento.key == pygame.K_p and self.estado == ESTADO_JUGANDO:
                    self.pausa = not self.pausa

            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                pos = evento.pos

                if self.estado == ESTADO_MENU:
                    if self._boton_jugar and self._boton_jugar.collidepoint(pos):
                        self.nivel_actual = 1
                        self.iniciar_nivel(self.nivel_actual, vidas_previas=3)
                        self.estado = ESTADO_JUGANDO
                    elif self._boton_salir and self._boton_salir.collidepoint(pos):
                        self.jugando = False

                elif self.estado in (ESTADO_GAME_OVER, ESTADO_VICTORIA):
                    if self._boton_menu and self._boton_menu.collidepoint(pos):
                        self.estado = ESTADO_MENU

                elif self.estado == ESTADO_JUGANDO:
                    if self._boton_fin_juego and self._boton_fin_juego.collidepoint(pos):
                        self.estado = ESTADO_MENU

    # ------------------------------------------------------------------
    # Lógica de juego
    # ------------------------------------------------------------------

    def actualizar_enemigos(self):
        """
        Por cada tanque enemigo: actualiza su ruta desde Prolog,
        lo mueve un paso si ya venció su cooldown, y decide si dispara.
        """
        frame_actual = pygame.time.get_ticks()
        for enemigo in self.tanques_enemigos:
            enemigo.actualizar_ruta(self.jugador.x, self.jugador.y, frame_actual)
            enemigo.mover_segun_ruta(self.mapa.malla,
                                     self.tanques_enemigos + [self.jugador])

            # Disparo: el enemigo apunta y dispara si el jugador está dentro
            # del rango DISTANCIA_DISPARO con una probabilidad de PROB_DISPARO %.
            dist = (abs(enemigo.x - self.jugador.x)
                    + abs(enemigo.y - self.jugador.y))
            if dist <= DISTANCIA_DISPARO:
                # Rotar el cañón hacia el jugador antes de disparar
                dx = self.jugador.x - enemigo.x
                dy = self.jugador.y - enemigo.y
                if abs(dx) >= abs(dy):
                    enemigo.direccion = DERECHA if dx > 0 else IZQUIERDA
                else:
                    enemigo.direccion = ABAJO if dy > 0 else ARRIBA

                if random.randint(1, 100) <= PROB_DISPARO:
                    bala = enemigo.disparar(pygame.time.get_ticks())
                    if bala:
                        self.balas.append(bala)

    def actualizar_balas(self):
        """
        Mueve cada bala y verifica sus posibles colisiones en orden:
          1. Salió de la pantalla  → eliminar
          2. Chocó con un muro     → eliminar
          3. Impactó un tanque     → aplicar daño y eliminar
          4. Impactó un objetivo   → aplicar daño y eliminar (solo balas del jugador)
        Las balas que no colisionaron se conservan para el siguiente frame.
        """
        nuevas_balas = []
        for bala in self.balas:
            bala.mover()
            eliminar = False

            # 1. Fuera de pantalla
            if (bala.x < 0 or bala.x > ANCHO_VENTANA or
                    bala.y < 0 or bala.y > ALTO_VENTANA):
                eliminar = True

            # 2. Colisión con muro
            if not eliminar:
                cx = int(bala.x // TAMANO_CELDA)
                cy = int(bala.y // TAMANO_CELDA)
                if (0 <= cx < self.mapa.ancho and 0 <= cy < self.mapa.alto
                        and self.mapa.malla[cx][cy] == 'muro'):
                    eliminar = True

            # 3. Colisión con tanques.
            # Se compara el centro de la bala contra el centro del tanque
            # con tolerancia de media celda (hit-box exacto al sprite).
            MEDIO = TAMANO_CELDA // 2
            if not eliminar:
                if bala.dueno != self.jugador:  # bala enemiga → golpea jugador
                    cx = self.jugador.x_pixel + MEDIO
                    cy = self.jugador.y_pixel + MEDIO
                    if abs(bala.x - cx) < MEDIO and abs(bala.y - cy) < MEDIO:
                        if self.jugador.recibir_dano(pygame.time.get_ticks()):
                            self._jugador_muerto()
                        eliminar = True
                else:  # bala del jugador → golpea enemigos
                    for enemigo in self.tanques_enemigos[:]:
                        cx = enemigo.x_pixel + MEDIO
                        cy = enemigo.y_pixel + MEDIO
                        if abs(bala.x - cx) < MEDIO and abs(bala.y - cy) < MEDIO:
                            enemigo.vida -= 1
                            if enemigo.vida <= 0:
                                self.tanques_enemigos.remove(enemigo)
                            eliminar = True
                            break

            # 4. Colisión con objetivos (solo balas del jugador)
            if not eliminar and bala.dueno == self.jugador:
                for objetivo in self.objetivos:
                    obj_cx = objetivo.x * TAMANO_CELDA + MEDIO
                    obj_cy = objetivo.y * TAMANO_CELDA + MEDIO
                    if (not objetivo.destruido and
                            abs(bala.x - obj_cx) < MEDIO and
                            abs(bala.y - obj_cy) < MEDIO):
                        objetivo.recibir_golpe()
                        eliminar = True
                        break

            if not eliminar:
                nuevas_balas.append(bala)

        self.balas = nuevas_balas

    def _respawnear_jugador(self):
        """
        Reposiciona al jugador en el mismo mapa sin reiniciar el nivel.
        Se conservan el estado de los enemigos, los objetivos y el progreso.
        Solo se reubica el tanque del jugador en una celda libre alejada,
        se limpia la lista de balas y se activa la invulnerabilidad inicial.
        """
        vidas = self.jugador.vidas_nivel  # la vida ya fue descontada antes de llamar aquí

        # Buscar celda de spawn alejada de enemigos y objetivos que aún estén activos
        intentos = 0
        while True:
            x = random.randint(1, self.mapa.ancho - 2)
            y = random.randint(1, self.mapa.alto - 2)
            if self.mapa.malla[x][y] != 'libre':
                continue
            lejos_de_enemigos = all(
                abs(t.x - x) + abs(t.y - y) >= MIN_DISTANCIA_SPAWN
                for t in self.tanques_enemigos
            )
            lejos_de_objetivos = all(
                abs(o.x - x) + abs(o.y - y) >= MIN_DISTANCIA_SPAWN
                for o in self.objetivos if not o.destruido
            )
            intentos += 1
            if lejos_de_enemigos and lejos_de_objetivos:
                break
            if intentos > 200:
                break  # mapa muy lleno: aceptar la posición disponible

        self.jugador = TanqueJugador(x, y)
        self.jugador.vidas_nivel = vidas
        self.jugador.invulnerable_hasta = pygame.time.get_ticks() + TIEMPO_INVULNERABLE
        # Limpiar balas para que ninguna impacte al jugador nada más aparecer
        self.balas = []

    def _jugador_muerto(self):
        """
        Maneja la pérdida de una vida.
        Si ya no quedan vidas → Game Over.
        Si aún quedan vidas → reaparece en el mismo mapa (sin reiniciar el nivel).
        """
        if self.jugador.vidas_nivel <= 0:
            self.estado = ESTADO_GAME_OVER
        else:
            self._respawnear_jugador()

    def verificar_fin_nivel(self):
        """Avanza al siguiente nivel si todos los objetivos están destruidos."""
        if all(o.destruido for o in self.objetivos):
            self.nivel_actual += 1
            if self.nivel_actual > self.max_niveles:
                self.estado = ESTADO_VICTORIA
            else:
                # Nuevo nivel: mapa nuevo y vidas reiniciadas a 3
                self.iniciar_nivel(self.nivel_actual, vidas_previas=3)

    # ------------------------------------------------------------------
    # Renderizado
    # ------------------------------------------------------------------

    def _dibujar_boton(self, texto, rect, color_fondo, color_texto=BLANCO):
        """Dibuja un botón y retorna su Rect para detección de clic."""
        pygame.draw.rect(self.pantalla, color_fondo, rect, border_radius=8)
        pygame.draw.rect(self.pantalla, BLANCO, rect, 2, border_radius=8)
        surf = self.font_hud.render(texto, True, color_texto)
        self.pantalla.blit(surf, surf.get_rect(center=rect.center))
        return rect

    def dibujar_menu(self):
        """Pantalla de menú principal."""
        self.pantalla.fill(NEGRO)

        titulo = self.font_titulo.render("TANK ATTACK", True, VERDE)
        self.pantalla.blit(titulo,
                           titulo.get_rect(center=(ANCHO_VENTANA // 2, 140)))

        sub = self.font_hud.render("Destruye todos los objetivos para ganar", True, GRIS)
        self.pantalla.blit(sub, sub.get_rect(center=(ANCHO_VENTANA // 2, 210)))

        cx = ANCHO_VENTANA // 2
        self._boton_jugar = self._dibujar_boton(
            "Jugar",
            pygame.Rect(cx - 100, 290, 200, 55),
            (0, 100, 0)
        )
        self._boton_salir = self._dibujar_boton(
            "Salir",
            pygame.Rect(cx - 100, 370, 200, 55),
            (120, 0, 0)
        )

        controles = [
            "Flechas: mover    Espacio: disparar    P: pausa",
            "Cuadrado verde = 1 hit    Rombo amarillo = 2 hits",
        ]
        for i, linea in enumerate(controles):
            s = pygame.font.Font(None, 26).render(linea, True, GRIS)
            self.pantalla.blit(s, s.get_rect(center=(ANCHO_VENTANA // 2,
                                                      480 + i * 28)))
        pygame.display.flip()

    def dibujar_game_over(self):
        """Pantalla de Game Over."""
        self.pantalla.fill(NEGRO)
        titulo = self.font_titulo.render("GAME OVER", True, ROJO)
        self.pantalla.blit(titulo,
                           titulo.get_rect(center=(ANCHO_VENTANA // 2, 150)))
        info = self.font_hud.render(
            f"Llegaste al nivel {self.nivel_actual}", True, BLANCO)
        self.pantalla.blit(info, info.get_rect(center=(ANCHO_VENTANA // 2, 240)))
        self._boton_menu = self._dibujar_boton(
            "Volver al menu",
            pygame.Rect(ANCHO_VENTANA // 2 - 120, 320, 240, 55),
            GRIS
        )
        pygame.display.flip()

    def dibujar_victoria(self):
        """Pantalla de Victoria."""
        self.pantalla.fill(NEGRO)
        titulo = self.font_titulo.render("VICTORIA!", True, VERDE)
        self.pantalla.blit(titulo,
                           titulo.get_rect(center=(ANCHO_VENTANA // 2, 150)))
        info = self.font_hud.render(
            "Completaste los 3 niveles", True, BLANCO)
        self.pantalla.blit(info, info.get_rect(center=(ANCHO_VENTANA // 2, 240)))
        self._boton_menu = self._dibujar_boton(
            "Volver al menu",
            pygame.Rect(ANCHO_VENTANA // 2 - 120, 320, 240, 55),
            GRIS
        )
        pygame.display.flip()

    def dibujar(self):
        """
        Renderiza el estado de juego activo: mapa, objetivos, tanques y balas.
        Cuando el jugador es invulnerable parpadea cada 100 ms para indicarlo visualmente.
        """
        self.pantalla.fill(NEGRO)
        self.mapa.dibujar(self.pantalla)
        for objetivo in self.objetivos:
            objetivo.dibujar(self.pantalla)
        for tanque in self.tanques_enemigos:
            tanque.dibujar(self.pantalla)
        # Parpadeo del jugador invulnerable: visible solo en los frames pares de 100 ms
        ahora = pygame.time.get_ticks()
        if not self.jugador.es_invulnerable(ahora) or (ahora // 100) % 2 == 0:
            self.jugador.dibujar(self.pantalla)
        for bala in self.balas:
            bala.dibujar(self.pantalla)

        # HUD: información de estado en la esquina superior izquierda
        objetivos_restantes = sum(1 for o in self.objetivos if not o.destruido)
        self.pantalla.blit(
            self.font_hud.render(f"Nivel: {self.nivel_actual}", True, BLANCO),
            (10, 10))
        self.pantalla.blit(
            self.font_hud.render(f"Vidas: {self.jugador.vidas_nivel}", True, BLANCO),
            (10, 50))
        self.pantalla.blit(
            self.font_hud.render(f"Objetivos: {objetivos_restantes}", True, BLANCO),
            (10, 90))

        if self.pausa:
            pausa_surf = self.font_medio.render("PAUSA", True, AMARILLO)
            self.pantalla.blit(
                pausa_surf,
                pausa_surf.get_rect(center=(ANCHO_VENTANA // 2, ALTO_VENTANA // 2)))

        self._boton_fin_juego = self._dibujar_boton(
            "Fin",
            pygame.Rect(ANCHO_VENTANA - 90, 10, 80, 35),
            (120, 0, 0)
        )
        pygame.display.flip()

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------

    def ejecutar(self):
        while self.jugando:
            self.manejar_eventos()

            if self.estado == ESTADO_MENU:
                self.dibujar_menu()

            elif self.estado == ESTADO_JUGANDO:
                if not self.pausa:
                    self.actualizar_enemigos()
                    self.actualizar_balas()
                    self.verificar_fin_nivel()
                self.dibujar()

            elif self.estado == ESTADO_GAME_OVER:
                self.dibujar_game_over()

            elif self.estado == ESTADO_VICTORIA:
                self.dibujar_victoria()

            self.reloj.tick(60)

        pygame.quit()
