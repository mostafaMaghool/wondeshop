from rest_framework import serializers
from django.contrib.auth import get_user_model

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
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirmation = serializers.CharField(write_only=True)
    extra_kwargs = {
        "password": {"write_only": True}
    }
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email','phone', 'first_name',
                  'last_name', 'password','Password_confirmation')
        
    def validate(self, data):
        if data["password"] != data["password_confirmation"]:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop("password_confirmation")
        user = User.objects.create_user(**validated_data)
        user.is_active = True
        user.is_staff = True
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','first_name','last_name','username','phone','email')

# endregion