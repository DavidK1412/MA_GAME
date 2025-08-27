import re


def replace_placeholders_in_equation(equation, context):
    def replacer(match):
        var_name = match.group(1)  # Extraer el nombre del placeholder
        return str(context.get(var_name, match.group(0)))  # Reemplazar por el valor o mantener el placeholder
    
    return re.sub(r"\$\{(.*?)\}", replacer, equation)

def evaluate_equation(equation, context):
    try:
        result = eval(equation, {}, context)
    except Exception as e:
        result = f"Error al evaluar la ecuación: {e}"
    return result
