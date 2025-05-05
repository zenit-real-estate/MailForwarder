class MissingAgentException(Exception):
    """Raised when the agent information is missing."""
    def __init__(self, message="Agent information is missing"):
        self.message = message
        super().__init__(self.message)

class MissingOwnerException(Exception):
    """Raised when the owner information is missing."""
    def __init__(self, message="Owner information is missing"):
        self.message = message
        super().__init__(self.message)

class MissingPriceException(Exception):
    """Raised when the price information is missing."""
    def __init__(self, message="Price information is missing"):
        self.message = message
        super().__init__(self.message)

class MissingLocalityException(Exception):
    """Raised when the locality information is missing."""
    def __init__(self, message="Locality information is missing"):
        self.message = message
        super().__init__(self.message)

class MissingTypeException(Exception):
    """Raised when the type (for rent/sale) information is missing."""
    def __init__(self, message="Type information is missing"):
        self.message = message
        super().__init__(self.message)