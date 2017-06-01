from django.apps import apps
from django.contrib.auth import models as auth

import graphene

from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from aristotle_mdr import models as mdr
from aristotle_dse import models as dse
from aristotle_mdr.contrib.identifiers import models as identifiers
from aristotle_mdr.contrib.links import models as links
from aristotle_mdr.contrib.slots import models as slots

from .filters import MetadataFilter


class baseMetadataTypeMixin(DjangoObjectType):
    class Meta:
        model = mdr._concept

    @classmethod
    def get_node(cls, id, context, info):
        # This doesn't actually get called ?
        try:
            return cls._meta.model.objects.filter(id=id).visible(context.user)
        except cls._meta.model.DoesNotExist:
            return None


class ConceptType(baseMetadataTypeMixin):
    """
    Use this to get metadata
    """
    class Meta:
        model = mdr._concept
        interfaces = (graphene.relay.Node, )



class StatusType(DjangoObjectType):
    class Meta:
        model = mdr.Status
    
class OrganizationType(DjangoObjectType):
    class Meta:
        model = mdr.Organization

class RegistrationAuthorityType(OrganizationType):
    class Meta:
        model = mdr.RegistrationAuthority


def issubclass_strict(cls, base):
    return cls and issubclass(cls, base) and cls is not base


def makeTypes():
    from django.contrib.contenttypes.models import ContentType
    
    for ct in ContentType.objects.all():
        klass = ct.model_class()
        if issubclass_strict(klass, mdr._concept):
            exec(
                "\n".join([
                    "class {app}_{model}Type(DjangoObjectType):",
                    "    __doc__ = apps.get_model('{app}','{model}').__doc__.replace('    ','') ",
                    "    class Meta:",
                    "        model = apps.get_model('{app}','{model}')",
                    "    @classmethod",
                    "    def get_node(*args, **kwargs): 1/0"
                ]).format(app=ct.app_label,model=ct.model,)
            )

        if issubclass_strict(klass, mdr.AbstractValue):
            exec(
                "\n".join([
                    "class {app}_{model}Type(DjangoObjectType):",
                    "    __doc__ = apps.get_model('{app}','{model}').__doc__.replace('    ','') ",
                    "    class Meta:",
                    "        model = apps.get_model('{app}','{model}')",
                ]).format(app=ct.app_label,model=ct.model,)
            )

    class LinkEndType(DjangoObjectType):
        class Meta:
            model = links.LinkEnd

    class LinkType(DjangoObjectType):
        class Meta:
            model = links.Link

    class RelationRoleType(DjangoObjectType):
        class Meta:
            model = links.RelationRole


    class SlotType(DjangoObjectType):
        class Meta:
            model = slots.Slot


    class IdentifierType(DjangoObjectType):
        class Meta:
            model = identifiers.ScopedIdentifier

    class NamespaceType(DjangoObjectType):
        class Meta:
            model = identifiers.Namespace


    class DSSDEInclusionType(DjangoObjectType):
        class Meta:
            model = dse.DSSDEInclusion

makeTypes()

class Query(graphene.AbstractType):
    """
    """
    all_metadata = DjangoFilterConnectionField(ConceptType, filterset_class=MetadataFilter)
    all_registrationauthorities = graphene.List(RegistrationAuthorityType)

    def resolve_all_metadata(self, args, context, info):
        return mdr._concept.objects.all().visible(context.user)

    def resolve_all_registrationauthorities(self, args, context, info):
        # We can easily optimize query count in the resolve method
        return mdr.RegistrationAuthority.objects.all().visible(context.user)

class AristotleQuery(Query, graphene.ObjectType):
    """My Cool GraphQL Endpoint"""
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass


schema = graphene.Schema(query=AristotleQuery)
