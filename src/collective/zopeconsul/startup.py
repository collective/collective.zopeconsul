from consulserver import Consul, set_keyvalues
from vhm import set_vhm


def notifyStartup(event):
    consul = Consul()

    # Set any configuration keys
    set_keyvalues(event, consul)

    # Update the VHM config
    set_vhm(event, consul)
