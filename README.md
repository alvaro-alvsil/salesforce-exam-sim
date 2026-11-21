# ⚡ Salesforce Certification Exam Simulator (Streamlit)

Simulador interactivo y profesional para exámenes de certificación de Salesforce (Administrator, Developer, App Builder, etc.), diseñado para replicar la experiencia de examen real de **Kryterion / Webassessor**.

---

## 🚀 Cómo Ejecutar la Aplicación

Dado que estás trabajando dentro de un **Dev Container** de Visual Studio Code:

1. Abre una terminal dentro del contenedor de VS Code (`Terminal` -> `New Terminal`).
2. Ejecuta el siguiente comando para arrancar Streamlit en el puerto expuesto `8501`:
   ```bash
   streamlit run app.py --server.address 0.0.0.0
   ```
3. VS Code detectará automáticamente el puerto `8501` y abrirá una notificación para abrirlo en tu navegador, o puedes abrirlo directamente en:
   ```
   http://localhost:8501
   ```

---

## 📁 Estructura del Proyecto

```text
salesforce-exam-sim/
├── .devcontainer/
│   └── devcontainer.json      # Configuración del entorno Dev Container
├── exams/
│   └── sample_admin.json      # Examen de ejemplo (Salesforce Administrator)
├── app.py                     # Aplicación principal de Streamlit
├── requirements.txt           # Dependencias de Python
└── README.md                  # Documentación
```

---

## 📝 Cómo Añadir Nuevos Exámenes

La aplicación escanea dinámicamente cualquier archivo `.json` que se encuentre dentro de la carpeta `exams/`.

Para añadir un nuevo examen (por ejemplo, *Platform App Builder* o *Platform Developer I*):

1. Crea un nuevo archivo en `exams/mi_nuevo_examen.json`.
2. Sigue estrictamente la siguiente estructura JSON:

```json
{
  "exam_title": "Salesforce Certified Platform App Builder",
  "time_limit_minutes": 105,
  "passing_score_percent": 68,
  "questions": [
    {
      "id": 1,
      "topic": "Data Modeling and Management",
      "type": "single",
      "question": "¿Cuál es la consecuencia directa de convertir una relación de tipo Lookup a Master-Detail?",
      "options": {
        "A": "Todos los registros secundarios deben tener un valor en el campo de búsqueda antes de la conversión.",
        "B": "Se eliminan automáticamente los campos calculados existentes.",
        "C": "El objeto principal pierde el acceso a reglas de flujo de trabajo.",
        "D": "No es posible convertir un campo Lookup en Master-Detail bajo ninguna circunstancia."
      },
      "correct_answers": ["A"],
      "explanation": "Para convertir una relación de búsqueda (Lookup) en una relación principal-detalle (Master-Detail), todos los registros existentes deben tener un valor asignado en el campo de búsqueda previo al cambio de tipo."
    },
    {
      "id": 2,
      "topic": "Business Logic and Process Automation",
      "type": "multiple",
      "question": "¿Qué DOS capacidades están disponibles exclusivamente en Record-Triggered Flows frente a Workflow Rules heredadas? (Elige 2)",
      "options": {
        "A": "Ejecución antes de guardar (Before-Save) para actualización rápida de campos sin DML recursivo.",
        "B": "Envío de correos electrónicos estándar.",
        "C": "Capacidad de actualizar registros secundarios o no relacionados de cualquier objeto.",
        "D": "Creación automática de registros de tareas pendientes."
      },
      "correct_answers": ["A", "C"],
      "explanation": "Los Record-Triggered Flows permiten actualizaciones Before-Save que ahorran tiempo de CPU y no requieren DML, además de la capacidad de crear y actualizar registros no relacionados o en objetos heterogéneos, algo que las reglas de flujo de trabajo heredadas no podían hacer."
    }
  ]
}
```

### Campos Clave del JSON:
- `exam_title`: Nombre que aparecerá en el selector y en el encabezado.
- `time_limit_minutes`: Duración límite del examen en minutos.
- `passing_score_percent`: Nota de corte requerida (ej. `65` para el 65%).
- `questions`: Lista de preguntas:
  - `id`: Identificador numérico o secuencial.
  - `topic`: Área temática oficial de la guía de examen de Salesforce.
  - `type`: `"single"` (para preguntas de 1 única respuesta) o `"multiple"` (para preguntas de elección múltiple).
  - `question`: Enunciado de la pregunta.
  - `options`: Diccionario con las alternativas con clave `"A"`, `"B"`, `"C"`, `"D"`, etc.
  - `correct_answers`: Lista con las letras correctas (ej. `["A"]` o `["A", "C"]`).
  - `explanation`: Explicación detallada con justificación técnica basada en la documentación oficial y Trailhead.

---

## 🌟 Funcionalidades Incluidas

1. **Selector Dinámico y Modos de Aprendizaje:**
   - **⏱️ Modo Examen:** Cronómetro con cuenta atrás, simulación estricta sin feedback inmediato hasta entregar, idéntico a Kryterion.
   - **🎓 Modo Estudio:** Práctica guiada con botón para comprobar respuestas al instante y leer la explicación oficial antes de avanzar.
   - **Barajado Opcional:** Posibilidad de aleatorizar el orden de las preguntas y de las opciones.

2. **Interfaz de Examen Profesional (UI/UX Salesforce):**
   - **Matriz de Navegación Rápida:** Cuadrícula lateral con salto directo a cualquier pregunta indicando visualmente su estado:
     - 🚩 Preguntas marcadas para revisar (*Marcar para revisar*).
     - ✅ Preguntas respondidas.
     - ⚪ Preguntas pendientes.
   - **Validación Inteligente:** Alertas en preguntas múltiples cuando faltan o sobran opciones seleccionadas.
   - **Confirmación de Entrega:** Resumen de preguntas pendientes o marcadas antes de enviar.

3. **Informe Oficial de Resultados y Revisión:**
   - Gran distintivo **APROBADO** (verde) o **NO APTO** (rojo) según el porcentaje de corte.
   - **Desglose por Áreas Temáticas (Section Breakdown):** Gráfico de barras interactivo y tabla con el % de aciertos por cada tema de la guía de certificación.
   - **Revisión Detallada con Filtros:** Filtra por *Todas*, *Solo Falladas*, *Marcadas para Revisión* o *Solo Acertadas*, con comparativa visual entre tu respuesta y la correcta junto a la explicación técnica.
