import os
import time
from PyQt6.QtCore import QThread, pyqtSignal


def download_model(model_name="base"):
    """下载模型到本地"""
    try:
        import whisper
        print(f"正在下载模型 {model_name}...")
        model = whisper.load_model(model_name)
        print("模型下载成功")
        return True
    except Exception as e:
        print(f"模型下载失败: {e}")
        return False


class TranscriptionWorker(QThread):
    progress_updated = pyqtSignal(int)
    segment_ready = pyqtSignal(str)
    transcription_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    estimation_ready = pyqtSignal(int)

    def __init__(self, audio_path, model_name="medium", enable_speaker_diarization=True):
        super().__init__()
        self.audio_path = audio_path
        self.model_name = model_name
        self.enable_speaker_diarization = enable_speaker_diarization
        self._is_running = True
        self._model = None
        self._start_time = None

    def run(self):
        try:
            self.transcribe()
        except Exception as e:
            self.error_occurred.emit(str(e))

    def stop(self):
        self._is_running = False

    def transcribe(self):
        try:
            import whisper
            import torch
            
            if not os.path.exists(self.audio_path):
                raise FileNotFoundError(f"音频文件不存在: {self.audio_path}")
            
            if not self.audio_path.lower().endswith(('.mp3', '.m4a')):
                raise ValueError("仅支持MP3和M4A格式文件")
            
            self.status_updated.emit("正在加载模型...")
            
            try:
                self._model = whisper.load_model(self.model_name)
            except Exception as model_error:
                raise RuntimeError(f"模型加载失败: {str(model_error)}\n请检查网络连接或删除 ~/.cache/whisper 目录后重试")
            
            self.status_updated.emit("正在分析音频...")
            audio = whisper.load_audio(self.audio_path)
            audio_duration = len(audio) / whisper.audio.SAMPLE_RATE
            
            self.status_updated.emit(f"音频时长: {int(audio_duration)}秒，准备转录...")
            
            if self._is_running:
                self.progress_updated.emit(0)
                self._start_time = time.time()
                self.status_updated.emit("正在转录音频...")
                
                result = self._model.transcribe(
                    audio,
                    language="zh",
                    fp16=False,
                    verbose=False
                )
                
                segments = result.get("segments", [])
                total_duration = result.get("duration", 0)
                
                speaker_assignments = None
                if self.enable_speaker_diarization:
                    self.status_updated.emit("正在识别说话人...")
                    try:
                        speaker_assignments = self.identify_speakers(audio, segments)
                    except Exception as e:
                        print(f"说话人识别失败，将使用普通模式: {e}")
                        self.status_updated.emit("说话人识别失败，使用普通模式")
                        speaker_assignments = None
                
                full_text = []
                segment_count = 0
                
                for i, segment in enumerate(segments):
                    if not self._is_running:
                        break
                    
                    segment_text = segment.get("text", "").strip()
                    if segment_text:
                        segment_count += 1
                        
                        start_time = segment.get("start", 0)
                        end_time = segment.get("end", 0)
                        
                        speaker_label = ""
                        if speaker_assignments:
                            speaker_label = self.get_speaker_for_segment(start_time, end_time, speaker_assignments)
                        
                        formatted_text = f"{speaker_label}{segment_text}"
                        full_text.append(formatted_text)
                        self.segment_ready.emit(formatted_text)
                        self.status_updated.emit(f"已识别 {segment_count} 个片段")
                
                if self._is_running:
                    self.progress_updated.emit(100)
                    self.transcription_complete.emit("\n".join(full_text))
                    elapsed = int(time.time() - self._start_time)
                    self.status_updated.emit(f"转录完成 (用时: {elapsed}秒)")
            
        except ImportError as e:
            self.error_occurred.emit(f"依赖库未安装: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"转录失败: {str(e)}")
    
    def identify_speakers(self, audio, segments):
        """识别说话人"""
        try:
            self.status_updated.emit("正在分析说话人...")
            
            import numpy as np
            from sklearn.cluster import AgglomerativeClustering
            from sklearn.preprocessing import StandardScaler
            
            if len(segments) < 2:
                return []
            
            features = []
            for segment in segments:
                start = segment.get("start", 0)
                end = segment.get("end", 0)
                duration = end - start
                
                start_idx = int(start * 16000)
                end_idx = int(end * 16000)
                if end_idx > len(audio):
                    end_idx = len(audio)
                
                audio_segment = audio[start_idx:end_idx]
                
                if len(audio_segment) > 0:
                    audio_float = audio_segment.astype(np.float32)
                    avg_energy = np.mean(audio_float ** 2)
                    zero_crossing_rate = np.sum(np.abs(np.diff(np.sign(audio_segment)))) / (2 * len(audio_segment))
                    
                    features.append([duration, avg_energy, zero_crossing_rate])
                else:
                    features.append([duration, 0, 0])
            
            if len(features) == 0:
                return []
            
            features = np.array(features)
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            n_clusters = min(2, len(features))
            clustering = AgglomerativeClustering(n_clusters=n_clusters)
            labels = clustering.fit_predict(features_scaled)
            
            speaker_times = []
            for i, segment in enumerate(segments):
                speaker_times.append({
                    'start': segment.get("start", 0),
                    'end': segment.get("end", 0),
                    'speaker': f'SPEAKER_{labels[i]}'
                })
            
            return speaker_times
            
        except Exception as e:
            print(f"说话人识别失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_speaker_for_segment(self, start, end, speaker_assignments):
        """为时间段匹配说话人"""
        if not speaker_assignments:
            return ""
        
        speaker_counts = {}
        
        for assignment in speaker_assignments:
            s_start = assignment['start']
            s_end = assignment['end']
            speaker = assignment['speaker']
            
            if s_end < start or s_start > end:
                continue
            
            overlap_start = max(start, s_start)
            overlap_end = min(end, s_end)
            overlap_duration = overlap_end - overlap_start
            
            if overlap_duration > 0:
                if speaker not in speaker_counts:
                    speaker_counts[speaker] = 0
                speaker_counts[speaker] += overlap_duration
        
        if not speaker_counts:
            return "[未知说话人] "
        
        dominant_speaker = max(speaker_counts.items(), key=lambda x: x[1])[0]
        speaker_id = 0
        
        unique_speakers = list(set([a['speaker'] for a in speaker_assignments]))
        try:
            speaker_id = unique_speakers.index(dominant_speaker) + 1
        except (ValueError, AttributeError):
            speaker_id = 1
        
        return f"[说话人{speaker_id:02d}] "
