from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth.password_validation import validate_password


# -----------------------
# USER SERIALIZER
# -----------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'phone_number']



# -----------------------
# REGISTER SERIALIZER
# -----------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone_number', 'password', 'password2']

    # Validate password match
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    # Validate unique email
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already taken.")
        return value

    # Create user
    def create(self, validated_data):
        validated_data.pop('password2')  # remove confirm password

        user = CustomUser.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            phone_number=validated_data.get('phone_number')
        )

        user.set_password(validated_data['password'])
        user.save()
        return user
