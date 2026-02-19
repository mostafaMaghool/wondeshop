from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer

from user.api.admin_models import Article, Media, Icon

User = get_user_model()

class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "is_active",
            "is_staff",
            "date_joined",
        )
        read_only_fields = ("email", "date_joined")

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = "__all__"

class MediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Media
        fields = (
            "id",
            "file",
            "file_url",
            "type",
            "created_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "file_url",
        )

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class IconSerializer(ModelSerializer):
    file_url = SerializerMethodField(read_only=True)

    class Meta:
        model = Icon
        fields = (
            "id",
            "name",
            "file",
            "file_url",
            "created_at",
        )
        read_only_fields = (
            "id",
            "created_at",
            "file_url",
        )

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
