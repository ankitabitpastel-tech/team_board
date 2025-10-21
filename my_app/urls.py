from django.urls import path
from . import views

urlpatterns = [
    path('employee/create/', views.employee_create, name='employee_create'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employee/', views.employee_detail, name='employee_detail'),
    path('employee/remove/', views.employee_remove, name='employee_remove'),

    path('project/create/', views.create_project, name='create_project'),
    path('projects/', views.project_list, name='project_list'),

    ]