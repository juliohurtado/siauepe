# -*- coding: utf-8 -*-
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse, Http404
from django.template.context import RequestContext
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
import json

from django.contrib.auth.models import User, Group

from models import Incidencia

from estudiante.models import Estudiante, Matricula
from cursoasignaturaestudiante.models import CursoAsignaturaEstudiante
from periodo.models import Periodo
from cursoasignatura.models import CursoAsignatura
from inspector.models import Inspector
from cursoasignaturaestudiante.models import CursoAsignaturaEstudiante
from horario.models import Horario
from curso.models import Curso
from asignatura.models import Asignatura

import xlsxwriter
from xlsxwriter.utility import xl_range_abs

import locale

locale.setlocale(locale.LC_ALL, "")

#####################################
#####################################
'''
////////////////////////////////////
///Librería para generar reportes///
////////////////////////////////////
'''
#####################################
#####################################

from reportlab.platypus import Paragraph
from reportlab.platypus import Image
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4, A5, landscape, A6
from reportlab.lib import colors
from reportlab.platypus import Table
from reportlab.lib.fonts import tt2ps

from forms import incidenciaForm, EstudiantesForm, JustificarForm, IncidenciaDia, JustificarFechaForm
from django import forms

# Create your views here.

from django.contrib.auth.decorators import login_required

import datetime, time


@login_required()
def home_incidencia(request):
	groups = request.user.groups.all()
	for g in groups:
		if g.name == 'Inspectores':
			return render(request, 'incidencia/home_incidencia.html', {}, context_instance=RequestContext(request))
	return render(request, 'nopermisos.html', {'error': 'Módulo de Incidencias'},
				  context_instance=RequestContext(request))


def busqueda(request):
	if request.is_ajax():
		estudiante = Estudiante.objects.filter(apellido__istartswith=request.GET['nombre']).values('nombre', 'apellido',
																								   'id') | Estudiante.objects.filter(
			nombre__istartswith=request.GET['nombre']).values('nombre', 'apellido', 'id') | Estudiante.objects.filter(
			cedula__istartswith=request.GET['nombre']).values('nombre', 'apellido', 'id')
		return JsonResponse(list(estudiante), safe=False)
	return JsonResponse("Solo se permiten consultas mediante AJAX", safe=False)


@login_required()
def incidencia_buscar_estudiante(request):
	return render(request, 'incidencia/buscar_estudiante.html', {}, context_instance=RequestContext(request))


@login_required()
def incidencia_registrar_estudiante(request, id, id2):
	estudiante = get_object_or_404(Estudiante, id=id)
	asignaturaestudiante = get_object_or_404(CursoAsignaturaEstudiante, id=id2)
	asignatura = asignaturaestudiante.asignatura.asignatura
	p = Periodo.objects.get(activo=True)
	cA = CursoAsignatura.objects.filter(periodo=p)
	if request.method == 'POST':
		form = incidenciaForm(request.POST)
		if form.is_valid():
			inspector = get_object_or_404(Inspector, user=request.user)
			incidencia = form.save(commit=False)
			incidencia.revisado_por = inspector
			incidencia.asignaturaestudiante = asignaturaestudiante
			horarios = Horario.objects.filter(dia=incidencia.fecha.weekday(),
											  cursoasignatura=asignaturaestudiante.asignatura)
			if not (horarios.exists()):
				return render(request, 'incidencia/registrar.html',
							  {'form': form, 'estudiante': estudiante, 'asignatura': asignatura, 'horario': True},
							  context_instance=RequestContext(request))
			else:
				for horario in horarios:
					inc = Incidencia()
					inc.estado = incidencia.estado
					inc.justificacion = incidencia.justificacion
					inc.asignaturaestudiante = incidencia.asignaturaestudiante
					inc.fecha = incidencia.fecha
					inc.tipo = incidencia.tipo
					inc.revisado_por = incidencia.revisado_por
					inc.hora = horario
					try:
						inc.save()
					except:
						return render(request, 'incidencia/registrar.html',
									  {'form': form, 'estudiante': estudiante, 'duplicado': True,
									   'asignatura': incidencia.asignaturaestudiante.asignatura.asignatura},
									  context_instance=RequestContext(request))
			return HttpResponseRedirect(
				reverse('incidencia_asignaturas_estudiante', args=(id)) + "?incidencia=correcto", )
		# return render(request, 'index.html', {'form': form, 'estudiante': estudiante, 'ingresado': True}, context_instance=RequestContext(request))
	else:
		form = incidenciaForm()
	return render(request, 'incidencia/registrar.html',
				  {'form': form, 'estudiante': estudiante, 'asignatura': asignatura},
				  context_instance=RequestContext(request))


@login_required()
def incidencia_asignaturas_estudiante(request, id):
	estudiante = get_object_or_404(Estudiante, id=id)
	periodo = get_object_or_404(Periodo, activo=True)
	asignaturas = CursoAsignaturaEstudiante.objects.filter(estudiante=estudiante, asignatura__periodo=periodo)
	return render(request, 'incidencia/estudiante_materias.html',
				  {'asignaturas': asignaturas, 'estudiante': estudiante}, context_instance=RequestContext(request))


@login_required()
def incidencia_asignaturas_estudiante_dia(request, id):
	estudiante = get_object_or_404(Estudiante, id=id)
	periodo = get_object_or_404(Periodo, activo=True)
	cursoAsigEst = CursoAsignaturaEstudiante.objects.filter(estudiante=estudiante,
															asignatura__periodo=periodo).values_list('asignatura')
	inspector = Inspector.objects.get(user=request.user)
	if request.method == 'POST':
		form = IncidenciaDia(request.POST)

		fechaString = request.POST.get('fecha')
		fecha = datetime.datetime.strptime(fechaString, '%Y-%m-%d').date()
		horarios = Horario.objects.filter(cursoasignatura__in=cursoAsigEst, dia=fecha.weekday())
		incidenciasRegistradas = Incidencia.objects.filter(fecha=fecha, tipo="F",
														   asignaturaestudiante__estudiante=estudiante)
		if horarios.exists() and incidenciasRegistradas.count() <= 0:
			for horario in horarios:
				cae = CursoAsignaturaEstudiante.objects.filter(asignatura=horario.cursoasignatura,
															   estudiante=estudiante)
				for i in cae:
					incidencia = Incidencia()
					incidencia.fecha = fecha
					incidencia.tipo = 'F'
					incidencia.revisado_por = inspector
					incidencia.asignaturaestudiante = i
					incidencia.hora = horario
					incidencia.save()
		else:
			return render(request, 'incidencia/registrar_dia.html',
						  {'form': form, 'estudiante': estudiante, 'duplicado': True},
						  context_instance=RequestContext(request))
		return HttpResponseRedirect(reverse('incidencia_asignaturas_estudiante', args=(id)) + "?incidencia=correcto")

	else:
		form = IncidenciaDia()
	return render(request, 'incidencia/registrar_dia.html', {'form': form, 'estudiante': estudiante},
				  context_instance=RequestContext(request))


@login_required()
def incidencia_buscar_curso(request):
	periodo = get_object_or_404(Periodo, activo=True)
	cursoasignaturas = CursoAsignatura.objects.filter(periodo=periodo)

	aux = list()

	for ca in cursoasignaturas:
		aux.append(ca.curso.id)
	cursos = Curso.objects.filter(id__in=aux).order_by('nombre', )

	return render(request, 'incidencia/cursos_periodo.html', {'cursos': cursos},
				  context_instance=RequestContext(request))


@login_required()
def incidencia_curso_materias(request, id):
	curso = get_object_or_404(Curso, id=id)
	periodo = get_object_or_404(Periodo, activo=True)
	asignaturasValues = CursoAsignatura.objects.filter(periodo=periodo, curso=curso).values('asignatura')
	asignaturas = Asignatura.objects.filter(id__in=asignaturasValues).order_by('nombre')
	return render(request, 'incidencia/cursos_periodo_materias.html', {'asignaturas': asignaturas},
				  context_instance=RequestContext(request))


@login_required()
def incidencia_curso_estudiantes(request, id_curso, id_asignatura):
	periodo = get_object_or_404(Periodo, activo=True)
	asignatura = get_object_or_404(Asignatura, id=id_asignatura)
	curso = get_object_or_404(Curso, id=id_curso)
	cursoasignatura = get_object_or_404(CursoAsignatura, asignatura=asignatura, periodo=periodo, curso=curso)
	cursoestudiantes = CursoAsignaturaEstudiante.objects.filter(asignatura=cursoasignatura).values('estudiante_id')
	estudiantes = Estudiante.objects.filter(id__in=cursoestudiantes)
	inspector = Inspector.objects.get(user=request.user)
	if request.method == 'POST':
		form = EstudiantesForm(query=estudiantes, data=request.POST)

		fechaString = request.POST.get('fecha')

		fecha = datetime.datetime.strptime(fechaString, '%Y-%m-%d').date()

		seleccionados = request.POST.getlist('estudiantes')
		tipo = request.POST.get('tipo')
		if (fechaString == '') or (len(seleccionados) == 0):
			return render(request, 'incidencia/registrar.html', {'form': form, 'fecha': fecha, },
						  context_instance=RequestContext(request))
		horarios = Horario.objects.filter(dia=fecha.weekday(),
										  cursoasignatura=cursoasignatura)
		if not (Horario.objects.filter(dia=fecha.weekday(),
									   cursoasignatura=cursoasignatura).exists()):
			return render(request, 'incidencia/registrar.html',
						  {'form': form, 'horario': True,
						   'asignatura': cursoasignatura.asignatura},
						  context_instance=RequestContext(request))
		else:

			stdSelected = Estudiante.objects.filter(id__in=seleccionados)

			crsEST = CursoAsignaturaEstudiante.objects.filter(asignatura=cursoasignatura, estudiante__in=stdSelected)
			# return HttpResponse(crsEST.count())
			for crsE in crsEST:
				hrs = Horario.objects.filter(cursoasignatura=crsE.asignatura, dia=fecha.weekday())
				prueba = list()
				for h in hrs:
					# return HttpResponse(Incidencia.objects.filter(fecha = fecha, asignaturaestudiante=crsE, hora = h).exists())
					if not (Incidencia.objects.filter(fecha=fecha, asignaturaestudiante=crsE, hora=h).exists()):
						incidencia = Incidencia()
						incidencia.fecha = fecha
						incidencia.tipo = tipo
						incidencia.revisado_por = inspector
						incidencia.asignaturaestudiante = crsE
						incidencia.hora = h
						incidencia.save()
			return HttpResponseRedirect(reverse('incidencia_curso_materias', args=(id_curso)) + "?incidencia=correcto")
	else:
		form = EstudiantesForm(query=estudiantes)
	return render(request, 'incidencia/registrar_por_curso.html', {'form': form, 'curso': cursoasignatura},
				  context_instance=RequestContext(request))


@login_required()
def incidencia_justificar(request):
	return render(request, 'incidencia/justificar/buscar_estudiante.html', {},
				  context_instance=RequestContext(request))


@login_required()
def incidencia_justificar_estudiante(request, id_estudiante):
	now = datetime.datetime.now()
	if (now.weekday() == 0 or now.weekday() == 1):
		dias = datetime.timedelta(days=4)
	elif (now.weekday() == 6):
		dias = datetime.timedelta(days=3)
	else:
		dias = datetime.timedelta(days=2)

	estudiante = get_object_or_404(Estudiante, id=id_estudiante)
	incidencias = Incidencia.objects.filter(asignaturaestudiante__estudiante=estudiante, fecha__range=(now - dias, now),
											estado=False).order_by('asignaturaestudiante', 'fecha')

	return render(request, 'incidencia/justificar/incidencias.html',
				  {'estudiante': estudiante, 'incidencias': incidencias},
				  context_instance=RequestContext(request))


@login_required()
def incidencia_justificar_estudiante_incidencia(request, id_estudiante, id_incidencia):
	now = datetime.datetime.now()
	if (now.weekday() == 0 or now.weekday() == 1):
		dias = datetime.timedelta(days=4)
	elif (now.weekday() == 6):
		dias = datetime.timedelta(days=3)
	else:
		dias = datetime.timedelta(days=2)

	incidencia = get_object_or_404(Incidencia, fecha__range=(now - dias, now), id=id_incidencia, estado=False)
	estudiante = incidencia.asignaturaestudiante.estudiante
	asignatura = incidencia.asignaturaestudiante.asignatura.asignatura
	# horario = Horario.objects.get(cursoasignatura=incidencia.asignaturaestudiante.asignatura, dia=incidencia.fecha.weekday())

	if request.method == 'POST':
		form = JustificarForm(request.POST, instance=incidencia)
		if form.is_valid():
			incidencia = form.save(commit=False)
			incidencia.estado = True
			incidencia.save()

			estiloHoja = getSampleStyleSheet()
			cabecera = estiloHoja['Title']
			cabecera.pageBreakBefore = 0
			cabecera.keepWithNext = 0
			cabecera.textColor = colors.red
			estilo = estiloHoja['BodyText']

			salto = Spacer(0, 10)

			pagina = []

			pagina.append(salto)
			pagina.append(Paragraph("Unidad Educativa Particular Emanuel", cabecera))

			cabecera.textColor = colors.black
			pagina.append(Paragraph("" + "Justificación", cabecera))
			pagina.append(salto)
			pagina.append(salto)

			pagina.append(Paragraph("Estudiante: " + estudiante.nombre + " " + estudiante.apellido, estilo))
			pagina.append(Paragraph("Fecha: " + incidencia.fecha.strftime('%m/%d/%Y'), estilo))
			pagina.append(Paragraph("Hora: " + incidencia.hora.get_hora_display(), estilo))
			pagina.append(Paragraph("Asignatura: " + asignatura.nombre, estilo))

			estilo.fontName = tt2ps('Times-Roman', 1, 0)

			pagina.append(Paragraph("" + "Justificación: ", estilo))
			estilo.fontName = tt2ps('Times-Roman', 0, 0)
			pagina.append(Paragraph("" + incidencia.justificacion, estilo))
			pagina.append(salto)
			pagina.append(salto)
			pagina.append(salto)
			pagina.append(salto)

			pagina.append(Paragraph("" + estudiante.representante.nombres_completos(), estilo))
			estilo.fontName = tt2ps('Times-Roman', 1, 0)
			pagina.append(Paragraph("REPRESENTANTE", estilo))
			pagina.append(salto)
			pagina.append(salto)
			pagina.append(salto)
			estilo.fontName = tt2ps('Times-Roman', 0, 0)
			pagina.append(Paragraph(incidencia.revisado_por.user.get_full_name(), estilo))
			estilo.fontName = tt2ps('Times-Roman', 1, 0)
			pagina.append(Paragraph("INSPECTOR", estilo))
			nombreArchivo = "justificante-" + incidencia.fecha.strftime('%m-%d-%Y') + ".pdf"
			documento = SimpleDocTemplate(nombreArchivo, pagesize=A6, showBoundary=1, displayDocTitle=1, leftMargin=2,
										  rightMargin=2, topMargin=2, bottomMargin=2, title="Justificante")

			documento.build(pagina)

			salida = open(nombreArchivo)
			response = HttpResponse(salida, content_type='application/pdf')
			response['Content-Disposition'] = 'inline; filename=' + nombreArchivo
			return response

		# return HttpResponseRedirect(reverse('incidencia_justificar_estudiante', args=(estudiante.id,))+"?mensaje=correcto")
	else:
		form = JustificarForm(instance=incidencia)

	return render(request, 'incidencia/justificar/justificar.html',
				  {'form': form, 'estudiante': estudiante, 'asignatura': asignatura, 'incidencia': incidencia},
				  context_instance=RequestContext(request))


@login_required()
def incidencia_justificar_estudiante_fecha(request, id_estudiante):
	# incidencia = get_object_or_404(Incidencia, fecha__range=(now-dias, now), id=id_incidencia, estado=False)
	estudiante = get_object_or_404(Estudiante, id=id_estudiante)
	inspector = Inspector.objects.get(user=request.user)
	# asignatura = incidencia.asignaturaestudiante.asignatura.asignatura
	# horario = Horario.objects.get(cursoasignatura=incidencia.asignaturaestudiante.asignatura, dia=incidencia.fecha.weekday())
	if request.method == 'POST':
		form = JustificarFechaForm(request.POST)
		if form.is_valid():
			inicioString = request.POST.get('fecha_inicio')
			finString = request.POST.get('fecha_fin')
			justificacion = request.POST.get('justificacion')

			fechaInicio = datetime.datetime.strptime(inicioString, '%Y-%m-%d').date()

			fechaFin = datetime.datetime.strptime(finString, '%Y-%m-%d').date()

			incidencias = Incidencia.objects.filter(fecha__in=(fechaInicio, fechaFin), estado=False)

			if not incidencias.exists():
				return render(request, 'incidencia/justificar/justificar_fecha.html',
							  {'form': form, 'estudiante': estudiante, 'estado': False},
							  context_instance=RequestContext(request))

			for incidencia in incidencias:
				incidencia.justificacion = justificacion
				incidencia.estado = True
				incidencia.revisado_por = inspector
				incidencia.save()

			estiloHoja = getSampleStyleSheet()
			cabecera = estiloHoja['Title']
			cabecera.pageBreakBefore = 0
			cabecera.keepWithNext = 0
			cabecera.textColor = colors.red
			estilo = estiloHoja['BodyText']

			salto = Spacer(0, 10)

			pagina = []

			pagina.append(salto)
			pagina.append(Paragraph("Unidad Educativa Particular Emanuel", cabecera))

			cabecera.textColor = colors.black
			pagina.append(Paragraph("" + "Justificación", cabecera))
			pagina.append(salto)
			pagina.append(salto)

			pagina.append(Paragraph("Estudiante: " + estudiante.nombre + " " + estudiante.apellido, estilo))

			fecha1 = fechaInicio.strftime("%A %d de %B del %Y %Z")
			fecha2 = fechaFin.strftime("%A %d de %B del %Y %Z")

			pagina.append(Paragraph("Fecha de Inicio: " + fecha1, estilo))
			pagina.append(Paragraph("Fecha de Final: " + fecha2, estilo))

			estilo.fontName = tt2ps('Times-Roman', 1, 0)

			pagina.append(Paragraph("" + "Justificación: ", estilo))
			estilo.fontName = tt2ps('Times-Roman', 0, 0)
			pagina.append(Paragraph("" + justificacion, estilo))
			pagina.append(salto)
			pagina.append(salto)
			pagina.append(salto)
			pagina.append(salto)

			pagina.append(Paragraph("" + estudiante.representante.nombres_completos(), estilo))
			estilo.fontName = tt2ps('Times-Roman', 1, 0)
			pagina.append(Paragraph("REPRESENTANTE", estilo))
			pagina.append(salto)
			pagina.append(salto)
			pagina.append(salto)
			estilo.fontName = tt2ps('Times-Roman', 0, 0)
			pagina.append(Paragraph(request.user.get_full_name(), estilo))
			estilo.fontName = tt2ps('Times-Roman', 1, 0)
			pagina.append(Paragraph("INSPECTOR", estilo))
			nombreArchivo = "justificante.pdf"
			documento = SimpleDocTemplate(nombreArchivo, pagesize=A6, showBoundary=1, displayDocTitle=1, leftMargin=2,
										  rightMargin=2, topMargin=2, bottomMargin=2, title="Justificante")

			documento.build(pagina)

			salida = open(nombreArchivo)
			response = HttpResponse(salida, content_type='application/pdf')
			response['Content-Disposition'] = 'inline; filename=' + nombreArchivo
			return response

		# return HttpResponseRedirect(reverse('incidencia_justificar_estudiante', args=(estudiante.id,))+"?mensaje=correcto")
	else:
		form = JustificarFechaForm()

	return render(request, 'incidencia/justificar/justificar_fecha.html',
				  {'form': form, 'estudiante': estudiante, },
				  context_instance=RequestContext(request))


@login_required()
def matricular(request):
	''
	periodo = get_object_or_404(Periodo, activo=True)
	matriculas = Matricula.objects.all()
	for m in matriculas:
		asignaturas = CursoAsignatura.objects.filter(curso=m.curso, periodo=periodo)
		for a in asignaturas:
			if not CursoAsignaturaEstudiante.objects.filter(asignatura=a, estudiante=m.estudiante).exists():
				cae = CursoAsignaturaEstudiante()
				cae.asignatura = a
				cae.estudiante = m.estudiante
				cae.save()

	return HttpResponse("Correcto, mostrar mensaje")


@login_required()
def reporte_index(request):
	return render(request, 'reportes/index.html', {},
				  context_instance=RequestContext(request))


@login_required()
def reporte_cursos(request):
	periodo = Periodo.objects.get(activo=True)
	cursoasignatura = CursoAsignatura.objects.filter(periodo=periodo).values_list('curso')
	cursos = Curso.objects.filter(id__in=cursoasignatura).order_by('especialidad')
	return render(request, 'reportes/ver_cursos.html', {'cursos': cursos},
				  context_instance=RequestContext(request))


@login_required()
def reporte_cursos_xls(request, curso):
	periodo = Periodo.objects.get(activo=True)
	curso = get_object_or_404(Curso, id=curso)

	cursoasignaturaestudiante = CursoAsignaturaEstudiante.objects.filter(asignatura__curso=curso,
																		 asignatura__periodo=periodo).order_by(
		'asignatura')

	asignaturas = Asignatura.objects.filter(id__in=cursoasignaturaestudiante.values_list('asignatura__asignatura'))

	# estudiantes = Estudiante.objects.filter(id__in=cursoasignaturaestudiante.values_list('estudiante'))

	filename = 'reporte-curso.xls'

	wb = xlsxwriter.Workbook(filename)
	reporte = wb.add_worksheet('Reporte Curso')
	reporte.set_column(0, 0, 35)
	reporte.set_column(1, 0, 35)
	reporte.set_column(2, 0, 25)
	reporte.set_column(3, 0, 25)
	reporte.set_column(4, 0, 25)
	reporte.set_column(5, 0, 25)
	num_format = wb.add_format({
		'num_format': '0',
		'align': 'right',
		'font_size': 12,

	})
	formato_negrita = wb.add_format({
		'bold': True,
		'align': 'center'
	})
	general_format = wb.add_format({
		'align': 'left',
		'font_size': 12,
	})

	filaInicio = 0
	reporte.merge_range(filaInicio, 0, filaInicio, 4, "UNIDAD EDUCATIVA PARTICULAR EMANUEL", formato_negrita)

	filaInicio += 2
	reporte.merge_range(filaInicio, 0, filaInicio, 4,
						"Reporte " + curso.nombre + " de " + curso.especialidad.nombre + " paralelo " + curso.paralelo,
						formato_negrita)

	filaInicio += 2
	reporte.write(filaInicio, 0, "Asignaturas", formato_negrita)
	reporte.write(filaInicio, 1, "Cantidad de Atrasos", formato_negrita)
	reporte.write(filaInicio, 2, "Horas Totales", formato_negrita)
	reporte.write(filaInicio, 3, u'Número de Estudiantes', formato_negrita)

	reporte.write(filaInicio, 4, "Cantidad de Faltas", formato_negrita)

	reporte.write(filaInicio, 5, "Horas Recibidas", formato_negrita)
	#reporte.write(filaInicio, 5, "Porcentajes de Faltas", formato_negrita)
	filaInicio += 1
	aux = filaInicio
	for a in asignaturas:
		cursoasig = cursoasignaturaestudiante.filter(asignatura__asignatura=a)

		ca = CursoAsignatura.objects.get(asignatura=a, curso=curso, periodo=periodo)

		estudiantes = cursoasignaturaestudiante.filter(asignatura__asignatura=a).values_list('estudiante')

		faltas = Incidencia.objects.filter(asignaturaestudiante__in=cursoasig, tipo="F")
		atrasos = Incidencia.objects.filter(asignaturaestudiante__in=cursoasig, tipo="A")
		horas_semana = Horario.objects.filter(cursoasignatura=ca, hora='1')
		cantidad_de_semanas = ((datetime.datetime.now().date() - periodo.inicio).days) / 7
		horas_reporte = horas_semana.count() * cantidad_de_semanas
		reporte.write(filaInicio, 0, a.nombre)
		reporte.write_number(filaInicio, 1, atrasos.count())
		reporte.write(filaInicio, 2, ca.numero_horas)
		reporte.write(filaInicio, 3, estudiantes.count())
		reporte.write(filaInicio, 4, faltas.count())

		reporte.write_number(filaInicio, 5, horas_reporte)
		columna_formula = "G" + str(filaInicio+1)
		if horas_reporte == 0:
			valor = 0
		else:
			valor = atrasos.count() * (100/horas_reporte)
		reporte.write(columna_formula, valor)

		filaInicio += 1

	chart = wb.add_chart({'type': 'pie'})
	chart.title_name = 'Atrasos'
	chart.width = reporte._size_col(0)
	#values = '=%s!%s' % (reporte.name, xl_range_abs(aux, 1, aux + asignaturas.count(), 1))
	values = [reporte.name, aux, 1, aux + asignaturas.count()-1, 1]
	#categories = '=%s!%s' % (reporte.name, xl_range_abs(aux, 0, aux + asignaturas.count(), 0))
	categories = [reporte.name, aux, 0, aux + asignaturas.count()-1, 0]
	chart.add_series({'values': values, 'categories': categories, 'smooth': True})
	reporte.insert_chart(filaInicio + 4, 0, chart)

	chartBarras = wb.add_chart({'type': 'column'})
	chartBarras.title_name = 'Atrasos'
	chartBarras.width = reporte._size_col(0)
	chartBarras.add_series({'values': values, 'categories': categories, 'smooth': True})
	reporte.insert_chart(filaInicio + 4, 2, chartBarras)

	wb.close()
	output = open(filename)
	nombre = 'attachment; filename=' + filename
	# return HttpResponse(filename)
	response = HttpResponse(output, content_type="application/ms-excel")
	response['Content-Disposition'] = nombre
	return response


@login_required()
def reporte_estudiante_buscar(request):
	return render(request, 'reportes/buscar_estudiante.html', {}, context_instance=RequestContext(request))
from decimal import Decimal
@login_required()
def reporte_estudiante(request, id_estudiante):
	estudiante = get_object_or_404(Estudiante, id = id_estudiante)
	periodo = get_object_or_404(Periodo, activo = True)
	cae = CursoAsignaturaEstudiante.objects.filter(estudiante = estudiante, asignatura__periodo = periodo)
	ca = CursoAsignatura.objects.filter(id__in = cae.values('asignatura__id'))
	#asignaturas = Asignatura.objects.filter(id__in= ca.values('asignatura__id'))
	reporte = list()
	for a in cae:
		incidencias = Incidencia.objects.filter(asignaturaestudiante = a, estado = False)
		horas = a.asignatura.numero_horas
		porcentaje_faltas = format((float(100)*float(incidencias.count()))/float(horas), '.2f')

		# horas = 100%
		# faltas = ?
		valor = (a.asignatura.asignatura.nombre, horas, incidencias.count(), porcentaje_faltas)

		reporte.append(valor)

	return render(request, 'reportes/listar.html',
				  {'estudiante': estudiante, 'asignaturas': reporte},
				  context_instance=RequestContext(request))




	return render(request, 'reportes/buscar_estudiante.html', {}, context_instance=RequestContext(request))