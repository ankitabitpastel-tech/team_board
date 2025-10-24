from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import re, os
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

class employees(models.Model):

    id = models.AutoField(primary_key=True)
    first_name = models.TextField(null=False, blank=False) 
    last_name = models.TextField(null=True, blank=True)
    user_name = models.TextField(null=True, blank=True)
    # email = models.EmailField(validators=[clean_email],max_length=255, null=False, blank=False )
    email = models.CharField(null=False, blank=False, max_length=255,)
    password = models.TextField(null=False, blank=False)
    phone_number = models.TextField(null=False, blank=False, max_length=20)
    address = models.TextField(null=False, blank=False) 
    profile_image_url = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    updated_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=1,
        choices=[('0', 'inactive'), ('1', 'active'), ('5', 'deleted')], 
        default='1', null=False,
        blank=False
    )

    class Meta:
        db_table = 'employees'
        
    def clean(self):
        # pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        # if not re.match(pattern, self.email):
        #     raise ValidationError("Enter a valid mail address!") 

        try:
            validate_email(self.email)
        except ValidationError:
            raise ValidationError("Enter a valid email address!")


        if employees.objects.filter(
            email=self.email,
            status__in=['0', '1']).exclude(id= self.id).exists():
            raise ValidationError({'email':'An employee with this email already exists.'})

    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        print(f"Password hashed: {self.password}")
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.set_password(self.password)
            print(f"After hashing :{self.password}")
        super().save(*args, **kwargs)
        

class projects(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.TextField(null=False, blank=False) #unique=True
    description = models.TextField(null=True, blank=True)
    banner_image_url=models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    updated_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=1,
        choices=[('0', 'inactive'), ('1', 'active'), ('5', 'deleted')], 
        default='1', null=False,
        blank=False
    )
    members = models.ManyToManyField('employees', through='project_memberships', through_fields=('project_id', 'member_id'))

    class Meta:
        db_table = 'projects'

    def clean(self):
        if projects.objects.filter(
            title__iexact=self.title,  
            status__in=['0', '1']   
        ).exclude(id=self.id).exists():
            raise ValidationError({'title': 'A project with this title already exists.'})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
        

class project_memberships(models.Model):
    id = models.AutoField(primary_key=True)
    project_id = models.ForeignKey('projects', on_delete=models.CASCADE, null=False, db_column='project_id')
    member_id = models.ForeignKey('employees', on_delete=models.CASCADE, null=False, blank=False, db_column='member_id')
    is_admin = models.BooleanField(default=False, null=False, blank=False) 
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    updated_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=1,
        choices=[('0', 'inactive'), ('1', 'active'), ('5', 'deleted')], 
        default='1', null=False,
        blank=False
    )

    class Meta:
        db_table = 'project_memberships'
        unique_together = ['project_id', 'member_id']