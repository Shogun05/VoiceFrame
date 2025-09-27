import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ViewStyle,
  TextStyle,
  View,
} from 'react-native';

interface FadingBorderButtonProps {
  title: string;
  onPress: () => void;
  disabled?: boolean;
  glowColor?: string;
  backgroundColor?: string;
  textColor?: string;
  width?: number;
  height?: number;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export const FadingBorderButton: React.FC<FadingBorderButtonProps> = ({
  title,
  onPress,
  disabled = false,
  glowColor = '#4A90E2',
  backgroundColor = 'rgba(255, 255, 255, 0.05)',
  textColor = '#FFFFFF',
  width = 200,
  height = 50,
  style,
  textStyle,
}) => {
  // Convert hex color to rgba for gradient layers
  const hexToRgba = (hex: string, alpha: number) => {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  };

  const buttonOpacity = disabled ? 0.5 : 1;

  return (
    <TouchableOpacity
      style={[
        styles.button,
        {
          width,
          height,
          backgroundColor,
          opacity: buttonOpacity,
          borderColor: glowColor,
        },
        style,
      ]}
      onPress={onPress}
      disabled={disabled}
      activeOpacity={0.8}
    >
      {/* Multiple gradient layers for bleed effect - same as progress cards */}
      <View
        style={[
          styles.gradientLayer1,
          {
            backgroundColor: hexToRgba(glowColor, 0.15),
            borderRadius: (height / 2) - 2,
          },
        ]}
      />
      <View
        style={[
          styles.gradientLayer2,
          {
            backgroundColor: hexToRgba(glowColor, 0.08),
            borderRadius: (height / 2) - 4,
          },
        ]}
      />
      <View
        style={[
          styles.gradientLayer3,
          {
            backgroundColor: hexToRgba(glowColor, 0.03),
            borderRadius: (height / 2) - 6,
          },
        ]}
      />

      {/* Border glow effect */}
      <View
        style={[
          styles.borderGlow,
          {
            shadowColor: glowColor,
            shadowOpacity: disabled ? 0.1 : 0.3,
            borderRadius: height / 2 + 2,
          },
        ]}
      />

      {/* Button content */}
      <View style={styles.content}>
        <Text
          style={[
            styles.text,
            { color: textColor },
            textStyle,
          ]}
        >
          {title}
        </Text>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    borderRadius: 25,
    borderWidth: 2,
    position: 'relative',
    overflow: 'hidden',
    justifyContent: 'center',
    alignItems: 'center',
  },
  gradientLayer1: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    // Outer layer - strongest bleed from border
  },
  gradientLayer2: {
    position: 'absolute',
    top: 4,
    left: 4,
    right: 4,
    bottom: 4,
    // Middle layer - medium bleed
  },
  gradientLayer3: {
    position: 'absolute',
    top: 8,
    left: 8,
    right: 8,
    bottom: 8,
    // Inner layer - lightest bleed, fades to transparent
  },
  borderGlow: {
    position: 'absolute',
    top: -2,
    left: -2,
    right: -2,
    bottom: -2,
    shadowOffset: { width: 0, height: 0 },
    shadowRadius: 8,
    elevation: 5,
  },
  content: {
    zIndex: 10,
    justifyContent: 'center',
    alignItems: 'center',
    flex: 1,
  },
  text: {
    fontSize: 16,
    fontWeight: '600',
    textAlign: 'center',
  },
});