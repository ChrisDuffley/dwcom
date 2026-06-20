import sys

# Remove this package entry so the import below re-executes dwcom.py fresh on each reload.
if __name__ in sys.modules:
    del sys.modules[__name__]

from dwcom import Trigger
