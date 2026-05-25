%  Hechos dinamicos cargados desde Python (via PySwip + assertz):
%    celda(X, Y, Tipo)              Tipo = libre | muro
%    tanque(ID, X, Y)               posicion de cada tanque enemigo
%    jugador(X, Y)                  posicion actual del jugador
%    jugador_prev(X, Y)             posicion anterior del jugador
%    objetivo_tanque(ID, OX, OY)    objetivo asignado al tanque ID
%
%  Punto de entrada desde Python:
%    ruta(TanqueID, Camino)         devuelve la lista de celdas del camino

:- dynamic celda/3.
:- dynamic tanque/3.
:- dynamic jugador/2.
:- dynamic jugador_prev/2.
:- dynamic objetivo_tanque/3.

% Limite maximo de nodos por consulta (evita colgarse en mapas complejos)
limite_nodos(150).

% ============================================================
%  Limpieza (utilitario)
% ============================================================

limpiar :-
    retractall(celda(_,_,_)),
    retractall(tanque(_,_,_)),
    retractall(jugador(_,_)),
    retractall(jugador_prev(_,_)),
    retractall(objetivo_tanque(_,_,_)).

% ============================================================
%  Heuristica: distancia Manhattan
%  Estima el costo desde un nodo hasta el destino.
%  Se usa para ordenar los vecinos en cada paso del DFS.
% ============================================================

heuristica((X1,Y1), (X2,Y2), D) :-
    D is abs(X1-X2) + abs(Y1-Y2).

% ============================================================
%  Movimientos validos en las 4 direcciones cardinales.
%  Una celda es transitable si es 'libre' y no hay tanque en ella.
% ============================================================

movimiento((X,Y), (X2,Y)) :-
    X2 is X+1,
    celda(X2,Y,libre),
    \+ tanque(_, X2,Y).
movimiento((X,Y), (X2,Y)) :-
    X2 is X-1,
    X2 >= 0,
    celda(X2,Y,libre),
    \+ tanque(_, X2,Y).
movimiento((X,Y), (X,Y2)) :-
    Y2 is Y+1,
    celda(X,Y2,libre),
    \+ tanque(_, X,Y2).
movimiento((X,Y), (X,Y2)) :-
    Y2 is Y-1,
    Y2 >= 0,
    celda(X,Y2,libre),
    \+ tanque(_, X,Y2).

% ============================================================
%  Busqueda DFS con heuristica (algoritmo activo)
%
%  Explora en profundidad: sigue el camino mas prometedor hasta
%  llegar al destino o agotar el limite de nodos. En cada nodo
%  ordena los vecinos por distancia Manhattan (el mas cercano
%  al destino se explora primero). Usa lista de visitados para
%  evitar ciclos. Si falla, Prolog retrocede (backtracking) y
%  prueba el siguiente vecino.
% ============================================================

dfs(Inicio, Fin, Camino) :-
    limite_nodos(Limite),
    dfs_aux(Inicio, Fin, [Inicio], CaminoRev, Limite),
    reverse(CaminoRev, Camino).

% Caso base: llegamos al destino
dfs_aux(Fin, Fin, Visitados, Visitados, _) :- !.

% Limite de nodos agotado: fallar limpiamente
dfs_aux(_, _, _, _, 0) :- !, fail.

% Caso recursivo: generar vecinos validos no visitados,
% ordenarlos por heuristica (menor distancia al destino primero)
% y explorar en profundidad siguiendo el primero de la lista.
% Si ese camino no llega al destino, Prolog hace backtracking
% y prueba el siguiente vecino (DFS con retroceso).
dfs_aux(Actual, Fin, Visitados, Resultado, Limite) :-
    NuevoLimite is Limite - 1,
    findall(
        (H, Vecino),
        (
            movimiento(Actual, Vecino),
            \+ member(Vecino, Visitados),
            heuristica(Vecino, Fin, H)
        ),
        Vecinos
    ),
    Vecinos \= [],
    sort(Vecinos, VecinosOrdenados),   % ordena ascendente por H
    member((_, Siguiente), VecinosOrdenados),
    dfs_aux(Siguiente, Fin, [Siguiente|Visitados], Resultado, NuevoLimite).

% ============================================================
%  Busqueda A* con limite de nodos  [ALTERNATIVA — no activa]
%
%  A diferencia del DFS, A* mantiene una lista global de nodos
%  abiertos ordenada por f = costo_acumulado + heuristica.
%  Siempre expande el nodo con menor f, garantizando la ruta
%  optima pero con mayor uso de memoria.
%  Se deja aqui como referencia; para activarlo reemplazar
%  las llamadas a dfs/3 en decidir/3 por astar/3.
% ============================================================

% astar(Inicio, Fin, Camino) :-
%     heuristica(Inicio, Fin, H),
%     limite_nodos(Limite),
%     astar_aux([(H, [Inicio])], Fin, CaminoInverso, Limite),
%     reverse(CaminoInverso, Camino).
%
% % Caso base: llegamos al destino
% astar_aux([(_, [Fin|Ruta])|_], Fin, [Fin|Ruta], _) :- !.
%
% % Limite de nodos agotado: fallar
% astar_aux(_, _, _, 0) :- !, fail.
%
% % Caso recursivo: expandir el nodo mas prometedor de la lista abierta
% astar_aux([(_, Camino)|Resto], Fin, Resultado, Limite) :-
%     NuevoLimite is Limite - 1,
%     Camino = [Actual|_],
%     findall(
%         (NuevaHeur, [Vecino|Camino]),
%         (
%             movimiento(Actual, Vecino),
%             \+ member(Vecino, Camino),
%             heuristica(Vecino, Fin, H),
%             length(Camino, Len),
%             NuevaHeur is Len + 1 + H
%         ),
%         NuevosCaminos
%     ),
%     append(Resto, NuevosCaminos, Todos),
%     sort(Todos, TodosOrdenados),
%     astar_aux(TodosOrdenados, Fin, Resultado, NuevoLimite).

% ============================================================
%  Motor de decision — decidir/3
%
%  Evalua el contexto de cada tanque y elige uno de 4 comportamientos:
%    retroceder  — el jugador esta muy cerca (< 3 celdas)
%    atacar      — el jugador esta a distancia media (3-8 celdas)
%    emboscar    — el jugador esta lejos y se acerca al tanque
%    defender    — el jugador esta lejos y se aleja (o esta estatico)
%
%  El orden de las clausulas define la prioridad.
%  El corte (!) evita backtracking innecesario entre comportamientos.
% ============================================================

% -- Comportamiento 1: RETROCEDER --
% El jugador esta muy cerca (< 3 celdas). El tanque da un paso en la
% direccion que mas lo aleja del jugador (comparando todos los movimientos validos).
decidir(TanqueID, retroceder, Camino) :-
    tanque(TanqueID, TX, TY),
    jugador(JX, JY),
    heuristica((TX,TY), (JX,JY), D),
    D < 3,
    !,
    % Recolectar movimientos validos con su distancia resultante al jugador
    findall(
        (Hdist, VX, VY),
        (   movimiento((TX,TY), (VX,VY)),
            heuristica((VX,VY), (JX,JY), Hdist)
        ),
        Movs
    ),
    (   Movs \= []
    ->  % msort ordena ascendente; last/2 obtiene el de mayor distancia
        msort(Movs, Sorted),
        last(Sorted, (_, BX, BY)),
        Camino = [(TX,TY), (BX,BY)]
    ;   Camino = [(TX,TY)]  % sin movimientos validos: quedarse
    ).

% -- Comportamiento 2: ATACAR --
% El jugador esta a distancia media (3-8 celdas). El tanque lo persigue
% usando DFS con heuristica para calcular la ruta.
decidir(TanqueID, atacar, Camino) :-
    tanque(TanqueID, TX, TY),
    jugador(JX, JY),
    heuristica((TX,TY), (JX,JY), D),
    D >= 3, D =< 8,
    !,
    (   dfs((TX,TY), (JX,JY), Camino)
    ->  true
    ;   Camino = []
    ).

% -- Comportamiento 3: EMBOSCAR --
% El jugador esta lejos (> 8) pero se esta acercando al tanque.
% El tanque se mueve a una posicion perpendicular para interceptar.
decidir(TanqueID, emboscar, Camino) :-
    tanque(TanqueID, TX, TY),
    jugador(JX, JY),
    jugador_prev(JPX, JPY),
    heuristica((TX,TY), (JX,JY), D),
    D > 8,
    % Detectar si el jugador se acerca: distancia actual < distancia previa
    heuristica((TX,TY), (JPX,JPY), DPrev),
    D < DPrev,
    !,
    % Calcular desplazamiento del jugador
    DirX is JX - JPX,
    DirY is JY - JPY,
    % Posicion perpendicular: desplazar 3 celdas en eje opuesto al movimiento
    (DirX =:= 0 -> PerpX is 3 ; PerpX is 0),
    (DirY =:= 0 -> PerpY is 3 ; PerpY is 0),
    EmbX is JX + PerpX,
    EmbY is JY + PerpY,
    % Verificar que la celda de emboscada sea transitable
    (   celda(EmbX, EmbY, libre)
    ->  (   dfs((TX,TY), (EmbX,EmbY), Camino)
        ->  true
        ;   Camino = []
        )
    ;   % Si no es transitable, ir directamente hacia el jugador
        (   dfs((TX,TY), (JX,JY), Camino)
        ->  true
        ;   Camino = []
        )
    ).

% -- Comportamiento 4: DEFENDER --
% El jugador esta lejos (> 8) y se aleja o esta estatico.
% El tanque vuelve a custodiar su objetivo asignado.
decidir(TanqueID, defender, Camino) :-
    tanque(TanqueID, TX, TY),
    jugador(JX, JY),
    heuristica((TX,TY), (JX,JY), D),
    D > 8,
    objetivo_tanque(TanqueID, OX, OY),
    !,
    (   dfs((TX,TY), (OX,OY), Camino)
    ->  true
    ;   Camino = []
    ).

% -- Fallback: ATACAR sin condicion de distancia --
% Si ninguna clausula anterior aplica, ir hacia el jugador.
decidir(TanqueID, atacar, Camino) :-
    tanque(TanqueID, TX, TY),
    jugador(JX, JY),
    (   dfs((TX,TY), (JX,JY), Camino)
    ->  true
    ;   Camino = []
    ).

% ============================================================
%  Punto de entrada principal — llamado desde Python
%  ruta/2 es un wrapper de decidir/3 que descarta la accion.
% ============================================================

ruta(TanqueID, Camino) :-
    decidir(TanqueID, _Accion, Camino).
