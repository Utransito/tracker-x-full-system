# GDN · Centro de Análisis y Seguridad Empresarial

Versión corregida del sistema, reestructurada para respetar el flujo documental del archivo `SIS_TRAKER v3.pdf`:

- Pantalla 01: generación de alerta
- Pantalla 02: espacio tiempo / tienda / georreferenciación
- Pantalla 03: novedad
- Pantalla 04: víctimas
- Pantalla 05: perfiles
- Pantalla 06: mercadería / bienes
- Pantalla 07: álbum fotográfico
- Pantalla 08: seguimiento de la novedad
- Pantalla 09: situación legal del sospechoso

## Stack

- FastAPI
- SQLAlchemy + SQLite
- Jinja2
- Bootstrap 5
- OpenPyXL
- ReportLab

## Usuarios iniciales

- admin / admin123
- central / 123456
- hurtos / 123456
- delitos / 123456

## Ejecución

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Abrir:

```text
http://127.0.0.1:8000
```

## Notas

- Esta versión corrige la lógica condicional principal del documento.
- El campo de central de monitoreo solo debe usarse para HURTO.
- Se incorporan víctimas, sospechosos, mercadería y notas fotográficas como arreglos JSON gestionados desde el formulario.
- Incluye PDFs de denuncia, diligencias y acta de audiencia.
- La arquitectura queda preparada para seguir creciendo a un sistema productivo con hashing, permisos finos, paginación, catálogos completos y adjuntos múltiples.
