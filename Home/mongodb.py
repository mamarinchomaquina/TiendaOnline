# Home/mongodb.py

from pymongo import MongoClient
from django.conf import settings
from bson import ObjectId
from datetime import datetime

# ==========================================
# 🔗 CONEXIÓN GLOBAL A MONGODB
# ==========================================
client = MongoClient(settings.MONGODB_URI)
db = client[settings.MONGODB_NAME]

# ==========================================
# 📦 COLECCIONES
# ==========================================
productos_collection = db['Productos']
ventas_collection = db['ventas']
carrito_collection = db['carrito']
comentarios_collection = db['comentarios']
auditoria_collection = db['auditoria']
usuarios_collection = db['usuarios']  # ✅ NUEVA COLECCIÓN PARA AVATARES


# ==========================================
# 🛠️ FUNCIONES BÁSICAS
# ==========================================

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
        accion (str): Tipo de acción (LOGIN, CREAR_VENTA, CREAR_PRODUCTO, etc.)
        usuario_email (str): Email del usuario que realizó la acción
        detalle (str): Descripción detallada de la acción
        datos_adicionales (dict): Datos extra relevantes a la acción
    
    Returns:
        bool: True si se registró correctamente, False si hubo error
    
    Ejemplos de acciones:
        - LOGIN
        - LOGOUT
        - REGISTRO
        - CREAR_PRODUCTO
        - ACTUALIZAR_PRODUCTO
        - ELIMINAR_PRODUCTO
        - CREAR_VENTA
        - AGREGAR_CARRITO
        - REMOVER_CARRITO
        - VACIAR_CARRITO
        - CREAR_COMENTARIO
        - ACTUALIZAR_PERFIL
        - ACTUALIZAR_AVATAR
        - ACTUALIZAR_STOCK
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
# 🔍 FUNCIONES DE CONSULTA DE AUDITORÍA
# ==========================================

def obtener_registros_auditoria(filtros=None, limite=100):
    """
    Obtiene registros de auditoría con filtros opcionales
    
    Args:
        filtros (dict): Filtros de búsqueda (ej: {'accion': 'LOGIN'})
        limite (int): Cantidad máxima de registros a retornar
    
    Returns:
        list: Lista de registros de auditoría ordenados por fecha descendente
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
        int: Cantidad de registros que coinciden con los filtros
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
    Obtiene las acciones más frecuentes usando aggregation
    
    Args:
        filtros (dict): Filtros de búsqueda
        limite (int): Cantidad de acciones a retornar
    
    Returns:
        list: Lista de diccionarios con formato [{'_id': 'LOGIN', 'cantidad': 45}, ...]
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


# ==========================================
# 👤 FUNCIONES DE USUARIOS (AVATARES)
# ==========================================

def guardar_avatar_usuario(usuario_id, email, avatar_data, content_type='image/jpeg'):
    """
    Guarda o actualiza el avatar de un usuario en MongoDB
    
    Args:
        usuario_id (int): ID del usuario de Django
        email (str): Email del usuario
        avatar_data (str): Imagen en formato Base64
        content_type (str): Tipo MIME de la imagen
    
    Returns:
        bool: True si se guardó correctamente, False si hubo error
    """
    try:
        usuarios_collection.update_one(
            {'usuario_id': usuario_id},
            {
                '$set': {
                    'email': email,
                    'avatar': {
                        'data': avatar_data,
                        'content_type': content_type
                    },
                    'avatar_actualizado': datetime.now()
                }
            },
            upsert=True  # Crear si no existe
        )
        print(f"✅ Avatar guardado para usuario {email}")
        return True
    
    except Exception as e:
        print(f"❌ Error al guardar avatar: {e}")
        return False


def obtener_avatar_usuario(usuario_id):
    """
    Obtiene el avatar de un usuario desde MongoDB
    
    Args:
        usuario_id (int): ID del usuario de Django
    
    Returns:
        dict: Documento del usuario con avatar o None si no existe
    """
    try:
        return usuarios_collection.find_one({'usuario_id': usuario_id})
    
    except Exception as e:
        print(f"❌ Error al obtener avatar: {e}")
        return None


def eliminar_avatar_usuario(usuario_id):
    """
    Elimina el avatar de un usuario
    
    Args:
        usuario_id (int): ID del usuario de Django
    
    Returns:
        bool: True si se eliminó correctamente, False si hubo error
    """
    try:
        usuarios_collection.update_one(
            {'usuario_id': usuario_id},
            {
                '$unset': {'avatar': ''},
                '$set': {'avatar_actualizado': datetime.now()}
            }
        )
        print(f"✅ Avatar eliminado para usuario ID {usuario_id}")
        return True
    
    except Exception as e:
        print(f"❌ Error al eliminar avatar: {e}")
        return False


# ==========================================
# 📦 FUNCIONES DE PRODUCTOS
# ==========================================

def obtener_total_productos():
    """Retorna el total de productos activos"""
    try:
        return productos_collection.count_documents({'activo': True})
    except Exception as e:
        print(f"❌ Error al contar productos: {e}")
        return 0


def obtener_producto_por_id(producto_id):
    """
    Obtiene un producto por su ID
    
    Args:
        producto_id (str): ID del producto (string)
    
    Returns:
        dict: Documento del producto o None si no existe
    """
    try:
        return productos_collection.find_one({'_id': ObjectId(producto_id)})
    except Exception as e:
        print(f"❌ Error al obtener producto: {e}")
        return None


def actualizar_stock_producto(producto_id, cantidad):
    """
    Actualiza el stock de un producto
    
    Args:
        producto_id (str): ID del producto
        cantidad (int): Cantidad a incrementar (negativo para reducir)
    
    Returns:
        bool: True si se actualizó correctamente
    """
    try:
        productos_collection.update_one(
            {'_id': ObjectId(producto_id)},
            {'$inc': {'stock': cantidad}}
        )
        return True
    except Exception as e:
        print(f"❌ Error al actualizar stock: {e}")
        return False


# ==========================================
# 💰 FUNCIONES DE VENTAS
# ==========================================

def obtener_total_ventas():
    """Retorna el total de ventas"""
    try:
        return ventas_collection.count_documents({})
    except Exception as e:
        print(f"❌ Error al contar ventas: {e}")
        return 0


def obtener_ingresos_totales():
    """Retorna los ingresos totales usando aggregation"""
    try:
        pipeline = [
            {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
        ]
        resultado = list(ventas_collection.aggregate(pipeline))
        return resultado[0]['total'] if resultado else 0
    except Exception as e:
        print(f"❌ Error al calcular ingresos: {e}")
        return 0


def obtener_ventas_por_usuario(usuario_id):
    """
    Obtiene todas las ventas de un usuario
    
    Args:
        usuario_id (int): ID del usuario de Django
    
    Returns:
        list: Lista de ventas del usuario
    """
    try:
        return list(ventas_collection.find(
            {'usuario_id': usuario_id}
        ).sort('fecha_venta', -1))
    except Exception as e:
        print(f"❌ Error al obtener ventas del usuario: {e}")
        return []


# ==========================================
# 🛒 FUNCIONES DE CARRITO
# ==========================================

def obtener_carrito_usuario(usuario_id):
    """
    Obtiene el carrito de un usuario
    
    Args:
        usuario_id (int): ID del usuario de Django
    
    Returns:
        dict: Documento del carrito o None si no existe
    """
    try:
        return carrito_collection.find_one({'usuario_id': usuario_id})
    except Exception as e:
        print(f"❌ Error al obtener carrito: {e}")
        return None


def crear_carrito_usuario(usuario_id):
    """
    Crea un carrito vacío para un usuario
    
    Args:
        usuario_id (int): ID del usuario de Django
    
    Returns:
        dict: Documento del carrito creado
    """
    try:
        carrito = {
            'usuario_id': usuario_id,
            'productos': [],
            'fecha_creacion': datetime.now(),
            'fecha_actualizacion': datetime.now()
        }
        carrito_collection.insert_one(carrito)
        return carrito
    except Exception as e:
        print(f"❌ Error al crear carrito: {e}")
        return None


# ==========================================
# 📊 FUNCIONES DE ESTADÍSTICAS
# ==========================================

def obtener_productos_mas_vendidos(limite=5):
    """
    Obtiene los productos más vendidos usando aggregation
    
    Args:
        limite (int): Cantidad de productos a retornar
    
    Returns:
        list: Lista de productos con cantidad vendida
    """
    try:
        pipeline = [
            {'$unwind': '$productos'},
            {
                '$group': {
                    '_id': '$productos.nombre',
                    'total_vendido': {'$sum': '$productos.cantidad'},
                    'ingresos': {'$sum': '$productos.subtotal'}
                }
            },
            {'$sort': {'total_vendido': -1}},
            {'$limit': limite}
        ]
        
        return list(ventas_collection.aggregate(pipeline))
    
    except Exception as e:
        print(f"❌ Error al obtener productos más vendidos: {e}")
        return []


def obtener_ventas_por_periodo(fecha_inicio, fecha_fin):
    """
    Obtiene ventas dentro de un periodo de tiempo
    
    Args:
        fecha_inicio (datetime): Fecha de inicio
        fecha_fin (datetime): Fecha de fin
    
    Returns:
        list: Lista de ventas en el periodo
    """
    try:
        return list(ventas_collection.find({
            'fecha_venta': {
                '$gte': fecha_inicio,
                '$lte': fecha_fin
            }
        }).sort('fecha_venta', -1))
    
    except Exception as e:
        print(f"❌ Error al obtener ventas por periodo: {e}")
        return []


# ==========================================
# 🧹 FUNCIONES DE MANTENIMIENTO
# ==========================================

def limpiar_carritos_vacios():
    """
    Elimina carritos que no tienen productos
    
    Returns:
        int: Cantidad de carritos eliminados
    """
    try:
        resultado = carrito_collection.delete_many({'productos': []})
        print(f"✅ {resultado.deleted_count} carritos vacíos eliminados")
        return resultado.deleted_count
    except Exception as e:
        print(f"❌ Error al limpiar carritos: {e}")
        return 0


def obtener_productos_sin_stock():
    """
    Obtiene productos sin stock o con stock bajo
    
    Returns:
        dict: Diccionario con productos críticos y bajos
    """
    try:
        criticos = list(productos_collection.find({
            'activo': True,
            'stock': {'$lte': 2}
        }))
        
        bajos = list(productos_collection.find({
            'activo': True,
            'stock': {'$gte': 3, '$lte': 5}
        }))
        
        return {
            'criticos': criticos,
            'bajos': bajos
        }
    
    except Exception as e:
        print(f"❌ Error al obtener productos sin stock: {e}")
        return {'criticos': [], 'bajos': []}


# ==========================================
# 🔧 FUNCIONES DE DEBUG
# ==========================================

def verificar_conexion():
    """
    Verifica si la conexión a MongoDB está activa
    
    Returns:
        bool: True si la conexión es exitosa
    """
    try:
        client.admin.command('ping')
        print("✅ Conexión a MongoDB exitosa")
        return True
    except Exception as e:
        print(f"❌ Error de conexión a MongoDB: {e}")
        return False


def listar_colecciones():
    """
    Lista todas las colecciones en la base de datos
    
    Returns:
        list: Lista de nombres de colecciones
    """
    try:
        return db.list_collection_names()
    except Exception as e:
        print(f"❌ Error al listar colecciones: {e}")
        return []


def obtener_estadisticas_db():
    """
    Obtiene estadísticas generales de la base de datos
    
    Returns:
        dict: Diccionario con estadísticas
    """
    try:
        return {
            'total_productos': productos_collection.count_documents({}),
            'productos_activos': productos_collection.count_documents({'activo': True}),
            'total_ventas': ventas_collection.count_documents({}),
            'total_carritos': carrito_collection.count_documents({}),
            'total_usuarios': usuarios_collection.count_documents({}),
            'total_auditoria': auditoria_collection.count_documents({}),
        }
    except Exception as e:
        print(f"❌ Error al obtener estadísticas: {e}")
        return {}


# ==========================================
# 🎯 EJEMPLOS DE USO
# ==========================================

"""
# Ejemplo 1: Registrar auditoría
registrar_auditoria(
    accion='CREAR_PRODUCTO',
    usuario_email='admin@example.com',
    detalle='Producto "Laptop HP" creado con precio $899',
    datos_adicionales={
        'producto_id': '123abc',
        'precio': 899,
        'stock': 10
    }
)

# Ejemplo 2: Guardar avatar
guardar_avatar_usuario(
    usuario_id=1,
    email='user@example.com',
    avatar_data='base64_string_here',
    content_type='image/jpeg'
)

# Ejemplo 3: Obtener productos más vendidos
productos_top = obtener_productos_mas_vendidos(limite=10)

# Ejemplo 4: Verificar conexión
if verificar_conexion():
    print("MongoDB está listo")

# Ejemplo 5: Obtener estadísticas
stats = obtener_estadisticas_db()
print(f"Total productos: {stats['total_productos']}")
"""