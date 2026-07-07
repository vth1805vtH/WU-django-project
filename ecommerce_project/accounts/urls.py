from django.urls import path

from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_update'),
    path('addresses/', views.AddressListView.as_view(), name='address_list'),
    path('addresses/add/', views.AddressCreateView.as_view(), name='address_add'),
    path('addresses/<int:pk>/edit/', views.AddressUpdateView.as_view(), name='address_edit'),
    path('addresses/<int:pk>/delete/', views.AddressDeleteView.as_view(), name='address_delete'),
    path('addresses/<int:pk>/set-default/', views.SetDefaultAddressView.as_view(), name='address_set_default'),
]
