import inspect

from graphene import Field, Dynamic

from aristotle_mdr.models import _concept
from aristotle_mdr.fields import ConceptManyToOneRel, ConceptForeignKey, ConceptManyToManyField, ConceptManyToManyRel
from .fields import ConceptListField

from graphene_django.converter import convert_django_field, convert_django_field_with_choices
from graphene_django.utils import get_related_model
from graphene_django.fields import get_connection_field

from graphene.relay import is_node
from django.core.exceptions import PermissionDenied

import re
first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')
def convert(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def concept_resolver(root, args, context, info):
    obj = getattr(root, info.field_name, None) or getattr(root, convert(info.field_name), None)
    if obj:
        if not obj.can_view(context.user):
            if issubclass(type(root), _concept):
                msg = '{field} on {obj} [{obj_name}][uuid:{uuid}] is not visible for the current user'.format(
                    field=info.field_name,
                    obj=type(root).__name__,
                    obj_name=root.name,
                    uuid=root.uuid
                )
            else:
                msg = '{field} on {obj} [{obj_repr}] is not visible for the current user'.format(
                    field=info.field_name,
                    obj=type(root).__name__,
                    obj_repr=str(root),
                )
            raise Exception(msg)
    return obj


@convert_django_field.register(ConceptManyToManyField)
@convert_django_field.register(ConceptManyToManyRel)
@convert_django_field.register(ConceptManyToOneRel)
def convert_field_to_list_or_connection(field, registry=None):
    model = get_related_model(field)

    def dynamic_type():
        _type = registry.get_type_for_model(model)
        if not _type:
            return

        if is_node(_type):
            return get_connection_field(_type)

        return ConceptListField(_type)

    return Dynamic(dynamic_type)


@convert_django_field.register(ConceptForeignKey)
def convert_field_to_djangomodel(field, registry=None):
    model = get_related_model(field)
    def dynamic_type():
        _type = registry.get_type_for_model(model)
        if not _type:
            return

        return Field(_type, resolver=concept_resolver, description=field.help_text, required=not field.null)

    return Dynamic(dynamic_type)
