from django.test import TestCase
from django.contrib.auth.models import User
from .forms import CustomErrorList


class AccountTests(TestCase):
    def test_signup_login_next_and_logout(self):
        response = self.client.post('/accounts/signup', {'username': 'newuser', 'password1': 'StrongExamplePass123!', 'password2': 'StrongExamplePass123!'})
        self.assertRedirects(response, '/accounts/login/')
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertContains(self.client.post('/accounts/login/', {}), 'incorrect')
        credentials = {'username': 'newuser', 'password': 'StrongExamplePass123!'}
        self.assertRedirects(self.client.post('/accounts/login/?next=/cart/', credentials), '/cart/')
        self.assertEqual(self.client.get('/accounts/logout/').status_code, 405)
        self.assertRedirects(self.client.post('/accounts/logout/'), '/')
        self.assertRedirects(self.client.post('/accounts/login/?next=https://example.com/', credentials), '/')

    def test_orders_login_redirect(self):
        self.assertRedirects(self.client.get('/accounts/orders/'), '/accounts/login/?next=/accounts/orders/')

    def test_error_list_escapes_html(self):
        errors = str(CustomErrorList(['<script>alert(1)</script>']))
        self.assertNotIn('<script>', errors)
        self.assertIn('&lt;script&gt;', errors)
