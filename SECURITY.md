# 🔒 Guía de Seguridad - SGMegaPrintLab

## Información Importante de Seguridad

Este documento describe las características de seguridad implementadas en SGMegaPrintLab y mejores prácticas para su uso.

---

## 📋 Tabla de Contenidos

1. [Configuración Inicial](#configuración-inicial)
2. [Gestión de Contraseñas](#gestión-de-contraseñas)
3. [Variables de Entorno](#variables-de-entorno)
4. [Control de Acceso](#control-de-acceso)
5. [Encriptación y Hashing](#encriptación-y-hashing)
6. [Validación de Entrada](#validación-de-entrada)
7. [Prácticas Recomendadas](#prácticas-recomendadas)
8. [Reporte de Vulnerabilidades](#reporte-de-vulnerabilidades)

---

## 🚀 Configuración Inicial

### Primera Vez que se Ejecuta

Al ejecutar por primera vez, el sistema crea un usuario administrador por defecto:

```
Usuario: admin
Contraseña: Taller2026
```

⚠️ **ACCIÓN OBLIGATORIA:**

1. Inicie sesión con estas credenciales
2. **Inmediatamente** vaya a "Cambiar Clave" en el menú
3. Cambie la contraseña a una contraseña fuerte
4. **Nunca** comparta estas credenciales por defecto

---

## 🔐 Gestión de Contraseñas

### Requisitos de Contraseña Fuerte

Todas las contraseñas deben cumplir:

✅ **Mínimo 8 caracteres**
✅ **Incluir mayúsculas** (A-Z)
✅ **Incluir minúsculas** (a-z)
✅ **Incluir números** (0-9)

### Ejemplos de Contraseñas Válidas

```
✓ Admin2024Lab
✓ Taller@Seguro123
✓ MiContraseña2024
```

### Ejemplos de Contraseñas Inválidas

```
✗ 1234567890    (solo números)
✗ password      (solo minúsculas)
✗ PASSWORD      (solo mayúsculas)
✗ Abc123        (7 caracteres)
```

### Cambiar Contraseña

1. Inicie sesión
2. Haga clic en "Cambiar Clave" en el menú lateral
3. Ingrese su contraseña actual
4. Ingrese la nueva contraseña (debe cumplir requisitos)
5. Confirme la nueva contraseña
6. Haga clic en "Guardar"

---

## 🔑 Variables de Entorno

### Configuración de la Clave Secreta

La clave secreta protege las sesiones y tokens CSRF. Es crítico que sea segura.

### Generar una Clave Segura

```bash
# En Linux/Mac
python3 -c "import secrets; print(secrets.token_hex(32))"

# En Windows PowerShell
python -c "import secrets; print(secrets.token_hex(32))"
```

Esto generará algo como: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6`

### Configurar la Clave

#### Método 1: Archivo .env (Recomendado para Desarrollo)

1. Copie `.env.example` a `.env`
2. Edite `.env` y cambie `SECRET_KEY`:

```bash
cp .env.example .env
# Editar .env con su editor favorito
```

```ini
# .env
SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
FLASK_ENV=production
FLASK_DEBUG=False
```

#### Método 2: Variables de Entorno del Sistema (Recomendado para Producción)

```bash
# Linux/Mac
export SECRET_KEY="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6"
export FLASK_ENV=production
export FLASK_DEBUG=False

# Luego ejecutar
python app.py
```

⚠️ **NUNCA** commit el archivo `.env` real a Git. El `.gitignore` lo protege.

---

## 👥 Control de Acceso

### Roles del Sistema

| Rol | Permisos | Acceso a |
|-----|----------|----------|
| **Administrador** | Control total | Dashboard completo, Usuarios, Configuración |
| **Técnico** | Órdenes y reparaciones | Órdenes, Inventario, Dispositivos |
| **Proveedor** | Gestión de inventario | Solo inventario de piezas |
| **Cliente** | Consulta personal | Solo sus órdenes y dispositivos |

### Restricciones de API

Las APIs internas están protegidas por rol:

```
/api/piezas → Admin, Técnico, Proveedor
/api/clientes/{id}/dispositivos → Admin, Técnico
/api/ordenes/* → Admin, Técnico
```

Los clientes **no pueden** acceder a estas APIs.

---

## 🔒 Encriptación y Hashing

### Almacenamiento de Contraseñas

- ✅ Las contraseñas se almacenan con **bcrypt** (no en texto plano)
- ✅ Cada contraseña tiene un **salt único**
- ✅ Las contraseñas no se pueden recuperar (solo resetear)

### Sesiones

- ✅ Las sesiones están protegidas con la `SECRET_KEY`
- ✅ Las cookies de sesión son **HttpOnly** (JavaScript no puede acceder)
- ✅ Las cookies de sesión tienen flag **Secure** en producción

---

## ✔️ Validación de Entrada

### Validaciones Implementadas

#### Contraseñas
- ✅ Longitud mínima y máxima
- ✅ Complejidad (mayúsculas, minúsculas, números)
- ✅ No reutilización de contraseña anterior

#### Nombres de Usuario
- ✅ Caracteres permitidos: letras, números, puntos, guiones
- ✅ Longitud: 3-32 caracteres
- ✅ No duplicados

#### Emails
- ✅ Formato válido
- ✅ Longitud máxima: 254 caracteres

#### Números (Cantidad, Precios)
- ✅ Deben ser positivos
- ✅ Validación en cliente y servidor
- ✅ Prevención de valores inválidos

---

## 📋 Prácticas Recomendadas

### 1. Cambiar Contraseña Regularmente

```
Recomendación: Cada 90 días
```

Especialmente después de:
- Cambios de personal
- Cambios de administrador
- Acceso no autorizado sospechoso

### 2. Usar Contraseñas Únicas por Usuario

❌ **NO HAGAS**
```
Todos usan: admin / Taller2026
```

✅ **HAZLO**
```
Cada técnico tiene su usuario y contraseña única
Juan: juan.perez / MiContraseña123
María: maria.garcia / OtraContraseña456
```

### 3. Monitorear Acceso

- Revisa regularmente quién tiene acceso al sistema
- Desactiva usuarios que se hayan ido
- Cambia contraseñas si se sospecha compromiso

### 4. Respaldar Regularmente

```
Frequencia: Diaria
Ubicación: USB externa en lugar seguro
Retención: Al menos 30 días
```

### 5. Mantener Actualizado

```bash
# Instalar actualizaciones
pip install --upgrade -r requirements.txt
```

---

## 🆘 Reporte de Vulnerabilidades

### Encontré una Vulnerabilidad de Seguridad

**NO** la publiques en GitHub Issues. En su lugar:

1. **No divulgues** la vulnerabilidad públicamente
2. **Contacta** al desarrollador en privado
3. **Describe** la vulnerabilidad detalladamente
4. **Espera** a que se corrija antes de publicar

### Información de Contacto

```
Email: clgil89@gmail.com
Asunto: [SEGURIDAD] Vulnerabilidad en SGMegaPrintLab
```

---

## 📚 Más Información

### OWASP Top 10

Este proyecto implementa defensas contra:

- A02 - Broken Authentication → Validación de contraseña fuerte
- A03 - Injection → Validación de entrada, SQLAlchemy ORM
- A04 - Insecure Design → Control de acceso por rol
- A05 - Security Misconfiguration → Variables de entorno
- A07 - Identification and Authentication Failures → Bcrypt hashing

### Lecturas Recomendadas

- [OWASP Security Guidelines](https://owasp.org/www-project-web-security-testing-guide/)
- [Flask Security Documentation](https://flask-login.readthedocs.io/)
- [Bcrypt Security](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

---

## 📝 Changelog de Seguridad

### v1.1.0 - Mejoras de Seguridad

✅ Eliminadas credenciales hardcodeadas de login.html
✅ SECRET_KEY ahora se carga desde variables de entorno
✅ Validación de contraseña fuerte (8 caracteres, mayúsculas, minúsculas, números)
✅ Añadido .env.example para configuración segura
✅ Mensajes de error diferenciados en login
✅ APIs protegidas por rol
✅ Validación de entrada mejorada
✅ Confirmaciones para acciones destructivas

---

## ⚖️ Disclaimer

Este sistema fue desarrollado con prácticas de seguridad razonables, pero **no hay seguridad 100%**. Se recomienda:

1. Realizar auditorías de seguridad regulares
2. Mantener el sistema y dependencias actualizadas
3. Monitorear accesos y cambios
4. Tener planes de respuesta ante incidentes
5. Hacer backups regulares

---

**Última actualización:** Julio 2026
**Versión:** 1.1.0
