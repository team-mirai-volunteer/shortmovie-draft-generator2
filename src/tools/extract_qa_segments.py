#!/usr/bin/env python3
"""質問回答セグメント抽出メインスクリプト"""

import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from qa_segmenter import QASegmenter, QASegmenterError


def load_transcription_file(file_path: str) -> Dict[str, Any]:
    """文字起こしファイルを読み込み"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'segments' not in data:
            raise ValueError("文字起こしデータに'segments'フィールドがありません")
        
        return data
    
    except FileNotFoundError:
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"JSONファイルの解析に失敗しました: {e}")


def save_qa_segments(qa_segments, output_path: str):
    """Q&Aセグメントを保存"""
    output_data = {
        "qa_segments": [segment.to_dict() for segment in qa_segments],
        "total_segments": len(qa_segments),
        "extraction_info": {
            "total_duration": sum(seg.total_duration for seg in qa_segments),
            "average_duration": sum(seg.total_duration for seg in qa_segments) / len(qa_segments) if qa_segments else 0
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)


def print_qa_summary(qa_segments):
    """Q&Aセグメントの要約を表示"""
    print(f"\n=== 抽出されたQ&Aセグメント ({len(qa_segments)}件) ===\n")
    
    for segment in qa_segments:
        segmenter = QASegmenter()
        
        print(f"【Q&A {segment.id}】")
        print(f"質問者: {segment.question.speaker or '不明'}")
        print(f"時間範囲: {segmenter.format_time_to_hms(segment.question.start_time)} - {segmenter.format_time_to_hms(segment.answer.end_time)}")
        print(f"総時間: {segment.total_duration:.1f}秒")
        print(f"質問: {segment.question.text[:100]}{'...' if len(segment.question.text) > 100 else ''}")
        print(f"回答: {segment.answer.text[:150]}{'...' if len(segment.answer.text) > 150 else ''}")
        print("-" * 80)


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='動画文字起こしから質問回答セグメントを抽出')
    parser.add_argument('input_file', help='入力文字起こしファイル（JSON形式）')
    parser.add_argument('output_file', help='出力ファイル（JSON形式）')
    parser.add_argument('--num-segments', type=int, default=3, help='抽出するセグメント数（デフォルト: 3）')
    parser.add_argument('--quiet', action='store_true', help='要約表示を無効にする')
    
    args = parser.parse_args()
    
    try:
        print(f"文字起こしファイルを読み込み中: {args.input_file}")
        transcription_data = load_transcription_file(args.input_file)
        
        print(f"Q&Aセグメントを抽出中（{args.num_segments}件）...")
        segmenter = QASegmenter()
        qa_segments = segmenter.extract_qa_segments(transcription_data, args.num_segments)
        
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_qa_segments(qa_segments, args.output_file)
        print(f"結果を保存しました: {args.output_file}")
        
        if not args.quiet:
            print_qa_summary(qa_segments)
        
        print(f"\n✅ 処理完了: {len(qa_segments)}件のQ&Aセグメントを抽出しました")
        
    except (FileNotFoundError, ValueError, QASegmenterError) as e:
        print(f"❌ エラー: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 予期しないエラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
