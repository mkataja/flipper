import glob
import os


def should_be_imported(file):
    if not os.path.isfile(file):
        return False
    if os.path.basename(file)[:-3] in ['__init__', 'command', 'commandlist']:
        return False
    return True


modules = glob.glob(os.path.dirname(__file__) + "/*.py")
__all__ = [os.path.basename(f)[:-3] for f in modules if should_be_imported(f)]
