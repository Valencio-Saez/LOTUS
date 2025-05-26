import SwiftUI
import AVFoundation
import Speech

struct ContentView: View {
    private let audioEngine = AVAudioEngine()
    
    @State private var isRecording = false
    @State private var fullTranscription = ""
    @State private var lastAppendedTranscription = ""
    @State private var instruction = "Tap the lotus to start speaking"
    @State private var recognitionTask: SFSpeechRecognitionTask?
    @State private var recognitionRequest: SFSpeechAudioBufferRecognitionRequest?
    @State private var micLevel: CGFloat = 0
    @State private var partialText = ""
    
    private let silenceDelay: TimeInterval = 1.5
    @State private var silenceTimer: Timer? = nil
    
    var body: some View {
        VStack(spacing: 20) {
            Spacer()
            
            ScrollViewReader { proxy in
                ScrollView(.vertical, showsIndicators: true) {
                    VStack(alignment: .leading, spacing: 12) {
                        ForEach(fullTranscription.components(separatedBy: "\n"), id: \.self) { line in
                            Text(line)
                                .foregroundColor(.black)
                                .font(.body)
                                .multilineTextAlignment(.leading)
                        }
                    }
                    .padding()
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .id("Bottom")
                }
                .frame(height: 250)
                .background(Color(white: 0.95))
                .cornerRadius(12)
                .padding(.horizontal)
                .onChange(of: fullTranscription) { _ in
                    withAnimation {
                        proxy.scrollTo("Bottom", anchor: .bottom)
                    }
                }
            }

            if isRecording {
                RoundedRectangle(cornerRadius: 4)
                    .fill(Color.red.opacity(0.6))
                    .frame(width: micLevel * 200, height: 8)
                    .padding(.horizontal)
                    .animation(.linear(duration: 0.1), value: micLevel)
                    .accessibilityHidden(true)
            }

            Image(isRecording ? "lotusopen" : "lotusclosed")
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(width: 200, height: 240)
                .onTapGesture {
                    isRecording ? stopRecording() : requestPermissionsAndStart()
                }
                .accessibilityLabel(isRecording ? "Stop recording" : "Start recording")

            Text(instruction)
                .padding()
                .multilineTextAlignment(.center)
                .foregroundColor(.gray)
                .font(.title3)
            
            Spacer().frame(height: 60)
        }
        .background(Color.white)
        .edgesIgnoringSafeArea(.all)
    }

    private func requestPermissionsAndStart() {
        SFSpeechRecognizer.requestAuthorization { authStatus in
            guard authStatus == .authorized else { return }
            AVAudioSession.sharedInstance().requestRecordPermission { granted in
                if granted {
                    DispatchQueue.main.async { startRecording() }
                }
            }
        }
    }

    private func startRecording() {
        stopRecording()

        let audioSession = AVAudioSession.sharedInstance()
        do {
            try audioSession.setCategory(.record, mode: .measurement, options: .duckOthers)
            try audioSession.setActive(true, options: .notifyOthersOnDeactivation)
        } catch {
            print("Audio session error: \(error.localizedDescription)")
            return
        }

        let recognizer = SFSpeechRecognizer(locale: Locale.current)
        recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
        guard let request = recognitionRequest else { return }
        
        request.shouldReportPartialResults = true
        request.taskHint = .dictation
        request.requiresOnDeviceRecognition = false

        let inputNode = audioEngine.inputNode
        let format = inputNode.outputFormat(forBus: 0)
        inputNode.removeTap(onBus: 0)
        inputNode.installTap(onBus: 0, bufferSize: 1024, format: format) { buffer, _ in
            request.append(buffer)
            updateMicLevel(buffer: buffer)
        }

        do {
            try audioEngine.start()
        } catch {
            print("Audio engine error: \(error.localizedDescription)")
            return
        }

        instruction = "Listening..."
        isRecording = true
        fullTranscription = ""
        lastAppendedTranscription = ""
        partialText = ""

        recognitionTask = recognizer?.recognitionTask(with: request) { result, error in
            if let result = result {
                let transcript = result.bestTranscription.formattedString
                DispatchQueue.main.async {
                    partialText = transcript
                    
                    silenceTimer?.invalidate()
                    silenceTimer = Timer.scheduledTimer(withTimeInterval: silenceDelay, repeats: false) { _ in
                        DispatchQueue.main.async {
                            let newText = partialText.replacingOccurrences(of: lastAppendedTranscription, with: "").trimmingCharacters(in: .whitespacesAndNewlines)
                            if !newText.isEmpty {
                                fullTranscription += (fullTranscription.isEmpty ? "" : "\n") + newText
                                lastAppendedTranscription = partialText
                            }
                            partialText = ""
                        }
                    }
                }
            }

            if error != nil {
                stopRecording()
            }
        }

        UIImpactFeedbackGenerator(style: .light).impactOccurred()
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
        micLevel = 0
        silenceTimer?.invalidate()
        silenceTimer = nil

        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
    }

    private func updateMicLevel(buffer: AVAudioPCMBuffer) {
        guard let channelData = buffer.floatChannelData?[0] else { return }
        let frameLength = Int(buffer.frameLength)
        let channelDataArray = Array(UnsafeBufferPointer(start: channelData, count: frameLength))
        let sumSquares = channelDataArray.map { $0 * $0 }.reduce(0, +)
        let meanSquare = sumSquares / Float(frameLength)
        let rms = sqrt(meanSquare)
        micLevel = CGFloat(min(max(rms * 50, 0), 1))
    }
}

