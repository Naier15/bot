from dependency_injector import containers, providers, schema


class App:

    def __init__(self, title: str):
        self.title = str(title)

    def __repr__(self):
        return '{0}(title={1})'.format(self.__class__.__name__, repr(self.title))
    

class Context(containers.DeclarativeContainer):
    config = providers.Configuration()
    config.from_yaml('config.yml')
    app = providers.Factory(App, 'Bashni bot')
    app2 = providers.Singleton(App, 'Bot 2')
    schema = schema.ContainerSchema(one=1, two=2)


def main():
    context = Context()
    app = context.app()
    config = context.config()
    app2 = context.app2()
    schem = context.schema.dict()
    print(schem)


if __name__ == '__main__':
    main()