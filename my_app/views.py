from django.utils import timezone
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from .models import employees, projects, project_memberships, messages
from .serializers import employeesserializer, projectcreateserializer, projectresponseserializer, projectmembershipserializer, messageserializer
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
            }, status=status.HTTP_400_BAD_REQUEST),
        
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
def project_add_member(request):
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
    
@api_view(['POST'])
@require_api_key
def project_remove_member(request):
    try: 
        project_id_hash = request.data.get('project_id')
        member_id_hash = request.data.get('member_id')

        if not project_id_hash or not member_id_hash:
            return Response({
                'status':'error',
                'message':'Both project_id and member_id are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(project_id_hash) != 32 or len(member_id_hash) != 32:
            return Response({
                'status':'error',
                'message':'project_id and member_id must be valid.'
            }, status=status.HTTP_400_BAD_REQUEST)

        project = find_project_by_hash(project_id_hash)
        if not project:
            return Response({
                'status':'error',
                'message':'Project not found'
            }, status=status.HTTP_404_NOT_FOUND)

        member = find_employee_by_hash(member_id_hash)
        if not member:
            return Response({
                'status':'error',
                'message':'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)

        if member.status == '5':
            return Response({
                'status':'error',
                'message':'Cannot remove deleted employee'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try: 
            membership = project_memberships.objects.get(
                project_id=project.id,
                member_id=member.id,
                status='1'
            )
        except project_memberships.DoesNotExist:
            return Response({
                'status':'error',
                'message':'This employee is not a member of this project or already removed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        membership.status = '5'
        membership.updated_at = timezone.now()
        membership.save()

        return Response({
            'status':'success',
            'message':'Member removed from the project successfully',
            'data':{
                'project_id': project_id_hash,
                'member_id': member_id_hash
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'status':'error',
            'message':str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def find_project_by_hash(hash_value):
    all_projects = projects.objects.all()
    for project in all_projects:
        if IDhasher.to_md5(project.id) == hash_value:
            return project
    return None

def find_employee_by_hash(hash_value):
    all_employees = employees.objects.all()
    for employee in all_employees:
        if IDhasher.to_md5(employee.id) == hash_value:
            return employee
    return None

@api_view(['POST'])
@require_api_key
def project_members(request):
    try:
        project_id_hash = request.data.get('project_id')

        if not project_id_hash:
            return Response({
                'status':'error',
                'message':'project_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(project_id_hash, str) or len(project_id_hash)!=32:
            return Response({
                'status':'error',
                'message':'project_id must be valid '
            }, status=status.HTTP_400_BAD_REQUEST)
        
        project = None
        all_projects=projects.objects.exclude(status='5')
        for proj in all_projects:
            if IDhasher.to_md5(proj.id) == project_id_hash:
                project = proj
                break

        if not project:
            return Response({
                'status':'error',
                'message':'project not found' 
        }, status=status.HTTP_404_NOT_FOUND)

        memberships = project_memberships.objects.filter(
            project_id=project.id,
            status='1'or '0'                                   
        ).select_related('member_id')

        members_data = []
        for membership in memberships:
            member=membership.member_id
            members_data.append({
                'id':IDhasher.to_md5(member.id),
                'first_name':member.first_name,
                'last_name':member.last_name,
                'email':member.email,
                'is_admin': membership.is_admin,
                'created_at': membership.created_at
            })

        return Response({
            'status':'success',
            'message':'project members retrived successfully',
            'data':members_data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        return Response({
            'status':'error',
            'message':str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@require_api_key
def send_message(request):
    try: 
        serializer = messageserializer(data=request.data)
        if serializer.is_valid():
            project_id = serializer.validated_data['project_id']
            sender_id = serializer.validated_data['sender_id']

            if not project_id or not sender_id:
                return Response({
                    'status':'error',
                    'message':'Both project_id and sender_id are required'
                }, status=status.HTTP_400_BAD_REQUEST)
        
            is_member = project_memberships.objects.filter(
                project_id = project_id,
                member_id = sender_id,
                status='1'
            ).exists()

            if not is_member:
                return Response({
                    'status':'error',
                    'message':'sender is not a member of this project'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            message = messages.objects.create(
                project_id_id = project_id, 
                sender_id_id = sender_id,
                text_body = serializer.validated_data.get('text_body'),
                media_url = serializer.validated_data.get('media_url'),
                status='1' 
            ) 
            response_serializer= messageserializer(message)

            return Response({
                'status':'OK',
                'message':'Message posted successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        else:
            return Response({
                'status':'error',
                'message': 'Invalid data!',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        return Response({
            'status':'error',
            'message':f'Server error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

     
@api_view(['POST'])
@require_api_key
def project_messages(request): 
    try:
        project_id = request.data.get('project_id')
        limit = int(request.data.get('limit', 0))
        page = int(request.data.get('page', 1))    
    
        messages_set = messages.objects.exclude(status='5').select_related('sender_id', 'project_id').order_by('-created_at')
        total_count = messages_set.count()

        if not isinstance(project_id, str) or len(project_id) != 32:
            return Response({
                'status': 'error',
                'message': 'project_id must be valid'
            }, status=status.HTTP_400_BAD_REQUEST)

        project = None
        all_projects = projects.objects.exclude(status='5')
        for proj in all_projects:
            if IDhasher.to_md5(proj.id) == project_id:
                project = proj
                break

        if not project:
                return Response({
                    'status': 'error',
                    'message': 'Project not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        messages_set = messages.objects.filter(
            project_id=project.id,
            status='1'
        ).select_related('sender_id').order_by('-created_at')
        total_count = messages_set.count()

        if limit == 0:
            serializer = messageserializer(messages_set, many=True)
            response_data = {
                'status': 'OK',
                'message': 'Messages retrived successfully',
                'count': total_count,
                'data': serializer.data
            }

            if project_id and project:
                response_data['project']={
                'id': project_id,
                'titel': project.title
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        if limit <= 0 or page <= 0:
            return Response({
                'status':'error',
                'mesage':'limit and page must be positive integers'
            }, status=status.HTTP_400_BAD_REQUEST)


        offset = (page - 1) * limit
        messages_list = messages_set[offset:offset+limit]
        total_pages = (total_count + limit -1) // limit

        serializer = messageserializer(messages_list, many=True)
        response_data = {
            'status': 'OK',
            'message': f'Message page {page} retrived successfully',
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_records': limit,
                'has_next': page < total_pages,
                'has_previous': page > 1                
            },
            'data': serializer.data
        }

        if project_id and project:
                response_data['project']={
                'id': project_id,
                'titel': project.title
            }

        return Response(response_data, status=status.HTTP_200_OK)
                
    # except ValueError:
    #     return Response({
    #         'status': 'error',
    #         'message':'Invalid pagination parameters. limit and page must be integers'
    #     }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'status': 'error',
            'message':f'server error:{str(e)}'
        }, status = status.HTTP_500_INTERNAL_SERVER_ERROR)


    
     
@api_view(['POST'])
@require_api_key
def employee_messages(request): 
    try:
        sender_id = request.data.get('sender_id')
        limit = int(request.data.get('limit', 0))
        page = int(request.data.get('page', 1))    
    
        messages_set = messages.objects.exclude(status='5').select_related('sender_id', 'project_id').order_by('-created_at')
        total_count = messages_set.count()

        if not isinstance(sender_id, str) or len(sender_id) != 32:
            return Response({
                'status': 'error',
                'message': 'sender_id must be valid'
            }, status=status.HTTP_400_BAD_REQUEST)

        employee = None
        all_employees = employees.objects.exclude(status='5')
        for emp in all_employees:
            if IDhasher.to_md5(emp.id) == sender_id:
                sender = emp
                break

        if not sender:
                return Response({
                    'status': 'error',
                    'message': 'Sender not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        messages_set = messages.objects.filter(
            sender_id_id=sender.id, 
            status='1'
        ).select_related('sender_id').order_by('-created_at')
        total_count = messages_set.count()

        if limit == 0:
            serializer = messageserializer(messages_set, many=True)
            response_data = {
                'status': 'OK',
                'message': 'Messages retrived successfully',
                'count': total_count,
                'data': serializer.data
            }

            if sender_id and sender:
                response_data['sender']={
                'id': sender_id,
                'first_name':sender.first_name
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        if limit <= 0 or page <= 0:
            return Response({
                'status':'error',
                'mesage':'limit and page must be positive integers'
            }, status=status.HTTP_400_BAD_REQUEST)


        offset = (page - 1) * limit
        messages_list = messages_set[offset:offset+limit]
        total_pages = (total_count + limit -1) // limit

        serializer = messageserializer(messages_list, many=True)
        response_data = {
            'status': 'OK',
            'message': f'Message page {page} retrived successfully',
            'pagination': {
                'current_page': page,
                'total_pages': total_pages,
                'total_records': limit,
                'has_next': page < total_pages,
                'has_previous': page > 1                
            },
            'data': serializer.data
        }

        if sender_id and sender:
                response_data['sender']={
                'id': sender_id,
                'first_name':sender.first_name
            }
            

        return Response(response_data, status=status.HTTP_200_OK)
                
    # except ValueError:
    #     return Response({
    #         'status': 'error',
    #         'message':'Invalid pagination parameters. limit and page must be integers'
    #     }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'status': 'error',
            'message':f'server error:{str(e)}'
        }, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
