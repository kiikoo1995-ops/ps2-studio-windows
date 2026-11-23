# PS2 Studio · Versión preliminar 0.3.0

**PS2 Studio** es una aplicación independiente para Windows que organiza una
biblioteca de juegos PS2 y los ejecuta mediante una instalación separada de
**PCSX2**. **El programa no emula el hardware por sí solo ni modifica el código
de PCSX2**: lo controla mediante su interfaz de línea de comandos oficial.

## Funciones de esta versión

- Biblioteca con búsqueda por nombre, favoritos y filtro «Solo favoritos».
- Vista lateral con carátulas PNG/GIF locales elegidas por el usuario y datos del archivo.
- Detección de carátula con el mismo nombre base que la imagen de disco, si está en esa carpeta.
- Sin descarga automática de portadas, API externas ni juegos incluidos.
- Detección local opcional de PCSX2 en PATH o carpetas de instalación habituales; selección manual disponible.
- Columnas de formato, tamaño y carpeta; los favoritos se guardan entre sesiones.
- Búsqueda de imágenes de disco en carpetas y subcarpetas configurables.
- Formatos: `.iso`, `.chd`, `.cso`, `.zso`, `.bin`, `.cue`, `.mdf`, `.gz`.
- Evita duplicar una pareja habitual `.cue`/`.bin` con el mismo nombre base.
- Ejecuta PCSX2 con `-batch [-fullscreen] -- <imagen_de_disco>`.
- Guarda ajustes y favoritos localmente en `%APPDATA%\PS2Studio\settings.json`.
- Sin cuentas, telemetría, descargas de BIOS ni servicios de pago.

## Ejecutar el código en Windows

1. Instala [Python 3.11 o posterior](https://www.python.org/downloads/windows/) con tkinter.
2. Descarga o clona el repositorio y abre una terminal en la carpeta raíz.
3. Ejecuta `python app.py`.
4. Si no se detecta automáticamente, pulsa **Seleccionar PCSX2** y elige `pcsx2-qt.exe`.
5. Pulsa **Añadir carpeta** y selecciona una carpeta con tus copias legítimas de juegos.
6. Selecciona un juego y pulsa **★ Favorito** para guardarlo, o activa **Solo favoritos** para filtrarlo.
7. Haz doble clic en un juego o pulsa **Iniciar juego**.

PCSX2 no está incluido. Instálalo desde https://pcsx2.net/downloads/ y completa
su configuración inicial, incluida una BIOS extraída de tu propia PS2.

## Generar un .exe desde GitHub

Al subir este código a un repositorio de GitHub, el flujo
`.github/workflows/windows.yml` ejecuta las pruebas en Windows y, si se superan,
crea un ejecutable mediante PyInstaller. El archivo `PS2Studio.exe` aparecerá
como artefacto **PS2Studio-Windows** en la ejecución de GitHub Actions.

**Verificación de descarga:** la publicación preliminar también incluye `PS2Studio-Windows.zip.sha256`. Compara la suma mediante PowerShell: `Get-FileHash .\PS2Studio-Windows.zip -Algorithm SHA256`. Al publicar una versión nueva cambia la suma; utiliza siempre la del ZIP que acabas de descargar.

**Descarga disponible:** [versión preliminar de Windows](https://github.com/kiikoo1995-ops/ps2-studio-windows/releases/tag/preview) generada por GitHub Actions. Es un lanzador, no una copia de PCSX2.

**Web pública gratuita:** https://ps2-studio-windows.kiikoo1995.workers.dev/ · [Manual de PS2 Studio](https://ps2-studio-windows.kiikoo1995.workers.dev/guias/uso/).

## Captura auténtica de la interfaz

La imagen [site/assets/app-real-demo.png](site/assets/app-real-demo.png) se genera
al ejecutar **PS2 Studio real** con `tkinter` en una pantalla virtual Linux/Xvfb,
utilizando el script [tools/capture_app_demo.py](tools/capture_app_demo.py).
Los archivos de juegos y las carátulas utilizados son ejemplos ficticios creados
para la demostración. **No es una imagen de IA ni una prueba de funcionamiento
con juegos comerciales o PCSX2 en Windows.** La compilación del EXE se comprueba
por separado con GitHub Actions.

## Pruebas locales

Desde la carpeta raíz:

```sh
python -m unittest discover -s tests -v
```

Las pruebas comprueban guardado de configuración, errores de JSON, búsqueda de
archivos, carpetas superpuestas, subcarpetas, parejas CUE/BIN, filtrado,
argumentos de PCSX2 y ejecución sin shell con proceso simulado.

No prueban compatibilidad de juegos comerciales, rendimiento gráfico ni BIOS.
Estas comprobaciones necesitan Windows, PCSX2 instalado y archivos legítimos.

## Estructura

```text
PS2Studio/
├── app.py                         # Entrada de la aplicación
├── ps2studio/
│   ├── config.py                  # Ajustes persistentes
│   ├── library.py                 # Escáner de juegos
│   ├── launcher.py                # Integración segura con PCSX2
│   ├── ui.py                      # Interfaz gráfica
│   └── __main__.py                # Ejecutar con python -m ps2studio
├── tests/                         # Pruebas automáticas
├── .github/workflows/windows.yml  # Pruebas y construcción .exe
├── AGENTS.md                      # Instrucciones para Codex
├── NOTICE.md                      # Avisos de PCSX2 y copyright
└── LICENSE                        # Licencia del lanzador
```

## Evolución prevista

- **v0.2:** favoritos persistentes y detección local de PCSX2 incluidos; pendientes historial y carátulas locales.
- **v0.3:** panel de carátulas locales y detalles incluido; navegación con mando y perfiles gráficos todavía pendientes.
- **v1.0:** distribución firmada y pruebas de integración con PCSX2 real (pendiente).

## Licencias

El **lanzador** es MIT; **PCSX2**, que se instala por separado, utiliza GPLv3+.
Consulta [NOTICE.md](NOTICE.md). No se incluyen juegos, BIOS ni contenido de Sony.
