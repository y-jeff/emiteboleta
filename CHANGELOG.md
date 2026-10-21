# Changelog

Todos los cambios relevantes de EmiteBoleta. El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa [versionado semántico](https://semver.org/lang/es/).

## [0.6.0] — 2026-10-21

### Agregado
- Identidad visual basada en el logo oficial: emblema, íconos de la app (PWA, iOS y favicon) e imagen de vista previa para redes y GitHub.
- Color «Azul EmiteBoleta» para el PDF, ahora el predeterminado.

### Cambiado
- Paleta de la interfaz: azul y celeste sobre azul noche y violeta, como el logo.
- Portada con fondo degradado de ancho completo y marca «emiteboleta» con degradado.

## [0.5.0] — 2026-10-21

### Agregado
- **Catálogo de servicios frecuentes**: se guardan con su precio y se agregan a la boleta con un toque desde el formulario.
- Guía para publicar la app gratis con Render y Neon ([docs/deploy-gratis.md](docs/deploy-gratis.md)).
- Sección de código abierto en el README.

### Cambiado
- `render.yaml` usa una base de datos externa (Neon) en vez de la base Free de Render, que vence a los 30 días.
- La cuenta demo y la portada usan a 3R Labs SpA como cliente de ejemplo.

## [0.4.0] — 2026-10-21

### Agregado
- CI con GitHub Actions: tests sobre PostgreSQL 16, chequeo de migraciones pendientes y verificación de que el CSS compilado esté al día.
- Capturas de pantalla en el README.
- Licencia MIT, plantillas de issues y pull requests.

### Cambiado
- Tailwind se compila a `static/css/app.css` en vez de cargarse desde el CDN: menos peso, sin JavaScript para estilos y sin advertencias en producción.
- La cuenta demo incluye logo y seis meses de boletas con retenciones.
- El saludo del inicio muestra solo el primer nombre.

## [0.3.0] — 2026-10-21

### Agregado
- Botón **WhatsApp** en cada boleta: abre un mensaje listo con el número, el monto y los datos para transferencia.
- Recuperación de contraseña por email (SMTP configurable por variables de entorno).
- Páginas de error 404 y 500 con el diseño de la app.
- La app se puede instalar en el celular como PWA (manifest e íconos).

## [0.2.0] — 2026-10-21

### Agregado
- **Resumen anual**: monto bruto, retención y líquido por mes, con gráfico de barras.
- Exportación del año a CSV compatible con Excel en español.
- Comando `python manage.py crear_demo` con una cuenta de ejemplo.

### Cambiado
- Los ejemplos de configuración usan valores genéricos en vez de un dominio aún no registrado.

## [0.1.0] — 2026-10-21

### Agregado
- Registro e ingreso con email.
- Perfil de emisor reutilizable con logo y color del documento.
- Boletas con múltiples ítems, retención opcional y numeración correlativa por usuario.
- PDF profesional generado con ReportLab, con sello «PAGADA».
- Estados pagada / pendiente y dashboard con totales del mes.
- Historial con búsqueda y filtros, duplicar boletas y autocompletar clientes.
- Validación de RUT chileno.
- Configuración de deploy para Render y Railway.

[0.6.0]: https://github.com/y-jeff/emiteboleta/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/y-jeff/emiteboleta/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/y-jeff/emiteboleta/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/y-jeff/emiteboleta/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/y-jeff/emiteboleta/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/y-jeff/emiteboleta/releases/tag/v0.1.0
