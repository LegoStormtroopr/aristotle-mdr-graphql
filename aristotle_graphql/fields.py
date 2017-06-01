from functools import partial

from graphene import Field, Dynamic
from graphene_django.fields import get_connection_field, DjangoListField
from graphene_django.utils import maybe_queryset

class ConceptListField(DjangoListField):

    @property
    def model(self):
        return self.type.of_type._meta.node._meta.model

    @staticmethod
    def list_resolver(resolver, root, args, context, info):
        qs = maybe_queryset(resolver(root, args, context, info))
        if hasattr(qs, 'visible'):
            return qs.visible(context.user)
        return qs

    def get_resolver(self, parent_resolver):
        return partial(self.list_resolver, parent_resolver)
