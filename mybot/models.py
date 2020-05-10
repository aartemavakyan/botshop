from django.db import models


class Profile(models.Model):
    external_id = models.PositiveIntegerField(verbose_name='Telegram ID', unique=True)
    username = models.CharField(verbose_name='Имя пользователя', max_length=50)
    first_name = models.CharField(verbose_name='Имя', max_length=50, blank=True, null=True)
    last_name = models.CharField(verbose_name='Фамилия', max_length=50, blank=True, null=True)
    phone = models.CharField(verbose_name='Номер телефона', max_length=25, blank=True, null=True)
    latitude = models.FloatField(verbose_name='Широта', blank=True, null=True)
    longitude = models.FloatField(verbose_name='Долгота', blank=True, null=True)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return self.username


class Category(models.Model):
    name_ru = models.CharField(verbose_name='Название категории RU', max_length=50)
    name_uz = models.CharField(verbose_name='Название категории UZ', max_length=50, blank=True, null=True)
    name_en = models.CharField(verbose_name='Название категории EN', max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name_ru


PRODUCT_TYPE = (
    ('pack', 'Упаковка'),
    ('bottle', 'Бутылка'),
    ('kilo', 'Развес'),
)


class Product(models.Model):
    name_ru = models.CharField(verbose_name='Наименование товара RU', max_length=100)
    name_uz = models.CharField(verbose_name='Наименование товара UZ', max_length=100, blank=True)
    name_en = models.CharField(verbose_name='Наименование товара EN', max_length=100, blank=True)
    description_ru = models.TextField(verbose_name='Описание товара RU')
    description_uz = models.TextField(verbose_name='Описание товара UZ', blank=True)
    description_en = models.TextField(verbose_name='Описание товара EN', blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='Категория товара')
    price = models.FloatField(verbose_name='Цена товара')
    type = models.CharField(verbose_name='Тип товара', max_length=20, choices=PRODUCT_TYPE, blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name_ru


class CartItem(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    count = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'Позиция в корзине'
        verbose_name_plural = 'Позиции в корзине'

    def __str__(self):
        return f'{self.product.name_ru} - {self.count}'

    def all_price(self):
        return self.product.price * self.count


class Cart(models.Model):
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE, verbose_name='Пользователь')
    cart_item = models.ManyToManyField(CartItem)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f'Корзина {self.profile.username}'

    def all_sum(self):
        total = 0
        for i in self.cart_item.all():
            total += i.all_price()
        return total


class Order(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    cost = models.FloatField()
    finished = models.BooleanField()
    created = models.DateTimeField(auto_now_add=True)
    changed = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def sum_price(self):
        total = 0
        for i in self.orderitem_set.all():
            total += i.price
        return total

    def save(self, *args, **kwargs):
        self.cost = self.sum_price()
        super(Order, self).save(*args, **kwargs)

    def __str__(self):
        return f'Заказ {self.id} от {self.profile.username}'


class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, blank=True, null=True)
    count = models.PositiveIntegerField()
    price = models.FloatField()
    created = models.DateTimeField(auto_now_add=True)
    changed = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Элемент заказа'
        verbose_name_plural = 'Элементы заказа'

    def __str__(self):
        return f'{self.product.name_ru} - {self.count}'

    def all_price(self):
        return self.product.price * self.count

    def save(self, *args, **kwargs):
        if not self.price:
            self.price = self.all_price()
        super(OrderItem, self).save(*args, **kwargs)