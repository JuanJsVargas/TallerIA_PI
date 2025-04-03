import os
from django.core.management.base import BaseCommand
from movie.models import Movie

class Command(BaseCommand):
    help = "Update movie images from the media/movie/images/ folder"

    def handle(self, *args, **kwargs):
        # ✅ Ruta de la carpeta de imágenes
        images_folder = 'media/movie/images/'
        
        # ✅ Verificar si la carpeta existe
        if not os.path.exists(images_folder):
            self.stderr.write(f"Images folder '{images_folder}' not found.")
            return

        # ✅ Obtener todas las películas
        movies = Movie.objects.all()
        self.stdout.write(f"Found {movies.count()} movies in the database")

        updated_count = 0
        not_found_count = 0

        # ✅ Recorrer cada película
        for movie in movies:
            try:
                # ✅ Construir el nombre del archivo esperado
                expected_filename = f"m_{movie.title}.png"
                image_path = os.path.join(images_folder, expected_filename)

                # ✅ Verificar si la imagen existe
                if os.path.exists(image_path):
                    # ✅ Actualizar la ruta de la imagen en la base de datos
                    relative_path = os.path.join('movie/images', expected_filename)
                    movie.image = relative_path
                    movie.save()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Updated image for: {movie.title}"))
                else:
                    not_found_count += 1
                    self.stderr.write(f"Image not found for: {movie.title}")

            except Exception as e:
                self.stderr.write(f"Error processing {movie.title}: {str(e)}")

        # ✅ Mostrar resumen
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("Processing Summary:"))
        self.stdout.write(self.style.SUCCESS(f"- Total movies processed: {movies.count()}"))
        self.stdout.write(self.style.SUCCESS(f"- Images updated: {updated_count}"))
        self.stdout.write(self.style.ERROR(f"- Images not found: {not_found_count}"))
        self.stdout.write("="*50) 