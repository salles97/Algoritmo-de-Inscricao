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
 
def find_closest_to_initial_point(gdf, current_point):
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
    closest_quadra = distances.nsmallest(5).tolist()
    
    # Obtém o índice do polígono mais próximo com base na menor latitude
    closest_quadra = gdf_filtered.loc[distances.idxmin()]
    
    # print('closest_quadra', closest_quadra)
    
    return closest_quadra
 
def find_right_neighbor(gdf, current_block):
    # Obter o bounding box do current_block
    miny, maxy = current_block['geometry'].bounds[1], current_block['geometry'].bounds[3]

    # Criar um box (polígono retangular) para a faixa de latitude do current_block
    lat_box = box(gdf.total_bounds[0], miny, gdf.total_bounds[2], maxy)

    # Filtrar geometrias que intersectam com a faixa de latitude do current_block
    valid_geometries = gdf[gdf.intersects(lat_box)]

    # Verificar se há geometrias dentro da faixa de longitude
    if not valid_geometries.empty:
        # Filtrar geometrias com minx > maxx do current_block
        candidate_geometries = valid_geometries[valid_geometries['geometry'].bounds['minx'] > current_block['geometry'].bounds[0]]

        # Verificar se há geometrias candidatas
        if not candidate_geometries.empty:
            # Ordenar candidatos pela coordenada x
            right_neighbor = candidate_geometries.loc[candidate_geometries.bounds['minx'].idxmin()]
            return right_neighbor

    return None

def caminho(gdf,  initial_point ):
   
    gdf = gerar_bbox_quadras(gdf)  
    # Converter a coluna 'min_left_point' para uma string representando um ponto
    # Agora, salve o GeoDataFrame
    gdf_aux = gdf.drop('min_left_point', axis=1).drop('bbox', axis=1)
    gdf_aux.to_file('./gdf_antes_de_numerar.shp', driver='ESRI Shapefile' )
    
    # // Encontrar o ponto min xy
    minXY = initial_point
  
    # encontrar a geometria mais proxima
    current_block = find_closest_to_initial_point(gdf, minXY) 
    cod = 1
    
    while gdf['cod'].eq(0).any():
        print(f"Current cod values: {gdf['cod'].unique()}")  # Adiciona esta linha para imprimir os valores de 'cod'
        print(f"Number of remaining blocks: {len(gdf[gdf['cod'] == 0])}")  # Adiciona esta linha para imprimir o número de blocos restantes
        
        gdf.loc[gdf['geometry'] == current_block['geometry'], 'cod'] = cod
        cod += 1 
        
        if len(gdf[gdf['cod'] == 0]) == 1:
            break
        # Chamar a função que retorna o vizinho à direita
        vizinho = find_right_neighbor(gdf[gdf['cod'] == 0], current_block)
        print('Vizinho: ', vizinho)
        
        if vizinho is not None:
            current_block = vizinho 
        else:
            current_block = find_closest_to_initial_point(gdf.loc[gdf.cod == 0], minXY)  
            if current_block is None:
                break
            print('Sem vizinho')


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
caminho(gdf,  coord_inicial )
# Plotar os polígonos com os códigos finais
gdf.plot(ax=ax, column='cod', legend=True, cmap='viridis', legend_kwds={'label': "Códigos"})

# Adicionar rótulos aos polígonos usando o atributo 'cod'
for x, y, label in zip(gdf.geometry.centroid.x, gdf.geometry.centroid.y, gdf['cod']):
    ax.text(x, y, str(label), fontsize=8, ha='right')

# Adicionar título
plt.title('GeoDataFrame com BoundingBox e Códigos')

# Adicionar legenda
plt.legend()

# Mostrar o gráfico
plt.show()

# Feche a conexão
conn.close()
