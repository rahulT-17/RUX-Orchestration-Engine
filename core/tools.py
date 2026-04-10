# CORE / tools.py => tools.py defines the Tool object blueprint,
#  while tools_registry.py builds and registers the actual tool instances used by the runtime.

class Tool:
    def __init__(self, name, schema, function, domain, task_type, requires_confirmation, risk) :
        self.name = name
        self.schema = schema 
        self.function = function
        self.domain = domain
        self.task_type = task_type
        self.requires_confirmation = requires_confirmation  
        self.risk = risk