from django.contrib import admin

from .models import Categoria, Entrada, Evento, Orden, TipoEntrada, Ubicacion, ValidacionAcceso


class TipoEntradaInline(admin.TabularInline):
    model = TipoEntrada
    extra = 1


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'categoria', 'ubicacion', 'fecha_inicio', 'estado', 'capacidad']
    list_filter = ['estado', 'categoria', 'fecha_inicio']
    search_fields = ['titulo', 'descripcion', 'ubicacion__nombre']
    inlines = [TipoEntradaInline]


@admin.register(Entrada)
class EntradaAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'evento', 'asistente', 'tipo_entrada', 'estado', 'creado']
    list_filter = ['estado', 'evento']
    search_fields = ['codigo', 'asistente__username', 'asistente__email', 'evento__titulo']
    readonly_fields = ['codigo', 'qr_imagen', 'creado', 'validado_en']


@admin.register(Orden)
class OrdenAdmin(admin.ModelAdmin):
    list_display = ['id', 'asistente', 'evento', 'cantidad', 'total', 'estado_pago', 'creado']
    list_filter = ['estado_pago', 'evento']
    search_fields = ['asistente__username', 'referencia_pago', 'evento__titulo']


admin.site.register(Categoria)
admin.site.register(Ubicacion)
admin.site.register(TipoEntrada)
admin.site.register(ValidacionAcceso)

# Register your models here.
