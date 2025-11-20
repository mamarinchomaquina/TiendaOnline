from django.urls import path
from . import views

urlpatterns = [
    # ==========================================
    # 🏠 PÁGINAS PRINCIPALES
    # ==========================================
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # ==========================================
    # 📦 PRODUCTOS
    # ==========================================
    path('productos/', views.ver_productos, name='ver_productos'),
    path('productos/agregar/', views.agregar_producto, name='agregar_producto'),
    
    # ==========================================
    # 💬 COMENTARIOS
    # ==========================================
    path('comentarios/', views.todos_comentarios, name='todos_comentarios'),
    path('comentarios/guardar/', views.guardar_comentario, name='guardar_comentario'),
    
    # ==========================================
    # 👤 PERFIL
    # ==========================================
    path('mi-cuenta/', views.mi_cuenta, name='mi_cuenta'),
    
    # ==========================================
    # 🛒 CARRITO
    # ==========================================
    path('carrito/', views.ver_carrito, name='ver_carrito'),
    path('carrito/agregar/<str:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/remover/<str:producto_id>/', views.remover_del_carrito, name='remover_del_carrito'),
    path('carrito/actualizar/<str:producto_id>/', views.actualizar_cantidad_carrito, name='actualizar_cantidad_carrito'),
    path('carrito/vaciar/', views.vaciar_carrito, name='vaciar_carrito'),
    
    # ==========================================
    # 💳 VENTAS
    # ==========================================
    path('compra/procesar/', views.procesar_compra, name='procesar_compra'),
    path('factura/<str:venta_id>/', views.ver_factura, name='ver_factura'),
    path('factura/<str:venta_id>/pdf/', views.descargar_factura_pdf, name='descargar_factura_pdf'),
    path('mis-compras/', views.mis_compras, name='mis_compras'),
    
    # ==========================================
    # 📊 REPORTES (ADMIN)
    # ==========================================
    path('reportes/ventas/', views.reporte_ventas, name='reporte_ventas'),
    path('reportes/ventas/pdf/', views.descargar_reporte_pdf, name='descargar_reporte_pdf'),
    
    # ==========================================
    # 📋 AUDITORÍA (ADMIN)
    # ==========================================
    path('auditoria/', views.ver_auditoria, name='ver_auditoria'),
]