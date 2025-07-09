"""WhisperClient統合テスト用スクリプト"""

import os
import tempfile
from pathlib import Path
from src.clients.whisper_client import WhisperClient, WhisperClientError


def test_whisper_client_initialization():
    """WhisperClientの初期化テスト"""
    print("=== WhisperClient初期化テスト ===")
    
    try:
        client = WhisperClient("")
        print("❌ 空のAPIキーでエラーが発生しませんでした")
    except ValueError as e:
        print(f"✅ 空のAPIキー検証: {e}")
    
    try:
        client = WhisperClient("test-api-key")
        print("✅ WhisperClientの初期化成功")
        print(f"   - モデル: {client.model}")
        print(f"   - 一時ディレクトリ: {client.temp_dir}")
    except Exception as e:
        print(f"❌ WhisperClient初期化エラー: {e}")


def test_file_validation():
    """ファイル検証機能のテスト"""
    print("\n=== ファイル検証テスト ===")
    
    client = WhisperClient("test-api-key")
    
    try:
        client._validate_video_file("nonexistent.mp4")
        print("❌ 存在しないファイルでエラーが発生しませんでした")
    except FileNotFoundError as e:
        print(f"✅ 存在しないファイル検証: {e}")
    
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(b"test content")
        tmp_path = tmp.name
    
    try:
        client._validate_video_file(tmp_path)
        print("❌ 無効な拡張子でエラーが発生しませんでした")
    except Exception as e:
        print(f"✅ 無効な拡張子検証: {e}")
    finally:
        os.unlink(tmp_path)


def test_response_validation():
    """レスポンス検証機能のテスト"""
    print("\n=== レスポンス検証テスト ===")
    
    client = WhisperClient("test-api-key")
    
    invalid_responses = [
        {},  # 空のレスポンス
        {"text": "テスト"},  # segmentsなし
        {"segments": []},  # textなし
        {"text": "テスト", "segments": "invalid"},  # segmentsが配列でない
        {"text": "テスト", "segments": [{"start": 0.0}]},  # 必須フィールドなし
    ]
    
    for i, response in enumerate(invalid_responses):
        try:
            client._validate_response_data(response)
            print(f"❌ 無効なレスポンス{i+1}でエラーが発生しませんでした")
        except Exception as e:
            print(f"✅ 無効なレスポンス{i+1}検証: {e}")
    
    valid_response = {
        "text": "こんにちは、今日は良い天気ですね。",
        "segments": [
            {"start": 0.0, "end": 2.5, "text": "こんにちは、"},
            {"start": 2.5, "end": 5.0, "text": "今日は良い天気ですね。"}
        ]
    }
    
    try:
        client._validate_response_data(valid_response)
        print("✅ 有効なレスポンス検証成功")
    except Exception as e:
        print(f"❌ 有効なレスポンス検証エラー: {e}")


def test_transcription_result_conversion():
    """TranscriptionResult変換テスト"""
    print("\n=== TranscriptionResult変換テスト ===")
    
    client = WhisperClient("test-api-key")
    
    response_data = {
        "text": "こんにちは、今日は良い天気ですね。",
        "segments": [
            {"start": 0.0, "end": 2.5, "text": "こんにちは、"},
            {"start": 2.5, "end": 5.0, "text": "今日は良い天気ですね。"}
        ]
    }
    
    try:
        result = client._convert_to_transcription_result(response_data)
        print("✅ TranscriptionResult変換成功")
        print(f"   - セグメント数: {len(result.segments)}")
        print(f"   - 全体テキスト: {result.full_text}")
        
        for i, segment in enumerate(result.segments):
            print(f"   - セグメント{i+1}: {segment.start_time}s-{segment.end_time}s: {segment.text}")
            
    except Exception as e:
        print(f"❌ TranscriptionResult変換エラー: {e}")


if __name__ == "__main__":
    print("WhisperClient統合テスト開始\n")
    
    test_whisper_client_initialization()
    test_file_validation()
    test_response_validation()
    test_transcription_result_conversion()
    
    print("\n=== テスト完了 ===")
    print("注意: 実際のWhisper API呼び出しテストには有効なAPIキーと動画ファイルが必要です。")
