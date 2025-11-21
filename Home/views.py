# Home/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from .models import Usuario, Producto, Comentario
from .forms import RegisterForm, ProductoForm, PerfilForm
from .mongodb import (
    productos_collection, 
    ventas_collection, 
    carrito_collection,
    auditoria_collection,
    usuarios_collection,
    registrar_auditoria,
    str_to_objectid,
    objectid_to_str
)
from bson import ObjectId
from datetime import datetime, timedelta
from .utils import generar_factura_pdf, generar_reporte_ventas_pdf

# ==========================================
# 🎨 IMPORTAR UTILIDADES DE IMÁGENES
# ==========================================
from .image_utils import (
    image_to_base64,
    base64_to_image_data_uri,
    get_default_avatar_base64,
    get_default_product_image_base64
)


# ==========================================
# 🏠 VISTAS PRINCIPALES
# ==========================================

def index(request):
    """Vista principal - Dashboard para admin, página simple para clientes"""
    
    # Si NO está autenticado, mostrar hero section
    if not request.user.is_authenticated:
        return render(request, 'index.html', {'usuario': None})
    
    # ========== SI ES ADMIN: DASHBOARD COMPLETO ==========
    if request.user.is_staff:
        # Comentarios recientes
        comentarios_recientes = Comentario.objects.select_related('usuario').filter(
            estado='activo'
        ).order_by('-fecha')[:6]
        
        # Estadísticas de productos
        productos = list(productos_collection.find({'activo': True}))
        total_productos = len(productos)
        
        # Convertir ObjectId a string
        for producto in productos:
            producto['id'] = str(producto['_id'])
        
        # Clasificar productos por stock
        stock_critico = [p for p in productos if p.get('stock', 0) <= 2]
        stock_bajo = [p for p in productos if 3 <= p.get('stock', 0) <= 5]
        stock_bueno = [p for p in productos if p.get('stock', 0) > 5]
        
        # ========== COMPARADOR DE INGRESOS ==========
        ahora = datetime.now()
        fecha_inicio_mes_actual = ahora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Mes anterior
        primer_dia_mes_actual = ahora.replace(day=1)
        ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
        fecha_inicio_mes_anterior = ultimo_dia_mes_anterior.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        fecha_fin_mes_anterior = ultimo_dia_mes_anterior.replace(hour=23, minute=59, second=59)
        
        # Ingresos mes actual
        pipeline_mes_actual = [
            {'$match': {'fecha_venta': {'$gte': fecha_inicio_mes_actual}}},
            {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
        ]
        resultado_mes_actual = list(ventas_collection.aggregate(pipeline_mes_actual))
        ingresos_mes_actual = resultado_mes_actual[0]['total'] if resultado_mes_actual else 0
        
        # Ventas mes actual
        ventas_mes_actual = ventas_collection.count_documents({
            'fecha_venta': {'$gte': fecha_inicio_mes_actual}
        })
        
        # Ingresos mes anterior
        pipeline_mes_anterior = [
            {'$match': {
                'fecha_venta': {
                    '$gte': fecha_inicio_mes_anterior,
                    '$lte': fecha_fin_mes_anterior
                }
            }},
            {'$group': {'_id': None, 'total': {'$sum': '$total'}}}
        ]
        resultado_mes_anterior = list(ventas_collection.aggregate(pipeline_mes_anterior))
        ingresos_mes_anterior = resultado_mes_anterior[0]['total'] if resultado_mes_anterior else 0
        
        # Ventas mes anterior
        ventas_mes_anterior = ventas_collection.count_documents({
            'fecha_venta': {
                '$gte': fecha_inicio_mes_anterior,
                '$lte': fecha_fin_mes_anterior
            }
        })
        
        # Calcular porcentaje de crecimiento
        if ingresos_mes_anterior > 0:
            crecimiento_ingresos = ((ingresos_mes_actual - ingresos_mes_anterior) / ingresos_mes_anterior) * 100
        else:
            crecimiento_ingresos = 100 if ingresos_mes_actual > 0 else 0
        
        # Calcular porcentaje de crecimiento en ventas
        if ventas_mes_anterior > 0:
            crecimiento_ventas = ((ventas_mes_actual - ventas_mes_anterior) / ventas_mes_anterior) * 100
        else:
            crecimiento_ventas = 100 if ventas_mes_actual > 0 else 0
        
        # Nombres de meses
        meses = [
            'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ]
        nombre_mes_actual = meses[ahora.month - 1]
        nombre_mes_anterior = meses[ultimo_dia_mes_anterior.month - 1]
        
        # Datos para gráfico de ventas (últimos 30 días)
        fecha_hace_30_dias = datetime.now() - timedelta(days=30)
        ventas_ultimos_30_dias = list(ventas_collection.find({
            'fecha_venta': {'$gte': fecha_hace_30_dias}
        }).sort('fecha_venta', 1))
        
        # Agrupar ventas por día
        ventas_por_dia = {}
        for i in range(30):
            fecha = (datetime.now() - timedelta(days=29-i)).strftime('%d/%m')
            ventas_por_dia[fecha] = 0
        
        for venta in ventas_ultimos_30_dias:
            fecha_key = venta['fecha_venta'].strftime('%d/%m')
            if fecha_key in ventas_por_dia:
                ventas_por_dia[fecha_key] += venta['total']
        
        labels_ventas = list(ventas_por_dia.keys())
        datos_ventas = list(ventas_por_dia.values())
        
        # Total de comentarios
        total_comentarios = Comentario.objects.filter(estado='activo').count()
        
        context = {
            'usuario': request.user.first_name,
            'usuario_info': request.user,
            'comentarios': comentarios_recientes,
            'total_productos': total_productos,
            'ventas_mes': ventas_mes_actual,
            'ingresos_mes': ingresos_mes_actual,
            'total_comentarios': total_comentarios,
            'stock_critico': stock_critico,
            'stock_bajo': stock_bajo,
            'stock_bueno': stock_bueno,
            'labels_ventas': labels_ventas,
            'datos_ventas': datos_ventas,
            'ingresos_mes_actual': ingresos_mes_actual,
            'ingresos_mes_anterior': ingresos_mes_anterior,
            'ventas_mes_actual': ventas_mes_actual,
            'ventas_mes_anterior': ventas_mes_anterior,
            'crecimiento_ingresos': crecimiento_ingresos,
            'crecimiento_ventas': crecimiento_ventas,
            'nombre_mes_actual': nombre_mes_actual,
            'nombre_mes_anterior': nombre_mes_anterior,
            'es_admin': True
        }
        
        return render(request, 'index.html', context)
    
    # ========== SI ES CLIENTE: PÁGINA SIMPLE ==========
    else:
        context = {
            'usuario': request.user.first_name,
            'usuario_info': request.user,
            'es_admin': False
        }
        return render(request, 'index.html', context)


def login_view(request):
    """Vista de login"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        email = request.POST.get('correo')
        password = request.POST.get('contraseña')
        
        try:
            usuario = Usuario.objects.get(email=email)
            user = authenticate(request, username=usuario.username, password=password)
            
            if user is not None:
                login(request, user)
                
                registrar_auditoria(
                    accion='LOGIN',
                    usuario_email=user.email,
                    detalle=f'Usuario {user.first_name} {user.last_name} inició sesión',
                    datos_adicionales={
                        'usuario_id': user.id,
                        'rol': 'admin' if user.is_staff else 'cliente'
                    }
                )
                
                messages.success(request, f'¡Bienvenido {user.first_name}! 👋')
                return redirect('index')
            else:
                messages.error(request, '❌ Correo o contraseña incorrectos')
        except Usuario.DoesNotExist:
            messages.error(request, '❌ Correo o contraseña incorrectos')
    
    return render(request, 'login.html')


def register_view(request):
    """Vista de registro"""
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            registrar_auditoria(
                accion='REGISTRO',
                usuario_email=user.email,
                detalle=f'Nuevo usuario registrado: {user.first_name} {user.last_name}',
                datos_adicionales={
                    'usuario_id': user.id,
                    'email': user.email
                }
            )
            
            messages.success(request, '✅ ¡Usuario creado correctamente! Ahora puedes iniciar sesión.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = RegisterForm()
    
    return render(request, 'register.html', {'form': form})


def logout_view(request):
    """Vista de logout"""
    registrar_auditoria(
        accion='LOGOUT',
        usuario_email=request.user.email if request.user.is_authenticated else 'Anónimo',
        detalle=f'Usuario cerró sesión',
        datos_adicionales={
            'usuario_id': request.user.id if request.user.is_authenticated else None
        }
    )
    
    logout(request)
    messages.info(request, '👋 Sesión cerrada correctamente')
    return redirect('index')


# ==========================================
# 📦 PRODUCTOS CON IMÁGENES BASE64
# ==========================================

@login_required
def agregar_producto(request):
    """Vista para agregar productos con imagen (solo admin)"""
    if not request.user.is_staff:
        messages.error(request, '❌ No tienes permiso para acceder a esta sección')
        return redirect('index')
    
    if request.method == 'POST':
        try:
            # Manejar imagen
            imagen_base64 = None
            imagen_content_type = 'image/jpeg'
            
            if 'imagen' in request.FILES:
                imagen = request.FILES['imagen']
                # Convertir a base64 (máx 800x800px, calidad 85%)
                resultado = image_to_base64(imagen, max_size=(800, 800), quality=85)
                
                if resultado:
                    imagen_base64 = resultado['data']
                    imagen_content_type = resultado['content_type']
                    print(f"✅ Imagen convertida a base64 ({len(imagen_base64)} caracteres)")
                else:
                    messages.warning(request, 'No se pudo procesar la imagen')
            
            # Crear documento del producto
            producto_data = {
                'nombre': request.POST.get('nombre'),
                'descripcion': request.POST.get('descripcion'),
                'precio': float(request.POST.get('precio')),
                'stock': int(request.POST.get('stock', 10)),
                'categoria': request.POST.get('categoria', 'General'),
                'imagen': {
                    'data': imagen_base64,
                    'content_type': imagen_content_type
                },
                'activo': True,
                'fecha_creacion': datetime.now(),
                'fecha_actualizacion': datetime.now(),
                'creado_por': request.user.email
            }
            
            resultado = productos_collection.insert_one(producto_data)
            
            registrar_auditoria(
                accion='CREAR_PRODUCTO',
                usuario_email=request.user.email,
                detalle=f'Producto "{producto_data["nombre"]}" creado con precio ${producto_data["precio"]}',
                datos_adicionales={
                    'producto_id': str(resultado.inserted_id),
                    'nombre': producto_data['nombre'],
                    'precio': producto_data['precio'],
                    'stock': producto_data['stock']
                }
            )
            
            messages.success(request, '✅ Producto agregado correctamente')
            return redirect('ver_productos')
            
        except Exception as e:
            print(f"❌ Error al agregar producto: {e}")
            messages.error(request, f'Error al agregar producto: {str(e)}')
    
    context = {
        'usuario': request.user.first_name
    }
    
    return render(request, 'agregar_producto.html', context)


@login_required
def ver_productos(request):
    """Vista del catálogo de productos - SOPORTA AMBOS FORMATOS DE IMAGEN"""
    productos = list(productos_collection.find({'activo': True}))
    
    # Convertir ObjectId y preparar imágenes
    for producto in productos:
        producto['id'] = str(producto['_id'])
        
        # ✅ MANEJAR AMBOS FORMATOS DE IMAGEN
        if producto.get('imagen'):
            # Caso 1: imagen es un diccionario con Base64 (formato nuevo)
            if isinstance(producto['imagen'], dict):
                if producto['imagen'].get('data'):
                    producto['imagen_url'] = base64_to_image_data_uri(
                        producto['imagen']['data'],
                        producto['imagen'].get('content_type', 'image/jpeg')
                    )
                else:
                    # Diccionario pero sin data
                    producto['imagen_url'] = get_default_product_image_base64()
            # Caso 2: imagen es un string con URL (formato antiguo)
            elif isinstance(producto['imagen'], str):
                producto['imagen_url'] = producto['imagen']
            else:
                # Formato desconocido
                producto['imagen_url'] = get_default_product_image_base64()
        else:
            # Sin imagen
            producto['imagen_url'] = get_default_product_image_base64()
    
    # Obtener cantidad de items en carrito
    carrito = carrito_collection.find_one({'usuario_id': request.user.id})
    carrito_items = sum(item['cantidad'] for item in carrito.get('productos', [])) if carrito else 0
    
    context = {
        'usuario': request.user.first_name,
        'productos': productos,
        'carrito_items': carrito_items
    }
    
    return render(request, 'productos.html', context)


@login_required
def comprar(request, producto_id):
    """Simular compra de producto"""
    producto = productos_collection.find_one({'_id': ObjectId(producto_id)})
    if producto:
        messages.success(request, f'🛍️ Compra de "{producto["nombre"]}" simulada correctamente')
    return redirect('ver_productos')


# ==========================================
# 💬 COMENTARIOS
# ==========================================

@login_required
def guardar_comentario(request):
    """Guardar comentario y calificación"""
    if request.method == 'POST':
        comentario_texto = request.POST.get('comentario')
        calificacion = request.POST.get('calificacion')
        
        if not comentario_texto or not calificacion:
            messages.error(request, '❌ Todos los campos son obligatorios')
            return redirect('index')
        
        try:
            comentario = Comentario.objects.create(
                usuario=request.user,
                comentario=comentario_texto,
                calificacion=int(calificacion),
                estado='activo'
            )
            
            registrar_auditoria(
                accion='CREAR_COMENTARIO',
                usuario_email=request.user.email,
                detalle=f'Comentario agregado con calificación de {calificacion} estrellas',
                datos_adicionales={
                    'comentario_id': comentario.id,
                    'calificacion': int(calificacion)
                }
            )
            
            messages.success(request, '✅ ¡Comentario agregado correctamente!')
        except Exception as e:
            messages.error(request, '❌ Error al guardar el comentario')
            print(f"Error: {e}")
    
    return redirect('index')


@login_required
def todos_comentarios(request):
    """Vista de todos los comentarios"""
    comentarios = Comentario.objects.select_related('usuario').filter(
        estado='activo'
    ).order_by('-fecha')
    
    context = {
        'usuario': request.user.first_name,
        'comentarios': comentarios
    }
    
    return render(request, 'todos_comentarios.html', context)


# ==========================================
# 👤 PERFIL CON AVATAR BASE64
# ==========================================

@login_required
def mi_cuenta(request):
    """Vista de perfil del usuario con avatar"""
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            
            registrar_auditoria(
                accion='ACTUALIZAR_PERFIL',
                usuario_email=request.user.email,
                detalle=f'Usuario actualizó su perfil',
                datos_adicionales={
                    'usuario_id': request.user.id
                }
            )
            
            messages.success(request, '✅ Datos actualizados correctamente')
            return redirect('mi_cuenta')
        else:
            messages.error(request, '❌ Error al actualizar los datos')
    else:
        form = PerfilForm(instance=request.user)
    
    # Obtener usuario de MongoDB
    try:
        usuario_mongo = usuarios_collection.find_one({'usuario_id': request.user.id})
        
        if usuario_mongo:
            # Preparar avatar
            if usuario_mongo.get('avatar') and usuario_mongo['avatar'].get('data'):
                usuario_mongo['avatar_url'] = base64_to_image_data_uri(
                    usuario_mongo['avatar']['data'],
                    usuario_mongo['avatar'].get('content_type', 'image/jpeg')
                )
            else:
                usuario_mongo['avatar_url'] = get_default_avatar_base64()
        else:
            # Crear documento de usuario en MongoDB si no existe
            usuario_mongo = {
                'usuario_id': request.user.id,
                'email': request.user.email,
                'avatar_url': get_default_avatar_base64()
            }
    except Exception as e:
        print(f"Error al obtener usuario de MongoDB: {e}")
        usuario_mongo = {
            'avatar_url': get_default_avatar_base64()
        }
    
    mis_comentarios = Comentario.objects.filter(
        usuario=request.user
    ).order_by('-fecha')
    
    context = {
        'usuario': request.user,
        'usuario_mongo': usuario_mongo,
        'form': form,
        'mis_comentarios': mis_comentarios
    }
    
    return render(request, 'mi_cuenta.html', context)


@login_required
def actualizar_avatar(request):
    """Actualizar avatar del usuario"""
    if request.method == 'POST' and 'avatar' in request.FILES:
        try:
            avatar = request.FILES['avatar']
            
            # Convertir avatar a base64 (máx 300x300px, calidad 90%)
            resultado = image_to_base64(avatar, max_size=(300, 300), quality=90)
            
            if resultado:
                # Actualizar o crear documento del usuario en MongoDB
                usuarios_collection.update_one(
                    {'usuario_id': request.user.id},
                    {
                        '$set': {
                            'email': request.user.email,
                            'avatar': {
                                'data': resultado['data'],
                                'content_type': resultado['content_type']
                            },
                            'avatar_actualizado': datetime.now()
                        }
                    },
                    upsert=True  # Crear si no existe
                )
                
                registrar_auditoria(
                    accion='ACTUALIZAR_AVATAR',
                    usuario_email=request.user.email,
                    detalle='Avatar actualizado exitosamente',
                    datos_adicionales={
                        'usuario_id': request.user.id
                    }
                )
                
                messages.success(request, '✅ Avatar actualizado exitosamente')
            else:
                messages.error(request, 'Error al procesar la imagen del avatar')
                
        except Exception as e:
            print(f"❌ Error al actualizar avatar: {e}")
            messages.error(request, f'Error al actualizar avatar: {str(e)}')
    
    return redirect('mi_cuenta')


# ==========================================
# 🛒 CARRITO
# ==========================================

@login_required
def ver_carrito(request):
    """Vista del carrito - SOPORTA AMBOS FORMATOS DE IMAGEN"""
    carrito = carrito_collection.find_one({'usuario_id': request.user.id})
    
    if not carrito:
        carrito = {
            'usuario_id': request.user.id,
            'productos': [],
            'fecha_creacion': datetime.now(),
            'fecha_actualizacion': datetime.now()
        }
        carrito_collection.insert_one(carrito)
    
    # Preparar imágenes de productos en el carrito
    for item in carrito.get('productos', []):
        # ✅ MANEJAR AMBOS FORMATOS DE IMAGEN EN CARRITO
        if item.get('imagen'):
            if isinstance(item['imagen'], dict) and item['imagen'].get('data'):
                item['imagen_url'] = base64_to_image_data_uri(
                    item['imagen']['data'],
                    item['imagen'].get('content_type', 'image/jpeg')
                )
            elif isinstance(item['imagen'], str):
                item['imagen_url'] = item['imagen']
            else:
                item['imagen_url'] = get_default_product_image_base64()
        else:
            item['imagen_url'] = get_default_product_image_base64()
    
    # Calcular totales
    subtotal = sum(item['precio'] * item['cantidad'] for item in carrito.get('productos', []))
    impuesto = subtotal * 0.16
    total = subtotal + impuesto
    cantidad_items = sum(item['cantidad'] for item in carrito.get('productos', []))
    
    context = {
        'usuario': request.user.first_name,
        'carrito': carrito,
        'subtotal': subtotal,
        'impuesto': impuesto,
        'total': total,
        'cantidad_items': cantidad_items
    }
    
    return render(request, 'carrito.html', context)


@login_required
def agregar_al_carrito(request, producto_id):
    """Agrega un producto al carrito con imagen"""
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
        
        # Buscar producto
        producto = productos_collection.find_one({'_id': ObjectId(producto_id)})
        
        if not producto:
            messages.error(request, '❌ Producto no encontrado')
            return redirect('ver_productos')
        
        # Verificar stock
        if producto.get('stock', 0) < cantidad:
            messages.error(request, f'❌ No hay suficiente stock de {producto["nombre"]}')
            return redirect('ver_productos')
        
        # Buscar o crear carrito
        carrito = carrito_collection.find_one({'usuario_id': request.user.id})
        
        if not carrito:
            carrito = {
                'usuario_id': request.user.id,
                'productos': [],
                'fecha_creacion': datetime.now(),
                'fecha_actualizacion': datetime.now()
            }
        
        # Verificar si el producto ya está en el carrito
        producto_existente = False
        for item in carrito.get('productos', []):
            if item['producto_id'] == str(producto['_id']):
                item['cantidad'] += cantidad
                producto_existente = True
                break
        
        # Si no existe, agregarlo
        if not producto_existente:
            if 'productos' not in carrito:
                carrito['productos'] = []
            
            carrito['productos'].append({
                'producto_id': str(producto['_id']),
                'nombre': producto['nombre'],
                'precio': float(producto['precio']),
                'cantidad': cantidad,
                'imagen': producto.get('imagen', {})  # Incluir imagen completa
            })
        
        carrito['fecha_actualizacion'] = datetime.now()
        
        # Actualizar o insertar
        if '_id' in carrito:
            carrito_collection.update_one(
                {'_id': carrito['_id']},
                {'$set': carrito}
            )
        else:
            carrito_collection.insert_one(carrito)
        
        registrar_auditoria(
            accion='AGREGAR_CARRITO',
            usuario_email=request.user.email,
            detalle=f'Producto "{producto["nombre"]}" agregado al carrito (cantidad: {cantidad})',
            datos_adicionales={
                'producto_id': str(producto['_id']),
                'producto_nombre': producto['nombre'],
                'cantidad': cantidad,
                'precio_unitario': producto['precio']
            }
        )
        
        messages.success(request, f'✅ {producto["nombre"]} agregado al carrito')
        return redirect('ver_carrito')
    
    return redirect('ver_productos')


@login_required
def remover_del_carrito(request, producto_id):
    """Remueve un producto del carrito"""
    carrito = carrito_collection.find_one({'usuario_id': request.user.id})
    
    if carrito:
        # Buscar el producto para registrar en auditoría
        producto_removido = next((p for p in carrito.get('productos', []) if p['producto_id'] == producto_id), None)
        
        carrito['productos'] = [
            p for p in carrito.get('productos', [])
            if p['producto_id'] != producto_id
        ]
        carrito['fecha_actualizacion'] = datetime.now()
        
        carrito_collection.update_one(
            {'_id': carrito['_id']},
            {'$set': carrito}
        )
        
        if producto_removido:
            registrar_auditoria(
                accion='REMOVER_CARRITO',
                usuario_email=request.user.email,
                detalle=f'Producto "{producto_removido["nombre"]}" removido del carrito',
                datos_adicionales={
                    'producto_id': producto_id,
                    'producto_nombre': producto_removido['nombre']
                }
            )
        
        messages.success(request, '🗑️ Producto eliminado del carrito')
    
    return redirect('ver_carrito')


@login_required
def actualizar_cantidad_carrito(request, producto_id):
    """Actualiza la cantidad de un producto en el carrito"""
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
        
        # Verificar stock
        producto = productos_collection.find_one({'_id': ObjectId(producto_id)})
        if producto and producto.get('stock', 0) < cantidad:
            return JsonResponse({
                'success': False,
                'message': f'Solo hay {producto["stock"]} unidades disponibles'
            })
        
        # Actualizar carrito
        carrito = carrito_collection.find_one({'usuario_id': request.user.id})
        
        if carrito:
            for item in carrito.get('productos', []):
                if item['producto_id'] == producto_id:
                    item['cantidad'] = cantidad
                    break
            
            carrito['fecha_actualizacion'] = datetime.now()
            
            carrito_collection.update_one(
                {'_id': carrito['_id']},
                {'$set': carrito}
            )
            
            # Calcular nuevos totales
            subtotal = sum(p['precio'] * p['cantidad'] for p in carrito['productos'])
            impuesto = subtotal * 0.16
            total = subtotal + impuesto
            
            return JsonResponse({
                'success': True,
                'subtotal': float(subtotal),
                'impuesto': float(impuesto),
                'total': float(total)
            })
    
    return JsonResponse({'success': False})


@login_required
def vaciar_carrito(request):
    """Vacía el carrito"""
    carrito_collection.update_one(
        {'usuario_id': request.user.id},
        {'$set': {
            'productos': [],
            'fecha_actualizacion': datetime.now()
        }}
    )
    
    registrar_auditoria(
        accion='VACIAR_CARRITO',
        usuario_email=request.user.email,
        detalle='Carrito vaciado completamente',
        datos_adicionales={
            'usuario_id': request.user.id
        }
    )
    
    messages.info(request, '🗑️ Carrito vaciado')
    return redirect('ver_carrito')


# ==========================================
# 💳 VENTAS
# ==========================================

def generar_numero_factura():
    """Genera un número de factura único"""
    año = datetime.now().year
    ultima_venta = ventas_collection.find_one(
        {'numero_factura': {'$regex': f'^FAC-{año}'}},
        sort=[('numero_factura', -1)]
    )
    
    if ultima_venta:
        ultimo_numero = int(ultima_venta['numero_factura'].split('-')[-1])
        nuevo_numero = ultimo_numero + 1
    else:
        nuevo_numero = 1
    
    return f'FAC-{año}-{nuevo_numero:05d}'


@login_required
def procesar_compra(request):
    """Procesa la compra y crea una venta"""
    if request.method == 'POST':
        carrito = carrito_collection.find_one({'usuario_id': request.user.id})
        
        if not carrito or not carrito.get('productos'):
            messages.error(request, '❌ El carrito está vacío')
            return redirect('ver_carrito')
        
        # Verificar stock
        for item in carrito['productos']:
            producto = productos_collection.find_one({'_id': ObjectId(item['producto_id'])})
            if producto and producto.get('stock', 0) < item['cantidad']:
                messages.error(request, f'❌ No hay suficiente stock de {producto["nombre"]}')
                return redirect('ver_carrito')
        
        # Calcular totales
        subtotal = sum(item['precio'] * item['cantidad'] for item in carrito['productos'])
        impuesto = subtotal * 0.16
        total = subtotal + impuesto
        
        # Crear venta
        venta = {
            'numero_factura': generar_numero_factura(),
            'usuario_id': request.user.id,
            'usuario_nombre': f"{request.user.first_name} {request.user.last_name}",
            'usuario_email': request.user.email,
            'productos': [
                {
                    'producto_id': item['producto_id'],
                    'nombre': item['nombre'],
                    'cantidad': item['cantidad'],
                    'precio_unitario': item['precio'],
                    'subtotal': item['precio'] * item['cantidad']
                }
                for item in carrito['productos']
            ],
            'subtotal': float(subtotal),
            'impuesto': float(impuesto),
            'total': float(total),
            'metodo_pago': request.POST.get('metodo_pago', 'Efectivo'),
            'estado': 'completada',
            'fecha_venta': datetime.now(),
            'notas': request.POST.get('notas', '')
        }
        
        # Guardar venta
        resultado = ventas_collection.insert_one(venta)
        
        registrar_auditoria(
            accion='CREAR_VENTA',
            usuario_email=request.user.email,
            detalle=f'Venta {venta["numero_factura"]} procesada por ${total:.2f} con {len(carrito["productos"])} productos',
            datos_adicionales={
                'venta_id': str(resultado.inserted_id),
                'numero_factura': venta['numero_factura'],
                'total': total,
                'metodo_pago': venta['metodo_pago'],
                'cantidad_productos': len(carrito['productos'])
            }
        )
        
        # Reducir stock
        for item in carrito['productos']:
            productos_collection.update_one(
                {'_id': ObjectId(item['producto_id'])},
                {'$inc': {'stock': -item['cantidad']}}
            )
            
            registrar_auditoria(
                accion='ACTUALIZAR_STOCK',
                usuario_email=request.user.email,
                detalle=f'Stock de "{item["nombre"]}" reducido en {item["cantidad"]} unidades',
                datos_adicionales={
                    'producto_id': item['producto_id'],
                    'producto_nombre': item['nombre'],
                    'cantidad_reducida': item['cantidad']
                }
            )
        
        # Vaciar carrito
        carrito_collection.update_one(
            {'_id': carrito['_id']},
            {'$set': {'productos': [], 'fecha_actualizacion': datetime.now()}}
        )
        
        messages.success(request, f'✅ ¡Compra realizada! Factura: {venta["numero_factura"]}')
        return redirect('ver_factura', venta_id=str(resultado.inserted_id))
    
    return redirect('ver_carrito')


@login_required
def ver_factura(request, venta_id):
    """Muestra los detalles de una factura"""
    venta = ventas_collection.find_one({'_id': ObjectId(venta_id)})
    
    if not venta:
        messages.error(request, '❌ Factura no encontrada')
        return redirect('index')
    
    # Verificar permisos
    if venta['usuario_id'] != request.user.id and not request.user.is_staff:
        messages.error(request, '❌ No tienes permiso para ver esta factura')
        return redirect('index')
    
    # Convertir ObjectId a string para usar en template
    venta['id'] = str(venta['_id'])
    
    context = {
        'usuario': request.user.first_name,
        'venta': venta
    }
    
    return render(request, 'factura.html', context)


@login_required
def mis_compras(request):
    """Muestra el historial de compras del usuario"""
    ventas = list(ventas_collection.find(
        {'usuario_id': request.user.id}
    ).sort('fecha_venta', -1))
    
    # Convertir ObjectId a string para usar en templates
    for venta in ventas:
        venta['id'] = str(venta['_id'])
    
    context = {
        'usuario': request.user.first_name,
        'ventas': ventas
    }
    
    return render(request, 'mis_compras.html', context)


@login_required
def descargar_factura_pdf(request, venta_id):
    """Descarga la factura en PDF"""
    venta = ventas_collection.find_one({'_id': ObjectId(venta_id)})
    
    if not venta:
        messages.error(request, '❌ Factura no encontrada')
        return redirect('index')
    
    # Verificar permisos
    if venta['usuario_id'] != request.user.id and not request.user.is_staff:
        messages.error(request, '❌ No tienes permiso')
        return redirect('index')
    
    # Generar PDF
    pdf_buffer = generar_factura_pdf(venta)
    
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Factura_{venta["numero_factura"]}.pdf"'
    
    return response


# ==========================================
# 📊 REPORTES (ADMIN)
# ==========================================

@login_required
def reporte_ventas(request):
    """Vista de reportes de ventas (solo admin) con aggregation pipeline"""
    if not request.user.is_staff:
        messages.error(request, '❌ No tienes permiso')
        return redirect('index')
    
    # Filtros del formulario
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    estado = request.GET.get('estado')
    metodo_pago = request.GET.get('metodo_pago')
    monto_minimo = request.GET.get('monto_minimo')
    monto_maximo = request.GET.get('monto_maximo')
    
    # Construir pipeline de aggregation
    pipeline = []
    
    # Stage 1: Match (filtros)
    match_stage = {}
    
    if fecha_inicio:
        try:
            fecha_inicio_dt = datetime.fromisoformat(fecha_inicio)
            match_stage['fecha_venta'] = {'$gte': fecha_inicio_dt}
        except:
            pass
    
    if fecha_fin:
        try:
            fecha_fin_dt = datetime.fromisoformat(fecha_fin)
            if 'fecha_venta' in match_stage:
                match_stage['fecha_venta']['$lte'] = fecha_fin_dt
            else:
                match_stage['fecha_venta'] = {'$lte': fecha_fin_dt}
        except:
            pass
    
    if estado:
        match_stage['estado'] = estado
    
    if metodo_pago:
        match_stage['metodo_pago'] = metodo_pago
    
    if monto_minimo:
        try:
            match_stage['total'] = {'$gte': float(monto_minimo)}
        except:
            pass
    
    if monto_maximo:
        try:
            if 'total' in match_stage:
                match_stage['total']['$lte'] = float(monto_maximo)
            else:
                match_stage['total'] = {'$lte': float(monto_maximo)}
        except:
            pass
    
    # Agregar match stage si hay filtros
    if match_stage:
        pipeline.append({'$match': match_stage})
    
    # Stage 2: Sort (ordenar por fecha descendente)
    pipeline.append({'$sort': {'fecha_venta': -1}})
    
    # Stage 3: Add computed fields
    pipeline.append({
        '$addFields': {
            'cantidad_productos': {'$size': '$productos'},
            'dia_semana': {'$dayOfWeek': '$fecha_venta'},
            'hora_venta': {'$hour': '$fecha_venta'}
        }
    })
    
    # Ejecutar pipeline
    ventas = list(ventas_collection.aggregate(pipeline))
    
    # Convertir ObjectId a string
    for venta in ventas:
        venta['id'] = str(venta['_id'])
    
    # ========== ESTADÍSTICAS CON AGGREGATION ==========
    
    # Pipeline para estadísticas generales
    stats_pipeline = []
    if match_stage:
        stats_pipeline.append({'$match': match_stage})
    
    stats_pipeline.extend([
        {
            '$group': {
                '_id': None,
                'total_ventas': {'$sum': 1},
                'total_ingresos': {'$sum': '$total'},
                'promedio_venta': {'$avg': '$total'},
                'venta_maxima': {'$max': '$total'},
                'venta_minima': {'$min': '$total'},
                'total_productos_vendidos': {
                    '$sum': {'$size': '$productos'}
                }
            }
        }
    ])
    
    stats_result = list(ventas_collection.aggregate(stats_pipeline))
    
    if stats_result:
        stats = stats_result[0]
        total_ventas = stats.get('total_ventas', 0)
        total_ingresos = stats.get('total_ingresos', 0)
        promedio_venta = stats.get('promedio_venta', 0)
        venta_maxima = stats.get('venta_maxima', 0)
        venta_minima = stats.get('venta_minima', 0)
        total_productos_vendidos = stats.get('total_productos_vendidos', 0)
    else:
        total_ventas = 0
        total_ingresos = 0
        promedio_venta = 0
        venta_maxima = 0
        venta_minima = 0
        total_productos_vendidos = 0
    
    # ========== VENTAS POR ESTADO ==========
    ventas_por_estado_pipeline = []
    if fecha_inicio or fecha_fin:
        match_estado = {}
        if fecha_inicio:
            match_estado['fecha_venta'] = {'$gte': datetime.fromisoformat(fecha_inicio)}
        if fecha_fin:
            if 'fecha_venta' in match_estado:
                match_estado['fecha_venta']['$lte'] = datetime.fromisoformat(fecha_fin)
            else:
                match_estado['fecha_venta'] = {'$lte': datetime.fromisoformat(fecha_fin)}
        ventas_por_estado_pipeline.append({'$match': match_estado})
    
    ventas_por_estado_pipeline.append({
        '$group': {
            '_id': '$estado',
            'cantidad': {'$sum': 1},
            'total_ingresos': {'$sum': '$total'}
        }
    })
    
    ventas_por_estado = list(ventas_collection.aggregate(ventas_por_estado_pipeline))
    
    # Convertir a diccionario
    ventas_estado_dict = {
        'completada': 0,
        'pendiente': 0,
        'cancelada': 0
    }
    
    ingresos_estado_dict = {
        'completada': 0,
        'pendiente': 0,
        'cancelada': 0
    }
    
    for item in ventas_por_estado:
        estado_key = item['_id']
        ventas_estado_dict[estado_key] = item['cantidad']
        ingresos_estado_dict[estado_key] = item['total_ingresos']
    
    # ========== VENTAS POR MÉTODO DE PAGO ==========
    ventas_por_metodo_pipeline = []
    if match_stage:
        ventas_por_metodo_pipeline.append({'$match': match_stage})
    
    ventas_por_metodo_pipeline.extend([
        {
            '$group': {
                '_id': '$metodo_pago',
                'cantidad': {'$sum': 1},
                'total': {'$sum': '$total'}
            }
        },
        {
            '$project': {
                '_id': 0,
                'metodo': '$_id',
                'cantidad': 1,
                'total': 1
            }
        }
    ])
    
    ventas_por_metodo = list(ventas_collection.aggregate(ventas_por_metodo_pipeline))
    
    # ========== TOP 5 PRODUCTOS MÁS VENDIDOS ==========
    top_productos_pipeline = []
    if match_stage:
        top_productos_pipeline.append({'$match': match_stage})
    
    top_productos_pipeline.extend([
        {'$unwind': '$productos'},
        {
            '$group': {
                '_id': '$productos.nombre',
                'total_vendido': {'$sum': '$productos.cantidad'},
                'ingresos_producto': {'$sum': '$productos.subtotal'}
            }
        },
        {'$sort': {'total_vendido': -1}},
        {'$limit': 5},
        {
            '$project': {
                '_id': 0,
                'nombre': '$_id',
                'total_vendido': 1,
                'ingresos_producto': 1
            }
        }
    ])
    
    top_productos = list(ventas_collection.aggregate(top_productos_pipeline))
    
    # ========== VENTAS POR DÍA (últimos 7 días) ==========
    fecha_hace_7_dias = datetime.now() - timedelta(days=7)
    ventas_por_dia_pipeline = [
        {
            '$match': {
                'fecha_venta': {'$gte': fecha_hace_7_dias}
            }
        },
        {
            '$group': {
                '_id': {
                    '$dateToString': {
                        'format': '%Y-%m-%d',
                        'date': '$fecha_venta'
                    }
                },
                'cantidad': {'$sum': 1},
                'total': {'$sum': '$total'}
            }
        },
        {'$sort': {'_id': 1}}
    ]
    
    ventas_por_dia = list(ventas_collection.aggregate(ventas_por_dia_pipeline))
    
    # ========== OBTENER MÉTODOS DE PAGO ÚNICOS ==========
    metodos_pago_pipeline = [
        {
            '$group': {
                '_id': '$metodo_pago'
            }
        },
        {'$sort': {'_id': 1}}
    ]
    
    metodos_pago_unicos = [m['_id'] for m in ventas_collection.aggregate(metodos_pago_pipeline) if m['_id']]
    
    context = {
        'usuario': request.user.first_name,
        'ventas': ventas,
        'total_ventas': total_ventas,
        'total_ingresos': total_ingresos,
        'promedio_venta': promedio_venta,
        'venta_maxima': venta_maxima,
        'venta_minima': venta_minima,
        'total_productos_vendidos': total_productos_vendidos,
        'ventas_completadas': ventas_estado_dict['completada'],
        'ventas_pendientes': ventas_estado_dict['pendiente'],
        'ventas_canceladas': ventas_estado_dict['cancelada'],
        'ingresos_completadas': ingresos_estado_dict['completada'],
        'ingresos_pendientes': ingresos_estado_dict['pendiente'],
        'ventas_por_metodo': ventas_por_metodo,
        'top_productos': top_productos,
        'ventas_por_dia': ventas_por_dia,
        'fecha_inicio': fecha_inicio or '',
        'fecha_fin': fecha_fin or '',
        'estado_filtro': estado or '',
        'metodo_pago_filtro': metodo_pago or '',
        'monto_minimo': monto_minimo or '',
        'monto_maximo': monto_maximo or '',
        'metodos_pago_disponibles': metodos_pago_unicos,
    }
    
    return render(request, 'reporte_ventas.html', context)


@login_required
def descargar_reporte_pdf(request):
    """Descarga el reporte de ventas en PDF"""
    if not request.user.is_staff:
        messages.error(request, '❌ No tienes permiso')
        return redirect('index')
    
    # Filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    estado = request.GET.get('estado')
    
    # Query
    filtro = {}
    if fecha_inicio:
        filtro['fecha_venta'] = {'$gte': datetime.fromisoformat(fecha_inicio)}
    if fecha_fin:
        if 'fecha_venta' in filtro:
            filtro['fecha_venta']['$lte'] = datetime.fromisoformat(fecha_fin)
        else:
            filtro['fecha_venta'] = {'$lte': datetime.fromisoformat(fecha_fin)}
    if estado:
        filtro['estado'] = estado
    
    ventas = list(ventas_collection.find(filtro).sort('fecha_venta', -1))
    
    # Generar PDF
    pdf_buffer = generar_reporte_ventas_pdf(ventas, fecha_inicio, fecha_fin)
    
    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Reporte_Ventas_{datetime.now().strftime("%Y%m%d")}.pdf"'
    
    return response


# ==========================================
# 📋 AUDITORÍA (ADMIN)
# ==========================================

@login_required
def ver_auditoria(request):
    """Vista de auditoría (solo admin)"""
    if not request.user.is_staff:
        messages.error(request, '❌ No tienes permiso')
        return redirect('index')
    
    # Filtros
    accion_filtro = request.GET.get('accion', '')
    usuario_filtro = request.GET.get('usuario', '')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # Construir filtros
    filtros = {}
    
    if accion_filtro:
        filtros['accion'] = accion_filtro
    
    if usuario_filtro:
        filtros['usuario_responsable'] = {'$regex': usuario_filtro, '$options': 'i'}
    
    if fecha_inicio and fecha_fin:
        filtros['fecha_hora'] = {
            '$gte': datetime.fromisoformat(fecha_inicio),
            '$lte': datetime.fromisoformat(fecha_fin)
        }
    
    # Obtener registros
    registros = list(auditoria_collection.find(filtros).sort('fecha_hora', -1).limit(100))
    
    # Convertir ObjectId
    for registro in registros:
        registro['id'] = str(registro['_id'])
    
    # Obtener acciones únicas para el filtro
    acciones_unicas = auditoria_collection.distinct('accion')
    
    # Estadísticas
    total_registros = auditoria_collection.count_documents(filtros)
    
    # Top acciones
    pipeline = [
        {'$group': {'_id': '$accion', 'cantidad': {'$sum': 1}}},
        {'$sort': {'cantidad': -1}},
        {'$limit': 5}
    ]
    
    if filtros:
        pipeline.insert(0, {'$match': filtros})
    
    top_acciones_raw = list(auditoria_collection.aggregate(pipeline))
    
    # Convertir _id a nombre para usar en template
    top_acciones = []
    for accion in top_acciones_raw:
        top_acciones.append({
            'nombre': accion['_id'],
            'cantidad': accion['cantidad']
        })
    
    context = {
        'usuario': request.user.first_name,
        'registros': registros,
        'total_registros': total_registros,
        'acciones_unicas': sorted(acciones_unicas),
        'top_acciones': top_acciones,
        'accion_filtro': accion_filtro,
        'usuario_filtro': usuario_filtro,
        'fecha_inicio': fecha_inicio or '',
        'fecha_fin': fecha_fin or '',
    }
    
    return render(request, 'auditoria.html', context)