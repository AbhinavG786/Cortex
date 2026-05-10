import io

def test_upload_missing_file_returns_400(client):
    """Test Error Handling: What happens if no file is sent?"""
    response = client.post('/api/v1/videos')
    assert response.status_code == 400
    assert b"No video file provided" in response.data

def test_upload_invalid_file_type_returns_400(client):
    """Test Security: What happens if a bad file type is uploaded?"""
    data = {
        'video': (io.BytesIO(b"fake image data"), 'malicious_script.sh')
    }
    response = client.post('/api/v1/videos', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 400
    assert b"Invalid file type" in response.data

def test_get_roi_for_nonexistent_video_returns_404(client):
    """Test API Contract: Requesting data that doesn't exist."""
    response = client.get('/api/v1/videos/999/roi')
    assert response.status_code == 404

def test_successful_video_upload_lifecycle(client, monkeypatch):
    """
    Test API Contract: A valid upload should return 202 Accepted.
    We 'monkeypatch' (mock) the background processing service so the test 
    doesn't actually spin up AI models and take 30 seconds to run.
    """
    # 1. Mock the background task to do nothing during the test
    def mock_process(*args, **kwargs):
        pass
    
    from app.services import VideoProcessingService
    monkeypatch.setattr(VideoProcessingService, 'process_video_async', mock_process)

    # 2. Simulate a valid video file upload
    data = {
        'video': (io.BytesIO(b"fake video bytes"), 'test_video.mp4')
    }
    
    # 3. Send the request
    response = client.post('/api/v1/videos', data=data, content_type='multipart/form-data')
    
    # 4. Assert the contract was fulfilled
    assert response.status_code == 202
    json_data = response.get_json()
    assert json_data['message'] == "Video accepted for processing"
    assert json_data['status'] == "pending"
    assert 'video_id' in json_data