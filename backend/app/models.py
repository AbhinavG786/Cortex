from app import db
from datetime import datetime, timezone

class Video(db.Model):
    """
    Represents a video uploaded to the system.
    """
    __tablename__ = 'videos'

    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    
    status = db.Column(db.String(50), default='pending') # states I am gonna use: pending, processing, completed, failed
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    rois = db.relationship('ROI', backref='video', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Video {self.id} - {self.status}>"

class ROI(db.Model):
    """
    Represents the Region of Interest (bounding box) for a single face in a single frame.
    """
    __tablename__ = 'rois'

    id = db.Column(db.Integer, primary_key=True)
    
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    
    frame_number = db.Column(db.Integer, nullable=False)

    x_min = db.Column(db.Float, nullable=False)
    y_min = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)

    def to_dict(self):
        """Helper method to easily serialize this model to JSON for the API"""
        return {
            "frame_number": self.frame_number,
            "x_min": self.x_min,
            "y_min": self.y_min,
            "width": self.width,
            "height": self.height
        }

    def __repr__(self):
        return f"<ROI Frame:{self.frame_number} Video:{self.video_id}>"