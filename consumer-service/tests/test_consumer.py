import pytest
import pika
import json
from unittest.mock import patch, MagicMock
from src.consumer import process_message

valid_event = {
    "user_id": 456,
    "event_type": "login",
    "timestamp": "2023-11-01T12:00:00Z",
    "metadata": {"ip": "192.168.1.1"}
}

def test_process_message_valid():
    mock_channel = MagicMock()
    mock_method = MagicMock()
    mock_method.delivery_tag = 1
    mock_properties = MagicMock()
    
    body = json.dumps(valid_event).encode('utf-8')

    with patch('src.consumer.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        
        process_message(mock_channel, mock_method, mock_properties, body)
        
        # Verify db.add and db.commit were called
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify message was acked
        mock_channel.basic_ack.assert_called_once_with(delivery_tag=1)

def test_process_message_invalid_json():
    mock_channel = MagicMock()
    mock_method = MagicMock()
    mock_method.delivery_tag = 2
    mock_properties = MagicMock()
    
    body = b"not a json string"

    with patch('src.consumer.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])
        
        process_message(mock_channel, mock_method, mock_properties, body)
        
        # Verify it was rejected without requeue
        mock_channel.basic_reject.assert_called_once_with(delivery_tag=2, requeue=False)
        mock_db.add.assert_not_called()

def test_process_message_db_error():
    mock_channel = MagicMock()
    mock_method = MagicMock()
    mock_method.delivery_tag = 3
    mock_properties = MagicMock()
    
    body = json.dumps(valid_event).encode('utf-8')

    with patch('src.consumer.get_db') as mock_get_db:
        mock_db = MagicMock()
        mock_db.commit.side_effect = Exception("DB Error")
        mock_get_db.return_value = iter([mock_db])
        
        process_message(mock_channel, mock_method, mock_properties, body)
        
        # Verify it was rolled back and still acked to prevent infinite crashing loop
        mock_db.rollback.assert_called_once()
        mock_channel.basic_ack.assert_called_once_with(delivery_tag=3)
