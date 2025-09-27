import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
// import PagerView from 'react-native-pager-view';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import { Sparkles, Video, Download, ArrowRight } from 'lucide-react-native';
import { useTheme } from '@/contexts/ThemeContext';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width } = Dimensions.get('window');

interface OnboardingItem {
  icon: React.ComponentType<any>;
  title: string;
  subtitle: string;
  description: string;
}

const onboardingData: OnboardingItem[] = [
  {
    icon: Sparkles,
    title: 'Create Stories',
    subtitle: 'AI-Powered Storytelling',
    description: 'Transform your ideas into compelling narratives with our advanced AI story generation.',
  },
  {
    icon: Video,
    title: 'Generate Videos',
    subtitle: 'Stories Come to Life',
    description: 'Watch your stories transform into beautiful, engaging videos with stunning visuals.',
  },
  {
    icon: Download,
    title: 'Save & Share',
    subtitle: 'Your Content, Your Way',
    description: 'Download your created videos and share them with friends, family, or social media.',
  },
];

export default function WelcomeScreen() {
  const { theme } = useTheme();
  const router = useRouter();
  const [currentPage, setCurrentPage] = useState(0);

  const handleComplete = async () => {
    try {
      await AsyncStorage.setItem('hasSeenOnboarding', 'true');
      router.replace('/(tabs)');
    } catch (error) {
      console.log('Error saving onboarding state:', error);
      router.replace('/(tabs)');
    }
  };

  const handleSkip = () => {
    handleComplete();
  };

  const handleNext = () => {
    if (currentPage < onboardingData.length - 1) {
      setCurrentPage(currentPage + 1);
    } else {
      handleComplete();
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <LinearGradient
        colors={[theme.primary, theme.secondary]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.headerGradient}
      >
        <View style={styles.header}>
          <Text style={styles.appTitle}>VoiceFrame</Text>
          <TouchableOpacity onPress={handleSkip} style={styles.skipButton}>
            <Text style={styles.skipText}>Skip</Text>
          </TouchableOpacity>
        </View>
      </LinearGradient>

      <PagerView
        style={styles.pagerView}
        initialPage={0}
        onPageSelected={(e) => setCurrentPage(e.nativeEvent.position)}
      >
        {onboardingData.map((item, index) => (
          <View key={index} style={styles.page}>
            <View style={styles.iconContainer}>
              <item.icon size={64} color={theme.primary} />
            </View>
            
            <Text style={[styles.title, { color: theme.text }]}>
              {item.title}
            </Text>
            
            <Text style={[styles.subtitle, { color: theme.primary }]}>
              {item.subtitle}
            </Text>
            
            <Text style={[styles.description, { color: theme.textSecondary }]}>
              {item.description}
            </Text>
          </View>
        ))}
      </PagerView>

      <View style={styles.footer}>
        {/* Page Indicators */}
        <View style={styles.indicators}>
          {onboardingData.map((_, index) => (
            <View
              key={index}
              style={[
                styles.indicator,
                {
                  backgroundColor: index === currentPage ? theme.primary : theme.border,
                },
              ]}
            />
          ))}
        </View>

        {/* Action Button */}
        <TouchableOpacity
          style={[styles.actionButton, { backgroundColor: theme.primary }]}
          onPress={handleNext}
        >
          <Text style={styles.actionButtonText}>
            {currentPage === onboardingData.length - 1 ? 'Get Started' : 'Next'}
          </Text>
          <ArrowRight size={20} color="#FFFFFF" />
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  headerGradient: {
    paddingTop: 48,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 16,
  },
  appTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  skipButton: {
    padding: 8,
  },
  skipText: {
    fontSize: 16,
    color: '#FFFFFF',
    opacity: 0.8,
  },
  pagerView: {
    flex: 1,
  },
  page: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  iconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0, 122, 255, 0.1)',
    marginBottom: 32,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 16,
  },
  description: {
    fontSize: 16,
    lineHeight: 24,
    textAlign: 'center',
  },
  footer: {
    paddingHorizontal: 24,
    paddingBottom: 32,
  },
  indicators: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 24,
    gap: 8,
  },
  indicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
  },
  actionButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
});