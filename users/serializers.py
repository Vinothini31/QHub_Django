from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth.password_validation import validate_password


# -----------------------
# USER SERIALIZER
# -----------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email']


# -----------------------
# REGISTER SERIALIZER
# -----------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']

    # Validate unique email
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already taken.")
        return value

    # Create user
    def create(self, validated_data):
        user = CustomUser.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            is_active=True
        )

        user.set_password(validated_data['password'])
        user.save()
        return user
