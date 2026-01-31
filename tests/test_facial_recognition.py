import os
import pickle
import pytest
from unittest.mock import MagicMock, patch
from facial_recognition.manager import FaceRecognizerManager

@pytest.fixture
def manager():
    """Fixture to provide a FaceRecognizerManager instance."""
    return FaceRecognizerManager(model_dir="/tmp/models", encoding_file="/tmp/encodings.pkl")

def test_manager_init(manager):
    """Test the initialization of FaceRecognizerManager."""
    assert manager.model_dir == "/tmp/models"
    assert manager.encoding_file == "/tmp/encodings.pkl"
    assert manager.threshold == 0.4
    assert manager.detector is None
    assert manager.recognizer is None

@patch("os.path.exists")
@patch("os.makedirs")
@patch("urllib.request.urlretrieve")
def test_check_and_download_models(mock_urlretrieve, mock_makedirs, mock_exists, manager):
    """Test checking and downloading models."""
    # models don't exist
    mock_exists.return_value = False
    
    result = manager.check_and_download_models()
    
    assert result is True
    assert mock_makedirs.called
    assert mock_urlretrieve.call_count == 2 

@patch("cv2.FaceDetectorYN.create")
@patch("cv2.FaceRecognizerSF.create")
def test_load_models(mock_sf_create, mock_yn_create, manager):
    """Test loading the ONNX models."""
    mock_yn_create.return_value = MagicMock()
    mock_sf_create.return_value = MagicMock()
    
    result = manager.load_models()
    
    assert result is True
    assert manager.detector is not None
    assert manager.recognizer is not None

@patch("os.path.exists")
@patch("builtins.open")
@patch("pickle.load")
def test_load_encodings_success(mock_pickle_load, mock_open, mock_exists, manager):
    """Test successful loading of encodings."""
    mock_exists.return_value = True
    mock_pickle_load.return_value = (["feat1"], ["name1"])
    
    success, count = manager.load_encodings()
    
    assert success is True
    assert count == 1
    assert manager.known_names == ["name1"]

def test_load_encodings_not_found(manager):
    """Test loading encodings when the file does not exist."""
    with patch("os.path.exists", return_value=False):
        success, count = manager.load_encodings()
        assert success is False
        assert count == 0

def test_rename_file_logic(manager):
    """Test the file renaming logic without actual OS calls."""
    with patch("os.path.exists") as mock_exists:
        with patch("os.rename") as mock_rename:
            # Simple rename
            mock_exists.side_effect = [False] # new_filepath doesn't exist
            result = manager._rename_file("/tmp", "image.jpg", {"Aimine"})
            assert result == "Aimine.jpg"
            mock_rename.assert_called_with("/tmp/image.jpg", "/tmp/Aimine.jpg")
            
            # Rename with multiple people
            mock_exists.side_effect = [False]
            result = manager._rename_file("/tmp", "image.jpg", {"Aimine", "Bob"})
            assert result == "Aimine_Bob.jpg"
            
            # Collision handling
            # First try Aimine.jpg exists, Aimine_2.jpg doesn't
            mock_exists.side_effect = [True, False]
            result = manager._rename_file("/tmp", "image.jpg", {"Aimine"})
            assert result == "Aimine_2.jpg"
            mock_rename.assert_called_with("/tmp/image.jpg", "/tmp/Aimine_2.jpg")

@patch("os.path.exists")
@patch("os.path.isdir")
@patch("os.listdir")
@patch("cv2.imread")
def test_train_faces(mock_imread, mock_listdir, mock_isdir, mock_exists, manager):
    """Test the training process logic."""
    manager.detector = MagicMock()
    manager.recognizer = MagicMock()
    
    mock_exists.return_value = True
    mock_isdir.return_value = True # Treat "Alice" as a directory
    # Structure: known_dir/Aimine/Léo.jpg
    mock_listdir.side_effect = [["Aimine"], ["Léo.jpg"]]
    
    mock_img = MagicMock()
    mock_img.shape = (100, 100, 3)
    mock_imread.return_value = mock_img
    
    # Mock detection and recognition
    manager.detector.detect.return_value = (None, [MagicMock()])
    manager.recognizer.alignCrop.return_value = MagicMock()
    manager.recognizer.feature.return_value = "feature_vector"
    
    with patch("builtins.open", MagicMock()):
        with patch("pickle.dump") as mock_pickle_dump:
            result = manager.train_faces("/tmp/known")
            
            assert result is True
            assert manager.known_names == ["Aimine"]
            assert manager.known_features == ["feature_vector"]
            assert mock_pickle_dump.called

@patch("os.path.exists")
@patch("os.listdir")
@patch("cv2.imread")
def test_process_directory(mock_imread, mock_listdir, mock_exists, manager):
    """Test processing a directory of unknown faces."""
    manager.known_features = ["known_feat"]
    manager.known_names = ["Aimine"]
    manager.detector = MagicMock()
    manager.recognizer = MagicMock()
    
    mock_exists.return_value = True
    mock_listdir.return_value = ["unknown.jpg"]
    
    mock_img = MagicMock()
    mock_img.shape = (100, 100, 3)
    mock_imread.return_value = mock_img
    
    # Mock detection: one face found
    manager.detector.detect.return_value = (None, [MagicMock()])
    manager.recognizer.alignCrop.return_value = MagicMock()
    manager.recognizer.feature.return_value = "unknown_feat"
    
    # Mock recognition match score > threshold
    manager.recognizer.match.return_value = 0.9 
    manager.threshold = 0.4
    
    with patch.object(manager, "_rename_file") as mock_rename:
        mock_rename.return_value = "Aimine.jpg"
        manager.process_directory("/tmp/unknown")
        
        assert mock_rename.called
        # Verify it passed the correct set of found names
        args, _ = mock_rename.call_args
        assert args[2] == {"Aimine"}
