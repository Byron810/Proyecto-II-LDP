from pyswip import Prolog
#import os
import re
#import signal
import time 

class MotorProlog:
    def __init__(self):
        ruta_prolog = r"c:\Users\cuent\OneDrive - Estudiantes ITCR\Lenguajes de Programación\Tank-Attack\prolog\tank_attack.pl"
        self.prolog = Prolog()
        self.prolog.consult(ruta_prolog)
        
    def limpiar(self):
        try:
            list(self.prolog.query("limpiar"))
        except:
            pass
        
    def actualizar_mapa(self, mapa, tanques, pos_jugador):
        self.limpiar()
        for x in range(len(mapa)):
            for y in range(len(mapa[0])):
                tipo = mapa[x][y]
                list(self.prolog.query(f"assertz(celda({x},{y},{tipo}))"))
        for i, tanque in enumerate(tanques):
            if hasattr(tanque, 'x') and hasattr(tanque, 'y'):
                list(self.prolog.query(f"assertz(tanque({i},{tanque.x},{tanque.y}))"))
        list(self.prolog.query(f"assertz(jugador({pos_jugador[0]},{pos_jugador[1]}))"))
    
    def obtener_ruta(self, tanque_id, x, y, jugador_x, jugador_y):
        inicio = time.time()
        try:
            # Actualizar posiciones
            list(self.prolog.query(f"retractall(tanque({tanque_id},_,_))"))
            list(self.prolog.query(f"assertz(tanque({tanque_id},{x},{y}))"))
            list(self.prolog.query(f"retractall(jugador(_,_))"))
            list(self.prolog.query(f"assertz(jugador({jugador_x},{jugador_y}))"))
            
            # Consulta con límite de tiempo usando un truco: obtener solo el primer resultado
            resultados = list(self.prolog.query(f"ruta({tanque_id}, Camino)"))
            
            if resultados:
                camino = resultados[0]['Camino']
                camino_str = str(camino)
                numeros = re.findall(r'\d+', camino_str)
                puntos = []
                for i in range(0, len(numeros), 2):
                    if i+1 < len(numeros):
                        puntos.append((int(numeros[i]), int(numeros[i+1])))
                # Limitar la ruta a 5 pasos por vez para evitar movimientos largos
                print(f"Consulta Prolog tomó: {time.time() - inicio:.4f} segundos")
                return puntos[:5] if len(puntos) > 5 else puntos
            return []
        except Exception as e:
            print(f"Error en Prolog: {e}")
            return []