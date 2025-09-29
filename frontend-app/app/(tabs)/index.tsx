import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Dimensions,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Sparkles, Mic, StopCircle, Play } from 'lucide-react-native';
import { useTheme } from '@/contexts/ThemeContext';
import { LoadingIndicator } from '@/components/LoadingIndicator';
import { Toast } from '@/components/Toast';
import { useRouter } from 'expo-router';
import { Audio } from 'expo-av';

const { width } = Dimensions.get('window');

export default function HomeScreen() {
  const { theme } = useTheme();
  const router = useRouter();

  const [storyPrompt, setStoryPrompt] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState({
    visible: false,
    message: '',
    type: 'success' as 'success' | 'error' | 'warning',
  });

  const mediaRecorderRef = useRef<MediaRecorder | Audio.Recording | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const showToast = (message: string, type: 'success' | 'error' | 'warning') => {
    setToast({ visible: true, message, type });
  };
  const hideToast = () => setToast(prev => ({ ...prev, visible: false }));

  const handleRecordPress = async () => {
    if (!isRecording) {
      if (Platform.OS === 'web') {
        // Web: MediaRecorder
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          const mediaRecorder = new MediaRecorder(stream);
          audioChunksRef.current = [];

          mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) audioChunksRef.current.push(e.data);
          };

          mediaRecorder.onstop = async () => {
            const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
            await handleTranscribe(blob);
          };

          mediaRecorder.start();
          mediaRecorderRef.current = mediaRecorder;
          setIsRecording(true);
          showToast('Recording started (Web)', 'success');
        } catch (err) {
          console.error(err);
          showToast('Failed to start recording', 'error');
        }
      } else {
        // Mobile: expo-av
        try {
          const { status } = await Audio.requestPermissionsAsync();
          if (status !== 'granted') {
            showToast('Microphone permission required', 'error');
            return;
          }

          await Audio.setAudioModeAsync({
            allowsRecordingIOS: true,
            playsInSilentModeIOS: true,
          });

          const recording = new Audio.Recording();
          await recording.prepareToRecordAsync(Audio.RECORDING_OPTIONS_PRESET_HIGH_QUALITY);
          await recording.startAsync();

          mediaRecorderRef.current = recording;
          setIsRecording(true);
          showToast('Recording started', 'success');
        } catch (err) {
          console.error(err);
          showToast('Failed to start recording', 'error');
        }
      }
    } else {
      // Stop recording
      if (Platform.OS === 'web') {
        mediaRecorderRef.current && (mediaRecorderRef.current as MediaRecorder).stop();
        setIsRecording(false);
      } else {
        const recording = mediaRecorderRef.current as Audio.Recording;
        if (!recording) return;

        try {
          await recording.stopAndUnloadAsync();
          const uri = recording.getURI();
          setIsRecording(false);
          if (uri) await handleTranscribe(uri);
        } catch (err) {
          console.error(err);
          showToast('Failed to stop recording', 'error');
        }
      }
    }
  };

  const handleTranscribe = async (input: Blob | string) => {
    setIsLoading(true);
    try {
      const formData = new FormData();
      if (Platform.OS === 'web') {
        formData.append('file', input as Blob, 'recording.webm');
      } else {
        const uri = input as string;
        formData.append('file', { uri, name: 'recording.m4a', type: 'audio/m4a' } as any);
      }

      const BASE_URL = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';

      const response = await fetch(`${BASE_URL}/transcribe`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Transcription failed');
      const data = await response.json();

      setStoryPrompt(prev => (prev ? prev + ' ' : '') + data.transcription);
      showToast('Transcription added!', 'success');
    } catch (err: any) {
      console.error(err);
      showToast(err.message || 'Transcription failed', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateVideo = () => {
    if (!storyPrompt.trim()) {
      showToast('Please enter or record a story', 'warning');
      return;
    }
    router.push({ pathname: '/video', params: { prompt: storyPrompt.trim() } });
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <Toast message={toast.message} type={toast.type} visible={toast.visible} onHide={hideToast} />
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <LinearGradient
          colors={[theme.primary, theme.secondary]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.headerGradient}
        >
          <View style={styles.header}>
            <Text style={styles.title}>VoiceFrame</Text>
            <Text style={styles.subtitle}>Transform your stories into beautiful videos</Text>
          </View>
        </LinearGradient>

        <View style={[styles.card, { backgroundColor: theme.surface }]}>
          <View style={styles.cardHeader}>
            <Sparkles size={24} color={theme.primary} />
            <Text style={[styles.cardTitle, { color: theme.text }]}>Create Your Story</Text>
          </View>

          <TextInput
            style={[styles.textInput, { backgroundColor: theme.background, borderColor: theme.border, color: theme.text }]}
            placeholder="Enter your story here or record audio..."
            placeholderTextColor={theme.textSecondary}
            value={storyPrompt}
            onChangeText={setStoryPrompt}
            multiline
            numberOfLines={4}
            textAlignVertical="top"
          />

          <TouchableOpacity style={styles.micButton} onPress={handleRecordPress} disabled={isLoading}>
            {isRecording ? <StopCircle size={32} color="red" /> : <Mic size={32} color={theme.primary} />}
            <Text style={styles.micText}>{isRecording ? 'Stop & Transcribe' : 'Record Audio'}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.generateButton, { backgroundColor: theme.primary, opacity: !storyPrompt.trim() ? 0.5 : 1 }]}
            onPress={handleGenerateVideo}
            disabled={!storyPrompt.trim() || isLoading}
          >
            <Play size={20} color="#fff" />
            <Text style={styles.generateButtonText}>Generate Video</Text>
          </TouchableOpacity>

          {isLoading && <LoadingIndicator size="small" />}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  scrollContent: { flexGrow: 1 },
  headerGradient: { borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  header: { paddingHorizontal: 24, paddingVertical: 32, alignItems: 'center' },
  title: { fontSize: 32, fontWeight: '800', color: '#fff', marginBottom: 8 },
  subtitle: { fontSize: 16, color: '#fff', opacity: 0.9, textAlign: 'center' },
  card: { margin: 16, padding: 20, borderRadius: 16, elevation: 2, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 4 },
  cardHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: 16 },
  cardTitle: { fontSize: 20, fontWeight: '700', marginLeft: 8 },
  textInput: { borderWidth: 1, borderRadius: 12, padding: 16, fontSize: 16, minHeight: 120, marginBottom: 16 },
  micButton: { flexDirection: 'row', alignItems: 'center', gap: 8, justifyContent: 'center', marginBottom: 16 },
  micText: { fontSize: 16, color: '#555', fontWeight: '600' },
  generateButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 16, borderRadius: 12, gap: 8 },
  generateButtonText: { color: '#fff', fontSize: 18, fontWeight: '700' },
});
