from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from eventos.models import Categoria, Evento, Orden, TipoEntrada, Ubicacion


class Command(BaseCommand):
    help = 'Carga usuarios, eventos y entradas de demostracion para Eventix.'

    def handle(self, *args, **options):
        organizadores, _ = Group.objects.get_or_create(name='Organizador')
        asistentes, _ = Group.objects.get_or_create(name='Asistente')

        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            admin.set_password('admin12345')
            admin.save()
        admin.groups.add(organizadores)

        organizador, created = User.objects.get_or_create(
            username='organizador',
            defaults={'email': 'organizador@example.com', 'first_name': 'Laura'},
        )
        if created:
            organizador.set_password('organizador123')
            organizador.save()
        organizador.groups.add(organizadores)

        asistente, created = User.objects.get_or_create(
            username='asistente',
            defaults={'email': 'asistente@example.com', 'first_name': 'Carlos'},
        )
        if created:
            asistente.set_password('asistente123')
            asistente.save()
        asistente.groups.add(asistentes)

        categorias = {
            nombre: Categoria.objects.get_or_create(nombre=nombre, defaults={'descripcion': descripcion})[0]
            for nombre, descripcion in {
                'Tecnologia': 'Conferencias, bootcamps y comunidades tech.',
                'Cultura': 'Eventos artisticos, ferias y encuentros culturales.',
                'Negocios': 'Networking, emprendimiento y formacion empresarial.',
            }.items()
        }

        teatro, _ = Ubicacion.objects.get_or_create(
            nombre='Auditorio Central',
            defaults={'direccion': 'Calle 10 # 20-30', 'ciudad': 'Bogota', 'capacidad': 450},
        )
        coworking, _ = Ubicacion.objects.get_or_create(
            nombre='Campus Innova',
            defaults={'direccion': 'Carrera 7 # 80-15', 'ciudad': 'Medellin', 'capacidad': 220},
        )

        now = timezone.now()
        eventos = [
            {
                'titulo': 'Django Summit Colombia',
                'descripcion': 'Charlas, talleres y networking sobre desarrollo web con Django.',
                'categoria': categorias['Tecnologia'],
                'ubicacion': teatro,
                'fecha_inicio': now + timedelta(days=12),
                'fecha_fin': now + timedelta(days=12, hours=6),
                'capacidad': 300,
            },
            {
                'titulo': 'Festival Creativo Digital',
                'descripcion': 'Muestras de arte, experiencias interactivas y cultura digital.',
                'categoria': categorias['Cultura'],
                'ubicacion': coworking,
                'fecha_inicio': now + timedelta(days=22),
                'fecha_fin': now + timedelta(days=22, hours=5),
                'capacidad': 180,
            },
            {
                'titulo': 'Foro de Emprendimiento',
                'descripcion': 'Paneles de inversion, ventas y crecimiento para nuevos negocios.',
                'categoria': categorias['Negocios'],
                'ubicacion': teatro,
                'fecha_inicio': now + timedelta(days=35),
                'fecha_fin': now + timedelta(days=35, hours=4),
                'capacidad': 250,
            },
        ]

        for data in eventos:
            evento, _ = Evento.objects.get_or_create(
                titulo=data['titulo'],
                defaults={**data, 'organizador': organizador, 'estado': Evento.PUBLICADO},
            )
            general, _ = TipoEntrada.objects.get_or_create(
                evento=evento,
                nombre='General',
                defaults={'precio': 35000, 'cupo': min(150, evento.capacidad), 'activo': True},
            )
            vip, _ = TipoEntrada.objects.get_or_create(
                evento=evento,
                nombre='VIP',
                defaults={'precio': 75000, 'cupo': min(60, evento.capacidad), 'activo': True},
            )

            if not Orden.objects.filter(evento=evento, asistente=asistente).exists():
                orden = Orden.objects.create(
                    asistente=asistente,
                    evento=evento,
                    tipo_entrada=general if evento.titulo != 'Foro de Emprendimiento' else vip,
                    cantidad=2,
                )
                orden.marcar_como_pagada()

        self.stdout.write(self.style.SUCCESS('Datos demo listos. Usuarios: admin/admin12345, organizador/organizador123, asistente/asistente123'))
