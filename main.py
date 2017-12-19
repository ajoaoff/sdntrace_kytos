"""Main module of amlight/sdntrace Kytos Network Application.

An OpenFlow Path Trace
"""

from kytos.core import KytosNApp, log, rest
from kytos.core.helpers import listen_to
from pyof.foundation.network_types import Ethernet
from flask import request
from napps.amlight.sdntrace import settings
from napps.amlight.sdntrace.shared.switches import Switches
from napps.amlight.sdntrace.tracing.trace_manager import TraceManager



class Main(KytosNApp):
    """Main class of amlight/sdntrace NApp.

    This application allows users to trace a path directly from the data
    plane. Originally written for Ryu (github.com/amlight/sdntrace), this app
    is being ported to Kytos.
    Steps:
        1 - User requests a trace using a specific flow characteristic,
            for example VLAN = 1000 Dest TCP Port = 25
        2 - REST module inserts trace request in a queue provided by the
            TraceManager
        3 - The TraceManager runs the Tracer, basically sending PacketOuts
            and waiting for PacketIn till reaching a timeout
        4 - After Timeout, result is provided back to REST that provides it
            back to user
    Dependencies:
        * - of_topology will discovery will the topology
        * - sdntrace_coloring will color all switches

    At this moment, only OpenFlow 1.0 is supported.
    """

    def setup(self):
        """ Default Kytos/Napps setup call. """
        log.info("Starting Kytos SDNTrace App!")

        # Create list of switches
        self.switches = Switches(self.controller.switches)

        # Instantiate TraceManager
        self.tracing = TraceManager(self.controller)

    @rest('/trace', methods=['PUT'])
    def rest_new_trace(self):
        return self.tracing.rest_new_trace(request.get_json())

    @rest('/trace/<trace_id>')
    def rest_get_result(self, trace_id):
        return self.tracing.rest_get_result(trace_id)

    @listen_to('kytos/of_core.v0x01.messages.in.ofpt_packet_in')
    def handle_packet_in(self, event):
        """ Receives PacketIn msgs and search from trace packets.

        Args:
            event (KycoPacketIn): Received Event
        """
        log.debug("PacketIn Received")
        packet_in = event.content['message']

        in_port = packet_in.in_port.value
        switch = event.source.switch

        ethernet = Ethernet()
        ethernet.unpack(packet_in.data.value)

        if settings.COLOR_VALUE in ethernet.source.value:
            self.tracing.process_probe_packet(event, ethernet,
                                              in_port, switch)

    def execute(self):
        """

        """
        pass

    def shutdown(self):
        """

        """
        pass
