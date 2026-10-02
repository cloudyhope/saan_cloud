
from rest_framework import exceptions, generics, serializers

from auth_app.models import Project, Company
from django.contrib.auth.models import User
from warehouse.models import Unit, WareVisitType, WareType, Ware, WarehouseLocation, WarehouseTransaction, TransactionLineType, WarehouseTransactionLine, WarehouseLocationPersonnel
from auth_app.views import ProjectSerializer, CompanySerializer, UserSerializer
from visit.views import VisitSerializer

class WareTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WareType
        fields = '__all__'
    
class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = '__all__'

class WareSerializer(serializers.ModelSerializer):
    type = WareTypeSerializer()
    project = ProjectSerializer()
    unit = UnitSerializer()
    class Meta:
        model = Ware
        fields = '__all__'

class WarehouseLocationSerializer(serializers.ModelSerializer):
    owner = CompanySerializer()
    projects = ProjectSerializer(many=True)
    class Meta:
        model = WarehouseLocation
        fields = '__all__'

class WarehouseTransactionSerializer(serializers.ModelSerializer):
    creator = UserSerializer()
    class Meta:
        model = WarehouseTransaction
        fields = '__all__'

class TransactionLineTypeSerializer(serializers.ModelSerializer):
    # creator = UserSerializer()
    class Meta:
        model = TransactionLineType
        fields = '__all__'

class WarehouseTransactionLineSerializer(serializers.ModelSerializer):
    transaction = WarehouseTransactionSerializer()
    location = WarehouseLocationSerializer()
    user = UserSerializer()
    type = TransactionLineTypeSerializer()
    ware = WareSerializer()
    class Meta:
        model = WarehouseTransactionLine
        fields = '__all__'

# class WareVisitTypeSerializer(serializers.ModelSerializer):
#     ware = WareSerializer()
#     visit_type = VisitSerializer()
#     class Meta:
#         model = WareType
#         fields = '__all__'


###########################
# Only:
###########################


class WareOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Ware
        exclude = ('creation_key', 'creation_hash')
        read_only_fields = ('creation_key', 'creation_hash')

class WarehouseLocationOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseLocation
        fields = '__all__'

class WarehouseTransactionOnlySerializer(serializers.ModelSerializer):
    creator = UserSerializer()
    class Meta:
        model = WarehouseTransaction
        fields = '__all__'

class TransactionLineTypeOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionLineType
        fields = '__all__'

class WarehouseTransactionLineOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseTransactionLine
        fields = '__all__'

class WareVisitTypeOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = WareType
        fields = '__all__'


###########################
# Aggregate:
###########################

class WareAggregatedListSerializer(serializers.ModelSerializer):
    project = ProjectSerializer()
    type = WareTypeSerializer()
    stock_count = serializers.SerializerMethodField()
    import_count = serializers.SerializerMethodField()
    export_count = serializers.SerializerMethodField()
    class Meta:
        model = Ware
        exclude = ('creation_key', 'creation_hash')

    def get_stock_count(self, obj):
        from django.db.models import Q
        val = WarehouseTransactionLine.objects.filter(type__involved=None, ware=obj).aggregate(Sum('amount'))['amount__sum']
        return 0 if val is None else abs(val)
    def get_import_count(self, obj):
        val = WarehouseTransactionLine.objects.filter(type__involved=None, type__side="FROM", ware=obj).aggregate(Sum('amount'))['amount__sum']
        return 0 if val is None else abs(val)
    def get_export_count(self, obj):
        val = WarehouseTransactionLine.objects.filter(type__involved=None, type__side="TO", ware=obj).aggregate(Sum('amount'))['amount__sum']
        return 0 if val is None else abs(val)


from django.db.models import Max, Sum
from django.db.models import Count

class WarehouseAggregatedLocationSerializer(serializers.ModelSerializer):
    owner = CompanySerializer()
    projects = ProjectSerializer(many=True)
    stock_info = serializers.SerializerMethodField()
    class Meta:
        model = WarehouseLocation
        fields = '__all__'

    def get_stock_info(self, obj):
        results = []
        project_id = self.context['request'].query_params.get('p')
        wares = Ware.objects.filter(project_id=project_id, project__in=obj.projects.all())
        for ware in wares:
            val_stock_count = WarehouseTransactionLine.objects.filter(ware=ware, location=obj).aggregate(Sum('amount'))['amount__sum'] or 0
            val_import_count = WarehouseTransactionLine.objects.filter(type__side="TO", ware=ware, location=obj).aggregate(Sum('amount'))['amount__sum'] or 0
            val_export_count = WarehouseTransactionLine.objects.filter(type__side="FROM", ware=ware, location=obj).aggregate(Sum('amount'))['amount__sum'] or 0
            results.append(
                {
                    "ware": WareSerializer(ware, many=False).data,
                    "stock_count": val_stock_count,
                    "import_count": val_import_count,
                    "export_count": abs(val_export_count),
                }
            )
        return results

###########################
# Stock User Serializer:
###########################


from auth_app.models import User
# from auth_app.views import Userser
from django.db.models import Q
        # return User.objects.filter(id__in=self.get_projectified_queryset(WarehouseTransactionLine.objects.filter(~Q(user=None))).values_list('user', flat=True))

class StockUserWareJoinSerializer(serializers.Serializer):
    ware = serializers.SerializerMethodField()
    count = serializers.IntegerField()

    def get_ware(self, dictionary):
        return WareSerializer(Ware.objects.get(id=dictionary['ware']), many=False).data

class StockUserSerializer(UserSerializer):
    stock_count = serializers.SerializerMethodField()
    import_count = serializers.SerializerMethodField() 
    export_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('stock_count', 'import_count', 'export_count')

    def project_lines(self, user):
        return WarehouseTransactionLine.objects.filter(
            type__involved="USER", user=user, ware__is_active=True,
            ware__project_id=self.context['request'].query_params.get('p'))

    def get_stock_count(self, obj):
        return StockUserWareJoinSerializer(self.project_lines(obj).values('ware').annotate(count=Sum('amount')), many=True).data
    def get_import_count(self, obj):
        return StockUserWareJoinSerializer(self.project_lines(obj).filter(type__side="TO").values('ware').annotate(count=Sum('amount')), many=True).data
    def get_export_count(self, obj):
        return StockUserWareJoinSerializer(self.project_lines(obj).filter(type__side="FROM").values('ware').annotate(count=Sum('amount')), many=True).data

#############################
# WareDistributionView
#############################

class WareDistributionBaseSerializer(WareSerializer):
    locations_stock_count = serializers.SerializerMethodField()
    users_stock_count = serializers.SerializerMethodField()
    
    def get_locations_stock_count(self, obj):
        return WarehouseTransactionLine.objects.filter(~Q(location=None), ware=obj).aggregate(Sum('amount'))['amount__sum']
    def get_users_stock_count(self, obj):    
        return WarehouseTransactionLine.objects.filter(~Q(user=None), ware=obj).aggregate(Sum('amount'))['amount__sum']

class UserWareDistributionSerializer(serializers.Serializer):
    user = serializers.SerializerMethodField()
    stock_count = serializers.IntegerField()    
    def get_user(self, dictionary):
        return UserSerializer(User.objects.get(id=dictionary['user']), many=False).data

class WareDistributionByUserSerializer(WareDistributionBaseSerializer):
    # class Meta:
    #     model = Ware
    #     fields = '__all__'

    users = serializers.SerializerMethodField()

    def get_users(self, obj):
        return UserWareDistributionSerializer(WarehouseTransactionLine.objects.filter(~Q(user=None), ware=obj).values('user').annotate(stock_count=Sum('amount')), many=True).data

class LocationDistributionSerializer(serializers.Serializer):
    location = serializers.SerializerMethodField()
    stock_count = serializers.IntegerField()

    def get_location(self, dictionary):
        return WarehouseLocationSerializer(WarehouseLocation.objects.get(id=dictionary['location']), many=False).data


class WareDistributionByLocationSerializer(WareDistributionBaseSerializer):
    # class Meta:
    #     model = Ware
    #     fields = '__all__'

    locations = serializers.SerializerMethodField()

    def get_locations(self, obj):
        return LocationDistributionSerializer(WarehouseTransactionLine.objects.filter(~Q(location=None), ware=obj).values('location').annotate(stock_count=Sum('amount')), many=True).data


##############################
# Create Ez Ware Transaction:
##############################

class WareTransactionLineEzCreateSerializer(serializers.ModelSerializer):
    side = serializers.CharField()
    involved = serializers.CharField()
    class Meta:
        model = WarehouseTransactionLine
        fields = ('ware', 'amount', 'location', 'user', 'side', 'involved',)

class WareTransactionEzCreateSerializer(serializers.ModelSerializer):
    lines = WareTransactionLineEzCreateSerializer(many=True)
    class Meta:
        model = WarehouseTransaction
        fields = '__all__'
    


##############################
# Ware VisitType Connection:
##############################

from visit.views import VisitTypeNestedSerializer, VisitSerializer
class WareVisitTypeSerializer(serializers.ModelSerializer):
    ware = WareSerializer()
    visit_type = VisitTypeNestedSerializer()
    visit = VisitSerializer()

    class Meta:
        model = WareVisitType
        fields = '__all__'

class WareVisitTypeOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = WareVisitType
        fields = '__all__'

class WareVisitTypeOnlyListSerializer(serializers.ListSerializer):
    child = WareVisitTypeOnlySerializer()


##############################
# Ware VisitType Connection:
# WareVisitSettings:
##########################

class WareVisitSettingsSerializer(serializers.Serializer):
    has_wares = serializers.BooleanField()
    total_count = serializers.IntegerField()

class WarehouseLocationPersonnelSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseLocationPersonnel
        fields = '__all__'

class WarehouseLocationPersonnelNestedSerializer(serializers.ModelSerializer):
    location = WarehouseLocation
    class Meta:
        model = WarehouseLocationPersonnel
        fields = '__all__'

