class Flowgraph():
    """
    Specify configuration parameters of a SatNOGS flowgraph

    :param script_name: The executable script name of the flowgraph
    :type script_name: str
    :param has_baudrate: Indicates if the flowgraph supports a baudrate option
    :type has_baudrate: bool, optional
    :param has_framing: Indicates if the flowgraph supports a framing option
    :type has_framing: bool, optional
    :param framing: A gr-satnogs compatible string specifying the framing to use
    :type framing: str, optional
    """
    def __init__(self, script_name, has_baudrate=False, has_framing=False, framing="ax25"):
        self._script_name = script_name
        self._has_baudrate = has_baudrate
        self._has_framing = has_framing
        self._framing = framing

    def script_name(self):
        return self._script_name

    def has_baudrate(self):
        return self._has_baudrate

    def has_framing(self):
        return self._has_framing

    def framing(self):
        if not self._has_framing:
            print('Flowgraph does not support any framing scheme')
            raise ValueError()
        return self._framing
