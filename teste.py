import geopandas as gpd
import pandas as pd
import psycopg2
from shapely.geometry import Polygon
from shapely.ops import unary_union
from shapely.wkb import loads

# Parte 1: Busca as geometrias no banco e salva em GeoDataFrame (gdf)
def fetch_geometries_from_db():
    # Substitua os parâmetros com suas próprias credenciais
    conn = psycopg2.connect(database="Itanhandu_stagging", user="postgres", password="654741", host="localhost", port="5432")
    cur = conn.cursor()
    
    cur.execute("SELECT id, cod, geom FROM public.quadras_teste_algoritmo;")
    rows = cur.fetchall()

    geometries = [loads(row[2]) for row in rows]

    gdf = gpd.GeoDataFrame({'id': [row[0] for row in rows],
                            'cod': [row[1] for row in rows],
                            'geometry': geometries},
                            crs='EPSG:31983')

    conn.close()
    
    return gdf

# Parte 2: Criar o Bounding Box e identificar o primeiro polígono
def create_bounding_box_and_select_starting_polygon(gdf):
    bounding_box = unary_union(gdf['geometry']).bounds
    starting_polygon = gdf.loc[gdf['geometry'].bounds[0].idxmin()]
    gdf.at[starting_polygon.name, 'cod'] = 1
    
    return bounding_box, starting_polygon

# Parte 3: Buscar as geometrias mais à direita e numerar sequencialmente
def create_path_and_number_polygons(gdf, starting_polygon):
    path = []
    current_polygon = starting_polygon
    i = 2  # Inicia a contagem a partir do segundo polígono
    
    while True:
        path.append(current_polygon)
        polygons_to_the_right = [polygon for polygon in gdf.itertuples() if polygon.geometry.bounds[0] > current_polygon.geometry.bounds[2]]
        
        if not polygons_to_the_right:
            # Se não houver mais polígonos à direita, encontre um novo polígono mais próximo do canto inferior esquerdo
            remaining_polygons = [polygon for polygon in gdf.itertuples() if polygon not in path]
            if remaining_polygons:
                current_polygon = min(remaining_polygons, key=lambda polygon: (polygon.geometry.bounds[0], -polygon.geometry.bounds[1]))
                gdf.at[current_polygon.Index, 'cod'] = i
                i += 1
            else:
                break
        else:
            # Se houver polígonos à direita, selecione o mais à direita
            current_polygon = max(polygons_to_the_right, key=lambda polygon: polygon.geometry.bounds[2])
            gdf.at[current_polygon.Index, 'cod'] = i
            i += 1

    return gdf

# Parte 4: Executar o algoritmo
gdf = fetch_geometries_from_db()
bounding_box, starting_polygon = create_bounding_box_and_select_starting_polygon(gdf)
gdf = create_path_and_number_polygons(gdf, starting_polygon)

# Exibir resultados
print("Bounding Box:", bounding_box)
print("Starting Polygon:", starting_polygon)
print("Resulting GeoDataFrame:")
print(gdf)
