import geopandas as gpd
import psycopg2
from shapely import wkt
from shapely.geometry import Point, box
import matplotlib.pyplot as plt

# Conectar ao banco de dados
conn = psycopg2.connect(database="Itanhandu_stagging", user="postgres", password="654741", host="localhost", port="5432")

# Função para buscar geometrias dos lotes por quadra
def get_lotes_por_quadra(setor_cod, quadra_cod):
    cur = conn.cursor()
    cur.execute(f"SELECT l.id, ST_AsText(ST_Buffer(l.geom, 0.1)) as geometry, SUM(ST_Length(t.geom)) as tam_testada FROM dado_novo.lote l JOIN dado_novo.testada t ON t.lote_id = l.id WHERE l.setor_cod = {setor_cod} AND l.quadra_cod = '{quadra_cod}' GROUP BY l.id, geometry")
    return cur.fetchall()

# def get_quadra(setor_cod, quadra_cod):
#     cur = conn.cursor()
#     cur.execute(f"SELECT id, ST_AsText(geom) as geometry FROM dado_novo.quadra WHERE setor_cod = {setor_cod} AND cod = '{quadra_cod}'")
#     return cur.fetchall()

# Função para calcular o comprimento das testadas de um lote
def calcular_comprimento_testadas(lote):
    # Aqui você deve implementar o cálculo do comprimento das testadas do lote
    # Estou assumindo que você tem uma função ou método para isso
    # Por exemplo: testadas_length = calcular_comprimento_testadas(lote)
    testadas_length = int(lote['tam_testada'] ) # Implemente o cálculo correto aqui
    return testadas_length
 
# Função para encontrar o lote vizinho mais próximo
def encontrar_lote_vizinho_proximo(lotes, lote_atual):
    lote_vizinho_proximo = None
    menor_distancia = float('inf')

    # Calcular o ponto inferior esquerdo do lote atual
    ponto_lote_atual = Point(lote_atual['geometry'].bounds[0], lote_atual['geometry'].bounds[1])

    for lote_vizinho in lotes:
        # Verificar se o lote atual não é o mesmo que o lote vizinho
        if lote_vizinho['id'] != lote_atual['id']:
            # Verificar se os lotes se intersectam
            if lote_atual['geometry'].intersects(lote_vizinho['geometry']):
                # Calcular o ponto inferior esquerdo do lote vizinho
                ponto_vizinho = Point(lote_vizinho['geometry'].bounds[0], lote_vizinho['geometry'].bounds[1])
                
                # Calcular a distância entre os pontos
                distancia = ponto_lote_atual.distance(ponto_vizinho)

                # Verificar se a distância é menor que a menor distância encontrada até agora
                if distancia < menor_distancia:
                    menor_distancia = distancia
                    lote_vizinho_proximo = lote_vizinho

    return lote_vizinho_proximo

# encontrar o lote mais inferior à esquerda
def encontrar_lote_proximo_a_ponto(ponto_inicial, gdf):
    lote_proximo = None
    menor_distancia = float('inf')

    for index, row in gdf.iterrows():
        # Calcular a distância entre o ponto inicial e o centroide do lote
        distancia = ponto_inicial.distance(row['geometry'].centroid)
        
        # Verificar se a distância é menor que a menor distância encontrada até agora
        if distancia < menor_distancia:
            menor_distancia = distancia
            lote_proximo = row
    
    return lote_proximo


# Função recursiva para percorrer os lotes e atribuir códigos
def percorrer_lotes_recursivo(gdf, lote_atual, cod):
    # Verificar se o lote atual é válido
    if lote_atual is None:
        return

    # Calcular o comprimento das testadas do lote atual
    testadas_length = calcular_comprimento_testadas(lote_atual)

    # Incrementar o código atual com o comprimento das testadas
    cod += testadas_length
    
    # Atribuir o comprimento das testadas como código
    gdf.loc[gdf['id'] == lote_atual['id'], 'cod'] = cod
 
    # Marcar o lote atual como visitado
    gdf.loc[gdf['id'] == lote_atual['id'], 'is_visited'] = True

    # Encontrar o próximo lote vizinho mais próximo não visitado
    proximo_lote = encontrar_lote_vizinho_proximo(gdf.loc[~gdf['is_visited']].to_dict('records'), lote_atual)
    
    while (proximo_lote != None) :
    # Chamar recursivamente a função para o próximo lote
      percorrer_lotes_recursivo(gdf, proximo_lote, cod)
      proximo_lote = encontrar_lote_vizinho_proximo(gdf.loc[~gdf['is_visited']].to_dict('records'), lote_atual)

      
    
    
    

# Chamar a função para buscar os lotes por quadra
lotes = get_lotes_por_quadra(setor_cod=2, quadra_cod='132')
# quadra = get_quadra(setor_cod=1, cod='130')

# Criar GeoDataFrame a partir dos lotes
gdf = gpd.GeoDataFrame(lotes, columns=['id', 'geometry', 'tam_testada'])
gdf['geometry'] = gdf['geometry'].apply(wkt.loads)
gdf = gdf.set_geometry('geometry')
gdf.set_crs(epsg=31983)

# Criar o Bounding Box
bbox = gdf.total_bounds
bbox_polygon = box(*bbox)

# Selecionar o lote inicial como o mais inferior esquerdo
# Aqui você deve implementar a lógica para selecionar o lote inicial 
initial_point = Point(bbox[0], bbox[1])

# Inicializar a coluna 'cod' com 0
gdf['cod'] = 0

# Inicializar a propriedade 'is_visited' como False
gdf['is_visited'] = False

# Chamar a função para encontrar o lote inferior esquerdo
lote_inferior_esquerdo = encontrar_lote_proximo_a_ponto(initial_point, gdf)

# Chamar a função recursiva para percorrer os lotes
percorrer_lotes_recursivo(gdf, lote_inferior_esquerdo, cod=0)

# Plotar o GeoDataFrame
fig, ax = plt.subplots()
gdf.plot(ax=ax, column='cod', legend=True, cmap='viridis', legend_kwds={'label': "Códigos"})

# Adicionar rótulos aos polígonos usando o atributo 'cod'
for x, y, label in zip(gdf.geometry.centroid.x, gdf.geometry.centroid.y, gdf['cod']):
    ax.text(x, y, str(label), fontsize=8, ha='right', bbox=dict(facecolor='white', alpha=0.5))

# Adicionar título
plt.title('GeoDataFrame com Códigos')

# Mostrar o gráfico
plt.show()

# Fechar a conexão
conn.close()
