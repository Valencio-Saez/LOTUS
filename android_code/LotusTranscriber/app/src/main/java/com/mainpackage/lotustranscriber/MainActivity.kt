package com.mainpackage.lotustranscriber

// Needed imports
import android.Manifest
import android.annotation.SuppressLint
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.ExperimentalAnimationApi
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.scaleIn
import androidx.compose.animation.scaleOut
import androidx.compose.animation.togetherWith
import androidx.compose.animation.with
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.mainpackage.lotustranscriber.ui.theme.LotusTranscriberTheme
import androidx.compose.runtime.collectAsState
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.compose.runtime.getValue
import androidx.compose.ui.res.painterResource
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.compose.material3.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.runtime.*
import android.content.Intent
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import android.widget.Toast
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import kotlinx.coroutines.delay
import kotlin.random.Random

// Entry point
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        requestAudioPermission()
        enableEdgeToEdge()
        setContent {
            LotusTranscriberTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    TranscriptionScreen(modifier = Modifier.padding(innerPadding))
                }
            }
        }
    }
    private fun requestAudioPermission() {
        val permission = Manifest.permission.RECORD_AUDIO
        val permissionCheck = ContextCompat.checkSelfPermission(this, permission)

        if (permissionCheck != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this, arrayOf(permission), 1)
        }
    }
}

@Composable
fun Greeting(name: String, modifier: Modifier = Modifier) {
    Text(
        text = "Hello $name!",
        modifier = modifier
    )
}

@SuppressLint("MissingPermission")
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TranscriptionScreen(
    modifier: Modifier = Modifier,
    viewModel: TranscriptionViewModel = viewModel()
) {
    val context = LocalContext.current
    val transcription by viewModel.transcription.collectAsState()
    val isRecording by viewModel.isRecording.collectAsState()

    var expanded by remember { mutableStateOf(false) }

    // File picker launcher
    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let {
            Toast.makeText(context, "Selected: $it", Toast.LENGTH_SHORT).show()
            // Upcoming file transcription here
        }
    }

    // top bar with dropdown menu
    CenterAlignedTopAppBar(
        title = {
            Text("Lotus Transcriber")
        },
        actions = {
            IconButton(onClick = { expanded = true }) {
                Icon(Icons.Default.MoreVert, contentDescription = "Menu")
            }
            DropdownMenu(
                expanded = expanded,
                onDismissRequest = { expanded = false }
            ) {
                DropdownMenuItem(
                    text = { Text("Select file") },
                    onClick = {
                        expanded = false
                        launcher.launch("*/*")
                    }
                )
            }
        }
    )


    // Main layout with the buttons and transcription
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(horizontal = 20.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Display transcription
        Text(
            text = transcription,
            fontSize = 18.sp,
            fontWeight = FontWeight.SemiBold,
            textAlign = TextAlign.Center,
            modifier = Modifier.padding(bottom = 24.dp)
        )
        //Observe the amplitude state of the mic and animate the bar accordingly
        val amplitude = viewModel.amplitude.collectAsState()

        val animatedAmplitude by animateFloatAsState(
            targetValue = amplitude.value,
            animationSpec = tween(durationMillis = 100)
        )

        //The visible bar
        Box(
            modifier = Modifier
                .fillMaxWidth(animatedAmplitude.coerceIn(0.05f, 1f))
                .height(6.dp)
                .background(Color(0xFFFF8C69))
                .padding(bottom = 16.dp)
        )

        // Record button
        LotusMicButton(isRecording) {
            if (!isRecording){
                viewModel.startRecording((context))
            }
        }

        Spacer(modifier = Modifier.height(40.dp))

        // Status text
        Text(
            text = if (isRecording) "Recording..." else "Tap the button to record",
            fontSize = 16.sp,
            fontWeight = FontWeight.Medium
        )
    }
}

@Preview(showBackground = true)
@Composable
fun GreetingPreview() {
    LotusTranscriberTheme {
        Greeting("Android")
    }
}

@OptIn(ExperimentalAnimationApi::class)
@Composable
// This is the button that records the audio
fun LotusMicButton(
    isRecording: Boolean,
    onClick: () -> Unit
) {
    Box(
        modifier = Modifier
            .size(120.dp)
            .clickable { onClick() },
        contentAlignment = Alignment.Center
    ) {
        AnimatedContent(
            targetState = isRecording,
            transitionSpec = {
                fadeIn() + scaleIn() togetherWith fadeOut() + scaleOut()
            },
            label = "Mic Image Animation"
        ) { recording ->
            // If recording, show lotus open, else show lotus closed
            val imageRes = if (recording) {
                R.drawable.lotusopen
            } else {
                R.drawable.lotusclosed
            }

            Image(
                painter = painterResource(id = imageRes),
                contentDescription = if (recording) "Recording" else "Idle"
            )
        }
    }
}
