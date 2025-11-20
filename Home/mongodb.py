from pymongo import MongoClient
from django.conf import settings
from bson import ObjectId
from datetime import datetime

# Conexión global a MongoDB
client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_NAME]

# Colecciones
productos_collection = db['Productos']
ventas_collection = db['ventas']
carrito_collection = db['carrito']
comentarios_collection = db['comentarios']
auditoria_collection = db['auditoria']  # ✅ NUEVA COLECCIÓN


def get_db():
    """Retorna la instancia de la base de datos"""
    return db


def get_collection(name):
    """Retorna una colección específica"""
    return db[name]


def str_to_objectid(id_str):
    """Convierte string a ObjectId"""
    try:
        return ObjectId(id_str)
    except:
        return None


def objectid_to_str(obj_id):
    """Convierte ObjectId a string"""
    return str(obj_id) if obj_id else None


# ==========================================
# 📋 FUNCIÓN DE AUDITORÍA
# ==========================================

def registrar_auditoria(accion, usuario_email, detalle, datos_adicionales=None):
    """
    Registra una acción en la colección de auditoría
    
    Args:
        accion (str): Tipo de acción (LOGIN, CREAR_VENTA, etc.)
        usuario_email (str): Email del usuario que realizó la acción
        detalle (str): Descripción detallada de la acción
        datos_adicionales (dict): Datos extra relevantes a la acción
    
    Returns:
        bool: True si se registró correctamente, False si hubo error
    """
    try:
        registro = {
            'accion': accion,
            'usuario_responsable': usuario_email,
            'detalle': detalle,
            'fecha_hora': datetime.now(),
            'datos_adicionales': datos_adicionales or {}
        }
        
        resultado = auditoria_collection.insert_one(registro)
        print(f"✅ Auditoría registrada: {accion} - {usuario_email}")
        return True
    
    except Exception as e:
        print(f"❌ Error al registrar auditoría: {e}")
        return False


# ==========================================
# 🔍 FUNCIONES DE CONSULTA (OPCIONAL)
# ==========================================

def obtener_registros_auditoria(filtros=None, limite=100):
    """
    Obtiene registros de auditoría con filtros opcionales
    
    Args:
        filtros (dict): Filtros de búsqueda
        limite (int): Cantidad máxima de registros a retornar
    
    Returns:
        list: Lista de registros de auditoría
    """
    try:
        if filtros:
            registros = auditoria_collection.find(filtros).sort('fecha_hora', -1).limit(limite)
        else:
            registros = auditoria_collection.find().sort('fecha_hora', -1).limit(limite)
        
        return list(registros)
    
    except Exception as e:
        print(f"❌ Error al obtener registros: {e}")
        return []


def contar_registros_auditoria(filtros=None):
    """
    Cuenta los registros de auditoría
    
    Args:
        filtros (dict): Filtros de búsqueda
    
    Returns:
        int: Cantidad de registros
    """
    try:
        if filtros:
            return auditoria_collection.count_documents(filtros)
        else:
            return auditoria_collection.count_documents({})
    
    except Exception as e:
        print(f"❌ Error al contar registros: {e}")
        return 0


def obtener_top_acciones(filtros=None, limite=5):
    """
    Obtiene las acciones más frecuentes
    
    Args:
        filtros (dict): Filtros de búsqueda
        limite (int): Cantidad de acciones a retornar
    
    Returns:
        list: Lista de acciones con su cantidad
    """
    try:
        pipeline = []
        
        if filtros:
            pipeline.append({'$match': filtros})
        
        pipeline.extend([
            {'$group': {'_id': '$accion', 'cantidad': {'$sum': 1}}},
            {'$sort': {'cantidad': -1}},
            {'$limit': limite}
        ])
        
        return list(auditoria_collection.aggregate(pipeline))
    
    except Exception as e:
        print(f"❌ Error al obtener top acciones: {e}")
        return []