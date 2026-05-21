# Eventix: Sistema de Gestion de Eventos y Entradas

Proyecto final numero 11 del documento de Django. Eventix permite publicar eventos, vender entradas con pago simulado, generar codigos QR, validar accesos, consultar dashboards y exportar reportes.

## Funcionalidades

- Registro, inicio de sesion y cierre de sesion.
- Roles por grupos: `Organizador` y `Asistente`.
- CRUD de eventos, categorias, ubicaciones y tipos de entrada.
- Compra de entradas con orden y pago simulado.
- Generacion automatica de QR por entrada.
- Validacion de acceso por codigo QR.
- Dashboard con indicadores y tres graficos dinamicos.
- Reportes filtrables por evento, estado y fechas.
- Exportacion a Excel y PDF.
- Panel administrativo responsive y admin nativo de Django.
- Correo de confirmacion usando backend de consola por defecto.

## Modelos principales

- `Categoria`: clasifica los eventos.
- `Ubicacion`: registra lugares, ciudad, direccion y capacidad.
- `Evento`: datos del evento, fechas, capacidad, estado y organizador.
- `TipoEntrada`: precios y cupos por evento.
- `Orden`: compra realizada por un asistente.
- `Entrada`: ticket digital con QR y estado.
- `ValidacionAcceso`: historial de validaciones de entrada.

## Instalacion local

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`.

## Usuarios demo

- Administrador: `admin` / `admin12345`
- Organizador: `organizador` / `organizador123`
- Asistente: `asistente` / `asistente123`

## Rutas principales

- `/`: listado y busqueda de eventos.
- `/registro/`: registro de asistentes.
- `/mis-entradas/`: entradas compradas por el usuario.
- `/dashboard/`: indicadores y graficos para organizadores.
- `/validar-acceso/`: validacion de codigos QR.
- `/reportes/`: filtros y exportaciones.
- `/gestion/eventos/`: CRUD de eventos.
- `/admin/`: panel administrativo de Django.

## Despliegue sugerido

En Render o Railway:

1. Subir el repositorio.
2. Configurar variables de entorno:
   - `SECRET_KEY`: clave segura.
   - `DEBUG=0`.
   - `ALLOWED_HOSTS=tu-dominio.onrender.com`.
   - `DATABASE_URL`: URL de PostgreSQL si se usa base remota.
3. Build command:

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

4. Start command:

```bash
gunicorn eventix.wsgi
```

Para cargar datos demo en produccion, ejecutar una vez:

```bash
python manage.py seed_demo
```
