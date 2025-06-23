package com.mainpackage.lotustranscriber

import android.Manifest
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener // You'll also need this for the listener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import androidx.lifecycle.ViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
// Potentially other imports like:
// import kotlinx.coroutines.flow.asStateFlow
// import androidx.lifecycle.viewModelScope
// import kotlinx.coroutines.launch
import java.util.Locale
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import androidx.annotation.RequiresPermission
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.*
import kotlin.math.abs
import kotlin.math.log10

class TranscriptionViewModel : ViewModel() {

    // Holds the transcribed text
    private val _transcription = MutableStateFlow("")
    val transcription: StateFlow<String> = _transcription

    // Holds the recording state
    private val _isRecording = MutableStateFlow(false)
    val isRecording: StateFlow<Boolean> = _isRecording

    // Holds the amplitude of the audio for the UI
    private val _amplitude = MutableStateFlow(0f)
    val amplitude = _amplitude.asStateFlow()

    // Launches the recording process, requires RECORD_AUDIO permission
    @RequiresPermission(Manifest.permission.RECORD_AUDIO)
    fun startRecording(context: Context) {
        // avoid starting multiple times
        if (_isRecording.value) return
        _isRecording.value = true

        // Androids built in speech recogniser (Google speech recognition)
        val recognizer = SpeechRecognizer.createSpeechRecognizer(context)

        // Create an intent to configure the speech recognizer
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault())
        }

        // Set up callbacks for various stages of speech recognition
        recognizer.setRecognitionListener(object : RecognitionListener {
            // Called when final recognition results are ready
            override fun onResults(results: Bundle?) {
                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                _transcription.value = matches?.firstOrNull() ?: "No speech recognized"
                _isRecording.value = false
                _amplitude.value = 0f
                recognizer.destroy()
            }

            // Called on recognition failure
            // Can be made more specific by checking error codes, instead of putting error codes on screen
            override fun onError(error: Int) {
                _transcription.value = "Error: $error"
                _isRecording.value = false
                _amplitude.value = 0f
                recognizer.destroy()
            }

            // Called regularly with RMS (volume) updates for UI display
            override fun onRmsChanged(rmsdB: Float) {
                // Normalize volume value to range between 0 and 1
                val normalized = (rmsdB + 2) / 20f
                _amplitude.value = normalized.coerceIn(0f, 1f)
            }

            // Required methods
            override fun onBeginningOfSpeech() {}
            override fun onEndOfSpeech() {}
            override fun onBufferReceived(buffer: ByteArray?) {}
            override fun onEvent(eventType: Int, params: Bundle?) {}
            override fun onPartialResults(partialResults: Bundle?) {}
            override fun onReadyForSpeech(params: Bundle?) {}
        })

        // Begin listening for speech
        recognizer.startListening(intent)
    }

}
