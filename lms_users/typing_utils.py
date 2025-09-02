from typing import Type, cast

from django.contrib.auth import get_user_model

from .models import User

UserModel: Type[User] = cast(Type[User], get_user_model())
