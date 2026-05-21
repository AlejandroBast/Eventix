# Eventix: Sistema de Gestion de Eventos y Entradas

Eventix es una aplicacion web desarrollada con Django para gestionar eventos, registrar asistentes, vender entradas mediante pago simulado, generar codigos QR, validar accesos y consultar reportes administrativos.

Este proyecto corresponde al **proyecto final numero 11: Sistema de Gestion de Eventos y Entradas**.

## Objetivo del sistema

Desarrollar una aplicacion web funcional que permita a organizadores administrar eventos y entradas, y a los asistentes comprar tickets digitales con codigo QR. El sistema incluye autenticacion, roles, operaciones CRUD, dashboard con graficos, reportes exportables y una base lista para despliegue.

## Tecnologias usadas

- Python 3.12
- Django 6
- SQLite para desarrollo local
- PostgreSQL compatible para despliegue mediante `DATABASE_URL`
- Bootstrap 5
- Bootstrap Icons
- Chart.js
- qrcode + Pillow para generar codigos QR
- openpyxl para exportar reportes a Excel
- reportlab para exportar reportes a PDF
- WhiteNoise para archivos estaticos en produccion
- Gunicorn para despliegue

## Funcionalidades principales

- Registro de usuarios.
- Inicio y cierre de sesion.
- Roles de usuario mediante grupos.
- Listado publico de eventos.
- Busqueda y filtros por nombre, categoria y fecha.
- Detalle de evento con informacion de cupos y precios.
- Compra de entradas.
- Pago simulado.
- Generacion automatica de codigos QR por entrada.
- Vista de entradas compradas por cada asistente.
- Validacion de acceso mediante codigo QR.
- Dashboard administrativo con indicadores.
- Graficos dinamicos con datos reales del sistema.
- CRUD de eventos.
- CRUD de categorias.
- CRUD de ubicaciones.
- CRUD de tipos de entrada.
- Reportes filtrables por evento, estado y fechas.
- Exportacion de reportes a Excel.
- Exportacion de reportes a PDF.
- Panel administrativo nativo de Django.
- Comando para cargar datos de demostracion.
- Pruebas automatizadas de flujos principales.

## Cumplimiento de requisitos del proyecto

| Requisito | Implementacion |
| --- | --- |
| Autenticacion | Registro, login y logout con Django Auth |
| Roles | Visitante, Asistente, Organizador y Administrador |
| Minimo 4 modelos | Se implementan 7 modelos principales |
| CRUD | Eventos, categorias, ubicaciones y tipos de entrada |
| Formularios validados | Formularios con Django Forms y ModelForms |
| Dashboard | Indicadores administrativos y graficos |
| Graficos | Entradas por evento, ingresos por mes y validaciones |
| Reportes | Filtros y exportacion a Excel/PDF |
| Interfaz responsive | Bootstrap 5 y CSS propio |
| Validaciones | Cupos, fechas, permisos y estados de entradas |
| Despliegue | Procfile, runtime, WhiteNoise y variables de entorno |
| Documentacion | README con instalacion, rutas, roles y flujo |

## Roles del sistema

### Visitante

Usuario que no ha iniciado sesion.

Puede:

- Ver eventos publicados.
- Buscar eventos.
- Filtrar eventos por categoria o fecha.
- Ver el detalle de un evento.
- Registrarse.
- Iniciar sesion.

No puede:

- Comprar entradas.
- Ver sus entradas.
- Validar accesos.
- Acceder al dashboard.
- Administrar registros.

### Asistente

Grupo: `Asistente`

Este rol se asigna automaticamente al registrarse desde `/registro/`.

Puede:

- Iniciar sesion.
- Cerrar sesion.
- Ver eventos publicados.
- Comprar entradas.
- Confirmar pago simulado.
- Generar entradas con QR.
- Ver sus entradas en `/mis-entradas/`.
- Ver el detalle de sus propios tickets.

No puede:

- Crear eventos.
- Editar eventos.
- Eliminar eventos.
- Ver reportes administrativos.
- Validar entradas.
- Acceder al dashboard.

### Organizador

Grupo: `Organizador`

Puede:

- Realizar todas las acciones de un asistente.
- Acceder al dashboard.
- Crear, editar y eliminar eventos.
- Crear, editar y eliminar categorias.
- Crear, editar y eliminar ubicaciones.
- Crear, editar y eliminar tipos de entrada.
- Validar codigos QR.
- Consultar reportes.
- Exportar reportes a Excel.
- Exportar reportes a PDF.
- Ver informacion administrativa de entradas y eventos.

### Administrador Django

Usuario con `is_staff=True` o `is_superuser=True`.

Puede:

- Realizar todas las acciones del organizador.
- Acceder a `/admin/`.
- Administrar usuarios.
- Administrar grupos.
- Administrar permisos.
- Administrar directamente todos los modelos desde Django Admin.

## Usuarios de prueba

El comando `seed_demo` crea usuarios, roles, eventos, ubicaciones, categorias, tipos de entrada y entradas de ejemplo.

| Rol | Usuario | Contrasena | Acceso principal |
| --- | --- | --- | --- |
| Administrador | `admin` | `admin12345` | `/admin/` y dashboard |
| Organizador | `organizador` | `organizador123` | `/dashboard/` |
| Asistente | `asistente` | `asistente123` | `/mis-entradas/` |

## Modelos principales

### Categoria

Clasifica los eventos. Ejemplos: tecnologia, cultura, negocios.

Campos principales:

- `nombre`
- `descripcion`

### Ubicacion

Representa el lugar donde se realiza un evento.

Campos principales:

- `nombre`
- `direccion`
- `ciudad`
- `capacidad`

### Evento

Contiene la informacion central del evento.

Campos principales:

- `titulo`
- `descripcion`
- `categoria`
- `ubicacion`
- `organizador`
- `fecha_inicio`
- `fecha_fin`
- `capacidad`
- `estado`
- `imagen_url`

Estados:

- `borrador`
- `publicado`
- `finalizado`
- `cancelado`

### TipoEntrada

Define precios y cupos por evento.

Campos principales:

- `evento`
- `nombre`
- `precio`
- `cupo`
- `activo`

### Orden

Representa una compra realizada por un asistente.

Campos principales:

- `asistente`
- `evento`
- `tipo_entrada`
- `cantidad`
- `total`
- `estado_pago`
- `referencia_pago`

Estados de pago:

- `pendiente`
- `pagada`
- `cancelada`

### Entrada

Ticket digital generado despues del pago simulado.

Campos principales:

- `asistente`
- `evento`
- `tipo_entrada`
- `orden`
- `codigo`
- `qr_imagen`
- `estado`

Estados:

- `activa`
- `usada`
- `cancelada`

### ValidacionAcceso

Guarda el historial de intentos de validacion de entradas.

Campos principales:

- `codigo_ingresado`
- `entrada`
- `validado_por`
- `resultado`
- `observacion`

Resultados:

- `valida`
- `invalida`

## Rutas principales

| Ruta | Descripcion | Acceso |
| --- | --- | --- |
| `/` | Listado publico de eventos | Publico |
| `/registro/` | Registro de usuarios | Publico |
| `/cuentas/login/` | Inicio de sesion | Publico |
| `/cuentas/logout/` | Cierre de sesion | Usuario autenticado |
| `/eventos/<id>/` | Detalle de evento | Publico |
| `/eventos/<id>/comprar/` | Crear orden de compra | Asistente |
| `/ordenes/<id>/pago-simulado/` | Confirmar pago simulado | Asistente |
| `/mis-entradas/` | Entradas del usuario | Asistente |
| `/entradas/<id>/` | Detalle de entrada y QR | Dueño u organizador |
| `/dashboard/` | Dashboard administrativo | Organizador/Admin |
| `/validar-acceso/` | Validacion de QR | Organizador/Admin |
| `/reportes/` | Reportes filtrables | Organizador/Admin |
| `/reportes/excel/` | Exportar Excel | Organizador/Admin |
| `/reportes/pdf/` | Exportar PDF | Organizador/Admin |
| `/gestion/eventos/` | CRUD de eventos | Organizador/Admin |
| `/gestion/categorias/` | CRUD de categorias | Organizador/Admin |
| `/gestion/ubicaciones/` | CRUD de ubicaciones | Organizador/Admin |
| `/gestion/tipos-entrada/` | CRUD de tipos de entrada | Organizador/Admin |
| `/admin/` | Admin nativo de Django | Admin |

## Estructura del proyecto

```text
.
|-- eventix/
|   |-- settings.py
|   |-- urls.py
|   |-- wsgi.py
|   `-- asgi.py
|-- eventos/
|   |-- admin.py
|   |-- apps.py
|   |-- context_processors.py
|   |-- forms.py
|   |-- models.py
|   |-- tests.py
|   |-- urls.py
|   |-- views.py
|   |-- management/
|   |   `-- commands/
|   |       `-- seed_demo.py
|   |-- migrations/
|   `-- templates/
|       `-- eventos/
|-- templates/
|   |-- base.html
|   `-- registration/
|-- static/
|   `-- css/
|       `-- styles.css
|-- media/
|   `-- qrcodes/
|-- manage.py
|-- requirements.txt
|-- Procfile
|-- runtime.txt
|-- .gitignore
`-- README.md
```

## Explicacion de archivos y carpetas

### `manage.py`

Archivo de comandos de Django. Se usa para ejecutar el servidor, migraciones, pruebas y comandos personalizados.

Ejemplos:

```powershell
python manage.py runserver
python manage.py migrate
python manage.py test
python manage.py seed_demo
```

### `eventix/`

Carpeta de configuracion global del proyecto.

- `settings.py`: configuracion general del proyecto.
- `urls.py`: rutas principales.
- `wsgi.py`: entrada para servidores de despliegue.
- `asgi.py`: entrada alternativa para servidores asincronos.

### `eventos/`

Aplicacion principal del sistema.

- `models.py`: modelos y relaciones de base de datos.
- `views.py`: logica de las paginas.
- `forms.py`: formularios y validaciones.
- `urls.py`: rutas propias de la aplicacion.
- `admin.py`: configuracion del panel administrativo.
- `tests.py`: pruebas automaticas.
- `context_processors.py`: datos globales para plantillas.
- `management/commands/seed_demo.py`: comando para cargar datos demo.

### `templates/`

Plantillas HTML globales.

- `base.html`: estructura principal, menu, footer y carga de estilos.
- `registration/login.html`: inicio de sesion.
- `registration/register.html`: registro de usuarios.

### `eventos/templates/eventos/`

Plantillas especificas de la aplicacion.

- `home.html`: listado y filtros de eventos.
- `evento_detalle.html`: detalle y compra.
- `pago_simulado.html`: simulacion de pago.
- `mis_entradas.html`: entradas del asistente.
- `entrada_detalle.html`: detalle del ticket y QR.
- `dashboard.html`: indicadores y graficos.
- `validar_acceso.html`: validacion de entradas.
- `reportes.html`: filtros y exportaciones.
- `eventos_admin.html`: gestion de eventos.
- `categorias_admin.html`: gestion de categorias.
- `ubicaciones_admin.html`: gestion de ubicaciones.
- `tipos_admin.html`: gestion de tipos de entrada.
- `form.html`: formulario reutilizable.
- `confirm_delete.html`: confirmacion de eliminacion.

### `static/`

Contiene archivos estaticos creados por el proyecto, como CSS, JavaScript o imagenes fijas.

En este sistema:

- `static/css/styles.css`: estilos personalizados de la interfaz.

### `staticfiles/`

Carpeta generada por `collectstatic`. Se usa para despliegue.

No se debe editar manualmente ni subir a Git.

### `media/`

Carpeta para archivos generados o subidos por el sistema.

En este proyecto guarda las imagenes QR:

```text
media/qrcodes/
```

### `db.sqlite3`

Base de datos local de desarrollo.

No se recomienda subirla a Git. Se puede reconstruir ejecutando:

```powershell
python manage.py migrate
python manage.py seed_demo
```

### `.venv/`

Entorno virtual de Python.

No se sube a Git. Cada equipo debe crear su propio entorno.

### `.gitignore`

Indica los archivos y carpetas que Git debe ignorar.

Ejemplos:

- `.venv/`
- `db.sqlite3`
- `__pycache__/`
- `staticfiles/`
- `.env`

### `requirements.txt`

Lista de dependencias necesarias para instalar el proyecto.

Instalacion:

```powershell
pip install -r requirements.txt
```

### `Procfile`

Archivo usado por plataformas como Render o Heroku para saber como iniciar la aplicacion.

Contenido:

```text
web: gunicorn eventix.wsgi
```

Significa que el proceso web debe iniciar usando Gunicorn y el archivo WSGI del proyecto.

### `runtime.txt`

Indica la version de Python sugerida para despliegue.

```text
python-3.12.13
```

## Instalacion local

### 1. Clonar el repositorio
```powershell
git clone url
```

### 2. Crear entorno virtual

```powershell
python -m venv .venv
```

### 3. Activar entorno virtual

En Windows PowerShell:

```powershell
.\.venv\Scripts\activate
```

### 4. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 5. Aplicar migraciones

```powershell
python manage.py migrate
```

### 6. Cargar datos de prueba

```powershell
python manage.py seed_demo
```

### 7. Ejecutar servidor

```powershell
python manage.py runserver
```

Abrir en el navegador:

```text
http://127.0.0.1:8000/
```

## Flujo de prueba sugerido

### Como asistente

1. Entrar a `/cuentas/login/`.
2. Iniciar sesion con `asistente` / `asistente123`.
3. Ir al inicio `/`.
4. Abrir un evento.
5. Comprar una entrada.
6. Confirmar el pago simulado.
7. Ir a `/mis-entradas/`.
8. Abrir el detalle de la entrada.
9. Revisar el codigo QR.

### Como organizador

1. Entrar a `/cuentas/login/`.
2. Iniciar sesion con `organizador` / `organizador123`.
3. Ir a `/dashboard/`.
4. Revisar graficos e indicadores.
5. Ir a `/gestion/eventos/`.
6. Crear o editar un evento.
7. Ir a `/validar-acceso/`.
8. Pegar el codigo de una entrada.
9. Validar el acceso.
10. Ir a `/reportes/`.
11. Exportar Excel o PDF.

### Como administrador

1. Entrar a `/admin/`.
2. Iniciar sesion con `admin` / `admin12345`.
3. Revisar usuarios, grupos, eventos, ordenes, entradas y validaciones.

## Comandos utiles

Crear migraciones:

```powershell
python manage.py makemigrations
```

Aplicar migraciones:

```powershell
python manage.py migrate
```

Cargar datos demo:

```powershell
python manage.py seed_demo
```

Ejecutar pruebas:

```powershell
python manage.py test
```

Verificar configuracion:

```powershell
python manage.py check
```

Recolectar archivos estaticos:

```powershell
python manage.py collectstatic --noinput
```

Crear superusuario manual:

```powershell
python manage.py createsuperuser
```

