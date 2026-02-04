import pytest

from store.models import Address


# Address List,Create(valid and invalid), Update, Delete API test; also ownership protection and default address are tested

@pytest.mark.django_db
def test_cannot_access_other_users_address(auth_client, django_user_model):
    other = django_user_model.objects.create_user(
        username="other",
        password="pass1234"
    )

    address = Address.objects.create(
        user=other,
        title="Other",
        city="Paris",
        state="IDF",
        postal_code="75001",
        country="FR",
        is_default=False
    )

    response = auth_client.get(f"/address/{address.id}/")
    assert response.status_code == 404

@pytest.mark.django_db
def test_list_addresses_only_returns_user_addresses(auth_client, user):
    Address.objects.create(
    user=user,
    title="Home",
    city="Berlin",
    state="BE",
    postal_code="10115",
    country="DE",
    is_default=True
    )


    response = auth_client.get("/address/")
    assert response.status_code == 200
    assert len(response.data["results"]) == 1

@pytest.mark.django_db
def test_create_address(auth_client):
    response = auth_client.post("/address/", {
        "title": "Home",
        "city": "Berlin",
        "state": "BE",
        "postal_code": "10115",
        "country": "Germany",
        "is_default": True
    })

    assert response.status_code == 201

@pytest.mark.django_db
def test_create_address_invalid_postal_code(auth_client):
    response = auth_client.post("/address/", {
    "title": "Home",
    "city": "Berlin",
    "state": "BE",
    "postal_code": "ABC",
    "country": "DE",
    "is_default": False
    })
    assert response.status_code == 400

@pytest.mark.django_db
def test_only_one_default_address_allowed(auth_client):
    auth_client.post("/address/", {
        "title": "Home",
        "city": "Berlin",
        "state": "BE",
        "postal_code": "10115",
        "country": "DE",
        "is_default": True
    })

    response = auth_client.post("/address/", {
        "title": "Office",
        "city": "Berlin",
        "state": "BE",
        "postal_code": "10117",
        "country": "DE",
        "is_default": True
    })

    assert response.status_code == 400

@pytest.mark.django_db
def test_retrieve_address(auth_client, user):
    address = Address.objects.create(
        user=user,
        title="Home",
        city="Berlin",
        state="BE",
        postal_code="10115",
        country="DE",
        is_default=True
    )

    response = auth_client.get(f"/address/{address.id}/")
    assert response.status_code == 200

@pytest.mark.django_db
def test_update_address(auth_client, user):
    address = Address.objects.create(
        user=user,
        title="Home",
        city="Berlin",
        state="BE",
        postal_code="10115",
        country="DE",
        is_default=False
    )

    response = auth_client.patch(
        f"/address/{address.id}/",
        {"city": "Munich"}
    )

    assert response.status_code == 200
    assert response.data["city"] == "Munich"

@pytest.mark.django_db
def test_delete_address(auth_client, user):
    address = Address.objects.create(
        user=user,
        title="Home",
        city="Berlin",
        state="BE",
        postal_code="10115",
        country="DE",
        is_default=False
    )

    response = auth_client.delete(f"/address/{address.id}/")
    assert response.status_code == 204



#endregion
#Address DetailView test

