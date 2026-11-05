from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Movie, Review


class MovieTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('reviewer', password='test-password')
        self.other = User.objects.create_user('other')
        self.movie = Movie.objects.create(name='Example', price=12, description='Example movie')
        self.other_movie = Movie.objects.create(name='Other', price=5)
        self.review = Review.objects.create(user=self.user, movie=self.movie, comment='Original')

    def url(self, action, movie=None):
        return reverse('movies.' + action, kwargs={'id': (movie or self.movie).id, 'review_id': self.review.id})

    def test_public_pages_and_missing_movie(self):
        for url in ['/', '/about', '/movies/', f'/movies/{self.movie.id}/', '/cart/', '/accounts/login/', '/accounts/signup']:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertEqual(self.client.get('/movies/999999/').status_code, 404)
        self.assertContains(self.client.get('/movies/?search=absent'), 'No movies found')

    def test_review_ownership_and_movie_binding(self):
        self.client.force_login(self.other)
        for action in ['edit_review', 'delete_review']:
            self.assertEqual(self.client.post(self.url(action), {'comment': 'Changed'}).status_code, 404)
        self.client.force_login(self.user)
        for action in ['edit_review', 'delete_review', 'report_review']:
            self.assertEqual(self.client.post(self.url(action, self.other_movie), {'comment': 'Changed'}).status_code, 404)
        self.review.refresh_from_db()
        self.assertEqual(self.review.comment, 'Original')

    def test_review_validation_and_edit(self):
        self.client.force_login(self.user)
        create = reverse('movies.create_review', kwargs={'id': self.movie.id})
        for comment in ['', '   ', 'x' * 256]:
            self.client.post(create, {'comment': comment})
            self.assertEqual(self.client.post(self.url('edit_review'), {'comment': comment}).status_code, 200)
        self.client.post(create, {})
        self.assertEqual(Review.objects.count(), 1)
        self.client.post(self.url('edit_review'), {'comment': 'Updated'})
        self.review.refresh_from_db()
        self.assertEqual(self.review.comment, 'Updated')
        self.client.post(create, {'comment': 'New'})
        self.assertEqual(Review.objects.count(), 2)

    def test_review_mutations_require_post_and_csrf(self):
        self.client.force_login(self.user)
        for action in ['delete_review', 'report_review']:
            self.assertEqual(self.client.get(self.url(action)).status_code, 405)
        from django.test import Client
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.user)
        self.assertEqual(csrf_client.post(self.url('delete_review')).status_code, 403)
        self.client.post(self.url('report_review'))
        self.assertNotContains(self.client.get(f'/movies/{self.movie.id}/'), 'Original')
        self.client.post(self.url('delete_review'))
        self.assertFalse(Review.objects.filter(pk=self.review.pk).exists())


class FavoriteCatalogTests(TestCase):
    def test_additions_preserve_existing_movies_and_are_repeatable(self):
        import tempfile
        from io import StringIO
        from django.core.management import call_command
        original = Movie.objects.create(name='Inception', price=12, description='Original')
        with tempfile.TemporaryDirectory() as media, self.settings(MEDIA_ROOT=media):
            call_command('add_favorites', stdout=StringIO())
            self.assertEqual(Movie.objects.count(), 5)
            for name in ['La La Land', '20th Century Girl', 'Baby Driver', 'Interstellar']:
                movie = Movie.objects.get(name=name)
                self.assertTrue(movie.image.storage.exists(movie.image.name))
                self.assertEqual(self.client.get(f'/movies/{movie.id}/').status_code, 200)
            favorite = Movie.objects.get(name='La La Land')
            favorite.price = 13
            favorite.save()
            call_command('add_favorites', stdout=StringIO())
            self.assertEqual(Movie.objects.count(), 5)
            favorite.refresh_from_db()
            self.assertEqual(favorite.price, 13)
            original.refresh_from_db()
            self.assertEqual(original.description, 'Original')
