from django import forms
from .models import Usuario, Producto, Comentario


class RegisterForm(forms.Form):
    """Formulario de registro"""
    nombre = forms.CharField(max_length=100, required=True)
    apellidos = forms.CharField(max_length=100, required=True)
    edad = forms.IntegerField(required=True)
    correo = forms.EmailField(required=True)
    contraseña = forms.CharField(widget=forms.PasswordInput, required=True)
    
    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if Usuario.objects.filter(email=correo).exists():
            raise forms.ValidationError('⚠️ El correo ya está registrado.')
        return correo
    
    def save(self):
        """Método para guardar el usuario"""
        usuario = Usuario()
        usuario.first_name = self.cleaned_data['nombre']
        usuario.last_name = self.cleaned_data['apellidos']
        usuario.edad = self.cleaned_data['edad']
        usuario.email = self.cleaned_data['correo']
        usuario.username = self.cleaned_data['correo']  # Usar email como username
        usuario.set_password(self.cleaned_data['contraseña'])
        usuario.save()
        return usuario


class ProductoForm(forms.ModelForm):
    """Formulario para agregar productos"""
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'imagen': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'URL de la imagen'}),
        }


class ComentarioForm(forms.ModelForm):
    """Formulario para comentarios"""
    class Meta:
        model = Comentario
        fields = ['comentario', 'calificacion']
        widgets = {
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'calificacion': forms.Select(attrs={'class': 'form-control'}),
        }


class PerfilForm(forms.ModelForm):
    """Formulario para editar perfil"""
    nombre = forms.CharField(max_length=100, required=True)
    apellidos = forms.CharField(max_length=100, required=True)
    
    class Meta:
        model = Usuario
        fields = ['edad', 'email', 'foto_perfil']
        widgets = {
            'edad': forms.NumberInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['nombre'].initial = self.instance.first_name
            self.fields['apellidos'].initial = self.instance.last_name
    
    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.first_name = self.cleaned_data['nombre']
        usuario.last_name = self.cleaned_data['apellidos']
        if commit:
            usuario.save()
        return usuario