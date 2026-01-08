from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from django.utils import timezone

from api.models import Food, Order, OrderFood, Category, Restaurant
from restaurant_web.models import Menu, OrderStatus
from common.permissions import JWTAuthentication


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


@api_view(['GET'])
def dashboard(request):
    """Dashboard view with statistics"""
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    approved_orders = Order.objects.filter(status='approved').count()
    total_foods = Food.objects.count()

    return Response({
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'approved_orders': approved_orders,
        'total_foods': total_foods,
    })
