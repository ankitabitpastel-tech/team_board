from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from .models import employees, projects, project_memberships
from .serializers import employeesserializer, projectcreateserializer, projectresponseserializer, projectmembershipserializer
from rest_framework.decorators import api_view
from .utils.id_hasher import IDhasher
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q

@api_view(['POST'])
def employee_create(request):
    try: 
        serializer = employeesserializer(data=request.data)
        print("Request data:", request.data)
        if serializer.is_valid():
            instance=serializer.save()
            print(f"Instance saved with ID:{instance.id}")
            print(f"Instance saved with password:{instance.password}")

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
    try:
        limit = int(request.data.get('limit', 0))
        page = int(request.data.get('page', 1))

        employees_set = employees.objects.exclude(status='5').order_by('created_at')
        total_count = employees_set.count()
        
        if limit == 0:
            serializer = employeesserializer(employees_set, many=True)
            return Response({
                'status': 'success',
                'message':'employees retrived successfully',
                'data': serializer.data 
            }, status= status.HTTP_200_OK)
        
        if limit <= 0 or page <1:
            return Response({
                'status':'error',
                'message':'limit and page must be positive integers.',
                'data':'{}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            try:
                offset = (page - 1)*limit

                employee_list = employees_set[offset:offset + limit]
                serializer = employeesserializer(employee_list, many=True)
                total_pages = (total_count + limit -1)// limit

                return Response({
                    'status': 'success',
                    'message': f'employees page {page} retrieved successfully',
                    'pagination': {
                        'current_page': page,
                        'total_pages': total_pages,
                        'limit_per_page': limit,
                        'has_next': page < total_pages,
                        'has_previous': page > 1,
                        'next_page': page + 1 if page < total_pages else None,
                        'previous_page': page - 1 if page > 1 else None,

                    },
                    'data': serializer.data 
                }, status= status.HTTP_200_OK)
            except ValueError:
                return Response({
                'status' : 'error',
                'message': 'Invalid pagination parameters. limit and page must be int'
            })

    except Exception as e:
                return Response({
                'status' : 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def employee_detail(request):
    try:
        employee_id_val= request.data.get('employee_id')

        if not employee_id_val:
            return Response({
                'status':'error',
                'message': 'employee_id is required!'
            }, status= status.HTTP_400_BAD_REQUEST)
        
        # try:
        #     employee = employees.objects.filter(id = employee_id).exclude(status='5').first()
           
        # except Exception as e:
        #     return Response({
        #         'status': 'error',
        #         'message': f'Employee not found str{e}' 
        #     }, status= status.HTTP_404_NOT_FOUND)
                
        employee = None
        all_employees = employees.objects.exclude(status='5')

        if isinstance(employee_id_val, str) and len(employee_id_val) == 32:
            for emp in all_employees:
                if IDhasher.to_md5(emp.id) == employee_id_val:
                    employee = emp
                    break
        
        else:
            # try:
            #     employee_id_int = int(employee_id_val) 
            #     employee = all_employees.filter(id=employee_id_int).first()
            # except ValueError:
                return Response({
                'status': 'error',
                'message': 'Invalid employee_id format',
                }, status= status.HTTP_404_NOT_FOUND)
        
        if not employee:
            return Response({
                'status': 'error',
                'message': 'Employee not found'
                }, status= status.HTTP_404_NOT_FOUND)
        
        serializer = employeesserializer(employee)

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
        
        employee = None
        all_employees = employees.objects.exclude(status='5')

        if isinstance(employee_id, str) and len(employee_id) == 32:
            for emp in all_employees:
                if IDhasher.to_md5(emp.id) == employee_id:
                    employee = emp
                    break
        
        else:
                return Response({
                'status': 'error',
                'message': 'Invalid employee_id format',
                }, status= status.HTTP_404_NOT_FOUND)
        

        try:
            employee = employees.objects.get(id=emp.id, status__in=['0','1']) 
        except employees.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Not Found'
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