import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated } from 'react-native';
import { useTheme } from '@/contexts/ThemeContext';

interface LoadingIndicatorProps {
  size?: 'small' | 'large';
}

export function LoadingIndicator({ size = 'large' }: LoadingIndicatorProps) {
  const { theme } = useTheme();
  const spinValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const spinAnimation = Animated.loop(
      Animated.timing(spinValue, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      })
    );
    spinAnimation.start();

    return () => spinAnimation.stop();
  }, []);

  const spin = spinValue.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const containerSize = size === 'small' ? 20 : 40;
  const borderWidth = size === 'small' ? 2 : 4;

  return (
    <View style={styles.container}>
      <Animated.View
        style={[
          styles.spinner,
          {
            width: containerSize,
            height: containerSize,
            borderWidth,
            borderColor: `${theme.primary}30`,
            borderTopColor: theme.primary,
            transform: [{ rotate: spin }],
          },
        ]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  spinner: {
    borderRadius: 100,
  },
});