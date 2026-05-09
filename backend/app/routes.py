import os
from flask import Blueprint, request, jsonify, current_app, send_from_directory
from werkzeug.utils import secure_filename
from app import db
from app.models import Video, ROI
from app.services import VideoProcessingService

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@api_bp.route('/videos', methods=['POST'])
def upload_video():
    """Accepts a video file, creates a DB record, and starts async processing."""
    
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    if file and allowed_file(file.filename):
       
        filename = secure_filename(file.filename) 
    
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        input_filepath = os.path.join(upload_folder, f"raw_{filename}")
        file.save(input_filepath)

        new_video = Video(original_filename=filename, status='pending')
        db.session.add(new_video)
        db.session.commit()

        output_filepath = os.path.join(upload_folder, f"processed_{new_video.id}_{filename}")

        app_context = current_app._get_current_object().app_context()
        VideoProcessingService.process_video_async(
            app_context, new_video.id, input_filepath, output_filepath
        )

        return jsonify({
            "message": "Video accepted for processing",
            "video_id": new_video.id,
            "status": new_video.status
        }), 202
        
    return jsonify({"error": "Invalid file type. Allowed types: mp4, avi, mov"}), 400


@api_bp.route('/videos/<int:video_id>/roi', methods=['GET'])
def get_roi_data(video_id):
    """Returns the JSON payload of bounding boxes for the processed video."""
    video = Video.query.get(video_id)
    
    if not video:
        return jsonify({"error": "Video not found"}), 404
        
    if video.status != 'completed':
        return jsonify({
            "message": f"Video is currently {video.status}", 
            "status": video.status
        }), 200

    rois = ROI.query.filter_by(video_id=video_id).order_by(ROI.frame_number).all()
    
    return jsonify({
        "video_id": video.id,
        "status": video.status,
        "rois": [roi.to_dict() for roi in rois]
    }), 200


@api_bp.route('/videos/<int:video_id>/stream', methods=['GET'])
def stream_video(video_id):
    """Serves the actual processed video file."""
    video = Video.query.get(video_id)
    
    if not video:
        return jsonify({"error": "Video not found"}), 404
        
    if video.status != 'completed':
        return jsonify({"error": "Video processing is not complete yet"}), 400

    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    filename = f"processed_{video.id}_{video.original_filename}"
    
    return send_from_directory(
        os.path.abspath(upload_folder), 
        filename, 
        as_attachment=False 
    )

@api_bp.app_errorhandler(500)
def handle_internal_error(error):
    return jsonify({"error": "An internal server error occurred"}), 500