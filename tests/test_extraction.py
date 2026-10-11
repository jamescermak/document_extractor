import pytest
from app import extraction
from app.schemas import Invoice
import os
from app.extraction import extract_from_file
from decimal import Decimal
import copy


def test_happy_path(monkeypatch, test_pdf, claude_message, raw_invoice):
    def mock_claude(*args, **kwargs):
        return claude_message(
            input_tokens=1000,
            output_tokens=10,
            stop_reason='end_turn',
            invoice=raw_invoice,
            model='claude-sonnet-5-5')
    
    file_path = os.path.abspath(test_pdf.name)
    monkeypatch.setattr(extraction, 'call_claude', mock_claude)
    message = extract_from_file(file_path=file_path, schema=Invoice)
    
    errors = []
    if not message['parsed_model'] == Invoice(**raw_invoice):
        errors.append('parsed_model error')
    
    if not message['usage_record']['input_tokens'] == 1000:
        errors.append('input_token error')
    
    if not message['usage_record']['cost_usd'] == Decimal('0.0021'):
        errors.append('cost_usd error')

    assert not errors, 'errors occured:\n{}'.format('\n'.join(errors))

def retry_good_responses(data):
    bad_response = copy.deepcopy(data)
    bad_response['tax'] = '-10.00'

    good_response = copy.deepcopy(data)
    good_response['tax'] = '10.00'

    responses = [bad_response, good_response]
    for response in responses:
        yield response
    
def test_retry_w_success(monkeypatch, test_pdf, claude_message, raw_invoice):
    gen = retry_good_responses(raw_invoice)
    def mock_claude(*args, **kwargs):
            return claude_message(
                input_tokens=1000,
                output_tokens=10,
                stop_reason='end_turn',
                invoice=next(gen),
                model='claude-sonnet-5-5')
    
    file_path = os.path.abspath(test_pdf.name)
    monkeypatch.setattr(extraction, 'call_claude', mock_claude)
    message = extract_from_file(file_path=file_path, schema=Invoice)
    
    errors = []
    if not message['usage_record']['input_tokens'] == 2000:
        errors.append('input_tokens error')
    
    if not message['status'] == 'extracted':
        errors.append('status error')
        
    if not message['attempt_count'] == 2:
        errors.append('attempt_count error')
    
    assert not errors, 'errors occured:\n{}'.format('\n'.join(errors))


def retry_bad_responses(data):
    bad_response = copy.deepcopy(data)
    bad_response['tax'] = '-10.00'

    responses = [bad_response, bad_response]
    for response in responses:
        yield response

def test_retry_w_failure(monkeypatch, test_pdf, claude_message, raw_invoice):
    gen = retry_bad_responses(raw_invoice)
    def mock_claude(*args, **kwargs):
            return claude_message(
                input_tokens=1000,
                output_tokens=10,
                stop_reason='end_turn',
                invoice=next(gen),
                model='claude-sonnet-5-5')
    
    file_path = os.path.abspath(test_pdf.name)
    monkeypatch.setattr(extraction, 'call_claude', mock_claude)
    message = extract_from_file(file_path=file_path, schema=Invoice)
    
    errors = []
    if not message['usage_record']['input_tokens'] == 2000:
        errors.append('input_tokens error')
    
    if not message['status'] == 'failed':
        errors.append('status error')
        
    if not message['attempt_count'] == 2:
        errors.append('attempt_count error')
    
    if message['parsed_model']:
        errors.append('parsed_model error')
    
    assert not errors, 'errors occured:\n{}'.format('\n'.join(errors))   
    
    

def test_max_tokens_rejection(monkeypatch, test_pdf, claude_message, raw_invoice):
    def mock_claude(*args, **kwargs):
        return claude_message(
            input_tokens=10,
            output_tokens=0,
            stop_reason='max_tokens',
            invoice=raw_invoice,
            model='claude-sonnet-5-5'
        )
    
    file_path = os.path.abspath(test_pdf.name)
    monkeypatch.setattr(extraction, 'call_claude', mock_claude)
    message = extract_from_file(file_path=file_path, schema=Invoice)
    
    errors = []
    if not message['status'] == 'failed':
        errors.append('status error')
    
    if not message['raw_errors'] == [f'message could not be parsed due to insufficient token']:
        errors.append('raw_errors error')
        
    if not message['usage_record'].items() >= {
        'model': 'claude-sonnet-5-5',
        'input_tokens': 10,
        'output_tokens': 0,
        'cost_usd': Decimal('0.00002'),
    }.items():
        errors.append('usage dict error')
    
    if message['parsed_model']:
        errors.append('parsed_model error')
    
    assert not errors, 'errors occured:\n{}'.format('\n'.join(errors))


def test_refusal_rejection(monkeypatch, test_pdf, claude_message, raw_invoice):
    def mock_claude(*args, **kwargs):
        return claude_message(
            input_tokens=10,
            output_tokens=0,
            stop_reason='refusal',
            invoice=raw_invoice,
            model='claude-sonnet-5-5'
        )
    
    file_path = os.path.abspath(test_pdf.name)
    monkeypatch.setattr(extraction, 'call_claude', mock_claude)
    message = extract_from_file(file_path=file_path, schema=Invoice)
    
    errors = []
    if not message['status'] == 'failed':
        errors.append('status failed')
    
    if not message['raw_errors'] == [f'message was refused']:
        errors.append('raw_errors failed')
        
    if not message['usage_record'].items() >= {
        'model': 'claude-sonnet-5-5',
        'input_tokens': 10,
        'output_tokens': 0,
        'cost_usd': Decimal('0.00002'),
    }.items():
        errors.append('usage dict failed')
    
    if message['parsed_model']:
        errors.append('parsed_model error')
    
    assert not errors, 'errors occured:\n{}'.format('\n'.join(errors))