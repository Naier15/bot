from dependency_injector import containers, providers


class Movie:
    def __init__(self, title: str):
        self.title = str(title)

    def __repr__(self):
        return '{0}(title={1})'.format(self.__class__.__name__, repr(self.title))
    

class ApplicationContainer(containers.DeclarativeContainer):
    movie = providers.Factory(Movie)
    config = providers.Configuration()

    # print(config.finder.csv.path, config.finder.csv.delimiter)


def main():
    container = ApplicationContainer()
    container.config.from_yaml('config.yml')
    config = container.config()
    print(config.)

    
    
    movie = Movie('Hello')
    print(movie)


if __name__ == '__main__':
    main()