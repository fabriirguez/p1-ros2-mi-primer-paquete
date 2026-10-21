# P1 — Sistema publicador y contador en ROS 2

**Asignatura:** Arquitecturas Software para Robótica · Tema 1  
**Universidad:** Universidad Camilo José Cela (UCJC)  
**Estudiante:** Fabricio Andree Rodriguez  
**Profesor:** Julio Merelo Casado  
**Entorno de desarrollo y pruebas:** Ubuntu 24.04 (ARM64, máquina virtual UTM) · ROS 2 Jazzy · Python 3.12.3

## 1. Qué hace este paquete

`mi_primer_paquete` es un paquete `ament_python` con dos nodos:

| Nodo | Responsabilidad |
|---|---|
| `mi_nodo` | Publicador de la Práctica Guiada de la Sesión 3. Publica un `std_msgs/msg/String` en `/saludo` una vez por segundo, con un número de mensaje creciente. |
| `contador_nodo` | Se suscribe a `/saludo`, cuenta los mensajes recibidos y publica el total en `/contador` (`std_msgs/msg/Int32`). Ofrece un servicio de reinicio y avisa con `WARN` al alcanzar un umbral configurable. |

Interfaces ROS 2:

| Interfaz | Nombre | Tipo | Detalle |
|---|---|---|---|
| Tópico | `/saludo` | `std_msgs/msg/String` | Publica `mi_nodo`. QoS por defecto, profundidad 10 |
| Tópico | `/contador` | `std_msgs/msg/Int32` | Publica `contador_nodo`. QoS `RELIABLE` + `TRANSIENT_LOCAL`, `KEEP_LAST` 10 |
| Servicio | `/reiniciar_contador` | `std_srvs/srv/Trigger` | Pone el contador a 0 y responde `success` y `message` |
| Parámetro | `/contador_nodo umbral` | entero, por defecto `10` | Modificable en caliente; solo acepta enteros ≥ 1 |
| Parámetro | `/mi_nodo frecuencia_hz` | decimal, por defecto `1.0` | Frecuencia de publicación (0.1–20.0 Hz), modificable en caliente |

## 2. Requisitos

- Ubuntu 24.04 con ROS 2 Jazzy instalado en `/opt/ros/jazzy`.
- `colcon` (`python3-colcon-common-extensions`).
- Dependencias ROS: `rclpy`, `std_msgs`, `std_srvs` y `rcl_interfaces`, incluidas en una instalación estándar de Jazzy. Si faltara alguna, se instala con `rosdep` (paso 3).

## 3. Crear el workspace y obtener el código

Los comandos de este README usan el workspace `~/p1_ros2_ws`, el mismo de las pruebas. Si se usa otro directorio, basta con sustituir la ruta.

```bash
mkdir -p ~/p1_ros2_ws/src
cd ~/p1_ros2_ws/src
git clone https://github.com/fabriirguez/p1-ros2-mi-primer-paquete.git mi_primer_paquete
```

También se puede descomprimir el ZIP de la entrega dentro de `~/p1_ros2_ws/`, de forma que quede `~/p1_ros2_ws/src/mi_primer_paquete/package.xml`.

Opcional, para comprobar dependencias:

```bash
cd ~/p1_ros2_ws
source /opt/ros/jazzy/setup.bash
rosdep install --from-paths src --ignore-src -y
```

## 4. Compilar

Desde la raíz del workspace:

```bash
cd ~/p1_ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select mi_primer_paquete
source install/setup.bash
ros2 pkg executables mi_primer_paquete
```

Resultado esperado: `Summary: 1 package finished` y dos ejecutables, `mi_primer_paquete contador_nodo` y `mi_primer_paquete mi_nodo`.

## 5. Ejecutar

**Cada terminal nueva** debe cargar los dos entornos antes de usar `ros2`:

```bash
source /opt/ros/jazzy/setup.bash
source ~/p1_ros2_ws/install/setup.bash
```

Terminal 1:

```bash
ros2 run mi_primer_paquete mi_nodo
```

Terminal 2:

```bash
ros2 run mi_primer_paquete contador_nodo
```

`contador_nodo` muestra `Contador iniciado` y, por cada saludo, una línea `Recibido: ... | Total: N`.

## 6. Verificación de los requisitos (R1–R5)

Con los dos nodos en marcha, abrir una tercera terminal y cargar los entornos del paso 5.

**R1 — Compilación y ejecutables.** Los pasos 4 y 5 deben terminar sin errores y arrancar ambos nodos.

**R2 — Publicación y conteo.**

```bash
ros2 node list          # /contador_nodo y /mi_nodo
ros2 topic list         # incluye /contador y /saludo
ros2 topic echo /contador
```

`/contador` muestra valores `data: N` crecientes.

**R3 — Servicio de reinicio.**

```bash
ros2 service call /reiniciar_contador std_srvs/srv/Trigger "{}"
```

Respuesta esperada: `success=True, message='Contador reiniciado correctamente'`. El total vuelve a empezar desde cero.

**R4 — Parámetro `umbral` en caliente.**

```bash
ros2 param get /contador_nodo umbral      # Integer value is: 10
ros2 param set /contador_nodo umbral 3    # Set parameter successful
```

Cuando el total alcanza el umbral, `contador_nodo` escribe `[WARN] ... Umbral alcanzado: N mensajes`. El aviso se emite una vez. Vuelve a habilitarse si se reinicia el contador o cambia el umbral. Si el total ya supera el nuevo umbral, el aviso aparece con el siguiente mensaje recibido.

**R5 — QoS y suscriptor tardío.**

```bash
ros2 topic info /contador --verbose
```

Debe mostrar `Reliability: RELIABLE` y `Durability: TRANSIENT_LOCAL`. La profundidad aparece como `History (Depth): UNKNOWN`, porque el descubrimiento DDS no propaga ese dato. Por eso la profundidad 10 se comprueba con el suscriptor tardío:

1. Detener **solo** `mi_nodo` (Ctrl+C) y dejar `contador_nodo` en marcha.
2. En otra terminal, conectar un suscriptor nuevo:

```bash
ros2 topic echo /contador std_msgs/msg/Int32 \
  --qos-reliability reliable --qos-durability transient_local --qos-depth 10
```

Sin publicaciones nuevas en `/saludo`, el suscriptor recibe los últimos 10 valores publicados, incluido el último total. Si se detiene también `contador_nodo`, ese historial se pierde, porque lo mantiene el propio publicador.

## 7. Decisiones de diseño

- **Un nodo por responsabilidad.** `mi_nodo` solo produce mensajes y `contador_nodo` solo los procesa. Cualquiera de los dos puede sustituirse sin modificar el otro.
- **Un mensaje `Int32` por saludo recibido.** El total se publica en cuanto cambia, en lugar de usar un temporizador propio.
- **Reinicio con `std_srvs/srv/Trigger`.** No necesita argumentos y su respuesta (`success`, `message`) es exactamente lo que pide el requisito. Tras reiniciar se publica `0` en `/contador`, para que los suscriptores vean el cambio.
- **`umbral` como parámetro ROS 2 validado.** Un callback previo rechaza valores no enteros o menores que 1. Otro posterior rearma el aviso, de modo que el `WARN` no se repite con cada mensaje.
- **QoS `RELIABLE` + `TRANSIENT_LOCAL` + `KEEP_LAST` 10 en `/contador`.** El contador es un estado: un nodo que se conecta tarde necesita conocer el último total sin esperar a la siguiente publicación.
- **`frecuencia_hz` en `mi_nodo`.** Parámetro validado (0.1–20.0 Hz) que ajusta el temporizador en caliente; por defecto mantiene 1 mensaje por segundo.

## 8. Pruebas automáticas

El paquete conserva los tests de estilo generados por `ros2 pkg create`: `test_flake8`, `test_pep257` y `test_copyright`, este último desactivado por la plantilla. Se ejecutan con:

```bash
cd ~/p1_ros2_ws
colcon test --packages-select mi_primer_paquete
colcon test-result --verbose
```

No hay tests funcionales automatizados. Las pruebas funcionales de R1–R5 se realizaron manualmente en Ubuntu y se documentan en la sección 9.

## 9. Evidencias

Capturas tomadas en Ubuntu 24.04 + ROS 2 Jazzy, en la máquina virtual `fabricio-andree-QEMU-Virtual-Machine`, el 21/10/2026. Están en [`evidencias/capturas/`](evidencias/capturas/) con su nombre original, que indica la hora de captura.

| Comprobación | Archivo | Qué muestra |
|---|---|---|
| Entorno | `PHOTO-2026-10-21-14-58-27.jpg` | `ROS_DISTRO=jazzy`, Python 3.12.3, rutas de `ros2` y `colcon` |
| R1 compilación | `PHOTO-2026-10-21-15-55-36.jpg` | `colcon build` sin errores: `Summary: 1 package finished` |
| R1 ejecutables | `PHOTO-2026-10-21-16-14-56.jpg` | `ros2 pkg executables`: `contador_nodo` y `mi_nodo` |
| R1/R2 `mi_nodo` | `PHOTO-2026-10-21-15-56-58.jpg` | `ros2 run ... mi_nodo` publicando en `/saludo` |
| R1/R2 `contador_nodo` | `PHOTO-2026-10-21-15-57-21.jpg` | `ros2 run ... contador_nodo` recibiendo y contando |
| R2 nodos y tópicos | `PHOTO-2026-10-21-15-17-16.jpg` | `ros2 node list`, `ros2 topic list` y `ros2 topic echo /contador` |
| R3 servicio | `PHOTO-2026-10-21-15-42-46.jpg` | `ros2 service call`: `success=True`, `'Contador reiniciado correctamente'` |
| R4 parámetro | `PHOTO-2026-10-21-15-41-42.jpg` | `ros2 param get` (10) y `ros2 param set ... umbral 3`: `Set parameter successful` |
| R4 aviso | `PHOTO-2026-10-21-15-45-28.jpg` | `[WARN] Umbral alcanzado: 3 mensajes` |
| R4 valor por defecto | `PHOTO-2026-10-21-16-01-47.jpg` | `[WARN] Umbral alcanzado: 10 mensajes`; total final 16 |
| R5 perfil QoS | `PHOTO-2026-10-21-15-58-10.jpg` | `ros2 topic info /contador --verbose`: `RELIABLE`, `TRANSIENT_LOCAL` |
| R5 publicador detenido | `PHOTO-2026-10-21-16-01-28.jpg` | `mi_nodo` detenido con Ctrl+C tras el mensaje 15 |
| R5 suscriptor tardío | `PHOTO-2026-10-21-16-02-37.jpg` | `ros2 topic echo` con QoS: recibe los valores 7 a 16 |
| M1 sin `spin()` | `PHOTO-2026-10-21-16-09-20.jpg` | `Contador interno: 0` tras 4 s sin ejecutor |
| M3 tipo incorrecto | `PHOTO-2026-10-21-16-13-35.jpg` | `ros2 topic type` → `Int32`; `echo` como `Float32` sin datos |
| M3 tipo correcto | `PHOTO-2026-10-21-16-14-11.jpg` | `echo` como `Int32`: `data: 151` |
| M4 ejecutable | `PHOTO-2026-10-21-16-14-56.jpg` | `ros2 run ... ejecutable_inexistente` → `No executable found` |

La memoria conceptual (M1–M4) está en [`memoria/`](memoria/).

## 10. Estructura

```text
mi_primer_paquete/
├── mi_primer_paquete/
│   ├── mi_nodo.py           # publicador /saludo
│   └── contador_nodo.py     # contador, servicio, parámetro y QoS
├── test/                    # tests de estilo de la plantilla ament
├── evidencias/capturas/     # capturas de las pruebas en Ubuntu
├── memoria/                 # memoria conceptual (Markdown y PDF)
├── resource/mi_primer_paquete
├── package.xml
├── setup.py
├── setup.cfg
└── LICENSE
```

## 11. Licencia

MIT. Ver [LICENSE](LICENSE).
