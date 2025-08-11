from .models import MenuItem, Category, Order, OrderItem, Cart
from rest_framework import serializers
from django.contrib.auth.models import User

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category']
        extra_kwargs = {
            'category': {'required': True},
            'price' : {'required': True, 'max_digits': 6, 'decimal_places': 2},
            'title': {'required': True, 'max_length': 255}
        }

class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['id', 'user', 'menuitem', 'quantity', 'unit_price', 'price']
        read_only_fields = ['user', 'unit_price', 'price']
        extra_kwargs = {
            'menuitem': {'required': True},
            'quantity': {'required': True, 'min_value': 1},
            'unit_price': {'required': True, 'max_digits': 6, 'decimal_places': 2}
        }

class OrderSerializer(serializers.ModelSerializer):
    delivery_crew = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),  # Aquí ponemos todos para validar después
        allow_null=True,
        required=False
    )

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date']
        read_only_fields = ['user', 'date', 'total']

    def validate_delivery_crew(self, value):
        if value is not None:
            # Comprueba si el usuario está en el grupo "Delivery crew"
            if not value.groups.filter(name='Delivery crew').exists():
                raise serializers.ValidationError("the user is not from Delivery crew.")
        return value

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'menuitem', 'quantity', 'unit_price', 'price']
        read_only_fields = ['order', 'unit_price', 'price']
        extra_kwargs = {
            'menuitem': {'required': True},
            'quantity': {'required': True, 'min_value': 1},
        }