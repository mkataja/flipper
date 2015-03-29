import datetime
import logging

import irc


def patch_irclib():
    """
    Patch the irc library to fix various bugs
    """
    logging.info("Patching irc library...")
    patch_client_reactor_sockets()
    patch_schedule_delayedcommand_now()
    
def patch_client_reactor_sockets():
    """
    Fix the situation where it tries to use a closed socket and crashes
    """
    logging.info("  Patching client.Reactor.sockets()")
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

def patch_schedule_delayedcommand_now():
    """
    Have delayed commands use UTC to avoid DST problems
    """
    logging.info("  Patching schedule.DelayedCommand.now()")
    @classmethod
    def now_new(cls, tzinfo=None):
        # Ignoring tzinfo because of UTC
        return datetime.datetime.utcnow()
    irc.schedule.DelayedCommand.now = now_new 
