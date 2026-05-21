import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Entrada, Evento, Orden, TipoEntrada, Ubicacion, ValidacionAcceso


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class EventosFlowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        organizadores = Group.objects.create(name='Organizador')
        Group.objects.create(name='Asistente')
        self.organizador = User.objects.create_user('organizador', password='organizador123')
        self.organizador.groups.add(organizadores)
        self.asistente = User.objects.create_user('asistente', password='asistente123', email='a@test.com')
        categoria = Categoria.objects.create(nombre='Tecnologia')
        ubicacion = Ubicacion.objects.create(
            nombre='Auditorio',
            direccion='Calle 1',
            ciudad='Bogota',
            capacidad=100,
        )
        self.evento = Evento.objects.create(
            titulo='Django Summit',
            descripcion='Evento de prueba',
            categoria=categoria,
            ubicacion=ubicacion,
            organizador=self.organizador,
            fecha_inicio=timezone.now() + timedelta(days=5),
            fecha_fin=timezone.now() + timedelta(days=5, hours=4),
            capacidad=80,
            estado=Evento.PUBLICADO,
        )
        self.tipo = TipoEntrada.objects.create(
            evento=self.evento,
            nombre='General',
            precio=25000,
            cupo=50,
        )

    def test_home_lista_eventos_publicados(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, 'Django Summit')
        self.assertContains(response, 'Filtrar')

    def test_compra_y_pago_generan_entrada_con_qr(self):
        self.client.login(username='asistente', password='asistente123')
        response = self.client.post(
            reverse('comprar_entrada', args=[self.evento.pk]),
            {'tipo_entrada': self.tipo.pk, 'cantidad': 1},
        )
        self.assertEqual(response.status_code, 302)
        orden = Orden.objects.get(asistente=self.asistente)

        response = self.client.post(reverse('pago_simulado', args=[orden.pk]))
        self.assertEqual(response.status_code, 302)
        entrada = Entrada.objects.get(orden=orden)
        self.assertEqual(entrada.estado, Entrada.ACTIVA)
        self.assertTrue(entrada.qr_imagen.name)

    def test_validacion_de_acceso_marca_entrada_como_usada(self):
        orden = Orden.objects.create(
            asistente=self.asistente,
            evento=self.evento,
            tipo_entrada=self.tipo,
            cantidad=1,
        )
        orden.marcar_como_pagada()
        entrada = orden.entradas.get()

        self.client.login(username='organizador', password='organizador123')
        response = self.client.post(reverse('validar_acceso'), {'codigo': str(entrada.codigo)})
        self.assertEqual(response.status_code, 200)

        entrada.refresh_from_db()
        self.assertEqual(entrada.estado, Entrada.USADA)
        self.assertEqual(ValidacionAcceso.objects.filter(resultado=ValidacionAcceso.VALIDA).count(), 1)

    def test_dashboard_requiere_rol_organizador(self):
        self.client.login(username='asistente', password='asistente123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

# Create your tests here.
