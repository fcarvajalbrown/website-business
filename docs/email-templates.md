# Outreach Templates — Sequence completa

**Variables Brevo:** `{{ contact.NOMBRE }}` / `{{ contact.STARTUP }}`  
**Variables GMass / mail merge genérico:** `{{nombre}}` / `{{startup}}`  
Usar el formato según la plataforma. Abajo se usa `{{}}` para legibilidad.

---

## Variables por lead

| Variable | Columna CSV | Fallback si vacío |
|----------|-------------|-------------------|
| `{{nombre}}` | `contact_1_name` | `equipo` |
| `{{startup}}` | `company` | (requerido, nunca vacío) |
| `{{ciudad}}` | `city` | `Santiago` |

---

## EMAIL 1 — Día 0 · Intro fría

### Asunto (A/B test — usar uno por fase)

| Versión | Asunto |
|---------|--------|
| A (recomendado) | `{{startup}} no tiene sitio web — lo resuelvo en 2 semanas` |
| B | `¿Por qué {{startup}} no aparece en Google?` |
| C | `Sitio web para {{startup}}: 14 días, precio fijo` |

### Cuerpo

```
Hola {{nombre}},

Encontré {{startup}} buscando empresas sin presencia web en Chile. Trabajo interesante — pero no hay dónde mandar a un cliente a conocerte.

Soy Felipe Carvajal, desarrollador en Santiago. Resuelvo exactamente esto:

Si no entrego en 14 días, devuelvo el pago completo. Sin excusas.

— Dominio .cl incluido
— Diseño limpio y rápido, apareces en Google desde el día 1
— $600 USD precio fijo, sin sorpresas

¿Tienes 20 minutos esta semana?

Felipe
felipecarvajal.cl
```

---

## EMAIL 2 — Día 3 · Follow-up corto

### Asunto

```
Re: {{startup}} no tiene sitio web — lo resuelvo en 2 semanas
```

*(responder al hilo del email 1 — Brevo lo hace automático)*

### Cuerpo

```
Hola {{nombre}},

Solo quería asegurarme de que no se perdió mi mensaje anterior.

Si no es el momento indicado, sin problema — solo dime y no te escribo más.

Felipe
felipecarvajal.cl
```

---

## EMAIL 3 — Día 7 · Valor concreto

### Asunto

```
Lo que incluye el sitio de {{startup}} (y cuánto demora)
```

### Cuerpo

```
Hola {{nombre}},

Por si sirve de contexto antes de decidir:

Lo que entrego en 14 días para {{startup}}:
— Sitio de 1 a 5 páginas (inicio, servicios, contacto, sobre nosotros)
— Dominio .cl registrado a tu nombre
— Hosting por 1 año incluido
— Optimizado para celular y para Google
— Formulario de contacto funcional

Garantía de plazo: si no lo entrego en 14 días, devuelvo el 100% del pago. No he incumplido esta garantía hasta hoy.

¿Coordinamos una llamada de 20 minutos esta semana?

Felipe
felipecarvajal.cl
```

---

## EMAIL 4 — Día 14 · Cierre

### Asunto

```
Último mensaje — {{startup}}
```

### Cuerpo

```
Hola {{nombre}},

Este es mi último mensaje para no ser molesto.

Si en algún momento necesitan un sitio web confiable, entregado a tiempo y sin sorpresas en el precio, saben dónde encontrarme.

Mucho éxito con {{startup}}.

Felipe
felipecarvajal.cl
```

---

## WHATSAPP 1 — Día 2

*(Máx. 160 caracteres para que se vea sin expandir)*

```
Hola {{nombre}}, te escribí por email sobre {{startup}}. Vi que no tienen sitio web — lo resuelvo en 2 semanas, precio fijo. ¿Hablamos? felipecarvajal.cl
```

---

## WHATSAPP 2 — Día 9

```
Hola {{nombre}}, última vez que te escribo. Si en algún momento necesitan sitio web para {{startup}}, aquí estoy. Saludos, Felipe.
```

---

## VARIANTE MINERÍA — Email 1 (leads direcmin)

Para los 151 leads de direcmin: el pitch es diferente — tienen website, no es "te falta sitio", es "tu presencia digital no te representa".

### Asunto

```
{{startup}}: presencia digital que esté a la altura
```

### Cuerpo

```
Hola {{nombre}},

Vi {{startup}} en el directorio de proveedores mineros. Buena reputación en el sector — pero cuando un cliente potencial busca en Google, lo que encuentra no hace justicia a lo que realmente hacen.

Soy Felipe Carvajal, desarrollador en Santiago. Trabajo con empresas B2B que necesitan un sitio profesional sin el tiempo ni el presupuesto para una agencia.

Si no entrego en 14 días, devuelvo el pago completo.

— Rediseño completo o sitio nuevo
— Dominio .cl si no tienen, o migración
— $600 USD precio fijo

¿Tienes 20 minutos esta semana?

Felipe
felipecarvajal.cl
```

---

## Notas de uso

**Brevo:** Crear una campaña por cada fase CSV. Secuencia automática en emails 2, 3, 4. Brevo detiene la secuencia si el lead responde.

**Personalización mínima antes de enviar phase3:** Para los 206 mejores leads, vale 5 minutos revisar el CSV y reemplazar "Trabajo interesante" por algo específico de la empresa si aparece en la columna `company`.

**Asunto que mejor convierte en Chile según datos de Brevo 2024:** preguntas directas > afirmaciones > nombres propios. Probar versión B en el TEST batch primero.

**Precio en email:** $600 USD elimina leads sin presupuesto antes de gastar tiempo en una llamada. Si la tasa de respuesta es muy baja, mover el precio al email 3 y probar sin precio en email 1.
