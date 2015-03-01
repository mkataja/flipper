import logging

import irc


def patch_irclib():
    """
    Patch the irc library to fix the situation where it tries to use a closed 
    socket and crashes.
    """
    logging.debug("Patching irc library...")
    
    sockets_orig = irc.client.Reactor.sockets
    @property
    def sockets_new(self):
        with self.mutex:
            return [
                    socket 
                    for socket in sockets_orig.fget(self) 
                    if socket.fileno() >= 0
            ]
    irc.client.Reactor.sockets = sockets_new
