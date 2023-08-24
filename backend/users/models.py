from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Subscription(models.Model):

    subscriber = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscription',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'author'],
                name='unique_subscriber_author')]
