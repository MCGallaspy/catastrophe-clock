from django.contrib.auth import get_user_model
from django.views.generic import TemplateView

from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser, )


class ClockView(TemplateView):
    """
    The view for the main page -- a clock that counts down until some catastrophe has been calculated to occur.
    """
    pass