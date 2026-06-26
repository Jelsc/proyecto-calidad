# CyberShield AI

MVP de detección y respuesta con login JWT y dashboard protegido.

## Credenciales demo

No uses estas credenciales fuera del entorno local.

- **Usuario:** `demo`
- **Contraseña:** `CyberShield123!`

## Ejecución

1. Copia `.env.example` a `.env` si lo necesitas.
2. Levanta el stack:

```bash
docker compose up --build
```

3. Abre la aplicación en:

- **Interfaz:** http://localhost:8080
- **Inicio de sesión:** la primera pantalla es el formulario de acceso

El backend crea/actualiza el usuario demo al arrancar, así que las credenciales anteriores deben funcionar justo después de `docker compose up`.

## Bootstrap del usuario demo

El backend ejecuta:

1. `python manage.py migrate --noinput`
2. `python manage.py bootstrap_demo_user`

El usuario demo se asigna por defecto al grupo `analyst`.
