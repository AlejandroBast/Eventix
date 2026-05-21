import uuid
from decimal import Decimal
from io import BytesIO

import qrcode
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.db.models import Count, Sum
from django.utils import timezone


User = get_user_model()


class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'categoria'
        verbose_name_plural = 'categorias'

    def __str__(self):
        return self.nombre


class Ubicacion(models.Model):
    nombre = models.CharField(max_length=120)
    direccion = models.CharField(max_length=180)
    ciudad = models.CharField(max_length=80, default='Bogota')
    capacidad = models.PositiveIntegerField()

    class Meta:
        ordering = ['ciudad', 'nombre']
        verbose_name = 'ubicacion'
        verbose_name_plural = 'ubicaciones'

    def __str__(self):
        return f'{self.nombre} - {self.ciudad}'


class Evento(models.Model):
    BORRADOR = 'borrador'
    PUBLICADO = 'publicado'
    FINALIZADO = 'finalizado'
    CANCELADO = 'cancelado'
    ESTADOS = [
        (BORRADOR, 'Borrador'),
        (PUBLICADO, 'Publicado'),
        (FINALIZADO, 'Finalizado'),
        (CANCELADO, 'Cancelado'),
    ]

    titulo = models.CharField(max_length=140)
    descripcion = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='eventos')
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT, related_name='eventos')
    organizador = models.ForeignKey(User, on_delete=models.PROTECT, related_name='eventos_creados')
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    capacidad = models.PositiveIntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default=PUBLICADO)
    imagen_url = models.URLField('URL de imagen', blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['fecha_inicio']
        verbose_name = 'evento'
        verbose_name_plural = 'eventos'

    def __str__(self):
        return self.titulo

    def clean(self):
        if self.fecha_fin <= self.fecha_inicio:
            raise ValidationError('La fecha de fin debe ser posterior a la fecha de inicio.')
        if self.ubicacion_id and self.capacidad > self.ubicacion.capacidad:
            raise ValidationError('La capacidad del evento no puede superar la capacidad de la ubicacion.')

    @property
    def entradas_vendidas(self):
        return self.entradas.filter(estado__in=[Entrada.ACTIVA, Entrada.USADA]).count()

    @property
    def cupos_disponibles(self):
        return max(self.capacidad - self.entradas_vendidas, 0)

    @property
    def porcentaje_ocupacion(self):
        if not self.capacidad:
            return 0
        return round((self.entradas_vendidas / self.capacidad) * 100, 1)

    @property
    def esta_activo(self):
        return self.estado == self.PUBLICADO and self.fecha_fin >= timezone.now()


class TipoEntrada(models.Model):
    evento = models.ForeignKey(Evento, on_delete=models.CASCADE, related_name='tipos_entrada')
    nombre = models.CharField(max_length=80)
    precio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cupo = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['evento', 'precio']
        unique_together = ['evento', 'nombre']
        verbose_name = 'tipo de entrada'
        verbose_name_plural = 'tipos de entrada'

    def __str__(self):
        return f'{self.evento} - {self.nombre}'

    @property
    def vendidas(self):
        return self.entradas.filter(estado__in=[Entrada.ACTIVA, Entrada.USADA]).count()

    @property
    def disponibles(self):
        return max(self.cupo - self.vendidas, 0)


class Orden(models.Model):
    PENDIENTE = 'pendiente'
    PAGADA = 'pagada'
    CANCELADA = 'cancelada'
    ESTADOS_PAGO = [
        (PENDIENTE, 'Pendiente'),
        (PAGADA, 'Pagada'),
        (CANCELADA, 'Cancelada'),
    ]

    asistente = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ordenes')
    evento = models.ForeignKey(Evento, on_delete=models.PROTECT, related_name='ordenes')
    tipo_entrada = models.ForeignKey(TipoEntrada, on_delete=models.PROTECT, related_name='ordenes')
    cantidad = models.PositiveIntegerField(default=1)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estado_pago = models.CharField(max_length=20, choices=ESTADOS_PAGO, default=PENDIENTE)
    referencia_pago = models.CharField(max_length=80, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    pagado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creado']
        verbose_name = 'orden'
        verbose_name_plural = 'ordenes'

    def __str__(self):
        return f'Orden #{self.pk} - {self.asistente}'

    def clean(self):
        if self.cantidad < 1:
            raise ValidationError('La cantidad debe ser mayor a cero.')
        if self.tipo_entrada_id and self.cantidad > self.tipo_entrada.disponibles:
            raise ValidationError('No hay suficientes entradas disponibles.')

    def save(self, *args, **kwargs):
        self.total = (self.tipo_entrada.precio if self.tipo_entrada_id else Decimal('0')) * self.cantidad
        super().save(*args, **kwargs)

    def marcar_como_pagada(self):
        if self.estado_pago == self.PAGADA:
            return
        self.estado_pago = self.PAGADA
        self.referencia_pago = f'SIM-{uuid.uuid4().hex[:10].upper()}'
        self.pagado_en = timezone.now()
        self.save(update_fields=['estado_pago', 'referencia_pago', 'pagado_en', 'total'])
        for _ in range(self.cantidad):
            Entrada.objects.create(
                asistente=self.asistente,
                evento=self.evento,
                tipo_entrada=self.tipo_entrada,
                orden=self,
            )


class Entrada(models.Model):
    ACTIVA = 'activa'
    USADA = 'usada'
    CANCELADA = 'cancelada'
    ESTADOS = [
        (ACTIVA, 'Activa'),
        (USADA, 'Usada'),
        (CANCELADA, 'Cancelada'),
    ]

    asistente = models.ForeignKey(User, on_delete=models.PROTECT, related_name='entradas')
    evento = models.ForeignKey(Evento, on_delete=models.PROTECT, related_name='entradas')
    tipo_entrada = models.ForeignKey(TipoEntrada, on_delete=models.PROTECT, related_name='entradas')
    orden = models.ForeignKey(Orden, on_delete=models.PROTECT, related_name='entradas')
    codigo = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    qr_imagen = models.ImageField(upload_to='qrcodes/', blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ACTIVA)
    creado = models.DateTimeField(auto_now_add=True)
    validado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-creado']
        verbose_name = 'entrada'
        verbose_name_plural = 'entradas'

    def __str__(self):
        return f'{self.evento} - {self.codigo}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.qr_imagen:
            qr = qrcode.make(f'EVENTIX:{self.codigo}')
            buffer = BytesIO()
            qr.save(buffer, format='PNG')
            filename = f'entrada-{self.codigo}.png'
            self.qr_imagen.save(filename, ContentFile(buffer.getvalue()), save=False)
            super().save(update_fields=['qr_imagen'])

    def validar(self):
        if self.estado != self.ACTIVA:
            return False
        self.estado = self.USADA
        self.validado_en = timezone.now()
        self.save(update_fields=['estado', 'validado_en'])
        return True


class ValidacionAcceso(models.Model):
    VALIDA = 'valida'
    INVALIDA = 'invalida'
    ESTADOS = [
        (VALIDA, 'Valida'),
        (INVALIDA, 'Invalida'),
    ]

    codigo_ingresado = models.CharField(max_length=80)
    entrada = models.ForeignKey(
        Entrada,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='validaciones',
    )
    validado_por = models.ForeignKey(User, on_delete=models.PROTECT, related_name='validaciones_realizadas')
    resultado = models.CharField(max_length=20, choices=ESTADOS)
    observacion = models.CharField(max_length=180, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado']
        verbose_name = 'validacion de acceso'
        verbose_name_plural = 'validaciones de acceso'

    def __str__(self):
        return f'{self.codigo_ingresado} - {self.resultado}'


def resumen_dashboard():
    total_entradas = Entrada.objects.filter(estado__in=[Entrada.ACTIVA, Entrada.USADA]).count()
    total_ingresos = Orden.objects.filter(estado_pago=Orden.PAGADA).aggregate(total=Sum('total'))['total'] or 0
    return {
        'eventos': Evento.objects.count(),
        'entradas': total_entradas,
        'ingresos': total_ingresos,
        'validaciones': ValidacionAcceso.objects.filter(resultado=ValidacionAcceso.VALIDA).count(),
    }


def eventos_mas_vendidos():
    return (
        Evento.objects.annotate(total_entradas=Count('entradas'))
        .order_by('-total_entradas')[:5]
    )
