from rest_framework.response import Response
from rest_framework.decorators import api_view
from backend.models import Todo
from api.serializers import TodoSerializer
from api.constants import *

# API to handle todos with HTTP methods GET, POST, and PUT
@api_view(['GET', 'POST', 'PUT'])
def todos_api(request, column_name=None, column_value=None, id=None):
    try:
        # URL route may pass column_value; legacy callers may pass id=
        if id is None and column_value is not None:
            id = column_value

        # Check if the request method is GET
        if request.method == 'GET':
            # If no specific 'id' provided, retrieve all todos
            if id is None:
                todos = Todo.objects.all()
                serializer = TodoSerializer(todos, many=True)
                # Prepare the response data with count and serialized data
                response_data = {
                    "data": {
                        "count": todos.count(),
                        "rows": serializer.data
                    },
                    "message": APIMessages.ALL_TODO_RETRIEVED.value,
                    "status": SUCCESS_STATUS_CODE
                }
            else:
                try:
                    # If 'id' is provided, retrieve the specific todo
                    todo = Todo.objects.get(id=id)
                    serializer = TodoSerializer(todo)
                    # Prepare the response data with count and serialized data
                    response_data = {
                        "data": {
                            "count": 1,
                            "rows": serializer.data
                        },
                        "message": APIMessages.TODO_RETRIEVED.value,
                        "status": SUCCESS_STATUS_CODE
                    }
                except Todo.DoesNotExist:
                    # Return a 404 response if the requested todo is not found
                    return Response({
                        "message": APIMessages.TODO_NOT_FOUND.value,
                        "status": NOT_FOUND_STATUS,
                    })

            # Return the response with appropriate data
            return Response(response_data)

        elif request.method == 'POST':
            # If the request method is POST, create a new todo
            serializer = TodoSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                # Prepare the response data with serialized data and status code 201 (Created)
                response_data = {
                    "data": serializer.data,
                    "message": APIMessages.TODO_CREATED.value,
                    "status": CREATED_CODE
                }
                return Response(response_data, status=CREATED_CODE)  # 201 Created status code
            return Response(serializer.errors, status=FAILED_STATUS_CODE)

        elif request.method == 'PUT':
            # If the request method is PUT, update the existing todo
            try:
                todo = Todo.objects.get(id=id)
                todo.status = request.data["status"]
                todo.save()

                serializer = TodoSerializer(todo)
                # Prepare the response data with serialized data and status code 200
                response_data = {
                    "data": serializer.data,
                    "message": APIMessages.TODO_UPDATED.value,
                    "status": SUCCESS_STATUS_CODE
                }
                return Response(response_data)
            except Todo.DoesNotExist:
                # Return a 404 response if the todo to update is not found
                return Response({
                    "message": APIMessages.TODO_NOT_FOUND.value,
                    "status": NOT_FOUND_STATUS,
                })
    except Exception as e:
        # If an unexpected error occurs, return an error response with status code 500
        return Response({
            "message": APIMessages.ERROR.value,
            "status": FAILED_STATUS_CODE,
        })

    # If the request method is not supported, return a 405 Method Not Allowed response
    return Response({
        "message": APIMessages.METHOD_NOT_ALLOWED.value,
        "status": METHOD_NOT_ALLOWED,
    })
