class AmoException(Exception):
    def __init__(self, message, response):
        # Call the base class constructor with the parameters it needs
        super(AmoException, self).__init__(message)
        self.message = message
        self.response = response