from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from .models import employees, projects, project_memberships
from .serializers import employeesserializer, projectcreateserializer, projectresponseserializer, projectmembershipserializer
from rest_framework.decorators import api_view

@api_view(['POST'])
def employee_create(request):
    try: 
        serializer = employeesserializer(data=request.data)
        print("Request data:", request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message' : 'employee added successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'status': 'error',
                'message':'Invalid data',
                'errors':serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'status':'error',
            'message':str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def employee_list(request):
    employee = employees.objects.exclude(status='5')
    serializer = employeesserializer(employee, many=True)
    return Response({
        'status': 'success',
        'message':'employees retrived successfully',
        # 'count': employee.count(),
        'data': serializer.data 
    }, status= status.HTTP_200_OK)

@api_view(['POST'])
def employee_detail(request):
    try:
        employee_id= request.data.get('employee_id')

        if not employee_id:
            return Response({
                'status':'error',
                'message': 'employee_id is required!'
            }, status= status.HTTP_400_BAD_REQUEST)
        try:
            employee = employees.objects.get(id = employee_id).exclude(status='5')
        except employee.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Employee not found'
            }, status= status.HTTP_404_NOT_FOUND)
        
        
        employee = employees.objects.filter(id = employee_id).exclude(status='5').first()
        serializer = employeesserializer(employee)

        if not employee:
            return Response({
                'status': 'error',
                'message': 'Employee not found'
                }, status= status.HTTP_404_NOT_FOUND)
        
        return Response({
                'status':'success',
                'data': serializer.data
            })
        
           
    except Exception as e:
        return Response({
            'status': 'error',
            'message':str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def employee_remove(request):
    try: 
        employee_id = request.data.get('employee_id')
        
        if not employee_id:
            return Response({
                'status':'error',
                'message':'employee_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = employees.objects.get(id=employee_id, status__in=['0','1']) 
        except employees.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'employee_id is required in payload'
            }, status=status.HTTP_404_NOT_FOUND)

        employee.status='5'
        employee.save()

        serializer = employeesserializer(employee)

        return Response({
            'status':'success',
            'message': 'Employee removed successfully',
            'data':serializer.data
        })
    except Exception as e:
        return Response({
            'status':'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
def create_project(request):
    if request.method == 'POST':
        try:
            serializer = projectcreateserializer(data=request.data)
            if serializer.is_valid():
                project=serializer.save()
                response_serializer = projectresponseserializer(project)

                return Response({
                    'status': 'OK',
                    'message':'project creaed successfully',
                    'data': response_serializer.data
                }, status=status.HTTP_201_CREATED)
            else :
                return Response({
                    'status': 'error',
                    'message':'Invalid data!',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print("Exception:", str(e))
            return Response({
                'status':'error',
                'message': f'server error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

@api_view(['POST'])
def project_list(request):
    try:
        all_projects = projects.objects.exclude(status='5')
        serializer = projectresponseserializer(all_projects, many=True)

        return Response({
            'status': "success",
            'message': 'projects retrived successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    
        
    except Exception as e:
        return Response({
            'status':'error',
            'message':f"Server error:{str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)