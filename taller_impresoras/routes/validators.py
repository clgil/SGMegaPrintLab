"""
Validadores de seguridad para el Sistema de Gestión de Taller de Impresoras
"""
import re


class PasswordValidator:
    """Validador de contraseñas con requisitos de seguridad OWASP"""
    
    # Requisitos de contraseña
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL = False  # Opcional: caracteres especiales
    
    @staticmethod
    def validar(password: str) -> tuple[bool, str]:
        """
        Valida que una contraseña cumpla con los requisitos de seguridad.
        
        Args:
            password: Contraseña a validar
            
        Returns:
            tuple: (es_válida, mensaje)
            
        Ejemplos:
            >>> PasswordValidator.validar('Abc123456')
            (True, 'Contraseña válida')
            
            >>> PasswordValidator.validar('weak')
            (False, 'La contraseña debe tener al menos 8 caracteres')
        """
        
        if not password:
            return False, "La contraseña es obligatoria"
        
        # Verificar longitud mínima
        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, f"La contraseña debe tener al menos {PasswordValidator.MIN_LENGTH} caracteres (actual: {len(password)})"
        
        # Verificar longitud máxima (prevenir buffer overflow)
        if len(password) > 128:
            return False, "La contraseña no puede tener más de 128 caracteres"
        
        # Verificar mayúsculas
        if PasswordValidator.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            return False, "La contraseña debe contener al menos una letra mayúscula (A-Z)"
        
        # Verificar minúsculas
        if PasswordValidator.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            return False, "La contraseña debe contener al menos una letra minúscula (a-z)"
        
        # Verificar números
        if PasswordValidator.REQUIRE_NUMBERS and not re.search(r'[0-9]', password):
            return False, "La contraseña debe contener al menos un número (0-9)"
        
        # Verificar caracteres especiales (opcional)
        if PasswordValidator.REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "La contraseña debe contener al menos un carácter especial (!@#$%^&*...)"
        
        return True, "Contraseña válida"
    
    @staticmethod
    def get_requirements() -> dict:
        """
        Retorna los requisitos de contraseña para mostrar en UI.
        
        Returns:
            dict: Diccionario con requisitos
        """
        return {
            'min_length': PasswordValidator.MIN_LENGTH,
            'require_uppercase': PasswordValidator.REQUIRE_UPPERCASE,
            'require_lowercase': PasswordValidator.REQUIRE_LOWERCASE,
            'require_numbers': PasswordValidator.REQUIRE_NUMBERS,
            'require_special': PasswordValidator.REQUIRE_SPECIAL,
            'description': f"""La contraseña debe contener:
                - Mínimo {PasswordValidator.MIN_LENGTH} caracteres
                - Al menos una letra mayúscula (A-Z)
                - Al menos una letra minúscula (a-z)
                - Al menos un número (0-9)
            """
        }


class UsernameValidator:
    """Validador para nombres de usuario"""
    
    MIN_LENGTH = 3
    MAX_LENGTH = 32
    ALLOWED_CHARS = re.compile(r'^[a-zA-Z0-9_.-]+$')
    
    @staticmethod
    def validar(username: str) -> tuple[bool, str]:
        """
        Valida que un nombre de usuario sea válido.
        
        Args:
            username: Nombre de usuario a validar
            
        Returns:
            tuple: (es_válido, mensaje)
        """
        
        if not username:
            return False, "El nombre de usuario es obligatorio"
        
        if len(username) < UsernameValidator.MIN_LENGTH:
            return False, f"El nombre de usuario debe tener al menos {UsernameValidator.MIN_LENGTH} caracteres"
        
        if len(username) > UsernameValidator.MAX_LENGTH:
            return False, f"El nombre de usuario no puede tener más de {UsernameValidator.MAX_LENGTH} caracteres"
        
        if not UsernameValidator.ALLOWED_CHARS.match(username):
            return False, "El nombre de usuario solo puede contener letras, números, puntos, guiones y guiones bajos"
        
        # No permitir que comience o termine con punto o guion
        if username[0] in '.-' or username[-1] in '.-':
            return False, "El nombre de usuario no puede comenzar ni terminar con punto o guion"
        
        return True, "Nombre de usuario válido"


class EmailValidator:
    """Validador básico para emails"""
    
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    @staticmethod
    def validar(email: str) -> tuple[bool, str]:
        """
        Valida que un email tenga formato válido.
        
        Args:
            email: Email a validar
            
        Returns:
            tuple: (es_válido, mensaje)
        """
        
        if not email:
            return True, "Email no requerido"  # Email es opcional
        
        if len(email) > 254:
            return False, "El email no puede tener más de 254 caracteres"
        
        if not EmailValidator.EMAIL_PATTERN.match(email):
            return False, "El formato del email no es válido"
        
        return True, "Email válido"
