import logging
from utils import build_response
import controller

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def route_request(event):
    # Support for both REST API (v1.0) and HTTP API (v2.0) payloads
    request_context = event.get('requestContext', {})
    
    if 'http' in request_context:
        # HTTP API v2.0 Payload
        http_method = request_context['http'].get('method')
        route_key = event.get('routeKey', '')
        if ' ' in route_key:
            resource = route_key.split(' ', 1)[1]
        else:
            resource = event.get('rawPath')
    else:
        # REST API v1.0 Payload
        http_method = event.get('httpMethod')
        resource = event.get('resource')

    path_parameters = event.get('pathParameters') or {}
    
    logger.info(f"Routing request: {http_method} {resource}")
    
    if http_method == 'POST' and resource == '/reports/generate':
        return controller.generate_report(event)
        
    elif http_method == 'GET' and resource == '/reports/tests':
        return controller.get_all_test_reports(event)
        
    elif http_method == 'GET' and resource == '/reports/tests/{testId}':
        return controller.get_test_report(event, path_parameters)
        
    elif http_method == 'GET' and resource == '/reports/tests/{testId}/candidates':
        return controller.get_test_candidates(event, path_parameters)
        
    elif http_method == 'GET' and resource == '/reports/tests/{testId}/excel':
        return controller.export_test_report(event, path_parameters)
        
    elif http_method == 'GET' and resource == '/reports/tests/{testId}/candidates/{mailId}':
        return controller.get_candidate_report(event, path_parameters)
        
    elif http_method == 'PATCH' and resource == '/reports/tests/{testId}/candidates/{mailId}/coding-score':
        return controller.update_coding_score(event, path_parameters)
        
    elif http_method == 'DELETE' and resource == '/reports/tests/{testId}/candidates/{mailId}':
        return controller.delete_candidate_report(event, path_parameters)
        
    elif http_method == 'GET' and resource == '/reports/health':
        return controller.health_check(event)
        
    else:
        logger.warning(f"Route not found: {http_method} {resource}")
        return build_response(404, False, "Not Found")
