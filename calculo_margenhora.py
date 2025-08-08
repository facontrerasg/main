# -*- coding: utf-8 -*-
"""
Created on Thu Aug  7 17:32:59 2025

@author: facontreras
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.graph_objects as go
import time

# Definir la tabla de parámetros
if 'parametros_df' not in st.session_state:
    st.session_state.parametros_df = pd.DataFrame({
        'Planta': ['Chillán', 'Chillán', 'Chillán', 'Chillán', 'Guadalajara', 'Guadalajara', 'Guadalajara', 'Guadalajara', 'Guadalajara', 'Guadalajara', 'Irapuato', 'Irapuato'],
        'Línea': ['L4', 'L1', 'L3', 'L5', 'L1', 'L2', 'L3', 'L4', 'L5', 'L6', 'L1', 'L2'],
        'Velocidad': [180.95,147.88,141.31,116.21, 90.41 , 113.01, 93.42, 89.68,198.46,198.34 , 124.6 , 63.56],  # Valores de ejemplo, ajustar si es necesario
        'Tiempo de Setup': [0.8 ,1.08 , 1.02 ,1.08 ,3.23,3.17,3.17,3.15,3.13,3.12,2.34 ,2.6] # Valores de ejemplo, ajustar si es necesario
    })

def calcular_margen_hora(margen_unitario, velocidad, tiempo_setup, tamano_lote):
    """
    Calcula el margen hora según la fórmula proporcionada.  
    """
    try:
        if velocidad == 0 or tamano_lote == 0:
            return 0
        
        parte1 = 1 / (60 * velocidad)
        parte2 = tiempo_setup / tamano_lote
        
        if (parte1 + parte2) == 0:
            return 0
            
        resultado = (1 / (parte1 + parte2)) * (margen_unitario / 1000)
        return resultado

    except ZeroDivisionError:
        return 0
    except Exception as e:
        st.error(f"Ocurrió un error: {e}")
        return 0

# --- Lógica de inicialización de estado ---
def inicializar_parametros_por_planta(planta, lineas):
    """Inicializa los parámetros base y los ajustados para cada planta y línea."""
    for linea in lineas:
        if f'base_velocidad_{planta}_{linea}' not in st.session_state:
            parametros = st.session_state.parametros_df[(st.session_state.parametros_df['Planta'] == planta) & (st.session_state.parametros_df['Línea'] == linea)].iloc[0]
            st.session_state[f'base_velocidad_{planta}_{linea}'] = float(parametros['Velocidad'])
            st.session_state[f'base_tiempo_setup_{planta}_{linea}'] = float(parametros['Tiempo de Setup'])
            st.session_state[f'ajustada_velocidad_{planta}_{linea}'] = float(parametros['Velocidad'])
            st.session_state[f'ajustada_tiempo_setup_{planta}_{linea}'] = float(parametros['Tiempo de Setup'])

def actualizar_velocidad_por_planta(planta, linea):
    """Actualiza la velocidad ajustada al mover el slider para una planta específica."""
    porcentaje = st.session_state[f'slider_velocidad_{planta}_{linea}']
    valor_base = st.session_state[f'base_velocidad_{planta}_{linea}']
    st.session_state[f'ajustada_velocidad_{planta}_{linea}'] = valor_base * (1 + porcentaje / 100)

def actualizar_tiempo_setup_por_planta(planta, linea):
    """Actualiza el tiempo de setup ajustado al mover el slider para una planta específica."""
    porcentaje = st.session_state[f'slider_setup_{planta}_{linea}']
    valor_base = st.session_state[f'base_tiempo_setup_{planta}_{linea}']
    st.session_state[f'ajustada_tiempo_setup_{planta}_{linea}'] = valor_base * (1 + porcentaje / 100)

# --- Interfaz de Streamlit ---
st.title('💰 Calculadora de Margen Hora')
st.markdown("""
Esta aplicación te ayuda a calcular el **margen por hora** y a visualizar cómo varía con el margen unitario.
""")

st.subheader("📊 Tabla de Parámetros Líneas")
st.dataframe(
    st.session_state.parametros_df,
    hide_index=True,
    column_config={
        'Planta': st.column_config.TextColumn('Planta', help='🌍 Planta de producción', width='small'),
        'Línea': st.column_config.TextColumn('Línea', help='🏭 Línea de producción', width='small'),
        'Velocidad': st.column_config.NumberColumn('Velocidad (sacos/min)', help='🚀 Velocidad de producción en sacos por minuto', format='%d'),
        'Tiempo de Setup': st.column_config.NumberColumn('Tiempo de Setup (sacos/min)', help='⏱️ Tiempo de cambio de formato', format='%d')
    }
)

st.header('Datos de Producción y Selección')
plantas_disponibles = st.session_state.parametros_df['Planta'].unique().tolist()
plantas_seleccionadas = st.multiselect(
    "Selecciona una o más plantas:",
    plantas_disponibles,
    default=plantas_disponibles[0] if plantas_disponibles else [],
    key='plantas_seleccionadas'
)

if plantas_seleccionadas:
    input_cols = st.columns(len(plantas_seleccionadas))
    lineas_por_planta = {}

    for i, planta in enumerate(plantas_seleccionadas):
        with input_cols[i]:
            st.markdown(f"**Planta: {planta}**")
            lineas_disponibles = st.session_state.parametros_df[st.session_state.parametros_df['Planta'] == planta]['Línea'].tolist()
            
            lineas_seleccionadas = st.multiselect(
                f"Líneas para {planta}:",
                options=lineas_disponibles,
                default=lineas_disponibles[0] if lineas_disponibles else [],
                key=f'lineas_seleccionadas_{planta}'
            )
            lineas_por_planta[planta] = lineas_seleccionadas
            
            if lineas_seleccionadas:
                inicializar_parametros_por_planta(planta, lineas_seleccionadas)

            for linea in lineas_seleccionadas:
                st.markdown(f"***Línea {linea}***")
                st.number_input(
                    f'Velocidad (Unidades/min):', 
                    min_value=0.0, 
                    value=st.session_state[f'ajustada_velocidad_{planta}_{linea}'],
                    key=f'velocidad_input_{planta}_{linea}'
                )
                st.slider(
                    'Mejora Velocidad %', 
                    min_value=0, max_value=100, value=0, step=1,
                    key=f'slider_velocidad_{planta}_{linea}',
                    on_change=actualizar_velocidad_por_planta, args=(planta, linea,)
                )
                st.number_input(
                    f'Tiempo de Setup (min):', 
                    min_value=0.0, 
                    value=st.session_state[f'ajustada_tiempo_setup_{planta}_{linea}'],
                    key=f'tiempo_setup_input_{planta}_{linea}'
                )
                st.slider(
                    'Reducción Setup %', 
                    min_value=-100, max_value=0, value=0, step=1,
                    key=f'slider_setup_{planta}_{linea}',
                    on_change=actualizar_tiempo_setup_por_planta, args=(planta, linea,)
                )
                st.markdown("---")
# Destacar las cajas de entrada de datos
st.markdown("### ✍️ **Valores de Entrada Principales**")
with st.container(border=True):
    margen_unitario_actual = st.number_input('Margen Unitario (USD/Mscs):', min_value=0.0, value=1000.0, format="%.2f")
    tamano_lote_actual = st.number_input('Tamaño de Lote:', min_value=0.0, value=500.0, format="%.2f")

st.subheader("Configuración de Variación para el Gráfico")
porcentaje_variacion_velocidad = st.slider('Variación de Velocidad % (+/-)', min_value=0, max_value=100, value=0, step=1)
porcentaje_variacion_setup = st.slider('Variación de Tiempo de Setup % (+/-)', min_value=0, max_value=100, value=0, step=1)

# --- Botón para calcular y mostrar resultados ---
if st.button('Calcular y Graficar Margen'):
    if not plantas_seleccionadas:
        st.warning("Por favor, selecciona al menos una planta.")
    else:
        st.markdown("---")
        barra_progreso = st.progress(0, text="Calculando...")
        fig = go.Figure()
        fig_tamano_lote = go.Figure()

        datos_descarga = pd.DataFrame()
        total_lineas_a_procesar = sum(len(lineas) for lineas in lineas_por_planta.values())
        lineas_procesadas = 0

        for planta in plantas_seleccionadas:
            for linea in lineas_por_planta.get(planta, []):
                velocidad_final = st.session_state[f'ajustada_velocidad_{planta}_{linea}']
                tiempo_setup_final = st.session_state[f'ajustada_tiempo_setup_{planta}_{linea}']
                margen_calculado = calcular_margen_hora(margen_unitario_actual, velocidad_final, tiempo_setup_final, tamano_lote_actual)
                
                            
                
                if planta == 'Chillán':
                    descuento = 317.26
                    margen_nivel_2 = margen_calculado - descuento
                else:
                    descuento = 295.29
                    margen_nivel_2 = margen_calculado - descuento
                
                # Definir el color según el valor de margen_nivel_2
                color_margen_nivel_1 = 'red' if margen_calculado < 0 else '#0077b6'

                color_margen_nivel_2 = 'red' if margen_nivel_2 < 0 else '#0077b6'
                
                st.subheader(f'Resultados para {planta} - Línea {linea}')
                
                col1_res, col2_res, col3_res = st.columns([1, 0.2, 1])
                with col1_res:
                    st.markdown(f"#### Margen Hora - Contr")
                    st.markdown(f"## <span style='color:{color_margen_nivel_1};'>**${margen_calculado:,.2f}**</span>", unsafe_allow_html=True)
                with col2_res:
                    st.markdown(f"<br><br><br>👉", unsafe_allow_html=True)
                with col3_res:
                    st.markdown(f"#### Margen Hora - Ebitda")
                    st.markdown(f"## <span style='color:{color_margen_nivel_2};'>**${margen_nivel_2:,.2f}**</span>", unsafe_allow_html=True)
                
             #   st.info(f"**Costo Fijo Descontado:** ${descuento:,.2f}")
                st.markdown("---")
                
                margenes_unitarios = np.linspace(margen_unitario_actual * 0.5, margen_unitario_actual * 1.5, 50)
                velocidad_min = velocidad_final * (1 - porcentaje_variacion_velocidad / 100)
                velocidad_max = velocidad_final * (1 + porcentaje_variacion_velocidad / 100)
                setup_min = tiempo_setup_final * (1 - porcentaje_variacion_setup / 100)
                setup_max = tiempo_setup_final * (1 + porcentaje_variacion_setup / 100)
                
                # Calcular los rangos del gráfico en base al Margen Nivel 2
                margen_hora_nivel2_min = [calcular_margen_hora(mu, velocidad_min, setup_max, tamano_lote_actual) - descuento for mu in margenes_unitarios]
                margen_hora_nivel2_max = [calcular_margen_hora(mu, velocidad_max, setup_min, tamano_lote_actual) - descuento for mu in margenes_unitarios]
                margen_hora_nivel2_centro = [calcular_margen_hora(mu, velocidad_final, tiempo_setup_final, tamano_lote_actual) - descuento for mu in margenes_unitarios]

                  # --- Generar datos para el nuevo gráfico de Tamaño de Lote ---
                tamanos_lote = np.linspace(tamano_lote_actual * 0.5, tamano_lote_actual * 4, 50)

                margen_hora_nivel2_min_lote = [calcular_margen_hora(margen_unitario_actual, velocidad_min, setup_max, tl) - descuento for tl in tamanos_lote]
                margen_hora_nivel2_max_lote = [calcular_margen_hora(margen_unitario_actual, velocidad_max, setup_min, tl) - descuento for tl in tamanos_lote]
                margen_hora_nivel2_centro_lote = [calcular_margen_hora(margen_unitario_actual, velocidad_final, tiempo_setup_final, tl) - descuento for tl in tamanos_lote]

               

                df_linea = pd.DataFrame({
                    'Planta': [planta] * len(margenes_unitarios),
                    'Línea': [linea] * len(margenes_unitarios),
                    'Margen Unitario ($)': margenes_unitarios,
                    'Margen Hora  (vs Margen Unitario)': margen_hora_nivel2_centro,
                    'Margen Hora  Min (vs Margen Unitario)': margen_hora_nivel2_min,
                    'Margen Hora Max (vs Margen Unitario)': margen_hora_nivel2_max,
                    'Tamaño de Lote (Proyección)': tamanos_lote,
                    'Margen Hora (vs Tamaño de Lote)': margen_hora_nivel2_centro_lote,
                    'Margen Hora  (vs Tamaño de Lote)': margen_hora_nivel2_min_lote,
                    'Margen Hora  (vs Tamaño de Lote)': margen_hora_nivel2_max_lote
                })
                
                datos_descarga = pd.concat([datos_descarga, df_linea], ignore_index=True)

                fig.add_trace(go.Scatter(x=list(margenes_unitarios) + list(margenes_unitarios[::-1]), y=list(margen_hora_nivel2_max) + list(margen_hora_nivel2_min[::-1]), fill='toself', fillcolor='rgba(0,100,80,0.2)', line_color='rgba(255,255,255,0)', name=f'Rango de Variación - {planta} - {linea}'))
                fig.add_trace(go.Scatter(x=margenes_unitarios, y=margen_hora_nivel2_centro, mode='lines', name=f'Proyección Margen hora - {planta} - {linea}'))
                
                margen_nivel_2_actual = calcular_margen_hora(margen_unitario_actual, velocidad_final, tiempo_setup_final, tamano_lote_actual) - descuento
                fig.add_trace(go.Scatter(x=[margen_unitario_actual], y=[margen_nivel_2_actual], mode='markers', name=f'Punto Actual Margen hora - {planta} - {linea}', marker=dict(size=10, symbol='circle', color='red')))
                
                lineas_procesadas += 1
                barra_progreso.progress(lineas_procesadas / total_lineas_a_procesar)
                time.sleep(0.05)
                
                
                fig_tamano_lote.add_trace(go.Scatter(x=list(tamanos_lote) + list(tamanos_lote[::-1]), y=list(margen_hora_nivel2_max_lote) + list(margen_hora_nivel2_min_lote[::-1]), fill='toself', fillcolor='rgba(0,100,80,0.2)', line_color='rgba(255,255,255,0)', name=f'Rango de Variación - {planta} - {linea}'))
                fig_tamano_lote.add_trace(go.Scatter(x=tamanos_lote, y=margen_hora_nivel2_centro_lote, mode='lines', name=f'Proyección Margen hora - {planta} - {linea}'))
                fig_tamano_lote.add_trace(go.Scatter(x=[tamano_lote_actual], y=[margen_nivel_2], mode='markers', name=f'Punto Actual Margen hora - {planta} - {linea}', marker=dict(size=10, symbol='circle', color='red')))

        
        barra_progreso.empty()

        st.subheader('Gráfico de Proyección de Margen hora')
        fig.update_layout(title='Proyección del Margen hora vs. Margen Unitario', xaxis_title='Margen Unitario (USD/Mscs)', yaxis_title='Margen Hora (USD/h)')
        st.plotly_chart(fig, use_container_width=True)
        
        # --- Mostrar el segundo gráfico ---
        st.subheader('Gráfico 2: Proyección de Margen Hora vs. Tamaño de Lote')
        fig_tamano_lote.update_layout(title='Proyección del Margen por Hora vs. Tamaño de Lote', xaxis_title='Tamaño de Lote', yaxis_title='Margen por (USD/h)')
        st.plotly_chart(fig_tamano_lote, use_container_width=True)

        st.download_button(
            label="💾 Descargar datos de los gráficos en CSV",
            data=datos_descarga.to_csv(index=False).encode('utf-8'),
            file_name=f'proyeccion_de_margenes.csv',
            mime='text/csv'
        )
        
        
