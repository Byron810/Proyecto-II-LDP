:- dynamic celda/3.
:- dynamic tanque/3.
:- dynamic jugador/2.

limpiar :-
    retractall(celda(_,_,_)),
    retractall(tanque(_,_,_)),
    retractall(jugador(_,_)).

% Heurística: distancia Manhattan
heuristica((X1,Y1), (X2,Y2), D) :-
    D is abs(X1-X2) + abs(Y1-Y2).

% Movimientos válidos
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

% Búsqueda A*
astar(Inicio, Fin, Camino) :-
    heuristica(Inicio, Fin, H),
    astar_aux([(H, [Inicio])], Fin, CaminoInverso),
    reverse(CaminoInverso, Camino).

astar_aux([(_, [Fin|Ruta])|_], Fin, [Fin|Ruta]) :- !.

astar_aux([(_, Camino)|Resto], Fin, Resultado) :-
    Camino = [Actual|_],
    findall((NuevaHeur, [Vecino|Camino]), (
        movimiento(Actual, Vecino),
        \+ member(Vecino, Camino),
        heuristica(Vecino, Fin, H),
        length(Camino, Len),
        NuevaHeur is Len + 1 + H
    ), NuevosCaminos),
    append(Resto, NuevosCaminos, Todos),
    sort(Todos, TodosOrdenados),
    astar_aux(TodosOrdenados, Fin, Resultado).

% Punto de entrada
ruta(TanqueID, Camino) :-
    tanque(TanqueID, TX, TY),
    jugador(JX, JY),
    astar((TX,TY), (JX,JY), Camino).
