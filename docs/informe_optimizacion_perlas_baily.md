# Informe Fotométrico y Optimización de Perlas de Baily: Análisis Empírico Ponferrada 2026 y Calibración para el Eclipse Total 2027

---

## 1. Resumen Ejecutivo y Contexto

El presente informe técnico recoge el análisis fotométrico y sensométrico de las capturas RAW (`.NEF`) obtenidas durante el eclipse solar total del **12 de agosto de 2026** desde las inmediaciones de **Ponferrada (León, España)**, ubicadas en el repositorio en [`tests/eclipse_2026/`](file:///d:/software/eclipZe/tests/eclipse_2026).

El objetivo es doble:
1. Evaluar el comportamiento del sensor de la **Nikon Z5 II** y la óptica **VR 150-500mm f/5-6.3G** ante el rango dinámico de las Perlas de Baily (*Baily's Beads*) y el Anillo de Diamante.
2. Formular las correcciones físicas necesarias debidas a la **extinción atmosférica**, la **masa de aire** y el **seeing** para optimizar la secuencia de disparo automatizada en [core/presets.py](file:///d:/software/eclipZe/core/presets.py) de cara al eclipse total del **2 de agosto de 2027** en el sur de España (Cádiz / Tarifa / Málaga).

---

## 2. Análisis Sensométrico de los RAW de Ponferrada 2026

### 2.1 Equipo y Metadatos de Captura
* **Cuerpo:** Nikon Z5 II (firmware reportado como `NIKON Z5_2` en EXIF).
* **Sensor:** CMOS Full Frame de 24.3 MP (resolución activa de $6048 \times 4032$ píxeles, 14 bits con punto de saturación RAW en `16383` cuentas).
* **Óptica:** Nikon VR 150-500mm f/5-6.3G empleada a **500 mm**, apertura fija **f/8.0**.
* **Sensibilidad:** ISO 200.
* **Muestreo:** Dos ráfagas consecutivas de horquillado continuo (9 disparos por ciclo, cadencia $\sim 7\,\text{fps}$).

### 2.2 Cronología de las Ráfagas

A través del análisis de las marcas de tiempo (`SubsecTimeOriginal`) y el flujo luminoso integrado en el sensor:

* **Ráfaga 1 (`_DSC1322` a `_DSC1330`, 20:28:49.43 – 20:28:50.60 CEST):**
  Corresponde a la fase de entrada hacia $C_2$ (Anillo de Diamante y fotosfera residual colapsando). Incluso a $1/8000\,\text{s}$, existen 1.164 píxeles saturados en el núcleo, lo que confirma la presencia de fotosfera directa visible.

* **Ráfaga 2 (`_DSC1331` a `_DSC1339`, 20:28:51.86 – 20:28:53.02 CEST):**
  Corresponde al instante exacto de las **Perlas de Baily finas** rompiendo a través de los valles orográficos del limbo lunar justo antes del segundo contacto ($C_2$). El flujo luminoso cae un orden de magnitud respecto a la Ráfaga 1, permitiendo aislar cada perla individual.

### 2.3 Telemetría y Fotometría de los 18 Archivos RAW

| Archivo | Timestamp (CEST) | Velocidad | Apertura | ISO | Píxeles Saturados ($\ge 16283$) | Intensidad Núcleo (`mean_top200`) | Píxeles Señal ($>5\%$) | Diagnóstico de Fase |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `_DSC1322.NEF` | 20:28:49.43 | 1/500 s | f/8.0 | 200 | 2.874 | 1.000 | 6.709 | Anillo de Diamante / Transición |
| `_DSC1323.NEF` | 20:28:49.57 | 1/8000 s | f/8.0 | 200 | 1.164 | 1.000 | 1.661 | Diamante / Fotosfera residual |
| `_DSC1324.NEF` | 20:28:49.72 | 1/4000 s | f/8.0 | 200 | 1.360 | 1.000 | 1.809 | Diamante / Fotosfera residual |
| `_DSC1325.NEF` | 20:28:49.86 | 1/2000 s | f/8.0 | 200 | 1.550 | 1.000 | 2.546 | Diamante / Inicio de perlas |
| `_DSC1326.NEF` | 20:28:50.00 | 1/1000 s | f/8.0 | 200 | 1.755 | 1.000 | 3.586 | Diamante + perlas secundarias |
| `_DSC1327.NEF` | 20:28:50.15 | 1/250 s | f/8.0 | 200 | 2.504 | 1.000 | 10.339 | Inicio de halo / sobreexpuesto |
| `_DSC1328.NEF` | 20:28:50.29 | 1/125 s | f/8.0 | 200 | 3.538 | 1.000 | 26.897 | Corona interna / Perlas quemadas |
| `_DSC1329.NEF` | 20:28:50.45 | 1/60 s | f/8.0 | 200 | 5.600 | 1.000 | 81.710 | Corona media |
| `_DSC1330.NEF` | 20:28:50.60 | 1/30 s | f/8.0 | 200 | 7.401 | 1.000 | 174.088 | Corona externa |
| `_DSC1331.NEF` | 20:28:51.86 | 1/500 s | f/8.0 | 200 | 853 | 1.000 | 3.697 | Retorno a ciclo rápido |
| `_DSC1332.NEF` | 20:28:52.00 | **1/8000 s** | f/8.0 | 200 | **57** | **0.720** | **931** | **Picos más brillantes sin saturar** |
| `_DSC1333.NEF` | 20:28:52.14 | **1/4000 s** | f/8.0 | 200 | **104** | **0.868** | **1.221** | **Sweet Spot ETTR (Perlas óptimas)** |
| `_DSC1334.NEF` | 20:28:52.29 | 1/2000 s | f/8.0 | 200 | 110 | 0.897 | 1.801 | Perlas tenues + cromosfera incipiente |
| `_DSC1335.NEF` | 20:28:52.43 | 1/1000 s | f/8.0 | 200 | 168 | 0.986 | 2.832 | Saturación de perla, cromosfera roja |
| `_DSC1336.NEF` | 20:28:52.57 | 1/250 s | f/8.0 | 200 | 504 | 1.000 | 10.628 | Fusión en mancha continua |
| `_DSC1337.NEF` | 20:28:52.72 | 1/125 s | f/8.0 | 200 | 1.074 | 1.000 | 36.008 | Corona interna |
| `_DSC1338.NEF` | 20:28:52.88 | 1/60 s | f/8.0 | 200 | 2.103 | 1.000 | 106.816 | Corona media |
| `_DSC1339.NEF` | 20:28:53.02 | 1/30 s | f/8.0 | 200 | 3.691 | 1.000 | 203.413 | Corona externa |

### 2.4 Hallazgos Clave de la Ráfaga 2
1. **`_DSC1333.NEF` (1/4000 s):** Registra el equilibrio perfecto de exposición. La intensidad del núcleo de las perlas alcanza el **86.8% de la saturación**, evitando el *clipping* en los canales verde y azul y permitiendo registrar las variaciones de altura de los valles lunares con máxima fidelidad.
2. **`_DSC1332.NEF` (1/8000 s):** Garantiza que las perlas más intensas permanezcan dentro del rango lineal del sensor (solo 57 píxeles en saturación, equivalentes a $0.0002\%$ del área).
3. **Dispersión cromática y enrojecimiento:** El ratio de canales en el núcleo medido directamente sobre los datos crudos da $R/B = 1.51$. La señal azul se encuentra deprimida en un $40\%$ respecto a la roja debido al esparcimiento de Rayleigh a baja altura.

---

## 3. Física Atmosférica: Comparativa Ponferrada 2026 vs. Sur de España 2027

### 3.1 Modelo de Masa de Aire ($X$)
La masa de aire óptica relativa $X(z)$ atravesada por los rayos solares se calcula mediante la formulación refinada de Kasten & Young (1989):

$$X(z) = \frac{1}{\cos(z) + 0.50572 \cdot (96.07995 - z)^{-1.6364}}$$

donde $z = 90^\circ - h$ es la distancia cenital en grados.

* **Ponferrada 2026:**
  * Altura solar en el eclipse: $h = 10.77^\circ \implies z = 79.23^\circ$.
  * Masa de aire: **$X_{2026} \approx 5.16$ atmósferas**.
* **Sur de España (Cádiz / Tarifa) 2027:**
  * Altura solar en totalidad: $h = 38.05^\circ \implies z = 51.95^\circ$.
  * Masa de aire: **$X_{2027} \approx 1.62$ atmósferas**.

La masa de aire efectiva que atravesará la luz en 2027 se reduce en un factor de **$\times 3.18$**.

### 3.2 Extinción Atmosférica y Compensación de Exposición ($EV$)
La extinción en magnitudes astronómicas en la banda fotométrica visual ($V$) sigue la ley de Bouguer:

$$\Delta m_V = k_V \cdot X$$

Tomando un coeficiente estándar continental de verano de $k_V \approx 0.20\,\text{mag/atmósfera}$ para Ponferrada y $k_V \approx 0.18\,\text{mag/atmósfera}$ para la costa atlántica andaluza:

* Extinción en Ponferrada: $\Delta m_{2026} = 0.20 \times 5.16 = \mathbf{1.03\,\text{mag}}$.
* Extinción en Tarifa/Cádiz: $\Delta m_{2027} = 0.18 \times 1.62 = \mathbf{0.29\,\text{mag}}$.
* Variación diferencial de brillo:
  $$\Delta m_{\text{dif}} = 1.03 - 0.29 = \mathbf{0.74\,\text{mag}}$$

Transformando la diferencia de magnitudes estelares a pasos de exposición fotográfica ($\Delta EV$):

$$\Delta EV = \frac{\Delta m}{2.5 \cdot \log_{10}(2)} = \frac{0.74}{0.7526} \approx \mathbf{+0.98\,\text{EV}}$$

> [!IMPORTANT]
> **El Sol, el Anillo de Diamante y las Perlas de Baily serán exactamente $\sim 1.0\,\text{EV}$ (1 paso de luz completo) más brillantes en el sur de España en 2027 que en Ponferrada en 2026.**

### 3.3 Turbulencia Atmosférica y Tamaño de Perla (*Seeing*)
El ensanchamiento angular de un punto de luz debido a la turbulencia troposférica escala con la masa de aire según:

$$\text{FWHM}_{\text{seeing}} \propto X^{3/5}$$

* En Ponferrada ($X = 5.16$), el seeing fue $\sim 2.7\times$ peor que en el cenit. Las perlas sufrieron un ensanchamiento de varios segundos de arco, lo que diluyó su brillo pico por píxel.
* En 2027 ($X = 1.62$), el seeing matinal será notablemente inferior ($\sim 1.3\times$ respecto al cenit). Las perlas se concentrarán en discos Airy mucho más compactos, lo que **aumenta la radiancia pico por píxel** por encima del cálculo puramente fotométrico.

---

## 4. Cinemática del Eclipse y Ventana de Disparo

| Magnitud Astronómica | Ponferrada 2026 (12-Ago-2026) | Sur de España 2027 (02-Ago-2027) | Consecuencia Operativa |
| :--- | :--- | :--- | :--- |
| **Duración de Totalidad** | **57.7 segundos** | **279.0 segundos (4m 39s)** | Totalidad casi 5 veces más larga |
| **Velocidad angular relativa Luna/Sol** | Muy rápida en el limbo | Moderada | El paso de los valles lunares es más pausado |
| **Ventana útil de Perlas de Baily** | $\sim 2.5 - 3.5$ segundos | **$\sim 8 - 12$ segundos** | Permite ráfagas pausadas de alta resolución |
| **Temperatura de color de perlas** | $\sim 4500\,\text{K}$ (doradas) | $\sim 5600\,\text{K}$ (blanco diamante puro) | Espectro equilibrado RGB en el sensor |

---

## 5. Recomendaciones de Calibración para eclipZe en 2027

Para trasladar los resultados empíricos óptimos de Ponferrada (`f/8.0`, `ISO 200`, `1/4000s`) al escenario de 2027:

### 5.1 Ajuste de Sensibilidad y Óptica
1. **Fijar ISO 100 base en la Nikon Z5 II:**
   * Pasar de `ISO 200` a `ISO 100` resta exactamente el **$1.0\,\text{EV}$** que la atmósfera añade por la menor masa de aire.
   * Maximiza la capacidad de pozo del sensor y el rango dinámico libre de ruido a 14 bits.
2. **Mantener la apertura en f/8.0 a 500mm:**
   * Evita disparar abierto a f/6.3, donde el viñeteo óptico y la aberración cromática longitudinal reducen el contraste fino en el limbo lunar.

### 5.2 Horquillado Óptimo para Perlas (`f/8.0`, `ISO 100`)

| Velocidad | Objetivo Científico y Visual | Resultado Esperado |
| :--- | :--- | :--- |
| **`1/8000 s`** | Picos de máxima irradiancia y valles profundos | Núcleo de las perlas principales con cero saturación destructiva. |
| **`1/4000 s`** | **Toma Maestra de Perlas de Baily (Sweet Spot)** | Rango dinámico orográfico completo del relieve lunar (equivalente a `_DSC1333`). |
| **`1/2000 s`** | Perlas secundarias débiles y cromosfera baja | Detalle de las microperlas y tono rosado de la emisión $H\alpha$. |
| **`1/1000 s`** | Cromosfera media y protuberancias solares | Destello del anillo de diamante y llamaradas prominenciales. |

### 5.3 Programación en el Secuenciador (`core/presets.py`)

Dado que la ventana de perlas dura entre 8 y 12 segundos en Cádiz/Tarifa, la secuencia en [core/presets.py](file:///d:/software/eclipZe/core/presets.py) debe estructurarse en **ráfagas cuádruples continuas** (`1/8000` $\rightarrow$ `1/4000` $\rightarrow$ `1/2000` $\rightarrow$ `1/1000`):

* **Entrada ($C_2$):** Disparo en bucle de ráfaga rápida desde **$C_2 - 6.0\,\text{s}$ hasta $C_2 + 2.0\,\text{s}$**.
* **Salida ($C_3$):** Disparo en bucle de ráfaga rápida desde **$C_3 - 2.0\,\text{s}$ hasta $C_3 + 6.0\,\text{s}$**.
