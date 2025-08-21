def is_function_call(response: dict) -> bool:
    """
    Check if the request is a function call. Works only for OpenAI Realtime function calls.

    Args:
        request (dict): The request dictionary to check.

    Returns:
        bool: True if the request is a function call, False otherwise.
    """
    if response.get('type') != 'response.done' or not response.get('response'):
        return False

    response = response.get('response')
    if not response.get('output') or not isinstance(response['output'], list):
        return False
    
    output = response.get('output')

    if output[0].get('type') == 'function_call':
        return True