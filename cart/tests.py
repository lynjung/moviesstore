from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth.models import User
from movies.models import Movie
from .models import Order, Item


class CartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('buyer', password='test-password')
        self.movie = Movie.objects.create(name='Example', price=12)
        self.add_url = f'/cart/{self.movie.id}/add/'

    def test_quantity_validation_and_replacement(self):
        for value in ['', 'abc', '1.5', '0', '-1', '11']:
            self.assertEqual(self.client.post(self.add_url, {'quantity': value}).status_code, 400)
        self.assertEqual(self.client.post(self.add_url).status_code, 400)
        self.client.post(self.add_url, {'quantity': '2'})
        self.client.post(self.add_url, {'quantity': '3'})
        self.assertEqual(self.client.session['cart'], {str(self.movie.id): 3})
        self.assertContains(self.client.get('/cart/'), '$36')

    def test_mutations_require_post(self):
        self.client.force_login(self.user)
        for url in [self.add_url, '/cart/clear/', '/cart/purchase/']:
            self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(Order.objects.count(), 0)

    def test_purchase_history_is_private_and_uses_snapshot_price(self):
        self.client.post(self.add_url, {'quantity': '2'})
        self.assertRedirects(self.client.post('/cart/purchase/'), '/accounts/login/?next=/cart/purchase/')
        self.client.force_login(self.user)
        self.assertEqual(self.client.post('/cart/purchase/').status_code, 200)
        order = Order.objects.get()
        self.assertEqual(order.total, 24)
        self.assertEqual(order.item_set.get().quantity, 2)
        self.assertEqual(self.client.session['cart'], {})
        self.client.post('/cart/purchase/')
        self.assertEqual(Order.objects.count(), 1)
        self.movie.price = 99
        self.movie.save()
        response = self.client.get('/accounts/orders/')
        self.assertContains(response, '$12')
        self.assertContains(response, f'href="/movies/{self.movie.id}/"')
        self.assertNotContains(response, '$99')
        self.client.force_login(User.objects.create_user('other'))
        self.assertNotContains(self.client.get('/accounts/orders/'), f'Order #{order.id}')

    def test_stale_or_invalid_session_cart_is_cleaned(self):
        for cart in [{'invalid': '2', str(self.movie.id): '-1'}, {'999999': '2'}, ['broken']]:
            session = self.client.session
            session['cart'] = cart
            session.save()
            self.assertEqual(self.client.get('/cart/').status_code, 200)
            self.client.force_login(self.user)
            self.client.post('/cart/purchase/')
        self.assertEqual(Order.objects.count(), 0)

    def test_purchase_rolls_back_if_item_creation_fails(self):
        self.client.force_login(self.user)
        self.client.post(self.add_url, {'quantity': 2})
        with patch('cart.views.Item.objects.create', side_effect=RuntimeError('test failure')):
            with self.assertRaises(RuntimeError):
                self.client.post('/cart/purchase/')
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Item.objects.count(), 0)
        self.assertEqual(self.client.session['cart'], {str(self.movie.id): 2})
