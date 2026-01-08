from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch, Sum, F, Avg
from django.db import models as db_models
from django.utils import timezone, dateparse

from api.models import Food, Order, OrderFood, Category, Restaurant, Delivery, DeliveryPrice, Worker, Coupon, Comment
from restaurant_web.models import Menu, OrderStatus, OperatingHours, Inventory
from common.permissions import JWTAuthentication
from datetime import datetime, timedelta


class MenuListView(APIView):
    """
    GET: List all menu items (Foods) with filtering
    POST: Create new menu item (Food)
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        """List all menu items with optional filters"""
        restaurant_id = request.query_params.get('restaurant_id')
        category_id = request.query_params.get('category_id')
        is_available = request.query_params.get('is_available')
        search = request.query_params.get('search')

        queryset = Food.objects.select_related('resID', 'catID').all()

        # Apply filters
        if restaurant_id:
            queryset = queryset.filter(resID_id=restaurant_id)
        if category_id:
            queryset = queryset.filter(catID_id=category_id)
        if is_available is not None:
            # Note: Food model doesn't have is_available, but Menu does
            menu_ids = Menu.objects.filter(is_available=is_available.lower() == 'true').values_list('food_id', flat=True)
            if is_available.lower() == 'true':
                queryset = queryset.filter(foodID__in=menu_ids)
            else:
                queryset = queryset.exclude(foodID__in=menu_ids)
        if search:
            queryset = queryset.filter(
                Q(foodName__icontains=search) | 
                Q(description__icontains=search)
            )

        foods = []
        for food in queryset:
            foods.append({
                'foodID': food.foodID,
                'foodName': food.foodName,
                'restaurant': {
                    'resID': food.resID.resID,
                    'resName': food.resID.resName,
                },
                'category': {
                    'catID': food.catID.catID,
                    'catName': food.catID.catName,
                },
                'price': food.price,
                'description': food.description,
                'image': food.image,
            })

        return Response({
            'count': len(foods),
            'results': foods
        })

    def post(self, request):
        """Create new menu item (Food)"""
        required_fields = ['foodName', 'resID', 'catID', 'price']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'error': f'{field} шаардлагатай'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            restaurant = Restaurant.objects.get(resID=request.data['resID'])
            category = Category.objects.get(catID=request.data['catID'])
        except (Restaurant.DoesNotExist, Category.DoesNotExist):
            return Response(
                {'error': 'Ресторан эсвэл ангилал олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        food = Food.objects.create(
            foodName=request.data['foodName'],
            resID=restaurant,
            catID=category,
            price=request.data['price'],
            description=request.data.get('description', ''),
            image=request.data.get('image', ''),
        )

        # Create menu entry
        Menu.objects.create(
            food=food,
            restaurant=restaurant,
            category=category,
            is_available=request.data.get('is_available', True)
        )

        return Response({
            'foodID': food.foodID,
            'foodName': food.foodName,
            'message': 'Меню амжилттай нэмэгдлээ'
        }, status=status.HTTP_201_CREATED)


class MenuDetailView(APIView):
    """
    GET: Get menu item details
    PUT: Update menu item
    DELETE: Delete menu item
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request, food_id):
        """Get menu item details"""
        try:
            food = Food.objects.select_related('resID', 'catID').get(foodID=food_id)
        except Food.DoesNotExist:
            return Response(
                {'error': 'Меню олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        menu = Menu.objects.filter(food=food).first()
        
        return Response({
            'foodID': food.foodID,
            'foodName': food.foodName,
            'restaurant': {
                'resID': food.resID.resID,
                'resName': food.resID.resName,
            },
            'category': {
                'catID': food.catID.catID,
                'catName': food.catID.catName,
            },
            'price': food.price,
            'description': food.description,
            'image': food.image,
            'is_available': menu.is_available if menu else True,
        })

    def put(self, request, food_id):
        """Update menu item"""
        try:
            food = Food.objects.get(foodID=food_id)
        except Food.DoesNotExist:
            return Response(
                {'error': 'Меню олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update food fields
        if 'foodName' in request.data:
            food.foodName = request.data['foodName']
        if 'price' in request.data:
            food.price = request.data['price']
        if 'description' in request.data:
            food.description = request.data['description']
        if 'image' in request.data:
            food.image = request.data['image']
        if 'resID' in request.data:
            try:
                food.resID = Restaurant.objects.get(resID=request.data['resID'])
            except Restaurant.DoesNotExist:
                return Response(
                    {'error': 'Ресторан олдсонгүй'},
                    status=status.HTTP_404_NOT_FOUND
                )
        if 'catID' in request.data:
            try:
                food.catID = Category.objects.get(catID=request.data['catID'])
            except Category.DoesNotExist:
                return Response(
                    {'error': 'Ангилал олдсонгүй'},
                    status=status.HTTP_404_NOT_FOUND
                )

        food.save()

        # Update menu availability
        menu = Menu.objects.filter(food=food).first()
        if menu:
            if 'is_available' in request.data:
                menu.is_available = request.data['is_available']
            menu.save()
        elif 'is_available' in request.data:
            Menu.objects.create(
                food=food,
                restaurant=food.resID,
                category=food.catID,
                is_available=request.data['is_available']
            )

        return Response({
            'foodID': food.foodID,
            'foodName': food.foodName,
            'message': 'Меню амжилттай шинэчлэгдлээ'
        })

    def delete(self, request, food_id):
        """Delete menu item"""
        try:
            food = Food.objects.get(foodID=food_id)
        except Food.DoesNotExist:
            return Response(
                {'error': 'Меню олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        food.delete()
        return Response(
            {'message': 'Меню амжилттай устгагдлаа'},
            status=status.HTTP_200_OK
        )


class OrderListView(APIView):
    """
    GET: List all orders with filtering
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        """List orders with optional status filter"""
        order_status = request.query_params.get('status')
        restaurant_id = request.query_params.get('restaurant_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        queryset = Order.objects.select_related('userID').prefetch_related(
            Prefetch('orderfood_set', queryset=OrderFood.objects.select_related('foodID'))
        ).all()

        # Apply filters
        if order_status:
            queryset = queryset.filter(status=order_status)
        if restaurant_id:
            # Filter by restaurant through order foods
            queryset = queryset.filter(orderfood_set__foodID__resID_id=restaurant_id).distinct()
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        orders = []
        for order in queryset.order_by('-date', '-orderID'):
            order_foods = order.orderfood_set.all()
            total_price = sum(of.price * of.stock for of in order_foods)

            orders.append({
                'orderID': order.orderID,
                'user': {
                    'userID': order.userID.userID,
                    'userName': order.userID.userName,
                    'email': order.userID.email,
                    'phone': order.userID.phone,
                },
                'date': order.date,
                'location': order.location,
                'status': order.status or 'pending',
                'total_price': total_price,
                'items_count': order_foods.count(),
            })

        return Response({
            'count': len(orders),
            'results': orders
        })


class OrderDetailView(APIView):
    """
    GET: Get order details
    PUT: Update order status
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request, order_id):
        """Get order details with all items"""
        try:
            order = Order.objects.select_related('userID').prefetch_related(
                Prefetch('orderfood_set', queryset=OrderFood.objects.select_related('foodID'))
            ).get(orderID=order_id)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Захиалга олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        order_foods = []
        total_price = 0
        for of in order.orderfood_set.all():
            item_total = of.price * of.stock
            total_price += item_total
            order_foods.append({
                'ID': of.ID,
                'food': {
                    'foodID': of.foodID.foodID,
                    'foodName': of.foodID.foodName,
                    'price': of.foodID.price,
                    'image': of.foodID.image,
                },
                'quantity': of.stock,
                'unit_price': of.price,
                'total': item_total,
            })

        # Get status history
        status_history = OrderStatus.objects.filter(order=order).order_by('-created_at')
        history = [{
            'status': s.status,
            'notes': s.notes,
            'created_at': s.created_at,
            'updated_by': s.updated_by,
        } for s in status_history]

        return Response({
            'orderID': order.orderID,
            'user': {
                'userID': order.userID.userID,
                'userName': order.userID.userName,
                'email': order.userID.email,
                'phone': order.userID.phone,
            },
            'date': order.date,
            'location': order.location,
            'status': order.status or 'pending',
            'items': order_foods,
            'total_price': total_price,
            'status_history': history,
        })

    def put(self, request, order_id):
        """Update order status"""
        try:
            order = Order.objects.get(orderID=order_id)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Захиалга олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        new_status = request.data.get('status')
        if not new_status:
            return Response(
                {'error': 'Status шаардлагатай'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate status
        valid_statuses = ['pending', 'approved', 'preparing', 'ready', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Буруу status. Зөв status: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = order.status or 'pending'
        order.status = new_status
        order.save()

        # Create status history entry
        OrderStatus.objects.create(
            order=order,
            status=new_status,
            notes=request.data.get('notes', ''),
            updated_by=request.data.get('updated_by', 'system')
        )

        return Response({
            'orderID': order.orderID,
            'old_status': old_status,
            'new_status': new_status,
            'message': 'Захиалгын статус амжилттай шинэчлэгдлээ'
        })


class OrderApproveView(APIView):
    """
    POST: Approve order (set status to approved)
    """
    authentication_classes = [JWTAuthentication]

    def post(self, request, order_id):
        """Approve an order"""
        try:
            order = Order.objects.get(orderID=order_id)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Захиалга олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        if order.status == 'approved':
            return Response(
                {'message': 'Захиалга аль хэдийн батлагдсан'},
                status=status.HTTP_200_OK
            )

        if order.status == 'cancelled':
            return Response(
                {'error': 'Цуцлагдсан захиалгыг батлах боломжгүй'},
                status=status.HTTP_400_BAD_REQUEST
            )

        old_status = order.status or 'pending'
        order.status = 'approved'
        order.save()

        # Create status history
        OrderStatus.objects.create(
            order=order,
            status='approved',
            notes=request.data.get('notes', 'Захиалга батлагдлаа'),
            updated_by=request.data.get('updated_by', getattr(request.user, 'username', 'system'))
        )

        return Response({
            'orderID': order.orderID,
            'old_status': old_status,
            'new_status': 'approved',
            'message': 'Захиалга амжилттай батлагдлаа'
        })


class RevenueReportView(APIView):
    """
    Орлогын тайлан (report)

    GET /restaurant/revenue-report/?
        date_from=2025-01-01
        &date_to=2025-01-31
        &restaurant_id=1
        &group_by=day|month|restaurant
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        restaurant_id = request.query_params.get('restaurant_id')
        group_by = request.query_params.get('group_by', 'day')

        qs = Order.objects.prefetch_related(
            Prefetch('orderfood_set', queryset=OrderFood.objects.select_related('foodID', 'foodID__resID'))
        )

        # filter only finished / paid orders (optional: here just ignore cancelled)
        qs = qs.exclude(status='cancelled')

        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        if restaurant_id:
            qs = qs.filter(orderfood_set__foodID__resID_id=restaurant_id).distinct()

        # raw aggregation in Python for simplicity
        total_revenue = 0
        total_orders = 0
        by_group = {}

        for order in qs:
            order_total = 0
            for of in order.orderfood_set.all():
                order_total += of.price * of.stock

            total_revenue += order_total
            total_orders += 1

            if group_by == 'month':
                key = order.date.strftime('%Y-%m')
            elif group_by == 'restaurant':
                # if order has multiple restaurants, group by each
                rest_ids = set(of.foodID.resID_id for of in order.orderfood_set.all())
                for rid in rest_ids:
                    rkey = f"restaurant_{rid}"
                    if rkey not in by_group:
                        by_group[rkey] = {'revenue': 0, 'orders': 0}
                    by_group[rkey]['revenue'] += order_total
                    by_group[rkey]['orders'] += 1
                continue
            else:  # day
                key = order.date.strftime('%Y-%m-%d')

            if key not in by_group:
                by_group[key] = {'revenue': 0, 'orders': 0}
            by_group[key]['revenue'] += order_total
            by_group[key]['orders'] += 1

        # Build response
        grouped_list = []
        for key, val in sorted(by_group.items(), key=lambda x: x[0]):
            grouped_list.append({
                'group': key,
                'revenue': val['revenue'],
                'orders': val['orders'],
                'avg_order': round(val['revenue'] / val['orders'], 2) if val['orders'] else 0,
            })

        return Response({
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'avg_order': round(total_revenue / total_orders, 2) if total_orders else 0,
            'groups': grouped_list,
        })


class DeliveryListView(APIView):
    """
    Хүргэлтийн жагсаалт

    GET /restaurant/deliveries/?
        status=pending|on_the_way|delivered
        &worker_id=1
        &date_from=2025-01-01
        &date_to=2025-01-31
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        status_filter = request.query_params.get('status')
        worker_id = request.query_params.get('worker_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        qs = Delivery.objects.select_related('orderID', 'workerID')

        if status_filter:
            qs = qs.filter(status=status_filter)
        if worker_id:
            qs = qs.filter(workerID_id=worker_id)
        if date_from:
            qs = qs.filter(startdate__gte=date_from)
        if date_to:
            qs = qs.filter(startdate__lte=date_to)

        deliveries = []
        for d in qs.order_by('-startdate', '-payID'):
            deliveries.append({
                'deliveryID': d.payID,
                'orderID': d.orderID.orderID,
                'worker': {
                    'workerID': d.workerID.workerID,
                    'workerName': d.workerID.workerName,
                    'phone': d.workerID.phone,
                },
                'status': d.status,
                'startdate': d.startdate,
                'enddate': d.enddate,
            })

        return Response({
            'count': len(deliveries),
            'results': deliveries,
        })


class DeliveryDetailView(APIView):
    """
    Хүргэлтийн дэлгэрэнгүй + статус өөрчлөх

    GET /restaurant/deliveries/<delivery_id>/
    PUT /restaurant/deliveries/<delivery_id>/  {status: 'on_the_way', enddate: '2025-01-08'}
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request, delivery_id):
        try:
            d = Delivery.objects.select_related('orderID', 'workerID').get(payID=delivery_id)
        except Delivery.DoesNotExist:
            return Response({'error': 'Хүргэлт олдсонгүй'}, status=status.HTTP_404_NOT_FOUND)

        order = d.orderID
        order_foods = order.orderfood_set.select_related('foodID')
        items = []
        total_price = 0
        for of in order_foods:
            item_total = of.price * of.stock
            total_price += item_total
            items.append({
                'foodID': of.foodID.foodID,
                'foodName': of.foodID.foodName,
                'quantity': of.stock,
                'unit_price': of.price,
                'total': item_total,
            })

        return Response({
            'deliveryID': d.payID,
            'status': d.status,
            'startdate': d.startdate,
            'enddate': d.enddate,
            'worker': {
                'workerID': d.workerID.workerID,
                'workerName': d.workerID.workerName,
                'phone': d.workerID.phone,
            },
            'order': {
                'orderID': order.orderID,
                'location': order.location,
                'date': order.date,
                'status': order.status,
                'total_price': total_price,
                'items': items,
            }
        })

    def put(self, request, delivery_id):
        try:
            d = Delivery.objects.select_related('orderID', 'workerID').get(payID=delivery_id)
        except Delivery.DoesNotExist:
            return Response({'error': 'Хүргэлт олдсонгүй'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': 'status шаардлагатай'}, status=status.HTTP_400_BAD_REQUEST)

        valid_statuses = ['pending', 'on_the_way', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Буруу статус. Зөв статусууд: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        d.status = new_status

        # update dates if provided
        if 'startdate' in request.data:
            d.startdate = request.data.get('startdate') or d.startdate
        if 'enddate' in request.data:
            d.enddate = request.data.get('enddate') or d.enddate

        d.save()

        return Response({
            'deliveryID': d.payID,
            'status': d.status,
            'message': 'Хүргэлтийн статус амжилттай шинэчлэгдлээ',
        })


# ==================== RESTAURANT PROFILE MANAGEMENT ====================

class RestaurantProfileView(APIView):
    """
    GET: Get restaurant profile
    PUT: Update restaurant profile
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request, restaurant_id):
        """Get restaurant profile details"""
        try:
            restaurant = Restaurant.objects.select_related('cateID').get(resID=restaurant_id)
        except Restaurant.DoesNotExist:
            return Response(
                {'error': 'Ресторан олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'resID': restaurant.resID,
            'resName': restaurant.resName,
            'location': restaurant.location,
            'branch': restaurant.branch,
            'phone': restaurant.phone,
            'restaurantType': {
                'ID': restaurant.cateID.ID,
                'name': restaurant.cateID.name,
            }
        })

    def put(self, request, restaurant_id):
        """Update restaurant profile"""
        try:
            restaurant = Restaurant.objects.get(resID=restaurant_id)
        except Restaurant.DoesNotExist:
            return Response(
                {'error': 'Ресторан олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        if 'resName' in request.data:
            restaurant.resName = request.data['resName']
        if 'location' in request.data:
            restaurant.location = request.data['location']
        if 'branch' in request.data:
            restaurant.branch = request.data['branch']
        if 'phone' in request.data:
            restaurant.phone = request.data['phone']
        if 'cateID' in request.data:
            from api.models import RestaurantType
            try:
                restaurant.cateID = RestaurantType.objects.get(ID=request.data['cateID'])
            except RestaurantType.DoesNotExist:
                return Response(
                    {'error': 'Рестораны төрөл олдсонгүй'},
                    status=status.HTTP_404_NOT_FOUND
                )

        restaurant.save()

        return Response({
            'resID': restaurant.resID,
            'resName': restaurant.resName,
            'message': 'Рестораны мэдээлэл амжилттай шинэчлэгдлээ'
        })


# ==================== OPERATING HOURS MANAGEMENT ====================

class OperatingHoursListView(APIView):
    """
    GET: Get all operating hours for a restaurant
    POST: Create/update operating hours for a restaurant
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request, restaurant_id):
        """Get operating hours"""
        hours = OperatingHours.objects.filter(restaurant_id=restaurant_id).order_by('day_of_week')
        
        result = []
        for h in hours:
            result.append({
                'ID': h.ID,
                'day_of_week': h.day_of_week,
                'day_name': h.get_day_of_week_display(),
                'open_time': h.open_time.strftime('%H:%M') if h.open_time else None,
                'close_time': h.close_time.strftime('%H:%M') if h.close_time else None,
                'is_closed': h.is_closed,
            })

        return Response({
            'restaurant_id': restaurant_id,
            'operating_hours': result
        })

    def post(self, request, restaurant_id):
        """Create or update operating hours"""
        try:
            restaurant = Restaurant.objects.get(resID=restaurant_id)
        except Restaurant.DoesNotExist:
            return Response(
                {'error': 'Ресторан олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        hours_data = request.data.get('hours', [])
        created_count = 0
        updated_count = 0

        for hour_data in hours_data:
            day = hour_data.get('day_of_week')
            is_closed = hour_data.get('is_closed', False)
            
            hour_obj, created = OperatingHours.objects.get_or_create(
                restaurant=restaurant,
                day_of_week=day,
                defaults={
                    'open_time': hour_data.get('open_time', '09:00') if not is_closed else None,
                    'close_time': hour_data.get('close_time', '22:00') if not is_closed else None,
                    'is_closed': is_closed,
                }
            )

            if not created:
                hour_obj.is_closed = is_closed
                if not is_closed:
                    hour_obj.open_time = hour_data.get('open_time', hour_obj.open_time)
                    hour_obj.close_time = hour_data.get('close_time', hour_obj.close_time)
                hour_obj.save()
                updated_count += 1
            else:
                created_count += 1

        return Response({
            'message': f'{created_count} шинэ, {updated_count} шинэчлэгдлээ',
            'restaurant_id': restaurant_id
        })


# ==================== PROMOTIONS/COUPONS MANAGEMENT ====================

class CouponListView(APIView):
    """
    GET: List all coupons
    POST: Create new coupon
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        """List coupons with optional filters"""
        active_only = request.query_params.get('active_only', 'false').lower() == 'true'
        
        queryset = Coupon.objects.all()
        if active_only:
            queryset = queryset.filter(active=True)

        coupons = []
        for coupon in queryset.order_by('-ID'):
            coupons.append({
                'ID': coupon.ID,
                'code': coupon.code,
                'percent': coupon.percent,
                'duration': coupon.duration,
                'active': coupon.active,
            })

        return Response({
            'count': len(coupons),
            'results': coupons
        })

    def post(self, request):
        """Create new coupon"""
        required_fields = ['code', 'percent', 'duration']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'error': f'{field} шаардлагатай'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Check if code already exists
        if Coupon.objects.filter(code=request.data['code']).exists():
            return Response(
                {'error': 'Энэ код аль хэдийн байна'},
                status=status.HTTP_400_BAD_REQUEST
            )

        coupon = Coupon.objects.create(
            code=request.data['code'],
            percent=request.data['percent'],
            duration=request.data['duration'],
            active=request.data.get('active', True)
        )

        return Response({
            'ID': coupon.ID,
            'code': coupon.code,
            'message': 'Урамшуулал амжилттай нэмэгдлээ'
        }, status=status.HTTP_201_CREATED)


class CouponDetailView(APIView):
    """
    GET: Get coupon details
    PUT: Update coupon
    DELETE: Delete coupon
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request, coupon_id):
        """Get coupon details"""
        try:
            coupon = Coupon.objects.get(ID=coupon_id)
        except Coupon.DoesNotExist:
            return Response(
                {'error': 'Урамшуулал олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'ID': coupon.ID,
            'code': coupon.code,
            'percent': coupon.percent,
            'duration': coupon.duration,
            'active': coupon.active,
        })

    def put(self, request, coupon_id):
        """Update coupon"""
        try:
            coupon = Coupon.objects.get(ID=coupon_id)
        except Coupon.DoesNotExist:
            return Response(
                {'error': 'Урамшуулал олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        if 'code' in request.data:
            # Check if new code already exists
            if Coupon.objects.filter(code=request.data['code']).exclude(ID=coupon_id).exists():
                return Response(
                    {'error': 'Энэ код аль хэдийн байна'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            coupon.code = request.data['code']
        if 'percent' in request.data:
            coupon.percent = request.data['percent']
        if 'duration' in request.data:
            coupon.duration = request.data['duration']
        if 'active' in request.data:
            coupon.active = request.data['active']

        coupon.save()

        return Response({
            'ID': coupon.ID,
            'code': coupon.code,
            'message': 'Урамшуулал амжилттай шинэчлэгдлээ'
        })

    def delete(self, request, coupon_id):
        """Delete coupon"""
        try:
            coupon = Coupon.objects.get(ID=coupon_id)
        except Coupon.DoesNotExist:
            return Response(
                {'error': 'Урамшуулал олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        coupon.delete()
        return Response(
            {'message': 'Урамшуулал амжилттай устгагдлаа'},
            status=status.HTTP_200_OK
        )


# ==================== REVIEWS/COMMENTS MANAGEMENT ====================

class ReviewListView(APIView):
    """
    GET: List all reviews/comments for restaurant or food
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        """List reviews with filters"""
        restaurant_id = request.query_params.get('restaurant_id')
        food_id = request.query_params.get('food_id')
        min_rating = request.query_params.get('min_rating')

        queryset = Comment.objects.select_related('userID', 'resID', 'foodID').all()

        if restaurant_id:
            queryset = queryset.filter(resID_id=restaurant_id)
        if food_id:
            queryset = queryset.filter(foodID_id=food_id)
        if min_rating:
            queryset = queryset.filter(review__gte=min_rating)

        reviews = []
        for review in queryset.order_by('-date'):
            reviews.append({
                'commID': review.commID,
                'user': {
                    'userID': review.userID.userID,
                    'userName': review.userID.userName,
                },
                'restaurant': {
                    'resID': review.resID.resID,
                    'resName': review.resID.resName,
                },
                'food': {
                    'foodID': review.foodID.foodID,
                    'foodName': review.foodID.foodName,
                },
                'review': review.review,
                'comment': review.comment,
                'date': review.date,
            })

        # Calculate average rating
        avg_rating = queryset.aggregate(avg=Avg('review'))['avg'] or 0

        return Response({
            'count': len(reviews),
            'average_rating': round(avg_rating, 2),
            'results': reviews
        })


class ReviewDetailView(APIView):
    """
    GET: Get review details
    DELETE: Delete review (restaurant owner can delete)
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request, review_id):
        """Get review details"""
        try:
            review = Comment.objects.select_related('userID', 'resID', 'foodID').get(commID=review_id)
        except Comment.DoesNotExist:
            return Response(
                {'error': 'Сэтгэгдэл олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'commID': review.commID,
            'user': {
                'userID': review.userID.userID,
                'userName': review.userID.userName,
                'email': review.userID.email,
            },
            'restaurant': {
                'resID': review.resID.resID,
                'resName': review.resID.resName,
            },
            'food': {
                'foodID': review.foodID.foodID,
                'foodName': review.foodID.foodName,
            },
            'review': review.review,
            'comment': review.comment,
            'date': review.date,
        })

    def delete(self, request, review_id):
        """Delete review"""
        try:
            review = Comment.objects.get(commID=review_id)
        except Comment.DoesNotExist:
            return Response(
                {'error': 'Сэтгэгдэл олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        review.delete()
        return Response(
            {'message': 'Сэтгэгдэл амжилттай устгагдлаа'},
            status=status.HTTP_200_OK
        )


# ==================== INVENTORY/STOCK MANAGEMENT ====================

class InventoryListView(APIView):
    """
    GET: List all inventory items
    POST: Create inventory entry
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        """List inventory with filters"""
        restaurant_id = request.query_params.get('restaurant_id')
        low_stock_only = request.query_params.get('low_stock_only', 'false').lower() == 'true'

        queryset = Inventory.objects.select_related('food', 'restaurant').all()

        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        if low_stock_only:
            queryset = queryset.filter(stock_quantity__lte=F('min_stock_level'))

        inventory_items = []
        for inv in queryset:
            inventory_items.append({
                'ID': inv.ID,
                'food': {
                    'foodID': inv.food.foodID,
                    'foodName': inv.food.foodName,
                },
                'restaurant': {
                    'resID': inv.restaurant.resID,
                    'resName': inv.restaurant.resName,
                },
                'stock_quantity': inv.stock_quantity,
                'min_stock_level': inv.min_stock_level,
                'unit': inv.unit,
                'is_low_stock': inv.is_low_stock,
                'last_updated': inv.last_updated,
            })

        return Response({
            'count': len(inventory_items),
            'low_stock_count': sum(1 for inv in queryset if inv.is_low_stock),
            'results': inventory_items
        })

    def post(self, request):
        """Create inventory entry"""
        required_fields = ['food_id', 'restaurant_id', 'stock_quantity']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'error': f'{field} шаардлагатай'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        try:
            food = Food.objects.get(foodID=request.data['food_id'])
            restaurant = Restaurant.objects.get(resID=request.data['restaurant_id'])
        except (Food.DoesNotExist, Restaurant.DoesNotExist):
            return Response(
                {'error': 'Хоол эсвэл ресторан олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        inventory, created = Inventory.objects.get_or_create(
            food=food,
            restaurant=restaurant,
            defaults={
                'stock_quantity': request.data['stock_quantity'],
                'min_stock_level': request.data.get('min_stock_level', 10),
                'unit': request.data.get('unit', 'ш'),
            }
        )

        if not created:
            inventory.stock_quantity = request.data['stock_quantity']
            if 'min_stock_level' in request.data:
                inventory.min_stock_level = request.data['min_stock_level']
            if 'unit' in request.data:
                inventory.unit = request.data['unit']
            inventory.save()

        return Response({
            'ID': inventory.ID,
            'message': 'Нөөц амжилттай нэмэгдлээ' if created else 'Нөөц амжилттай шинэчлэгдлээ'
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class InventoryDetailView(APIView):
    """
    GET: Get inventory details
    PUT: Update inventory stock
    DELETE: Delete inventory entry
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request, inventory_id):
        """Get inventory details"""
        try:
            inv = Inventory.objects.select_related('food', 'restaurant').get(ID=inventory_id)
        except Inventory.DoesNotExist:
            return Response(
                {'error': 'Нөөц олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'ID': inv.ID,
            'food': {
                'foodID': inv.food.foodID,
                'foodName': inv.food.foodName,
            },
            'restaurant': {
                'resID': inv.restaurant.resID,
                'resName': inv.restaurant.resName,
            },
            'stock_quantity': inv.stock_quantity,
            'min_stock_level': inv.min_stock_level,
            'unit': inv.unit,
            'is_low_stock': inv.is_low_stock,
            'last_updated': inv.last_updated,
        })

    def put(self, request, inventory_id):
        """Update inventory stock"""
        try:
            inv = Inventory.objects.get(ID=inventory_id)
        except Inventory.DoesNotExist:
            return Response(
                {'error': 'Нөөц олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        if 'stock_quantity' in request.data:
            inv.stock_quantity = request.data['stock_quantity']
        if 'min_stock_level' in request.data:
            inv.min_stock_level = request.data['min_stock_level']
        if 'unit' in request.data:
            inv.unit = request.data['unit']

        inv.save()

        return Response({
            'ID': inv.ID,
            'stock_quantity': inv.stock_quantity,
            'is_low_stock': inv.is_low_stock,
            'message': 'Нөөц амжилттай шинэчлэгдлээ'
        })

    def delete(self, request, inventory_id):
        """Delete inventory entry"""
        try:
            inv = Inventory.objects.get(ID=inventory_id)
        except Inventory.DoesNotExist:
            return Response(
                {'error': 'Нөөц олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        inv.delete()
        return Response(
            {'message': 'Нөөц амжилттай устгагдлаа'},
            status=status.HTTP_200_OK
        )


# ==================== STAFF/WORKERS MANAGEMENT ====================

class WorkerListView(APIView):
    """
    GET: List all workers
    POST: Create new worker
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        """List workers"""
        workers = Worker.objects.all()

        result = []
        for worker in workers.order_by('workerID'):
            # Count deliveries for this worker
            delivery_count = Delivery.objects.filter(workerID=worker).count()
            active_deliveries = Delivery.objects.filter(workerID=worker, status='on_the_way').count()

            result.append({
                'workerID': worker.workerID,
                'workerName': worker.workerName,
                'phone': worker.phone,
                'total_deliveries': delivery_count,
                'active_deliveries': active_deliveries,
            })

        return Response({
            'count': len(result),
            'results': result
        })

    def post(self, request):
        """Create new worker"""
        required_fields = ['workerName', 'phone']
        for field in required_fields:
            if field not in request.data:
                return Response(
                    {'error': f'{field} шаардлагатай'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        worker = Worker.objects.create(
            workerName=request.data['workerName'],
            phone=request.data['phone']
        )

        return Response({
            'workerID': worker.workerID,
            'workerName': worker.workerName,
            'message': 'Ажилтан амжилттай нэмэгдлээ'
        }, status=status.HTTP_201_CREATED)


class WorkerDetailView(APIView):
    """
    GET: Get worker details
    PUT: Update worker
    DELETE: Delete worker
    """
    authentication_classes = [JWTAuthentication]

    def get(self, request, worker_id):
        """Get worker details with delivery stats"""
        try:
            worker = Worker.objects.get(workerID=worker_id)
        except Worker.DoesNotExist:
            return Response(
                {'error': 'Ажилтан олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        deliveries = Delivery.objects.filter(workerID=worker).select_related('orderID')
        delivery_stats = {
            'total': deliveries.count(),
            'pending': deliveries.filter(status='pending').count(),
            'on_the_way': deliveries.filter(status='on_the_way').count(),
            'delivered': deliveries.filter(status='delivered').count(),
        }

        return Response({
            'workerID': worker.workerID,
            'workerName': worker.workerName,
            'phone': worker.phone,
            'delivery_stats': delivery_stats,
        })

    def put(self, request, worker_id):
        """Update worker"""
        try:
            worker = Worker.objects.get(workerID=worker_id)
        except Worker.DoesNotExist:
            return Response(
                {'error': 'Ажилтан олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        if 'workerName' in request.data:
            worker.workerName = request.data['workerName']
        if 'phone' in request.data:
            worker.phone = request.data['phone']

        worker.save()

        return Response({
            'workerID': worker.workerID,
            'workerName': worker.workerName,
            'message': 'Ажилтны мэдээлэл амжилттай шинэчлэгдлээ'
        })

    def delete(self, request, worker_id):
        """Delete worker"""
        try:
            worker = Worker.objects.get(workerID=worker_id)
        except Worker.DoesNotExist:
            return Response(
                {'error': 'Ажилтан олдсонгүй'},
                status=status.HTTP_404_NOT_FOUND
            )

        worker.delete()
        return Response(
            {'message': 'Ажилтан амжилттай устгагдлаа'},
            status=status.HTTP_200_OK
        )


# ==================== ENHANCED DASHBOARD ====================

@api_view(['GET'])
def dashboard(request):
    """Enhanced dashboard with comprehensive statistics"""
    restaurant_id = request.query_params.get('restaurant_id')
    
    # Base querysets
    orders_qs = Order.objects.prefetch_related('orderfood_set')
    foods_qs = Food.objects.all()
    
    if restaurant_id:
        orders_qs = orders_qs.filter(orderfood_set__foodID__resID_id=restaurant_id).distinct()
        foods_qs = foods_qs.filter(resID_id=restaurant_id)

    # Order statistics
    total_orders = orders_qs.count()
    pending_orders = orders_qs.filter(status='pending').count()
    approved_orders = orders_qs.filter(status='approved').count()
    preparing_orders = orders_qs.filter(status='preparing').count()
    ready_orders = orders_qs.filter(status='ready').count()
    delivered_orders = orders_qs.filter(status='delivered').count()
    cancelled_orders = orders_qs.filter(status='cancelled').count()

    # Today's statistics
    today = timezone.now().date()
    today_orders = orders_qs.filter(date=today).count()
    today_revenue = 0
    for order in orders_qs.filter(date=today):
        for of in order.orderfood_set.all():
            today_revenue += of.price * of.stock

    # This week's statistics
    week_start = today - timedelta(days=today.weekday())
    week_orders = orders_qs.filter(date__gte=week_start).count()
    week_revenue = 0
    for order in orders_qs.filter(date__gte=week_start):
        for of in order.orderfood_set.all():
            week_revenue += of.price * of.stock

    # Menu statistics
    total_foods = foods_qs.count()
    available_foods = Menu.objects.filter(is_available=True, food__in=foods_qs).count() if restaurant_id else Menu.objects.filter(is_available=True).count()

    # Inventory statistics
    inventory_qs = Inventory.objects.all()
    if restaurant_id:
        inventory_qs = inventory_qs.filter(restaurant_id=restaurant_id)
    low_stock_items = inventory_qs.filter(stock_quantity__lte=F('min_stock_level')).count()
    total_inventory_items = inventory_qs.count()

    # Review statistics
    reviews_qs = Comment.objects.all()
    if restaurant_id:
        reviews_qs = reviews_qs.filter(resID_id=restaurant_id)
    total_reviews = reviews_qs.count()
    avg_rating = reviews_qs.aggregate(avg=Avg('review'))['avg'] or 0

    # Worker statistics
    total_workers = Worker.objects.count()
    active_deliveries = Delivery.objects.filter(status='on_the_way').count()

    return Response({
        'orders': {
            'total': total_orders,
            'pending': pending_orders,
            'approved': approved_orders,
            'preparing': preparing_orders,
            'ready': ready_orders,
            'delivered': delivered_orders,
            'cancelled': cancelled_orders,
        },
        'today': {
            'orders': today_orders,
            'revenue': today_revenue,
        },
        'this_week': {
            'orders': week_orders,
            'revenue': week_revenue,
        },
        'menu': {
            'total_foods': total_foods,
            'available_foods': available_foods,
        },
        'inventory': {
            'total_items': total_inventory_items,
            'low_stock_items': low_stock_items,
        },
        'reviews': {
            'total': total_reviews,
            'average_rating': round(avg_rating, 2),
        },
        'workers': {
            'total': total_workers,
            'active_deliveries': active_deliveries,
        }
    })
