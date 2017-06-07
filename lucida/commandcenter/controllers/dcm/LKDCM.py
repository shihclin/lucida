import abc
from collections import OrderedDict
import re
from Decision import*

# Information from Ford on various elements of the lane keeping system
LK_INFO = OrderedDict([
    ('red', 'Red lanes mean you are drifiting out of your lane so your wheel vibrates to warn you.'),
    ('yellow', 'Yellow lanes mean you are starting to drift so your wheel will turn back to your lane.'),
    ('gray', 'Gray lanes mean either you are driving under the minimum speed threshold or the road lane markings are not visible.'),
    ('no lane', 'No lanes mean your lane keeping system is off. Would you like me to turn it on?'),
    ('aid', 'Aid mode warns you when you are starting to drift out of your lane.'),
    ('alert', 'Alert mode warns you when you are drifting out of your lane.'),
    ('alerting', 'When changing lanes make sure to use your turn signal to temporarily deactive the lane keeping system.'),
    ('lane', 'The lane keeping system helps to keep you in your lane and warns you otherwise through the aid and alert modes.'),
    ('vibration', 'Vibration insenity is a setting for the aid mode. There are three levels: Low, Normal, High.')])

# Slots that can be extracted for informational queries
INFO_SLOTS = {
        'red':r"\bred(ish)?\b",
        'yellow':r"\byellow(ish)?\b",
        'gray':r"gray(ish)?|grey(ish)?",
        'no lane':r'(\bno\b|\bnot\b|\bany\b) (\blane(s)?\b( markings)?|\bline(s)?\b( markings)?)',
        'aid':r'\baid\b',
        'alert':r'\balert\b',
        'lane':r'\blane(s)?\b( markings)?|\bline(s)?\b( markings)?',
        'vibration':r'\bvibrate\b|\bvibration\b',
        'alerting':r'warning|alerting|vibrating'
}

# Slots that can be extracted for command queries
CMD_SLOTS = {
        'up':r'increase|\bup\b',
        'down':r'decrease|\bdown\b',
        'on':r'\bon\b|running|working|start',
        'off':r'\boff\b|not (running|working)|stop',
        'yes':r'(?i)\byes\b|\bokay\b|\bsure\b|\byeah?\b',
        'no':r'(?i)\bno\b|\bnope\b|nah\b',
        'vibration':r'vibrate|vibration|vibrating',
        'lane':r'\blane(s)?\b( \bmarkings\b)?|\bline(s)?\b( \bmarkings\b)?',
        'change':r'(?i)change|\bturn\b|increase|decrease'
}

# Response for instances in which we do not alter the system
NO_CHANGE = 'Okay, I will leave your system the way it is.'

# Mapping command slot variations to single LK commands
CMD_MAP = OrderedDict([
        (('lane', 'change', 'on', 'yes'),'power on'),
        (('lane', 'change', 'off', 'no'),NO_CHANGE),
        (('lane', 'change', 'off', 'yes'),'power off'),
        (('lane', 'change', 'on', 'no'),NO_CHANGE),
        (('lane', 'change', 'on'),'power on'),
        (('lane', 'change', 'off'),'power off'),
        (('lane', 'on'),'power status'),
        (('lane', 'off'),'power status'),
        (('vibration', 'change', 'up'),'vibration up'),
        (('vibration', 'change', 'down'),'vibration down'),
        (('vibration',),'vibration status'),
        (('change', 'on', 'yes'),'power on'),
        (('change', 'on', 'no'),NO_CHANGE),
        (('change', 'off', 'yes'),'power off'),
        (('change', 'off', 'no'),NO_CHANGE),
])

# Two classifier groups
# TODO: Ideally, we want to create an actual classifier instead of using regex
CLASSIFIER = OrderedDict([
        ('info', r'\bmean\b|\bwork\b|\babout\b|\bwhy\b'),
        ('cmd', r'\w')])

# Default answer when we are unsure how to handle a case
DEFAULT_ANSWER = 'Sorry, I do not know how to handle that.'


class LKDCM(Decision):
    """
    Decision class for LK decision making nodes.
    """
    def __init__(self):
        self.clf = ''
        self.slots = []

    def _classify_query(self, query):
        for key, val in CLASSIFIER.items():
            if re.search(val, query):
                self.clf = key
                return

    def _extract_info(self, query):
        print query
        for key in INFO_SLOTS:
            print INFO_SLOTS[key]
            if re.search(INFO_SLOTS[key], query):
                self.slots.append(key)

    def _extract_cmd(self, query):
        for key in CMD_SLOTS:
            if re.search(CMD_SLOTS[key], query):
                self.slots.append(key)

    def _extract_slots(self, query):
        if self.clf == 'info':
            self._extract_info(query)
        elif self.clf == 'cmd':
            self._extract_cmd(query)

    def _process_info(self):
        for key, val in LK_INFO.items():
            if key in self.slots:
                return val

    def _process_cmd(self):
        for key, val in CMD_MAP.items():
            if all(word in self.slots for word in key):
                return ('', val) if val == NO_CHANGE else (val, '')

    def _process_query(self):
        lk_query = ''
        response = DEFAULT_ANSWER
        if self.clf == 'info':
            response = self._process_info()
        elif self.clf == 'cmd':
            lk_query, response = self._process_cmd()

        if not response:
            response = DEFAULT_ANSWER

        return lk_query, response

    def logic_method(self, response_data, service_graph, dcm_node):
        """
        Decision logic for LKDCM.
        The flow is classify a query as 'info' or 'cmd',
        extract slots based on the classifier,
        and process the query based on the slots and
        classifier.

        Scenarios:
        1. If the query is from the LK node then we pass the response
        to the user

        2. If our response contains a question then we pass it to the
        user to get more information (save slots/clf to save context)

        3. If we need information from the LK Node we send an lk_query
        to the LK node

        4. Otherwise, we finish the state and send our response to the
        user

        Arg:
            response_data: response text/image from previous services
            service_graph: current workflow
            dcm_node: current DCM node in workflow

        Return:
            lucida_response: response to send back to user
            next_node: next node to go to in workflow
        """
        query = response_data['text'][-1]

        # Responses from LK node are prefaced with 'LK'
        # Need classification/slots/processing if query is from user
        if 'LK' not in query:
            if not self.clf:
                self._classify_query(query)
            self._extract_slots(query)
            lk_query, response = self._process_query()
        else:
            # Remove the 'LK' prefix from LK response
            response = query[2:]
            lk_query = ''


        if '?' == response[-1]:
            # Send question to user for more info
            # Responses from user will be a command
            # since we are asking a question
            self.clf = 'cmd'
            # Extract/save slots from question
            self.slots = []
            self._extract_slots(re.split('[?.]', response)[-2])
            self.lucida_response = response
            self.next_node = service_graph.get_next_index(dcm_node, 'DCM_LK')
        elif lk_query:
            # Send command to LK node
            self.slots = []
            self.clf = ''
            response_data['text'].append(lk_query)
            self.lucida_response = ''
            self.next_node = service_graph.get_next_index(dcm_node, 'LK')
        else:
            # Finish state and send response to user
            self.slots = []
            self.clf = ''
            response_data['text'].append(response)
            self.lucida_response = ''
            self.next_node = None
        return
