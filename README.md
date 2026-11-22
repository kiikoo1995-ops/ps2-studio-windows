# PS2 Studio · Versión inicial 0.1.0

**PS2 Studio** es una aplicación independiente para Windows que organiza una
biblioteca de juegos PS2 y los ejecuta mediante una instalación separada de
**PCSX2**. **El programa no emula el hardware por sí solo ni modifica el código
de PCSX2**: lo controla mediante su interfaz de línea de comandos oficial.

## Funciones de esta versión

- Biblioteca con búsqueda por nombre y columnas de formato, tamaño y carpeta.
- Búsqueda de imágenes de disco en carpetas y subcarpetas configurables.
- Formatos: `.iso`, `.chd`, `.cso`, `.zso`, `.bin`, `.cue`, `.mdf`, `.gz`.
- Evita duplicar una pareja habitual `.cue`/`.bin` con el mismo nombre base.
- Ejecuta PCSX2 con `-batch [-fullscreen] -- <imagen_de_disco>`.
- Guarda ajustes localmente en `%APPDATA%\PS2Studio\settings.json`.
- Sin cuentas, telemetría, descargas de BIOS ni servicios de pago.

## Ejecutar el código en Windows

1. Instala [Python 3.11 o posterior](https://www.python.org/downloads/windows/) con tkinter.
2. Descarga o clona el repositorio y abre una terminal en la carpeta raíz.
3. Ejecuta `python app.py`.
4. Pulsa **Seleccionar PCSX2** y elige el archivo `pcsx2-qt.exe` del emulador.
5. Pulsa **Añadir carpeta** y selecciona una carpeta con tus copias legítimas de juegos.
6. Haz doble clic en un juego o pulsa **Iniciar juego**.

PCSX2 no está incluido. Instálalo desde https://pcsx2.net/downloads/ y completa
su configuración inicial, incluida una BIOS extraída de tu propia PS2.

## Generar un .exe desde GitHub

Al subir este código a un repositorio de GitHub, el flujo
`.github/workflows/windows.yml` ejecuta las pruebas en Windows y, si se superan,
crea un ejecutable mediante PyInstaller. El archivo `PS2Studio.exe` aparecerá
como artefacto **PS2Studio-Windows** en la ejecución de GitHub Actions.

**Importante:** el ejecutable todavía no existe hasta que el flujo se ejecute
correctamente en Windows. El archivo será un lanzador, no una copia de PCSX2.

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

- **v0.2:** favoritos, historial y carátulas locales opcionales.
- **v0.3:** navegación con mando y perfiles gráficos.
- **v1.0:** distribución firmada y pruebas de integración con PCSX2 real.

## Licencias

El **lanzador** es MIT; **PCSX2**, que se instala por separado, utiliza GPLv3+.
Consulta [NOTICE.md](NOTICE.md). No se incluyen juegos, BIOS ni contenido de Sony.
