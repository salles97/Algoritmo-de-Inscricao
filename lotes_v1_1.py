import geopandas as gpd
import pandas as pd
import psycopg2
from shapely import wkt
from shapely.geometry import Point, box
import matplotlib.pyplot as plt
import numpy as np  # Importe o numpy para lidar com NaN


# Conectar ao banco de dados
conn = psycopg2.connect(database="Itanhandu_stagging", user="postgres", password="654741", host="localhost", port="5432")

# Variável global para armazenar o código
cod = 0

# Função para buscar geometrias dos lotes por quadra, retorna o id, geom, e a soma do tamanho de suas testadas
def get_lotes_por_quadra(cur,setor_cod, quadra_cod):
    # cur = conn.cursor()
    cur.execute(f"SELECT l.id, ST_AsText(ST_Buffer(l.geom, 0.1)) as geometry, SUM(ST_Length(t.geom)) as tam_testada FROM dado_novo.lote l JOIN dado_novo.testada t ON t.lote_id = l.id WHERE l.setor_cod = {setor_cod} AND l.quadra_cod = '{quadra_cod}' GROUP BY l.id, geometry")
    return cur.fetchall()

# Função para buscar todas as quadras no banco de dados
def get_todas_quadras(cur):
    cur.execute("SELECT DISTINCT setor_cod, quadra_cod FROM dado_novo.lote WHERE setor_cod is not Null")
    return cur.fetchall()

# Função para calcular o comprimento das testadas de um lote
def calcular_comprimento_testadas(lote): 
  testadas_length = 5 if np.isnan(lote['tam_testada']) else int(lote['tam_testada'])
  return testadas_length

# Função para encontrar o lote vizinho mais próximo
def encontrar_lote_vizinho_proximo(lotes, lote_atual):
    lote_vizinho_proximo = None
    menor_distancia = float('inf')

    # Calcular os valores mínimos de X e Y do lote atual
    xmin_atual, ymin_atual = lote_atual['geometry'].bounds[0], lote_atual['geometry'].bounds[1]

    for lote_vizinho in lotes:
        # Verificar se o lote atual não é o mesmo que o lote vizinho
        if lote_vizinho['id'] != lote_atual['id']:
            # Verificar se os lotes se intersectam
            if lote_atual['geometry'].intersects(lote_vizinho['geometry']):
                # Calcular os valores mínimos de X e Y do lote vizinho
                xmin_vizinho, ymin_vizinho = lote_vizinho['geometry'].bounds[0], lote_vizinho['geometry'].bounds[1]
                # Calcular a distância baseada nos mínimos valores de X e Y
                distancia = abs(xmin_atual - xmin_vizinho) + abs(ymin_atual - ymin_vizinho)

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
        vizinho_mais_proximo = encontrar_lote_vizinho_proximo(gdf.loc[~gdf['is_visited']].to_dict('records'), lote_atual) 
        print('Lote atual: %s \n' % (lote_atual['id']))
        while vizinho_mais_proximo is not None:
            print('Lote atual: %s, cod: %s, próximo vizinho: %s \n' % (lote_atual['id'], gdf.loc[gdf['id'] == lote_atual['id'], 'cod'].values[0], vizinho_mais_proximo['id']))
            # Chama a função recursivamente para o vizinho mais próximo não visitado
            cod = percorrer_lotes(gdf, vizinho_mais_proximo, cod)
            print('Lote atual: %s, cod: %s \n' % (lote_atual['id'], gdf.loc[gdf['id'] == lote_atual['id'], 'cod'].values[0]))
            
            vizinho_mais_proximo = encontrar_lote_vizinho_proximo(gdf.loc[~gdf['is_visited']].to_dict('records'), lote_atual) 
        return cod

def percorrer_quadra(gdf, cod):
    while not gdf['is_visited'].all():
        # Encontrar o primeiro lote inferior esquerdo não visitado
        lote_inferior_esquerdo = encontrar_lote_inferior_esquerda(gdf.loc[~gdf['is_visited']].copy())
        
        if lote_inferior_esquerdo is None:
            break
        
        # Chamar a função para percorrer todos os lotes a partir do lote inicial
        cod = percorrer_lotes(gdf, lote_inferior_esquerdo, cod)
        
def atualizar_codigos_no_banco(gdf):
    # Abre um cursor
    cur = conn.cursor()
    try:
        # Atualiza cada lote no banco de dados com o novo código
        for index, row in gdf.iterrows():
            cur.execute("UPDATE dado_novo.lote SET lote_cod = %s WHERE id = %s", (row['cod'], row['id']))
        
        # Confirma a transação
        conn.commit()
    except Exception as e:
        print(f"Erro ao atualizar códigos no banco de dados: {e}")
        # Reverte a transação em caso de erro
        conn.rollback()
    finally:
        # Fecha o cursor
        cur.close()

cur = conn.cursor()
# Buscar todas as quadras
quadras = get_todas_quadras(cur)

# Lista para armazenar todos os GeoDataFrames
gdfs = []

for quadra in quadras:
    setor_cod, quadra_cod = quadra
    print(f"Processando Setor: {setor_cod}, Quadra: {quadra_cod}")
    
    # Chamar a função para buscar os lotes dado um setor e quadra
    lotes = get_lotes_por_quadra(cur=cur, setor_cod=setor_cod, quadra_cod=quadra_cod)

    if not lotes:
        continue

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

    atualizar_codigos_no_banco(gdf)
    # Adicionar o GeoDataFrame processado à lista
    gdfs.append(gdf)

# Concatenar todos os GeoDataFrames em um único GeoDataFrame
gdf_combinado = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))

# Exportar o GeoDataFrame combinado para um arquivo shapefile
nome_arquivo_combinado = "Lotes_Renumerados_Combinados.shp"
gdf_combinado.to_file(nome_arquivo_combinado)

# Plotar o GeoDataFrame combinado
fig, ax = plt.subplots()
gdf_combinado.plot(ax=ax, column='cod', legend=True, cmap='viridis', legend_kwds={'label': "Códigos"})

# Adicionar rótulos aos polígonos usando o atributo 'cod'
for x, y, label in zip(gdf_combinado.geometry.centroid.x, gdf_combinado.geometry.centroid.y, gdf_combinado['cod']):
    ax.text(x, y, str(label), fontsize=8, ha='right', bbox=dict(facecolor='white', alpha=0.5))

# Adicionar título
plt.title('GeoDataFrame Combinado com Códigos')

# Mostrar o gráfico
plt.show()

# Fechar a conexão
conn.close()
