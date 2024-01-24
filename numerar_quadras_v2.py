import geopandas as gpd
import psycopg2
from shapely import wkt
from shapely.geometry import Point, box
import matplotlib.pyplot as plt

# Conecta ao banco
conn = psycopg2.connect(database="Itanhandu_stagging", user="postgres", password="654741", host="localhost", port="5432")

# Busca as geometrias
cur = conn.cursor()
cur.execute('SELECT id, ST_AsText(geom) as geometry FROM public.quadras_teste_algoritmo')

# Salva em GeoDataFrame
gdf = gpd.GeoDataFrame(cur.fetchall(), columns=['id','geometry'])
# Define a coluna 'geometry' como a coluna de geometria ativa
gdf['geometry'] = gdf['geometry'].apply(wkt.loads)

gdf = gdf.set_geometry('geometry')
gdf.set_crs(epsg=31983) 

gdf['id'] = gdf.index
# Cria o Bounding Box
bbox = gdf.total_bounds
bbox_polygon = box(*bbox)

# Seleciona a coordenada mais ao sul e ao oeste
coord_inicial = Point(bbox[0], bbox[1])  # Cria um objeto Point

# Inicializa a coluna cod com 0
gdf['cod'] = 0

cod = 1
 
def gerar_bbox_quadras(gdf):
    # Criar colunas para armazenar os Bounding Boxes e os pontos mais inferiores esquerdos
    gdf['bbox'] = gdf['geometry'].bounds.apply(lambda row: (row['minx'], row['miny'], row['maxx'], row['maxy']), axis=1)
    gdf['min_left_point'] = gdf.apply(lambda row: (row['bbox'][0], row['bbox'][1]), axis=1)
    gdf['cod'] = 0
    return gdf

 
def find_closest_quadras(gdf, current_point, n=5):
    # Cria um objeto Point com as coordenadas do ponto
    point = Point(current_point)
    
    # Filtra os polígonos com cod = 0
    gdf_filtered = gdf[gdf['cod'] == 0]
    
    # Verifica se há polígonos disponíveis
    if gdf_filtered.empty: 
        return None
    
    # Calcula as distâncias entre o ponto e todos os polígonos disponíveis
    distances = gdf_filtered['geometry'].apply(lambda geom: point.distance(geom))
    
    # Obtém os índices dos n polígonos mais próximos
    closest_quadras = distances.nsmallest(n).index.tolist()
    
    return closest_quadras

def choose_next_polygon(gdf, candidates, current_point, initial_point): 
    # Verifica se há candidatos
    if not candidates:
        return None
    
   # Se o ponto atual for igual ao ponto inicial, escolhe o mais próximo com cod = 0
    if current_point == initial_point:
        distances_to_initial = gdf.loc[candidates, 'geometry'].apply(lambda geom: initial_point.distance(geom))
        closest_with_cod_zero = distances_to_initial.idxmin()
        return closest_with_cod_zero
    # Obtém os BBox dos candidatos
    candidates_bbox = gdf.loc[candidates, 'geometry'].bounds 
    
    # Coordenada x do ponto atual
    current_x = current_point[0] if isinstance(current_point, tuple) else current_point.x
    
    # Filtra os candidatos que estão à direita do ponto atual
    right_of_current = candidates_bbox['minx'] > current_x
    
    # Verifica se há candidatos à direita
    if right_of_current.any():  # Verifica se pelo menos um é True
        # Seleciona o polígono com menor latitude e maior longitude
        right_candidates = [candidate for candidate, is_right in zip(candidates, right_of_current) if is_right]
        chosen_index = candidates_bbox.loc[right_candidates, 'miny'].idxmin()
        return chosen_index
    else:
        return None


def caminho(gdf,  initial_point,   i):
   
    gdf = gerar_bbox_quadras(gdf)  
    # Converter a coluna 'min_left_point' para uma string representando um ponto
    # Agora, salve o GeoDataFrame
    gdf_aux = gdf.drop('min_left_point', axis=1).drop('bbox', axis=1)
    gdf_aux.to_file('./gdf_antes_de_numerar.shp', driver='ESRI Shapefile' )

    current_point = initial_point
    last_change_count = 0

    while gdf['cod'].eq(0).any() and last_change_count < len(gdf):
        print("Current Point:", current_point)
        candidates = find_closest_quadras(gdf, current_point)
        print("Candidates:", candidates)
        next_polygon = choose_next_polygon(gdf, candidates, current_point, initial_point)
        print("Next Polygon:", next_polygon)

        # Se houver polígono à direita!
        if next_polygon is not None:
            gdf.loc[next_polygon, 'cod'] = i
            i += 1  
            current_point = gdf.loc[next_polygon, 'min_left_point']
            last_change_count = 0
        else:
            last_change_count += 1
            current_point = initial_point

    gdf_aux = gdf.drop('min_left_point', axis=1).drop('bbox', axis=1)
    gdf_aux.to_file('./gdf_depois_de_numerar.shp', driver='ESRI Shapefile' )

    
    
    
# Plotar o GeoDataFrame
fig, ax = plt.subplots()
gdf.plot(ax=ax, color='lightgray', edgecolor='black')

# Plotar o BoundingBox
gpd.GeoSeries([bbox_polygon]).plot(ax=ax, facecolor='none', edgecolor='red', linestyle='--')

# Plotar o ponto inicial
gpd.GeoSeries([coord_inicial]).plot(ax=ax, color='blue', markersize=50, label='Ponto Inicial')

# Chama a função inicialmente
caminho(gdf,  coord_inicial,   1)
# Plotar os polígonos com os códigos finais
gdf.plot(ax=ax, column='cod', legend=True, cmap='viridis', legend_kwds={'label': "Códigos"})

# Adicionar título
plt.title('GeoDataFrame com BoundingBox e Códigos')

# Adicionar legenda
plt.legend()

# Mostrar o gráfico
plt.show()

# Feche a conexão
conn.close()
