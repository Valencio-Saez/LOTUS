import SwiftUI
import AVFoundation
import Speech

struct ContentView: View {
    private let audioEngine = AVAudioEngine()

    @State private var isRecording = false
    @State private var animatedTranscription = ""
    @State private var lastTranscription = ""
    @State private var instruction = "Tap the lotus to start speaking"
    @State private var recognitionTask: SFSpeechRecognitionTask?
    @State private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    @State private var micLevel: CGFloat = 0

    
    var body: some View {
        VStack(spacing: 16) {
            Spacer()

            Text(highlightedText())
                .padding()
                .multilineTextAlignment(.center)
                .foregroundColor(.black)
                .font(.headline)
                .animation(.easeInOut, value: animatedTranscription)
                .accessibilityLabel("Transcribed speech")

            if isRecording {
                RoundedRectangle(cornerRadius: 4)
                    .fill(Color(red: 1.0, green: 0.78, blue: 0.78))  // original soft pink
                    .frame(width: micLevel * 200, height: 8)          // same height
                    .padding(.horizontal)
                    .animation(.linear(duration: 0.1), value: micLevel)
                    .accessibilityHidden(true)
            }

            Image(isRecording ? "lotusopen" : "lotusclosed")
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(width: 200, height: 240)
                .onTapGesture {
                    if isRecording {
                        stopRecording()
                    } else {
                        requestPermissionsAndStart()
                    }
                }
                .animation(.easeInOut(duration: 0.3), value: isRecording)
                .accessibilityLabel(isRecording ? "Tap to stop recording" : "Tap to start recording")

            Text(instruction)
                .padding()
                .multilineTextAlignment(.center)
                .foregroundColor(.black)
                .font(.title2)             // larger font size for instruction
                .fontWeight(.semibold)
                .accessibilityHint("Tap the lotus image above to begin or end speech transcription")

            Spacer().frame(height: 100)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.white)
        .edgesIgnoringSafeArea(.all)
    }

    private func requestPermissionsAndStart() {
        SFSpeechRecognizer.requestAuthorization { status in
            guard status == .authorized else { return }
            AVAudioSession.sharedInstance().requestRecordPermission { granted in
                guard granted else { return }
                DispatchQueue.main.async {
                    startRecording()
                }
            }
        }
    }

    
    
    private func startRecording() {
        stopRecording()

        // Configure audio session
        let session = AVAudioSession.sharedInstance()
        do {
            try session.setCategory(.record, mode: .measurement, options: .duckOthers)
            try session.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            print("Audio session setup failed: \(error.localizedDescription)")
        }

        // Set up recognition
        let locale = Locale.current
        let recognizer = SFSpeechRecognizer(locale: locale)
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let request = recognitionRequest else { return }
        request.shouldReportPartialResults = true
        request.taskHint = .dictation
        request.requiresOnDeviceRecognition = false

        let node = audioEngine.inputNode
        let format = node.outputFormat(forBus: 0)
        node.removeTap(onBus: 0)
        node.installTap(onBus: 0, bufferSize: 1024, format: format) { buffer, _ in
            request.append(buffer)
            updateMicLevel(buffer: buffer)
        }

        do {
            try audioEngine.start()
        } catch {
            print("Unable to start audioEngine: \(error.localizedDescription)")
        }

        instruction = "Recording..."
        isRecording = true
        animatedTranscription = ""
        lastTranscription = ""
        micLevel = 0

        UIImpactFeedbackGenerator(style: .light).impactOccurred()

        recognitionTask = recognizer?.recognitionTask(with: request) { result, error in
            if let result = result {
                let text = result.bestTranscription.formattedString
                withAnimation(.easeInOut(duration: 0.3)) {
                    animatedTranscription = text
                }
                lastTranscription = text
            }
            if error != nil {
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
        animatedTranscription = ""
        lastTranscription = ""
        micLevel = 0

        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
    }

    private func updateMicLevel(buffer: AVAudioPCMBuffer) {
        guard let data = buffer.floatChannelData?[0] else { return }
        let frames = Int(buffer.frameLength)
        let values = Array(UnsafeBufferPointer(start: data, count: frames))
        let rms = sqrt(values.map { $0 * $0 }.reduce(0, +) / Float(frames))
        micLevel = CGFloat(min(max(rms * 60, 0), 1))  // increased multiplier from 20 to 35
    }

    private func highlightedText() -> AttributedString {
        var attributed = AttributedString(animatedTranscription)
        let plain = String(animatedTranscription)
        let parts = lastTranscription.split(whereSeparator: { $0.isWhitespace })
        guard let last = parts.last else { return attributed }
        if let range = plain.range(of: String(last), options: .backwards) {
            let ns = NSRange(range, in: plain)
            if let ar = Range(ns, in: attributed) {
                attributed[ar].foregroundColor = Color(red:1.0, green:0.78, blue:0.78)
                attributed[ar].font = .headline.bold()
            }
        }
        return attributed
    }
}
