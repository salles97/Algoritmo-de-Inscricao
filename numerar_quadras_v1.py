import geopandas as gpd
import psycopg2
from shapely import wkt
from shapely.geometry import Point, box
import matplotlib.pyplot as plt

# Conecta ao banco
conn = psycopg2.connect(database="Itanhandu_stagging", user="postgres", password="654741", host="localhost", port="5432")

# Busca as geometrias
cur = conn.cursor()
cur.execute('SELECT ST_AsText(geom) as geometry FROM public.quadras_teste_algoritmo')

# Salva em GeoDataFrame
gdf = gpd.GeoDataFrame(cur.fetchall(), columns=['geometry'])
# Define a coluna 'geometry' como a coluna de geometria ativa
gdf['geometry'] = gdf['geometry'].apply(wkt.loads)

gdf = gdf.set_geometry('geometry')
gdf.set_crs(epsg=31983) 

# Cria o Bounding Box
bbox = gdf.total_bounds
bbox_polygon = box(*bbox)

# Seleciona a coordenada mais ao sul e ao oeste
coord_inicial = Point(bbox[0], bbox[1])  # Cria um objeto Point

# Inicializa a coluna cod com 0
gdf['cod'] = 0

cod = 1

def encontrar_vizinhos(gdf, ponto_atual, cod):
    ponto_inicial = Point(ponto_atual)
    
    # Verifica se há polígonos não visitados
    while not gdf.loc[gdf.cod == 0].empty: 
        # Seleciona o polígono mais próximo da coordenada atual
        poligonos_nao_visitados = gdf.loc[gdf.cod == 0]
        ponto_atual = Point(ponto_atual)
        poligono_proximo_idx = poligonos_nao_visitados.geometry.distance(ponto_atual).idxmin()

        # Verifica se o polígono mais próximo está dentro do intervalo desejado
        if poligonos_nao_visitados.loc[poligono_proximo_idx, 'geometry'].distance(ponto_atual) <= 1000:
            # Cria o Bounding Box do polígono selecionado
            bbox_proximo = gdf.loc[poligono_proximo_idx, 'geometry'].bounds
            
            # Verifica se há vizinhos dentro do intervalo no novo Bounding Box
            vizinhos_proximos = gdf[gdf.geometry.distance(gdf.loc[poligono_proximo_idx, 'geometry']) <= 100]

            # Verifica se há vizinhos próximos
            if not vizinhos_proximos.empty:
                # Atualiza a coluna cod do polígono selecionado
                gdf.loc[poligono_proximo_idx, 'cod'] = cod
                cod += 1 
                # Seleciona o ponto mais à direita e inferior do Bounding Box
                ponto_atual = Point(bbox_proximo[2], bbox_proximo[1])
                
            else:
                # Adiciona valor de cod ao poligono_proximo_idx
                gdf.loc[poligono_proximo_idx, 'cod'] = cod
                cod += 1
                ponto_atual = ponto_inicial
                
        else:
            # Atualiza a coluna cod do polígono selecionado
            gdf.loc[poligono_proximo_idx, 'cod'] = cod
            cod += 1
    
    # Exportar GeoDataFrame para Shapefile
    gdf.to_file('./teste_quadras_numeradas.shp', driver='ESRI Shapefile')

# Plotar o GeoDataFrame
fig, ax = plt.subplots()
gdf.plot(ax=ax, color='lightgray', edgecolor='black')

# Plotar o BoundingBox
gpd.GeoSeries([bbox_polygon]).plot(ax=ax, facecolor='none', edgecolor='red', linestyle='--')

# Plotar o ponto inicial
gpd.GeoSeries([coord_inicial]).plot(ax=ax, color='blue', markersize=50, label='Ponto Inicial')

# Chama a função inicialmente
encontrar_vizinhos(gdf, coord_inicial, cod)

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
