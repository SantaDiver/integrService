class AmoException(Exception):
    message = 'GOT Exception Message '
    context = {}
    resend = False
    def __init__(self, message, context, resend=False):
        # Call the base class constructor with the parameters it needs
        super(AmoException, self).__init__(message)
        self.message = message
        self.context = context
        self.resend = resend