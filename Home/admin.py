from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Producto, Comentario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Administración personalizada de usuarios"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'edad', 'is_active']
    list_filter = ['is_active', 'is_staff', 'edad']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información Adicional', {'fields': ('apellidos', 'edad', 'foto_perfil')}),
    )


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Administración de productos"""
    list_display = ['nombre', 'precio', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    list_editable = ['activo', 'precio']
    date_hierarchy = 'fecha_creacion'


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    """Administración de comentarios"""
    list_display = ['usuario', 'calificacion', 'get_estrellas', 'estado', 'fecha']
    list_filter = ['estado', 'calificacion', 'fecha']
    search_fields = ['usuario__first_name', 'usuario__last_name', 'comentario']
    list_editable = ['estado']
    date_hierarchy = 'fecha'
    raw_id_fields = ['usuario']
    
    def get_estrellas(self, obj):
        return obj.get_estrellas()
    get_estrellas.short_description = 'Estrellas'