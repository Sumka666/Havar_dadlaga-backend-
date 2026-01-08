from django.db import models

class User(models.Model):
    userID = models.BigAutoField(primary_key=True)
    userName = models.CharField(max_length=255)
    email = models.CharField(max_length=255, unique=True)
    phone = models.IntegerField()
    password = models.CharField(max_length=255)

    class Meta:
        db_table = 'tbl_user'

    def __str__(self):
        return self.userName


class Category(models.Model):
    catID = models.BigAutoField(primary_key=True)
    catName = models.CharField(max_length=255)

    class Meta:
        db_table = 'tbl_category'

    def __str__(self):
        return self.catName


class RestaurantType(models.Model):
    ID = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'tbl_restaurantType'

    def __str__(self):
        return self.name


class Restaurant(models.Model):
    resID = models.BigAutoField(primary_key=True)
    resName = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    cateID = models.ForeignKey(RestaurantType, on_delete=models.CASCADE)
    branch = models.CharField(max_length=255)
    phone = models.IntegerField()
    
    class Meta:
        db_table = 'tbl_restaurant'

    def __str__(self):
        return self.resName


class Food(models.Model):
    foodID = models.BigAutoField(primary_key=True)
    foodName = models.CharField(max_length=255)
    resID = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    catID = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.IntegerField()
    description = models.CharField(max_length=500)
    image = models.CharField(max_length=255)

    class Meta:
        db_table = 'tbl_food'

    def __str__(self):
        return self.foodName


class Worker(models.Model):
    workerID = models.BigAutoField(primary_key=True)
    workerName = models.CharField(max_length=255)
    phone = models.IntegerField()

    class Meta:
        db_table = 'tbl_worker'

    def __str__(self):
        return self.workerName


class Order(models.Model):
    orderID = models.BigAutoField(primary_key=True)
    userID = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    location = models.CharField(max_length=255)
    status = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'tbl_order'

    def __str__(self):
        return str(self.orderID)


class OrderFood(models.Model):
    ID = models.BigAutoField(primary_key=True)
    orderID = models.ForeignKey(Order, on_delete=models.CASCADE)
    foodID = models.ForeignKey(Food, on_delete=models.CASCADE)
    stock = models.IntegerField()
    price = models.IntegerField()

    class Meta:
        db_table = 'tbl_orderFood'

class Payment(models.Model):
    payID = models.BigAutoField(primary_key=True)
    orderID = models.ForeignKey(Order, on_delete=models.CASCADE)
    price = models.IntegerField()
    turul = models.CharField(max_length=255)
    status = models.CharField(max_length=255)

    class Meta:
        db_table = 'tbl_payment'


class Delivery(models.Model):
    payID = models.BigAutoField(primary_key=True)
    orderID = models.ForeignKey(Order, on_delete=models.CASCADE)
    workerID = models.ForeignKey(Worker, on_delete=models.CASCADE)
    status = models.CharField(max_length=255, null=True, blank=True)
    startdate = models.DateField(null=True, blank=True)
    enddate = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'tbl_delivery'


class Comment(models.Model):
    commID = models.BigAutoField(primary_key=True)
    userID = models.ForeignKey(User, on_delete=models.CASCADE)
    resID = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    foodID = models.ForeignKey(Food, on_delete=models.CASCADE)
    review = models.IntegerField()
    comment = models.CharField(max_length=500)
    date = models.DateField()

    class Meta:
        db_table = 'tbl_comment'


class Cart(models.Model):
    cartID = models.BigAutoField(primary_key=True)
    userID = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'tbl_cart'


class CartFood(models.Model):
    cartID = models.ForeignKey(Cart, on_delete=models.CASCADE)
    foodID = models.ForeignKey(Food, on_delete=models.CASCADE)
    stock = models.IntegerField()

    class Meta:
        db_table = 'tbl_cartFood'
        unique_together = ('cartID', 'foodID')



class DeliveryPrice(models.Model):
    ID = models.BigAutoField(primary_key=True)
    map = models.CharField(max_length=255)
    price = models.IntegerField()
    note = models.CharField(max_length=255)

    class Meta:
        db_table = 'tbl_deliveryPrice'


class History(models.Model):
    ID = models.BigAutoField(primary_key=True)
    orderID = models.ForeignKey(Order, on_delete=models.CASCADE)
    status = models.CharField(max_length=255)
    date = models.DateField()

    class Meta:
        db_table = 'tbl_history'


class Notification(models.Model):
    ID = models.BigAutoField(primary_key=True)
    userID = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    is_read = models.BooleanField(default=False)
    date = models.DateField()

    class Meta:
        db_table = 'tbl_notification'


class Address(models.Model):
    ID = models.BigAutoField(primary_key=True)
    userID = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    detail_address = models.CharField(max_length=255)

    class Meta:
        db_table = 'tbl_address'


class Coupon(models.Model):
    ID = models.BigAutoField(primary_key=True)
    code = models.CharField(max_length=255)
    percent = models.CharField(max_length=50)
    duration = models.CharField(max_length=255)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'tbl_coupon'
