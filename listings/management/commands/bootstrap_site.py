import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = "从部署环境初始化管理员；已存在的账号不会改动。"

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME", "")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")
        if not username or not password:
            self.stdout.write("未设置管理员初始化变量，跳过。")
            return
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write("管理员账号已存在，跳过。")
            return
        user = User(username=username, is_staff=True, is_superuser=True)
        try:
            validate_password(password, user)
        except ValidationError as error:
            raise CommandError("管理员初始密码不符合安全要求。") from error
        User.objects.create_superuser(username=username, password=password)
        self.stdout.write(self.style.SUCCESS("管理员账号已初始化。"))
