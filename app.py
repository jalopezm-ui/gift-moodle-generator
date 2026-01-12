import streamlit as st
import pandas as pd
import io

st.set_page_config(
    page_title="Generador GIFT para Moodle",
    page_icon="🎁",
    layout="centered"
)

# CSS personalizado - Fondo claro con mejor contraste
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
    }
    .main .block-container {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        margin-top: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    section[data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #e0e0e0;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
    }
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .correct-badge {
        background: #d4edda;
        color: #155724;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
    }
    .wrong-badge {
        background: #f8d7da;
        color: #721c24;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
    }
    h1 {
        color: #333 !important;
    }
</style>
""", unsafe_allow_html=True)

def escape_gift(text):
    """Escapar caracteres especiales del formato GIFT"""
    if pd.isna(text) or text is None:
        return ''
    text = str(text)
    replacements = [
        ('\\', '\\\\'),
        ('~', '\\~'),
        ('=', '\\='),
        ('#', '\\#'),
        ('{', '\\{'),
        ('}', '\\}'),
        (':', '\\:'),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text

def generate_gift(df, wrong_score, category):
    """Generar contenido en formato GIFT"""
    gift = ''
    
    if category:
        gift += f'$CATEGORY: {category}\n\n'
    
    # Detectar columnas (flexible)
    col_map = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower in ['id']:
            col_map['id'] = col
        elif col_lower in ['enunciado', 'pregunta', 'question']:
            col_map['enunciado'] = col
        elif col_lower in ['correcta', 'respuesta', 'correct', 'answer']:
            col_map['correcta'] = col
    
    # Detectar distractores
    distractor_cols = []
    for col in df.columns:
        col_lower = col.lower().strip()
        if 'distractor' in col_lower or col_lower.startswith('d') and col_lower[1:].isdigit():
            distractor_cols.append(col)
    
    for idx, row in df.iterrows():
        # ID
        q_id = row.get(col_map.get('id', 'id'), f'Pregunta_{idx+1}')
        if pd.isna(q_id):
            q_id = f'Pregunta_{idx+1}'
        
        # Enunciado
        enunciado = row.get(col_map.get('enunciado', 'enunciado'), '')
        if pd.isna(enunciado) or not str(enunciado).strip():
            continue
        
        # Respuesta correcta
        correcta = row.get(col_map.get('correcta', 'correcta'), '')
        if pd.isna(correcta) or not str(correcta).strip():
            continue
        
        # Distractores
        distractores = []
        for d_col in distractor_cols:
            val = row.get(d_col, '')
            if not pd.isna(val) and str(val).strip():
                distractores.append(str(val))
        
        # Construir pregunta GIFT
        gift += f'::{escape_gift(q_id)}::{escape_gift(enunciado)} {{\n'
        gift += f'  =%100%{escape_gift(correcta)}\n'
        
        for d in distractores:
            gift += f'  ~%{wrong_score}%{escape_gift(d)}\n'
        
        gift += '}\n\n'
    
    return gift, len(df), len(distractor_cols) + 1

# Título
st.markdown("# 🎁 Generador GIFT para Moodle")
st.markdown("*Campus Virtual UCM - Convierte Excel a formato GIFT con puntuaciones*")

st.divider()

# Sidebar para configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    wrong_score = st.selectbox(
        "❌ Penalización por error",
        options=[0, -5, -10, -20, -25, -33.33333, -50],
        index=2,
        format_func=lambda x: f"{x}%" if x <= 0 else f"{x}%"
    )
    
    category = st.text_input(
        "📁 Categoría (opcional)",
        placeholder="Ej: Psicobiología/Tema1"
    )
    
    st.divider()
    
    st.markdown("""
    ### 📊 Sistema de puntuación
    <span class="correct-badge">✅ Acierto: +100%</span><br><br>
    <span class="wrong-badge">❌ Error: penalización</span>
    """, unsafe_allow_html=True)
    
    st.info("Con 5 opciones y -10%, el azar da ~12% esperado (vs 0% con -25%)")

# Subida de archivo
uploaded_file = st.file_uploader(
    "📤 Sube tu archivo Excel o CSV",
    type=['xlsx', 'xls', 'csv'],
    help="El archivo debe tener columnas: id, enunciado, correcta, distractor1, distractor2..."
)

if uploaded_file:
    # Leer archivo
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ Archivo cargado: **{uploaded_file.name}** ({len(df)} preguntas)")
        
        # Mostrar preview de datos
        with st.expander("👀 Vista previa de los datos", expanded=False):
            st.dataframe(df.head(5), use_container_width=True)
        
        # Generar GIFT
        gift_content, total_q, total_opts = generate_gift(df, wrong_score, category)
        
        # Estadísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-number">{total_q}</div>
                <div class="stat-label">Preguntas</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-number">{total_opts}</div>
                <div class="stat-label">Opciones/pregunta</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="stat-box">
                <div class="stat-number">{wrong_score}%</div>
                <div class="stat-label">Penalización</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Vista previa del GIFT
        st.subheader("👁️ Vista previa del formato GIFT")
        st.code(gift_content[:2000] + ("..." if len(gift_content) > 2000 else ""), language="text")
        
        # Botón de descarga
        st.download_button(
            label="⬇️ Descargar archivo .gift",
            data=gift_content,
            file_name="preguntas_moodle.gift",
            mime="text/plain",
            type="primary",
            use_container_width=True
        )
        
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")

else:
    # Instrucciones cuando no hay archivo
    st.info("👆 Inicia subiendo un archivo en la zona superior para empezar.")
    
    st.divider()
    
    st.subheader("📖 Formato del archivo Excel")
    st.markdown("Tu Excel debe tener estas columnas (el orden no importa):")
    
    example_data = {
        "Columna": ["id", "enunciado", "correcta", "distractor1", "distractor2", "distractor3", "distractor4"],
        "Descripción": [
            "Identificador único (opcional)",
            "Texto de la pregunta",
            "Respuesta correcta",
            "Opción incorrecta 1",
            "Opción incorrecta 2",
            "Opción incorrecta 3",
            "Opción incorrecta 4 (opcional)"
        ],
        "Ejemplo": [
            "JoAn_01",
            "¿Cuál es la capital de España?",
            "Madrid",
            "Barcelona",
            "Valencia",
            "Sevilla",
            "Bilbao"
        ]
    }
    
    st.table(pd.DataFrame(example_data))

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.85rem;">
    Desarrollado con ❤️ para profesores UCM | <a href="https://gapthecode.com" target="_blank">Gap-the-Code</a>
</div>
""", unsafe_allow_html=True)
