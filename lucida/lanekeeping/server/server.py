#!/usr/bin/env python

import sys
sys.path.append('../')

from TemplateConfig import *

from lucidatypes.ttypes import QuerySpec
from lucidaservice import LucidaService

from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol
from thrift.server import TServer

# Default answer when we do not know how to handle a query
DEFAULT_ANSWER = 'Sorry, I do not know how to handle that.'

# Default power setting
POWER_DEFAULT = 'off'

# Default vibration setting index
VIBRATION_DEFAULT_INDEX = 1

# Vibration settings
VIBRATION = ['Low', 'Normal', 'High']

# Default lane keeping system entry
LK_DEFAULT = {
        'power': POWER_DEFAULT,
        'vibration_idx': VIBRATION_DEFAULT_INDEX
}

# Global to keep track of LUCID Lane Keeping Systems
LK_SYSTEM = {}

class TemplateHandler(LucidaService.Iface):
    def create(self, LUCID, spec):
        return

    def learn(self, LUCID, knowledge):
        return

    def infer(self, LUCID, query):
        """
        Function to handle queries about the Lane Keeping System
        """
        print("@@@@@ Infer; User: " + LUCID)
        if len(query.content) == 0 or len(query.content[0].data) == 0:
            return "error: incorrect query"
        query_data = query.content[0].data[-1]
        print("Asking: " + query_data)
        answer_data = DEFAULT_ANSWER

        # Add entry for LUCID not in system
        if LUCID not in LK_SYSTEM:
            LK_SYSTEM[LUCID] = {'lk_system':LK_DEFAULT}

        # Status Commands
        if 'status' in query_data:
            # Power Commands
            if query_data == 'power status':
                system = 'lane keeping system'
                status = LK_SYSTEM[LUCID]['lk_system']['power']

            # Vibration Commands
            elif query_data == 'vibration status':
                system = 'vibration intensity level'
                status = VIBRATION[LK_SYSTEM[LUCID]['lk_system']['vibration_idx']]
            answer_data = 'Currently, your %s is %s.' %(system, status)

        # Functional Commands
        else:
            # Power Commands
            if 'power' in query_data:
                if query_data == 'power on':
                    power = 'on'
                elif query_data == 'power off':
                    power = 'off'
                LK_SYSTEM[LUCID]['lk_system']['power'] = power
                answer_data = 'Okay, your lane keeping system in now %s.' %(power)

            # Vibration Commands
            elif 'vibration' in query_data:
                vibration_idx = LK_SYSTEM[LUCID]['lk_system']['vibration_idx']
                if query_data == 'vibration up':
                    if vibration_idx == 2:
                        answer_data = 'Sorry but your vibration intesity is already at its maximum level.'
                    else:
                        vibration_idx = vibration_idx + 1
                        LK_SYSTEM[LUCID]['lk_system']['vibration_idx'] = vibration_idx
                        answer_data = 'Okay, your vibration intensity is now set to %s' %(VIBRATION[vibration_idx])
                elif query_data == 'vibration down':
                    if vibration_idx == 0:
                        answer_data = 'Sorry but your vibration intesity is already at its minimum level.'
                    else:
                        vibration_idx = vibration_idx - 1
                        LK_SYSTEM[LUCID]['lk_system']['vibration_idx'] = vibration_idx
                        answer_data = 'Okay, your vibration intensity is now set to %s' %(VIBRATION[vibration_idx])

        print("Result: " + answer_data)
        return 'LK' + answer_data

# Set handler to our implementation and setup the server
handler = TemplateHandler()
processor = LucidaService.Processor(handler)
transport = TSocket.TServerSocket(port=PORT)
tfactory = TTransport.TFramedTransportFactory()
pfactory = TBinaryProtocol.TBinaryProtocolFactory()
server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)

# Display useful information on the command center and start the server
print 'LK at port %d' % PORT
server.serve()
