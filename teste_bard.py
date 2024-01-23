import geopandas as gpd
import psycopg2 


# Conecta ao banco
conn = psycopg2.connect(database="Itanhandu_stagging", user="postgres", password="654741", host="localhost", port="5432")

# Busca as geometrias
cur = conn.cursor()
cur.execute('SELECT  geom FROM public.quadras_teste_algoritmo')

# Salva em GeoDataFrame
gdf = gpd.GeoDataFrame(cur.fetchall(), columns=['geom'])

# Cria o Bounding Box
bbox = gdf.total_bounds

# Seleciona a coordenada mais ao sul e ao oeste
coord_inicial = bbox.minx, bbox.miny

# Inicializa a coluna cod com 0
gdf['cod'] = 0

 
cod = 1      

def renumerar_poligonos(gdf, ponto_atual, cod):

    # Verifica se há poligonos não visitados
    if not gdf.loc[gdf.cod == 0].empty: 

        # Seleciona o polígono mais próximo da coordenada atual
        poligonos_nao_visitados = gdf.loc[gdf.cod == 0]
        poligono_proximo_idx = poligonos_nao_visitados.geometry.distance(ponto_atual).idxmin()

        # Verifica se o polígono mais próximo atende à condição de distância
        distancia_limite = 0.5 * bbox.width  # Definir um limite de distância em unidades de coordenadas
        distancia = poligonos_nao_visitados.loc[poligono_proximo_idx, 'geometry'].distance(ponto_atual)

        if distancia > distancia_limite:
          
          
          # Atualiza a coluna cod do poligono selecionado
          gdf.loc[poligono_proximo_idx, 'cod'] = cod

          cod += 1
          
          # Cria o Bounding Box do poligono selecionado
          bbox_proximo = gdf.loc[poligono_proximo_idx, 'geom'].bounds

          # Seleciona o ponto mais a direita e inferior do Bounding Box
          ponto_atual = bbox_proximo.maxx, bbox_proximo.miny
 
 

          # Chama a função recursivamente
          renumerar_poligonos(gdf, ponto_atual, cod )


  
while not gdf.loc[gdf.cod == 0].empty:
    
  # Seleciona o poligono mais próximo da coordenada inicial
  poligono_sel = gdf.loc[gdf.cod == 0].geom.distance(coord_inicial).idxmin()
  
  # Atualiza a coluna cod do poligono selecionado
  gdf.loc[poligono_sel, 'cod'] = cod
  
  cod += 1
  
  # Cria o Bounding Box do poligono selecionado
  bbox_proximo = gdf.loc[poligono_sel, 'geom'].bounds

  # Seleciona o ponto mais a direita e inferior do Bounding Box
  ponto_atual = bbox_proximo.maxx, bbox_proximo.miny


  # Chama a função recursiva passando o poligono selecionado e a coordenada atual
  renumerar_poligonos(gdf, ponto_atual, cod)