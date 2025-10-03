# REDEPSE
**Registro de Escuelitas de formación DEPortiva de Santiago del Estero**

## 📌 Descripción del Proyecto
REDEPSE es un sistema web desarrollado con **Django** y **MySQL** como base de datos, cuyo objetivo principal es centralizar el **registro y gestión de escuelitas deportivas** de la provincia de Santiago del Estero.  

Este proyecto forma parte de nuestra **Práctica Profesionalizante** de la **Tecnicatura Superior en Desarrollo de Software**, y tiene como finalidad aplicar en un caso real los conocimientos adquiridos durante la carrera, trabajando en equipo bajo metodologías y herramientas de desarrollo profesional.

El sistema permitirá que cada escuelita cree un usuario, cargue sus datos institucionales y presente la documentación necesaria para registrarse en la Secretaría de Deportes.  
Por su parte, la Secretaría contará con un panel de administración propio (diferente al admin de Django) desde donde podrá gestionar las solicitudes recibidas y analizar estadísticas sobre las escuelas registradas.

---

## 🎯 Objetivos del Sistema
- Facilitar el **registro digital** de las escuelitas deportivas.
- Permitir a la **Secretaría de Deportes** llevar un control centralizado de las solicitudes.
- Reducir la burocracia y los trámites manuales con un flujo **online y transparente**.
- Ofrecer herramientas para mejorar la toma de decisiones.

---

## 🏫 Funcionalidades principales

### 🔹 Escuelitas deportivas
- Registro de usuario y acceso seguro mediante login.
- Completar formularios de inscripción con:
  - Datos institucionales
  - Cantidad de entrenadores
  - Cantidad de alumnos
  - Disciplinas ofrecidas
  - Instalaciones deportivas (canchas, espacios, etc.)
  - Subida de documentos (PDFs, certificados, fotos de perfil, etc.)
- Seguimiento del estado de la solicitud:
  - Pendiente
  - Aprobada
  - Rechazada
  - Pausada (en espera de documentación adicional)
- Notificaciones sobre cambios en el estado de la solicitud.

### 🔹 Secretaría de Deportes (Panel Administrativo)
- Visualización de solicitudes pendientes.
- Aprobación, rechazo o solicitud de información adicional a las escuelitas.
- Gestión de escuelitas ya registradas.
- Panel con indicadores como:
  - Cantidad total de escuelitas registradas
  - Escuelas por localidad
  - Promedio de alumnos por escuelita
- Interfaz **ligera y de fácil uso**, diferente al admin técnico de Django.

---

## 👥 Equipo de Desarrollo
Este proyecto forma parte de la **Práctica Profesionalizante** del equipo conformado por:  
- Juan Cruz  
- Máximo  
- Mariano  
- Julián  
- Juan  

---

## ⚙️ Tecnologías utilizadas
- **Backend:** Django (Python)  
- **Base de datos:** MySQL  
- **Frontend:** HTML, CSS, JavaScript (con posibilidad de usar plantillas responsivas ligeras)  
- **Control de versiones:** Git + GitHub  
- **Gestión del proyecto:** Trello/Jira
