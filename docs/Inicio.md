# 🏫 NEXUS ENTERPRISE | Bóveda de Documentación

Bienvenido a la documentación técnica y operativa del **Sistema Integrado de Gestión de Inventario NEXUS** para la **I.E. Guaimaral**. Esta bóveda de Obsidian está diseñada para actuar como la memoria local y de contexto para el desarrollo y mantenimiento del software.

## 📂 Estructura de la Bóveda

Esta documentación está organizada en las siguientes secciones clave para facilitar la navegación y edición:

1. **[Estructura y Arquitectura](Arquitectura.md)**: Información técnica sobre el diseño del software, CustomTkinter, concurrencia (hilos) y la infraestructura del sistema.
2. **[Esquema de Base de Datos](Base_de_Datos.md)**: Detalle técnico de las tablas SQLite (`assets`, `dependencies`, `loans`), triggers de sincronización y optimizaciones de rendimiento en disco (WAL).
3. **[Motor de Importación y Exportación](Importacion_y_Exportacion.md)**: Explicación del sistema de mapeo inteligente de columnas para la importación desde planillas Excel de la Secretaría de Educación.
4. **[Lógica de Bajas Patrimoniales](Lógica_de_Bajas.md)**: Reglas y cálculos matemáticos aplicados durante las bajas totales y parciales de activos (depreciación acumulada y valor en libros).

---

## 🚀 Ficha del Proyecto

* **Entidad**: Institución Educativa Guaimaral (Guaimaral-Atlántico)
* **Tecnología**: Python 3.13 + CustomTkinter + SQLite3
* **Estado**: Producción (333 activos cargados)
* **Objetivo principal**: Controlar el inventario físico, préstamos a docentes, traslados entre aulas y reportar el balance contable amortizado.
