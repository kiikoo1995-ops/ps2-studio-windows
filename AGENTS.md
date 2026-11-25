# Instrucciones de desarrollo

Objetivo: PS2 Studio para Windows con Play! distribuido junto a la aplicación, sin instalación ni dependencia de PCSX2. Mantener la biblioteca, favoritos, carátulas y preferencias locales.

## Calidad obligatoria

1. Leer README.md, NOTICE.md y los módulos afectados antes de editar.
2. Mantener cambios pequeños, comprobables y guardados en GitHub; trabajar en feature/play-engine hasta que el paquete autónomo esté validado.
3. Ejecutar python -m unittest discover -s tests -v y verificar CI antes de fusionar.
4. Ejecutar procesos con listas de argumentos y shell=False. Usar la CLI documentada de Play! en la revisión fijada en tools/play-engine.lock.json.
5. No descargar, alojar o incorporar BIOS propietarias, ROMs, juegos comerciales, claves ni carátulas protegidas.
6. No borrar ni reescribir imágenes de disco o datos de usuario.
7. Mantener interfaz en español. No afirmar compatibilidad comercial, rendimiento ni funcionamiento del motor sin pruebas reales.
8. No publicar hasta comprobar el arranque del motor incluido, el paquete completo, las licencias de todas las dependencias y la ausencia de PCSX2 como requisito.
9. No contratar servicios de pago. Evitar compilaciones redundantes y comprobar los límites gratuitos antes de iniciar trabajos que puedan generar cargos.
10. No mezclar este repositorio con otros proyectos.

## Pendientes

- Verificar compilación y dependencias de Play! en Windows x64.
- Retirar módulos antiguos y sus pruebas en un cambio coherente.
- Empaquetar el motor junto a PS2Studio.exe y comprobar su arranque en Windows.
- Probar emulación con software homebrew legal y documentar resultados.
