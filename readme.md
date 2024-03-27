<h1 align="center">Algoritmo de atribuição de Inscrição Municipal</h1>


 <h4 align="center"> 
	🚧  Algoritmo 🚀 Em construção...  🚧
</h4>


## Sobre

 

## Sumário 
<!--ts-->
   * [Sobre](#sobre)
   * [Sumário](#sumário)
   * [Features](#features)
   * [Instalação](#instalação) 
      * [Pre Requisitos](#pré-requisitos) 
      * [Como Rodar](#como-rodar)   
   * [Contribuição](#contribuição)
   * [Licença](#licença)
<!--te-->
 
 
## Features

- [x] Numeração de quadras - Versão 1
- [ ] Numeração de quadras - Versão 2
- [ ] Numeração de Lotes - Versão 1
- [ ] Versão 3

### Quadras Versão 1:
  - [1] Consulta no banco as quadras
  - [2] Criar um Bounding Box envolvendo todas as quadras
  - [3] Selecionar a coordenada do canto inferior e esquerdo do BBox como ponto inicial
  - [4] Visita a quadra mais próxima do ponto inicial, e atribui um código a ela.
        Enquanto houver quadras com cod igual 0.
  - [5] Busca o vizinho mais próximo da quadra atual, e atribui um código a ela. 
          Repete esta etapa até não ter mais vizinho próximo.
          Se não houver vizinho próximo, volta ao passo 4.
  - [6] Imprime o resultado.

### Quadras Versão 2:
  - [1] Consulta no banco as quadras
  - [2] Criar um Bounding Box envolvendo todas as quadras e selecionar a coordenada do canto inferior e esquerdo do BBox como ponto inicial
  - [3] A partir do ponto inicial, encontre as quadras mais próximas
  - [4] Obtenha os BBox das quadras e o ponto mais inferior esquerdo
  - [5] Escolhe a quadra com menor latitude e maior longitude 
        -> Substitua o ponto inicial por essa primeira quadra escolhida
  - [6] Numera essa quadra e volta ao passo 3.
  - [7] Repete até não ter mais quadras à direita.
  - [8] Redefina o valor do ponto inicial e volte ao passo 3 enquanto houver quadras sem número.
  - [9] Imprime o resultado.

### Lotes Versão 1:
  - [1] Consulta no banco os lotes por quadra e os carrega em um GeoDataFrame.
  - [2] Cria um Bounding Box envolvendo todas os lotes e seleciona o lote inicial como o mais próximo de um ponto inicial.
  - [3] Inicia a função recursiva com o lote Inicial
  - [4] Calcula o perimetro do lote que faz fronteira com a quadra.
  - [5] Consulta o lote vizinho mais próximo, considerando a interseção entre os lotes.
  - [6] Volta ao passo 4 até não haver lotes não visitados
 
### Lotes Versão 2:
  = [1] - Todas função da V1
  - [2] - Tratamento para lotes sem testadas
  = [3] = tratamento para quadras irregulares/lotes encravados


## Instalação
### Pré-requisitos 

Antes de começar, você vai precisar ter instalado em sua máquina as seguintes ferramentas:
[Git](https://git-scm.com), [Python](https://www.python.org/). 
Além disto é bom ter um editor para trabalhar com o código como [VSCode](https://code.visualstudio.com/)
### Como Rodar
```

# Clone este repositório
$  git clone <https://github.com/salles97/Algoritmo-de-Inscricao> 

# Acesse a pasta do projeto
$ cd Algoritmo de Inscricao
 
# Instale as dependências Python
$ pip install -r requirements.txt

# Execute o script Python
python script.py numerar_quadras
```
 
 
## Contribuição
 
Faça um fork do projeto
Crie uma branch para sua modificação (git checkout -b feature/nova-feature)
Faça commit das suas alterações (git commit -am 'Adiciona nova feature')
Faça push para a branch (git push origin feature/nova-feature)
Abra um Pull Request
 