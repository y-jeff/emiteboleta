# Publicar EmiteBoleta gratis

Esta guía deja la app en internet **sin costo** usando dos servicios con plan gratuito:

| Pieza | Servicio | Qué da gratis |
|-------|----------|---------------|
| Aplicación web | [Render](https://render.com) (plan Free) | URL `https://<nombre>.onrender.com` con HTTPS y deploy automático desde GitHub |
| Base de datos | [Neon](https://neon.com) (plan Free) | PostgreSQL que no vence |

No necesitas tarjeta de crédito para ninguno de los dos (revisa sus condiciones al registrarte, porque pueden cambiar).

> **Ten en cuenta:** en el plan Free, Render "duerme" la app después de unos 15 minutos sin visitas. La primera visita siguiente tarda cerca de un minuto en cargar; después funciona normal. Para un proyecto de portafolio o para empezar es suficiente.

## 1. Crear la base de datos en Neon

1. Entra a [neon.com](https://neon.com) y crea una cuenta (puedes usar tu GitHub).
2. Crea un proyecto llamado `emiteboleta`. Elige la región más cercana a la de Render (por ejemplo, *AWS US East*).
3. En **Connection details**, desactiva **Connection pooling** y copia la URL de conexión. Se ve así:

   ```
   postgresql://usuario:clave@ep-algo-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

   Guárdala: la usarás en el paso 2. Es una contraseña, no la publiques.

## 2. Crear la app en Render

1. Entra a [render.com](https://render.com) y crea una cuenta con tu GitHub.
2. Ve a **New → Blueprint** y elige el repositorio `emiteboleta`.
3. Render lee el archivo [`render.yaml`](../render.yaml) y te pide el valor de `DATABASE_URL`: pega la URL de Neon.
4. Presiona **Apply**. Render instala dependencias, compila los estáticos y corre las migraciones (ver [`build.sh`](../build.sh)). Tarda unos minutos.
5. Cuando termine, la app queda en `https://emiteboleta.onrender.com` (o el nombre que Render te asigne).

Desde ahí, **cada push a la rama `main` se publica automáticamente**. Por eso `main` es la rama de producción y el desarrollo ocurre en `develop`.

## 3. (Opcional) Cargar la cuenta demo

El plan Free de Render no incluye consola, pero como la base de datos está en Neon puedes correr el comando desde tu computador apuntando a ella:

```bash
DATABASE_URL="postgresql://...neon.tech/neondb?sslmode=require" DEBUG=1 python manage.py crear_demo
```

Así cualquier persona que visite la app puede probarla con `demo@example.com` / `demo-emiteboleta`.

## 4. (Opcional) Email para recuperar contraseña

Sin configurar nada, los correos de recuperación se escriben en el log de Render. Para enviarlos de verdad gratis puedes usar una cuenta de Gmail con una [contraseña de aplicación](https://support.google.com/accounts/answer/185833). En Render → **Environment** agrega:

| Variable | Valor |
|----------|-------|
| `EMAIL_HOST` | `smtp.gmail.com` |
| `EMAIL_HOST_USER` | tu correo de Gmail |
| `EMAIL_HOST_PASSWORD` | la contraseña de aplicación |
| `DEFAULT_FROM_EMAIL` | `EmiteBoleta <tu-correo@gmail.com>` |

## 5. (Más adelante) Dominio propio

Cuando compres un dominio (un `.cl` se registra en [NIC Chile](https://www.nic.cl)):

1. En Render → **Settings → Custom Domains**, agrega el dominio y sigue las instrucciones para configurar el DNS. Render emite el certificado HTTPS solo.
2. En **Environment** agrega:
   - `ALLOWED_HOSTS` = `tu-dominio.cl`
   - `CSRF_TRUSTED_ORIGINS` = `https://tu-dominio.cl`

## Otras opciones gratuitas

| Opción | Por qué no es la principal |
|--------|----------------------------|
| PythonAnywhere (plan Beginner) | Siempre encendido, pero el plan gratis tiene poca CPU diaria, la app se debe renovar cada mes y no incluye PostgreSQL |
| Base de datos Free de Render | Vence 30 días después de crearla |
| AWS EC2 | Las cuentas nuevas reciben créditos por un máximo de 6 meses; después se cobra |
| Oracle Cloud Always Free | VM gratis, pero hay que administrar el servidor, pide tarjeta y redujo sus límites en 2026 |
