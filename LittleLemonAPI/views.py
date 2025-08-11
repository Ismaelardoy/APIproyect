from django.shortcuts import get_object_or_404, render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User, Group
from .models import MenuItem, Category, Order, OrderItem, Cart
from .serializers import MenuItemSerializer, CategorySerializer, OrderSerializer, OrderItemSerializer, CartSerializer
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from django.utils import timezone
from django.core.exceptions import PermissionDenied
# Create your views here.
class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser
    
class IsManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.is_superuser or user.groups.filter(name="Manager").exists())

class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.is_superuser or not user.groups.exists())
    
class IsDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.is_superuser or user.groups.filter(name="Delivery crew").exists())

#Manager API views
class ManagerGroupView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        try:
            group = Group.objects.get(name="Manager")  
        except Group.DoesNotExist:
            return Response({"error": "Group Manager not found"}, status=status.HTTP_404_NOT_FOUND)

        users = group.user_set.all()
        data = [{"id": u.id, "username": u.username} for u in users]
        return Response(data)
    
    def post(self, request):
        user_id = request.data.get("user_id")
        try:
            user = User.objects.get(id=user_id)
            group = Group.objects.get(name="Manager")
            group.user_set.add(user)
            return Response({"message": "User added to Manager group"}, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({"error": "Group Manager not found"}, status=status.HTTP_404_NOT_FOUND)

class RemoveManagerUserView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            group = Group.objects.get(name="Manager")
            group.user_set.remove(user)
            return Response({"message": "User removed from Manager group"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({"error": "Group Manager not found"}, status=status.HTTP_404_NOT_FOUND)




class DeliveryGroupView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        try:
            group = Group.objects.get(name="Delivery crew")
        except Group.DoesNotExist:
            return Response({"error": "Group Delivery crew not found"}, status=status.HTTP_404_NOT_FOUND)
        
        users = group.user_set.all()
        data = [{"id": u.id, "username": u.username} for u in users]
        return Response(data)   
    
    def post(self, request):
        user_id = request.data.get("user_id")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            group = Group.objects.get(name="Delivery crew")
        except Group.DoesNotExist:
            return Response({"error": "Group Delivery crew not found"}, status=status.HTTP_404_NOT_FOUND)
        
        group.user_set.add(user)
        return Response({"message": "User added to Delivery crew group"}, status=status.HTTP_201_CREATED)
    
class RemoveDeliveryUserView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            group = Group.objects.get(name="Delivery crew")
        except Group.DoesNotExist:
            return Response({"error": "Group Delivery crew not found"}, status=status.HTTP_404_NOT_FOUND)
        
        group.user_set.remove(user)
        return Response({"message": "User removed from Delivery crew group"}, status=status.HTTP_200_OK)

#API views for MenuItem

class MenuItemView(generics.ListCreateAPIView):  
    serializer_class = MenuItemSerializer
    queryset = MenuItem.objects.all()
    filter_backends = [OrderingFilter]  # habilita ordenación
    ordering_fields = ['price']  # campos por los que se puede ordenar
    ordering = ['id']  # orden por defecto


    def get_queryset(self):
        queryset = MenuItem.objects.all()
        category_name = self.request.query_params.get('category')
        if category_name:
            queryset = queryset.filter(category__title__iexact=category_name)
        return queryset
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsManager()]
        return [IsAuthenticated()]
    

class MenuItemDetailView(APIView):
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'POST']:
            return [IsAuthenticated(), IsManager()]
        elif self.request.method == 'DELETE':
            return [IsAuthenticated(), IsSuperUser()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        try:
            menu_item = MenuItem.objects.get(pk=pk)
            serializer = MenuItemSerializer(menu_item)
            return Response(serializer.data)
        except MenuItem.DoesNotExist:
            return Response({"error": "Menu item not found"}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        try:
            menu_item = MenuItem.objects.get(pk=pk)
            serializer = MenuItemSerializer(menu_item, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except MenuItem.DoesNotExist:
            return Response({"error": "Menu item not found"}, status=status.HTTP_404_NOT_FOUND)
        
    def patch(self, request, pk):
        try:
            menu_item = MenuItem.objects.get(pk=pk)
            serializer = MenuItemSerializer(menu_item, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except MenuItem.DoesNotExist:
            return Response({"error": "Menu item not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        try:
            menu_item = MenuItem.objects.get(pk=pk)
            menu_item.delete()
            return Response({"message": "Menu item deleted"}, status=status.HTTP_204_NO_CONTENT)
        except MenuItem.DoesNotExist:
            return Response({"error": "Menu item not found"}, status=status.HTTP_404_NOT_FOUND)

class CartView(APIView):
    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = CartSerializer

    def get(self, request):
        user = request.user
        cart_items = Cart.objects.filter(user=user)
        serializer = self.serializer_class(cart_items, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        user = request.user
        data = request.data.copy()

        try:
            menuitem = MenuItem.objects.get(id=data['menuitem'])
        except MenuItem.DoesNotExist:
            return Response({"error": "Menu item not found"}, status=status.HTTP_404_NOT_FOUND)

        quantity = int(data['quantity'])
        unit_price = menuitem.price
        price = unit_price * quantity

        cart_item = Cart(user=user, menuitem=menuitem, quantity=quantity, unit_price=unit_price, price=price)
        cart_item.save()
        return Response({"message": "Item added to cart"}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        user = request.user
        Cart.objects.filter(user=user).delete()
        return Response({"message": "Cart cleared"}, status=status.HTTP_204_NO_CONTENT)
    

class OrderView(APIView):
    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.request.method in ['POST']:
            return [IsAuthenticated(), IsCustomer()]
        return [IsAuthenticated()]

    def get(self, request):
        user = request.user
        if not user.groups.exists(): #user gets orders only if they are a customer
            orders = Order.objects.filter(user=user)
            serializer = self.serializer_class(orders, many=True)
            return Response(serializer.data)
        elif user.groups.filter(name="Manager").exists(): #Managers can see all orders
            orders = Order.objects.all()
            serializer = self.serializer_class(orders, many=True)
            return Response(serializer.data)
        elif user.groups.filter(name="Delivery crew").exists(): #Delivery crew can see their own orders

            delivery_crew_group = Group.objects.get(name='Delivery crew')
            delivery_crew_users = delivery_crew_group.user_set.all()

            orders = Order.objects.filter(delivery_crew__in=delivery_crew_users)
            serializer = self.serializer_class(orders, many=True)
            return Response(serializer.data)

    def post(self, request):    #Only for customers
        user = request.user
        if not user.is_authenticated:
            return Response({"error": "Debes iniciar sesión"}, status=status.HTTP_401_UNAUTHORIZED)

        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            return Response({"error": "El carrito está vacío"}, status=status.HTTP_400_BAD_REQUEST)

        # 🔹 Calcular total de todos los items
        total = sum(item.menuitem.price * item.quantity for item in cart_items)

        # 🔹 Crear UNA sola orden
        order = Order.objects.create(user=user, total=total)

        # 🔹 Crear OrderItem para cada producto en el carrito
        for item in cart_items:
            OrderItem.objects.create(
            order=order,
            menuitem=item.menuitem,
            quantity=item.quantity,
            unit_price=item.menuitem.price,           
            price=item.menuitem.price * item.quantity
        )   

        # 🔹 Vaciar el carrito
        cart_items.delete()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class OrderItemView(APIView):
    serializer_class = OrderItemSerializer

    def get_permissions(self):
        if self.request.method in ['DELETE']:
            return [IsAuthenticated(), IsManager()]
        return [IsAuthenticated()]

    def get(self, request, pk):
        user = request.user
        order = Order.objects.get(pk=pk, user=user)
        if not user.groups.exists(): #user gets his orders only if they are a customer
            order_items = OrderItem.objects.filter(order=order)
            serializer = self.serializer_class(order_items, many=True)
            return Response(serializer.data)
        
    
    def put(self, request, pk):
        user = request.user
        if not user.groups.exists():  # Solo usuarios sin grupos (clientes)
            try:
                order_item = OrderItem.objects.get(pk=pk, order__user=user)
            except OrderItem.DoesNotExist:
                return Response({"error": "OrderItem not found or does not belong to the user"}, status=404)
        
            serializer = OrderItemSerializer(order_item, data=request.data, partial=False)  # para PUT usa partial=False
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif user.groups.filter(name="Manager").exists():
            try:
                order = Order.objects.get(pk=pk)
            except Order.DoesNotExist:
                return Response({"error": "Order not found"}, status=404)

            data = request.data.copy()

            # Validar campos permitidos para actualizar por manager
            allowed_fields = {'delivery_crew', 'status'}
            for field in data:
                if field not in allowed_fields:
                    return Response({"error": f"you cannot modify '{field}'"}, status=403)

            # Validar status
            if 'status' in data and data['status'] not in [0, 1]:
                return Response({"error": "Status must be 0 or 1"}, status=400)

            serializer = OrderSerializer(order, data=data, partial=True)  # partial=True para PATCH
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data)
        
    
    def patch(self, request, pk):
        user = request.user
        if not user.groups.exists():  # Solo usuarios sin grupos (clientes)
            try:
             order_item = OrderItem.objects.get(pk=pk, order__user=user)
            except OrderItem.DoesNotExist:
                return Response({"error": "OrderItem no encontrado o no pertenece al usuario"}, status=404)
            
            serializer = OrderItemSerializer(order_item, data=request.data, partial=True)  # para PATCH partial=True
            serializer.is_valid(raise_exception=True)
            serializer.save()
            
            return Response(serializer.data)
        
        elif user.groups.filter(name="Manager").exists():
            try:
                order = Order.objects.get(pk=pk)
            except Order.DoesNotExist:
                return Response({"error": "Order not found"}, status=404)

            data = request.data.copy()

            # Validar campos permitidos para actualizar por manager
            allowed_fields = {'delivery_crew', 'status'}
            for field in data:
                if field not in allowed_fields:
                    return Response({"error": f"you cannot modify '{field}'"}, status=403)

            # Validar status
            if 'status' in data and data['status'] not in [0, 1]:
                return Response({"error": "Status must be 0 or 1"}, status=400)

            serializer = OrderSerializer(order, data=data, partial=True)  # partial=True para PATCH
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data)
        elif user.groups.filter(name="Delivery crew").exists():
            try:
                delivery_crew_group = Group.objects.get(name="Delivery crew")
                delivery_crew_users = delivery_crew_group.user_set.all()
            
                # Buscar orden cuyo delivery_crew está en ese grupo
                order = Order.objects.get(pk=pk, delivery_crew__in=delivery_crew_users)
            except Order.DoesNotExist:
                return Response({"error": "Order not found or does not belong to the delivery crew"}, status=404)
            except Group.DoesNotExist:
                return Response({"error": "Delivery crew group not found"}, status=404)
            
            data = request.data.copy()

            # Validar campos permitidos para actualizar por delivery crew
            allowed_fields = {'status'}
            for field in data:
                if field not in allowed_fields:
                    return Response({"error": f"you cannot modify '{field}'"}, status=403)
            # Validar status
            if 'status' in data and data['status'] not in [0, 1]:
                return Response({"error": "Status must be 0 or 1"}, status=400)
            serializer = OrderSerializer(order, data=data, partial=True)  # partial=True para PATCH
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

    # Solo los managers pueden eliminar una orden

    def delete(self, request, pk):
        user = request.user
        if not user.groups.filter(name="Manager").exists():
            return Response({"error": "You do not have permission to delete this order"}, status=403)

        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=404)

        order.delete()
        return Response(status=204)

class CategoryView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]