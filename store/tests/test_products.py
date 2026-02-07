# store/tests/test_products.py
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
# from .factories import ProductFactory
from django.contrib.auth import get_user_model

User = get_user_model()

class ProductAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='test', password='pass')
        self.client.force_authenticate(user=self.user)

    def test_create_product(self):
        url = reverse('product-list')
        payload = {
            "name": "کالای تست",
            "price": "199.99",
            "stock": 10
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], payload['name'])
        # self.assertTrue(Product.objects.filter(name="کالای تست").exists())