from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('registro/', views.registro, name='registro'),
    path('eventos/<int:pk>/', views.detalle_evento, name='detalle_evento'),
    path('eventos/<int:pk>/comprar/', views.comprar_entrada, name='comprar_entrada'),
    path('ordenes/<int:pk>/pago-simulado/', views.pago_simulado, name='pago_simulado'),
    path('mis-entradas/', views.mis_entradas, name='mis_entradas'),
    path('entradas/<int:pk>/', views.detalle_entrada, name='detalle_entrada'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('validar-acceso/', views.validar_acceso, name='validar_acceso'),
    path('reportes/', views.reportes, name='reportes'),
    path('reportes/excel/', views.exportar_excel, name='exportar_excel'),
    path('reportes/pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('gestion/eventos/', views.eventos_admin, name='eventos_admin'),
    path('gestion/eventos/nuevo/', views.evento_form, name='evento_crear'),
    path('gestion/eventos/<int:pk>/editar/', views.evento_form, name='evento_editar'),
    path('gestion/eventos/<int:pk>/eliminar/', views.evento_eliminar, name='evento_eliminar'),
    path('gestion/ubicaciones/', views.ubicaciones_admin, name='ubicaciones_admin'),
    path('gestion/ubicaciones/nueva/', views.ubicacion_form, name='ubicacion_crear'),
    path('gestion/ubicaciones/<int:pk>/editar/', views.ubicacion_form, name='ubicacion_editar'),
    path('gestion/ubicaciones/<int:pk>/eliminar/', views.ubicacion_eliminar, name='ubicacion_eliminar'),
    path('gestion/categorias/', views.categorias_admin, name='categorias_admin'),
    path('gestion/categorias/nueva/', views.categoria_form, name='categoria_crear'),
    path('gestion/categorias/<int:pk>/editar/', views.categoria_form, name='categoria_editar'),
    path('gestion/categorias/<int:pk>/eliminar/', views.categoria_eliminar, name='categoria_eliminar'),
    path('gestion/tipos-entrada/', views.tipos_admin, name='tipos_admin'),
    path('gestion/tipos-entrada/nuevo/', views.tipo_form, name='tipo_crear'),
    path('gestion/tipos-entrada/<int:pk>/editar/', views.tipo_form, name='tipo_editar'),
    path('gestion/tipos-entrada/<int:pk>/eliminar/', views.tipo_eliminar, name='tipo_eliminar'),
]
