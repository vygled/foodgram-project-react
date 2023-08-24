import io
from rest_framework import renderers

SHOPPING_CART_HEADERS = ["ingredient", "measurement_unit", "amount"]


class TXTShoppingCartRenderer(renderers.BaseRenderer):

    media_type = "text/plain"
    format = "txt"

    def render(self, data, accepted_media_type=None, renderer_context=None):

        text_buffer = io.StringIO()
        text_buffer.write(
            ' '.join(header for header in SHOPPING_CART_HEADERS) + '\n'
        )

        for ingredients_data in data:
            text_buffer.write(
                ' '.join(
                    str(sd) for sd in list(ingredients_data.values())
                ) + '\n'
            )

        return text_buffer.getvalue()
