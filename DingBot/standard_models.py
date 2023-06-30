from django.db import models


class Administrator(models.Model):
    phone = models.CharField(max_length=15)
    password = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'Administrator'


class Category(models.Model):
    level = models.IntegerField()
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'Category'


class Choice(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    order = models.IntegerField()
    module = models.ForeignKey('Module', models.DO_NOTHING, db_column='module')

    class Meta:
        managed = False
        db_table = 'Choice'


class ChoiceImage(models.Model):
    image = models.CharField(max_length=50)
    choice = models.ForeignKey(Choice, models.DO_NOTHING, db_column='choice')
    view = models.ForeignKey('View', models.DO_NOTHING, db_column='view')

    class Meta:
        managed = False
        db_table = 'ChoiceImage'


class Configuration(models.Model):
    identifier = models.CharField(max_length=30)
    config = models.CharField(max_length=50)
    product = models.ForeignKey('Product', models.DO_NOTHING, db_column='product')

    class Meta:
        managed = False
        db_table = 'Configuration'


class Customer(models.Model):
    openid = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'Customer'


class Module(models.Model):
    name = models.CharField(max_length=50)
    order = models.IntegerField()
    product = models.ForeignKey('Product', models.DO_NOTHING, db_column='product')

    class Meta:
        managed = False
        db_table = 'Module'


class Order(models.Model):
    identifier = models.CharField(max_length=30)
    customer = models.ForeignKey(Customer, models.DO_NOTHING, db_column='customer')
    product = models.ForeignKey('Product', models.DO_NOTHING, db_column='product')
    configuration = models.ForeignKey(Configuration, models.DO_NOTHING, db_column='configuration')
    price = models.DecimalField(max_digits=9, decimal_places=2)
    status = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'Order'


class Product(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    image = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'Product'


class ProductCategory(models.Model):
    product = models.ForeignKey(Product, models.DO_NOTHING, db_column='product')
    category = models.ForeignKey(Category, models.DO_NOTHING, db_column='category')

    class Meta:
        managed = False
        db_table = 'ProductCategory'


class View(models.Model):
    name = models.CharField(max_length=50)
    image = models.CharField(max_length=50)
    product = models.ForeignKey(Product, models.DO_NOTHING, db_column='product')

    class Meta:
        managed = False
        db_table = 'View'
