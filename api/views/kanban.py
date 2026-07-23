from api.constants import SUCCESS_STATUS_CODE, APIMessages, METHOD_NOT_ALLOWED
from backend.models import KanbanComment, KanbanItem, KanbanProfile, KanbanColumn
from api.serializers import (
    KanbanProfileSerializer, KanbanItemSerializer, KanbanColumnSerializer
)
from api.decorators import jwt_authentication_required
from api.throttles import SustainedRateThrottle
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from datetime import datetime


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def Kanban(request, profile_id=None):

    # get items
    if request.method == 'GET':
        # Get all kanban profiles
        branch_id = request.GET['branch_id']
        user_id = request.GET['user_id']
        kanban_profiles = KanbanProfile.objects.filter(
            user_id=user_id, branch_id=branch_id).values()
        total_rows = kanban_profiles.count()
        serializer = KanbanProfileSerializer(kanban_profiles, many=True)
        # Return the serialized data in the response
        return Response({
            "data": {
                "count": total_rows,
                "rows": list(serializer.data)
            },
            "message": APIMessages.ALL_EXPENSE_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        })

    elif request.method == 'POST':
        data = request.data
        user_id = data.get('user_id')
        salon_id = data.get('salon_id')
        branch_id = data.get('branch_id')
        kanban_items = data.get('kanban_items', [])

        # Check if a Kanban profile already exists for the user, salon, and branch combination
        kanban_profile, created = KanbanProfile.objects.get_or_create(
            user_id=user_id,
            salon_id=salon_id,
            branch_id=branch_id
        )

        if not created:
            # If the profile already exists, add Kanban items to the existing profile
            for item_id in kanban_items:
                kanban_item = KanbanItem.objects.get(pk=item_id)
                kanban_profile.kanban_items.add(kanban_item)

            return Response({
                "message": APIMessages.KANBAN_ITEM_CREATED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        else:
            # If the profile was created, assign the Kanban items directly
            kanban_profile.kanban_items.set(kanban_items)

            return Response({
                "message": APIMessages.KANBAN_ITEM_CREATED.value,
                "status": SUCCESS_STATUS_CODE,
            })

    elif request.method == 'PUT':
        if profile_id is None:
            return Response({'error': 'Profile ID is required for updating'}, status=400)

        kanban_profile = get_object_or_404(KanbanProfile, pk=profile_id)
        data = request.data
        kanban_profile.user_id = data.get('user_id', kanban_profile.user_id)
        kanban_profile.salon_id = data.get('salon_id', kanban_profile.salon_id)
        kanban_profile.branch_id = data.get(
            'branch_id', kanban_profile.branch_id)
        if 'kanban_items' in data:
            kanban_profile.kanban_items.set(data.get('kanban_items'))
        kanban_profile.save()

        return Response({
            "message": APIMessages.KANBAN_ITEM_UPDATED.value,
            "status": SUCCESS_STATUS_CODE,
        })

    elif request.method == 'DELETE':
        if profile_id is None:
            return Response({'error': 'Profile ID is required for deletion'}, status=400)

        kanban_profile = get_object_or_404(KanbanProfile, pk=profile_id)
        kanban_profile.delete()

        return Response({
            "message": APIMessages.KANBAN_ITEM_DELETED.value,
            "status": SUCCESS_STATUS_CODE,
        })


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def handle_user_story(request, profile_id=None):
    if request.method == 'POST':
        data = request.data
        user_id = data.get('user_id')
        salon_id = data.get('salon_id')
        branch_id = data.get('branch_id')
        branch_id = data.get('branch_id')
        story = data.get('story')

        # columnId, columns, item, items, storyId, userStory

        # Check if a Kanban profile already exists for the user, salon, and branch combination
        # kanban_profile, created = KanbanProfile.objects.get_or_create(
        #     user_id=user_id,
        #     salon_id=salon_id
        # )

        if not created:

            return Response({
                "message": APIMessages.KANBAN_ITEM_CREATED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        else:
            # If the profile was created, assign the Kanban items directly
            kanban_profile.kanban_items.set(kanban_items)

            return Response({
                "message": APIMessages.KANBAN_ITEM_CREATED.value,
                "status": SUCCESS_STATUS_CODE,
            })


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def handle_profiles(request, profile_id=None):
    # Frontend uses POST to fetch; also accept GET with query params
    if request.method in ('POST', 'GET'):
        data = request.data if request.method == 'POST' else request.GET
        branch_id = data.get('branch_id')
        user_id = data.get('user_id')
        salon_id = data.get('salon_id')
        kanban_profiles = KanbanProfile.objects.filter(
            user_id=user_id, branch_id=branch_id, salon_id=salon_id)
        total_rows = kanban_profiles.count()
        serializer = KanbanProfileSerializer(kanban_profiles.all(), many=True)

        return Response({
            "data": {
                "count": total_rows,
                "rows": list(serializer.data)
            },
            "message": APIMessages.ALL_KANBAN_ITEMS_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        })
    return Response({
        "message": APIMessages.METHOD_NOT_ALLOWED.value,
        "status": METHOD_NOT_ALLOWED,
    }, status=METHOD_NOT_ALLOWED)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def handle_items(request, profile_id=None):
    if request.method in ('POST', 'GET'):
        data = request.data if request.method == 'POST' else request.GET
        branch_id = data.get('branch_id')
        user_id = data.get('user_id')
        salon_id = data.get('salon_id')
        kanban_profile = KanbanProfile.objects.filter(
            user_id=user_id, branch_id=branch_id, salon_id=salon_id).first()
        if kanban_profile is None:
            return Response({
                "data": {"count": 0, "rows": []},
                "message": APIMessages.ALL_KANBAN_ITEMS_RETRIEVED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        kanban_items = kanban_profile.kanban_items
        total_rows = kanban_items.count()
        serializer = KanbanItemSerializer(kanban_items, many=True)

        return Response({
            "data": {
                "count": total_rows,
                "rows": list(serializer.data)
            },
            "message": APIMessages.ALL_KANBAN_ITEMS_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        })
    return Response({
        "message": APIMessages.METHOD_NOT_ALLOWED.value,
        "status": METHOD_NOT_ALLOWED,
    }, status=METHOD_NOT_ALLOWED)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def add_kanban_items(request, profile_id=None):
    # get profiles
    if request.method == 'POST':
        # Get all kanban profiles
        data = request.data
        branch_id = data.get('branch_id')
        user_id = data.get('user_id')
        salon_id = data.get('salon_id')
        item = data.get('item')
        column_id = data.get('columnId')


        # Check if a Kanban profile already exists for the user, salon, and branch combination
        kanban_profile, created = KanbanProfile.objects.get_or_create(
            user_id=user_id,
            salon_id=salon_id,
            branch_id=branch_id
        )

        item_due_date = datetime.strptime(
            item['dueDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
        new_kanban_item = KanbanItem(
            assign=kanban_profile.user,
            description=item['description'],
            dueDate=item_due_date,
            title=item['title'],
            priority=item['priority'],

        )
        new_kanban_item.save()

        kanban_column = KanbanColumn.objects.get(pk=column_id)
        kanban_column.itemIds.add(new_kanban_item)
        kanban_column.save()

        kanban_profile.kanban_items.add(new_kanban_item)
        kanban_profile.save()

        kanban_items = kanban_profile.kanban_items
        total_rows = kanban_items.count()

        column_serializer = KanbanColumnSerializer(
            kanban_profile.kanban_columns, many=True)

        serializer = KanbanItemSerializer(kanban_items, many=True)


        # if not created:
        #     # If the profile already exists, add Kanban items to the existing profile
        #     for item_id in kanban_items:
        #         kanban_item = KanbanItem.objects.get(pk=item_id)
        #         kanban_profile.kanban_items.add(kanban_item)

        # else:
        #     # If the profile was created, assign the Kanban items directly
        #     kanban_profile.kanban_items.set(kanban_items)

        # Return the serialized data in the response
        return Response({
            "data": {
                "items": {
                    "count": total_rows,
                    "rows": list(serializer.data)
                },
                "columns": {
                    "count": kanban_profile.kanban_columns.count(),
                    "rows": list(column_serializer.data)
                },
            },
            "message": APIMessages.ALL_EXPENSE_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        })


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def handle_columns(request, column_id=None):
    if request.method in ('POST', 'GET'):
        data = request.data if request.method == 'POST' else request.GET
        branch_id = data.get('branch_id')
        user_id = data.get('user_id')
        salon_id = data.get('salon_id')

        kanban_profile, created = KanbanProfile.objects.get_or_create(
            user_id=user_id,
            salon_id=salon_id,
            branch_id=branch_id
        )

        kanban_columns = kanban_profile.kanban_columns
        total_rows = kanban_columns.count()
        serializer = KanbanColumnSerializer(kanban_columns, many=True)

        return Response({
            "data": {
                "count": total_rows,
                "rows": list(serializer.data)
            },
            "message": APIMessages.ALL_KANBAN_ITEMS_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        })

    if request.method == 'DELETE':
        if column_id is None:
            return Response({'error': 'Invalid Column Id'}, status=400)

        kanban_column = get_object_or_404(KanbanColumn, pk=column_id)
        kanban_column.delete()

        return Response({
            "message": APIMessages.KANBAN_COLUMN_DELETED.value,
            "status": SUCCESS_STATUS_CODE,
        })

    return Response({
        "message": APIMessages.METHOD_NOT_ALLOWED.value,
        "status": METHOD_NOT_ALLOWED,
    }, status=METHOD_NOT_ALLOWED)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def reorder_kanban_items(request, profile_id=None):
    # get profiles
    if request.method == 'PUT':
        # Get all kanban profiles
        data = request.data
        branch_id = data.get('branch_id')
        user_id = data.get('user_id')
        salon_id = data.get('salon_id')
        columns = data.get('columns')
        updated_kanban_columns = []

        for column in columns:
            kanban_column = KanbanColumn.objects.get(pk=int(column['id']))
            item_ids = []
            for item_id in column['itemIds']:
                kanban_item = KanbanItem.objects.get(pk=int(item_id))
                item_ids.append(kanban_item)
            kanban_column.itemIds.set(item_ids)
            kanban_column.save()
            updated_kanban_columns.append(kanban_column)

        # Check if a Kanban profile already exists for the user, salon, and branch combination
        kanban_profile, created = KanbanProfile.objects.get_or_create(
            user_id=user_id,
            salon_id=salon_id,
            branch_id=branch_id
        )
        # item_due_date = datetime.strptime(
        #     item['dueDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
        # new_kanban_item = KanbanItem(
        #     assign=kanban_profile.user,
        #     description=item['description'],
        #     dueDate=item_due_date,
        #     title=item['title'],
        #     priority=item['priority'],

        # )
        # new_kanban_item.save()

        # kanban_profile.kanban_items.add(new_kanban_item)
        # kanban_profile.save()
        kanban_profile.kanban_columns.set(updated_kanban_columns)
        kanban_profile.save()

        kanban_columns = kanban_profile.kanban_columns
        total_rows = kanban_columns.count()
        serializer = KanbanColumnSerializer(kanban_columns, many=True)

        # if not created:
        #     # If the profile already exists, add Kanban items to the existing profile
        #     for item_id in kanban_items:
        #         kanban_item = KanbanItem.objects.get(pk=item_id)
        #         kanban_profile.kanban_items.add(kanban_item)

        # else:
        #     # If the profile was created, assign the Kanban items directly
        #     kanban_profile.kanban_items.set(kanban_items)

        # Return the serialized data in the response
        return Response({
            "data": {
                "count": total_rows,
                "rows": list(serializer.data)
            },
            "message": APIMessages.ALL_EXPENSE_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        })


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def add_columns(request, profile_id=None):
    # get profiles
    if request.method == 'POST':
        # Get all kanban profiles
        data = request.data
        branch_id = data.get('branch_id')
        user_id = data.get('user_id')
        salon_id = data.get('salon_id')
        title = data.get('column')['title']

        # Check if a Kanban profile already exists for the user, salon, and branch combination
        kanban_profile, created = KanbanProfile.objects.get_or_create(
            user_id=user_id,
            salon_id=salon_id,
            branch_id=branch_id
        )
        # item_due_date = datetime.strptime(
        #     item['dueDate'], "%Y-%m-%dT%H:%M:%S.%fZ")
        # new_kanban_item = KanbanItem(
        #     assign=kanban_profile.user,
        #     description=item['description'],
        #     dueDate=item_due_date,
        #     title=item['title'],
        #     priority=item['priority'],

        # )
        # new_kanban_item.save()

        # kanban_profile.kanban_items.add(new_kanban_item)
        # kanban_profile.save()

        kanban_profile.kanban_columns.add(
            KanbanColumn.objects.create(title=title))
        kanban_profile.save()
        kanban_columns = kanban_profile.kanban_columns
        total_rows = kanban_columns.count()

        serializer = KanbanColumnSerializer(kanban_columns, many=True)


        # if not created:
        #     # If the profile already exists, add Kanban items to the existing profile
        #     for item_id in kanban_items:
        #         kanban_item = KanbanItem.objects.get(pk=item_id)
        #         kanban_profile.kanban_items.add(kanban_item)

        # else:
        #     # If the profile was created, assign the Kanban items directly
        #     kanban_profile.kanban_items.set(kanban_items)

        # Return the serialized data in the response
        return Response({
            "data": {
                "count": total_rows,
                "rows": list(serializer.data)
            },
            "message": APIMessages.ALL_EXPENSE_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        })


'''
from backend.models import KanbanItem, KanbanProfile, KanbanColumn, KanbanComment
from django.contrib.auth.models import User

# Create a user
user = User.objects.create(username='testuser', password='password')

# Create some columns
column1 = KanbanColumn.objects.create(title='Column 1')
column2 = KanbanColumn.objects.create(title='Column 2')

# Create a profile
profile = KanbanProfile.objects.create(user=user, salon=None, branch=None)

# Create some items
item1 = KanbanItem.objects.create(
    assign='Assignee 1',
    attachments={'file1.txt', 'file2.txt'},
    commentIds=[1, 2],
    description='Task 1 Description',
    dueDate='2024-01-31T12:00:00Z',
    image='image1.jpg',
    priority='low',
    title='Task 1',
    status='TODO',
    column=column1,
)

item2 = KanbanItem.objects.create(
    assign='Assignee 2',
    attachments={'file3.txt', 'file4.txt'},
    commentIds=[3, 4],
    description='Task 2 Description',
    dueDate='2024-02-15T14:30:00Z',
    image='image2.jpg',
    priority='medium',
    title='Task 2',
    status='IN_PROGRESS',
    column=column2,
)

# Create some comments
comment1 = KanbanComment.objects.create(comment='Comment 1', profile=profile)
comment2 = KanbanComment.objects.create(comment='Comment 2', profile=profile)

# Add items and comments to the profile
profile.kanban_items.add(item1, item2)
profile.save()

exit()
'''
