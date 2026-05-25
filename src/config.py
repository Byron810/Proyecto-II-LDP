# Constantes del juego
ANCHO_VENTANA = 800
ALTO_VENTANA = 600
TAMANO_CELDA = 40

# Colores (RGB)
NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)
VERDE = (0, 255, 0)
ROJO = (255, 0, 0)
AZUL = (0, 0, 255)
GRIS = (128, 128, 128)
MARRON = (139, 69, 19)
AMARILLO = (255, 215, 0)
NARANJA  = (255, 165, 0)
VERDE_OSCURO = (34, 139, 34)

# Direcciones
ARRIBA = 0
DERECHA = 1
ABAJO = 2
IZQUIERDA = 3

# Velocidades
VELOCIDAD_TANQUE = 5
VELOCIDAD_BALA = 10
TIEMPO_ENTRE_DISPAROS = 30  # frames
TIEMPO_DECISION_ENEMIGO = 2000  # frames (1 segundo a 60 FPS)

# Delay en ms entre movimientos de enemigos según tipo (mayor velocidad → menor delay)
# Jugador a 100ms de repeat → enemigos ligeramente más lentos para ser esquivables
DELAY_POR_VELOCIDAD = {1: 200, 2: 150, 3: 300}  # tipo: ms

# Tipos de tanques enemigos
TIPO_1 = 1  # Normal: velocidad normal, vida normal
TIPO_2 = 2  # Rápido: más velocidad, menos vida
TIPO_3 = 3  # Resistente: más vida, menos velocidad

# IA enemigos
DISTANCIA_DISPARO  = 6   # celdas (distancia Manhattan) para que el enemigo dispare
PROB_DISPARO       = 5   # % de probabilidad de disparar por frame cuando está en rango

# Spawn del jugador
MIN_DISTANCIA_SPAWN = 7  # distancia mínima (Manhattan) entre jugador y enemigos/objetivos al aparecer
TIEMPO_INVULNERABLE = 2000  # ms de invulnerabilidad al aparecer/respawnear

# Estados del juego
ESTADO_MENU      = 0
ESTADO_JUGANDO   = 1
ESTADO_GAME_OVER = 2
ESTADO_VICTORIA  = 3