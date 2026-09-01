# Clínica Salud Total — Sistema de Gestión de Citas Médicas

Sistema web desarrollado con **Django 4.2** para gestionar citas médicas, agendas de médicos, consultas clínicas y salas de atención.

---

## Cómo funciona

### Roles del sistema

| Rol               | Qué puede hacer                                                                               |
| ----------------- | --------------------------------------------------------------------------------------------- |
| **Administrador** | Accede al panel admin (`/admin/`), gestiona usuarios, especialidades, salas y genera reportes |
| **Médico**        | Crea su agenda semanal, confirma o rechaza citas, registra consultas y diagnósticos           |
| **Paciente**      | Reserva citas según disponibilidad, ve su historial de consultas                              |

### Flujo principal de una cita

```
Paciente reserva cita
       v
   Estado: PENDIENTE -> se notifica al médico por email
       v
Médico confirma / rechaza  (o el sistema auto-confirma tras 2 horas)
       v
   Estado: CONFIRMADA -> se notifica al paciente por email
       v
El día de la cita el médico registra la Consulta (diagnósticos, prescripciones)
       v
   Estado cita: COMPLETADA
```

### Estructura de apps

```
mi_proyecto/
├── core/           -> Landing, dashboard, reportes, middleware de roles
├── usuarios/       -> Registro con verificación por email, login, perfil
├── citas/          -> Agenda médico, reserva de citas, salas, notificaciones
└── consultas/      -> Registro de consultas, diagnósticos, prescripciones, historial
```

### Salas de atención médica

- Hay 10 salas cargadas: C-01 a C-06 (consulta), P-01/P-02 (procedimiento), U-01/U-02 (urgencias).
- Al crear su agenda el médico recibe **automáticamente** una sala de consulta para cada día.
- Un médico usa la **misma sala todo el día**; otros médicos no pueden usar esa sala ese día.

### Seguridad implementada

- `SECRET_KEY`, credenciales SMTP en `.env` (nunca dentro del código)
- Middleware de roles: rutas protegidas por login y por rol
- Verificación de email al registrarse (código de 5 min, máx. 5 intentos)
- Logout solo por POST con CSRF token
- `X_FRAME_OPTIONS = DENY`, `SECURE_CONTENT_TYPE_NOSNIFF`
- Sesión expira a los 30 min de inactividad

---

## Inicio rápido

### Requisitos previos

- Python 3.12+
- XAMPP con MySQL/MariaDB corriendo en puerto **3307**(ajustar si usas otro puerto)
- Cuenta Gmail con [contraseña de aplicación](https://myaccount.google.com/apppasswords) (para emails en este caso)

```
Crear Gmail → entrar a Cuenta de Google → Seguridad → activar Verificación en 2 pasos → buscar Contraseñas de aplicaciones → escribir un nombre para la aplicación → Crear → copiar la contraseña de 16 caracteres y usarla en la aplicación.
```

### 1. Crear entorno virtual e instalar dependencias

```powershell
# Desde la carpeta raíz del proyecto
python -m venv .venv
.\.venv\Scripts\activate
pip install -r mi_proyecto/requirements.txt
```

### 2. Crear la base de datos en phpMyAdmin

1. Abrir `http://localhost/phpmyadmin`
2. Crear una base de datos llamada `mi_proyecto_db` con cotejamiento `utf8mb4_general_ci`

### 3. Configurar variables de entorno

Copiar `mi_proyecto/.env.example` como `mi_proyecto/.env` y reemplazar los
valores locales. Para generar una clave segura:

```powershell
..\.venv\Scripts\python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Configuración mínima de desarrollo:

```ini
SECRET_KEY=pega_aqui_la_clave_generada
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=mi_proyecto_db
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3307
EMAIL_HOST_USER=tu_correo@gmail.com
EMAIL_HOST_PASSWORD=tu_contraseña_de_aplicacion
```

> El archivo `.env` contiene secretos y está excluido de Git. No lo publiques.
> Para producción usa `DJANGO_DEBUG=False`, configura el dominio en
> `DJANGO_ALLOWED_HOSTS`
> y activa las opciones HTTPS documentadas en `.env.example` solamente cuando
> el sitio disponga de un certificado válido.

### 4. Aplicar migraciones y crear datos iniciales

```powershell
cd mi_proyecto

# Crear tablas en la BD
..\.venv\Scripts\python manage.py migrate

# Crear superusuario (admin)
..\.venv\Scripts\python manage.py createsuperuser

# Cargar las 10 salas de consulta iniciales
..\.venv\Scripts\python manage.py crear_salas
```

### 5. Levantar el servidor

```powershell
..\.venv\Scripts\python manage.py runserver
```

Abrir en el navegador: **http://127.0.0.1:8000/**

---

## URLs principales

| URL                      | Descripción                         |
| ------------------------ | ----------------------------------- |
| `/`                      | Página de inicio                    |
| `/usuarios/registro/`    | Registro de nuevo usuario           |
| `/usuarios/login/`       | Inicio de sesión                    |
| `/dashboard/`            | Panel principal (requiere login)    |
| `/citas/reservar/`       | Reservar cita (paciente)            |
| `/citas/mis-citas/`      | Ver mis citas (paciente)            |
| `/citas/agenda/`         | Ver agenda (médico)                 |
| `/citas/agenda/agregar/` | Crear horarios disponibles (médico) |
| `/consultas/mis-citas/`  | Citas del día (médico)              |
| `/consultas/buscar/`     | Buscar paciente por RUT (médico)    |
| `/reportes/`             | Reporte general (admin)             |
| `/admin/`                | Panel de administración Django      |

---

## Usuarios de prueba (entorno local)

Estas son credenciales de ejemplo para una base de datos exclusivamente local.
No deben reutilizarse en un despliegue ni corresponden a cuentas incluidas en
el repositorio.

| Usuario        | Contraseña      | Rol          |
| -------------- | --------------- | ------------ |
| `admin`        | `Admin1234!`    | Superusuario |
| `dra.martinez` | `Medico1234!`   | Médico       |
| `dr.rojas`     | `Medico1234!`   | Médico       |
| `dra.vega`     | `Medico1234!`   | Médico       |
| `paciente1`    | `Paciente1234!` | Paciente     |

---

## Pruebas y verificaciones

La suite usa SQLite en memoria y un backend de correo local, por lo que no
modifica la base de datos MySQL ni envía mensajes reales:

```powershell
$env:DJANGO_SETTINGS_MODULE='mi_proyecto.settings_test'
..\.venv\Scripts\python manage.py check
..\.venv\Scripts\python manage.py makemigrations --check --dry-run
..\.venv\Scripts\python manage.py test
```

GitHub Actions ejecuta estas comprobaciones automáticamente en cada cambio de
la rama `main` y en cada pull request dirigido a ella.

---

## Capturas

Las capturas de las pantallas principales se incorporarán al finalizar el
proyecto.

---

## Stack tecnológico

| Capa          | Tecnología                                     |
| ------------- | ---------------------------------------------- |
| Backend       | Django 4.2 / Python 3.12                       |
| Base de datos | MySQL 8 / MariaDB (XAMPP)                      |
| Frontend      | Bootstrap 5.3.3 + Bootstrap Icons 1.11.3 (CDN) |
| Email         | Gmail SMTP via `django.core.mail`              |
| Config segura | python-decouple 3.8                            |

---

## ====================================================

## Advertencia: Prettier rompe los templates Django

## ====================================================

**No uses Prettier (ni ningún formatter HTML) sobre los archivos de `templates/`.**

Django usa etiquetas de la forma `{% block contenido %}` y `{{ variable }}`. Prettier las parte en varias líneas porque supera su límite de 80 caracteres:

```html
<!-- Antes (correcto) -->
{% extends 'base.html' %} {% block titulo %}Título{% endblock %} {% block
contenido %}

<!-- Después al guardar el Prettier (ROTO — Django no acepta saltos dentro de {% %}) -->
{% extends 'base.html' %} {% block titulo %}Título{% endblock %} {% block
contenido %}
```

Esto produce errores como:

```
TemplateSyntaxError: Invalid block tag on line X: 'endblock'
TemplateSyntaxError: Unclosed tag on line 1: 'block'
```

### Protección instalada

El proyecto ya incluye dos archivos que bloquean el formatter:

- **`.prettierignore`** — excluye toda la carpeta `templates/` de Prettier
- **`.vscode/settings.json`** — desactiva `formatOnSave`, `formatOnPaste` y el formatter por defecto para archivos HTML

Si aun así el formatter actúa (puede ocurrir tras actualizar extensiones), ejecuta este comando para detectar y reportar todos los templates rotos de una sola pasada:

```powershell
cd mi_proyecto
..\.venv\Scripts\python -c "
import os
base = r'templates'
for root, _, files in os.walk(base):
    for fn in files:
        if not fn.endswith('.html'): continue
        lines = open(os.path.join(root, fn), encoding='utf-8').readlines()
        for i, l in enumerate(lines, 1):
            s = l.rstrip()
            if ('{%' in s and '%}' not in s) or ('{{' in s and '}}' not in s):
                print(f'{fn}:{i}: {s[:120]}')
"
```

Si no produce ninguna salida, todos los templates están bien y no hay que tocarlos.
