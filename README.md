# Real-Time Audio Transcription System with Whisper AI

## Overview
This project implements a real-time audio transcription system leveraging OpenAI's Whisper model with CUDA acceleration. The system captures system audio output and performs continuous transcription using a segmented approach for optimal performance.

## Key Features
- Real-time audio capture and processing
- CUDA-accelerated Whisper model integration
- Segment-based processing for continuous streams
- Efficient memory management and resource utilization
- Multi-threaded architecture for concurrent processing
- Automated file management and cleanup

## Technical Architecture
The system operates through several key components:

1. **Audio Capture Engine**
   - Utilizes FFmpeg for real-time audio capture
   - Implements audio filtering for voice optimization
   - Supports configurable sampling rates and formats

2. **Processing Pipeline**
   - Segment-based audio processing
   - Concurrent processing using Python threading
   - Automated memory management
   - Real-time transcription using Whisper AI

3. **Resource Management**
   - CUDA memory optimization
   - Efficient file handling with automatic cleanup
   - Thread-safe operations

## Requirements
- NVIDIA GPU with CUDA support
- Python 3.8+
- FFmpeg
- PyTorch with CUDA support

## Dependencies
```bash
torch>=2.0.0
whisper>=1.0.0
pydub>=0.25.1
ffmpeg-python>=0.2.0
numpy>=1.21.0
```

## Installation
1. Create a Conda environment:
```bash
conda create -n whisper_env python=3.8
conda activate whisper_env
```

2. Install dependencies:
```bash
pip install torch whisper pydub ffmpeg-python numpy
```

3. Verify CUDA installation:
```python
import torch
print(torch.cuda.is_available())
```

## Usage
The system can be initialized and run using the following steps:

```python
from transcription_system import TranscriptionSystem

# Initialize the system
transcriber = TranscriptionSystem(
    model_size="small",
    segment_duration=60,
    language="en"
)

# Start transcription
transcriber.start()
```

## Performance Optimization
The system includes several optimizations:
- Segmented processing to manage memory efficiently
- CUDA memory management configurations
- Parallel processing of audio segments
- Efficient file handling with automatic cleanup

## Error Handling
Robust error handling is implemented throughout:
- Audio device availability checks
- CUDA memory management
- File system operations
- Thread safety mechanisms

## Contributing
Contributions are welcome! Please read our contributing guidelines and submit pull requests for any enhancements.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
