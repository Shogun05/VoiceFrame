import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import { Sparkles, Play } from 'lucide-react-native';
import { useTheme } from '@/contexts/ThemeContext';
import { LoadingIndicator } from '@/components/LoadingIndicator';
import { Toast } from '@/components/Toast';

const { width } = Dimensions.get('window');

export default function HomeScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const [storyPrompt, setStoryPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [toast, setToast] = useState({
    visible: false,
    message: '',
    type: 'success' as 'success' | 'error' | 'warning',
  });

  const showToast = (message: string, type: 'success' | 'error' | 'warning') => {
    setToast({ visible: true, message, type });
  };

  const hideToast = () => {
    setToast(prev => ({ ...prev, visible: false }));
  };

  const handleGenerate = async () => {
    if (!storyPrompt.trim()) {
      showToast('Please enter a story prompt', 'warning');
      return;
    }

    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // For now, always return success and navigate to video
      showToast('Story generated successfully!', 'success');
      
      // Navigate to video screen after short delay
      setTimeout(() => {
        router.push('/video');
      }, 1000);
    } catch (error) {
      showToast('Failed to generate story', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <Toast
        message={toast.message}
        type={toast.type}
        visible={toast.visible}
        onHide={hideToast}
      />
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <LinearGradient
          colors={[theme.primary, theme.secondary]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.headerGradient}
        >
          <View style={styles.header}>
            <Text style={styles.title}>VoiceFrame</Text>
            <Text style={styles.subtitle}>
              Transform your stories into beautiful videos
            </Text>
          </View>
        </LinearGradient>

        {/* Story Input Card */}
        <View style={[styles.card, { backgroundColor: theme.surface }]}>
          <View style={styles.cardHeader}>
            <Sparkles size={24} color={theme.primary} />
            <Text style={[styles.cardTitle, { color: theme.text }]}>
              Create Your Story
            </Text>
          </View>
          
          <TextInput
            style={[
              styles.textInput,
              {
                backgroundColor: theme.background,
                borderColor: theme.border,
                color: theme.text,
              },
            ]}
            placeholder="Enter your story prompt here..."
            placeholderTextColor={theme.textSecondary}
            value={storyPrompt}
            onChangeText={setStoryPrompt}
            multiline
            numberOfLines={4}
            textAlignVertical="top"
          />
          
          <TouchableOpacity
            style={[
              styles.generateButton,
              {
                backgroundColor: theme.primary,
                opacity: isLoading || !storyPrompt.trim() ? 0.5 : 1,
              },
            ]}
            onPress={handleGenerate}
            disabled={isLoading || !storyPrompt.trim()}
          >
            {isLoading ? (
              <LoadingIndicator size="small" />
            ) : (
              <>
                <Play size={20} color="#FFFFFF" />
                <Text style={styles.generateButtonText}>Generate Video</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {/* Recent Stories */}
        <View style={[styles.card, { backgroundColor: theme.surface }]}>
          <Text style={[styles.cardTitle, { color: theme.text }]}>
            Recent Stories
          </Text>
          <Text style={[styles.emptyText, { color: theme.textSecondary }]}>
            No stories generated yet. Create your first story above!
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  headerGradient: {
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  header: {
    paddingHorizontal: 24,
    paddingVertical: 32,
    alignItems: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#FFFFFF',
    opacity: 0.9,
    textAlign: 'center',
  },
  card: {
    margin: 16,
    padding: 20,
    borderRadius: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginLeft: 8,
  },
  textInput: {
    borderWidth: 1,
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    minHeight: 120,
    marginBottom: 16,
  },
  generateButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
  },
  generateButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
  emptyText: {
    textAlign: 'center',
    fontSize: 16,
    lineHeight: 24,
  },
});