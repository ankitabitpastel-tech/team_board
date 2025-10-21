from rest_framework import serializers
from .models import employees, projects, project_memberships

class employeesserializer(serializers.ModelSerializer):
    class Meta:
        model = employees
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
        extra_kwargs ={
            'password' : {'write_only': True}
        }

        # def clean_email():
class projectcreateserializer(serializers.ModelSerializer):
    created_by = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = projects
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

    def create(self, validated_data):
        created_by_id = validated_data.pop('created_by')
        # project = projects.objects.create(**validated_data)

        project = projects.objects.create(
            title=validated_data['title'],
            description=validated_data['description'],
            banner_image_url=validated_data.get('banner_image_url')
        )
        project_memberships.objects.create(
            project_id=project, 
            member_id_id=created_by_id,  
            is_admin=True,
            status='1'
        )

        return project
    
class projectresponseserializer(serializers.ModelSerializer):
    system_creation_time = serializers.DateTimeField(source='created_at', read_only=True)
    
    class Meta:
        model = projects
        fields = '__all__'


class projectmembershipserializer(serializers.ModelSerializer):
    # project = projectserializer(source='project_id', read_only=True)
    # member = employeesserializer(source='employee_id', read_only=True)

    project_id = serializers.PrimaryKeyRelatedField(
        queryset=projects.objects.all(), 
        write_only=True
    )
    member_id = serializers.PrimaryKeyRelatedField(
        queryset=employees.objects.all(), 
        write_only=True
    )

    class Meta:
        model = project_memberships
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

