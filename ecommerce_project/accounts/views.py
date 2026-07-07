from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View

from .forms import AddressForm, CustomerProfileForm, LoginForm, ProfileUpdateForm, RegistrationForm
from .models import Address, CustomerProfile

User = get_user_model()


class UserLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = LoginForm

    def get_success_url(self):
        return reverse_lazy('products:product_list')


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('accounts:login')


class RegisterView(SuccessMessageMixin, CreateView):
    form_class = RegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:login')
    success_message = 'Account created successfully. You can now log in.'


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/profile.html'
    context_object_name = 'profile_user'

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = CustomerProfile.objects.get_or_create(user=self.request.user)
        context['profile'] = profile
        return context


class ProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile_update.html'
    success_message = 'Profile updated successfully.'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse_lazy('accounts:profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'profile_form' not in context:
            profile, _ = CustomerProfile.objects.get_or_create(user=self.request.user)
            context['profile_form'] = CustomerProfileForm(instance=profile)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
        profile_form = CustomerProfileForm(request.POST, instance=profile)

        if form.is_valid() and profile_form.is_valid():
            form.save()
            profile_form.save()
            messages.success(request, self.success_message)
            return redirect(self.get_success_url())

        return self.form_invalid(form)

    def form_invalid(self, form):
        profile, _ = CustomerProfile.objects.get_or_create(user=self.request.user)
        return self.render_to_response(
            self.get_context_data(form=form, profile_form=CustomerProfileForm(self.request.POST, instance=profile))
        )


class AddressListView(LoginRequiredMixin, ListView):
    model = Address
    template_name = 'accounts/address_list.html'
    context_object_name = 'addresses'

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)


class AddressCreateView(LoginRequiredMixin, CreateView):
    model = Address
    form_class = AddressForm
    template_name = 'accounts/address_form.html'
    success_url = reverse_lazy('accounts:address_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add Address'
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Address added successfully.')
        return super().form_valid(form)


class AddressUpdateView(LoginRequiredMixin, UpdateView):
    model = Address
    form_class = AddressForm
    template_name = 'accounts/address_form.html'
    success_url = reverse_lazy('accounts:address_list')

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Edit Address'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Address updated successfully.')
        return super().form_valid(form)


class AddressDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        address.delete()
        messages.success(request, 'Address deleted successfully.')
        return redirect('accounts:address_list')


class SetDefaultAddressView(LoginRequiredMixin, View):
    def post(self, request, pk):
        address = get_object_or_404(Address, pk=pk, user=request.user)
        Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
        address.is_default = True
        address.save()
        messages.success(request, f'{address.full_name} set as default address.')
        return redirect('accounts:address_list')
