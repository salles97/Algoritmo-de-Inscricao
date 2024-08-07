import geopandas as gpd
import psycopg2
from shapely import wkt
from shapely.geometry import Point, box
import matplotlib.pyplot as plt

# Conectar ao banco de dados
conn = psycopg2.connect(database="Itanhandu_stagging", user="postgres", password="654741", host="localhost", port="5432")

# Variável global para armazenar o código
cod = 0
# Função para buscar todas as quadras no banco de dados
def get_todas_quadras():
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT  setor_cod, quadra_cod FROM dado_novo.lote")
    return cur.fetchall()

# Função para buscar geometrias dos lotes por quadra, retorna o id, geom, e a soma do tamanha de suas testadas
def get_lotes_por_quadra(setor_cod, quadra_cod):
    cur = conn.cursor()
    cur.execute(f"SELECT l.id, ST_AsText(ST_Buffer(l.geom, 0.1)) as geometry, SUM(ST_Length(t.geom)) as tam_testada FROM dado_novo.lote l JOIN dado_novo.testada t ON t.lote_id = l.id WHERE l.setor_cod = {setor_cod} AND l.quadra_cod = '{quadra_cod}' GROUP BY l.id, geometry")
    return cur.fetchall()

# Função para calcular o comprimento das testadas de um lote
def calcular_comprimento_testadas(lote): 
    testadas_length = int(lote['tam_testada'] )  
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
                #  Calcular distância baseada nos mínimos valores de X e Y
                # distancia_x = abs(ponto_lote_atual.x - ponto_vizinho.x)
                # distancia_y = abs(ponto_lote_atual.y - ponto_vizinho.y)
                
                # Distância considerada como a soma das diferenças de X e Y
                # distancia = distancia_x + distancia_y
                
                # Calcular a distância entre os pontos
                distancia = ponto_lote_atual.distance(ponto_vizinho)

                # Verificar se a distância é menor que a menor distância encontrada até agora
                if distancia < menor_distancia:
                    menor_distancia = distancia
                    lote_vizinho_proximo = lote_vizinho

    return lote_vizinho_proximo
 
# Função para encontrar o lote mais inferior à esquerda não visitado
def encontrar_lote_inferior_esquerda(gdf):
    lote_inferior_esquerda = None
    menor_y = float('inf')
    menor_x = float('inf')

    for index, row in gdf.iterrows():
        if not row['is_visited']:
            lote = row['geometry']
            xmin, ymin, xmax, ymax = lote.bounds
            if ymin < menor_y or (ymin == menor_y and xmin < menor_x):
                menor_y = ymin
                menor_x = xmin
                lote_inferior_esquerda = row 

     # Atribuir um código inicial
    return lote_inferior_esquerda
 
def percorrer_lotes(gdf, lote_atual, cod):
    # Verifica se o lote atual já foi visitado
    if lote_atual['is_visited']:
  
        return cod
    else:
        # Calcula o comprimento das testadas do lote atual
        testadas_length = calcular_comprimento_testadas(lote_atual)
        # Atualiza o código e marca o lote como visitado
        cod += testadas_length
        gdf.loc[gdf['id'] == lote_atual['id'], 'cod'] = cod
        gdf.loc[gdf['id'] == lote_atual['id'], 'is_visited'] = True
        
        # Busca os vizinhos não visitados
        vizinho_mais_proximo =  encontrar_lote_vizinho_proximo(gdf.loc[~gdf['is_visited']].to_dict('records'), lote_atual) 
        print('Lote atual: %s \n' % (lote_atual['id']))
        while vizinho_mais_proximo is not None:
        # if vizinho_mais_proximo:
            print('Lote atual: %s, cod: %s, próximo vizinho: %s \n' % (lote_atual['id'], gdf.loc[gdf['id'] == lote_atual['id'], 'cod'].values[0], vizinho_mais_proximo['id']))
            # Chama a função recursivamente para o vizinho mais próximo não visitado
            cod = percorrer_lotes(gdf, vizinho_mais_proximo , cod)
        # else:
            print('Lote atual: %s, cod: %s \n' % (lote_atual['id'], gdf.loc[gdf['id'] == lote_atual['id'], 'cod'].values[0]))
            
            vizinho_mais_proximo =  encontrar_lote_vizinho_proximo(gdf.loc[~gdf['is_visited']].to_dict('records'), lote_atual) 
        return cod
      
def percorrer_quadra(gdf, cod):
    while not gdf['is_visited'].all():
        # Encontrar o primeiro lote inferior esquerdo não visitado
        lote_inferior_esquerdo = encontrar_lote_inferior_esquerda(gdf.loc[~gdf['is_visited']].copy())
        
        if lote_inferior_esquerdo is None:
            break
        
        # Chamar a função para percorrer todos os lotes a partir do lote inicial
        cod = percorrer_lotes(gdf, lote_inferior_esquerdo, cod)


quadras = get_todas_quadras()

# for quadras in quadras:
for setor_cod, quadra_cod in quadras:
    print(f"Processando Setor: {setor_cod}, Quadra: {quadra_cod}")

    # Chamar a função para buscar os lotes dado um setor e quadra
    lotes = get_lotes_por_quadra(setor_cod=setor_cod, quadra_cod=quadra_cod)

    if not lotes:
        continue
# setor_cod = 2
# quadra_cod = '132'

    versao = 'test'    
    # Chamar a função para buscar os lotes dado um setor e quadra
    # lotes = get_lotes_por_quadra(setor_cod=setor_cod, quadra_cod=quadra_cod)

    # Criar GeoDataFrame a partir dos lotes
    gdf = gpd.GeoDataFrame(lotes, columns=['id', 'geometry', 'tam_testada'])
    gdf['geometry'] = gdf['geometry'].apply(wkt.loads)
    gdf = gdf.set_geometry('geometry')
    gdf.set_crs(epsg=31983)

    # Inicializar a coluna 'cod' com 0
    gdf['cod'] = 0

    # Inicializar a propriedade 'is_visited' como False
    gdf['is_visited'] = False

    # Chamar a função para percorrer todas as quadras
    percorrer_quadra(gdf, 0)

    # Exportar o GeoDataFrame para um arquivo shapefile
    nome_arquivo = f"shp/S_{setor_cod}_Q_{quadra_cod}_Renumeração_{versao}.shp"
    gdf.to_file(nome_arquivo)
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

