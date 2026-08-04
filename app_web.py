import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Toyota Pro App", page_icon="🏎️", layout="centered")

# --- 1. BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('toyota_historial.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            mes INTEGER PRIMARY KEY AUTOINCREMENT,
            valor_xli REAL,
            valor_grs REAL,
            valor_seg REAL,
            capital_mp REAL,
            cuota_pura REAL,
            cuota_total REAL,
            faltante_grs REAL,
            faltante_seg REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- INTERFAZ STREAMLIT ---
st.title("🏎️ Toyota Pro App (Web V1)")
st.markdown("Cargá los valores actuales para evaluar tu estrategia de licitación.")

# --- FORMULARIO DE CARGA ---
with st.form("carga_mes"):
    col1, col2 = st.columns(2)
    
    with col1:
        val_xli = st.number_input("Valor XLI Base", min_value=0, value=44082000, step=100000)
        val_grs = st.number_input("Valor GR-Sport", min_value=0, value=55439000, step=100000)
    with col2:
        val_seg = st.number_input("Valor SEG", min_value=0, value=54392000, step=100000)
        capital_mp = st.number_input("Tu Capital M.Pago", min_value=0, value=4000000, step=100000)
        
    submitted = st.form_submit_button("Ejecutar y Guardar Mes")

# --- MOTOR MATEMÁTICO AL PRESIONAR EL BOTÓN ---
if submitted:
    conn = sqlite3.connect('toyota_historial.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM historial")
    mes_actual = cursor.fetchone()[0] + 1
    
    cuota_pura = val_xli * (382764 / 44082000)

    if mes_actual == 1: cuota_total = cuota_pura * (494777 / 382764)
    elif mes_actual <= 18: cuota_total = cuota_pura * (503067 / 382764)
    elif mes_actual <= 24: cuota_total = cuota_pura * (462339 / 382764)
    else: cuota_total = cuota_pura * (457693 / 382764)
    
    cuotas_faltantes = max(0, 24 - mes_actual)
    oferta_minima = cuotas_faltantes * cuota_pura
    derecho_adj = val_xli * 0.01
    
    total_necesario_grs = oferta_minima + (val_grs - val_xli) + derecho_adj
    total_necesario_seg = oferta_minima + (val_seg - val_xli) + derecho_adj

    faltante_grs = total_necesario_grs - capital_mp
    faltante_seg = total_necesario_seg - capital_mp

    # Guardar en BD
    cursor.execute('''INSERT INTO historial 
                      (valor_xli, valor_grs, valor_seg, capital_mp, cuota_pura, cuota_total, faltante_grs, faltante_seg) 
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', 
                   (val_xli, val_grs, val_seg, capital_mp, cuota_pura, cuota_total, faltante_grs, faltante_seg))
    conn.commit()
    conn.close()
    
    st.success(f"¡Cálculo del Mes {mes_actual} guardado con éxito!")

# --- SECCIÓN DE RESULTADOS RÁPIDOS ---
st.divider()
st.subheader("📊 Último Veredicto")

# Leer el último registro para mostrar el dashboard
conn = sqlite3.connect('toyota_historial.db')
df = pd.read_sql_query("SELECT * FROM historial", conn)
conn.close()

if not df.empty:
    ultimo = df.iloc[-1]
    
    col_a, col_b = st.columns(2)
    col_a.metric("Cuota Pura (70%)", f"${ultimo['cuota_pura']:,.0f}")
    col_b.metric("Cuota Total Est.", f"${ultimo['cuota_total']:,.0f}")
    
    col_c, col_d = st.columns(2)
    if ultimo['faltante_grs'] <= 0:
        col_c.success("🟢 ALCANZA PARA GR-SPORT")
    else:
        col_c.error(f"🔴 Faltan ${ultimo['faltante_grs']:,.0f} para GR-S")
        
    if ultimo['faltante_seg'] <= 0:
        col_d.success("🟢 ALCANZA PARA SEG")
    else:
        col_d.error(f"🔴 Faltan ${ultimo['faltante_seg']:,.0f} para SEG")

# --- SECCIÓN HISTORIAL Y GRÁFICO ---
st.divider()
st.subheader("📈 Evolución Patrimonial")

if not df.empty:
    # Mostramos la tabla linda con Pandas
    st.dataframe(df[['mes', 'valor_xli', 'valor_grs', 'valor_seg', 'capital_mp']], use_container_width=True)
    
    # Dibujamos el gráfico
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df['mes'], df['valor_xli'], label="XLI Base", linestyle="--", color="gray", marker="o")
    ax.plot(df['mes'], df['valor_grs'], label="GR-Sport", color="red", marker="o")
    ax.plot(df['mes'], df['valor_seg'], label="SEG", color="green", marker="o")
    ax.plot(df['mes'], df['capital_mp'], label="Tu Capital", color="blue", linewidth=3, marker="s")
    
    ax.set_ylabel("Monto ($)")
    ax.set_xlabel("Mes")
    ax.legend()
    ax.ticklabel_format(style='plain', axis='y')
    ax.grid(True, linestyle=":", alpha=0.6)
    
    st.pyplot(fig)
else:
    st.info("Aún no hay datos guardados. Ingresá tu primer mes arriba.")

# Botón peligroso para borrar todo
if st.button("Borrar todo el historial (Peligro)"):
    conn = sqlite3.connect('toyota_historial.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM historial")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='historial'")
    conn.commit()
    conn.close()
    st.rerun() # Recarga la página