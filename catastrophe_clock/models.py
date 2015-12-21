from django.db import models


class Catastrophe(models.Model):
    arrival_date = models.DateTimeField(
        help_text="When this catastrophe will occur."
    )
    name = models.CharField(
        max_length=255,
        help_text="What this catastrophe is called."
    )
    description = models.TextField(
        help_text="A brief description of the catastrophe."
    )
