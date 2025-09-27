import { useEffect, useState } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useFrameworkReady } from '@/hooks/useFrameworkReady';
import { ThemeProvider } from '@/contexts/ThemeContext';

export default function RootLayout() {
  useFrameworkReady();
  const [isFirstLaunch, setIsFirstLaunch] = useState<boolean | null>(null);

  useEffect(() => {
    checkFirstLaunch();
  }, []);

  const checkFirstLaunch = async () => {
    try {
      const hasSeenOnboarding = await AsyncStorage.getItem('hasSeenOnboarding');
      setIsFirstLaunch(hasSeenOnboarding === null);
    } catch (error) {
      console.log('Error checking first launch:', error);
      setIsFirstLaunch(true);
    }
  };

  if (isFirstLaunch === null) {
    // Show loading or splash screen while checking
    return null;
  }

  return (
    <ThemeProvider>
      <Stack
        screenOptions={{ headerShown: false }}
        initialRouteName={isFirstLaunch ? "welcome" : "(tabs)"}
      >
        <Stack.Screen name="welcome" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="video" />
        <Stack.Screen name="+not-found" />
      </Stack>
      <StatusBar style="auto" />
    </ThemeProvider>
  );
}