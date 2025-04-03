import os
import csv
from django.core.management.base import BaseCommand
from movie.models import Movie

class Command(BaseCommand):
    help = "Update movie descriptions in the database from a CSV file"

    def handle(self, *args, **kwargs):
        # 📥 Ruta del archivo CSV con las descripciones actualizadas
        csv_file = 'updated_movie_descriptions.csv'

        # ✅ Verifica si el archivo existe
        if not os.path.exists(csv_file):
            self.stderr.write(f"CSV file '{csv_file}' not found.")
            return

        self.stdout.write(f"Processing CSV file: {csv_file}")
        updated_count = 0
        created_count = 0
        error_count = 0

        # 📖 Abrimos el CSV y leemos cada fila
        with open(csv_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            total_rows = sum(1 for row in reader)
            self.stdout.write(f"Total rows in CSV: {total_rows}")
            
            # Volvemos al inicio del archivo
            file.seek(0)
            next(reader)  # Saltamos la cabecera
            
            for row in reader:
                title = row['Title']
                new_description = row['Updated Description']

                self.stdout.write(f"\nProcessing movie: {title}")
                self.stdout.write(f"Description length: {len(new_description)} characters")

                try:
                    # Buscar la película por título
                    movie, created = Movie.objects.get_or_create(
                        title=title,
                        defaults={
                            'description': new_description,
                            'image': 'movie/images/default.jpg',
                            'genre': 'Drama',
                            'year': 2023
                        }
                    )

                    if not created:
                        # Si la película ya existe, actualizamos su descripción
                        movie.description = new_description
                        movie.save()
                        updated_count += 1
                        self.stdout.write(self.style.SUCCESS(f"Updated: {title}"))
                    else:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f"Created: {title}"))

                except Exception as e:
                    error_count += 1
                    self.stderr.write(self.style.ERROR(f"Error processing {title}: {str(e)}"))

        # ✅ Al finalizar, muestra un resumen detallado
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("Processing Summary:"))
        self.stdout.write(self.style.SUCCESS(f"- Total rows processed: {total_rows}"))
        self.stdout.write(self.style.SUCCESS(f"- Movies updated: {updated_count}"))
        self.stdout.write(self.style.SUCCESS(f"- Movies created: {created_count}"))
        self.stdout.write(self.style.ERROR(f"- Errors encountered: {error_count}"))
        self.stdout.write("="*50) 