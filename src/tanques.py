import pygame
import random
from config import *
from objetos import Bala


class Tanque:
    """
    Clase base para todos los tanques del juego.
    Define posición, movimiento, disparo y renderizado.
    Tanto el jugador como los enemigos heredan de aquí.
    """

    def __init__(self, x, y, color, velocidad):
        self.x = x
        self.y = y
        self.color = color
        self.velocidad = velocidad
        self.direccion = ARRIBA
        self.vida = 3
        self.ultimo_disparo = 0
        # Posición en píxeles calculada a partir de la celda de la cuadrícula
        self.x_pixel = x * TAMANO_CELDA
        self.y_pixel = y * TAMANO_CELDA

    def mover(self, direccion, mapa, otros_tanques):
        """
        Intenta mover el tanque una celda en la dirección indicada.
        Antes de moverse verifica dos condiciones:
          1. La celda destino no es un muro ni está fuera del mapa.
          2. Ningún otro tanque ocupa esa celda.
        Si alguna condición falla, el tanque no se mueve pero sí actualiza
        su dirección (para que el cañón apunte hacia donde se intentó ir).
        """
        nueva_x, nueva_y = self.x, self.y

        if direccion == ARRIBA:
            nueva_y -= 1
        elif direccion == ABAJO:
            nueva_y += 1
        elif direccion == IZQUIERDA:
            nueva_x -= 1
        elif direccion == DERECHA:
            nueva_x += 1

        # Verificar límites del mapa y que la celda no sea muro
        if (0 <= nueva_x < len(mapa) and 0 <= nueva_y < len(mapa[0]) and
                mapa[nueva_x][nueva_y] != 'muro'):

            # Verificar que ningún otro tanque esté en la celda destino
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
        """
        Mueve el tanque UN paso en dirección al punto destino.
        Primero intenta moverse en el eje con mayor diferencia (X o Y).
        Usado por los tanques enemigos para seguir su ruta calculada.
        """
        if destino_x > self.x:
            self.mover(DERECHA, mapa, otros_tanques)
        elif destino_x < self.x:
            self.mover(IZQUIERDA, mapa, otros_tanques)
        elif destino_y > self.y:
            self.mover(ABAJO, mapa, otros_tanques)
        elif destino_y < self.y:
            self.mover(ARRIBA, mapa, otros_tanques)

    def disparar(self, tiempo_actual):
        """
        Crea una bala en el centro del tanque apuntando en su dirección actual.
        Respeta el cooldown TIEMPO_ENTRE_DISPAROS para no disparar cada frame.
        Retorna la bala si se pudo disparar, o None si aún está en cooldown.
        """
        if tiempo_actual - self.ultimo_disparo >= TIEMPO_ENTRE_DISPAROS:
            self.ultimo_disparo = tiempo_actual
            return Bala(self.x_pixel + TAMANO_CELDA // 2,
                        self.y_pixel + TAMANO_CELDA // 2,
                        self.direccion, self)
        return None

    def dibujar(self, pantalla):
        """Dibuja el cuerpo del tanque y una línea que representa el cañón."""
        rect = pygame.Rect(self.x_pixel, self.y_pixel, TAMANO_CELDA, TAMANO_CELDA)
        pygame.draw.rect(pantalla, self.color, rect)

        # Cañón: línea desde el centro hacia la dirección actual
        centro_x = self.x_pixel + TAMANO_CELDA // 2
        centro_y = self.y_pixel + TAMANO_CELDA // 2

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
    """
    Tanque controlado por el jugador.
    Añade un sistema de vidas por nivel y un período de invulnerabilidad
    tras recibir daño, para evitar perder varias vidas en un mismo instante.
    """

    def __init__(self, x, y):
        super().__init__(x, y, AZUL, VELOCIDAD_TANQUE)
        self.vidas_nivel = 3
        # Timestamp hasta el que el jugador es invulnerable tras recibir daño
        self.invulnerable_hasta = 0

    def recibir_dano(self, tiempo_actual):
        """
        Descuenta una vida si el jugador no está en período de invulnerabilidad.
        Al recibir daño activa la invulnerabilidad por TIEMPO_INVULNERABLE ms.
        Retorna True si se perdió la vida (el llamador decide qué hacer a continuación).
        """
        if tiempo_actual < self.invulnerable_hasta:
            return False  # golpe ignorado: sigue invulnerable
        self.vidas_nivel -= 1
        self.invulnerable_hasta = tiempo_actual + TIEMPO_INVULNERABLE
        return True

    def es_invulnerable(self, tiempo_actual):
        return tiempo_actual < self.invulnerable_hasta


class TanqueEnemigo(Tanque):
    """
    Tanque controlado por la IA en Prolog.
    Hay 3 tipos con distintas características:
      Tipo 1 (gris)         — normal: 3 vidas, velocidad media
      Tipo 2 (marrón)       — rápido: 1 vida, mayor velocidad
      Tipo 3 (verde oscuro) — resistente: 5 vidas, movimiento lento

    El movimiento funciona en dos pasos por frame:
      1. actualizar_ruta()    → pide una nueva ruta a Prolog cada 2 segundos
      2. mover_segun_ruta()   → avanza un paso si ya pasó el cooldown del tipo
    """

    def __init__(self, x, y, tipo, motor_prolog, id_tanque):
        colores = {1: GRIS, 2: MARRON, 3: VERDE_OSCURO}
        velocidades = {1: 2, 2: 4, 3: 1}
        vidas = {1: 3, 2: 1, 3: 5}

        super().__init__(x, y, colores[tipo], velocidades[tipo])
        self.tipo = tipo
        self.vida = vidas[tipo]

        # Estado de navegación
        self.ruta_actual = []          # lista de (x, y) calculada por Prolog
        self.objetivo_asignado = None  # objetivo que este tanque defiende

        self.frame_counter = 0
        self.motor_prolog = motor_prolog
        self.id_tanque = id_tanque

        # Valor negativo para que la primera llamada pida ruta inmediatamente
        self.ultima_actualizacion = -TIEMPO_DECISION_ENEMIGO

        # Detección de atasco: si el tanque no puede moverse varios intentos
        # seguidos, pide una ruta nueva de urgencia para desatascarse
        self.frames_atascado = 0
        self._pedir_ruta_urgente = False

        # Cooldown de movimiento: timestamp del último paso efectivo
        self.ultimo_movimiento = 0

        # Caché de la última posición conocida del jugador
        self._jugador_x_cache = 0
        self._jugador_y_cache = 0

    def actualizar_ruta(self, jugador_x, jugador_y, frame_actual):
        """
        Solicita una nueva ruta a Prolog cada TIEMPO_DECISION_ENEMIGO ms
        (o de inmediato si el tanque está atascado).
        La solicitud es no bloqueante: se encola en el hilo de Prolog y el
        resultado llega en el siguiente frame en que Prolog lo procese.
        """
        self._jugador_x_cache = jugador_x
        self._jugador_y_cache = jugador_y

        # Pedir nueva ruta si venció el intervalo o si hay una solicitud urgente
        if (frame_actual - self.ultima_actualizacion >= TIEMPO_DECISION_ENEMIGO
                or self._pedir_ruta_urgente):
            self.ultima_actualizacion = frame_actual
            self._pedir_ruta_urgente = False
            self.motor_prolog.solicitar_ruta(
                self.id_tanque, self.x, self.y, jugador_x, jugador_y
            )

        # obtener_ruta_actual usa pop interno: devuelve [] si Prolog aún
        # no terminó de calcular (evita pisar una ruta válida con datos viejos)
        ruta_nueva = self.motor_prolog.obtener_ruta_actual(self.id_tanque)
        if ruta_nueva:
            self.ruta_actual = ruta_nueva
            self.frames_atascado = 0

    def mover_segun_ruta(self, mapa, otros_tanques):
        """
        Avanza el tanque un paso por la ruta calculada por Prolog.

        Cooldown: cada tipo tiene un delay distinto (DELAY_POR_VELOCIDAD) para
        que los enemigos se muevan casilla por casilla con pausas visibles,
        en lugar de recorrer el mapa a 60 celdas por segundo.

        Detección de atasco: si el tanque intenta moverse pero no puede
        (muro o colisión) durante 45 intentos consecutivos, descarta la ruta
        y solicita una nueva de urgencia.
        """
        if not self.ruta_actual or len(self.ruta_actual) < 2:
            return

        # Respetar el cooldown antes de intentar mover
        ahora = pygame.time.get_ticks()
        delay = DELAY_POR_VELOCIDAD.get(self.tipo, 200)
        if ahora - self.ultimo_movimiento < delay:
            return  # Aún no es tiempo de mover; no contar como atasco

        siguiente = self.ruta_actual[1]
        pos_antes = (self.x, self.y)
        self.mover_a_punto(siguiente[0], siguiente[1], mapa, otros_tanques)

        if self.x == siguiente[0] and self.y == siguiente[1]:
            # Movimiento exitoso: avanzar en la ruta y registrar timestamp
            self.ruta_actual.pop(0)
            self.frames_atascado = 0
            self.ultimo_movimiento = ahora
        elif (self.x, self.y) == pos_antes:
            # El tanque no se movió: incrementar contador de atasco
            self.frames_atascado += 1
            if self.frames_atascado >= 45:  # ~0.75 s atascado → pedir nueva ruta
                self.ruta_actual = []
                self.frames_atascado = 0
                self._pedir_ruta_urgente = True
