import json
from datetime import datetime, time
from io import BytesIO
from uuid import UUID

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .forms import (
    CategoriaForm,
    CompraEntradaForm,
    EventoForm,
    FiltroReporteForm,
    RegistroUsuarioForm,
    TipoEntradaForm,
    UbicacionForm,
    ValidacionEntradaForm,
    crear_orden_desde_form,
)
from .models import (
    Categoria,
    Entrada,
    Evento,
    Orden,
    TipoEntrada,
    Ubicacion,
    ValidacionAcceso,
    eventos_mas_vendidos,
    resumen_dashboard,
)


def es_organizador(user):
    return user.is_authenticated and (
        user.is_staff or user.groups.filter(name='Organizador').exists()
    )


organizador_required = user_passes_test(es_organizador, login_url='login')


def home(request):
    eventos = Evento.objects.filter(estado=Evento.PUBLICADO).select_related('categoria', 'ubicacion')
    q = request.GET.get('q', '').strip()
    categoria = request.GET.get('categoria', '').strip()
    fecha = request.GET.get('fecha', '').strip()

    if q:
        eventos = eventos.filter(titulo__icontains=q)
    if categoria:
        eventos = eventos.filter(categoria_id=categoria)
    if fecha:
        try:
            dia = datetime.strptime(fecha, '%Y-%m-%d').date()
            eventos = eventos.filter(fecha_inicio__date=dia)
        except ValueError:
            messages.warning(request, 'La fecha de busqueda no es valida.')

    return render(
        request,
        'eventos/home.html',
        {
            'eventos': eventos,
            'categorias': Categoria.objects.all(),
            'q': q,
            'categoria_actual': categoria,
            'fecha_actual': fecha,
        },
    )


def registro(request):
    if request.method == 'POST':
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Tu cuenta fue creada correctamente.')
            return redirect('home')
    else:
        form = RegistroUsuarioForm()
    return render(request, 'registration/register.html', {'form': form})


def detalle_evento(request, pk):
    evento = get_object_or_404(
        Evento.objects.select_related('categoria', 'ubicacion', 'organizador'),
        pk=pk,
    )
    form = CompraEntradaForm(evento=evento)
    return render(request, 'eventos/evento_detalle.html', {'evento': evento, 'form': form})


@login_required
def comprar_entrada(request, pk):
    evento = get_object_or_404(Evento, pk=pk, estado=Evento.PUBLICADO)
    form = CompraEntradaForm(request.POST or None, evento=evento)
    if request.method == 'POST' and form.is_valid():
        orden = crear_orden_desde_form(request.user, evento, form)
        messages.info(request, 'Orden creada. Confirma el pago simulado para generar tus entradas.')
        return redirect('pago_simulado', pk=orden.pk)
    return render(request, 'eventos/evento_detalle.html', {'evento': evento, 'form': form})


@login_required
def pago_simulado(request, pk):
    orden = get_object_or_404(
        Orden.objects.select_related('evento', 'tipo_entrada', 'asistente'),
        pk=pk,
        asistente=request.user,
    )
    if request.method == 'POST':
        orden.full_clean()
        orden.marcar_como_pagada()
        send_mail(
            subject=f'Confirmacion de entradas - {orden.evento.titulo}',
            message=(
                f'Tu pago simulado fue aprobado.\n'
                f'Orden: #{orden.pk}\nEvento: {orden.evento.titulo}\n'
                f'Entradas: {orden.cantidad}\nReferencia: {orden.referencia_pago}'
            ),
            from_email=None,
            recipient_list=[orden.asistente.email] if orden.asistente.email else [],
            fail_silently=True,
        )
        messages.success(request, 'Pago aprobado. Tus entradas con QR fueron generadas.')
        return redirect('mis_entradas')
    return render(request, 'eventos/pago_simulado.html', {'orden': orden})


@login_required
def mis_entradas(request):
    entradas = (
        Entrada.objects.filter(asistente=request.user)
        .select_related('evento', 'tipo_entrada', 'orden')
        .order_by('-creado')
    )
    return render(request, 'eventos/mis_entradas.html', {'entradas': entradas})


@login_required
def detalle_entrada(request, pk):
    entrada = get_object_or_404(
        Entrada.objects.select_related('evento', 'tipo_entrada', 'asistente'),
        pk=pk,
    )
    if entrada.asistente != request.user and not es_organizador(request.user):
        messages.error(request, 'No tienes permiso para ver esta entrada.')
        return redirect('mis_entradas')
    return render(request, 'eventos/entrada_detalle.html', {'entrada': entrada})


@login_required
@organizador_required
def dashboard(request):
    resumen = resumen_dashboard()
    top_eventos = eventos_mas_vendidos()
    ventas_mes = (
        Orden.objects.filter(estado_pago=Orden.PAGADA)
        .annotate(mes=TruncMonth('creado'))
        .values('mes')
        .annotate(total=Sum('total'), entradas=Sum('cantidad'))
        .order_by('mes')
    )
    validaciones = (
        ValidacionAcceso.objects.values('resultado')
        .annotate(total=Count('id'))
        .order_by('resultado')
    )
    charts = {
        'eventos_labels': [evento.titulo for evento in top_eventos],
        'eventos_data': [evento.total_entradas for evento in top_eventos],
        'mes_labels': [item['mes'].strftime('%b %Y') for item in ventas_mes if item['mes']],
        'mes_data': [float(item['total'] or 0) for item in ventas_mes],
        'validacion_labels': [item['resultado'].title() for item in validaciones],
        'validacion_data': [item['total'] for item in validaciones],
    }
    return render(
        request,
        'eventos/dashboard.html',
        {
            'resumen': resumen,
            'charts_json': json.dumps(charts),
            'eventos': Evento.objects.select_related('categoria', 'ubicacion')[:6],
            'entradas_recientes': Entrada.objects.select_related('evento', 'asistente')[:8],
        },
    )


@login_required
@organizador_required
def validar_acceso(request):
    form = ValidacionEntradaForm(request.POST or None)
    resultado = None
    if request.method == 'POST' and form.is_valid():
        codigo = form.cleaned_data['codigo']
        entrada = None
        observacion = ''
        try:
            entrada = Entrada.objects.select_related('evento', 'asistente').get(codigo=UUID(codigo))
        except (ValueError, Entrada.DoesNotExist):
            observacion = 'Codigo no encontrado.'

        if entrada and entrada.validar():
            resultado = 'Entrada valida. Acceso autorizado.'
            estado = ValidacionAcceso.VALIDA
            observacion = f'Acceso para {entrada.asistente.get_full_name() or entrada.asistente.username}.'
            messages.success(request, resultado)
        else:
            estado = ValidacionAcceso.INVALIDA
            if entrada and entrada.estado == Entrada.USADA:
                observacion = 'Esta entrada ya fue usada.'
            messages.error(request, observacion or 'Entrada invalida.')

        ValidacionAcceso.objects.create(
            codigo_ingresado=codigo,
            entrada=entrada,
            validado_por=request.user,
            resultado=estado,
            observacion=observacion,
        )
    return render(request, 'eventos/validar_acceso.html', {'form': form, 'resultado': resultado})


def filtrar_entradas_reporte(request):
    form = FiltroReporteForm(request.GET or None)
    entradas = Entrada.objects.select_related('evento', 'tipo_entrada', 'asistente', 'orden')
    if form.is_valid():
        evento = form.cleaned_data.get('evento')
        estado = form.cleaned_data.get('estado')
        desde = form.cleaned_data.get('desde')
        hasta = form.cleaned_data.get('hasta')
        if evento:
            entradas = entradas.filter(evento=evento)
        if estado:
            entradas = entradas.filter(estado=estado)
        if desde:
            entradas = entradas.filter(creado__date__gte=desde)
        if hasta:
            entradas = entradas.filter(creado__date__lte=hasta)
    return form, entradas


@login_required
@organizador_required
def reportes(request):
    form, entradas = filtrar_entradas_reporte(request)
    return render(request, 'eventos/reportes.html', {'form': form, 'entradas': entradas[:100]})


@login_required
@organizador_required
def exportar_excel(request):
    _, entradas = filtrar_entradas_reporte(request)
    wb = Workbook()
    ws = wb.active
    ws.title = 'Entradas'
    ws.append(['Codigo', 'Evento', 'Asistente', 'Tipo', 'Estado', 'Orden', 'Creado'])
    for entrada in entradas:
        ws.append([
            str(entrada.codigo),
            entrada.evento.titulo,
            entrada.asistente.get_full_name() or entrada.asistente.username,
            entrada.tipo_entrada.nombre,
            entrada.get_estado_display(),
            entrada.orden_id,
            timezone.localtime(entrada.creado).strftime('%Y-%m-%d %H:%M'),
        ])
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="reporte_entradas.xlsx"'
    wb.save(response)
    return response


@login_required
@organizador_required
def exportar_pdf(request):
    _, entradas = filtrar_entradas_reporte(request)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50
    pdf.setFont('Helvetica-Bold', 14)
    pdf.drawString(40, y, 'Reporte de entradas - Eventix')
    y -= 28
    pdf.setFont('Helvetica', 9)
    for entrada in entradas[:35]:
        linea = (
            f'{entrada.evento.titulo[:24]} | '
            f'{entrada.asistente.username[:14]} | '
            f'{entrada.tipo_entrada.nombre[:12]} | '
            f'{entrada.get_estado_display()} | '
            f'{timezone.localtime(entrada.creado).strftime("%Y-%m-%d")}'
        )
        pdf.drawString(40, y, linea)
        y -= 17
        if y < 60:
            pdf.showPage()
            y = height - 50
            pdf.setFont('Helvetica', 9)
    pdf.save()
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte_entradas.pdf"'
    return response


@login_required
@organizador_required
def eventos_admin(request):
    eventos = Evento.objects.select_related('categoria', 'ubicacion', 'organizador')
    return render(request, 'eventos/eventos_admin.html', {'eventos': eventos})


@login_required
@organizador_required
def evento_form(request, pk=None):
    evento = get_object_or_404(Evento, pk=pk) if pk else None
    form = EventoForm(request.POST or None, instance=evento)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        if not obj.pk:
            obj.organizador = request.user
        obj.save()
        messages.success(request, 'Evento guardado correctamente.')
        return redirect('eventos_admin')
    return render(request, 'eventos/form.html', {'form': form, 'titulo': 'Evento'})


@login_required
@organizador_required
def evento_eliminar(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    if request.method == 'POST':
        evento.delete()
        messages.success(request, 'Evento eliminado.')
        return redirect('eventos_admin')
    return render(request, 'eventos/confirm_delete.html', {'objeto': evento})


@login_required
@organizador_required
def ubicaciones_admin(request):
    return render(request, 'eventos/ubicaciones_admin.html', {'ubicaciones': Ubicacion.objects.all()})


@login_required
@organizador_required
def ubicacion_form(request, pk=None):
    ubicacion = get_object_or_404(Ubicacion, pk=pk) if pk else None
    form = UbicacionForm(request.POST or None, instance=ubicacion)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Ubicacion guardada.')
        return redirect('ubicaciones_admin')
    return render(request, 'eventos/form.html', {'form': form, 'titulo': 'Ubicacion'})


@login_required
@organizador_required
def ubicacion_eliminar(request, pk):
    ubicacion = get_object_or_404(Ubicacion, pk=pk)
    if request.method == 'POST':
        ubicacion.delete()
        messages.success(request, 'Ubicacion eliminada.')
        return redirect('ubicaciones_admin')
    return render(request, 'eventos/confirm_delete.html', {'objeto': ubicacion})


@login_required
@organizador_required
def categorias_admin(request):
    return render(request, 'eventos/categorias_admin.html', {'categorias': Categoria.objects.all()})


@login_required
@organizador_required
def categoria_form(request, pk=None):
    categoria = get_object_or_404(Categoria, pk=pk) if pk else None
    form = CategoriaForm(request.POST or None, instance=categoria)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Categoria guardada.')
        return redirect('categorias_admin')
    return render(request, 'eventos/form.html', {'form': form, 'titulo': 'Categoria'})


@login_required
@organizador_required
def categoria_eliminar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        categoria.delete()
        messages.success(request, 'Categoria eliminada.')
        return redirect('categorias_admin')
    return render(request, 'eventos/confirm_delete.html', {'objeto': categoria})


@login_required
@organizador_required
def tipos_admin(request):
    tipos = TipoEntrada.objects.select_related('evento')
    return render(request, 'eventos/tipos_admin.html', {'tipos': tipos})


@login_required
@organizador_required
def tipo_form(request, pk=None):
    tipo = get_object_or_404(TipoEntrada, pk=pk) if pk else None
    form = TipoEntradaForm(request.POST or None, instance=tipo)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tipo de entrada guardado.')
        return redirect('tipos_admin')
    return render(request, 'eventos/form.html', {'form': form, 'titulo': 'Tipo de entrada'})


@login_required
@organizador_required
def tipo_eliminar(request, pk):
    tipo = get_object_or_404(TipoEntrada, pk=pk)
    if request.method == 'POST':
        tipo.delete()
        messages.success(request, 'Tipo de entrada eliminado.')
        return redirect('tipos_admin')
    return render(request, 'eventos/confirm_delete.html', {'objeto': tipo})
