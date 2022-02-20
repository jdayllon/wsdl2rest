import jinja2, zeep
import os 

WSDL_URL = os.environ['WSDL_URL']

client = zeep.Client(WSDL_URL)

# Transforms zeep types into python types
def translate_xsd_python_type(type_name):
  python_type = getattr(zeep.xsd.types.builtins, type_name.split('(')[0]).accepted_types[0]
  if python_type == "_Decimal":
    return "Decimal"
  else:
    return python_type

## Based on StackOverflow answer by user "jessy_galley" 
## https://stackoverflow.com/a/50093489
## https://stackoverflow.com/users/608725/jesse-galley

def parseElements(elements):
    all_elements = {}
    for name, element in elements:
        all_elements[name] = {}
        all_elements[name]['optional'] = element.is_optional
        if hasattr(element.type, 'elements'):
            all_elements[name]['type'] = parseElements(
                element.type.elements)
        else:
            all_elements[name]['type'] = str(element.type)

    return all_elements


interface = {}
for service in client.wsdl.services.values():
    interface[service.name] = {}
    for port in service.ports.values():
        interface[service.name][port.name] = {}
        operations = {}
        for operation in port.binding._operations.values():
            operations[operation.name] = {}
            operations[operation.name]['input'] = {}
            elements = operation.input.body.type.elements
            operations[operation.name]['input'] = parseElements(elements)
        interface[service.name][port.name]['operations'] = operations

operations_definition = []

# Obtains operations from the WSDL
for cur_operation in list(operations.keys()):

  # Obtains the input parameters for the operation
  cur_params = list(operations[cur_operation]['input'].keys())

  # Builds query string parameters
  cur_operation_qs_params = '/'.join(cur_params)
  cur_operation_qs_params

  # Builds function parameters definition
  cur_operation_fun_params_lst = []

  for k,v in operations[cur_operation]['input'].items():
    
    if v['optional']:
      cur_operation_fun_param = f"{k}:Optional[{ translate_xsd_python_type(v['type']).__name__ }]"
    else:
      cur_operation_fun_param = f"{k}:{ translate_xsd_python_type(v['type']).__name__ }"

    cur_operation_fun_params_lst += [cur_operation_fun_param]

  cur_operation_fun_params = ",".join(cur_operation_fun_params_lst)  

  operations_definition += [{
    'operation_name': cur_operation,
    'operation_qs_params': cur_operation_qs_params,
    'operation_fun_params': cur_operation_fun_params,
    'operation_params_lst': cur_params,
  }]

# Prints the REST API definition
templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)
TEMPLATE_FILE = "base.j2"
template = templateEnv.get_template(TEMPLATE_FILE)
rest_api_base_code = template.render(operations_definition=operations_definition, WSDL_URL=WSDL_URL)  # this is where to put args to the template renderer

# to save the results
with open("app/wsdl.py", "w") as fh:
    fh.write(rest_api_base_code)