import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np
import requests
import urllib3

# Desactivar advertencias de SSL para evitar bloqueos de red
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =========================================================
# CONFIGURACIÓN
# =========================================================
st.set_page_config(layout="wide", page_title="Monitor de Contagio Geopolítico")
st.title("🌎 Monitor de Contagio Global: Efecto Red")
st.caption("🔴 Rojo Puro: El riesgo es sistémico (PageRank domina) | 🟢 Verde Puro: El riesgo es local | Blanco: Sin datos")

# Rutas de tus archivos Min-Max
ARCHIVO_LOCAL = r"D:\geopolitical_risk\Matriz_Mensual_Geopol_Normalizada.csv"
ARCHIVO_PR = r"D:\geopolitical_risk\Matriz_PageRank_MinMax_Pais.csv"

# URL pública para obtener las fronteras de los países en formato GeoJSON
URL_GEOJSON = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"

# =========================================================
# DICCIONARIO MAESTRO: TRADUCTOR DE 3 LETRAS A 2 LETRAS
# =========================================================
iso_3_to_2 = {
    'AFG': 'AF', 'ALB': 'AL', 'DZA': 'DZ', 'ASM': 'AS', 'AND': 'AD', 'AGO': 'AO', 'AIA': 'AI', 'ATA': 'AQ',
    'ATG': 'AG', 'ARG': 'AR', 'ARM': 'AM', 'ABW': 'AW', 'AUS': 'AU', 'AUT': 'AT', 'AZE': 'AZ', 'BHS': 'BS',
    'BHR': 'BH', 'BGD': 'BD', 'BRB': 'BB', 'BLR': 'BY', 'BEL': 'BE', 'BLZ': 'BZ', 'BEN': 'BJ', 'BMU': 'BM',
    'BTN': 'BT', 'BOL': 'BO', 'BES': 'BQ', 'BIH': 'BA', 'BWA': 'BW', 'BVT': 'BV', 'BRA': 'BR', 'IOT': 'IO',
    'BRN': 'BN', 'BGR': 'BG', 'BFA': 'BF', 'BDI': 'BI', 'CPV': 'CV', 'KHM': 'KH', 'CMR': 'CM', 'CAN': 'CA',
    'CYM': 'KY', 'CAF': 'CF', 'TCD': 'TD', 'CHL': 'CL', 'CHN': 'CN', 'CXR': 'CX', 'CCK': 'CC', 'COL': 'CO',
    'COM': 'KM', 'COD': 'CD', 'COG': 'CG', 'COK': 'CK', 'CRI': 'CR', 'HRV': 'HR', 'CUB': 'CU', 'CUW': 'CW',
    'CYP': 'CY', 'CZE': 'CZ', 'CIV': 'CI', 'DNK': 'DK', 'DJI': 'DJ', 'DMA': 'DM', 'DOM': 'DO', 'ECU': 'EC',
    'EGY': 'EG', 'SLV': 'SV', 'GNQ': 'GQ', 'ERI': 'ER', 'EST': 'EE', 'SWZ': 'SZ', 'ETH': 'ET', 'FLK': 'FK',
    'FRO': 'FO', 'FJI': 'FJ', 'FIN': 'FI', 'FRA': 'FR', 'GUF': 'GF', 'PYF': 'PF', 'ATF': 'TF', 'GAB': 'GA',
    'GMB': 'GM', 'GEO': 'GE', 'DEU': 'DE', 'GHA': 'GH', 'GIB': 'GI', 'GRC': 'GR', 'GRL': 'GL', 'GRD': 'GD',
    'GLP': 'GP', 'GUM': 'GU', 'GTM': 'GT', 'GGY': 'GG', 'GIN': 'GN', 'GNB': 'GW', 'GUY': 'GY', 'HTI': 'HT',
    'HMD': 'HM', 'VAT': 'VA', 'HND': 'HN', 'HKG': 'HK', 'HUN': 'HU', 'ISL': 'IS', 'IND': 'IN', 'IDN': 'ID',
    'IRN': 'IR', 'IRQ': 'IQ', 'IRL': 'IE', 'IMN': 'IM', 'ISR': 'IL', 'ITA': 'IT', 'JAM': 'JM', 'JPN': 'JP',
    'JEY': 'JE', 'JOR': 'JO', 'KAZ': 'KZ', 'KEN': 'KE', 'KIR': 'KI', 'PRK': 'KP', 'KOR': 'KR', 'KWT': 'KW',
    'KGZ': 'KG', 'LAO': 'LA', 'LVA': 'LV', 'LBN': 'LB', 'LSO': 'LS', 'LBR': 'LR', 'LBY': 'LY', 'LIE': 'LI',
    'LTU': 'LT', 'LUX': 'LU', 'MAC': 'MO', 'MDG': 'MG', 'MWI': 'MW', 'MYS': 'MY', 'MDV': 'MV', 'MLI': 'ML',
    'MLT': 'MT', 'MHL': 'MH', 'MTQ': 'MQ', 'MRT': 'MR', 'MUS': 'MU', 'MYT': 'YT', 'MEX': 'MX', 'FSM': 'FM',
    'MDA': 'MD', 'MCO': 'MC', 'MNG': 'MN', 'MNE': 'ME', 'MSR': 'MS', 'MAR': 'MA', 'MOZ': 'MZ', 'MMR': 'MM',
    'NAM': 'NA', 'NRU': 'NR', 'NPL': 'NP', 'NLD': 'NL', 'NCL': 'NC', 'NZL': 'NZ', 'NIC': 'NI', 'NER': 'NE',
    'NGA': 'NG', 'NIU': 'NU', 'NFK': 'NF', 'MNP': 'MP', 'NOR': 'NO', 'OMN': 'OM', 'PAK': 'PK', 'PLW': 'PW',
    'PSE': 'PS', 'PAN': 'PA', 'PNG': 'PG', 'PRY': 'PY', 'PER': 'PE', 'PHL': 'PH', 'PCN': 'PN', 'POL': 'PL',
    'PRT': 'PT', 'PRI': 'PR', 'QAT': 'QA', 'MKD': 'MK', 'ROU': 'RO', 'RUS': 'RU', 'RWA': 'RW', 'REU': 'RE',
    'BLM': 'BL', 'SHN': 'SH', 'KNA': 'KN', 'LCA': 'LC', 'MAF': 'MF', 'SPM': 'PM', 'VCT': 'VC', 'WSM': 'WS',
    'SMR': 'SM', 'STP': 'ST', 'SAU': 'SA', 'SEN': 'SN', 'SRB': 'RS', 'SYC': 'SC', 'SLE': 'SL', 'SGP': 'SG',
    'SXM': 'SX', 'SVK': 'SK', 'SVN': 'SI', 'SLB': 'SB', 'SOM': 'SO', 'ZAF': 'ZA', 'SGS': 'GS', 'SSD': 'SS',
    'ESP': 'ES', 'LKA': 'LK', 'SDN': 'SD', 'SUR': 'SR', 'SJM': 'SJ', 'SWE': 'SE', 'CHE': 'CH', 'SYR': 'SY',
    'TWN': 'TW', 'TJK': 'TJ', 'TZA': 'TZ', 'THA': 'TH', 'TLS': 'TL', 'TGO': 'TG', 'TKL': 'TK', 'TON': 'TO',
    'TTO': 'TT', 'TUN': 'TN', 'TUR': 'TR', 'TKM': 'TM', 'TCA': 'TC', 'TUV': 'TV', 'UGA': 'UG', 'UKR': 'UA',
    'ARE': 'AE', 'GBR': 'GB', 'UMI': 'UM', 'USA': 'US', 'URY': 'UY', 'UZB': 'UZ', 'VUT': 'VU', 'VEN': 'VE',
    'VNM': 'VN', 'VGB': 'VG', 'VIR': 'VI', 'WLF': 'WF', 'ESH': 'EH', 'YEM': 'YE', 'ZMB': 'ZM', 'ZWE': 'ZW',
    'ALA': 'AX', 'CAF': 'CF', 'NAM': 'NA', 'SVN': 'SI', 'SRB': 'RS', 'XKX': 'XK'
}

# =========================================================
# CARGA Y PRE-PROCESAMIENTO
# =========================================================
@st.cache_data
def cargar_matrices_y_geojson():
    df_orig = pd.read_csv(ARCHIVO_LOCAL, index_col='Mes')
    df_pr = pd.read_csv(ARCHIVO_PR, index_col='Mes')
    
    paises = [c for c in df_orig.columns if c in df_pr.columns and c not in ['GLOBAL_TOTAL', 'Total']]
    df_orig = df_orig[paises]
    df_pr = df_pr[paises]
    
    try:
        respuesta = requests.get(URL_GEOJSON, verify=False)
        geojson_data = respuesta.json()
    except Exception as e:
        st.error(f"No se pudo cargar el mapa base GeoJSON: {e}")
        geojson_data = {"type": "FeatureCollection", "features": []}

    return df_orig, df_pr, geojson_data

df_orig, df_pr, geojson_base = cargar_matrices_y_geojson()

df_orig.index = pd.to_datetime(df_orig.index)
df_pr.index = pd.to_datetime(df_pr.index)

df_gap_completo = df_pr - df_orig

# =========================================================
# INTERFAZ DE USUARIO (MAPA)
# =========================================================
col_ui1, col_ui2 = st.columns([1, 3])

with col_ui1:
    modo_vista = st.radio("🔍 Tipo de Visualización en Mapa", ["Mes Específico", "Promedio Histórico Completo"])

lista_meses = list(df_orig.index.strftime('%Y-%m'))

if modo_vista == "Mes Específico":
    mes_str = st.select_slider("📅 Selecciona el Mes", options=lista_meses, value=lista_meses[-1])
    mes_sel = df_orig.index[lista_meses.index(mes_str)]
    
    serie_brecha = df_gap_completo.loc[mes_sel]
    serie_orig = df_orig.loc[mes_sel]
    serie_pr = df_pr.loc[mes_sel]
else:
    st.info("Mostrando el promedio de contagio para todo el periodo analizado.")
    serie_brecha = df_gap_completo.mean()
    serie_orig = df_orig.mean()
    serie_pr = df_pr.mean()

# =========================================================
# ASIGNACIÓN DE COLORES SÓLIDOS (NUEVA LÓGICA)
# =========================================================
def asignar_colores_fijos(gap):
    # Colores institucionales (menos saturados, más sobrios)
    if gap > 0:
        return [180, 30, 30, 255]    # Rojo institucional
    else:
        return [30, 150, 30, 255]    # Verde institucional

geojson_pintado = {"type": "FeatureCollection", "features": []}

for feature in geojson_base["features"]:
    id_geo_3letras = feature["id"]
    id_datos_2letras = iso_3_to_2.get(id_geo_3letras, id_geo_3letras)
        
    if id_datos_2letras in serie_brecha.index:
        gap = serie_brecha[id_datos_2letras]
        color = asignar_colores_fijos(gap)
        
        # Redondeo de datos a 4 decimales
        val_gap = round(gap, 4)
        val_local = round(serie_orig[id_datos_2letras], 4)
        val_pr = round(serie_pr[id_datos_2letras], 4)
        
        # 1. Guardamos en properties (Estándar GeoJSON)
        feature["properties"]["gap"] = val_gap
        feature["properties"]["fill_color"] = color
        feature["properties"]["local_risk"] = val_local
        feature["properties"]["pr_risk"] = val_pr
        
        # 2. Guardamos a nivel raíz (Para que Pydeck NO falle al leer el tooltip)
        feature["gap"] = val_gap
        feature["local_risk"] = val_local
        feature["pr_risk"] = val_pr
        feature["id"] = id_datos_2letras 
        
        geojson_pintado["features"].append(feature)

# =========================================================
# RENDER DEL MAPA
# =========================================================
layer_geojson = pdk.Layer(
    "GeoJsonLayer",
    data=geojson_pintado,
    pickable=True,
    stroked=True,
    filled=True,
    get_fill_color="properties.fill_color", # Pydeck sí lee properties para el color
    get_line_color=[50, 50, 50, 255],
    get_line_width=1,
    line_width_units="pixels",
)

layer_borders = pdk.Layer(
    "GeoJsonLayer",
    data=geojson_pintado,
    stroked=True,
    filled=False,  # SOLO líneas
    get_line_color=[255, 255, 255, 200],  # blanco visible
    get_line_width=1.5,
    line_width_units="pixels",
)

def get_centroid(feature):
    coords = feature["geometry"]["coordinates"]

    # Manejo simple para Polygons y MultiPolygons
    if feature["geometry"]["type"] == "Polygon":
        lon = np.mean([c[0] for c in coords[0]])
        lat = np.mean([c[1] for c in coords[0]])
    else:  # MultiPolygon
        lon = np.mean([c[0] for poly in coords for c in poly[0]])
        lat = np.mean([c[1] for poly in coords for c in poly[0]])

    return lon, lat

labels = []

for feature in geojson_pintado["features"]:
    lon, lat = get_centroid(feature)
    nombre = feature["id"]  

    labels.append({
        "name": nombre,
        "lon": lon,
        "lat": lat
    })

df_labels = pd.DataFrame(labels)

layer_text = pdk.Layer(
    "TextLayer",
    data=df_labels,
    get_position='[lon, lat]',
    get_text='name',
    get_size=12,
    get_color=[255, 255, 255, 200],
    get_angle=0,
    get_text_anchor='"middle"',
    get_alignment_baseline='"center"',
)

st.pydeck_chart(pdk.Deck(
    layers=[layer_geojson, layer_borders, layer_text],
    initial_view_state=pdk.ViewState(latitude=20, longitude=0, zoom=1.2, pitch=0),
    map_style="dark",
    tooltip={
        # Aquí quitamos el prefijo 'properties.' y Pydeck leerá las variables raíz
        "html": "<b>País:</b> {id}<br>"
                "<b>Brecha:</b> {gap}<br>"
                "<b>Riesgo Local:</b> {local_risk}<br>"
                "<b>PageRank:</b> {pr_risk}"
    }
))

# =========================================================
# SECCIÓN DINÁMICA: GRÁFICA HISTÓRICA POR PAÍS (NATIVA)
# =========================================================
st.write("---")
st.subheader("📈 Análisis de Serie Temporal por País")

lista_paises_disponibles = sorted(list(df_orig.columns))
pais_seleccionado = st.selectbox(
    "🎯 Selecciona un país para ver su evolución histórica:", 
    lista_paises_disponibles, 
    index=lista_paises_disponibles.index('MX') if 'MX' in lista_paises_disponibles else 0
)

if pais_seleccionado:
    s_orig = df_orig[pais_seleccionado]
    s_pr = df_pr[pais_seleccionado]
    
    df_grafica = pd.DataFrame({
        'Riesgo Local (Original Min-Max)': s_orig,
        'Riesgo Sistémico (PageRank Min-Max)': s_pr
    })
    
    st.line_chart(df_grafica)