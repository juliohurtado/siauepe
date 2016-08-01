# -*- coding: utf-8 -*-
"""siauepe URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

from django.contrib.auth.views import login

#import incidencia.views
#import inspector.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', 'inspector.views.home', name='home'),

    url(r'^login/$', login, {'template_name': 'login.html', }, name='login'),
    url(r'^logout/$', 'inspector.views.logout_v', name='logout'),
    url(r'^perfil/password/$', 'django.contrib.auth.views.password_change', {'post_change_redirect' : '/','template_name': 'password.html'},name='contrasena'),

    url(r'^incidencia/$', 'incidencia.views.home_incidencia', name='home_incidencia'),
    url(r'^incidencia/registrar/estudiante/$', 'incidencia.views.incidencia_buscar_estudiante', name='incidencia_buscar_estudiante'),
    url(r'^incidencia/registrar/estudiante/([^/]+)/$', 'incidencia.views.incidencia_asignaturas_estudiante', name='incidencia_asignaturas_estudiante'),
	url(r'^incidencia/registrar/estudiante/([^/]+)/([^/]+)/$', 'incidencia.views.incidencia_registrar_estudiante', name='incidencia_registrar_estudiante'),

    url(r'^incidencia/registrar/curso/$', 'incidencia.views.incidencia_buscar_curso',
        name='incidencia_buscar_curso'),
	url(r'^incidencia/registrar/curso/([^/]+)/$', 'incidencia.views.incidencia_curso_materias',
        name='incidencia_curso_materias'),



    url(r'^estudiante/buscar/$', 'incidencia.views.busqueda', name='busqueda'),


    #url(r'^incidencia/registrar/curso/$', incidencia.views.incidencia_buscar_curso, name='incidencia_buscar_curso'),
    #url(r'^incidencia/registrar/curso/(?P<id>\d+)/$', incidencia.views.incidencia_registrar_curso, name='incidencia_registrar_curso'),
]
