//
//  ContentView.swift
//  LOTUS-IOS
//
//  Created by Valencio Muskiet on 18/05/2025.
//

import SwiftUI
import AVFoundation
import Speech

struct ContentView: View {
    @State private var isRecording = false
    @State private var transcription = "Tap to start speaking"
    
    private let speechRecognizer = SFSpeechRecognizer()
    private let audioEngine = AVAudioEngine()
    @State private var recognitionTask: SFSpeechRecognitionTask?
    @State private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?

    var body: some View {
        VStack {
            Text(transcription)
                .padding()
                .foregroundColor(.black) // Text color set to black

            Button(action: {
                isRecording ? stopRecording() : requestPermissionsAndStart()
            }) {
                Circle()
                    .fill(isRecording ? Color.red : Color.blue)
                    .frame(width: 100, height: 100)
                    .overlay(
                        Image(systemName: isRecording ? "stop.fill" : "mic.fill")
                            .font(.system(size: 30))
                            .foregroundColor(.white)
                    )
            }
            .padding()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity) // Full screen
        .background(Color.white) // Background set to white
        .edgesIgnoringSafeArea(.all) // Optional: ignores safe areas for full coverage
    }
    
    func requestPermissionsAndStart() {
        SFSpeechRecognizer.requestAuthorization { authStatus in
            if authStatus == .authorized {
                AVAudioApplication.requestRecordPermission { granted in
                    if granted {
                        DispatchQueue.main.async {
                            startRecording()
                        }
                    }
                }
            }
        }
    }

    func startRecording() {
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        
        guard let recognitionRequest = recognitionRequest else { return }
        
        let node = audioEngine.inputNode
        let format = node.outputFormat(forBus: 0)
        node.removeTap(onBus: 0) // clean up any existing taps
        node.installTap(onBus: 0, bufferSize: 1024, format: format) { buffer, _ in
            recognitionRequest.append(buffer)
        }
        
        audioEngine.prepare()
        try? audioEngine.start()
        
        transcription = "Listening..."
        isRecording = true
        
        recognitionTask = speechRecognizer?.recognitionTask(with: recognitionRequest) { result, error in
            if let result = result {
                transcription = result.bestTranscription.formattedString
            } else if let error = error {
                print("Recognition error: \(error.localizedDescription)")
                stopRecording()
            }
        }
    }
    
    func stopRecording() {
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        recognitionTask?.cancel()
        
        isRecording = false
    }
}
