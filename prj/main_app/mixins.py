from django.views.generic.detail import SingleObjectMixin
from django.views.generic import View

from .models import Category, Cart, Customer, Product


class CategoryDetailMixin(SingleObjectMixin):

    def get_context_data(self, **kwargs):
        if isinstance(self.get_object(), Category):
            context = super().get_context_data(**kwargs)
            if self.request.user.is_authenticated:
                customer = Customer.objects.get(user=self.request.user)
                context['cart'] = Cart.objects.get(owner=customer, in_order=False)
            context['categories'] = Category.objects.all()
            context['products'] = Product.objects.filter(in_stock=True, category=self.get_object())
            return context
        context = super().get_context_data(**kwargs)
        customer = Customer.objects.get(user=self.request.user)
        context['cart'] = Cart.objects.get(owner=customer, in_order=False)
        context['categories'] = Category.objects.all()
        return context


class CartMixin(View):

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            customer = Customer.objects.filter(user=request.user).first()
            cart = Cart.objects.filter(owner=customer, in_order=False).first()
            if not cart:
                cart = Cart.objects.create(owner=customer)
        else:
            cart = Cart.objects.filter(for_anonymous_user=True, in_order=False).first()
            if not cart:
                cart = Cart.objects.create(for_anonymous_user=True)
        self.cart = cart
        return super().dispatch(request, *args, **kwargs)
