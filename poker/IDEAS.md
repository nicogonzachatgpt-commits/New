# App de Poker: Estadísticas y Calculadora de Manos — Ideas y Roadmap

Documento de ideas para una app (Texas Hold'em) que ayude con **estadísticas de tu juego** y con **las manos que podrías formar** en cada situación.

---

## 1. Módulos de la app

### A. Calculadora de manos y probabilidades ⭐ (el corazón de la app)

Ingresás tus 2 cartas y las comunitarias visibles, y la app te muestra:

- **Tu mejor mano actual** (par, doble par, trío, etc.).
- **Probabilidad de terminar con cada tipo de mano al river**: par, doble par, trío, escalera, color, full house, poker, escalera de color.
- **Outs de cada proyecto** y probabilidad de completarlo (exacta + regla del 2 y 4).
- **Equity contra el rango estimado del rival** (simulación Monte Carlo): "tenés 62% de ganar contra un rango de pares altos y broadways".
- **Pot odds**: cuánto conviene pagar según el tamaño del pozo ("necesitás 25% de equity para pagar esta apuesta; tenés 35% → call rentable").

Tabla de referencia que la app puede calcular y enseñar:

| Proyecto | Outs | Flop → River | Turn → River |
|---|---|---|---|
| Color (flush draw) | 9 | ~35% | ~19,6% |
| Escalera abierta (OESD) | 8 | ~31,5% | ~17,4% |
| Escalera interna (gutshot) | 4 | ~16,5% | ~8,7% |
| Dos overcards | 6 | ~24,1% | ~13,0% |
| Color + escalera abierta | 15 | ~54% | ~32,6% |

**Regla del 2 y 4** (modo "aprendizaje" de la app): outs × 4 en el flop, outs × 2 en el turn ≈ probabilidad de completar.

**Detalle técnico**: con el flop visible quedan 47 cartas → C(47,2) = 1.081 combinaciones de turn+river. Se puede calcular **exacto** en milisegundos enumerando todas. Para preflop o contra varios rivales conviene Monte Carlo (~100.000 manos simuladas).

### B. Estadísticas de tu juego (estilo PokerTracker)

- **Registro de sesiones**: fecha, lugar/sala, cash o torneo, stakes, buy-in, resultado, horas jugadas.
- **Gráfica de bankroll** en el tiempo, ganancia por hora, por stake, por lugar, por día de la semana.
- Si además registrás manos, stats clásicas:
  - **VPIP** (% de manos que jugás voluntariamente)
  - **PFR** (% de subidas preflop)
  - **3-bet%**, **fold al 3-bet**
  - **AF** (factor de agresión), **C-bet%**
  - **WTSD** (% de veces que llegás al showdown) y **W$SD** (% que ganás al llegar)
- **Por posición**: cuánto ganás/perdés en botón, ciegas, early position → detecta fugas ("perdés plata defendiendo la ciega grande de más").

### C. Registro y revisión de manos

- Carga rápida de manos con una UI de mesa (tocás las cartas, las acciones).
- **Replayer visual** calle por calle.
- Marcar manos dudosas con tags ("bluff", "cooler", "¿fold correcto?") y notas.
- Análisis EV de la decisión: "el call en el turn fue -EV por X fichas".

### D. Perfiles de rivales (ideal si jugás con el mismo grupo)

- Ficha por jugador: tags (TAG, LAG, calling station, nit), notas, stats acumuladas.
- "Contra Juan: 3-betea mucho desde el botón, se tira a la doble apuesta."
- Sus stats se van armando solas a partir de las manos que registrás.

### E. Estudio y entrenamiento

- **Charts de rangos preflop** por posición (open-raise, 3-bet, defensa de ciegas), editables.
- **Quiz de odds**: "tenés proyecto de color en el flop, ¿qué % tenés de completarlo?"
- **Quiz de decisiones**: te muestra un spot y elegís fold/call/raise; la app te dice el EV de cada opción.
- Repetición espaciada para memorizar rangos.

### F. Extras para partidas caseras

- **Timer de ciegas** para torneos caseros (niveles, sonido, estructura configurable).
- **Calculadora de premios / ICM** para acordar pagos cuando quedan pocos.
- Caja/banco: quién compró cuántas fichas, liquidación al final.

---

## 2. MVP sugerido (por fases)

1. **Fase 1 — Calculadora de probabilidades**: cartas propias + board → mejor mano actual, probabilidades por tipo de mano, outs, pot odds. Es lo más útil de entrada y no necesita base de datos.
2. **Fase 2 — Sesiones y bankroll**: alta de sesiones + gráficas. Datos guardados localmente.
3. **Fase 3 — Registro de manos y stats**: replayer, VPIP/PFR/etc., stats por posición.
4. **Fase 4 — Rivales + entrenador**: perfiles, quizzes, charts de rangos.

---

## 3. Stack técnico sugerido

- **Web app / PWA** con React (Next.js o Vite) + TypeScript → la usás en el celular sin pasar por las stores, funciona offline.
- **Motor de poker propio en TypeScript** (evaluador de 7 cartas + enumeración/Monte Carlo en un Web Worker para no trabar la UI). Alternativa: librerías como `pokersolver` (JS) o `treys` (Python) si el backend fuera Python.
- **Datos**: IndexedDB/localStorage al principio; SQLite o Supabase más adelante si querés sincronizar entre dispositivos.
- **Gráficas**: Recharts.
- **Mobile nativa** (más adelante, si hace falta): React Native/Expo reutilizando el motor de TypeScript.

---

## 4. Modelo de datos (borrador)

```
Session  { id, fecha, lugar, tipo (cash|torneo), stakes, buyIn, cashOut, horas }
Hand     { id, sessionId, cartasHero, board, posicion, acciones[], resultado, tags[], notas }
Action   { calle (preflop|flop|turn|river), jugador, tipo (fold|check|call|bet|raise), monto }
Player   { id, nombre, tags[], notas }   // rivales
```

Las estadísticas (VPIP, PFR, bankroll, etc.) se **derivan** de estas tablas; no se guardan a mano.

---

## 5. Nota importante

Las salas online (PokerStars, GGPoker, etc.) **prohíben el software de asistencia en tiempo real (RTA)** y pueden cerrar cuentas por usarlo durante la partida. Esta app apunta a: **estudio post-sesión, partidas caseras en vivo y entrenamiento** — ahí es 100% legítima y es donde más valor da.
