import os
import numpy as np
from django.core.management.base import BaseCommand
from movie.models import Movie
from openai import OpenAI
from dotenv import load_dotenv

class Command(BaseCommand):
    help = "Generate and store embeddings for all movies in the database"

    def handle(self, *args, **kwargs):
        # ✅ Load OpenAI API key
        load_dotenv('../api_keys.env')
        client = OpenAI(api_key=os.environ.get('openai_apikey'))

        # ✅ Get all movies
        movies = Movie.objects.all()
        self.stdout.write(f"Found {movies.count()} movies to process")

        def get_embedding(text):
            response = client.embeddings.create(
                input=[text],
                model="text-embedding-3-small"
            )
            return np.array(response.data[0].embedding, dtype=np.float32)

        # ✅ Iterate through movies and generate embeddings
        for movie in movies:
            try:
                # Generate embedding
                emb = get_embedding(movie.description)
                
                # Verify embedding is valid
                if not np.all(np.isfinite(emb)):
                    self.stderr.write(f"❌ Invalid embedding generated for {movie.title}")
                    continue
                    
                # Store embedding as binary
                movie.emb = emb.tobytes()
                movie.save()
                
                # Verify the stored embedding
                stored_emb = np.frombuffer(movie.emb, dtype=np.float32)
                if not np.array_equal(emb, stored_emb):
                    self.stderr.write(f"❌ Embedding verification failed for {movie.title}")
                    continue
                    
                self.stdout.write(self.style.SUCCESS(f"✅ Embedding stored for: {movie.title}"))
                
            except Exception as e:
                self.stderr.write(f"❌ Failed to generate embedding for {movie.title}: {e}")

        self.stdout.write(self.style.SUCCESS("🎯 Finished generating embeddings for all movies")) 