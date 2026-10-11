import anthropic
import os
import base64
import time
from pydantic import ValidationError
from decimal import Decimal

MEDIA_TYPES = {
    '.png': ('image/png', 'image'),
    '.jpg': ('image/jpeg', 'image'),
    '.jpeg': ('image/jpeg', 'image'),
    '.pdf' : ('application/pdf', 'document')
}
ANTHROPIC_PRICING = {
    'claude-sonnet-5-5': lambda input, output: ((Decimal('2.00') * Decimal(str(input))) + (Decimal('10.00') * Decimal(str(output)))) / Decimal('1_000_000') 
}

def get_usage_record(*, message, input_tokens, output_tokens, start, end):
    return {
        'model': message.model,
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'cost_usd': ANTHROPIC_PRICING[message.model](input_tokens, output_tokens),
        'latency_ms': (end - start) * 1000
    }

def call_claude(messages, schema):
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    schema = anthropic.transform_schema(schema)
    message = client.messages.create(
        model='claude-sonnet-5-5',
        max_tokens=1024,
        messages=messages,
        output_config={
            'format': {
                'type': 'json_schema',
                'schema': schema
            }
        }
    )
    return message


def extract_from_file(*, file_path, schema):
    extension = os.path.splitext(file_path)[1].lower()
    media_type, content_type = MEDIA_TYPES[extension]
    with open(file_path, 'rb') as file:
        file_data = base64.b64encode(file.read()).decode('utf-8')
    messages=[
        {
            'role': 'user', 
            'content': [
                {
                    'type': content_type, 
                    'source': {
                        'type': 'base64', 
                        'media_type': media_type, 
                        'data': file_data
                    }
                }, 
                {
                    'type': 'text', 
                    'text': f'Analyze this file according to its media type of {media_type} and return the result in the specified JSON format.'
                    }
            ]
        }
    ]
 
    start = time.perf_counter()
    attempts = 1
    max_attempts = 2
    input_tokens = 0
    output_tokens = 0
    while attempts <= max_attempts:
        try:
            message = call_claude(messages, schema)
            input_tokens += message.usage.input_tokens
            output_tokens += message.usage.output_tokens        
            if message.stop_reason == 'max_tokens':
                end = time.perf_counter()
                return {
                    'parsed_model': None,
                    'attempt_count': attempts,
                    'raw_errors': [f'message could not be parsed due to insufficient token'],
                    'status': 'failed',
                    'usage_record': get_usage_record(message=message, input_tokens=input_tokens, output_tokens=output_tokens, start=start, end=end)
                }
                
            if message.stop_reason == 'refusal':
                end = time.perf_counter()
                return {
                    'parsed_model': None,
                    'attempt_count': attempts,
                    'raw_errors': [f'message was refused'],
                    'status': 'failed',
                    'usage_record': get_usage_record(message=message, input_tokens=input_tokens, output_tokens=output_tokens, start=start, end=end)
                }
                
            data = [block.text for block in message.content if isinstance(block, anthropic.types.TextBlock)]    
            if not data:
                end = time.perf_counter()
                return {
                    'parsed_model': None,
                    'attempt_count': attempts,
                    'raw_errors': [f'error retrieving data'],
                    'status': 'failed',
                    'usage_record': get_usage_record(message=message, input_tokens=input_tokens, output_tokens=output_tokens, start=start, end=end)
                }
            
            parsed_model = schema.model_validate_json(data[0])
            break       
        
        except ValidationError as ve:
            retry_message = [
                {
                    'role': 'assistant',
                    'content': [
                        {
                            'type': 'text',
                            'text': data[0]
                        }
                    ]
                },
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': f'That failed with a response of {str(ve)}. Please try again with the correct object output'
                        }
                    ]
                }
            ]
            messages.extend(retry_message)
            attempts += 1
            if attempts > max_attempts:
                end = time.perf_counter()
                return {
                    'parsed_model': None,
                    'attempt_count': attempts - 1,
                    'raw_errors': [str(ve)],
                    'status': 'failed',
                    'usage_record': get_usage_record(message=message, input_tokens=input_tokens, output_tokens=output_tokens, start=start, end=end)
                }
                        
    end = time.perf_counter()
    result = {
        'parsed_model': parsed_model,
        'attempt_count': attempts,
        'raw_errors': [],
        'status': 'extracted',
        'usage_record': get_usage_record(message=message, input_tokens=input_tokens, output_tokens=output_tokens, start=start, end=end)
    }
    return result


if __name__ == '__main__':
    from .schemas import Invoice
    file_path = r'E:\code\document_extractor\sample\Fitness-Studio-Receipt-Template.jpg'
    
    message = extract_from_file(file_path=file_path, schema=Invoice)
    print(message)