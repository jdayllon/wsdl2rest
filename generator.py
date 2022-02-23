import jinja2, zeep
import os 
from pprint import pprint
import typer

def main(wsdl_url: str):
  
  if wsdl_url is None: 
    wsdl_url = os.environ['WSDL_URL']

  client = zeep.Client(wsdl_url)

  def __get_python_type(soap_type_definition):
    if type(soap_type_definition) is dict:
      return dict
    else:
      python_type = getattr(zeep.xsd.types.builtins, soap_type_definition.split('(')[0]).accepted_types[0]
      if python_type == "_Decimal":
        return "Decimal"
      else:
        return python_type

  # Transforms zeep types into python types
  def translate_xsd_python_type(soap_type):

    if type(soap_type) is dict and len(soap_type.keys()) == 1:
      return str
    elif type(soap_type) is dict and len(soap_type.keys()) > 1:
      type_format = {}
      for k,v in soap_type.items():
        c_v_type = __get_python_type(v['type']).__name__
        if c_v_type == 'dict':
          type_format[k] = translate_xsd_python_type(v['type']).__name__
        else:
          type_format[k] = c_v_type
      return type_format
    else:
      return __get_python_type(soap_type)


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
  pprint("--------")
  pprint(operations)
  pprint("--------")

  # Obtains operations from the WSDL
  for cur_operation in list(operations.keys()):
    pprint(cur_operation)
    # Obtains the input parameters for the operation
    cur_params = list(operations[cur_operation]['input'].keys())

    # Builds query string parameters
    cur_operation_qs_params = ''#.join(cur_params)

    # Builds function parameters definition
    cur_operation_fun_params_lst = []

    for k,v in operations[cur_operation]['input'].items():
      
      if v['optional']:
        cur_operation_fun_param = f"{k}:Optional[{ translate_xsd_python_type(v['type']).__name__ }]"
        cur_operation_type = 'get'
      else:
        translated_type = translate_xsd_python_type(v['type'])
        if hasattr(translated_type,"__name__"):
          cur_operation_fun_param = f"{k}:{ translated_type.__name__ }"
          cur_operation_qs_params = f"{cur_operation_qs_params}/{{{k}}}"
          cur_operation_type = 'get'
        else:
          cur_operation_fun_param = f"{k}:JSONStructure"
          cur_operation_type = 'post'

      cur_operation_fun_params_lst += [cur_operation_fun_param]

    cur_operation_fun_params = ",".join(cur_operation_fun_params_lst)  

    operations_definition += [{
      'operation_name': cur_operation,
      'operation_qs_params': cur_operation_qs_params,
      'operation_fun_params': cur_operation_fun_params,
      'operation_params_lst': cur_params,
      'operation_type': cur_operation_type,
    }]

  # Prints the REST API definition
  templateLoader = jinja2.FileSystemLoader(searchpath="./templates")
  templateEnv = jinja2.Environment(loader=templateLoader)
  TEMPLATE_FILE_WSDL = "wsdl.j2"
  template_wsdl = templateEnv.get_template(TEMPLATE_FILE_WSDL)
  rest_api_base_code = template_wsdl.render(operations_definition=operations_definition, wsdl_url=wsdl_url)  # this is where to put args to the template renderer

  # to save the results
  with open("app/wsdl.py", "w") as fh:
    fh.write(rest_api_base_code)
      
  # Add custom code calls to main.py
  custom_code_files = []
  for file in os.listdir("./app"):
    if file.endswith(".py"):
      if file not in ["wsdl.py", "main.py", "config.py"]:
        custom_code_files += [file.split(".")[0]]
        
  # Prints MAIN application code 
  TEMPLATE_FILE_MAIN = "main.j2"
  template_main = templateEnv.get_template(TEMPLATE_FILE_MAIN)
  rest_api_base_code = template_main.render(custom_code_files=custom_code_files)  # this is where to put args to the template renderer

  with open("app/main.py", "w") as fh:
    fh.write(rest_api_base_code)

if __name__ == "__main__":
    typer.run(main)