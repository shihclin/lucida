from Service import Service, WorkerService
from Graph import Graph, Node
from Parser import port_dic
from dcm import*

# The maximum number of texts or images for each user.
# This is to prevent the server from over-loading.
MAX_DOC_NUM_PER_USER = 30 # non-negative inetegr

# Train or load the query classifier.
# If you set it to 'load', it is assumed that
# models are already saved in `../models`.
TRAIN_OR_LOAD = 'train' # either 'train' or 'load'

# Pre-configured services.
# The ThriftClient assumes that the following services are running.
# Host IP addresses are resolved dynamically:
# either set by Kubernetes or localhost.
SERVICES = {
    'LK' : Service('LK', int(port_dic["lk_port"]), 'text', None),
    'DCM_LK' : WorkerService('DCM', LKDCM.LKDCM()),
    }

# Map from input type to query classes and services needed by each class.
CLASSIFIER_DESCRIPTIONS = {
    'text' : { 'class_LK_DCM' : Graph([Node('DCM_LK', [0,1]), Node('LK', [0])])}
}

# TODO: Should I have this in its own Config file?
# Structure used to save the state/context across requests in a session
# example:
# SESSION = { <user>:
#                   'graph': <Graph>,
#                   'data': <response_data>
# }
SESSION = {}
