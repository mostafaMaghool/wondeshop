import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
django.setup()

from store.models import Product
from django.db import transaction

def create_random_products(count: int =10):
    objs =[]
    for _ in range(count):
        objs.append(
            Product(
                name=f'product-{_+1}',
                price=round(( _ + 1)*100,2),
                description='description',
                image_url='store/product_img/default.jpg',
                stock=round(( _ + 1)*10.5,2),
            )
        )
    with transaction.atomic():
        Product.objects.bulk_create(objs)
    print(f'محصول رندوم ایجاد شد')

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Create random Product entries')
    parser.add_argument('-n','--number',type=int,default=10,help='Number of random products to create')
    args = parser.parse_args()
    create_random_products(args.number)