class AmoException(Exception):
    message = 'GOT Exception Message '
    context = {}
    def __init__(self, message, context):
        # Call the base class constructor with the parameters it needs
        super(AmoException, self).__init__(message)
        self.message = message
        self.context = context