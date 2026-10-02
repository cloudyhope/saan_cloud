from django_filters import rest_framework as filters
from django.db import models
from collections import defaultdict

class SmartAutoFilterMixin:
    """
    Smart filtering mixin that automatically sets filterset_fields with:
    - Appropriate lookups based on field type
    - Exclusion of unsupported fields (file fields, etc.)
    - Relation filtering with max depth 4
    - Intelligent field type detection
    """
    
    @property
    def filterset_fields(self):
        """
        Return filterable fields with appropriate lookups for the model
        """
        model = self.get_queryset().model
        filterable_fields = {}
        
        # Get direct fields
        self._add_model_fields(model, filterable_fields)
        
        # Get relation fields up to depth 4
        self._add_relation_fields(model, filterable_fields, max_depth=4)
        print(filterable_fields)
        return filterable_fields
    
    def _add_model_fields(self, model, filterable_fields, prefix=''):
        """Add direct model fields to filterable_fields"""
        for field in model._meta.get_fields():
            if self._is_filterable_field(field):
                field_name = f"{prefix}{field.name}" if prefix else field.name
                filterable_fields[field_name] = self._get_field_lookups(field)
    
    def _add_relation_fields(self, model, filterable_fields, max_depth=4, current_depth=0, prefix='', visited_models=None):
        """Add relation fields recursively up to max_depth"""
        if visited_models is None:
            visited_models = set()
        
        if current_depth >= max_depth:
            return
        
        # Avoid circular references
        if model in visited_models:
            return
        
        visited_models.add(model)
        
        for field in model._meta.get_fields():
            if self._is_filterable_relation(field):
                related_model = field.related_model
                field_name = f"{prefix}{field.name}" if prefix else field.name
                
                # Add the relation field itself (for exact lookups)
                filterable_fields[field_name] = ['exact', 'isnull']
                
                # Add related model fields
                new_prefix = f"{field_name}__"
                self._add_model_fields(related_model, filterable_fields, new_prefix)
                
                # Recursively add nested relations
                self._add_relation_fields(
                    related_model, 
                    filterable_fields, 
                    max_depth, 
                    current_depth + 1, 
                    new_prefix, 
                    visited_models.copy()
                )
    
    def _is_filterable_field(self, field):
        """Check if field should be included in filtering"""
        excluded_types = (
            models.FileField,
            models.ImageField,
            models.BinaryField,
            models.JSONField,
            # Add more excluded types as needed
        )
        
        # Exclude file fields and unsupported types
        if isinstance(field, excluded_types):
            return False
        
        # Exclude reverse relations (one_to_many, many_to_many)
        if field.is_relation and (field.one_to_many or field.many_to_many):
            return False
        
        # Only include fields that have an attname (direct fields)
        if field.is_relation:
            return field.many_to_one or field.one_to_one
        
        return hasattr(field, 'attname')
    
    def _is_filterable_relation(self, field):
        """Check if relation field should be included"""
        # Only include forward relations (many_to_one, one_to_one)
        if not field.is_relation:
            return False
        
        if field.many_to_one or field.one_to_one:
            return True
        
        return False
    
    def _get_field_lookups(self, field):
        """Get appropriate lookups based on field type"""
        if isinstance(field, models.CharField):
            return ['exact', 'icontains', 'istartswith', 'iendswith', 'isnull']
        
        elif isinstance(field, models.TextField):
            return ['exact', 'icontains', 'isnull']
        
        elif isinstance(field, (models.DateTimeField, models.DateField)):
            return ['exact', 'gte', 'lte', 'gt', 'lt', 'year', 'month', 'day', 'isnull'] #'date', 
        
        elif isinstance(field, models.TimeField):
            return ['exact', 'gte', 'lte', 'gt', 'lt', 'hour', 'minute', 'isnull']
        
        elif isinstance(field, models.BooleanField):
            return ['exact']
        
        elif isinstance(field, (models.IntegerField, models.BigIntegerField, models.SmallIntegerField)):
            return ['exact', 'gte', 'lte', 'gt', 'lt', 'in', 'isnull']
        
        elif isinstance(field, (models.FloatField, models.DecimalField)):
            return ['exact', 'gte', 'lte', 'gt', 'lt', 'isnull']
        
        elif isinstance(field, models.EmailField):
            return ['exact', 'icontains', 'istartswith', 'iendswith', 'isnull']
        
        elif isinstance(field, models.URLField):
            return ['exact', 'icontains', 'istartswith', 'isnull']
        
        elif isinstance(field, models.SlugField):
            return ['exact', 'icontains', 'istartswith', 'isnull']
        
        elif isinstance(field, models.UUIDField):
            return ['exact', 'isnull']
        
        elif field.is_relation and (field.many_to_one or field.one_to_one):
            return ['exact', 'isnull']
        
        else:
            # Default lookups for unknown field types
            return ['exact', 'isnull']


# Advanced version with customizable options
class ConfigurableAutoFilterMixin(SmartAutoFilterMixin):
    """
    Extended version with customizable options
    """
    
    # Override these in your view class to customize behavior
    filter_max_depth = 4
    filter_excluded_field_types = (
        models.FileField,
        models.ImageField,
        models.BinaryField,
        models.JSONField,
    )
    filter_excluded_field_names = []  # List of field names to exclude
    filter_include_text_search = True  # Whether to include text field searching
    
    def get_filterset_fields(self):
        """Override to use configurable options"""
        model = self.get_queryset().model
        filterable_fields = {}
        
        # Get direct fields
        self._add_model_fields(model, filterable_fields)
        
        # Get relation fields with configurable depth
        self._add_relation_fields(model, filterable_fields, max_depth=self.filter_max_depth)
        
        return filterable_fields
    
    def _is_filterable_field(self, field):
        """Override to use configurable exclusions"""
        # Check excluded types
        if isinstance(field, self.filter_excluded_field_types):
            return False
        
        # Check excluded field names
        if field.name in self.filter_excluded_field_names:
            return False
        
        # Check text fields if not included
        if not self.filter_include_text_search and isinstance(field, models.TextField):
            return False
        
        return super()._is_filterable_field(field)



# USAGE:

# class OrderListCreateAPIView(ConfigurableAutoFilterMixin, generics.ListCreateAPIView):
#     queryset = Order.objects.all()
#     serializer_class = OrderSerializer
#     filter_backends = [filters.DjangoFilterBackend]
    
#     # Customize the filtering behavior
#     filter_max_depth = 3  # Only go 3 levels deep in relations
#     filter_excluded_field_names = ['internal_notes', 'debug_info']
#     filter_include_text_search = False  # Exclude text field searching