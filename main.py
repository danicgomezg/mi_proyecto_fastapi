from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
import pandas as pd
import plotly.graph_objects as go
from jinja2 import Template

app = FastAPI()

# Cargar datos desde CSV
csv_path = "data.csv"  # Ruta del archivo CSV
final_df = pd.read_csv(csv_path, parse_dates=["Date"])

series_cols = ['DispoReal_kWh/d', 'Gene_kWh/d', 'CapEfecNeta_kWh/d']
filter_cols = ['Nombre Recurso', 'Combustible por Defecto', 'Municipio', 'Departamento',
               'Agente Representante', 'Estado Recurso', 'Tipo Generación', 'Clasificación', 'Tipo Despacho']

def generar_graficos(filtros, fecha_inicio, fecha_fin):
    filtro = pd.Series(True, index=final_df.index)
    for col, val in filtros.items():
        if val and val != "Todos":
            filtro &= (final_df[col] == val)
    
    filtro &= (final_df['Date'] >= fecha_inicio) & (final_df['Date'] <= fecha_fin)
    filtered_df = final_df[filtro]
    filtered_df = filtered_df.fillna(0)
    time_series = filtered_df.groupby('Date')[series_cols].sum().reset_index()
    time_series['Excedente de Energía'] = time_series['DispoReal_kWh/d'] - time_series['Gene_kWh/d']
    
    fig1 = go.Figure()
    colores = ['#1f77b4', '#ff7f0e', '#2ca02c']
    for i, col in enumerate(series_cols):
        fig1.add_trace(go.Scatter(x=time_series['Date'], y=time_series[col], mode='lines', name=col,
                                  line=dict(width=2, color=colores[i])))
    fig1_html = fig1.to_html(full_html=False, include_plotlyjs='cdn')
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=time_series['Date'], y=time_series['Excedente de Energía'], mode='lines',
                              name='Excedente de Energía', line=dict(width=2, color='#2ca02c')))
    fig2_html = fig2.to_html(full_html=False, include_plotlyjs=False)
    
    return fig1_html, fig2_html

@app.get("/", response_class=HTMLResponse)
def index():
    template = Template(open("template.html").read())
    return template.render(filtros={col: ['Todos'] + sorted(final_df[col].dropna().unique().tolist()) for col in filter_cols},
                           fechas=sorted(final_df['Date'].astype(str).unique()))

@app.post("/actualizar", response_class=HTMLResponse)
def actualizar(request: Request, 
               fecha_inicio: str = Form(...), fecha_fin: str = Form(...),
               **kwargs):
    filtros = {col: kwargs.get(col, "Todos") for col in filter_cols}
    fig1_html, fig2_html = generar_graficos(filtros, fecha_inicio, fecha_fin)
    return fig1_html + "<hr>" + fig2_html
