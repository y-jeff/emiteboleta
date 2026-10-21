# EmiteBoleta

**Boletas de servicios en PDF, desde el celular, en 30 segundos.**

EmiteBoleta es una aplicación web para trabajadores independientes e informales en Chile —gasfíteres, profesores particulares, diseñadores, técnicos— que necesitan entregar un comprobante de cobro con aspecto profesional sin pelear con Word ni con plantillas.

> EmiteBoleta genera comprobantes de prestación de servicios. **No reemplaza** la boleta de honorarios electrónica del SII cuando corresponda emitirla.

## Funcionalidades

**Lo esencial**
- Formulario de boleta: emisor, cliente, servicios, montos y fecha
- Numeración correlativa automática por usuario (sin números repetidos, incluso con requests concurrentes)
- Logo opcional
- PDF descargable con diseño profesional

**Producto completo**
- Registro e ingreso con email (Django auth)
- Historial con búsqueda (cliente, RUT, N° o servicio) y filtro por estado
- Datos del emisor guardados una sola vez y copiados a cada boleta (las boletas antiguas no cambian si editas tu perfil)
- Múltiples ítems por boleta, con total calculado en vivo
- Estado pagada / pendiente, con fecha de pago
- Dashboard con totales del mes (emitido, pagado, por cobrar)
- Retención opcional en porcentaje
- Autocompletar clientes anteriores y duplicar boletas
- Validación de RUT chileno (módulo 11)

**Diferenciadores**
- PDF con jerarquía tipográfica, color de acento a elección, sello «PAGADA» y datos para transferencia
- Diseño *mobile-first*: navegación inferior tipo app, botones al alcance del pulgar y botón **Compartir** que envía el PDF directo a WhatsApp o email (Web Share API)

## Stack

| Capa | Tecnología |
|------|------------|
| Backend | Django 6 · Python 3.13+ |
| Base de datos | PostgreSQL en producción · SQLite en local |
| PDF | ReportLab |
| UI | Tailwind CSS · JavaScript sin frameworks |
| Deploy | Render o Railway · Gunicorn · WhiteNoise |

## Correr en local

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   ·   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

export DEBUG=1              # PowerShell: $env:DEBUG = "1"
python manage.py migrate
python manage.py runserver
```

Abre http://127.0.0.1:8000, crea una cuenta y completa tus datos de emisor.

Para probar con datos de ejemplo, crea la cuenta demo (se reinicia cada vez que corres el comando):

```bash
python manage.py crear_demo
# email: demo@example.com · clave: demo-emiteboleta
```

### Tests

```bash
DEBUG=1 python manage.py test
```

Cubren validación de RUT, formato de montos, numeración correlativa, cálculo de totales con retención, generación de PDF, aislamiento entre usuarios (nadie puede ver ni borrar boletas ajenas), registro e ingreso.

## Deploy

Variables de entorno necesarias en producción:

| Variable | Ejemplo |
|----------|---------|
| `SECRET_KEY` | una cadena larga y aleatoria |
| `DATABASE_URL` | `postgres://usuario:clave@host:5432/emiteboleta` |
| `ALLOWED_HOSTS` | `tu-dominio.cl` (opcional en Render y Railway: su subdominio se agrega solo) |
| `CSRF_TRUSTED_ORIGINS` | `https://tu-dominio.cl` (solo si usas dominio propio) |

- **Render**: conecta el repositorio y usa el *Blueprint* de [render.yaml](render.yaml), que crea el servicio web y la base PostgreSQL.
- **Railway**: crea un proyecto con PostgreSQL y este repositorio; el [Procfile](Procfile) corre las migraciones y levanta Gunicorn. El dominio público se agrega solo a `ALLOWED_HOSTS`.

El logo se guarda en la base de datos y no en disco, porque Render y Railway usan disco efímero.

## Ramas

| Rama | Uso |
|------|-----|
| `main` | Producción. Solo recibe merges desde `develop` cuando una versión está lista, y cada merge lleva un tag (`v0.1.0`, `v0.2.0`, …). |
| `develop` | Desarrollo. Aquí se integran las nuevas funcionalidades antes de pasar a producción. |

## Estructura

```
config/      Configuración de Django (settings por variables de entorno)
cuentas/     Registro e ingreso con email
boletas/     Modelos, vistas, formularios, generación del PDF, utilidades de RUT y formato
templates/   Plantillas con Tailwind
static/      Archivos estáticos
```

## Próximos pasos

- Compilar Tailwind en el build en vez de usar el CDN
- Envío de la boleta por email desde la app
- Exportar el historial a Excel para la declaración de renta
