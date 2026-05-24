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

# Tipos de tanques enemigos
TIPO_1 = 1  # Normal: velocidad normal, vida normal
TIPO_2 = 2  # Rápido: más velocidad, menos vida
TIPO_3 = 3  # Resistente: más vida, menos velocidad