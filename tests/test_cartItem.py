from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from store.models import Product, Cart, Category
from user.models import User


class CartItemAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="itemuser",
            password="12345678"
        )

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        self.category = Category.objects.create(name="Test Cat")

        self.product = Product.objects.create(
            name="Test Product",
            description="Test description long enough",
            price=100,
            stock=10,
            category=self.category,  # adjust properly
            slug="test-product"
        )
        Product.objects.create(
            name="Test Product 2",
            description="another Test description long enough",
            price=50,
            stock=30,
            category=self.category,  # adjust properly
            slug="second-test-product"
        )

    def test_cart_item_creates_cart_automatically(self):
        response = self.client.post("/cart-items/", {
            "product": self.product.id,
            "quantity": 4
        })
        print(response.data)
        self.assertEqual(response.status_code, 201)

        # Cart should now exist
        self.assertTrue(Cart.objects.filter(user=self.user).exists())

        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.items.count(), 1)


    def test_user_only_sees_own_cart_items(self):
        # create item
        self.client.post("/cart-items/", {
            "product": self.product.id,
            "quantity": 1
        })
        self.client.post("/cart-items/", {
            "product": self.product.id + 1,
            "quantity": 6
        })

        response = self.client.get("/cart-items/")

        print(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_anonymous_user_cannot_create_cart_item(self):
        self.client.credentials()  # remove auth

        response = self.client.post("/cart-items/", {
            "product": self.product.id,
            "quantity": 1
        })

        self.assertEqual(response.status_code, 401)
        self.assertEqual(Cart.objects.count(), 0)


    def test_cart_is_attached_to_authenticated_user(self):
        response = self.client.post("/cart-items/", {
            "product": self.product.id,
            "quantity": 2
        })

        self.assertEqual(response.status_code, 201)

        cart = Cart.objects.first()
        self.assertIsNotNone(cart.user)
        self.assertEqual(cart.user, self.user)


    def test_same_product_updates_quantity(self):
        self.client.post("/cart-items/", {
            "product": self.product.id,
            "quantity": 2
        })

        self.client.post("/cart-items/", {
            "product": self.product.id,
            "quantity": 3
        })

        cart = Cart.objects.get(user=self.user)
        item = cart.items.get(product=self.product)

        self.assertEqual(cart.items.count(), 1)
        print(item.quantity)
        self.assertEqual(item.quantity, 5)

    def test_user_cannot_see_other_users_cart_items(self):
        # create item for self.user
        self.client.post("/cart-items/", {
            "product": self.product.id,
            "quantity": 2
        })

        # create second user
        other_user = User.objects.create_user(
            username="other",
            password="12345678"
        )

        refresh = RefreshToken.for_user(other_user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}"
        )

        response = self.client.get("/cart-items/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)


    def test_invalid_product_returns_400(self):
        response = self.client.post("/cart-items/", {
            "product": 9999,
            "quantity": 1
        })

        self.assertEqual(response.status_code, 400)