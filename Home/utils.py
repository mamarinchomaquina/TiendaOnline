from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from io import BytesIO
from datetime import datetime


def generar_factura_pdf(venta):
    """
    Genera un PDF de factura profesional
    
    Args:
        venta: Diccionario con datos de la venta
    
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elementos = []
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para el título
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Estilo para subtítulos
    subtitulo_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#3b82f6'),
        spaceAfter=12
    )
    
    # ==========================================
    # ENCABEZADO
    # ==========================================
    
    titulo = Paragraph("🛒 TIENDAONLINE", titulo_style)
    elementos.append(titulo)
    
    subtitulo = Paragraph("FACTURA DE VENTA", subtitulo_style)
    elementos.append(subtitulo)
    elementos.append(Spacer(1, 0.2*inch))
    
    # ==========================================
    # INFORMACIÓN DE LA FACTURA
    # ==========================================
    
    info_factura = [
        ['Número de Factura:', venta['numero_factura']],
        ['Fecha:', venta['fecha_venta'].strftime('%d/%m/%Y %H:%M')],
        ['Estado:', venta['estado'].upper()],
        ['Método de Pago:', venta['metodo_pago']]
    ]
    
    tabla_info = Table(info_factura, colWidths=[2*inch, 4*inch])
    tabla_info.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    elementos.append(tabla_info)
    elementos.append(Spacer(1, 0.3*inch))
    
    # ==========================================
    # INFORMACIÓN DEL CLIENTE
    # ==========================================
    
    cliente_titulo = Paragraph("<b>DATOS DEL CLIENTE</b>", subtitulo_style)
    elementos.append(cliente_titulo)
    
    info_cliente = [
        ['Nombre:', venta['usuario_nombre']],
        ['Email:', venta['usuario_email']]
    ]
    
    tabla_cliente = Table(info_cliente, colWidths=[2*inch, 4*inch])
    tabla_cliente.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    elementos.append(tabla_cliente)
    elementos.append(Spacer(1, 0.3*inch))
    
    # ==========================================
    # DETALLE DE PRODUCTOS
    # ==========================================
    
    productos_titulo = Paragraph("<b>DETALLE DE PRODUCTOS</b>", subtitulo_style)
    elementos.append(productos_titulo)
    
    # Encabezados de la tabla
    datos_productos = [
        ['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']
    ]
    
    # Agregar productos
    for producto in venta['productos']:
        datos_productos.append([
            producto['nombre'],
            str(producto['cantidad']),
            f"${producto['precio_unitario']:,.2f}",
            f"${producto['subtotal']:,.2f}"
        ])
    
    tabla_productos = Table(datos_productos, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    tabla_productos.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Cuerpo
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        
        # Bordes
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2563eb'))
    ]))
    
    elementos.append(tabla_productos)
    elementos.append(Spacer(1, 0.3*inch))
    
    # ==========================================
    # TOTALES
    # ==========================================
    
    datos_totales = [
        ['', '', 'Subtotal:', f"${venta['subtotal']:,.2f}"],
        ['', '', 'Impuesto (16%):', f"${venta['impuesto']:,.2f}"],
        ['', '', 'TOTAL:', f"${venta['total']:,.2f}"]
    ]
    
    tabla_totales = Table(datos_totales, colWidths=[3*inch, 1*inch, 1.5*inch, 1.5*inch])
    tabla_totales.setStyle(TableStyle([
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (2, 0), (-1, -1), 11),
        ('LINEABOVE', (2, 2), (-1, 2), 2, colors.HexColor('#2563eb')),
        ('BACKGROUND', (2, 2), (-1, 2), colors.HexColor('#dbeafe')),
        ('TEXTCOLOR', (2, 2), (-1, 2), colors.HexColor('#2563eb')),
        ('FONTSIZE', (2, 2), (-1, 2), 14),
        ('FONTNAME', (2, 2), (-1, 2), 'Helvetica-Bold'),
        ('TOPPADDING', (2, 2), (-1, 2), 12),
        ('BOTTOMPADDING', (2, 2), (-1, 2), 12),
    ]))
    
    elementos.append(tabla_totales)
    elementos.append(Spacer(1, 0.5*inch))
    
    # ==========================================
    # NOTAS
    # ==========================================
    
    if venta.get('notas'):
        notas_titulo = Paragraph("<b>NOTAS:</b>", subtitulo_style)
        elementos.append(notas_titulo)
        notas_texto = Paragraph(venta['notas'], styles['Normal'])
        elementos.append(notas_texto)
        elementos.append(Spacer(1, 0.3*inch))
    
    # ==========================================
    # PIE DE PÁGINA
    # ==========================================
    
    pie_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    
    pie = Paragraph(
        "Gracias por su compra | TiendaOnline © 2025 | www.tiendaonline.com",
        pie_style
    )
    elementos.append(pie)
    
    # Construir PDF
    doc.build(elementos)
    
    buffer.seek(0)
    return buffer


def generar_reporte_ventas_pdf(ventas, fecha_inicio=None, fecha_fin=None):
    """
    Genera un PDF de reporte de ventas
    
    Args:
        ventas: Lista de ventas
        fecha_inicio: Fecha de inicio del reporte
        fecha_fin: Fecha de fin del reporte
    
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elementos = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    subtitulo_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#3b82f6'),
        spaceAfter=10
    )
    
    # ==========================================
    # ENCABEZADO
    # ==========================================
    
    titulo = Paragraph("📊 REPORTE DE VENTAS", titulo_style)
    elementos.append(titulo)
    
    # Período
    if fecha_inicio and fecha_fin:
        periodo = f"Período: {fecha_inicio} - {fecha_fin}"
    elif fecha_inicio:
        periodo = f"Desde: {fecha_inicio}"
    elif fecha_fin:
        periodo = f"Hasta: {fecha_fin}"
    else:
        periodo = "Todas las ventas"
    
    periodo_p = Paragraph(periodo, subtitulo_style)
    elementos.append(periodo_p)
    
    fecha_generacion = Paragraph(
        f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        styles['Normal']
    )
    elementos.append(fecha_generacion)
    elementos.append(Spacer(1, 0.3*inch))
    
    # ==========================================
    # ESTADÍSTICAS GENERALES
    # ==========================================
    
    total_ventas = len(ventas)
    total_ingresos = sum(float(v['total']) for v in ventas)
    promedio_venta = total_ingresos / total_ventas if total_ventas > 0 else 0
    
    estadisticas = [
        ['Total de Ventas:', str(total_ventas)],
        ['Ingresos Totales:', f"${total_ingresos:,.2f}"],
        ['Promedio por Venta:', f"${promedio_venta:,.2f}"]
    ]
    
    tabla_stats = Table(estadisticas, colWidths=[3*inch, 2*inch])
    tabla_stats.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    elementos.append(tabla_stats)
    elementos.append(Spacer(1, 0.3*inch))
    
    # ==========================================
    # LISTADO DE VENTAS
    # ==========================================
    
    ventas_titulo = Paragraph("<b>DETALLE DE VENTAS</b>", subtitulo_style)
    elementos.append(ventas_titulo)
    
    # Encabezados
    datos_ventas = [
        ['Factura', 'Fecha', 'Cliente', 'Total', 'Estado']
    ]
    
    # Agregar ventas (limitar a 50)
    for venta in ventas[:50]:
        datos_ventas.append([
            venta['numero_factura'],
            venta['fecha_venta'].strftime('%d/%m/%Y'),
            venta['usuario_nombre'][:25],
            f"${venta['total']:,.2f}",
            venta['estado']
        ])
    
    tabla_ventas = Table(datos_ventas, colWidths=[1.5*inch, 1.2*inch, 2*inch, 1*inch, 1*inch])
    tabla_ventas.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        
        # Cuerpo
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        
        # Bordes
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2563eb'))
    ]))
    
    elementos.append(tabla_ventas)
    
    if len(ventas) > 50:
        nota = Paragraph(
            f"<i>Nota: Se muestran las primeras 50 ventas de {len(ventas)} totales</i>",
            styles['Normal']
        )
        elementos.append(Spacer(1, 0.2*inch))
        elementos.append(nota)
    
    # Construir PDF
    doc.build(elementos)
    
    buffer.seek(0)
    return buffer