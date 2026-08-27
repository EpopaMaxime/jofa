from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User


class EmailOrUsernameModelBackend(ModelBackend):
    """Allow login with username or email address."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None

        user = self._get_user_by_identifier(username)
        if user is None:
            User().set_password(password)
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def _get_user_by_identifier(self, identifier):
        identifier = (identifier or '').strip()
        if not identifier:
            return None
        qs = User.objects
        if '@' in identifier:
            matches = list(qs.filter(email__iexact=identifier).order_by('id')[:2])
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                return matches[0]
            return None
        try:
            return qs.get(username__iexact=identifier)
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            return qs.filter(username__iexact=identifier).order_by('id').first()
