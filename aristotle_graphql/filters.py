from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist, PermissionDenied

import django_filters

from aristotle_mdr import models as MDR



class MetadataFilter(django_filters.FilterSet):
    superseded_by = django_filters.UUIDFilter(
        name='superseded_by__uuid',
        label="Superseded by"
    )
    identifier = django_filters.CharFilter(
        label="Identifier",
        method='identifier_filter',
        help_text = (
            'Used to filter concept based on the requested identifier. '
            'Identifiers must be of the type `identifier`, `namespace::identifier` '
            'or `namespace::identifier::version.` '
            'Multiple metadata items may be returned if items have the same identifier '
            'but different versions or namespaces.'
        )
    )
    type = django_filters.CharFilter(
        method='concept_type_filter',
        label='Filter by metadata type',
        help_text = (
            'An `app_label:concept_type` pair that filters results to '
            'only return concepts of the specified type.\n\n'
            'A list of models can be accessed at `/api/types/`, filterable '
            'models are limited to the values of the `model` on each item returned '
            'from the list.'

        )
    )
    modified = django_filters.DateFromToRangeFilter(
        # lookup_expr=['exact', 'gte', 'lte'],
        help_text = (
            'An `app_label:concept_type` pair that filters results to '
            'only return concepts of the specified type.\n\n'
            'A list of models can be accessed at `/api/types/`, filterable '
            'models are limited to the values of the `model` on each item returned '
            'from the list.'

        )
    )
    dq = django_filters.CharFilter(
        label="Django QuerySet Field",
        method='queryset_filter',
        help_text = (
            'Used to filter based on Django Querysets'
        )
    )

    class Meta:
        model = MDR._concept
        fields = {
            'name': ['icontains',],
            # 'modified': ['exact', 'gte', 'lte'],
            'created': ['exact', 'gte', 'lte'],
            'uuid': ['exact'],
            'type': ['exact']
        }
        strict = django_filters.STRICTNESS.RAISE_VALIDATION_ERROR

    def identifier_filter(self, queryset, name, value):
        # construct the full lookup expression.
        args = value.split('::')
        if len(args) == 1:
            kwargs = {'identifiers__identifier': args[0]}
        if len(args) == 2:
            kwargs = {'identifiers__identifier': args[0]}
        elif len(args) == 3:
            kwargs = dict([
                ('identifiers__%s'%k, v)
                for k, v in 
                zip(
                    ['namespace__shorthand_prefix', 'identifier', 'version'],
                    args
                )
                if v
            ])

        return queryset.filter(**kwargs)

    def queryset_filter(self, queryset, name, value):
        # construct the full lookup expression.
        f,v = value.split(':', 1)
        
        if self.has_forbidden_join(queryset.model()._meta.model, f):
            raise PermissionDenied(detail="Joining on that field is not allowed")
        
        
        try:
            queryset = queryset.filter(**{f:v})
        except:
            raise PermissionDenied(
                detail="This field [{j}] makes no sense".format(
                    j=f
                )
            )

        return queryset

    def has_forbidden_join(self, model, join):
        disallowed_models = [
            'User','Permission', 'Group',  # django.contrib.auth
            'Revision', 'Version', # django_reversion
            "PossumProfile","Discussion","Workgroup", #  aristotle_mdr
            'Notification', 
        ]
        checking_model = model
        forbidden = False
        joins = join.split('__')
        for i, relation in enumerate(joins):
            if checking_model:
                try:
                    attr = checking_model._meta.get_field(relation)
                    if attr.related_model:
                        if attr.related_model._meta.model_name.lower() in [w.lower() for w in disallowed_models]:
                            # Despite the join/field being named differently, this column is forbidden!
                            return True
                    checking_model = attr.related_model
                except FieldDoesNotExist:
                    pass
        return forbidden

    def concept_type_filter(self, queryset, name, value):
        ct = value.lower().split(":",1)
        if len(ct) == 2:
            app,model = ct
            concept_type = ContentType.objects.get(app_label=app,model=model).model_class()
        else:
            model = value
            concept_type = ContentType.objects.get(model=model).model_class()

        return queryset.filter(**{"%s__isnull"%model:False})
