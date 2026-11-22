# Instrucciones para Codex

Objetivo: desarrollar **PS2 Studio**, aplicación Windows de biblioteca de juegos que
inicia una **instalación independiente** de PCSX2. No descargar, alojar o incorporar
BIOS, ROMs, imágenes comerciales ni archivos propietarios. No reimplementar PCSX2
sin un plan técnico/licencia y una petición expresa del propietario.

Antes de editar, leer `README.md`, `NOTICE.md` y los módulos de `ps2studio/`.
No mezclar este trabajo con ningún repositorio empresarial o de tienda.

## Calidad obligatoria

1. Cada comportamiento nuevo debe tener pruebas unitarias o un motivo documentado
   que explique por qué necesita pruebas de integración.
2. Ejecutar `python -m unittest discover -s tests -v` antes de proponer cambios.
3. Mantener la CLI de PCSX2 conforme a https://pcsx2.net/docs/advanced/cli/.
4. Ejecutar procesos con listas de argumentos y `shell=False`, nunca shell/strings.
5. Nunca borrar o reescribir imágenes de disco o archivos del emulador.
6. Conservar una interfaz en español y componentes de biblioteca estándar siempre
   que sea viable.
7. No afirmar que el ejecutable Windows o juegos comerciales funcionan hasta
   haber comprobado ambos mediante pruebas reales.
8. Los cambios mayores deben enviarse mediante pull request y pasar CI.

## Próximas tareas

- Añadir un conjunto de pruebas del frontend con entorno gráfico virtual o
  simulación de eventos y validación de flujos de usuario.
- Añadir favoritos locales y detectar cambios en las carpetas sin bloquear UI.
- Mejorar el tratamiento de CUE/BIN con nombres distintos y varios tracks.
- Permitir importar metadatos locales sin descargar carátulas protegidas.
- Añadir comprobación de la versión y existencia de PCSX2 antes de lanzar.
