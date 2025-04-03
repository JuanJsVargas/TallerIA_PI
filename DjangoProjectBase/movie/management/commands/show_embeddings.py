import os
import numpy as np
from django.core.management.base import BaseCommand
from movie.models import Movie
import random

class Command(BaseCommand):
    help = "Show embeddings for a random movie"

    def add_arguments(self, parser):
        parser.add_argument('--title', type=str, help='Title of the specific movie to show (optional)')

    def handle(self, *args, **kwargs):
        # ✅ Get movies
        title = kwargs.get('title')
        if title:
            movies = Movie.objects.filter(title=title)
            if not movies.exists():
                self.stderr.write(f"❌ No movie found with title: {title}")
                return
            movie = movies.first()
        else:
            movies = Movie.objects.all()
            if not movies.exists():
                self.stderr.write("❌ No movies found in the database")
                return
            movie = random.choice(movies)
        
        try:
            # ✅ Get the embedding and convert from bytes to numpy array
            embedding_bytes = movie.emb
            if embedding_bytes is None:
                self.stderr.write(f"❌ No embedding found for movie: {movie.title}")
                return
                
            embedding_vector = np.frombuffer(embedding_bytes, dtype=np.float32)
            
            # ✅ Print movie information
            self.stdout.write(self.style.SUCCESS(f"\n🎬 Selected Movie: {movie.title}"))
            self.stdout.write(f"📝 Description: {movie.description[:200]}...")
            self.stdout.write(f"📊 Embedding Dimensions: {embedding_vector.shape}")
            
            # ✅ Print the first 10 values of the embedding
            self.stdout.write("\n🔢 First 10 values of the embedding vector:")
            for i, value in enumerate(embedding_vector[:10]):
                self.stdout.write(f"  [{i:2d}]: {value:>10.6f}")

            # ✅ Calculate statistics only on finite values
            valid_mask = np.isfinite(embedding_vector)
            valid_values = embedding_vector[valid_mask]
            
            if len(valid_values) > 0:
                self.stdout.write("\n📈 Embedding Statistics:")
                self.stdout.write(f"  Mean:    {np.mean(valid_values):>10.6f}")
                self.stdout.write(f"  Std Dev: {np.std(valid_values):>10.6f}")
                self.stdout.write(f"  Min:     {np.min(valid_values):>10.6f}")
                self.stdout.write(f"  Max:     {np.max(valid_values):>10.6f}")
                
                # ✅ Print a visual representation of the first 20 valid values
                self.stdout.write("\n📊 Visual representation (normalized) of first 20 values:")
                
                # Normalize values between 0 and 1 for visualization
                min_val = np.min(valid_values)
                max_val = np.max(valid_values)
                range_val = max_val - min_val
                
                for i, value in enumerate(embedding_vector[:20]):
                    if np.isfinite(value):
                        # Normalize to 0-1 range and then scale to 0-40 characters
                        norm_value = (value - min_val) / range_val if range_val != 0 else 0.5
                        bar_length = int(norm_value * 40)
                        bar = '█' * min(bar_length, 40)  # Limit bar length to 40 characters
                        self.stdout.write(f"  [{i:2d}]: {value:>10.6f} {bar}")
                    else:
                        self.stdout.write(f"  [{i:2d}]: {value:>10.6f} [Invalid value]")
            else:
                self.stderr.write("❌ No valid values found in the embedding")
                
        except Exception as e:
            self.stderr.write(f"❌ Error processing embedding: {str(e)}") 