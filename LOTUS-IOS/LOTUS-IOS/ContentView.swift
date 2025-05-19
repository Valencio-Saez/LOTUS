//  ContentView.swift
//  LOTUS-IOS
//  Created by Valencio Muskiet on 18/05/2025.


// ContentView.swift
// LOTUS-IOS

import SwiftUI
import AVFoundation
import Speech

struct ContentView: View {
    @State private var isRecording = false
    @State private var transcription = ""
    @State private var animatedTranscription = ""
    @State private var lastTranscription = ""
    @State private var instruction = "Tap the lotus to start speaking"
    @State private var animationSessionID = UUID()

    private let speechRecognizer = SFSpeechRecognizer()
    private let audioEngine = AVAudioEngine()
    @State private var recognitionTask: SFSpeechRecognitionTask?
    @State private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?

    var body: some View {
        VStack(spacing: 16) {
            Spacer()

            Text(animatedTranscription)
                .padding()
                .multilineTextAlignment(.center)
                .foregroundColor(.black)
                .font(.headline)
                .transition(.opacity)
                .animation(.easeInOut, value: animatedTranscription)

            Image(isRecording ? "lotusopen" : "lotusclosed")
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(width: 200, height: 240)
                .onTapGesture {
                    isRecording ? stopRecording() : requestPermissionsAndStart()
                }
                .animation(.easeInOut(duration: 0.3), value: isRecording)

            Text(instruction)
                .padding()
                .multilineTextAlignment(.center)
                .foregroundColor(.black)
                .font(.headline)

            Spacer().frame(height: 100)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.white)
        .edgesIgnoringSafeArea(.all)
    }

    private func requestPermissionsAndStart() {
        SFSpeechRecognizer.requestAuthorization { authStatus in
            guard authStatus == .authorized else { return }
            AVAudioApplication.requestRecordPermission { granted in
                guard granted else { return }
                DispatchQueue.main.async { startRecording() }
            }
        }
    }

    private func startRecording() {
        stopRecording() // Clean up before starting fresh

        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let request = recognitionRequest else { return }

        let node = audioEngine.inputNode
        let format = node.outputFormat(forBus: 0)

        node.removeTap(onBus: 0)
        node.installTap(onBus: 0, bufferSize: 1024, format: format) { buffer, _ in
            request.append(buffer)
        }

        try? audioEngine.start()
        instruction = "Listening..."
        isRecording = true
        animationSessionID = UUID()
        transcription = ""
        animatedTranscription = ""
        lastTranscription = ""

        recognitionTask = speechRecognizer?.recognitionTask(with: request) { result, error in
            if let fullText = result?.bestTranscription.formattedString {
                let newSegment = String(fullText.dropFirst(lastTranscription.count))
                animateTextAppend(newSegment)
                lastTranscription = fullText
            } else if error != nil {
                stopRecording()
            }
        }
    }

    private func stopRecording() {
        audioEngine.stop()
        audioEngine.inputNode.removeTap(onBus: 0)
        recognitionRequest?.endAudio()
        recognitionTask?.cancel()

        recognitionRequest = nil
        recognitionTask = nil
        isRecording = false
        instruction = "Tap the lotus to start speaking"
        animationSessionID = UUID()
        transcription = ""
        animatedTranscription = ""
        lastTranscription = ""
    }

    private func animateTextAppend(_ newText: String) {
        let currentSession = animationSessionID
        for (i, letter) in newText.enumerated() {
            DispatchQueue.main.asyncAfter(deadline: .now() + Double(i) * 0.04) {
                if currentSession == animationSessionID {
                    animatedTranscription.append(letter)
                }
            }
        }
    }
}
