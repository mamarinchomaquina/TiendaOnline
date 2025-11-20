from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from .mongodb import get_collection, str_to_objectid, objectid_to_str

class Usuario(AbstractUser):
    """Modelo de Usuario para Django Admin"""
    edad = models.IntegerField(null=True, blank=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    mongo_id = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip()

    def save(self, *args, **kwargs):
        """
        Guarda en la base de datos relacional y sincroniza/crea el documento en la colección 'usuarios' de MongoDB.
        """
        super().save(*args, **kwargs)
        try:
            usuarios_col = get_collection('usuarios')
            doc = {
                'django_id': self.pk,
                'username': self.username,
                'email': self.email,
                'first_name': self.first_name,
                'last_name': self.last_name,
                'edad': self.edad,
                'foto_perfil': (self.foto_perfil.url if getattr(self.foto_perfil, 'url', None) else None),
                'last_sync': timezone.now(),
            }
            if self.mongo_id:
                oid = str_to_objectid(self.mongo_id)
                if oid:
                    usuarios_col.update_one({'_id': oid}, {'$set': doc}, upsert=True)
                else:
                    res = usuarios_col.insert_one(doc)
                    self.mongo_id = objectid_to_str(res.inserted_id)
                    super().save(update_fields=['mongo_id'])
            else:
                res = usuarios_col.insert_one(doc)
                self.mongo_id = objectid_to_str(res.inserted_id)
                super().save(update_fields=['mongo_id'])
        except Exception:
            pass

    def delete(self, *args, **kwargs):
        """Elimina también el documento asociado en MongoDB si existe."""
        try:
            usuarios_col = get_collection('usuarios')
            if self.mongo_id:
                oid = str_to_objectid(self.mongo_id)
                if oid:
                    usuarios_col.delete_one({'_id': oid})
            else:
                usuarios_col.delete_one({'django_id': self.pk})
        except Exception:
            pass
        super().delete(*args, **kwargs)


class Producto(models.Model):
    """Modelo para productos de la tienda"""
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    imagen = models.URLField(max_length=500)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['-fecha_creacion']


class Comentario(models.Model):
    """Modelo para comentarios y calificaciones"""
    CALIFICACIONES = [
        (1, '⭐'),
        (2, '⭐⭐'),
        (3, '⭐⭐⭐'),
        (4, '⭐⭐⭐⭐'),
        (5, '⭐⭐⭐⭐⭐'),
    ]
    
    ESTADOS = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='comentarios')
    comentario = models.TextField()
    calificacion = models.IntegerField(choices=CALIFICACIONES)
    fecha = models.DateTimeField(default=timezone.now)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='activo')
    
    def __str__(self):
        return f"Comentario de {self.usuario.first_name} - {self.calificacion}⭐"
    
    def get_estrellas(self):
        return '⭐' * self.calificacion
    
    class Meta:
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"
        ordering = ['-fecha']