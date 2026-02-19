from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

# region Mostafa
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name',
                  'last_name', 'password')
        extra_kwargs = {
            'email': {'required': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password) 
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance

class RegisterSerializer(serializers.ModelSerializer):
    password_confirmation = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = [
            'id',               # اگر می‌خوای
            'username',         # یا email یا هر چیزی که استفاده می‌کنی
            'email',
            'password',
            'password_confirmation',   # ← این خط رو حتما اضافه کن
        ]

    def validate(self, data):
        if data['password'] != data['password_confirmation']:
            raise serializers.ValidationError("رمز عبور و تکرار آن یکسان نیستند")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirmation')   # حذف فیلد اضافی
        user = User.objects.create_user(**validated_data)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','first_name','last_name','username','phone','email')

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def save(self, **kwargs):
        token = RefreshToken(self.validated_data["refresh"])
        token.blacklist()

# endregion