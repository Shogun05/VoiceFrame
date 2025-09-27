import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { Download, Trash2, Share } from 'lucide-react-native';
import { useTheme } from '@/contexts/ThemeContext';

export default function DownloadsScreen() {
  const { theme } = useTheme();

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: theme.background }]}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: theme.text }]}>Downloads</Text>
        <Text style={[styles.subtitle, { color: theme.textSecondary }]}>
          Your saved videos
        </Text>
      </View>

      <ScrollView style={styles.scrollView}>
        <View style={styles.emptyState}>
          <Download size={64} color={theme.textSecondary} />
          <Text style={[styles.emptyTitle, { color: theme.text }]}>
            No Downloads
          </Text>
          <Text style={[styles.emptySubtitle, { color: theme.textSecondary }]}>
            Downloaded videos will appear here
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
  header: {
    paddingHorizontal: 24,
    paddingVertical: 24,
    paddingTop: 48,
  },
  title: {
    fontSize: 28,
    fontWeight: '800',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
  },
  scrollView: {
    flex: 1,
    paddingHorizontal: 16,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 64,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: '700',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 16,
    textAlign: 'center',
  },
});