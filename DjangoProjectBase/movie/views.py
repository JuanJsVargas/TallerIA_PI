from django.shortcuts import render
from django.http import HttpResponse
from .models import Movie
import matplotlib.pyplot as plt
import matplotlib
import io
import urllib, base64
import os
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('api_keys.env')

def home(request):
    #return HttpResponse('<h1>Welcome to Home Page</h1>')
    #return render(request, 'home.html')
    #return render(request, 'home.html', {'name':'Paola Vallejo'})
    searchTerm = request.GET.get('searchMovie') # GET se usa para solicitar recursos de un servidor
    if searchTerm:
        movies = Movie.objects.filter(title__icontains=searchTerm)
    else:
        movies = Movie.objects.all()
    return render(request, 'home.html', {'searchTerm':searchTerm, 'movies':movies})


def about(request):
    #return HttpResponse('<h1>Welcome to About Page</h1>')
    return render(request, 'about.html')

def signup(request):
    email = request.GET.get('email') 
    return render(request, 'signup.html', {'email':email})


def statistics_view0(request):
    matplotlib.use('Agg')
    # Obtener todas las películas
    all_movies = Movie.objects.all()

    # Crear un diccionario para almacenar la cantidad de películas por año
    movie_counts_by_year = {}

    # Filtrar las películas por año y contar la cantidad de películas por año
    for movie in all_movies:
        year = movie.year if movie.year else "None"
        if year in movie_counts_by_year:
            movie_counts_by_year[year] += 1
        else:
            movie_counts_by_year[year] = 1

    # Ancho de las barras
    bar_width = 0.5
    # Posiciones de las barras
    bar_positions = range(len(movie_counts_by_year))

    # Crear la gráfica de barras
    plt.bar(bar_positions, movie_counts_by_year.values(), width=bar_width, align='center')

    # Personalizar la gráfica
    plt.title('Movies per year')
    plt.xlabel('Year')
    plt.ylabel('Number of movies')
    plt.xticks(bar_positions, movie_counts_by_year.keys(), rotation=90)

    # Ajustar el espaciado entre las barras
    plt.subplots_adjust(bottom=0.3)

    # Guardar la gráfica en un objeto BytesIO
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    # Convertir la gráfica a base64
    image_png = buffer.getvalue()
    buffer.close()
    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')

    # Renderizar la plantilla statistics.html con la gráfica
    return render(request, 'statistics.html', {'graphic': graphic})

def statistics_view(request):
    matplotlib.use('Agg')
    # Gráfica de películas por año
    all_movies = Movie.objects.all()
    movie_counts_by_year = {}
    for movie in all_movies:
        print(movie.genre)
        year = movie.year if movie.year else "None"
        if year in movie_counts_by_year:
            movie_counts_by_year[year] += 1
        else:
            movie_counts_by_year[year] = 1

    year_graphic = generate_bar_chart(movie_counts_by_year, 'Year', 'Number of movies')

    # Gráfica de películas por género
    movie_counts_by_genre = {}
    for movie in all_movies:
        # Obtener el primer género
        genres = movie.genre.split(',')[0].strip() if movie.genre else "None"
        if genres in movie_counts_by_genre:
            movie_counts_by_genre[genres] += 1
        else:
            movie_counts_by_genre[genres] = 1

    genre_graphic = generate_bar_chart(movie_counts_by_genre, 'Genre', 'Number of movies')

    return render(request, 'statistics.html', {'year_graphic': year_graphic, 'genre_graphic': genre_graphic})


def generate_bar_chart(data, xlabel, ylabel):
    keys = [str(key) for key in data.keys()]
    plt.bar(keys, data.values())
    plt.title('Movies Distribution')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.xticks(rotation=90)
    plt.tight_layout()
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    image_png = buffer.getvalue()
    buffer.close()
    graphic = base64.b64encode(image_png).decode('utf-8')
    return graphic

def recommendations_view(request):
    prompt = request.GET.get('prompt', '')
    movies = []
    error_message = None
    
    if prompt:
        try:
            print(f"Procesando prompt: {prompt}")
            
            # Obtener el embedding del prompt
            api_key = os.environ.get('openai_apikey')
            if not api_key:
                raise ValueError("No se encontró la clave de API de OpenAI en las variables de entorno")
            
            client = OpenAI(api_key=api_key)
            print("Cliente OpenAI creado")
            
            response = client.embeddings.create(
                input=[prompt],
                model="text-embedding-3-small"
            )
            prompt_embedding = np.array(response.data[0].embedding, dtype=np.float32)
            print(f"Embedding del prompt generado, dimensiones: {prompt_embedding.shape}")
            
            # Obtener todas las películas
            all_movies = Movie.objects.all()
            print(f"Total de películas en la base de datos: {all_movies.count()}")
            
            # Calcular similitud con cada película
            movie_similarities = []
            for movie in all_movies:
                if movie.emb:
                    try:
                        movie_embedding = np.frombuffer(movie.emb, dtype=np.float32)
                        similarity = np.dot(prompt_embedding, movie_embedding) / (
                            np.linalg.norm(prompt_embedding) * np.linalg.norm(movie_embedding)
                        )
                        movie_similarities.append((movie, similarity))
                        print(f"Similitud calculada para {movie.title}: {similarity}")
                    except Exception as e:
                        print(f"Error procesando película {movie.title}: {str(e)}")
                else:
                    print(f"Película {movie.title} no tiene embedding")
            
            print(f"Total de similitudes calculadas: {len(movie_similarities)}")
            
            # Ordenar por similitud y tomar la más similar
            movie_similarities.sort(key=lambda x: x[1], reverse=True)
            if movie_similarities:
                movies = [movie_similarities[0][0]]  # Solo tomar la primera película (la más similar)
                print(f"Película recomendada seleccionada: {movies[0].title}")
            else:
                error_message = "No se encontraron películas con embeddings para comparar."
                
        except Exception as e:
            error_message = f"Error generando recomendaciones: {str(e)}"
            print(f"Error: {str(e)}")
    
    return render(request, 'recommendations.html', {
        'movies': movies,
        'prompt': prompt,
        'error_message': error_message
    })