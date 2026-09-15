# 🏫 Sistema de Control de Inventario - I.E. Guaimaral

Sistema integral de auditoría, control patrimonial, registro de activos físicos, gestión de dependencias y préstamos para la **Institución Educativa Guaimaral** (Sedes: *Guaimaral* y *Cuatro Bocas*).

---

## 🚀 Descarga Directa del Instalador (.exe)

Para instalar el programa en cualquier equipo con Windows sin necesidad de instalar Python:

[![Descargar Instalador](https://img.shields.io/badge/Descargar-Instalador%20Windows%20(.exe)-0284c7?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/proyectomexic12-lang/INVEBTARIO-COLEGIO/releases/latest/download/Instalar_Control_Inventario.exe)

> 🔗 **Enlace directo de descarga:**  
> 👉 **[Descargar Instalar_Control_Inventario.exe](https://github.com/proyectomexic12-lang/INVEBTARIO-COLEGIO/releases/latest/download/Instalar_Control_Inventario.exe)**  
> *(Versión estable v1.0.0 - Incluye instalador automático y acceso directo en el escritorio).*

Para ver el historial de versiones y notas de la versión:  
👉 **[Ver Sección de Releases en GitHub](https://github.com/proyectomexic12-lang/INVEBTARIO-COLEGIO/releases)**

---

## ✨ Módulos Principales

* 📊 **Panel Maestro (Consola Ejecutiva):** Métricas patrimoniales en tiempo real, valor histórico, depreciación acumulada y valor en libros.
* 📝 **Unidad de Registro:** Alta de bienes institucionales con códigos únicos por sede, cálculo automático de vida útil y depreciación.
* 📦 **Gestión Global:** Catálogo general con búsqueda ultrarrápida, filtros avanzados, traslados masivos y exportación oficial a Excel / PDF.
* 🤝 **Préstamos y Asignaciones:** Control de equipos entregados a docentes y funcionarios, actas de entrega digitales y seguimiento de devoluciones.
* 🏢 **Salones y Dependencias:** Control de inventarios por salón y aula física (sin salones comodines).
* ⚙️ **Gestión del Sistema:** Copias de seguridad atómicas consistentes, auditoría de cambios y configuración general.

---

## 💻 Ejecución desde Código Fuente (Desarrollo)

Si deseas ejecutar el proyecto en modo desarrollo:

```bash
# 1. Clonar el repositorio
git clone https://github.com/proyectomexic12-lang/INVEBTARIO-COLEGIO.git
cd INVEBTARIO-COLEGIO/desktop_app

# 2. Crear y activar entorno virtual
python -m venv venv
.\venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Iniciar la aplicación
python main.py
```

---

## 🛠️ Compilación del Instalador

Para compilar el archivo `.exe` desde el entorno de desarrollo:

```bash
cd desktop_app
.\venv\Scripts\python.exe builder.py
```
El instalador resultante se generará en la carpeta raíz como `Instalar_Control_Inventario.exe`.
