from pyswip import Prolog
import os
import re
import time
import threading
import queue


class MotorProlog:
    """
    Motor de integración Python <-> Prolog.

    Todas las consultas Prolog se ejecutan en un hilo dedicado
    para que NUNCA bloqueen el bucle principal del juego.

    Flujo:
      - cargar_mapa_nivel()           → UNA vez al iniciar cada nivel
      - registrar_objetivo_tanque()   → UNA vez por tanque al iniciar nivel
      - solicitar_ruta()              → encola cálculo (no bloquea)
      - obtener_ruta_actual()         → devuelve última ruta calculada (instantáneo)
    """

    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ruta_prolog = os.path.join(base_dir, "prolog", "tank_attack.pl")
        self.prolog = Prolog()
        self.prolog.consult(ruta_prolog)

        # Rutas calculadas: tanque_id -> lista de (x, y)
        self._rutas = {}

        # Cola de tareas para el hilo Prolog
        self._cola = queue.Queue()

        # IDs con solicitud pendiente (evita duplicados en cola)
        self._en_cola = set()

        # Hilo dedicado — todo Prolog pasa por aquí
        self._hilo = threading.Thread(target=self._worker, daemon=True)
        self._hilo.start()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def cargar_mapa_nivel(self, mapa):
        """
        Carga las celdas del mapa en Prolog. Llamar UNA VEZ por nivel.
        Los muros no cambian durante el nivel, así que no se recargan.
        """
        self._cola.put(('cargar_mapa', mapa))

    def registrar_objetivo_tanque(self, tanque_id, obj_x, obj_y):
        """
        Registra en Prolog el objetivo asignado a un tanque enemigo.
        Se usa en el comportamiento 'defender' de la IA.
        Llamar después de cargar_mapa_nivel, una vez por tanque.
        """
        self._cola.put(('objetivo', (tanque_id, obj_x, obj_y)))

    def solicitar_ruta(self, tanque_id, x, y, jugador_x, jugador_y):
        """
        Solicita el cálculo de ruta para un tanque. No bloquea.
        El resultado se recupera con obtener_ruta_actual().
        """
        if tanque_id not in self._en_cola:
            self._en_cola.add(tanque_id)
            self._cola.put(('ruta', (tanque_id, x, y, jugador_x, jugador_y)))

    def obtener_ruta_actual(self, tanque_id):
        """
        Retorna y CONSUME la última ruta calculada para el tanque.
        Retorna [] si no hay ruta nueva desde la última lectura.
        (pop garantiza que la misma ruta no se aplica en múltiples frames)
        """
        return self._rutas.pop(tanque_id, [])

    # ------------------------------------------------------------------
    # Hilo trabajador
    # ------------------------------------------------------------------

    def _worker(self):
        """Procesa tareas Prolog de forma secuencial en un hilo separado."""
        while True:
            tarea = self._cola.get()
            if tarea is None:
                break
            tipo = tarea[0]
            try:
                if tipo == 'cargar_mapa':
                    self._cargar_mapa_sync(tarea[1])
                elif tipo == 'objetivo':
                    self._registrar_objetivo_sync(*tarea[1])
                elif tipo == 'ruta':
                    self._calcular_ruta_sync(*tarea[1])
            except Exception as e:
                print(f"[Prolog Worker] Error en tarea '{tipo}': {e}")
                if tipo == 'ruta':
                    self._en_cola.discard(tarea[1][0])

    def _cargar_mapa_sync(self, mapa):
        """Limpia Prolog y recarga todas las celdas del mapa."""
        list(self.prolog.query("retractall(celda(_,_,_))"))
        list(self.prolog.query("retractall(tanque(_,_,_))"))
        list(self.prolog.query("retractall(jugador(_,_))"))
        list(self.prolog.query("retractall(jugador_prev(_,_))"))
        list(self.prolog.query("retractall(objetivo_tanque(_,_,_))"))
        for x in range(len(mapa)):
            for y in range(len(mapa[0])):
                list(self.prolog.query(
                    f"assertz(celda({x},{y},{mapa[x][y]}))"))

    def _registrar_objetivo_sync(self, tanque_id, obj_x, obj_y):
        """Registra el objetivo de un tanque en la base de datos Prolog."""
        list(self.prolog.query(
            f"retractall(objetivo_tanque({tanque_id},_,_))"))
        list(self.prolog.query(
            f"assertz(objetivo_tanque({tanque_id},{obj_x},{obj_y}))"))

    def _calcular_ruta_sync(self, tanque_id, x, y, jugador_x, jugador_y):
        """
        Actualiza posiciones dinámicas y ejecuta decidir/3 para obtener la ruta.
        Guarda la posición anterior del jugador para que Prolog detecte
        si se está acercando (comportamiento 'emboscar').
        """
        self._en_cola.discard(tanque_id)
        inicio = time.time()
        try:
            # Guardar posición anterior del jugador antes de actualizar
            prev = list(self.prolog.query("jugador(X,Y)"))
            list(self.prolog.query("retractall(jugador_prev(_,_))"))
            if prev:
                jpx, jpy = prev[0]['X'], prev[0]['Y']
            else:
                jpx, jpy = jugador_x, jugador_y
            list(self.prolog.query(f"assertz(jugador_prev({jpx},{jpy}))"))

            # Actualizar posición del tanque y del jugador
            list(self.prolog.query(f"retractall(tanque({tanque_id},_,_))"))
            list(self.prolog.query(f"assertz(tanque({tanque_id},{x},{y}))"))
            list(self.prolog.query("retractall(jugador(_,_))"))
            list(self.prolog.query(f"assertz(jugador({jugador_x},{jugador_y}))"))

            # Pedir ruta (ruta/2 es wrapper de decidir/3)
            resultados = list(self.prolog.query(f"ruta({tanque_id}, Camino)"))

            if resultados:
                camino_str = str(resultados[0]['Camino'])
                numeros = re.findall(r'\d+', camino_str)
                puntos = [
                    (int(numeros[i]), int(numeros[i + 1]))
                    for i in range(0, len(numeros) - 1, 2)
                ]
                self._rutas[tanque_id] = puntos[:6]
            else:
                self._rutas[tanque_id] = []

            print(f"[Prolog] Tanque {tanque_id}: {time.time()-inicio:.4f}s "
                  f"-> {len(self._rutas.get(tanque_id, []))} pasos")
        except Exception as e:
            print(f"[Prolog] Error ruta tanque {tanque_id}: {e}")
            self._rutas[tanque_id] = []
