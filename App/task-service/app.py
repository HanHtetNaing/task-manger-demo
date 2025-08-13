import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

from config import Config
from models import db, Task
from auth import authenticate, get_current_user
from schemas import TaskSchema, task_schema, tasks_schema

# Metrics
REQUEST_COUNT = Counter('flask_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('flask_request_duration_seconds', 'Request latency')

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Rate limiting
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["1000 per hour"]
    )
    
    # Logging
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)
    
    # Middleware for metrics
    @app.before_request
    def before_request():
        request.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        request_latency = time.time() - request.start_time
        REQUEST_LATENCY.observe(request_latency)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.endpoint or 'unknown',
            status=response.status_code
        ).inc()
        return response
    
    # Health checks
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'task-service'
        })
    
    @app.route('/ready')
    def ready():
        try:
            # Check database connection
            db.session.execute('SELECT 1')
            return jsonify({
                'status': 'ready',
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            app.logger.error(f"Readiness check failed: {e}")
            return jsonify({
                'status': 'not ready',
                'error': str(e)
            }), 503
    
    # Metrics endpoint
    @app.route('/metrics')
    def metrics():
        return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
    
    # Task routes
    @app.route('/api/v1/tasks', methods=['GET'])
    @authenticate
    def get_tasks():
        try:
            user_id = get_current_user()['userId']
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            status = request.args.get('status')
            
            query = Task.query.filter_by(user_id=user_id)
            
            if status:
                query = query.filter_by(status=status)
            
            tasks = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return jsonify({
                'tasks': tasks_schema.dump(tasks.items),
                'pagination': {
                    'page': page,
                    'pages': tasks.pages,
                    'per_page': per_page,
                    'total': tasks.total
                }
            })
        except Exception as e:
            app.logger.error(f"Get tasks error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/v1/tasks', methods=['POST'])
    @authenticate
    @limiter.limit("100 per hour")
    def create_task():
        try:
            user_id = get_current_user()['userId']
            data = request.get_json()
            
            # Validate input
            try:
                validated_data = task_schema.load(data)
            except Exception as e:
                return jsonify({'error': 'Validation error', 'details': str(e)}), 400
            
            task = Task(
                title=validated_data['title'],
                description=validated_data.get('description', ''),
                status=validated_data.get('status', 'todo'),
                priority=validated_data.get('priority', 'medium'),
                due_date=validated_data.get('due_date'),
                user_id=user_id
            )
            
            db.session.add(task)
            db.session.commit()
            
            app.logger.info(f"Task created: {task.id} by user {user_id}")
            
            return jsonify({
                'message': 'Task created successfully',
                'task': task_schema.dump(task)
            }), 201
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Create task error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/v1/tasks/<int:task_id>', methods=['GET'])
    @authenticate
    def get_task(task_id):
        try:
            user_id = get_current_user()['userId']
            task = Task.query.filter_by(id=task_id, user_id=user_id).first()
            
            if not task:
                return jsonify({'error': 'Task not found'}), 404
            
            return jsonify({'task': task_schema.dump(task)})
            
        except Exception as e:
            app.logger.error(f"Get task error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/v1/tasks/<int:task_id>', methods=['PUT'])
    @authenticate
    def update_task(task_id):
        try:
            user_id = get_current_user()['userId']
            task = Task.query.filter_by(id=task_id, user_id=user_id).first()
            
            if not task:
                return jsonify({'error': 'Task not found'}), 404
            
            data = request.get_json()
            
            # Update allowed fields
            allowed_fields = ['title', 'description', 'status', 'priority', 'due_date']
            for field in allowed_fields:
                if field in data:
                    setattr(task, field, data[field])
            
            task.updated_at = datetime.utcnow()
            db.session.commit()
            
            app.logger.info(f"Task updated: {task.id} by user {user_id}")
            
            return jsonify({
                'message': 'Task updated successfully',
                'task': task_schema.dump(task)
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Update task error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/v1/tasks/<int:task_id>', methods=['DELETE'])
    @authenticate
    def delete_task(task_id):
        try:
            user_id = get_current_user()['userId']
            task = Task.query.filter_by(id=task_id, user_id=user_id).first()
            
            if not task:
                return jsonify({'error': 'Task not found'}), 404
            
            db.session.delete(task)
            db.session.commit()
            
            app.logger.info(f"Task deleted: {task_id} by user {user_id}")
            
            return jsonify({'message': 'Task deleted successfully'})
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Delete task error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    # Task statistics
    @app.route('/api/v1/tasks/stats', methods=['GET'])
    @authenticate
    def get_task_stats():
        try:
            user_id = get_current_user()['userId']
            
            stats = {
                'total': Task.query.filter_by(user_id=user_id).count(),
                'todo': Task.query.filter_by(user_id=user_id, status='todo').count(),
                'in_progress': Task.query.filter_by(user_id=user_id, status='in_progress').count(),
                'completed': Task.query.filter_by(user_id=user_id, status='completed').count(),
                'overdue': Task.query.filter(
                    Task.user_id == user_id,
                    Task.due_date < datetime.utcnow(),
                    Task.status != 'completed'
                ).count()
            }
            
            return jsonify({'stats': stats})
            
        except Exception as e:
            app.logger.error(f"Get stats error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Route not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    return app