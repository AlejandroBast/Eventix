def roles(request):
    user = request.user
    es_organizador = False
    if user.is_authenticated:
        es_organizador = user.is_staff or user.groups.filter(name='Organizador').exists()
    return {'es_organizador': es_organizador}
