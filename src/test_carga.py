from pyswip import Prolog
import os
import sys

print("=== PRUEBA DE CARGA DE PROLOG ===\n")

# Obtener ruta absoluta al archivo Prolog
ruta_actual = os.path.dirname(os.path.abspath(__file__))
print(f"Directorio actual (src): {ruta_actual}")

ruta_prolog = os.path.join(ruta_actual, "..", "prolog", "tank_attack.pl")
ruta_prolog = os.path.abspath(ruta_prolog)
print(f"Buscando archivo Prolog en: {ruta_prolog}")

# Verificar si el archivo existe
if os.path.exists(ruta_prolog):
    print("✓ Archivo encontrado")
    
    # Mostrar contenido del archivo
    print("\n=== CONTENIDO DEL ARCHIVO ===")
    with open(ruta_prolog, 'r', encoding='utf-8') as f:
        contenido = f.read()
        print(contenido[:500])  # Mostrar primeras 500 caracteres
        print("...\n")
else:
    print(f"✗ Archivo NO encontrado")
    print(f"Creando archivo Prolog...")
    
    # Crear directorio si no existe
    os.makedirs(os.path.dirname(ruta_prolog), exist_ok=True)
    
    # Crear archivo Prolog básico
    codigo_prolog = ''':- dynamic celda/3.
:- dynamic tanque/3.
:- dynamic jugador/2.

limpiar :-
    retractall(celda(_,_,_)),
    retractall(tanque(_,_,_)),
    retractall(jugador(_,_)).

transitable(X,Y) :-
    celda(X,Y,libre),
    \\+ tanque(_, X,Y).

movimiento(X,Y,X2,Y) :- X2 is X+1, transitable(X2,Y).
movimiento(X,Y,X2,Y) :- X2 is X-1, X2>=0, transitable(X2,Y).
movimiento(X,Y,X,Y2) :- Y2 is Y+1, transitable(X,Y2).
movimiento(X,Y,X,Y2) :- Y2 is Y-1, Y2>=0, transitable(X,Y2).

bfs(Inicio, Fin, Camino) :-
    bfs_aux([[Inicio]], Fin, CaminoReves),
    reverse(CaminoReves, Camino).

bfs_aux([[Fin|Ruta]|_], Fin, [Fin|Ruta]).
bfs_aux([Camino|Otros], Fin, Resultado) :-
    Camino = [Actual|_],
    findall([Nuevo|Camino], (
        movimiento(Actual, X, Y),
        Nuevo = (X,Y),
        \\+ member(Nuevo, Camino)
    ), NuevosCaminos),
    append(Otros, NuevosCaminos, Todos),
    bfs_aux(Todos, Fin, Resultado).

ruta_tanque(TanqueID, Ruta) :-
    tanque(TanqueID, TX, TY),
    jugador(JX, JY),
    bfs((TX,TY), (JX,JY), Ruta).
'''
    with open(ruta_prolog, 'w', encoding='utf-8') as f:
        f.write(codigo_prolog)
    print("✓ Archivo Prolog creado")

# Probar cargar archivo
print("\n=== CARGANDO ARCHIVO EN PROLOG ===")
try:
    prolog = Prolog()
    prolog.consult(ruta_prolog)
    print("✓ Archivo cargado exitosamente")
except Exception as e:
    print(f"✗ Error al cargar: {e}")
    sys.exit(1)

# Probar limpiar
print("\n=== PROBANDO LIMPIAR ===")
try:
    list(prolog.query("limpiar"))
    print("✓ Limpiar ejecutado")
except Exception as e:
    print(f"✗ Error en limpiar: {e}")

# Agregar datos de prueba
print("\n=== AGREGANDO DATOS DE PRUEBA ===")
try:
    # Agregar celdas (mapa 3x3)
    for x in range(3):
        for y in range(3):
            list(prolog.query(f"assertz(celda({x},{y},libre))"))
    print("✓ Celdas agregadas")
    
    # Agregar tanque
    list(prolog.query("assertz(tanque(1,0,0))"))
    print("✓ Tanque agregado")
    
    # Agregar jugador
    list(prolog.query("assertz(jugador(2,0))"))
    print("✓ Jugador agregado")
    
except Exception as e:
    print(f"✗ Error al agregar datos: {e}")

# Probar consultas
print("\n=== PROBANDO CONSULTAS ===")

# 1. Verificar transitable
print("\n1. Verificando celdas transitables:")
try:
    resultados = list(prolog.query("transitable(1,0)"))
    print(f"   ¿(1,0) es transitable? {'SI' if resultados else 'NO'}")
    
    resultados = list(prolog.query("transitable(0,0)"))
    print(f"   ¿(0,0) es transitable? {'SI' if resultados else 'NO'}")
except Exception as e:
    print(f"   Error: {e}")

# 2. Verificar movimientos
print("\n2. Verificando movimientos desde (0,0):")
try:
    resultados = list(prolog.query("movimiento(0,0,X,Y)"))
    if resultados:
        for r in resultados:
            print(f"   → ({r['X']},{r['Y']})")
    else:
        print("   No hay movimientos")
except Exception as e:
    print(f"   Error: {e}")

# 3. Buscar ruta
print("\n3. Buscando ruta del tanque al jugador:")
try:
    resultados = list(prolog.query("ruta_tanque(1, Ruta)"))
    if resultados:
        ruta = resultados[0]['Ruta']
        print(f"   ✓ Ruta encontrada: {ruta}")
        
        # Convertir a formato legible
        puntos = []
        for p in ruta:
            if hasattr(p, 'args'):
                x = int(p.args[0])
                y = int(p.args[1])
                puntos.append((x, y))
        print(f"   ✓ Puntos: {puntos}")
    else:
        print("   ✗ No se encontró ruta")
except Exception as e:
    print(f"   Error: {e}")

print("\n=== PRUEBA COMPLETADA ===")