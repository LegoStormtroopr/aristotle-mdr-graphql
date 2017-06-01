from django.apps import AppConfig

class GraphQLConfig(AppConfig):
    name = 'aristotle_graphql'

    def ready(self):

        from . import converter