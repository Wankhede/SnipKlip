from api.common import apply_filters, custom_pagination, get_all_table_records
from api.throttles import SustainedRateThrottle
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from backend.models import *
from api.serializers import ProductSerializer
from api.constants import *

# @group_required('Manager')
@api_view(['PUT', 'POST','GET'])
@throttle_classes([SustainedRateThrottle])
def getAllProducts(request, column_name=None, column_value=None):
    if request.method == "GET":
        if column_value is None:
            branch_id = request.GET['branch_id']
            request_args = request.GET
            if branch_id == '-1':
                products = get_all_table_records(request, Product)
            else:
                branch = Branch.objects.get(id=branch_id)
                products = Product.objects.filter(branch=branch).order_by('-id')

            final_products_list = apply_filters(Product, products, request_args)

            total_rows = final_products_list.count()
            
            # Call the custom_pagination function to get the paginated items.
            products = custom_pagination(request, final_products_list)   
            serializer = ProductSerializer(final_products_list, many=True)

            # Return the serialized data in the response
            return Response({
                "data": {
                    "count": total_rows,
                    "rows": serializer.data
                },
                "message": APIMessages.ALL_PRODUCT_RETRIEVED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        else:
            data = request.GET
            try:
                # Check if column_name is a valid field in the Product model
                valid_fields = [f.name for f in Product._meta.get_fields()]
                if column_name not in valid_fields:
                    return Response({"message": f"Invalid column name: {column_name}", "status":400})

                # Build a dynamic filter using double-underscore notation
                filter_kwargs = {f"{column_name}__exact": column_value} if column_name else {}
                product = Product.objects.get(**filter_kwargs)
                serializer = ProductSerializer(product, many=False)
                return Response({
                        "data": {
                            "count": len(serializer.data),
                            "rows": [serializer.data]
                        },
                        "message": APIMessages.PRODUCT_RETRIEVED.value,
                        "status": SUCCESS_STATUS_CODE,
                })
            except Exception:
                return Response({
                            "message": APIMessages.PRODUCT_NOT_FOUND.value,
                            "status": BAD_REQUEST_STATUS
                    })
            
    elif request.method == "PUT":
        data = request.data
        try:
            product = Product.objects.get(id=data['id'])
            if product.branch.id == data['branch_id']:
                product.name = data['name']
                product.category = data['category']
                product.description = data['description']
                product.price = data['price']
                product.availablity = data['availablity']
                product.quantity = data['quantity']

                if data['sku'] == None or data['sku'] == 'None':
                    product.sku = ''
                else:
                    product.sku = data['sku']
                
                product.save()

                return Response({
                    'message':APIMessages.PRODUCT_UPDATED.value,
                    'status':SUCCESS_STATUS_CODE
                })
            else:
                return Response({
                    'message':APIMessages.PRODUCT_NOT_FOUND.value,
                    'status':BAD_REQUEST_STATUS
                })
        except Exception:
            return Response({
                'message':APIMessages.PRODUCT_NOT_FOUND.value,
                'status':BAD_REQUEST_STATUS
            })

    elif request.method == "POST":
        data = request.data
        if not hasattr(data, 'get'):
            return Response({
                "message": "Invalid JSON body; expected an object",
                "status": BAD_REQUEST_STATUS,
            }, status=BAD_REQUEST_STATUS)

        product_name = data.get('name', '')
        product_price = data.get('price', '')
        product_descrition = data.get('description', '')
        product_availablity = data.get('status', '') or data.get('availablity', '')
        product_category = data.get('category', '')
        product_image = request.FILES.get('product_image', '')
        product_quantity = data.get('quantity', '')
        product_sku = data.get('sku', '')
        branch_id = data.get('branch_id')
        salon_id = data.get('salon_id')

        try:
            if branch_id:
                branch_associated = Branch.objects.get(id=branch_id)
            elif salon_id:
                branch_associated = Branch.objects.filter(salon_id=salon_id).first()
                if branch_associated is None:
                    raise Branch.DoesNotExist
            else:
                user = User.objects.get(id=data.get('user_id'))
                salon_associate = SalonDetails.objects.filter(user=user).first()
                if salon_associate is None:
                    return Response({
                        "message": APIMessages.SALON_NOT_FOUND.value,
                        "status": BAD_REQUEST_STATUS,
                    })
                branch_associated = Branch.objects.filter(salon=salon_associate).first()
                if branch_associated is None:
                    raise Branch.DoesNotExist
        except (User.DoesNotExist, Branch.DoesNotExist, SalonDetails.DoesNotExist, TypeError, ValueError):
            return Response({
                "message": APIMessages.PRODUCT_NOT_FOUND.value,
                "status": BAD_REQUEST_STATUS,
            })

        if product_image == None or not product_image or product_image == "":
            product_image = None

        try:
            # Creating Product object with data from POST request
            product_save = Product(
                name=product_name,
                price=product_price,
                description=product_descrition,
                category=product_category,
                image=product_image,
                availablity=product_availablity,
                quantity=product_quantity,
                branch=branch_associated,
                sku=product_sku or '',
            )
            product_save.save()
            return Response({
                "message": APIMessages.PRODUCT_CREATED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        except Exception:
            return Response({
                "message": APIMessages.PRODUCT_NOT_FOUND.value,
                "status": BAD_REQUEST_STATUS,
            })
        
@api_view(['POST'])
def deleteProduct(request,product_id):
    data = request.data
    if not Product.objects.filter(id=product_id) or not User.objects.filter(id=data['user_id']):
        return Response({
            'message':APIMessages.PRODUCT_NOT_FOUND.value,
            'status':BAD_REQUEST_STATUS
        })
    else:
        product = Product.objects.get(id=product_id)
        user = User.objects.get(id=data['user_id'])
        if not SalonDetails.objects.filter(user=user):
            return Response({
                'message':APIMessages.SALON_NOT_FOUND.value,
                'status':BAD_REQUEST_STATUS
            })
        else:
            try:
                branch = Branch.objects.get(id=data['branch_id'])
            except:
                return Response({
                    'message':APIMessages.PRODUCT_DOES_NOT_BELONGS_TO_YOU.value,
                    'status':BAD_REQUEST_STATUS
                })
            if not Product.objects.filter(id=product_id,branch=branch):
                return Response({
                    'message':APIMessages.PRODUCT_DOES_NOT_BELONGS_TO_YOU.value,
                    'status':BAD_REQUEST_STATUS
                })
            else:
                product.delete()
                return Response({
                    'message':APIMessages.PRODUCT_DELETE_SUCCESS.value,
                    'status':BAD_REQUEST_STATUS
                })

