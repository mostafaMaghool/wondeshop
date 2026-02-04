#Create, Delete, Ownership and quantity validation
import pytest

from store.models import Product, Order, OrderItem


#Create
@pytest.mark.django_db
def test_create_order_item(auth_client, user):
    product = Product.objects.create(
        name="Laptop",
        description="Good laptop device",
        price=1000,
        stock=10
    )

    order = Order.objects.create(user=user, follow_up_code=111)

    response = auth_client.post("/orderItems/", {
        "order": order.id,
        "product": product.id,
        "quantity": 2
    })

    assert response.status_code == 201

#Quantity Validation
@pytest.mark.django_db
def test_order_item_quantity_validation(auth_client, user):
    product = Product.objects.create(
        name="Laptop",
        description="Good laptop device",
        price=1000,
        stock=10
    )

    order = Order.objects.create(user=user, follow_up_code=111)

    response = auth_client.post("/orderItems/", {
        "order": order.id,
        "product": product.id,
        "quantity": 0
    })

    assert response.status_code == 400

#Ownership protection
@pytest.mark.django_db
def test_cannot_add_item_to_other_users_order(auth_client, django_user_model):
    other = django_user_model.objects.create_user(
        username="other",
        password="pass1234"
    )

    product = Product.objects.create(
        name="Laptop",
        description="Good laptop device",
        price=1000,
        stock=10
    )

    order = Order.objects.create(user=other, follow_up_code=111)

    response = auth_client.post("/orderItems/", {
        "order": order.id,
        "product": product.id,
        "quantity": 1
    })

    assert response.status_code in (403, 404)

#Delete
@pytest.mark.django_db
def test_delete_order_item(auth_client, user):
    product = Product.objects.create(
        name="Laptop",
        description="Good laptop device",
        price=1000,
        stock=10
    )

    order = Order.objects.create(user=user, follow_up_code=111)

    item = OrderItem.objects.create(
        order=order,
        product=product,
        quantity=1
    )

    response = auth_client.delete(f"/orderItems/{item.id}")
    assert response.status_code == 204