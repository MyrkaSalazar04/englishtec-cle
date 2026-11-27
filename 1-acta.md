# Misión 1 · Acta de constitución e Interesados

- **Consultora:** EnglishTec · Myrka Neftalí Salazar Morales
- **Cliente:** TecNM Campus Matehuala · Coordinación de Lenguas Extranjeras (CLE) · Responsable: Christian Alejandro Valdez Gea, Coordinador
- **Proyecto:** Sistema de Pre-Registro y Consulta de Calificaciones de Los Cursos de Inglés
- **Fecha del Acta:** 26 de noviembre de 2026

---

## 1. Acta de Constitución

**Propósito.** Automatizar la parte humana del proceso de la CLE que hoy se hace a mano: anotar a los interesados en una hoja impresa y buscar al docente para saber si se aprobó el curso. El alumno se pre-registra desde su celular y consulta su resultado en línea.

**Objetivos Medibles.**
1. Que el pre-registro se complete en **5 Minutos o Menos** (hoy: de 20 a 30 minutos, según las 3 entrevistas a alumnos).
2. Que el alumno consulte su resultado **Sin Buscar Al Docente** (hoy: unas 2 veces por alumno, según las 3 entrevistas).
3. Que la Coordinación vea el **Estado de Los 10 Grupos** (pendiente, capturado o publicado) sin preguntar a cada docente.
4. Que el **SUS Promedio Sea de 70 o Más** con 5 usuarios, y que se aprueben las pruebas de los **10 Requisitos «Debe»**.

**Alcance General.** Pre-registro con QR o enlace; lista, pago, nivel y grupo para la Coordinación; captura, importación y publicación de calificaciones por el docente; consulta del alumno con resultado Aprobado o Reprobado. Detalle en `2-alcance.md`.

**Fuera del Alcance.** Pagos en línea o trámite con Financieros, examen digital dentro del sistema, integración con el sistema escolar institucional y NIP institucional.

**Supuestos.**
- El coordinador valida la propuesta y está de acuerdo con ella (ya lo expresó en la entrevista).
- Todos los datos son simulados; nunca se usan datos reales de alumnos ni de personal.
- Los docentes **No Fueron Entrevistados**: sus necesidades se infieren de lo que dijo el coordinador y de los alumnos, y se validarán antes del cierre.
- El hospedaje gratuito de Render basta para la demostración.

**Presupuesto.** Construcción: horas estimadas por una tarifa justificada, que se calcula en `3-cronograma.md`. Operación mensual: **$0 MXN** con el plan gratuito de Render; el precio, la liga y la fecha de consulta se registran en `3-cronograma.md`.

**Fecha Límite.** Lunes 7 de diciembre de 2026, 7:00 a.m. Revisiones: 30 de noviembre, 2 y 4 de diciembre.

**Criterio de Éxito.** El sistema corre en la nube con datos simulados; cumple los 10 requisitos «Debe» con pruebas aprobadas; el alumno ve su resultado correcto (Aprobado con general de 70 o más); y el cliente firma el acta de aceptación.

---

## 2. Matriz de Interesados

| Interesado | Poder | Interés | Qué quiere | Qué cede | Estrategia |
|---|---|---|---|---|---|
| **Coordinación de Lenguas Extranjeras** (coordinador) | Alto | Alto | Una base de datos de pre-registros con enlace o QR, saber qué grupos ya tienen calificaciones y conservar el control del pago, del nivel y del archivo físico. | La publicación de calificaciones: la hace el docente, no la Coordinación. El pago y el nivel siguen siendo manuales (el sistema solo los registra). | **Gestionar de Cerca.** Mostrarle el avance en cada revisión y validar con él cada regla de negocio. |
| **Docentes de Inglés** | Alto | Bajo | Seguir usando su Excel actual y no capturar dos veces. Decidir cuándo se publican las calificaciones de su grupo. | Capturan o importan en el sistema, no solo en la hoja de OneDrive, y dan un paso más: publicar. Su avance queda visible para la Coordinación. | **Mantener Satisfechos.** Importación directa de su Excel y publicación con un solo botón. *Inferido; se valida con ellos.* |
| **Alumnos** | Bajo | Alto | Consultar su resultado desde el celular, a cualquier hora, y tener fechas e información en un solo lugar. | Ven sus calificaciones hasta que el docente las publica, no en cuanto las captura. Usan un código propio además de su número de control. | **Mantener Informados.** Mensajes claros de estado («aún no publicadas»), fechas del examen y diseño para celular. |

---

## 3. Conflicto Principal y Cómo Se Resuelve

**El Conflicto: ¿Cuándo Ve El Alumno Su Calificación?**
- El **Alumno** quiere verla en cuanto exista.
- La **Coordinación** y el **Docente** quieren revisarla antes de que se haga pública, porque un error visible para todos cuesta más que esperar.

**Decisión.** La captura y la publicación son pasos separados. El docente captura o importa las calificaciones de su grupo (estado «capturado») y las publica cuando las revisó (estado «publicado»). Mientras tanto, el alumno ve un mensaje que dice que aún no están publicadas, y la Coordinación ve el estado de cada grupo y puede imprimir un PDF en «borrador».

**Qué Cede Cada Uno.**
- **El Alumno** espera a la publicación, pero deja de buscar al docente y siempre sabe en qué estado está su resultado.
- **El Docente** hace un paso más (publicar) y su avance es visible para la Coordinación.
- **La Coordinación** renuncia a publicar por su cuenta; decide el docente.

**Qué Esconde Esta Decisión.** Si el docente olvida publicar, el alumno sigue esperando. Se mitiga con la vista de estados de la Coordinación, que muestra qué grupos están «capturados» sin publicar, y se registra como riesgo en `5-riesgos.md`.
