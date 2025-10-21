"""API routes for feedback application"""
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from app.database import DatabaseManager
from app.models import Feedback
from app.metrics import record_feedback_operation, update_feedback_count

logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)
db = DatabaseManager()


def validate_feedback_message(data: dict) -> tuple[bool, str]:
    """Validate feedback message from request"""
    if not data:
        return False, "Request body is required"

    message = data.get('message', '').strip()
    if not message:
        return False, "Message field is required and cannot be empty"

    if len(message) > 500:
        return False, "Message cannot exceed 500 characters"

    return True, message


@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    from app.metrics import http_requests_total, http_request_duration_seconds
    import time
    start_time = time.time()

    try:
        feedback_count = db.count_feedback()
        logger.info("Health check performed")

        duration = time.time() - start_time
        http_requests_total.labels(method='GET', endpoint='/health', status=200).inc()
        http_request_duration_seconds.labels(method='GET', endpoint='/health').observe(duration)

        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'feedback_count': feedback_count
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        duration = time.time() - start_time
        http_requests_total.labels(method='GET', endpoint='/health', status=503).inc()
        http_request_duration_seconds.labels(method='GET', endpoint='/health').observe(duration)

        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

@api.route('/feedback', methods=['POST'])
def create_feedback():
    """Create new feedback entry"""
    from app.metrics import http_requests_total, http_request_duration_seconds
    import time
    start_time = time.time()

    try:
        is_valid, result = validate_feedback_message(request.json)
        if not is_valid:
            duration = time.time() - start_time
            http_requests_total.labels(method='POST', endpoint='/feedback', status=400).inc()
            http_request_duration_seconds.labels(method='POST', endpoint='/feedback').observe(duration)
            return jsonify({'error': result}), 400

        feedback = Feedback.create(message=result)
        saved_feedback = db.create_feedback(feedback)

        record_feedback_operation('create')
        update_feedback_count(db.count_feedback())

        duration = time.time() - start_time
        http_requests_total.labels(method='POST', endpoint='/feedback', status=201).inc()
        http_request_duration_seconds.labels(method='POST', endpoint='/feedback').observe(duration)

        logger.info(f"Feedback created: {saved_feedback.id}")
        return jsonify(saved_feedback.to_dict()), 201

    except Exception as e:
        logger.error(f"Error creating feedback: {e}")
        duration = time.time() - start_time
        http_requests_total.labels(method='POST', endpoint='/feedback', status=500).inc()
        http_request_duration_seconds.labels(method='POST', endpoint='/feedback').observe(duration)
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/feedback', methods=['GET'])
def get_all_feedback():
    """Retrieve all feedback entries"""
    from app.metrics import http_requests_total, http_request_duration_seconds
    import time
    start_time = time.time()

    try:
        feedbacks = db.get_all_feedback()
        record_feedback_operation('read')

        duration = time.time() - start_time
        http_requests_total.labels(method='GET', endpoint='/feedback', status=200).inc()
        http_request_duration_seconds.labels(method='GET', endpoint='/feedback').observe(duration)

        logger.info(f"Retrieved {len(feedbacks)} feedback entries")
        return jsonify([f.to_dict() for f in feedbacks]), 200

    except Exception as e:
        logger.error(f"Error retrieving feedback: {e}")
        duration = time.time() - start_time
        http_requests_total.labels(method='GET', endpoint='/feedback', status=500).inc()
        http_request_duration_seconds.labels(method='GET', endpoint='/feedback').observe(duration)
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/feedback/<int:feedback_id>', methods=['GET'])
def get_feedback(feedback_id):
    """Retrieve specific feedback by ID"""
    from app.metrics import http_requests_total, http_request_duration_seconds
    import time
    start_time = time.time()

    try:
        feedback = db.get_feedback_by_id(feedback_id)
        if not feedback:
            duration = time.time() - start_time
            http_requests_total.labels(method='GET', endpoint='/feedback/:id', status=404).inc()
            http_request_duration_seconds.labels(method='GET', endpoint='/feedback/:id').observe(duration)
            return jsonify({'error': 'Feedback not found'}), 404

        duration = time.time() - start_time
        http_requests_total.labels(method='GET', endpoint='/feedback/:id', status=200).inc()
        http_request_duration_seconds.labels(method='GET', endpoint='/feedback/:id').observe(duration)

        logger.info(f"Retrieved feedback: {feedback_id}")
        return jsonify(feedback.to_dict()), 200

    except Exception as e:
        logger.error(f"Error retrieving feedback {feedback_id}: {e}")
        duration = time.time() - start_time
        http_requests_total.labels(method='GET', endpoint='/feedback/:id', status=500).inc()
        http_request_duration_seconds.labels(method='GET', endpoint='/feedback/:id').observe(duration)
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/feedback/<int:feedback_id>', methods=['PUT'])
def update_feedback(feedback_id):
    """Update existing feedback"""
    from app.metrics import http_requests_total, http_request_duration_seconds
    import time
    start_time = time.time()

    try:
        is_valid, result = validate_feedback_message(request.json)
        if not is_valid:
            duration = time.time() - start_time
            http_requests_total.labels(method='PUT', endpoint='/feedback/:id', status=400).inc()
            http_request_duration_seconds.labels(method='PUT', endpoint='/feedback/:id').observe(duration)
            return jsonify({'error': result}), 400

        existing = db.get_feedback_by_id(feedback_id)
        if not existing:
            duration = time.time() - start_time
            http_requests_total.labels(method='PUT', endpoint='/feedback/:id', status=404).inc()
            http_request_duration_seconds.labels(method='PUT', endpoint='/feedback/:id').observe(duration)
            return jsonify({'error': 'Feedback not found'}), 404

        updated_at = datetime.utcnow().isoformat()
        success = db.update_feedback(feedback_id, result, updated_at)

        if success:
            updated_feedback = db.get_feedback_by_id(feedback_id)
            record_feedback_operation('update')

            duration = time.time() - start_time
            http_requests_total.labels(method='PUT', endpoint='/feedback/:id', status=200).inc()
            http_request_duration_seconds.labels(method='PUT', endpoint='/feedback/:id').observe(duration)

            logger.info(f"Feedback updated: {feedback_id}")
            return jsonify(updated_feedback.to_dict()), 200
        else:
            duration = time.time() - start_time
            http_requests_total.labels(method='PUT', endpoint='/feedback/:id', status=500).inc()
            http_request_duration_seconds.labels(method='PUT', endpoint='/feedback/:id').observe(duration)
            return jsonify({'error': 'Update failed'}), 500

    except Exception as e:
        logger.error(f"Error updating feedback {feedback_id}: {e}")
        duration = time.time() - start_time
        http_requests_total.labels(method='PUT', endpoint='/feedback/:id', status=500).inc()
        http_request_duration_seconds.labels(method='PUT', endpoint='/feedback/:id').observe(duration)
        return jsonify({'error': 'Internal server error'}), 500

@api.route('/feedback/<int:feedback_id>', methods=['DELETE'])
def delete_feedback(feedback_id):
    """Delete feedback by ID"""
    from app.metrics import http_requests_total, http_request_duration_seconds
    import time
    start_time = time.time()

    try:
        success = db.delete_feedback(feedback_id)
        if not success:
            duration = time.time() - start_time
            http_requests_total.labels(method='DELETE', endpoint='/feedback/:id', status=404).inc()
            http_request_duration_seconds.labels(method='DELETE', endpoint='/feedback/:id').observe(duration)
            return jsonify({'error': 'Feedback not found'}), 404

        record_feedback_operation('delete')
        update_feedback_count(db.count_feedback())

        duration = time.time() - start_time
        http_requests_total.labels(method='DELETE', endpoint='/feedback/:id', status=200).inc()
        http_request_duration_seconds.labels(method='DELETE', endpoint='/feedback/:id').observe(duration)

        logger.info(f"Feedback deleted: {feedback_id}")
        return jsonify({'message': 'Feedback deleted successfully'}), 200

    except Exception as e:
        logger.error(f"Error deleting feedback {feedback_id}: {e}")
        duration = time.time() - start_time
        http_requests_total.labels(method='DELETE', endpoint='/feedback/:id', status=500).inc()
        http_request_duration_seconds.labels(method='DELETE', endpoint='/feedback/:id').observe(duration)
        return jsonify({'error': 'Internal server error'}), 500
