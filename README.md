# PS2 Studio 0.4.0.dev0 — Play! experimental (NO publicar todavía)

**Esta rama es experimental.** No necesita PCSX2 ni lo integra: el motor de
emulación es **Play!**, compilado desde la revisión fijada en
[`tools/play-engine.lock.json`](tools/play-engine.lock.json). La versión
pública actual, alojada en `main`, continúa siendo el lanzador 0.3 con PCSX2.
No confundir la descarga pública `preview` con el motor experimental Play!.

## Funciones implementadas en la rama experimental

- Programa Windows con biblioteca, favoritos, búsqueda y carátulas PNG/GIF locales.
- Inicio de un juego ISO con `Play.exe --disc archivo.iso`.
- Inicio de homebrew PS2 ELF con `Play.exe --elf archivo.elf`.
- Detecta Play! en `engine/play/Play.exe` (GPU nativa) y
  `engine/play-mesa/Play.exe` (fallback Mesa local). No usa instalaciones de PCSX2.
- Perfiles de resolución interna: auto/velocidad 1x, equilibrado 2x,
  calidad 4x, ultra 8x para OpenGL con GPU nativa.
- Mesa (renderizado software CPU) limitado a 1x, para no forzar escalado costoso.
- Vulkan compilado en la versión experimental, disponible solo con hardware
  adecuado, escala 1x y soporte verificado por Play! al arrancar.
- Solo ISO y ELF están habilitados para iniciar mediante la integración actual;
  otros formatos pueden aparecer en el listado, pero no se anuncian compatibles.
- Preferencias locales y sin descarga de BIOS/juegos/ROMs ni datos de usuario enviados.

## Lo que está probado y lo que NO

La CI de Windows comprueba bibliotecas, argumentos de ejecución, perfiles,
construcción del motor Play!, arranque de su interfaz y empaquetado.
El flujo `.github/workflows/play-engine.yml` también ejecuta una prueba
con `cubes_demo.elf`, software casero de PS2 MIT de
[glampert/ps2-homebrew](https://github.com/glampert/ps2-homebrew),
revision `602441a6877a3136709d6320664340d52e3027a1`, comprobado por Git SHA.
El ELF no se incluye en los paquetes de PS2 Studio.

**Las pruebas automáticas de compilación, ventana abierta o carga de ELF no
demuestran FPS, ausencia de pantallas negras, audio, compatibilidad comercial,
fluidez o estabilidad en una GPU de usuario.** No publicar la versión
independiente hasta completar pruebas de renderizado, mandos y compatibilidad,
además de revisar las licencias de las bibliotecas distribuidas.

## Ejecutar la integración experimental

La aplicación sola, ejecutada con `python app.py`, no incluye Play!
si no existe `engine/play/Play.exe` junto al ejecutable o a la raíz del
repositorio. La CI experimental prepara una distribución completa para pruebas
internas con las dos opciones de motor. No bajar ni ejecutar archivos de
juegos de origen dudoso; utiliza homebrew libre o tus propios archivos legítimos.

1. En GitHub → Actions abre «Experimental Play! engine build» en la rama
   `feature/play-engine`; el artefacto interno solo aparece si toda la CI pasa.
2. Descarga el ZIP experimental completo de esa ejecución (no el ZIP estable).
3. Extrae el directorio entero. No copies solo `PS2Studio.exe`.
4. Abre PS2 Studio, añade una carpeta de ISO/ELF, configura el modo de gráficos
   que soporte tu equipo y utiliza **Iniciar juego**.
5. Los controles, gráficos y audio dependen del motor Play! y del dispositivo.

## Pruebas locales

```powershell
python -m unittest discover -s tests -v
```

## Publicación, derechos y coste

Consulta [NOTICE.md](NOTICE.md) y el texto legal integrado
`engine/play/Play-LICENSE.txt`. Play! es un proyecto de terceros y la app no
está afiliada a Sony. La distribución del código frontal sigue siendo MIT.
No se incluyen ROMs, juegos, BIOS ni carátulas comerciales. Presupuesto: 0 €.

**Pendiente para release:** revisar dependencias/avisos de Qt y Mesa, validar
capturas reales de homebrew y FPS sobre hardware Windows, comprobar controles,
sonido y errores con archivos propios. No fusionar el PR #7 ni reemplazar
la versión `preview` sin esas verificaciones.
