from django.urls import include, path
from . import views

urlpatterns = [
    path('auth/', include('djoser.urls')),                  # Registro, login, logout, etc.
    path('auth/', include('djoser.urls.authtoken')),        # Para login por token
    path('groups/manager/users', views.ManagerGroupView.as_view()),  # Vista para obtener usuarios del grupo Manager
    path('groups/manager/users/<int:user_id>', views.RemoveManagerUserView.as_view()),  # Vista para eliminar usuario del grupo Manager
    path('groups/delivery-crew/users', views.DeliveryGroupView.as_view()),  # Vista para obtener usuarios del grupo Delivery-crew
    path('groups/delivery-crew/users/<int:user_id>', views.RemoveDeliveryUserView.as_view()),  # Vista para eliminar usuario del grupo Delivery-crew
    path('menu-items/', views.MenuItemView.as_view(), name='menu-items'),  # Vista para MenuItem
    path('menu-items/<int:pk>/', views.MenuItemDetailView.as_view(), name='menu-item-detail'),  # Vista para detalle de MenuItem
    path('cart/menu-items/', views.CartView.as_view(), name='cart'),
    path('orders/', views.OrderView.as_view(), name='orders'),
    path('orders/<int:pk>/', views.OrderItemView.as_view(), name='order-detail'),  # Vista para detalle de Order
    path('categories/', views.CategoryView.as_view(), name='categories')

]