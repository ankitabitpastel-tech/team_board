from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from .models import employees, projects, project_memberships
from .serializers import employeesserializer, projectcreateserializer, projectresponseserializer, projectmembershipserializer
from rest_framework.decorators import api_view
from .utils.id_hasher import IDhasher
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q

VALID_API_KEYS = {
    'teamboard_admin_2025'
}

def require_api_key(view_func):
    def wrapper(request, *args, **kwargs):
        api_key = request.META.get('HTTP_X_API_KEY') or request.META.get('HTTP_AUTHORIZATION')
        print(f"Received API Key: {api_key}")  # Debug print
        print(f"Valid Keys: {VALID_API_KEYS}")  

        # is_valid, message = check_api_key(request)
        if not api_key:
            return Response({
                'status':'error',
                'message': 'API key required'
            }, status=status.HTTP_401_UNAUTHORIZED)
        # if api_key.startswith('Bearer'):
        #     api_key = api_key[7:]

        if api_key not in VALID_API_KEYS:
            return Response({
                'status':'error',
                'message': 'Invalid API Key'
            }, status=status.HTTP_401_UNAUTHORIZED)

        return view_func(request, *args, **kwargs)
    return wrapper


@api_view(['POST'])
@require_api_key
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
@require_api_key
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
@require_api_key
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
@require_api_key
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
        
        if not employee:
            return Response({
                'status': 'error',
                'message': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)

        if employee.status == '5':
            return Response({
                'status': 'error',
                'message': 'Employee is already deleted'
            }, status=status.HTTP_400_BAD_REQUEST)


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
@require_api_key
def create_project(request):
    if request.method == 'POST':
        try:
            serializer = projectcreateserializer(data=request.data)
            if serializer.is_valid():
                project=serializer.save()
                response_serializer = projectresponseserializer(project)
                print(f"Response data: {response_serializer.data}")
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
@require_api_key
def project_list(request):
    try:
        limit = int(request.data.get('limit', 0))
        page = int(request.data.get('page', 1))

        all_projects = projects.objects.exclude(status='5').order_by('created_at')
        total_count = all_projects.count()

        if limit == 0:
            serializer = projectresponseserializer(all_projects, many=True)
            return Response({
                'status': "success",
                'message': 'projects retrived successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        if limit <= 0 or page < 1:
            return Response({
                'status': 'error',
                'message': 'limit and page must be positive integers.',
                'data': {}
            }, status=status.HTTP_400_BAD_REQUEST)
        
        offset = (page - 1) * limit
        project_list = all_projects[offset:offset + limit]
        serializer = projectresponseserializer(project_list, many=True)
        total_pages = (total_count + limit - 1) // limit
        
        return Response({
            'status': 'success',
            'message': f'projects page {page} retrieved successfully',
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_records': total_count,
                'limit_per_page': limit,
                'has_next': page < total_pages,
                'has_previous': page > 1
            },
            'data': serializer.data 
        }, status=status.HTTP_200_OK)
    
    except ValueError:
        return Response({
            'status' : 'error',
            'message': 'Invalid pagination parameters. limit and bouth must be integers'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'status':'error',
            'message':f"Server error:{str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
@require_api_key
def project_detail(request):
    try:
        project_id = request.data.get('project_id')

        if not project_id:
            return Response({
                'status': 'error',
                'message': 'project_id is required!'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        project = None
        all_projects = projects.objects.exclude(status='5')

        if isinstance(project_id, str) and len(project_id) == 32:
            for proj in all_projects:
                if IDhasher.to_md5(proj.id) == project_id:
                    project = proj
                    break
        
        else:
            return Response({
                'status': 'error',
                'message':'Invalid project_id format. Must be MD5 hash', 
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not project:
            return Response({
                'status':'error',
                'message':'No project found'
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = projectresponseserializer(project)

        return Response({
            'status':'success',
            'message': 'project ditailes retrived.',
            'data':serializer.data
        })
    except Exception as e:
        return Response({
            'status':'error',
            'message':str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['POST'])
@require_api_key
def project_add_meber(request):
    try:
        serializer = projectmembershipserializer(data=request.data)

        if serializer.is_valid():
            project_id = serializer.validated_data['project_id']
            member_id = serializer.validated_data['member_id']
            is_admin = serializer.validated_data.get('is_admin', False)

            existing_memberships = project_memberships.objects.filter(
                project_id = project_id,
                member_id=member_id,
                status='1'
            ).first()

            if existing_memberships:
                return Response({
                    'status':'error',
                    'message':"Member is already part of this group"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            membership = project_memberships.objects.create(
                project_id_id=project_id,
                member_id_id=member_id,   
                is_admin=is_admin,
                status='1'
            )

            response_serializer = projectmembershipserializer(membership)

            return Response({
                'status': 'OK',
                'message': 'Member added successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'status': 'error',
                'message': 'Invalid data!',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({
            'status':'error',
            'message': f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)