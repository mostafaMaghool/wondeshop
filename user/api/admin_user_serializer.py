import os

from django.contrib.auth import get_user_model
from django.db.models import Max
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.relations import StringRelatedField
from rest_framework.serializers import ModelSerializer

from user.api.admin_models import Article, Media, Icon, AuditLog, IconCategory

User = get_user_model()


class UserAdminSerializer(serializers.ModelSerializer):
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
        # ordering = ["order", "id"]


class MediaSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Media
        fields = (
            "id",
            "file",
            "file_url",
            "type",
            "order",
            "content_type",
            "object_id",
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

    def create(self, validated_data):
        content_type = validated_data.get("content_type")
        object_id = validated_data.get("object_id")

        if content_type and object_id:
            max_order = (
                    Media.objects
                    .filter(
                        content_type=content_type,
                        object_id=object_id,
                    )
                    .aggregate(max_order=Max("order"))
                    .get("max_order") or 0
            )

            validated_data["order"] = max_order + 1

        return super().create(validated_data)

    def validate(self, attrs):
        file = attrs.get("file")
        media_type = attrs.get("type")

        ext = os.path.splitext(file.name)[1].lower()

        rules = {
            "image": {
                "ext": [".jpg", ".jpeg", ".png", ".webp"],
                "max_size": 5 * 1024 * 1024,
            },
            "video": {
                "ext": [".mp4", ".mkv"],
                "max_size": 50 * 1024 * 1024,
            },
            "icon": {
                "ext": [".svg", ".png", ".tiff"],
                "max_size": 1 * 1024 * 1024,
            },
        }

        rule = rules.get(media_type)
        if not rule:
            raise serializers.ValidationError("Invalid media type")

        if ext not in rule["ext"]:
            raise serializers.ValidationError("Invalid file format")

        if file.size > rule["max_size"]:
            raise serializers.ValidationError("File too large")

        return attrs


class IconSerializer(ModelSerializer):
    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    class Meta:
        model = Icon
        fields = (
            "id",
            "name",
            "file",
            "category",
            "category_name",
            "created_at",
        )

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class IconCategorySerializer(serializers.ModelSerializer):
    icons_count = serializers.IntegerField(
        source="icons.count",
        read_only=True,
    )

    class Meta:
        model = IconCategory
        fields = (
            "id",
            "name",
            "description",
            "is_active",
            "icons_count",
        )


class AuditLogSerializer(ModelSerializer):
    user = StringRelatedField()

    class Meta:
        model = AuditLog
        fields = "__all__"
        read_only_fields = fields
