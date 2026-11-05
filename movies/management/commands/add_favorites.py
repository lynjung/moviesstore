"""Add the approved catalog selections without replacing existing movies."""
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from movies.models import Movie


POSTERS = Path(__file__).resolve().parents[2] / 'catalog' / 'posters'
MOVIES = [
    ('La La Land', 11, 'la-la-land.png',
     'An aspiring actress and a jazz pianist fall in love while chasing their dreams in Los Angeles.'),
    ('20th Century Girl', 11, '20th-century-girl.jpg',
     'In 1999, a Korean teenager helps her best friend learn about a crush, only to discover her own first love.'),
    ('Baby Driver', 12, 'baby-driver.jpg',
     'A talented getaway driver moves to the beat of his favorite songs while searching for a way out of a life of crime.'),
    ('Interstellar', 14, 'interstellar.jpg',
     'As Earth becomes harder to inhabit, a former pilot joins a mission beyond the solar system to find humanity a new home.'),
]


class Command(BaseCommand):
    help = 'Add La La Land, 20th Century Girl, Baby Driver, and Interstellar once.'

    def handle(self, *args, **options):
        # Read every asset before changing the database.
        for _, _, poster, _ in MOVIES:
            if not (POSTERS / poster).is_file():
                raise FileNotFoundError(POSTERS / poster)
        with transaction.atomic():
            for name, price, poster, description in MOVIES:
                if Movie.objects.filter(name__iexact=name).exists():
                    self.stdout.write(f'Already present: {name}')
                    continue
                movie = Movie(name=name, price=price, description=description)
                with (POSTERS / poster).open('rb') as image:
                    movie.image.save(poster, File(image), save=False)
                movie.save()
                self.stdout.write(self.style.SUCCESS(f'Added: {name} (${price})'))
