from intergov.monitoring import increase_counter


class BaseUseCase:
    """
    Base objects for logging and monitoring mostly;
    probably won't have any business logic bearing, just the code structure
    """

    def execute(self, *args, **kwargs):
        increase_counter(f"usecase.{self.__class__.__name__}.execute_called", 1)
