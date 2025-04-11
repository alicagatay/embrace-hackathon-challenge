import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:io';
import 'package:path_provider/path_provider.dart';
import 'package:record/record.dart';
import 'package:just_audio/just_audio.dart';

void main() {
  runApp(const EmbraceApp());
}

class EmbraceApp extends StatefulWidget {
  const EmbraceApp({super.key});

  @override
  State<EmbraceApp> createState() => _EmbraceAppState();
}

class _EmbraceAppState extends State<EmbraceApp> {
  final AudioRecorder _record = AudioRecorder();
  final AudioPlayer _audioPlayer = AudioPlayer();
  bool _isRecording = false;
  String _status = 'Press the button to start recording';

  Future<void> _toggleRecording() async {
    if (!_isRecording) {
      bool hasPermission = await _record.hasPermission();
      if (hasPermission) {
        final dir = await getTemporaryDirectory();
        final path = '${dir.path}/voice_query.m4a';

        await _record.start(
          const RecordConfig(encoder: AudioEncoder.aacLc, bitRate: 128000),
          path: path,
        );

        setState(() {
          _isRecording = true;
          _status = 'Recording...';
        });
      } else {
        setState(() {
          _status = 'Microphone permission denied';
        });
      }
    } else {
      final path = await _record.stop();

      if (path != null) {
        setState(() {
          _isRecording = false;
          _status = 'Sending audio...';
        });

        await _sendAudioToBackend(File(path));

        setState(() {
          _status = 'Recording sent successfully';
        });
      }
    }
  }

  Future<void> _sendAudioToBackend(File file) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('http://localhost:8000/upload-audio/'),
    );
    request.files.add(await http.MultipartFile.fromPath('file', file.path));
    final response = await request.send();

    if (response.statusCode == 200) {
      final bytes = await response.stream.toBytes();
      print('Received audio bytes: ${bytes.length}');

      final tempDir = await getTemporaryDirectory();
      final audioFile = File('${tempDir.path}/response_audio.mp3');

      await audioFile.writeAsBytes(bytes);
      print('Saved audio file to: ${audioFile.path}');

      try {
        await _audioPlayer.setFilePath(audioFile.path);
        await _audioPlayer.play();
        print('Playback started');
      } catch (e) {
        print('AudioPlayer error: $e');
      }
    } else {
      print('Upload failed with status: ${response.statusCode}');
    }
  }

  @override
  void dispose() {
    _audioPlayer.dispose();
    _record.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
        appBar: AppBar(title: const Text('Voice Chat')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                _status,
                style: const TextStyle(fontSize: 24),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 20),
              FloatingActionButton(
                onPressed: _toggleRecording,
                child: Icon(_isRecording ? Icons.stop : Icons.mic),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
