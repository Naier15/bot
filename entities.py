from dependency_injector import containers, providers


class App:
    def __init__(self, title: str):
        self.title = str(title)

    def __repr__(self):
        return '{0}(title={1})'.format(self.__class__.__name__, repr(self.title))
    

class Context(containers.DeclarativeContainer):
    config = providers.Configuration()
    config.from_yaml('config.yml')
    app = providers.Factory(App, 'Bashni bot')


def main():
    context = Context()
    app = context.app()
    config = context.config()


if __name__ == '__main__':
    main()