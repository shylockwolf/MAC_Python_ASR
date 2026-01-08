from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QComboBox, QProgressBar, QTextEdit, 
                             QFileDialog, QMessageBox, QCheckBox)
from PyQt6.QtCore import Qt, QTimer
from transcriber import TranscriptionWorker


class AudioTranscriberGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.audio_path = None
        self.worker = None
        self.full_transcription = ""
        self.progress_timer = QTimer()
        self.progress_timer.setInterval(500)
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_value = 0
        self.transcription_start_time = None
        self.estimated_duration = 0
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("音频转文字")
        self.setGeometry(100, 100, 500, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        
        self.file_label = QLabel("未选择文件")
        layout.addWidget(QLabel("选择音频文件："))
        self.select_file_btn = QPushButton("选择音频文件")
        self.select_file_btn.clicked.connect(self.select_file)
        layout.addWidget(self.select_file_btn)
        layout.addWidget(self.file_label)
        
        layout.addWidget(QLabel("选择模型："))
        self.model_combo = QComboBox()
        models = [
            ("small", "Small (~470MB, 较快, 中等准确度)"),
            ("medium", "Medium (~769MB, 较慢, 高准确度)"),
            ("large-v3", "Large (~1550MB, 慢, 最高准确度)")
        ]
        for model_name, model_desc in models:
            self.model_combo.addItem(model_desc, model_name)
        self.model_combo.setCurrentIndex(1)
        layout.addWidget(self.model_combo)
        
        self.speaker_checkbox = QCheckBox("识别说话人 (较慢)")
        self.speaker_checkbox.setChecked(True)
        layout.addWidget(self.speaker_checkbox)
        
        self.start_btn = QPushButton("开始转录")
        self.start_btn.clicked.connect(self.start_transcription)
        layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止转录")
        self.stop_btn.clicked.connect(self.stop_transcription)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn)
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        layout.addWidget(QLabel("状态："))
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(QLabel("进度："))
        layout.addWidget(self.progress_bar)
        
        layout.addWidget(QLabel("转录结果："))
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)
        
        self.save_btn = QPushButton("另存为")
        self.save_btn.clicked.connect(self.save_result)
        layout.addWidget(self.save_btn)
        
        central_widget.setLayout(layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择音频文件",
            "",
            "Audio Files (*.mp3 *.m4a);;All Files (*)"
        )
        if file_path:
            if not file_path.lower().endswith(('.mp3', '.m4a')):
                QMessageBox.warning(self, "警告", "请选择MP3或M4A格式文件")
                return
            self.audio_path = file_path
            self.file_label.setText(file_path)

    def start_transcription(self):
        if not self.audio_path:
            QMessageBox.warning(self, "警告", "请先选择音频文件")
            return
        
        self.result_text.clear()
        self.full_transcription = ""
        self.progress_bar.setValue(0)
        self.status_label.setText("准备中...")
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.select_file_btn.setEnabled(False)
        
        model_name = self.model_combo.currentData()
        enable_speaker_diarization = self.speaker_checkbox.isChecked()
        self.worker = TranscriptionWorker(self.audio_path, model_name, enable_speaker_diarization)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.segment_ready.connect(self.on_segment_ready)
        self.worker.transcription_complete.connect(self.on_complete)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.status_updated.connect(self.on_status_update)
        self.worker.start()

    def stop_transcription(self):
        self.progress_timer.stop()
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.select_file_btn.setEnabled(True)
        self.status_label.setText("已停止")
        QMessageBox.information(self, "提示", "转录已停止")

    def on_status_update(self, status_text):
        self.status_label.setText(status_text)
        
        if "正在分析音频" in status_text or "准备转录" in status_text:
            import time
            self.transcription_start_time = time.time()
            
            if self.audio_path:
                import whisper
                try:
                    audio = whisper.load_audio(self.audio_path)
                    audio_duration = len(audio) / whisper.audio.SAMPLE_RATE
                    
                    model_speed = {
                        "small": 3,
                        "medium": 4,
                        "large-v3": 6
                    }
                    
                    model_name = self.model_combo.currentData()
                    speed_factor = model_speed.get(model_name, 4)
                    
                    self.estimated_duration = int(audio_duration * speed_factor)
                    self.progress_value = 0
                    self.progress_timer.start()
                except Exception as e:
                    self.estimated_duration = 30

    def on_segment_ready(self, segment_text):
        self.result_text.append(segment_text)

    def on_complete(self, full_text):
        self.full_transcription = full_text
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.select_file_btn.setEnabled(True)
        self.progress_timer.stop()
        self.progress_bar.setValue(100)
        self.status_label.setText("完成")
        
        auto_save_result = self.auto_save_result()
        if auto_save_result:
            QMessageBox.information(self, "完成", f"转录完成\n\n已自动保存到：\n{auto_save_result}")
        else:
            QMessageBox.information(self, "完成", "转录完成\n\n自动保存失败，请手动保存")

    def update_progress(self):
        if not self.transcription_start_time or self.estimated_duration <= 0:
            return
        
        import time
        elapsed = time.time() - self.transcription_start_time
        progress = int((elapsed / self.estimated_duration) * 100)
        
        if progress >= 100:
            progress = 99
        
        self.progress_bar.setValue(progress)
        remaining = self.estimated_duration - int(elapsed)
        if remaining > 0:
            self.status_label.setText(f"正在转录... {progress}% (剩余约{remaining}秒)")
        else:
            self.status_label.setText(f"正在转录... {progress}%")

    def auto_save_result(self):
        if not self.full_transcription or not self.audio_path:
            return None
        
        try:
            import os
            
            dir_path = os.path.dirname(self.audio_path)
            base_name = os.path.basename(self.audio_path)
            name_without_ext = os.path.splitext(base_name)[0]
            txt_file_path = os.path.join(dir_path, f"{name_without_ext}.txt")
            
            with open(txt_file_path, 'w', encoding='utf-8') as f:
                f.write(self.full_transcription)
            
            return txt_file_path
            
        except Exception as e:
            print(f"自动保存失败: {e}")
            return None

    def on_error(self, error_msg):
        self.progress_timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.select_file_btn.setEnabled(True)
        self.status_label.setText("错误")
        QMessageBox.critical(self, "错误", error_msg)

    def save_result(self):
        if not self.full_transcription:
            QMessageBox.warning(self, "警告", "没有可保存的内容")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存转录结果",
            "",
            "Text Files (*.txt);;All Files (*)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.full_transcription)
                QMessageBox.information(self, "成功", "文件保存成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
