# Guía Técnica de Bracketing para la Totalidad sin Star Tracker y Control USB (eclipZe)

---

## 1. Resumen y Objetivos

Este documento establece las directrices de captura fotográfica y configuración de horquillado (*bracketing*) para la fase de **totalidad** del eclipse solar del **2 de agosto de 2027** (Sur de España / Cádiz / Tarifa / Luxor). 

Aborda directamente los fallos de trepidación experimentados en el eclipse de **agosto de 2026 en Ponferrada** (evidenciados en las tomas a 1/30s de [`tests/eclipse_2026_1_30/`](file:///d:/software/eclipZe/tests/eclipse_2026_1_30)) y proporciona:
1. El diagnóstico físico y matemático de por qué las fotos a 1/30s resultaron trepidadas.
2. Los límites de tiempo de exposición admisibles a 500 mm sobre trípode rígido fijo (sin montura de seguimiento ecuatorial ni *star tracker*).
3. La calibración óptima del horquillado por hardware de **9 disparos** de la **Nikon Z5 II**.
4. El procedimiento de disparo desatendido por **USB PTP** mediante [core/camera.py](file:///d:/software/eclipZe/core/camera.py) para erradicar al 100% las vibraciones mecánicas.

---

## 2. Diagnóstico de las Tomas a 1/30s de Ponferrada 2026

En el directorio [`tests/eclipse_2026_1_30/`](file:///d:/software/eclipZe/tests/eclipse_2026_1_30) se encuentran 6 tomas correspondientes al último disparo (el más lento) de sendas secuencias de horquillado: `_DSC1429`, `_DSC1438`, `_DSC1447`, `_DSC1456`, `_DSC1474` y `_DSC1483` (todas a `1/30 s`, `f/8.0`, `ISO 200`, `500 mm`).

### 2.1 Demostración de Deriva Celeste (La rotación terrestre no fue la culpable)
Para la **Nikon Z5 II** (sensor de $35.9 \times 23.9\,\text{mm}$, matriz de $6048 \times 4032$ píxeles):
* **Tamaño del píxel:**
  $$p = \frac{35.9\,\text{mm}}{6048} \approx 5.936\,\mu\text{m}$$
* **Escala de placa a 500 mm de focal:**
  $$\text{Scale} = \frac{206265 \cdot 0.005936\,\text{mm}}{500\,\text{mm}} \approx 2.449^{\prime\prime}/\text{píxel}$$
* **Velocidad angular aparente del Sol en agosto:**
  Con una declinación solar de $\delta \approx +17.8^\circ$, la rotación terrestre traslada el Sol a una tasa de:
  $$\omega = 15.041^{\prime\prime}/\text{s} \cdot \cos(17.8^\circ) \approx 14.32^{\prime\prime}/\text{s}$$
* **Deriva en píxeles por segundo:**
  $$v_{\text{deriva}} = \frac{14.32^{\prime\prime}/\text{s}}{2.449^{\prime\prime}/\text{px}} \approx \mathbf{5.84\text{ píxeles/segundo}}$$

A una velocidad de obturación de **$1/30\,\text{s}$**, el desplazamiento solar teórico sobre el sensor fue:

$$\text{Deriva}_{1/30s} = 5.84 \cdot \frac{1}{30} \approx \mathbf{0.195\text{ píxeles}}$$

> [!IMPORTANT]
> Un desplazamiento de **$0.19\text{ píxeles}$** es estrictamente sub-píxel y ópticamente indetectable. El desenfoque y trepidación en las fotos de Ponferrada a 1/30s **no se debió a la falta de star tracker**.

### 2.2 Causas Reales de la Trepidación

1. **Par de torsión angular por pulsación táctil (Disparo manual):**
   Al pulsar el botón disparador directamente con el dedo, la fuerza aplicada sobre el extremo del cuerpo de la cámara actúa sobre un brazo de palanca de más de 40 cm respecto a la rótula. A 500 mm de focal, una micro-oscilación de apenas **$0.05^\circ$** desvía la imagen en el sensor más de **70 píxeles**.
2. **Desplazamiento acumulado del encuadre:**
   Al medir el centro del disco lunar en las tomas de `tests/eclipse_2026_1_30`:
   * Entre `_DSC1447` y `_DSC1456`, el centro saltó **46 píxeles**.
   * En `_DSC1483`, el centro sufrió una desviación brusca de **180 píxeles** verticales provocada por la fuerza física transmitida al trípode.
3. **Colapso de Nitidez (Varianza Laplaciana):**
   * Disparo a $1/1000\,\text{s}$ (`_DSC1326`): Varianza Laplaciana = **$2.916,0$** (bordes extremadamente nítidos).
   * Disparo a $1/30\,\text{s}$ (`_DSC1429`): Varianza Laplaciana = **$118,8$** (pérdida del 96% de acutancia por trepidación).
4. **Vibración de cortinillas (*Shutter Shock*):**
   En trípode a 500 mm, el accionamiento del obturador mecánico en el rango entre 1/15s y 1/60s entra en resonancia armónica si no se usa obturador electrónico.
5. **Deriva del giroscopio del estabilizador (VR):**
   Tener el sistema VR activado cuando el equipo está anclado en trípode genera micro-derivas de compensación espuria que emborronan exposiciones de más de 1/60s.

---

## 3. Modelo Físico: Límites de Exposición sin Star Tracker a 500 mm

La siguiente tabla resume el arrastre celeste admisible para la Nikon Z5 II a 500 mm sobre trípode fijo:

| Tiempo de Exposición ($t$) | Deriva Celeste Teórica | Estado de Nitidez en el Sensor | Viabilidad sin Star Tracker |
| :--- | :--- | :--- | :--- |
| **`1/8000 s`** | $0.0007\text{ px}$ | Perfección absoluta | Óptimo |
| **`1/4000 s`** | $0.0015\text{ px}$ | Perfección absoluta | Óptimo |
| **`1/1000 s`** | $0.0058\text{ px}$ | Perfección absoluta | Óptimo |
| **`1/125 s`** | $0.0467\text{ px}$ | Indetectable | Óptimo |
| **`1/30 s`** | $0.1947\text{ px}$ | Indetectable | **100% Viable (si no se toca la cámara)** |
| **`1/15 s`** | $0.3893\text{ px}$ | Sub-píxel | **100% Viable** |
| **`1/8 s`** | $0.7300\text{ px}$ | Ligeramente visible al 200% | **Completamente seguro** |
| **`1/6 s`** | **$0.9733\text{ px}$** | **Umbral estricto de 1 píxel** | **Límite de nitidez crítica** |
| **`1/4 s`** | **$1.4600\text{ px}$** | Límite aceptable en pantalla/impresión | **Tolerable para corona débil** |
| **`1/2 s`** | $2.9200\text{ px}$ | Pérdida apreciable de detalle radial | Desaconsejado |
| **`1.0 s`** | $5.8400\text{ px}$ | Estrellas y filamentos elípticos | Requiere Star Tracker |
| **`2.0 s`** | $11.6800\text{ px}$ | Borrón evidente de 12 píxeles | Inviable sin seguimiento |

> [!TIP]
> **Regla operativa para 500 mm sin Star Tracker:**  
> Puedes disparar con total seguridad hasta **$1/6\,\text{s}$** (deriva $< 1\text{ px}$) y hasta **$1/4\,\text{s}$** (deriva $\approx 1.4\text{ px}$, imperceptible en streamers difusos).

---

## 4. Configuración del Horquillado (9 Fotos) para la Totalidad 2027

Para el eclipse del 2 de agosto de 2027 (f/8.0, ISO 100 base para aprovechar la menor masa de aire y maximizar rango dinámico), el menú BKT de la Nikon Z5 II ofrece dos alternativas recomendadas:

### 4.1 Opción A: Paso de 1.7 EV (5 clics de 1/3 EV) — Centrado en 1/125s (Recomendado)
Abarca un rango dinámico colosal de **$13.3\,\text{EV}$** sin desperdiciar tomas por tope físico del obturador:

| Disparo | Nivel EV | Tiempo | Estructura Solar Diana | Deriva Celeste a 500 mm |
| :--- | :--- | :--- | :--- | :--- |
| **#1** | $-6.7\text{ EV}$ | **`1/8000 s`** | Cromosfera extrema y valles solares | $0.00\text{ px}$ |
| **#2** | $-5.0\text{ EV}$ | **`1/4000 s`** | Bucles de protuberancias ($H\alpha$) | $0.00\text{ px}$ |
| **#3** | $-3.3\text{ EV}$ | **`1/1250 s`** | Base brillante de la corona interna | $0.00\text{ px}$ |
| **#4** | $-1.7\text{ EV}$ | **`1/400 s`** | Corona interna y penachos polares | $0.01\text{ px}$ |
| **#5** | **`0.0 EV`** | **`1/125 s`** | **Corona media (Punto de anclaje)** | $0.05\text{ px}$ |
| **#6** | $+1.7\text{ EV}$ | **`1/40 s`** | Corona media-externa | $0.15\text{ px}$ |
| **#7** | $+3.3\text{ EV}$ | **`1/13 s`** | Corona externa y filamentos | $0.45\text{ px}$ |
| **#8** | $+5.0\text{ EV}$ | **`1/4 s`** | Streamers lejanos (corona tenue) | **$1.46\text{ px}$ (Límite seguro)** |
| **#9** | $+6.7\text{ EV}$ | **`0.8 s`** | Brillo ceniciento / fondo estelar | $4.67\text{ px}$ (Aceptable para Luna) |

> [!WARNING]
> No fijes el centro en `1/250s` con paso de `1.7 EV`: las tomas #1 y #2 se truncarían ambas a `1/8000s` debido al límite físico del obturador de la Z5 II, perdiendo un disparo del horquillado.

### 4.2 Opción B: Paso de 1.3 EV (4 clics de 1/3 EV) — Centrado en 1/250s (Régimen Zero-Trailing)
Si se desea garantizar matemáticamente que **ninguna foto supere 1 píxel de deriva**:
* Secuencia resultante: **`1/8000s` $\rightarrow$ `1/4000s` $\rightarrow$ `1/1600s` $\rightarrow$ `1/640s` $\rightarrow$ `1/250s` $\rightarrow$ `1/100s` $\rightarrow$ `1/40s` $\rightarrow$ `1/15s` $\rightarrow$ `1/6s`**.
* La toma más lenta (`1/6s`) genera un arrastre de únicamente **$0.97\text{ px}$**.

---

## 5. Control Automatizado por USB PTP con eclipZe

Para erradicar la trepidación humana y los saltos de encuadre, el sistema utilizará el módulo de comunicación nativa de [core/camera.py](file:///d:/software/eclipZe/core/camera.py).

### 5.1 Protocolo de Configuración de Hardware (Cámara y Trípode)
1. **Montaje mecánico:** Fijar la zapata rápida del trípode al **collarín de rotación del objetivo 150-500mm**, jamás a la rosca del cuerpo de la cámara. Esto equilibra el centro de masas e impide el cabeceo.
2. **Desconexión del VR:** Ajustar el interruptor físico del objetivo `VR` a **OFF**.
3. **Obturación electrónica silenciosa:** En el menú de la Nikon Z5 II:
   * *Modo de disparo silencioso* (*Silent Photography*) = **ON**.
   * Esto elimina completamente el *shutter shock* y el movimiento mecánico de las cortinillas.
4. **Modo de avance:** Configurar en ráfaga rápida continua (**CH**).
5. **Horquillado:** BKT = **9F**, paso = **1.7** (o 1.3), centrado en **1/125s**.

### 5.2 Disparo Desatendido por Software
Con la cámara conectada por cable USB-C a la estación eclipZe, el despachador ejecuta la ráfaga de 9 tomas mediante PTP nativo:

```python
from core.camera import NikonPTPDriver

driver = NikonPTPDriver(camera_name="Nikon Z5 II")
if driver.connect():
    # Dispara la ráfaga completa de 9 disparos BKT sin tocar la cámara
    driver.trigger_burst(count=9)
```

* **Tiempo de ejecución de la ráfaga:** La cámara gestiona internamente la ráfaga a $\sim 7.5\,\text{fps}$, completando las 9 tomas en **menos de 1.8 segundos**.
* **Estrategia para 2027:**
  Dado que la totalidad dura **279 segundos (4 min 39 s)** en Cádiz/Tarifa:
  * El secuenciador en [core/sequencer.py](file:///d:/software/eclipZe/core/sequencer.py) puede disparar un ciclo de 9 tomas **cada 15 segundos**.
  * Se obtendrán hasta **18 secuencias completas de 9 tomas (162 archivos RAW idénticos)** para apilado HDR y reducción de ruido térmico, con cero vibración táctil y alineación perfecta.
