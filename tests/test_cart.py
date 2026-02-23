from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from store.models import Cart
from django.db import IntegrityError

User = get_user_model()


class CartModelTest(TestCase):

    def test_cart_requires_user(self):
        with self.assertRaises(IntegrityError):
            Cart.objects.create()  # should fail

    def test_cart_creation_with_user(self):
        user = User.objects.create(
            username="testuser",
            password="12345678"
        )
        cart = Cart.objects.create(user=user)

        self.assertIsNotNone(cart.id)
        self.assertEqual(cart.user, user)

    def test_cart_user_field_is_not_nullable(self):
        field = Cart._meta.get_field("user")
        self.assertFalse(field.null)

    def test_user_has_only_one_cart(self):
        user = User.objects.create(
            username="uniqueuser",
            password="12345678"
        )

        Cart.objects.create(user=user)

        with self.assertRaises(Exception):
            Cart.objects.create(user=user)


