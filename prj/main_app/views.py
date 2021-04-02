from django.db import transaction
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.views.generic import DetailView, View
from django.contrib import messages
from .models import Product, Category, CartProduct, Customer

from .mixins import CategoryDetailMixin, CartMixin

from .forms import OrderForm


class BaseView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        categories = Category.objects.all()
        products = Product.objects.filter(slug__contains='pan')[:6]
        context = {
            'ct_model': products.model._meta.model_name,
            'categories': categories,
            'products': products,
            'cart': self.cart
        }
        return render(request, 'base.html', context)


class ProductDetailView(CartMixin, CategoryDetailMixin, DetailView):
    model = Product
    queryset = Product.objects.all()
    context_object_name = 'product'
    template_name = 'product_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ct_model'] = self.model._meta.model_name
        return context


class CategoryDetailView(CartMixin, CategoryDetailMixin, DetailView):
    model = Category
    queryset = Category.objects.all()
    context_object_name = 'category'
    template_name = 'category_detail.html'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ct_model'] = self.model._meta.model_name
        return context


class AddToCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        cart_product, created = CartProduct.objects.get_or_create(cart=self.cart, product=product)
        self.cart.save()
        messages.add_message(request, messages.INFO, 'Товар успішно доданий')
        return HttpResponseRedirect('/cart/')


class DeleteFromCartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        CartProduct.objects.get(cart=self.cart, product=product).delete()
        self.cart.save()
        messages.add_message(request, messages.INFO, 'Товар успішно видалений')
        return HttpResponseRedirect('/cart/')


class ChangeQtyView(CartMixin, View):

    def post(self, request, *args, **kwargs):
        ct_model, product_slug = kwargs.get('ct_model'), kwargs.get('slug')
        product = Product.objects.get(slug=product_slug)
        cart_product = CartProduct.objects.get(cart=self.cart, product=product)
        qty = int(request.POST.get('qty'))
        cart_product.qty = qty
        cart_product.save()
        self.cart.save()
        messages.add_message(request, messages.INFO, 'Кількість товару успішно змінена')
        return HttpResponseRedirect('/cart/')


class CartView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        products = CartProduct.objects.filter(cart=self.cart.id)
        categories = Category.objects.all()
        context = {
            'products': products,
            'categories': categories,
            'cart': self.cart
        }
        return render(request, 'cart.html', context)


class CheckoutView(CartMixin, View):

    def get(self, request, *args, **kwargs):
        products = CartProduct.objects.filter(cart=self.cart.id)
        categories = Category.objects.all()
        form = OrderForm(request.POST or None)
        context = {
            'products': products,
            'categories': categories,
            'cart': self.cart,
            'form': form
        }
        return render(request, 'checkout.html', context)


class MakeOrderView(CartMixin, View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        form = OrderForm(request.POST or None)
        if request.user.is_authenticated:
            customer = Customer.objects.get(user=request.user)
        if form.is_valid():
            new_order = form.save(commit=False)
            if request.user.is_authenticated:
                new_order.customer = customer
            new_order.first_name = form.cleaned_data['first_name']
            new_order.last_name = form.cleaned_data['last_name']
            new_order.phone_number = form.cleaned_data['phone_number']
            new_order.address = form.cleaned_data['address']
            new_order.buying_type = form.cleaned_data['buying_type']
            new_order.order_date = form.cleaned_data['order_date']
            new_order.comment = form.cleaned_data['comment']
            self.cart.in_order = True
            self.cart.save()
            new_order.cart = self.cart
            new_order.save()
            if not self.cart.for_anonymous_user:
                customer.orders.add(new_order)
            messages.add_message(request, messages.INFO, 'Дякую за замовлення! Менеджер з Вами зв\'яжеться')
            return HttpResponseRedirect('/')
        return HttpResponseRedirect('/checkout/')
