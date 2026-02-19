# Prueba tecnica - Login y visualizacion por rol

Aplicacion web con login, manejo de sesion por cookies (HTTPOnly) y visualizacion de usuarios segun rol (admin/supervisor/usuario). 

## Requisitos
- Python 3.11+ (recomendado)
- pip

## Stack (segun requerimiento)
- Frontend: HTML/CSS/JavaScript + jQuery + DataTables.
- Backend: Python + Litestar. 
- Base de datos: SQLite. 
- Hash de password: bcrypt.

## Estructura del proyecto
- backend/
  - app.py (API + static files + init DB)
  - db.py, models.py, auth.py (logica de datos y autenticacion)
- frontend/
  - index.html (login)
  - dashboard.html (tabla DataTables)
- data/
  - usuarios.json
- requirements.txt

## Instalacion (local)
1) Clonar y entrar al proyecto:
```bash
git clone <TU_URL>
cd <TU_REPO>
```

2) Crear y activar entorno virtual:

Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Mac/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

3) Instalar dependencias:
```bash
python -m pip install -r requirements.txt
```

## Ejecucion (local)
Importante: corre el backend desde la carpeta `backend/` para que funcionen las rutas relativas (DB y JSON).

```bash
cd backend
python app.py
```

Luego abre en el navegador:
- http://127.0.0.1:8000/index.html

## Credenciales de prueba
- Password para todos: `password`
- Username: se genera como `<nombre_slug>_<id>`

Ejemplos:
- Admin: `jhon_doe_1`
- Admin: `juan_perez_2`
- Supervisor: `ana_torres_3`
- Usuario: `valentina_rios_11`

## Reglas de visualizacion por rol
- Admin: ve todos los usuarios (admins, supervisores y usuarios). 
- Supervisor: ve supervisores y usuarios, no ve admins.
- Usuario: solo se ve a si mismo. 

## Endpoints
- POST `/auth/login`
  - Body JSON: `{ "username": "...", "password": "..." }`
  - Setea cookies HTTPOnly: `user_id`, `role`
- POST `/auth/logout`
  - Borra cookies `user_id`, `role`
- GET `/usuarios`
  - Requiere cookies, retorna usuarios segun rol

## Reset de base de datos (opcional)
Si quieres volver a poblar desde `data/usuarios.json`:

Windows (PowerShell):
```powershell
cd backend
$env:RESET_DB="1"
python app.py
```

Mac/Linux:
```bash
cd backend
RESET_DB=1 python app.py
```

## Notas
- No se utilizan frameworks externos de autenticacion (ej: Firebase Auth, Auth0). 
- La tabla del dashboard usa DataTables para busqueda, paginacion y ordenamiento. 


## Pruebas (pytest)
Desde la raiz del proyecto:

```bash
python -m pytest -q
```
```Si quieres ver el nombre de cada test:
python -m pytest -v
```
# Deploy en Render (extra)
```Si lo despliegas en Render como Web Service, el Start Command recomendado es:
uvicorn backend.app:app --host 0.0.0.0 --port $PORT
```
URL del deploy:

https://prueba-tecnica-zqjl.onrender.com/index.html
