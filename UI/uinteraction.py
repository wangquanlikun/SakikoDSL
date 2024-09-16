class UserInteraction:

    @staticmethod
    async def print(_string, _socket = None):
        mode = "socket server"
        if mode == "command line":
            print(_string)
        elif mode == "socket server" and _socket:
            await _socket.send(_string)
        else:
            pass