import pytest

from store.models import Order

#CRUD, ownership protection included

#List
@pytest.mark.django_db
def test_list_orders(auth_client, user):
    Order.objects.create(user=user, follow_up_code=111)
    response = auth_client.get("/orders/")
    assert response.status_code == 200

#Retrieve
@pytest.mark.django_db
def test_retrieve_order(auth_client, user):
    order = Order.objects.create(user=user, follow_up_code=111)
    response = auth_client.get(f"/orders/{order.id}")
    assert response.status_code == 200

#Create
@pytest.mark.django_db
def test_create_order(auth_client):
    response = auth_client.post("/orders/", {
        "follow_up_code": 123456
    })
    assert response.status_code == 201

#Update with changes
@pytest.mark.django_db
def test_update_order_status(auth_client, user):
    order = Order.objects.create(user=user, follow_up_code=111)

    response = auth_client.patch(
        f"/orders/{order.id}",
        {"status": "CONFIRMED"}
    )

    assert response.status_code == 200


#Delete
@pytest.mark.django_db
def test_delete_order(auth_client, user):
    order = Order.objects.create(user=user, follow_up_code=111)
    response = auth_client.delete(f"/orders/{order.id}")
    assert response.status_code == 204

#Ownership protection
@pytest.mark.django_db
def test_user_cannot_access_other_users_order(auth_client, django_user_model):
    other = django_user_model.objects.create_user(
        username="other",
        password="pass1234"
    )

    order = Order.objects.create(user=other, follow_up_code=111)
    response = auth_client.get(f"/orders/{order.id}")
    assert response.status_code == 404