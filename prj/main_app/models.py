from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.images import get_image_dimensions
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils import timezone

from datetime import datetime

User = get_user_model()


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Ім\'я категорії')
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    MIN_RESOLUTION = (400, 400)
    MAX_RESOLUTION = (4000, 4000)
    MAX_SIZE = 6 * 1024 * 1024

    category = models.ForeignKey(Category, verbose_name='Категорія', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='Найменування')
    slug = models.SlugField(unique=True)
    image = models.ImageField(
        verbose_name='Зображення',
        help_text=mark_safe(
            '<span style="color:red; font-size: 14px">Завантажуйте зображення з мінімальним розширенням 400X400</span>'
        )
    )
    description = models.TextField(verbose_name='Опис', null=True)
    size = models.TextField(max_length=25, verbose_name='Розмір')
    price = models.DecimalField(max_digits=9, decimal_places=2, verbose_name='Ціна')
    in_stock = models.BooleanField(default=False, verbose_name='В наявності')

    def __str__(self):
        return self.title

    def clean(self):

        if not self.image:
            raise ValidationError("No image!")
        elif self.image.size > Product.MAX_SIZE:
            raise ValidationError(
                f'The image size is {int((self.image.size / 1024) / 1024)} Mb. It\'s supposed to be lower than {int((Product.MAX_SIZE / 1024) / 1024)}')
        else:
            width, height = get_image_dimensions(self.image)
            if width < Product.MIN_RESOLUTION[0] or width > Product.MAX_RESOLUTION[0]:
                raise ValidationError(
                    f"The image is {width} pixel wide. It's supposed to be bigger than 400px and lower than 4000")
            if height < Product.MIN_RESOLUTION[1] or height > Product.MAX_RESOLUTION[1]:
                raise ValidationError(
                    f"The image is {height} pixel high. It's supposed to be bigger than 400px and lower than 4000")

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'ct_model': self.category.slug, 'slug': self.slug})

    def get_product_name(self):
        return self.__class__._meta.model_name


class CartProduct(models.Model):
    cart = models.ForeignKey('Cart', null=True, blank=True, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', verbose_name='Товар', on_delete=models.CASCADE, null=True)
    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        verbose_name='Загальна вартість',
        default=0
    )

    def __str__(self):
        return f'Продукт: {self.product.title} (для корзини)'

    def save(self, *args, **kwargs):
        self.final_price = self.qty * self.product.price
        super().save(*args, **kwargs)


class Cart(models.Model):
    owner = models.ForeignKey('Customer', verbose_name='Власник', on_delete=models.CASCADE, null=True)
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        verbose_name='Загальна вартість',
        default=0
    )
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return f'{self.owner.__str__()}, cart id {self.id}'

    def save(self, *args, **kwargs):
        products = CartProduct.objects.filter(cart=self.id)
        self.total_products = sum([x.qty for x in products])
        self.final_price = sum([x.final_price for x in products])
        super().save(*args, **kwargs)


class Customer(models.Model):

    user = models.ForeignKey(User, verbose_name='Користувач', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='Номер телефону')
    address = models.CharField(max_length=255, verbose_name='Адреса')
    orders = models.ManyToManyField('Order', verbose_name='Замовлення покупця', related_name='related_customer',
                                    blank=True, null=True)

    def __str__(self):
        return f'Покупець: {self.user.first_name} {self.user.last_name}'


class Order(models.Model):
    STATUS_NEW = 'new'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_READY = 'is_ready'
    STATUS_COMPLETED = 'completed'

    BUYING_TYPE_SELF = 'self'
    BUYING_TYPE_DELIVERY = 'delivery'

    STATUS_CHOICES = (
        (STATUS_NEW, 'Нове замовлення'),
        (STATUS_IN_PROGRESS, 'Замовлення в обробці'),
        (STATUS_READY, 'Замовлення готове'),
        (STATUS_COMPLETED, 'Замовлення виконане'),
    )

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'Самовивоз'),
        (BUYING_TYPE_DELIVERY, 'Доставка'),
    )

    customer = models.ForeignKey(
        Customer,
        verbose_name='Покупець',
        related_name='related_order',
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    first_name = models.CharField(max_length=255, verbose_name='Ім\'я')
    last_name = models.CharField(max_length=255, verbose_name='Прізвище')
    phone_number = models.CharField(max_length=20, verbose_name='Номер телефону')
    cart = models.ForeignKey(Cart, verbose_name='Кошик', on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=1024, verbose_name='Адреса', null=True, blank=True)
    status = models.CharField(
        max_length=100,
        verbose_name='Статус замовлення',
        choices=STATUS_CHOICES,
        default=STATUS_NEW
    )
    buying_type = models.CharField(
        max_length=100,
        verbose_name='Тип замовлення',
        choices=BUYING_TYPE_CHOICES,
        default=BUYING_TYPE_DELIVERY
    )
    comment = models.TextField(verbose_name='Коментар до замовлення', null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, verbose_name='Дата створення замовлення')
    order_date = models.DateTimeField(verbose_name='Дата отримання замовлення', default=timezone.now)

    def __str__(self):
        return str(self.id)
