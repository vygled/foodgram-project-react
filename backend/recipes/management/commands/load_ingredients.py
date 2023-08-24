from csv import DictReader

from django.core.management import BaseCommand
from recipes.models import Ingredient

from foodgram.settings import BASE_DIR


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        with open(
            BASE_DIR / '../data/ingredients.csv',
            'r',
            encoding='UTF-8'
        ) as file:
            reader = DictReader(file)
            ingredients = []
            for row in reader:
                ingredients.append(Ingredient(
                    name=row['name'],
                    measurement_unit=row['measurement_unit']
                ))
        Ingredient.objects.bulk_create(ingredients)
