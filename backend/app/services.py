import os
import threading
import imageio
import numpy as np
import mediapipe as mp
from PIL import Image, ImageDraw
from flask import current_app
from app import db
from app.models import Video, ROI

mp_face_detection = mp.solutions.face_detection

class VideoProcessingService:
    @staticmethod
    def process_video_async(app_context, video_id, input_filepath, output_filepath):
        """
        Wrapper to run the video processing in a background thread.
        """
        thread = threading.Thread(
            target=VideoProcessingService._process_video,
            args=(app_context, video_id, input_filepath, output_filepath)
        )
        thread.start()

    @staticmethod
    def _process_video(app_context, video_id, input_filepath, output_filepath):
        """
        The core pipeline: Read -> Detect -> Draw -> Write -> Save DB
        """
        with app_context:
            video = Video.query.get(video_id)
            video.status = 'processing'
            db.session.commit()

            rois_to_insert = []

            try:
     
                reader = imageio.get_reader(input_filepath)
                meta = reader.get_meta_data()
                fps = meta.get('fps', 30.0) 
                
                writer = imageio.get_writer(output_filepath, fps=fps)

                # 2. Initialize MediaPipe (model_selection=0 is best for faces within 2 meters)
                with mp_face_detection.FaceDetection(
                    model_selection=0, 
                    min_detection_confidence=0.5
                ) as face_detection:
                    
                    for frame_number, frame_rgb in enumerate(reader):

                        results = face_detection.process(frame_rgb)

                        if results.detections:
                            detection = results.detections[0] # assuming only one face per frame
                            bbox = detection.location_data.relative_bounding_box
                            
                            # MediaPipe returns relative coordinates (0.0 to 1.0). 
                            # need to convert them to absolute pixel values.
                            h, w, _ = frame_rgb.shape
                            x_min = int(bbox.xmin * w)
                            y_min = int(bbox.ymin * h)
                            width = int(bbox.width * w)
                            height = int(bbox.height * h)

                            # Convert numpy array to Pillow Image
                            pil_image = Image.fromarray(frame_rgb)
                            draw = ImageDraw.Draw(pil_image)
                            
                            # Draw Axis-aligned minimal bounding box [x0, y0, x1, y1]
                            draw.rectangle(
                                [x_min, y_min, x_min + width, y_min + height],
                                outline="red",
                                width=3
                            )
                            
                            # Convert back to numpy array for the video writer
                            frame_rgb = np.array(pil_image)

                            rois_to_insert.append(ROI(
                                video_id=video_id,
                                frame_number=frame_number,
                                x_min=float(x_min),
                                y_min=float(y_min),
                                width=float(width),
                                height=float(height)
                            ))

                        writer.append_data(frame_rgb)

                writer.close()
                reader.close()

                db.session.bulk_save_objects(rois_to_insert)
                
                video.status = 'completed'
                db.session.commit()

                if os.path.exists(input_filepath):
                    os.remove(input_filepath)

            except Exception as e:
                video.status = 'failed'
                db.session.commit()
                print(f"Error processing video {video_id}: {str(e)}")