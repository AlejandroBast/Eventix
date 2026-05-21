from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError

from .models import Categoria, Entrada, Evento, Orden, TipoEntrada, Ubicacion


class RegistroUsuarioForm(UserCreationForm):
    first_name = forms.CharField(label='Nombre', max_length=80)
    last_name = forms.CharField(label='Apellido', max_length=80, required=False)
    email = forms.EmailField(label='Correo electronico')

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Ya existe un usuario con este correo.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email'].lower()
        if commit:
            user.save()
            grupo, _ = Group.objects.get_or_create(name='Asistente')
            user.groups.add(grupo)
        return user


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            if isinstance(field.widget, forms.CheckboxInput):
                css = 'form-check-input'
            field.widget.attrs.update({'class': css})


class CategoriaForm(BootstrapModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion']


class UbicacionForm(BootstrapModelForm):
    class Meta:
        model = Ubicacion
        fields = ['nombre', 'direccion', 'ciudad', 'capacidad']


class EventoForm(BootstrapModelForm):
    fecha_inicio = forms.DateTimeField(
        label='Fecha de inicio',
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
    )
    fecha_fin = forms.DateTimeField(
        label='Fecha de fin',
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
    )

    class Meta:
        model = Evento
        fields = [
            'titulo',
            'descripcion',
            'categoria',
            'ubicacion',
            'fecha_inicio',
            'fecha_fin',
            'capacidad',
            'estado',
            'imagen_url',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }


class TipoEntradaForm(BootstrapModelForm):
    class Meta:
        model = TipoEntrada
        fields = ['evento', 'nombre', 'precio', 'cupo', 'activo']


class CompraEntradaForm(forms.Form):
    tipo_entrada = forms.ModelChoiceField(
        label='Tipo de entrada',
        queryset=TipoEntrada.objects.none(),
        empty_label=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    cantidad = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )

    def __init__(self, *args, evento=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.evento = evento
        self.fields['tipo_entrada'].queryset = evento.tipos_entrada.filter(activo=True)

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo_entrada')
        cantidad = cleaned.get('cantidad') or 0
        if tipo and cantidad > tipo.disponibles:
            raise ValidationError('No hay suficientes entradas disponibles para ese tipo.')
        if self.evento and cantidad > self.evento.cupos_disponibles:
            raise ValidationError('No hay suficientes cupos disponibles en el evento.')
        return cleaned


class ValidacionEntradaForm(forms.Form):
    codigo = forms.CharField(
        label='Codigo de entrada',
        max_length=80,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pega o escanea el codigo QR'}),
    )

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo'].strip()
        if codigo.startswith('EVENTIX:'):
            codigo = codigo.replace('EVENTIX:', '', 1)
        return codigo


class FiltroReporteForm(forms.Form):
    evento = forms.ModelChoiceField(
        queryset=Evento.objects.all(),
        required=False,
        label='Evento',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    estado = forms.ChoiceField(
        choices=[('', 'Todos')] + Entrada.ESTADOS,
        required=False,
        label='Estado',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    desde = forms.DateField(
        required=False,
        label='Desde',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    hasta = forms.DateField(
        required=False,
        label='Hasta',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )


def crear_orden_desde_form(usuario, evento, form):
    tipo = form.cleaned_data['tipo_entrada']
    cantidad = form.cleaned_data['cantidad']
    orden = Orden.objects.create(
        asistente=usuario,
        evento=evento,
        tipo_entrada=tipo,
        cantidad=cantidad,
    )
    return orden
