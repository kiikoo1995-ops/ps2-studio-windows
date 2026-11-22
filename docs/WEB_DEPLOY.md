# PS2 Studio Web — publicación sin inversión y monetización responsable

## Arquitectura
- Sitio web estático en `site/`, sin dependencias de pago, cuentas o rastreadores.
- Descarga del ZIP desde GitHub Releases, no desde Cloudflare.
- Alojamiento recomendado: Cloudflare Pages Free. GitHub Pages tiene restricciones para alojar negocios.
- Cambios en `main` publicados automáticamente **después** de conectar el repositorio a Cloudflare.

## Conectar el alojamiento una única vez
1. Abre https://dash.cloudflare.com/ → Workers & Pages → Create application → Pages.
2. Conecta GitHub y autoriza específicamente `kiikoo1995-ops/ps2-studio-windows`.
3. Rama de producción: `main`; framework: None; build command: `exit 0`; output directory: `site`.
4. Despliega y verifica la dirección real `*.pages.dev` asignada por Cloudflare.
5. Desde ese momento los pushes a main desplegarán automáticamente la web. No inventar dominios ni anunciar sitio publicado antes del despliegue.

## Descargar
- El workflow de Windows ejecuta todos los tests, compila `PS2Studio.exe`, empaqueta ZIP y publica o reemplaza el activo de GitHub Release `preview` en cada push a `main`.
- Verificar la release real antes de afirmar que el enlace directo está listo.
- Versión preliminar; requiere instalar PCSX2 por separado, BIOS propia y juegos legítimos.

## Requisitos antes de habilitar publicidad
- Identificar públicamente el titular legal, datos exigibles por la normativa española aplicable y contacto real; actualizar aviso legal y privacidad.
- Aprobar el sitio en AdSense; confirmar contenido editorial propio y descarga funcional.
- Configurar CMP certificada por Google e integrada con TCF para audiencia EEE y otros territorios exigidos, con consentimiento cuando corresponda, **antes** de solicitar anuncios.
- No integrar scripts ni IDs falsos; separar los anuncios de navegación, botones y descarga de software.
- No ofrecer BIOS, claves ni juegos comerciales protegidos ni insinuar patrocinio de Sony o PCSX2.

## Verificación local
`python -m unittest discover -s tests -v`
`python -m http.server 8000 --directory site`

Fuentes:
https://developers.cloudflare.com/pages/framework-guides/deploy-anything/
https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
https://support.google.com/adsense/answer/48182
https://support.google.com/adsense/answer/13554116
