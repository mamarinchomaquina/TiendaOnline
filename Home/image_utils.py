# Home/image_utils.py

import base64
from io import BytesIO
from PIL import Image

def image_to_base64(image_file, max_size=(800, 800), quality=85):
    """
    Convierte una imagen a base64 optimizado
    
    Args:
        image_file: Archivo de imagen de Django
        max_size: Tupla (ancho, alto) máximo
        quality: Calidad de compresión (1-100)
        
    Returns:
        dict: {'data': base64_string, 'content_type': 'image/jpeg'}
    """
    try:
        # Abrir imagen con Pillow
        img = Image.open(image_file)
        
        # Convertir a RGB si es necesario (para PNGs con transparencia)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Redimensionar si es muy grande
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Convertir a bytes
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)
        
        # Convertir a base64
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        
        return {
            'data': image_base64,
            'content_type': 'image/jpeg'
        }
    except Exception as e:
        print(f"❌ Error al convertir imagen: {e}")
        return None


def base64_to_image_data_uri(base64_string, content_type='image/jpeg'):
    """
    Convierte base64 a Data URI para usar en HTML
    
    Args:
        base64_string: String base64 de la imagen
        content_type: Tipo MIME de la imagen
        
    Returns:
        str: Data URI completa (data:image/jpeg;base64,...)
    """
    return f"data:{content_type};base64,{base64_string}"


def get_default_avatar_base64():
    """
    Retorna un avatar por defecto en base64
    """
    # Avatar por defecto (un círculo azul simple)
    default_svg = '''<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="100" r="80" fill="#2563eb"/>
        <text x="100" y="120" font-size="80" fill="white" text-anchor="middle" font-family="Arial">?</text>
    </svg>'''
    
    svg_base64 = base64.b64encode(default_svg.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{svg_base64}"


def get_default_product_image_base64():
    """
    Retorna una imagen por defecto para productos en base64
    """
    default_svg = '''<svg width="400" height="400" xmlns="http://www.w3.org/2000/svg">
        <rect width="400" height="400" fill="#f3f4f6"/>
        <text x="200" y="200" font-size="40" fill="#9ca3af" text-anchor="middle" font-family="Arial">Sin Imagen</text>
        <text x="200" y="250" font-size="60" fill="#d1d5db" text-anchor="middle" font-family="Arial">📦</text>
    </svg>'''
    
    svg_base64 = base64.b64encode(default_svg.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{svg_base64}"