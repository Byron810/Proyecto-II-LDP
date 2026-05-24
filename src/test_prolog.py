from pyswip import Prolog
import os

print("=== TEST DE RUTA CON RUTA EXACTA ===\n")

# Ruta exacta al archivo Prolog
ruta_prolog = r"c:\Users\cuent\OneDrive - Estudiantes ITCR\Lenguajes de Programación\Tank-Attack\prolog\tank_attack.pl"

print(f"Usando archivo: {ruta_prolog}")
print(f"Archivo existe: {os.path.exists(ruta_prolog)}")

# Cargar Prolog
prolog = Prolog()
prolog.consult(ruta_prolog)

# Limpiar datos previos
print("\n1. Limpiando...")
list(prolog.query("limpiar"))

# Crear mapa 3x3
print("2. Creando mapa 3x3...")
for x in range(3):
    for y in range(3):
        list(prolog.query(f"assertz(celda({x},{y},libre))"))
print("   Mapa creado")

# Agregar posiciones
print("3. Agregando tanque y jugador...")
list(prolog.query("assertz(tanque(1,0,0))"))
list(prolog.query("assertz(jugador(2,0))"))
print("   Tanque en (0,0)")
print("   Jugador en (2,0)")

# Buscar ruta
print("\n4. Buscando ruta...")
resultados = list(prolog.query("ruta(1, Camino)"))

if resultados:
    camino = resultados[0]['Camino']
    print(f"\n>>> RUTA ENCONTRADA: {camino}")
    
    # Convertir a string y extraer números
    camino_str = str(camino)
    print(f"   Como string: {camino_str}")
    
    # Extraer los puntos usando split
    import re
    numeros = re.findall(r'\d+', camino_str)
    print(f"   Números encontrados: {numeros}")
    
    if len(numeros) >= 6:
        puntos = []
        for i in range(0, len(numeros), 2):
            if i+1 < len(numeros):
                puntos.append((int(numeros[i]), int(numeros[i+1])))
        print(f"\n>>> PUNTOS: {puntos}")
    else:
        print("\n>>> PUNTOS: No se pudieron extraer")
else:
    print("\n>>> NO SE ENCONTRO RUTA")

print("\n=== FIN ===")