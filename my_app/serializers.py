from rest_framework import serializers
from .models import employees, projects, project_memberships, messages
from .utils.id_hasher import IDhasher

class employeesserializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    class Meta:
        model = employees
        fields = '__all__'
        # ['id', 'first_name', 'last_name', 'user_name', 'email', ]
        # exclude = ['password']
        read_only_fields = ('id', 'created_at', 'updated_at')
        # extra_kwargs ={
        #     'password' : {'write_only': True}
        # }
    
    def validate(self, attrs):
        employee_instance = employees(**attrs)
        try:
            employee_instance.clean()
        except ValueError as e:
            raise serializers.ValidationError(e)
        return attrs
    
    def get_id(self, obj):
        return IDhasher.to_md5(obj.id)
    
    def create(self, validated_data):
        return super().create(validated_data)

        # def clean_email():
class projectcreateserializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    created_by = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        validation_attrs = attrs.copy()
        validation_attrs.pop('created_by', None)
        instance = projects(**validation_attrs)
        try: 
            instance.clean()
        except ValueError as e:
            raise serializers.ValidationError(e.message_dict)
        return attrs

    class Meta:
        model = projects
        fields = '__all__'
        
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_created_by(self, value):
        try: 
            return int(value)
        except ValueError:
            pass
        
        if isinstance(value, str) and len(value) == 32:
            all_employees = employees.objects.exclude(status='5')
            for emp in all_employees:
                if IDhasher.to_md5(emp.id) == value:
                    return emp.id
        raise serializers.ValidationError("Invalid employee ID or hash")
    
    def get_id(self, obj):
        return IDhasher.to_md5(obj.id)

    def create(self, validated_data):
        created_by_id = validated_data.pop('created_by')
        project = projects.objects.create(**validated_data)

        project_memberships.objects.create(
            project_id=project, 
            member_id_id=created_by_id,  
            is_admin=True,
            status='1'
        )

        return project
    
class projectresponseserializer(serializers.ModelSerializer):
    system_creation_time = serializers.DateTimeField(source='created_at', read_only=True)
    id = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = projects
        # fields = '__all__'
        exclude = ['members']

    def get_id(self, obj):
        return IDhasher.to_md5(obj.id)
    
    def get_created_by(self, obj):
        membership = project_memberships.objects.filter(
            project_id=obj, 
            is_admin=True
        ).first()
        if membership:
            return IDhasher.to_md5(membership.member_id.id)
        return None


class projectmembershipserializer(serializers.ModelSerializer):
    project_id = serializers.CharField(write_only=True)
    member_id = serializers.CharField(write_only=True)

    id = serializers.SerializerMethodField(read_only = True)
    project_id_hash= serializers.SerializerMethodField(read_only=True)
    member_id_hash= serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = project_memberships
        fields = '__all__'
        # fields = ['id', 'project_id', 'member_id', 'project_id_input', 'member_id_input', 'is_admin', 'created_at', 'updated_at', 'status']

        read_only_fields = ['id', 'created_at', 'status']

    def validate_project_id(self, value):
        if isinstance(value, str) and len(value) == 32:
            all_projects = projects.objects.exclude(status='5')
            for proj in all_projects:
                if IDhasher.to_md5(proj.id) == value:
                    return proj.id
        raise serializers.ValidationError("Invalid project ID")

    def validate_member_id(self, value):
        if isinstance(value, str) and len(value) == 32:
            all_employees = employees.objects.exclude(status='5')
            for emp in all_employees:
                if IDhasher.to_md5(emp.id) == value:
                    return emp.id
        
        raise serializers.ValidationError("Invalid employee ID")

    def get_id(self, obj):
        return IDhasher.to_md5(obj.id)
    
    def get_project_id_hash(self, obj):
        return IDhasher.to_md5(obj.project_id.id)
    
    def get_member_id_hash(self, obj):
        return IDhasher.to_md5(obj.member_id.id)
    
    def create(self, validated_data):
        return super().create(validated_data)
    
class messageserializer(serializers.ModelSerializer):
    project_id = serializers.CharField(write_only=True)
    sender_id = serializers.CharField(write_only=True)

    id = serializers.SerializerMethodField(read_only=True)
    project_id_ = serializers.SerializerMethodField(read_only=True)
    sender_id_ = serializers.SerializerMethodField(read_only=True)

    class Meta: 
        model = messages
        # fields = ['project_id', 'sender_id', 'text_body', 'media_url']
        fields = '__all__'
        read_only_fields = ('id', 'project_id_', 'sender_id_', 'has_media', 'created_at', 'updated_at', 'status')

    def validate_project_id(self, value):

        if isinstance(value, str) and len(value) == 32:
            all_projects = projects.objects.exclude(status='5')
            for proj in all_projects:
                if IDhasher.to_md5(proj.id)==value:
                    return proj.id
        
        raise serializers.ValidationError("Invalid project ID")
    
    def validate_sender_id(self, value):
        if isinstance(value, str) and len(value) == 32:
            all_employees = employees.objects.exclude(status='5')
            for emp in all_employees:
                if IDhasher.to_md5(emp.id)==value:
                    return emp.id
        
        raise serializers.ValidationError("Invalid employee ID ")
    
    def get_id(self, obj):
        return IDhasher.to_md5(obj.id)
    
    def get_project_id_(self, obj):
        return IDhasher.to_md5(obj.project_id.id)
    
    def get_sender_id_(self, obj):
        return IDhasher.to_md5(obj.sender_id.id)
    
    # def get_sender(self, obj):
    #     return{
    #         'id': IDhasher.to_md5(obj.sender_id.id),
    #         'first_name': obj.sender_id.first_name,
    #         'last_name':obj.sender_id.last_name
    #     }

    # def get_project(self, obj):
    #     return{
    #         'id': IDhasher.to_md5(obj.project_id.id),
    #         'titel': obj.project_id.tite'
    #         'first_name': obj.sender_id.first_name,
    #         'last_name':obj.sender_id.last_name
    #     }