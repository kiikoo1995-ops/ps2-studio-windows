# PS2 Studio Web — Cloudflare Workers Static Assets

## Configuración actual (22 de noviembre de 2026)
- El usuario conectó GitHub con **Cloudflare Workers Builds** (no Cloudflare Pages) y eligió el proyecto `ps2-studio-windows`.
- Al primer intento de publicación, los pasos de clonado e instalación se completaron, pero el despliegue falló; la captura no incluía el mensaje de error final.
- Para evitar ambigüedades del despliegue se agregó `wrangler.jsonc` a la raíz, con el nombre exacto del Worker y la carpeta estática `./site`.
- `assets.not_found_handling` apunta a la página `404.html`; `assets.html_handling` preserva URLs de páginas de directorio con barra final.

## Ajustes en Cloudflare para este proyecto
- Proyecto: `ps2-studio-windows`.
- Repositorio: `kiikoo1995-ops/ps2-studio-windows`.
- Rama: `main`.
- Root directory: `/`.
- Build command: vacío (HTML/CSS estático).
- **Deploy command recomendado:** `npx wrangler deploy`.
- **Deploy command previo:** `npx wrangler deploy --assets ./site`, válido para subir assets, pero redundante una vez configurado `wrangler.jsonc`.
- Preview command: mantener el valor de Cloudflare mientras no haya otra necesidad.
- Si ya hay integración con GitHub, cada push a `main` puede desencadenar un nuevo despliegue automáticamente.

## Si falla el deploy
1. Abre Cloudflare → Workers & Pages → `ps2-studio-windows` → Deployments.
2. Selecciona la compilación fallida; desplaza el registro hacia abajo hasta la línea `[ERROR]` **final** (no basta con el símbolo rojo de Deploying).
3. Verifica que el proyecto en el dashboard y el campo `name` del config coincidan.
4. Si muestra `Missing entry-point`, comprueba que `wrangler.jsonc` se obtiene desde `main`.
5. Si muestra un error de permisos o token API, verifica el token de Workers Builds conectado a la cuenta; **no** envíes tokens a chats.
6. Solo tras desplegar correctamente, comprueba la **URL real** `*.workers.dev`, la portada, `/descargar/` y `/legal/privacidad/`. No inventes un dominio.
7. Comprueba que el enlace de descarga hacia GitHub Releases devuelve el ZIP esperado.

## Descarga
El flujo `.github/workflows/windows.yml` ejecuta pruebas, compila el lanzador en Windows y publica la release `preview` con `PS2Studio-Windows.zip`. No distribuye BIOS ni juegos.

## Publicidad (NO activar todavía)
- Completar identificación y contacto legal de titular conforme a legislación aplicable en España.
- Verificar sitio público, enlaces y contenido de calidad.
- Conseguir aprobación real de AdSense; sin garantía de aprobación.
- Preparar CMP certificada por Google / TCF según región y uso; actualizar privacidad.
- Solo entonces añadir script real de anuncios y `ads.txt` con ID verdadero.
- No mostrar publicidad camuflada como botones de descarga.

## Documentación oficial
- https://developers.cloudflare.com/workers/ci-cd/builds/troubleshoot/
- https://developers.cloudflare.com/workers/static-assets/
- https://developers.cloudflare.com/workers/static-assets/routing/static-site-generation/
- https://support.google.com/adsense/answer/48182
